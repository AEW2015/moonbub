"""Bounded deterministic state-machine regression, not exhaustive proof."""
import random
import unittest
import zlib
from collections import Counter
from model import Model, Token

SEED = 20261103
STEPS = 5000

def snapshot(m):
    return tuple((b.generation, b.state, b.frame_id, b.expected_length,
                  b.expected_crc, bytes(b.data)) for b in m.banks)

class StateMachineRegression(unittest.TestCase):
 def test_seeded_delays_retries_and_bank_isolation(self):
    rng = random.Random(SEED)
    m = Model(100, capacity=8)
    next_id = 0
    issued = []  # exact requests, for delayed duplicate/conflicting deliveries
    known_tokens = []
    intended = {}
    coverage = Counter()

    def send(op, **kw):
        nonlocal next_id
        rid = next_id; next_id += 1
        before = snapshot(m)
        ack = m.request(m.epoch, rid, op, **kw)
        issued.append((m.epoch, rid, op, kw.copy(), ack))
        coverage[op] += 1
        coverage[ack.outcome] += 1
        token = kw.get('token')
        if isinstance(token, Token) and token.epoch == m.epoch and token.bank in (0,1):
            if before[1-token.bank][1] != 'FREE': coverage['other_bank_live'] += 1
            self.assertEqual(before[1-token.bank], snapshot(m)[1-token.bank],
                             f'cross-bank mutation op={op} token={token}')
        if ack.outcome in ('STALE_TOKEN','BAD_DATA','WRONG_STATE','BUSY'):
            self.assertEqual(before, snapshot(m), f'rejected operation mutated state: {ack}')
        if ack.outcome == 'BEGIN_OK':
            known_tokens.append(ack.token)
        return ack

    for step in range(STEPS):
        choice = rng.randrange(100)
        if choice < 23:
            content = bytes([rng.randrange(256) for _ in range(rng.randrange(1,9))])
            ack = send('BEGIN', frame_id=step, length=len(content), crc=zlib.crc32(content))
            if ack.outcome == 'BEGIN_OK': intended[ack.token] = content
        elif choice < 40:
            live = [Token(m.epoch,i,b.generation) for i,b in enumerate(m.banks) if b.state=='RECEIVING']
            if live:
                t = rng.choice(live); b = m.banks[t.bank]
                space = b.expected_length-len(b.data)
                amount = rng.randrange(1,space+1) if space else 1
                if space and rng.randrange(4):
                    payload = intended[t][len(b.data):len(b.data)+amount]
                else:
                    payload = bytes(rng.randrange(256) for _ in range(amount))
                send('DATA',token=t,offset=len(b.data),payload=payload)
        elif choice < 52:
            live = [Token(m.epoch,i,b.generation) for i,b in enumerate(m.banks) if b.state=='RECEIVING']
            if live: send('ABORT', token=rng.choice(live))
        elif choice < 64:
            live = [Token(m.epoch,i,b.generation) for i,b in enumerate(m.banks) if b.state=='RECEIVING']
            if live: send('COMMIT', token=rng.choice(live))
        elif choice < 70:
            ready = [Token(m.epoch,i,b.generation) for i,b in enumerate(m.banks) if b.state=='READY']
            if ready: send('RELEASE', token=rng.choice(ready))
        elif choice < 83:
            stale = [t for t in known_tokens if t.epoch==m.epoch and
                     (m.banks[t.bank].state=='FREE' or m.banks[t.bank].generation != t.generation)]
            if stale:
                t=rng.choice(stale); op=rng.choice(('DATA','COMMIT','ABORT'))
                kw={'token':t}
                if op=='DATA':kw.update(offset=0,payload=b'x')
                ack=send(op,**kw);self.assertEqual(ack.outcome,'STALE_TOKEN')
                coverage['stale_'+op]+=1
                if m.banks[t.bank].generation != t.generation:
                    coverage['reused_'+op]+=1
        elif choice < 95 and issued:
            epoch,rid,op,kw,original = rng.choice(issued)
            before=snapshot(m)
            ack=m.request(epoch,rid,op,**kw)
            self.assertEqual(ack,original if epoch==m.epoch else type(ack)(rid,'STALE_EPOCH',kw.get('token')))
            self.assertEqual(before,snapshot(m),'delayed retry mutated banks')
            coverage['duplicate_current' if epoch==m.epoch else 'duplicate_old_epoch']+=1
            if epoch==m.epoch:
                conflict=m.request(epoch,rid,op,**(kw | {'payload':b'conflict'}))
                if kw.get('payload',b'')!=b'conflict':
                    self.assertEqual(conflict.outcome,'REQUEST_ID_CONFLICT')
                    self.assertEqual(before,snapshot(m))
                    coverage['conflict']+=1
        elif choice >= 95:
            old_epoch=m.epoch; old_tokens=known_tokens[:]
            m.reset(old_epoch+1);coverage['reset']+=1
            if old_tokens:
                t=rng.choice(old_tokens);before=snapshot(m)
                ack=m.request(m.epoch,next_id,'ABORT',token=t);next_id+=1
                self.assertEqual(ack.outcome,'STALE_TOKEN')
                self.assertEqual(before,snapshot(m));coverage['old_epoch_token']+=1
    for key in ('BEGIN_OK','BUSY','DATA_OK','ABORT_OK','COMMIT_REJECTED',
                'COMMIT_OK','RELEASE_OK','stale_DATA','stale_COMMIT','stale_ABORT',
                'reused_DATA','reused_COMMIT','reused_ABORT','other_bank_live','duplicate_current',
                'duplicate_old_epoch','conflict','reset','old_epoch_token'):
        self.assertGreater(coverage[key],0, f'missing deterministic coverage {key}')
    print(f'STATE_MACHINE_COVERAGE seed={SEED} steps={STEPS} '+
          ' '.join(f'{k}={coverage[k]}' for k in sorted(coverage)))

if __name__=='__main__':unittest.main(verbosity=2)
