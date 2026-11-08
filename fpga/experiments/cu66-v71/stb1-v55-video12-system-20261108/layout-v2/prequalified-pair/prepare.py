"""Export historical first12 historical KEY/P sequence and freshly checked independent oracles."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zlib
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=Path('C:/moon/dev')
BASE=ROOT/'experiments/cu66-native-v69'
HELPER=ROOT/'experiments/python-game-canonical-tag-v66-study/helpers.py'
sha=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('three_fixture_helpers',HELPER)
h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
r=h.bound('three_fixture_receiver',HELPER.parent/'receiver.py',h)
w=h.bound('three_fixture_wire',HELPER.parent/'protocol.py',h)
source_manifest=BASE/'manifest.json'
case=next(c for c in json.loads(source_manifest.read_text())['cases'] if c['scene']=='mass-effect-10000')
rx=r.Receiver('CU66');records=[];bodies=[]
for row in case['rows'][:12]:
    packet=(BASE/row['packet']['path']).read_bytes();assert sha(packet)==row['packet']['sha256']
    assert len(packet)<=49152 and zlib.crc32(packet[:-4])==int.from_bytes(packet[-4:],'little')
    bodies.append(packet)
    canonical,patches,meta,_=rx.receive(packet)
    assert not np.any(meta['vectors']) and all(d in (5,6) for d in meta['dispatch'])
    yuv=b''.join(p.astype(np.uint8).tobytes()for p in canonical)
    hud=b''.join(p['words'].astype('<u2').tobytes()for p in patches)
    display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(canonical)),tuple(p['words']for p in patches)).astype('<u2').tobytes()
    assert sha(yuv)==row['canonical_yuv_u8_sha256']
    assert sha(hud)==row['hud_words_u16le_sha256']
    assert sha(display)==row['display_rgb565_u16le_sha256']
    assert w.tag_u8(canonical).hex()==row['canonical_tag']
    tiled=b''.join(p.astype(np.uint8).reshape(p.shape[0]//8,8,p.shape[1]//8,8).transpose(0,2,1,3).tobytes() for p in canonical)
    if row['id']<2:
        old=ROOT/f'evidence/explore01-hardware-20261106-run01/reference-canonical-frame{row["id"]}.u16'
        assert tiled==old.read_bytes(), 'tiled canonical must equal retained native reference'
    files={}
    for ext,blob in [('cu66',packet),('yuv',yuv),('hud',hud),('rgb565',display),('canonical.u16',tiled)]:
        name=f'frame{row["id"]}.{ext}';(OUT/name).write_bytes(blob)
        files[ext]={'path':name,'bytes':len(blob),'sha256':sha(blob)}
    records.append({'id':row['id'],'reference_id':row['reference_id'],'key':row['key'],
        'canonical_tag':row['canonical_tag'],'files':files,'dispatch':meta['dispatch']})
v43=Path('C:/moon/publish/firmware/experiments/v43-dy71-bulk-hud-20261107/handheld/src/cu66/fixtures')
assert bodies[0]==(v43/'packet0.cu66').read_bytes() and bodies[1]==(v43/'packet1.cu66').read_bytes()

faults=[]
def rejected(label,receiver,packet):
    before=(receiver.last,receiver.rid,receiver.cached_tag)
    try:receiver.receive(packet)
    except ValueError as e:
        assert before==(receiver.last,receiver.rid,receiver.cached_tag)
        faults.append({'case':label,'rejected':True,'reason':str(e),'publication_unchanged':True})
    else:raise AssertionError(label+' unexpectedly accepted')
rejected('P1_without_KEY',r.Receiver('CU66'),bodies[1])
gap=r.Receiver('CU66');gap.receive(bodies[0]);rejected('P2_without_P1',gap,bodies[2])
bad=bytearray(bodies[2]);bad[100]^=1;rejected('outer_CRC_corruption',rx,bytes(bad))
rejected('stale_P2_after_later_publication',rx,bodies[2])
manifest={'status':'PASS_FRESH_SOFTWARE_REFERENCE_AND_FAULTS','scene':'mass-effect-10000',
 'source_kind':'historical retained ~4s cohort; NOT requested 120s Mass Effect clip',
 'source_manifest':str(source_manifest),'source_manifest_sha256':sha(source_manifest.read_bytes()),
 'helper_sha256':sha(HELPER.read_bytes()),'frames':records,'faults':faults,
 'dimensions':[720,480],'canonical_layout':'Y480x720 then U240x360 then V240x360 uint8',
 'hud_layout':'native reference rectangle order; concatenated uint16 little endian',
 'display_layout':'480 rows x720 columns RGB565 little endian',
 'canonical_u16_layout':'tile-major8x8 within each plane Y/U/V; adjacent x pixels packed low/high byte into u16le; exact original0/1 native reference equality',
 'limits':['Python reference correctness only; no native/RTL/hardware performance proof.',
           'Frames3..11 require actual native arena/lifecycle and integrated V027/V45 qualification before sending.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'frames':12,'faults':len(faults),'original_pair_exact':True,'manifest':str(OUT/'manifest.json')}))
