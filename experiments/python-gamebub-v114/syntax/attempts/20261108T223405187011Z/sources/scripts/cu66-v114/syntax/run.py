#!/usr/bin/env python3
"""Measure actual BR88 restart-chunk byte cost, not emulated FPGA throughput."""
import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import time
import zlib

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v114/syntax'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
CASES=ROOT/'experiments/python-gamebub-v91i2/vectors/cases.tsv'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def memory():
    m={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines()}
    f=next(l for l in Path('/proc/pressure/memory').read_text().splitlines()if l.startswith('full '))
    return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]))


class Native:
    def __init__(self,binary,log):self.p=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log)
    def request(self,op,data):
        self.p.stdin.write(op+struct.pack('<I',len(data))+data);self.p.stdin.flush()
        header=self.p.stdout.read(5)
        if len(header)!=5:raise RuntimeError('native helper ended')
        n=int.from_bytes(header[1:],'little');assert n<=1048576
        payload=self.p.stdout.read(n);assert len(payload)==n
        if not header[0]:raise ValueError(payload.decode())
        return payload
    def close(self):self.p.stdin.close();assert self.p.wait(timeout=15)==0


def worker(out,build):
    spec=importlib.util.spec_from_file_location('sr14',ROOT/'scripts/cu66-v114/syntax/codec.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
    sources=[Path(__file__).resolve(),ROOT/'scripts/cu66-v114/syntax/codec.py',AREA/'native.cpp',CASES,
             ROOT/'experiments/python-gamebub-v88/entropy/codec.py',ROOT/'experiments/python-gamebub-v88/entropy/codec.hpp',ROOT/'experiments/python-gamebub-v85/residual/encode.hpp']
    sources+=sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    pins={str(p.relative_to(ROOT)):sha(p)for p in sources}
    report=dict(schema='v114-restartable-packed-residual-chunk-study-v1',status='FAIL',source_sha256=pins,
                syntax='SR14 version1 experimental container, independent BR88 v1 chunks',
                production_profile_changed=False,FPGA_support=False,ESP32_support=False,Sunshine_support=False,
                actual_RTL_run=False,hardware_30fps=False,validated_decode_under10ms=False,
                limits=['Packed residual-block order, not spatial image-row partitions or a changed motion/reference model.',
                        'Python encoder/native encoder byte parity; independent Python and native container/coefficient roundtrip.',
                        'Projected parent byte size only: no CS88 parent with SR14 admission, native Sunshine encoder or frame publication.',
                        'Bit-load balancing is a hypothetical work distribution, not cycles, achieved clock or multi-lane hardware speed.',
                        'Existing reference/HUD/C2, reorder, memory-port, transport and parser costs are not integrated here.'],
                commands=[],rows=[],negative_checks=0,recovery_checks=0)
    started=time.monotonic();native=None;log=None
    try:
        for p in sources:
            target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
        binary=build/'sr14-native'
        cmd=['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),str(AREA/'native.cpp'),'-o',str(binary)]
        report['commands'].append(cmd)
        with(out/'compile.log').open('w')as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
        report['native_binary_sha256']=sha(binary);log=(out/'native-stderr.log').open('wb');native=Native(binary,log)
        frames=[]
        for line in CASES.read_text().splitlines():
            name,error,hexdata,*_=line.split('\t')
            if int(error):continue
            packet=bytes.fromhex(hexdata);assert packet[:4]==b'CS88'and zlib.crc32(packet[:-4])==int.from_bytes(packet[-4:],'big')
            mode,qmap,hud,residual=struct.unpack_from('>4I',packet,36)
            at=128+mode+qmap;end=at+residual;planes=[]
            for axis in range(3):
                count=int.from_bytes(packet[at:at+4],'big');at+=4;assert count in (0,1)
                if count:
                    blocks,size=struct.unpack_from('>II',packet,at);at+=8;payload=packet[at:at+size];at+=size
                    values=codec.strict.decode(payload,blocks);planes.append((axis,payload,values))
            assert at==end and end+hud+4==len(packet);frames.append((name,packet,planes))
        assert len(frames)==6
        for name,packet,planes in frames:
            for quantum in (32,64,128,256):
                new_bytes=0;old_bytes=0;bit_jobs=[];chunks=0
                for axis,old,values in planes:
                    encoded=codec.pack(values,axis,quantum);plane,decoded,entries=codec.unpack(encoded)
                    assert plane==axis and decoded==values
                    raw=struct.pack('<'+'h'*len(values),*values)
                    assert native.request(b'D',encoded)==raw
                    for start,n,payload in entries:
                        dense=struct.pack('<'+'h'*(n*64),*values[start*64:(start+n)*64])
                        assert native.request(b'E',dense)==payload,'Python/native encoder bytes'
                        assert codec.strict.decode(payload,n)==values[start*64:(start+n)*64]
                        if payload[5]:bits=n*64*16
                        else:
                            lengths=struct.unpack_from('<4I',payload,14);offset=42;bits=0
                            for length in lengths:bits+=int.from_bytes(payload[offset+2:offset+6],'little');offset+=length
                        bit_jobs.append(bits)
                    for mutation in ('offset','start','inner_crc'):
                        bad=bytearray(encoded)
                        if mutation=='offset':bad[20:24]=(int.from_bytes(bad[20:24],'big')+1).to_bytes(4,'big')
                        elif mutation=='start':bad[12:16]=(1).to_bytes(4,'big')
                        else:bad[-5]^=1
                        bad[-4:]=zlib.crc32(bad[:-4]).to_bytes(4,'big');bad=bytes(bad)
                        for decoder in (codec.unpack,lambda x:native.request(b'D',x)):
                            try:decoder(bad)
                            except ValueError:report['negative_checks']+=1
                            else:raise AssertionError('malformed container accepted')
                        assert native.request(b'D',encoded)==raw;report['recovery_checks']+=1
                    chunks+=len(entries);old_bytes+=len(old);new_bytes+=len(encoded)
                loads={}
                for lanes in (1,2,4):
                    lane=[0]*lanes
                    for bits in sorted(bit_jobs,reverse=True):lane[min(range(lanes),key=lambda i:lane[i])]+=bits
                    loads[str(lanes)]=max(lane)
                report['rows'].append(dict(case=name,chunk_blocks=quantum,source_frame_bytes=len(packet),
                    old_BR88_bytes=old_bytes,new_container_bytes=new_bytes,byte_change=new_bytes-old_bytes,
                    projected_parent_frame_bytes=len(packet)-old_bytes+new_bytes,
                    projected_parent_fits49152=len(packet)-old_bytes+new_bytes<=49152,chunks=chunks,
                    hypothetical_max_lane_Rice_bit_work=loads))
                print('SR14_CASE_PASS',name,quantum,flush=True)
        native.close();native=None;assert pins=={str(p.relative_to(ROOT)):sha(p)for p in sources}
        report.update(status='PASS_PYTHON_NATIVE_RESTART_CHUNK_ROUNDTRIPS_BYTE_COST_ONLY',frames=6,case_profiles=24)
    except BaseException as e:report['error']=repr(e);raise
    finally:
        if native is not None:native.p.kill();native.p.wait()
        if log is not None:log.close()
        report['wall_seconds']=time.monotonic()-started
        if report['rows']:
            with(out/'rows.csv').open('w',newline='')as f:
                w=csv.DictWriter(f,fieldnames=list(report['rows'][0]));w.writeheader();w.writerows(report['rows'])
        report['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()and p.name not in ('worker.log','memory.jsonl')}
        write(out/'receipt.json',report)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--worker',nargs=2,type=Path);args=ap.parse_args()
    if args.worker:worker(*args.worker);return
    if not args.run:print('PREPARED_NOT_RUN_SR14');return
    before=memory();assert before['available_bytes']>=8*1024**3 and before['PSI_full_avg10']<1,before
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v114-syntax-'+stamp);build.mkdir()
    cmd=['docker','run','--rm','--init','--name','gamebub-v114-syntax-'+stamp.lower(),'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','256','--network','none','--ulimit','core=0',
         '--mount',f'type=bind,src={ROOT},dst={ROOT},readonly','--mount',f'type=bind,src={out},dst={out}','--mount',f'type=bind,src={build},dst={build}',
         '-e','PYTHONDONTWRITEBYTECODE=1',IMAGE,'timeout','--kill-after=5s','600s','python3',str(Path(__file__).resolve()),'--worker',str(out),str(build)]
    write(out/'launch.json',dict(command=cmd,memory_before=before))
    stopped=None;high=0;started=time.monotonic()
    with(out/'worker.log').open('w')as f,(out/'memory.jsonl').open('w')as telemetry:
        process=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
        while process.poll()is None:
            sample=dict(elapsed=time.monotonic()-started,**memory());telemetry.write(json.dumps(sample)+'\n');telemetry.flush()
            high=high+1 if sample['PSI_full_avg10']>=5 else 0
            if sample['available_bytes']<4*1024**3 or high>=2 or sample['elapsed']>620:
                stopped=sample;subprocess.run(['docker','stop','--time','5','gamebub-v114-syntax-'+stamp.lower()],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
            time.sleep(2)
        code=process.wait(timeout=20)
    write(out/'host-completion.json',dict(exit_code=code,resource_stop=stopped,artifact_sha256={n:sha(out/n)for n in ('worker.log','memory.jsonl','launch.json')}))
    if (out/'receipt.json').exists():
        raw=json.loads((out/'receipt.json').read_text());write(AREA/'results.json',dict(raw,selected_receipt=str((out/'receipt.json').relative_to(ROOT)),host_completion=dict(path=str((out/'host-completion.json').relative_to(ROOT)),sha256=sha(out/'host-completion.json'))))
    assert code==0 and stopped is None,(code,stopped)
    print('V114_SYNTAX_FINISHED',json.loads((out/'receipt.json').read_text())['status'],out)


if __name__=='__main__':main()
