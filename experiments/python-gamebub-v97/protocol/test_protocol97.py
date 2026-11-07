"""Shared byte vectors: generated once by Python, read independently by Rust."""
import importlib.util
from pathlib import Path
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'host'))
from moonshine import protocol97 as p
from moonshine import protocol as legacy


def sender(s=p.Session(7), config=p.SinkConfig()):
    h = p.HostSession(s, config)
    h.accept_ack(p.Receiver(config, s.core_generation).setup(h.request()))
    return h


def build_vectors():
    rows = []
    def case(name, actions, config=0):
        rows.extend((name, config, *a) for a in actions)
    def setup(s=p.Session(7)):
        return ('SETUP', 'OK', s.encode().hex())
    def packet(b, outcome):
        return ('PACKET', outcome, b.hex())
    good = list(sender().packets(b'good', 11, 42))[0]
    recover = packet(good, 'DONE')
    for chunk in (1024, 1400):
        h = sender(p.Session(7, payload_size=chunk))
        for n in (1,2,3,chunk-1,chunk,chunk+1,chunk*2+1,p.JPEG_CAP):
            data = bytes((i * 31 + 7) & 255 for i in range(n))
            ps = list(h.packets(data, 10, 123456789))
            case(f'valid-{chunk}-{n}', [setup(h.session)] + [packet(b, 'DONE' if i == len(ps)-1 else 'MORE') for i,b in enumerate(ps)])
    raw = p.Session(7).encode()
    for n in range(40):
        case(f'setup-short-{n}', [('SETUP','ERR',raw[:n].hex()), setup(), recover])
    mutations = {'magic':(0,0),'version':(4,96),'kind':(5,2),'length':(7,39),'width':(16,0),'height':(18,0),
                 'cap':(20,1),'payload':(24,0),'flags':(27,1),'caps':(31,3),'reserved':(39,1)}
    for name,(at,value) in mutations.items():
        b=bytearray(raw); b[at]=value
        case('setup-'+name, [('SETUP','ERR',b.hex()),setup(),recover])
    for name,at in [('epochzero',8),('corezero',32)]:
        b=bytearray(raw); b[at:at+4]=b'\0'*4
        case('setup-'+name,[('SETUP','ERR',b.hex()),setup(),recover])
    case('setup-extra',[('SETUP','ERR',(raw+b'x').hex()),setup(),recover])
    for profile in (*p.RESEARCH,0xdeadbeef):
        s=p.Session(7,profile=profile,frame_cap=p.RESEARCH_CAP,sink_caps=p.CAP_OPAQUE)
        case(f'profile-deny-{profile:x}', [('SETUP','ERR',s.encode().hex()),setup(),recover])
        if profile in p.RESEARCH:
            h=sender(s,p.SinkConfig(profile))
            case(f'profile-optin-{profile:x}',[setup(s),packet(next(h.packets(b'opaque',10,42)),'DONE')],profile)
            wrong=p.Session(7,profile=profile,frame_cap=p.RESEARCH_CAP,sink_caps=p.CAP_JPEG)
            case(f'profile-cap-deny-{profile:x}',[('SETUP','ERR',wrong.encode().hex()),setup(),recover],profile)
    base=next(sender().packets(b'test',10,42))
    bads=[(f'packet-short-{n}',base[:n]) for n in range(28)]
    for name,at,value in [('epoch',0,1),('kind',10,4),('flags',11,7),('missing-sof',11,2),('missing-eof',11,1),('crc',16,1),('zero-total',15,0)]:
        b=bytearray(base); b[at]=value
        bads.append((name,bytes(b)))
    for name,total in [('zero',0),('overcap',p.JPEG_CAP+1),('overflow',0xffffffff)]:
        b=bytearray(base); b[12:16]=struct.pack('!I',total); bads.append((name,bytes(b)))
    bads.extend([('extra-payload',base+b'x'),('short-payload',base[:-1])])
    large=list(sender().packets(b'a'*2801,10,42))
    b=bytearray(large[0]);b[11]|=2;bads.append(('early-eof',bytes(b)))
    for name,b in bads:
        case('data-'+name,[setup(),packet(b,'ERR'),recover])
    case('lost-setup',[packet(base,'ERR'),setup(),recover])
    case('missing-start',[setup(),packet(large[1],'ERR'),recover])
    for name,seq in [('duplicate',[large[0],large[0]]),('reorder',[large[0],large[2]]),('missing',[large[0],large[2]])]:
        case(name,[setup(),packet(seq[0],'MORE'),packet(seq[1],'ERR'),recover])
    b=bytearray(large[1]);b[8:10]=b'\xff\xff'
    case('index-overflow',[setup(),packet(large[0],'MORE'),packet(b,'ERR'),recover])
    b=bytearray(large[1]);b[11]|=1
    case('continuation-sof',[setup(),packet(large[0],'MORE'),packet(b,'ERR'),recover])
    one=next(sender().packets(b'x',10,42))
    old=next(sender().packets(b'x',9,42))
    half=next(sender().packets(b'x',10+0x80000000,42))
    case('id-history',[setup(),packet(one,'DONE'),packet(one,'ERR'),packet(old,'ERR'),packet(half,'ERR'),recover])
    wrap=[next(sender().packets(b'x',i,42)) for i in (0xffffffff,0,0xffffffff,1)]
    case('id-wrap',[setup(),packet(wrap[0],'DONE'),packet(wrap[1],'DONE'),packet(wrap[2],'ERR'),packet(wrap[3],'DONE')])
    case('setup-idempotent',[setup(),packet(large[0],'MORE'),setup(),packet(large[1],'MORE'),packet(large[2],'DONE'),packet(one,'ERR'),recover])
    case('setup-same-epoch-change',[setup(),('SETUP','ERR',p.Session(7,payload_size=1024).encode().hex()),recover])
    s8=p.Session(8)
    case('epoch-reset-history',[setup(),packet(one,'DONE'),('RESET','OK',''),('SETUP','ERR',raw.hex()),setup(s8),packet(one,'ERR'),packet(next(sender(s8).packets(b'new',0,42)),'DONE')])
    case('lost-final-timeout',[setup(),packet(large[0],'MORE'),('TIMEOUT','OK',''),packet(large[1],'ERR'),recover])
    s9=p.Session(9,core_generation=2)
    case('core-change',[setup(),packet(large[0],'MORE'),('CORE','OK','2'),('SETUP','ERR',s8.encode().hex()),setup(s9),packet(next(sender(s9).packets(b'new',0,42)),'DONE')])
    return rows


def run_vectors(rows):
    previous=None
    counts={'cases':0,'rows':0,'accepted_fragments':0,'completed_frames':0,'rejected':0}
    for name,config,action,expected,value in rows:
        if name!=previous:
            r=p.Receiver(p.SinkConfig(config or None)); previous=name; counts['cases']+=1
        actual='OK'
        try:
            if action=='SETUP':
                ack=r.setup(bytes.fromhex(value))
                assert p.parse_session(ack,p.ACK,p.SinkConfig(config or None))==r.session
            elif action=='PACKET':
                c=r.accept(bytes.fromhex(value)); actual='DONE' if c.crc_complete else 'MORE'
                counts['accepted_fragments']+=1
                counts['completed_frames']+=c.crc_complete
            elif action=='RESET': r.reset()
            elif action=='TIMEOUT': r.abort()
            elif action=='CORE': r.core_changed(int(value))
            else: raise AssertionError(action)
        except ValueError:
            actual='ERR'; counts['rejected']+=1
        assert actual==expected,(name,action,expected,actual)
        counts['rows']+=1
    return counts


def extra_checks():
    h=p.HostSession(p.Session(1))
    try: list(h.packets(b'x',1,0))
    except ValueError: pass
    else: raise AssertionError('unacknowledged sender')
    for ack in (p.Session(2).encode(p.ACK), p.Session(1).encode(p.REQUEST)):
        try: h.accept_ack(ack)
        except ValueError: pass
        else: raise AssertionError('bad ack accepted')
    h.accept_ack(p.Receiver().setup(h.request()))
    for payload in (b'', bytes(p.JPEG_CAP+1)):
        try: list(h.packets(payload,1,0))
        except ValueError: pass
        else: raise AssertionError('bad size accepted')
    for n in (1,1024,1025,legacy.MAX_FRAME):
        data=bytes((i*13)&255 for i in range(n)); r=legacy.Reassembler(); result=None
        for b in legacy.packets(data,1,42): result=r.accept(b)
        assert result[1]==data
    for scenario in ('crc','loss','duplicate'):
        r=legacy.Reassembler(); ps=list(legacy.packets(b'x'*2050,1,42))
        if scenario=='crc':
            b=bytearray(ps[-1]);b[-1]^=1;ps[-1]=bytes(b)
        elif scenario=='loss': ps.pop(1)
        else: ps.insert(1,ps[0])
        try:
            for b in ps: r.accept(b)
        except ValueError: pass
        else: raise AssertionError('legacy malformed accepted')
    return {'sender_ack_and_bounds':True,'legacy_msv1_valid_sizes':4,'legacy_msv1_error_controls':3}


def write_vectors(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    rows=build_vectors()
    (directory/'vectors.tsv').write_text(''.join('\t'.join(map(str,row))+'\n' for row in rows))
    result=run_vectors(rows);result.update(extra_checks())
    (directory/'vectors.json').write_text(json.dumps({'format':'V97 shared wire vectors v1','columns':['case','opaque_profile_or_zero','action','expected','hex_or_value'],'summary':result,'cases':list(dict.fromkeys(row[0] for row in rows))},indent=2)+'\n')
    return result

if __name__=='__main__':
    print(json.dumps(write_vectors(Path(__file__).parent),indent=2))
