#!/usr/bin/env python3
"""Build the native C ABI offline in an existing container, one rustc at a time."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import struct
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v97/protocol'
sys.path.insert(0,str(ROOT/'host'))
from moonshine import protocol97 as p

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def memgate():
    available=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
    full=float(next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full ')).split('avg10=')[1].split()[0])
    return dict(available_bytes=available,psi_full_avg10=full,passed=available>=8*1024**3 and full<1)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--container',default='gamebub-esp32-dev');args=parser.parse_args()
    ident=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    out=AREA/'ffi-attempts'/ident;out.mkdir(parents=True);data=out/'data';data.mkdir()
    receipt={'id':ident,'status':'running','scope':'x86_64 native C ABI around portable Rust Gateway; no ESP32/Wi-Fi/QSPI timing or codec decoding','commands':[]}
    def cmd(argv,label,timeout=60):
        started=time.perf_counter_ns();entry={'argv':argv,'timeout_seconds':timeout};receipt['commands'].append(entry);save(out/'receipt.json',receipt)
        try:r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            (out/(label+'.log')).write_bytes(exc.stdout or b'');entry['timeout']=True;save(out/'receipt.json',receipt);raise
        (out/(label+'.log')).write_bytes(r.stdout);entry.update(returncode=r.returncode,elapsed_ns=time.perf_counter_ns()-started);save(out/'receipt.json',receipt)
        if r.returncode:raise RuntimeError(f'{label} returned {r.returncode}')
        return r.stdout.decode(errors='replace')
    try:
        source_rels=['scripts/cu66-v97/build_ffi.py','experiments/python-gamebub-v97/protocol/ffi.rs','experiments/python-gamebub-v97/protocol/protocol97_c.h','firmware/handheld/src/streaming/protocol97.rs','host/moonshine/protocol97.py']
        for rel in source_rels:
            dst=out/'sources'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dst)
        receipt['sources']={rel:sha(out/'sources'/rel) for rel in source_rels}
        host_pointer=ROOT/'experiments/python-gamebub-v97/host/results.json';host=json.loads(host_pointer.read_text());host_report=ROOT/host['selected_report'];receipt['host_report']={'path':str(host_report.relative_to(ROOT)),'sha256':sha(host_report),'pointer_sha256':sha(host_pointer)}
        jpeg=host_report.parent/'jpeg-00.jpg';noise=host_report.parent/'jpeg-02.jpg'
        cs92=ROOT/'experiments/python-gamebub-v92/wire/attempts/20261107T050111854625Z-5491490e/c0-f0-context_byte_min.cs92'
        fixtures=[]
        for n in (1,2,3,1401,1402,1403):fixtures.append((f'tail-{n}',bytes((i*29+3)&255 for i in range(n)),None,0))
        fixtures.extend([('real-720-jpeg',jpeg.read_bytes(),str(jpeg.relative_to(ROOT)),0),('real-720-noise-jpeg',noise.read_bytes(),str(noise.relative_to(ROOT)),0),('real-cs92-opaque',cs92.read_bytes(),str(cs92.relative_to(ROOT)),int.from_bytes(b'CS92','big'))])
        rows=[];pins=[]
        for i,(label,payload,origin,profile) in enumerate(fixtures):
            config=p.SinkConfig(profile or None)
            session=p.Session(97000+i,profile=profile or p.JPEG,frame_cap=p.RESEARCH_CAP if profile else p.JPEG_CAP,sink_caps=p.CAP_OPAQUE if profile else p.CAP_JPEG,payload_size=1400)
            h=p.HostSession(session,config);h.accept_ack(p.Receiver(config).setup(h.request()));packets=list(h.packets(payload,i,123456789))
            golden=label+'.bin';wire=label+'.datagrams';(data/golden).write_bytes(payload);(data/wire).write_bytes(b''.join(struct.pack('!I',len(b))+b for b in packets))
            rows.append('\t'.join((label,session.encode().hex(),golden,wire))+'\n')
            pins.append(dict(name=label,source=origin,profile=profile or p.JPEG,receiver_opaque_profile=profile,bytes=len(payload),payload_sha256=sha(data/golden),datagrams_sha256=sha(data/wire),session_hex=session.encode().hex(),packets=len(packets)))
        (data/'live-inputs.tsv').write_text(''.join(rows));save(data/'inputs.json',pins);receipt['inputs']=pins
        remote='/tmp/cu66-v97-ffi-'+ident
        cmd(['docker','exec',args.container,'mkdir','-p',remote],'mkdir')
        cmd(['docker','cp',str(out/'sources'),args.container+':'+remote+'/sources'],'copy-sources')
        receipt['rustc']=cmd(['docker','exec',args.container,'sh','-lc','rustc --version'],'rust-version').strip()
        receipt['memory_gate']=memgate();save(out/'receipt.json',receipt)
        if not receipt['memory_gate']['passed']:raise RuntimeError('compile resource gate failed')
        src=remote+'/sources/experiments/python-gamebub-v97/protocol/ffi.rs'
        cmd(['docker','exec',args.container,'sh','-lc',f'timeout 90 rustc --edition=2021 --test -C codegen-units=1 -C opt-level=1 {src} -o {remote}/ffi-tests'],'ffi-test-compile',110)
        cmd(['docker','exec',args.container,'timeout','30',remote+'/ffi-tests','--test-threads=1','--nocapture'],'ffi-tests',45)
        receipt['memory_gate_staticlib']=memgate();save(out/'receipt.json',receipt)
        if not receipt['memory_gate_staticlib']['passed']:raise RuntimeError('compile resource gate failed')
        cmd(['docker','exec',args.container,'sh','-lc',f'timeout 90 rustc --edition=2021 --crate-type staticlib -C codegen-units=1 -C opt-level=1 {src} -o {remote}/libv97_gateway.a'],'ffi-staticlib-compile',110)
        cmd(['docker','cp',args.container+':'+remote+'/libv97_gateway.a',str(out/'libv97_gateway.a')],'retain-staticlib')
        cmd(['docker','cp',args.container+':'+remote+'/ffi-tests',str(out/'ffi-tests')],'retain-tests')
        shutil.copyfile(AREA/'protocol97_c.h',out/'protocol97_c.h')
        receipt['status']='pass';receipt['staticlib_sha256']=sha(out/'libv97_gateway.a');receipt['ffi_tests_sha256']=sha(out/'ffi-tests');receipt['artifacts']={str(f.relative_to(out)):sha(f) for f in data.iterdir() if f.is_file()};save(out/'receipt.json',receipt)
        index={'latest_attempt':ident,'receipt':str((out/'receipt.json').relative_to(ROOT)),'staticlib':str((out/'libv97_gateway.a').relative_to(ROOT)),'header':str((out/'protocol97_c.h').relative_to(ROOT)),'live_inputs':str((data/'live-inputs.tsv').relative_to(ROOT)),'status':'pass'};save(AREA/'ffi-index.json',index);print(json.dumps(index,indent=2))
    except Exception as exc:
        receipt['status']='failed';receipt['error']=repr(exc);save(out/'receipt.json',receipt);print(out/'receipt.json',file=sys.stderr);raise
if __name__=='__main__':main()
