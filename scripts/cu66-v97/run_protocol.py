#!/usr/bin/env python3
"""Finite, single-job native protocol/gateway proof. No install, flash or timing claims."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import statistics
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


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def memory_gate():
    lines=Path('/proc/meminfo').read_text().splitlines()
    available=int(next(x.split()[1] for x in lines if x.startswith('MemAvailable:')))*1024
    pressure=Path('/proc/pressure/memory').read_text()
    full=float(next(x for x in pressure.splitlines() if x.startswith('full ')).split('avg10=')[1].split()[0])
    return {'available_bytes':available,'psi_full_avg10':full,'pass':available>=8*1024**3 and full<1.0}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--container',default='gamebub-esp32-dev');args=parser.parse_args()
    # Container identifier is a CLI argv element, never interpolated shell code.
    name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    attempt=AREA/'attempts'/name;attempt.mkdir(parents=True);data_dir=attempt/'data';data_dir.mkdir()
    state={'attempt':name,'status':'running','commands':[],'scope':'native CPU parser/gateway only; no ESP32/Wi-Fi/QSPI timing or decoder/publication proof','memory_gate':memory_gate()}
    record=attempt/'attempt.json';write_json(record,state)
    def call(argv,label,timeout=60):
        started=time.perf_counter_ns();entry={'label':label,'argv':argv,'timeout_seconds':timeout};state['commands'].append(entry);write_json(record,state)
        try:
            result=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
            (attempt/(label+'.log')).write_bytes(result.stdout);entry.update(returncode=result.returncode,elapsed_ns=time.perf_counter_ns()-started)
            write_json(record,state)
            if result.returncode: raise RuntimeError(f'{label} exited {result.returncode}; see {attempt/(label+".log")}')
            return result.stdout.decode(errors='replace')
        except subprocess.TimeoutExpired as exc:
            (attempt/(label+'.log')).write_bytes(exc.stdout or b'');entry.update(timed_out=True,elapsed_ns=time.perf_counter_ns()-started);write_json(record,state);raise
    try:
        spec=importlib.util.spec_from_file_location('v97_tests',AREA/'test_protocol97.py');tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        state['python']=tests.write_vectors(AREA)
        for filename in ('vectors.tsv','vectors.json'):shutil.copyfile(AREA/filename,data_dir/filename)
        sources=['scripts/cu66-v97/run_protocol.py','experiments/python-gamebub-v97/protocol/test_protocol97.py','experiments/python-gamebub-v97/protocol/native_driver.rs','host/moonshine/protocol97.py','host/moonshine/protocol.py','firmware/handheld/src/streaming/protocol97.rs','firmware/handheld/src/streaming/protocol.rs']
        for rel in sources:
            dst=attempt/'sources'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dst)
        state['sources']={rel:digest(attempt/'sources'/rel) for rel in sources}
        state['baseline_git_head']=call(['git','rev-parse','HEAD'],'git-head').strip()
        fixtures=[]
        for i,n in enumerate((1,2,3,1024,1025,1400,1401,1402,1403,2801,p.JPEG_CAP)):
            fixtures.append((f'synthetic-{n}',bytes((j*17+19)&255 for j in range(n)),None))
        real=ROOT/'host/fixtures/pattern-720x480-420-q65.jpg'
        if real.is_file(): fixtures.append(('retained-jpeg',real.read_bytes(),str(real.relative_to(ROOT))))
        inputs=[];input_manifest=[]
        for i,(label,payload,origin) in enumerate(fixtures):
            session=p.Session(100+i,payload_size=1400 if i%2 else 1024)
            h=tests.sender(session);wire=list(h.packets(payload,i,123456789))
            payload_file=label+'.bin';wire_file=label+'.datagrams'
            (data_dir/payload_file).write_bytes(payload)
            (data_dir/wire_file).write_bytes(b''.join(struct.pack('!I',len(b))+b for b in wire))
            inputs.append('\t'.join((label,session.encode().hex(),payload_file,wire_file))+'\n')
            input_manifest.append({'name':label,'origin':origin,'bytes':len(payload),'sha256':digest(data_dir/payload_file),'packet_file_sha256':digest(data_dir/wire_file),'fragment_payload':session.payload_size,'epoch':session.epoch,'frame_id':i,'packets':len(wire)})
        (data_dir/'trace-inputs.tsv').write_text(''.join(inputs));write_json(data_dir/'inputs.json',input_manifest)
        state['inputs']=input_manifest
        if real.is_file():
            payload=real.read_bytes();h=tests.sender(p.Session(500));packet_ns=[];crc_ns=[];copy_ns=[];stages=[bytearray(1400),bytearray(1400)];parts=list(h.packets(payload,1,0));views=[memoryview(b)[28 if i==0 else 12:] for i,b in enumerate(parts)]
            import zlib
            for i in range(105):
                t=time.perf_counter_ns();packets=list(h.packets(payload,i,0));dt=time.perf_counter_ns()-t
                t=time.perf_counter_ns();crc=zlib.crc32(payload);ct=time.perf_counter_ns()-t
                t=time.perf_counter_ns()
                for j,view in enumerate(views):stages[j%2][:len(view)]=view
                mt=time.perf_counter_ns()-t
                if i>=5:packet_ns.append(dt);crc_ns.append(ct);copy_ns.append(mt)
            def metrics(ns):return {'median_ns':statistics.median(ns),'p95_ns':sorted(ns)[94],'max_ns':max(ns),'samples':len(ns)}
            state['host_measurement']={'input':str(real.relative_to(ROOT)),'sha256':digest(real),'bytes':len(payload),'packetization_including_crc_and_wire_bytes_allocation':metrics(packet_ns),'crc_only_zlib':metrics(crc_ns),'two_bytearray_staging_copy_only_python_control':metrics(copy_ns),'packet_payload_copy_bytes_per_frame':len(payload),'staging_copy_bytes_per_frame':len(payload),'codec_encode_and_capture_measured':False,'scope':'actual native host Python wall clock; no ESP32 timing; input already retained JPEG'}
        if not state['memory_gate']['pass']:raise RuntimeError('compile memory gate failed')
        remote='/tmp/cu66-v97-'+name
        call(['docker','exec',args.container,'mkdir','-p',remote],'container-mkdir')
        call(['docker','cp',str(attempt/'sources'),args.container+':'+remote+'/sources'],'copy-sources')
        call(['docker','cp',str(data_dir),args.container+':'+remote+'/data'],'copy-inputs')
        state['toolchain']=call(['docker','exec',args.container,'sh','-lc','rustc --version'],'rust-version').strip()
        compile_source=remote+'/sources/experiments/python-gamebub-v97/protocol/native_driver.rs'
        state['memory_gate_before_compile']=memory_gate();write_json(record,state)
        if not state['memory_gate_before_compile']['pass']:raise RuntimeError('compile memory gate failed')
        call(['docker','exec',args.container,'sh','-lc',f'timeout 90 rustc --edition=2021 --test -C codegen-units=1 -C opt-level=1 {compile_source} -o {remote}/native-tests'],'native-compile',110)
        call(['docker','exec','-e','V97_VECTORS='+remote+'/data/vectors.tsv','-e','V97_DATA='+remote+'/data',args.container,'timeout','40',remote+'/native-tests','--test-threads=1','--nocapture'],'native-tests',55)
        call(['docker','cp',args.container+':'+remote+'/native-tests',str(attempt/'native-tests')],'retain-binary')
        call(['docker','cp',args.container+':'+remote+'/data/.',str(data_dir)],'retain-results')
        state['binary_sha256']=digest(attempt/'native-tests');state['native_metrics']=json.loads((data_dir/'native-metrics.json').read_text());state['status']='pass'
        state['artifacts']={str(f.relative_to(attempt)):digest(f) for f in sorted(data_dir.iterdir()) if f.is_file()}
        write_json(record,state)
        write_json(AREA/'index.json',{'latest_attempt':name,'attempt_json':str(record.relative_to(ROOT)),'status':state['status'],'native_trace':str((data_dir/'gateway-trace.txt').relative_to(ROOT)),'binary_sha256':state['binary_sha256'],'python':state['python'],'native_metrics':state['native_metrics']})
        print(json.dumps({'attempt':str(attempt.relative_to(ROOT)),'status':state['status'],'python':state['python'],'native_metrics':state['native_metrics']},indent=2))
    except Exception as exc:
        state['status']='failed';state['error']=repr(exc);write_json(record,state);print(str(record),file=sys.stderr);raise

if __name__=='__main__':main()
