#!/usr/bin/env python3
"""Retained finite RS24 loss traces and actual epoch-refresh packet probes."""
from pathlib import Path
import hashlib
import json
import numpy as np
import model as r

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pins():
    old = json.loads((HERE.parent / 'python-game-hd22-joint-study/results.json').read_text())
    paths = {ROOT / p for p in old['source_sha256']}
    paths |= {HERE.parent / 'python-game-hd22-joint-study/model.py'}
    paths |= set(HERE.glob('*.py'))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def endpoints():
    h, t = r.Host(101), r.Target(202)
    h.transport_drained = t.transport_drained = True
    return h, t


def probe(h, t, frame=0):
    source = np.full((480, 720, 3), [44, 96, 156], dtype=np.uint8)
    candidate = h.build(source, frame)
    assert candidate.accepted
    packet = h.commit(candidate)
    task = t.prepare_data(packet)
    t.receiver.mark_writes_drained(task)
    ack = t.receiver.present(task)
    h.acknowledge_data(ack)
    words = r.m.C.corpus.rgb565(source)
    for x, y, w, hh in r.m.hc.RECTANGLES:
        np.testing.assert_array_equal(t.receiver.display[y:y + hh, x:x + w], words[y:y + hh, x:x + w])
    base, hud = r.m.compose.unbind(packet)
    meta, hm = r.m.C.identity(base), r.m.hc.parse(hud)
    return dict(frame=frame, epoch=meta['epoch'], packet_hex=packet.hex(), ack_hex=ack.hex(),
                key=meta['key'], hud_independent=hm['refslot'] == r.m.hc.NO_REF,
                display_rgb565_sha256=hashlib.sha256(t.receiver.display.tobytes()).hexdigest(),
                exact_hud_words=21120)


def run():
    cases = []
    for drop in (None, *range(r.HELLO, r.GO_ACK + 1)):
        h, t = endpoints()
        trace, complete = r.exchange(h, t, drop_once=drop)
        assert complete
        output = probe(h, t)
        assert output['key'] and output['hud_independent']
        cases.append(dict(name='nominal' if drop is None else 'single_loss_kind_' + str(drop),
                          trace=trace, complete=complete, host_phase=h.phase, target_phase=t.phase,
                          control_application_bytes=sum(len(bytes.fromhex(x['bytes'])) for x in trace),
                          control_ipv4_udp_bytes=sum(len(bytes.fromhex(x['bytes'])) + 28 for x in trace),
                          lost_messages=sum(not x['delivered'] for x in trace), output=output))
    h, t = endpoints()
    trace, complete = r.exchange(h, t, drop_all=r.GO_ACK)
    assert not complete and h.phase == 'SAFE_STOP' and t.phase == 'RUNNING'
    cases.append(dict(name='all_go_ack_lost', trace=trace, complete=complete,
                      host_phase=h.phase, target_phase=t.phase,
                      control_application_bytes=46 * len(trace), control_ipv4_udp_bytes=74 * len(trace),
                      lost_messages=sum(not x['delivered'] for x in trace), output=None))
    h, t = endpoints()
    trace1, _ = r.exchange(h, t)
    old = probe(h, t)
    target2 = r.Target(303, ledger=t.ledger)
    target2.transport_drained = True
    trace2, _ = r.exchange(h, target2)
    before = target2.receiver.published_snapshot()
    try:
        target2.prepare_data(bytes.fromhex(old['packet_hex']))
    except ValueError:
        pass
    else:
        raise AssertionError('old epoch data accepted')
    assert target2.receiver.published_snapshot() == before
    new = probe(h, target2)
    host2 = r.Host(404, ledger=h.ledger)
    host2.transport_drained = True
    trace3, _ = r.exchange(host2, target2)
    newest = probe(host2, target2)
    assert [old['epoch'], new['epoch'], newest['epoch']] == [1, 2, 3]
    return dict(cases=cases, reboot_sequence=dict(traces=[trace1, trace2, trace3],
                                                outputs=[old, new, newest], stale_epoch_data_rejected=True))


def main():
    before = pins()
    result = run()
    assert before == pins()
    data = dict(schema='gamebub-recovery-v24', source_sha256=before,
                profile=r.PROFILE, profile_sha256_128=r.PROFILE_TAG.hex(),
                control_bytes=r.CONTROL_BYTES, results=result,
                scope=[
                    'In-memory synchronous reset/profile agreement, with actual CP23 key/full-HUD and JA23 probes. It is not installed or networked.',
                    'EpochLedger objects model durable monotonic state across reboot. Durable atomic writes, nonce generation and cryptographic rekey/authentication are not implemented.',
                    'Transport-drained and write/vblank gates are explicit model permissions. Actual DMA/FIFO/packet credits and physical scanout drain are not proved.',
                    'Successful reset clears reference/cache agreement and requires independent key/full HUD; pixel probes are one static synthetic source, not gameplay or FPS evidence.',
                    'Every emitted control is charged, including lost and repeated messages. No RF airtime/timeout latency/host scheduler model. Persistent loss can leave targetRUNNING while hostSAFE_STOP; host data remains blocked.'])
    (HERE / 'results.json').write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(campaigns=len(result['cases']), recovered=sum(c['complete'] for c in result['cases']),
                          nominal_messages=len(result['cases'][0]['trace']),
                          nominal_control_application_bytes=result['cases'][0]['control_application_bytes'],
                          nominal_control_ipv4_udp_bytes=result['cases'][0]['control_ipv4_udp_bytes'],
                          reboot_epochs=[p['epoch'] for p in result['reboot_sequence']['outputs']],
                          physical_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
