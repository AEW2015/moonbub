import hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path('/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study')
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
wire=load('v91l_wire',ROOT/'scripts/cu66-v88/run_wire.py')
original=load('v91l_original',ROOT/'experiments/python-gamebub-v82/native/data.py')
data=load('v91l_components',ROOT/'experiments/python-gamebub-v88/entropy/data.py')
oldwire=load('v91l_oldwire',ROOT/'scripts/cu66-v86/run_wire.py')
qcodec=load('v91l_qcodec',ROOT/'scripts/cu66-v87/quantizer_codec.py')
oldmap=load('v91l_oldmap',ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
groupmap=load('v91l_groupmap',ROOT/'scripts/cu66-v86/prototype_maps.py')
selected=json.loads((ROOT/'experiments/python-gamebub-v90/policy/results.json').read_text());pp=ROOT/selected['selected_report']
proxies={(r['cohort'],r['fid'],r['cost']):r for r in map(json.loads,pp.with_name('selections.jsonl').read_text().splitlines())}
commitments={(r['cohort'],r['fid']):r for r in map(json.loads,oldwire.C2_CONTROL.read_text().splitlines())}
targets={(0,2),(3,48),(3,49)};wanted={}
qcache={};n=0
for frame,native in zip(data.iter_frames(),original.iter_frames(),strict=True):
 key=(frame['cohort'],frame['fid']);assert key==(native['cohort'],native['fid'])
 ops=[1 if h else 0 if not frame['key'] and bool(native['zero_coeff_mask'][t]) else 2 for t,h in enumerate(native['hidden_mask'])]
 old=None if frame['key'] else qcache.get(frame['cohort']);values=qcodec.unpacked(frame['qmap'],1350)
 block=qcodec.encode(values,ops,old);qcache[frame['cohort']]=qcodec.decode(block,ops,old)
 if key in targets:
  options={c['mask']:c for c in wire.candidates(frame,native,commitments[key],block,oldwire,oldmap,groupmap)}
  choice=proxies[(*key,'LOW')];packet=options[choice['mask']]['packet']
  assert hashlib.sha256(packet).hexdigest()==choice['packet_sha256']
  path=ROOT/'/tmp'
  out=Path('/tmp')/f'v91l-c{key[0]}-f{key[1]}-proxy_LOW.cs88';out.write_bytes(packet)
  wanted[key]=dict(path=str(out),sha256=hashlib.sha256(packet).hexdigest(),bytes=len(packet),mask=choice['mask'])
  print(key,wanted[key])
 n+=1
 if len(wanted)==len(targets):break
print('scanned',n)
