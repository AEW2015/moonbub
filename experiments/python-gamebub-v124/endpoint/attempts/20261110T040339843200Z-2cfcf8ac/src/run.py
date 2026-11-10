#!/usr/bin/env python3
"""Prepare or run a bounded native-Sunshine to actual-Rust MSV1 host probe."""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time, uuid, zlib

ROOT=pathlib.Path(__file__).resolve().parents[3]
SUN=pathlib.Path('/home/lori/gamebub-streaming-prototype/repos/sunshine-30fps-study')
MOON=ROOT
SUN_HEAD='3d49c6fe87753eb5b35d693991fdff0365e4bbbf'
MOON_HEAD='1d462803bf2a638f25c2d13bd2215ca08a30518d'
IMAGE='sha256:e6e97e6db1c57d0f07530d7ae6912e455bb7079de7428f282a508a2fcca3fb5a'
IMAGE_TAG='gamebub-v124-native-endpoints:20261109'
JPEG_REL='tools/gamebub/fixtures/receiver-pattern-720x480-420-q65.jpg'
PACKETS_REL='tools/gamebub/fixtures/receiver-pattern-msv1-packets.bin'
EXPECTED_JPEG_SHA='8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de'
EXPECTED_PACKETS_SHA='78c58cfcc4860761c33bcc7021e3db14e9fa66ef5e9a385ae1e4c00c82a6447f'
FRAME_ID=0x12345678
CAPTURE_US=1234567890123
TOOL_ROOT=pathlib.Path('/home/lori/gamebub-tools')


def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return sha_bytes(pathlib.Path(p).read_bytes())
def write_json(p,d): pathlib.Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def run(cmd,**kw): return subprocess.run([str(x) for x in cmd],check=True,**kw)


def git_blob(repo,head,rel):
    return subprocess.check_output(['git','-C',str(repo),'show',f'{head}:{rel}'])


def source_catalog():
    files={
      'source/sunshine/msv1.cpp':(SUN,'src/gamebub/msv1.cpp',SUN_HEAD),
      'source/sunshine/msv1.h':(SUN,'src/gamebub/msv1.h',SUN_HEAD),
      'source/moonbub/protocol.rs':(MOON,'firmware/handheld/src/streaming/protocol.rs',MOON_HEAD),
      'source/sunshine/receiver-pattern-720x480-420-q65.jpg':(SUN,JPEG_REL,SUN_HEAD),
      'source/sunshine/receiver-pattern-msv1-packets.bin':(SUN,PACKETS_REL,SUN_HEAD),
      'source/moonbub/host-pattern-720x480-420-q65.jpg':(MOON,'host/fixtures/pattern-720x480-420-q65.jpg',MOON_HEAD),
      'source/moonbub/host-pattern-msv1-packets.bin':(MOON,'host/fixtures/pattern-msv1-packets.bin',MOON_HEAD),
    }
    return files


def prepare():
    assert subprocess.check_output(['git','-C',str(SUN),'rev-parse','HEAD'],text=True).strip()==SUN_HEAD
    assert subprocess.check_output(['git','-C',str(MOON),'rev-parse','HEAD'],text=True).strip()==MOON_HEAD
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'experiments/python-gamebub-v124/endpoint/attempts'/f'{stamp}-{uuid.uuid4().hex[:8]}'
    (out/'source').mkdir(parents=True)
    (out/'src').mkdir(); (out/'bin').mkdir(); (out/'out').mkdir()
    copies={}
    for dest,(repo,rel,head) in source_catalog().items():
        actual=(repo/rel).read_bytes(); committed=git_blob(repo,head,rel)
        if actual!=committed: raise ValueError(f'working source differs from pinned Git blob: {repo}/{rel}')
        target=out/dest; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(actual)
        copies[dest]={'repo':str(repo),'git_head':head,'source_path':rel,'sha256':sha_bytes(actual),'git_blob_sha256':sha_bytes(committed),'bytes':len(actual)}
    for rel in ('scripts/cu66-v124/endpoint/packetizer_probe.cpp','scripts/cu66-v124/endpoint/receiver_probe.rs','scripts/cu66-v124/endpoint/run.py'):
        data=(ROOT/rel).read_bytes(); target=out/'src'/pathlib.Path(rel).name; target.write_bytes(data)
        copies['src/'+target.name]={'repo':'moonbub-30fps-study','git_head':MOON_HEAD,'source_path':rel,'sha256':sha_bytes(data),'git_blob_sha256':None,'bytes':len(data),'status':'new probe source (working tree)'}
    j=out/'source/sunshine/receiver-pattern-720x480-420-q65.jpg'
    p=out/'source/sunshine/receiver-pattern-msv1-packets.bin'
    if sha_file(j)!=EXPECTED_JPEG_SHA or sha_file(p)!=EXPECTED_PACKETS_SHA: raise ValueError('pinned shared golden fixture hash mismatch')
    if (out/'source/moonbub/host-pattern-720x480-420-q65.jpg').read_bytes()!=j.read_bytes(): raise ValueError('Moonbub/Sunshine JPEG fixtures differ')
    if (out/'source/moonbub/host-pattern-msv1-packets.bin').read_bytes()!=p.read_bytes(): raise ValueError('Moonbub/Sunshine packet fixtures differ')
    commands={
      'cpp':['g++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-Isource/sunshine','src/packetizer_probe.cpp','source/sunshine/msv1.cpp','-o','bin/packetizer_probe'],
      'rust':['/opt/gamebub-tools/cargo/bin/rustc','+stable','--edition=2021','-D','warnings','src/receiver_probe.rs','-o','bin/receiver_probe'],
      'packetize_1024':['bin/packetizer_probe','--packetize','source/sunshine/receiver-pattern-720x480-420-q65.jpg','out/native-1024.bin',str(FRAME_ID),str(CAPTURE_US),'1024'],
      'packetize_100':['bin/packetizer_probe','--packetize','source/sunshine/receiver-pattern-720x480-420-q65.jpg','out/native-100.bin',str(FRAME_ID),str(CAPTURE_US),'100'],
      'packetize_1':['bin/packetizer_probe','--packetize','source/sunshine/receiver-pattern-720x480-420-q65.jpg','out/native-1.bin',str(FRAME_ID),str(CAPTURE_US),'1'],
      'bounds':['bin/packetizer_probe','--bounds']}
    receipt={'schema':'v124-native-endpoint-attempt-v1','status':'PREPARED_NOT_RUN','attempt_dir':str(out.relative_to(ROOT)),
      'source_snapshots':copies,'source_pins':{'sunshine_git_head':SUN_HEAD,'moonbub_git_head':MOON_HEAD,
       'sunshine_packetizer_sha256':copies['source/sunshine/msv1.cpp']['sha256'],'sunshine_header_sha256':copies['source/sunshine/msv1.h']['sha256'],
       'actual_rust_receiver_sha256':copies['source/moonbub/protocol.rs']['sha256'],
       'input_jpeg_sha256':EXPECTED_JPEG_SHA,'golden_packets_sha256':EXPECTED_PACKETS_SHA},
      'driver_source_sha256':{'packetizer_probe.cpp':copies['src/packetizer_probe.cpp']['sha256'],'receiver_probe.rs':copies['src/receiver_probe.rs']['sha256'],'run.py':copies['src/run.py']['sha256']},
      'commands':commands,'image':{'immutable_id':IMAGE,'tag_for_human_reference':IMAGE_TAG},
      'resource_policy':{'root_grant':'ROOT_V124_ENDPOINT','cpus':2,'memory_bytes':8*1024**3,'memory_swap_bytes':8*1024**3,'network':'none','timeout_seconds':900,'max_active_heavy_jobs':2},
      'scope':'Native serializer and Rust protocol parser/reassembler only; no capture, encode, send, session, ESP-IDF, CPU/Wi-Fi/QSPI/RTL or board claim.',
      'fixture_metadata':{'width':720,'height':480,'jpeg_bytes':len(j.read_bytes()),'chunk_sizes':[1024,100,1],
       'frame_id':FRAME_ID,'capture_us':CAPTURE_US,'packet_framing':'u16 big-endian datagram length then bytes'},
      'outputs':{},'resource_samples':[]}
    write_json(out/'receipt.json',receipt)
    print(json.dumps({'attempt':str(out.relative_to(ROOT)),'status':receipt['status'],'jpeg_sha256':EXPECTED_JPEG_SHA,'golden_packets_sha256':EXPECTED_PACKETS_SHA},indent=2))
    return out


def parse_framed(data):
    packets=[]; at=0
    while at<len(data):
        if at+2>len(data): raise ValueError('incomplete u16 prefix')
        n=int.from_bytes(data[at:at+2],'big'); at+=2
        if at+n>len(data): raise ValueError('truncated framed datagram')
        packets.append(data[at:at+n]); at+=n
    return packets


def frame_packets(packets):
    out=bytearray()
    for p in packets:
        if len(p)>65535: raise ValueError('u16 datagram length overflow')
        out.extend(len(p).to_bytes(2,'big')); out.extend(p)
    return bytes(out)


def packet_id(p): return int.from_bytes(p[8:12],'big')
def with_id(p,ident):
    q=bytearray(p); q[8:12]=ident.to_bytes(4,'big'); return bytes(q)


def make_inside_cases(attempt):
    d=pathlib.Path(attempt); source=d/'source/sunshine/receiver-pattern-720x480-420-q65.jpg'
    driver=d/'bin/packetizer_probe'; frame=source.read_bytes()
    commands=[]
    def packetize(fid,capture,chunk,name):
        dest=d/f'out/native-{name}.bin'
        cmd=[driver,'--packetize',source,dest,str(fid),str(capture),str(chunk)]
        run(cmd); commands.append([str(x) for x in cmd]); return dest.read_bytes()
    streams={size:packetize(FRAME_ID,CAPTURE_US,size,str(size)) for size in (1024,100,1)}
    stream_next=packetize(FRAME_ID+1,CAPTURE_US+1,1024,'next')
    stream_max=packetize(0xffffffff,CAPTURE_US+2,1024,'maxid')
    stream_zero=packetize(0,CAPTURE_US+3,1024,'zeroid')
    golden=(d/'source/sunshine/receiver-pattern-msv1-packets.bin').read_bytes()
    if streams[1024]!=golden: raise AssertionError('native packet stream differs byte-for-byte from shared golden')
    packets=parse_framed(streams[1024]); assert len(packets)==26
    crc=int.from_bytes(packets[0][28:32],'big')
    if crc!=zlib.crc32(frame)&0xffffffff: raise AssertionError('Python independent IEEE CRC differs from C++ header')
    # All mutations operate on actual C++ packetizer outputs.
    p_next=parse_framed(stream_next); p_max=parse_framed(stream_max); p_zero=parse_framed(stream_zero)
    cases={
      'native_golden_1024':(packets,'success',[FRAME_ID]),
      'native_chunk_100':(parse_framed(streams[100]),'success',[FRAME_ID]),
      'native_chunk_1_bounded':(parse_framed(streams[1]),'success',[FRAME_ID]),
      'loss_then_recovery':([packets[0],packets[2]]+p_next,'Sequence',[FRAME_ID+1]),
      'reorder_then_recovery':([packets[1],packets[0]]+p_next,'Sequence',[FRAME_ID+1]),
      'duplicate_then_recovery':([packets[0],packets[0]]+p_next,'Sequence',[FRAME_ID+1]),
      'truncated_final_then_recovery':(packets[:-1]+[packets[-1][:-1]]+p_next,'Bounds',[FRAME_ID+1]),
      'corrupt_final_then_recovery':(packets[:-1]+[bytes(bytearray(packets[-1])[:-1]+bytes([packets[-1][-1]^1]))]+p_next,'Integrity',[FRAME_ID+1]),
      'stale_id_then_recovery':(packets+packets+p_next,'Sequence',[FRAME_ID,FRAME_ID+1]),
      'u32_wrap_max_to_zero':(p_max+p_zero,'success',[0xffffffff,0]),
    }
    reports=[]
    for name,(seq,expected_error,expected_done_ids) in cases.items():
        inp=d/f'out/case-{name}.u16'; recovered=d/f'out/case-{name}.jpg'; events=d/f'out/case-{name}.json'
        inp.write_bytes(frame_packets(seq))
        cmd=[d/'bin/receiver_probe',inp,recovered,events]; run(cmd); commands.append([str(x) for x in cmd])
        ev=json.loads(events.read_text()); errors=[e['error'] for e in ev if e.get('type')=='error']
        done_ids=[e['id'] for e in ev if e.get('type')=='done']
        if expected_error=='success':
            if errors: raise AssertionError(f'{name}: unexpected Rust receiver errors {errors[:3]}')
            if done_ids!=expected_done_ids: raise AssertionError(f'{name}: done IDs {done_ids}')
        else:
            if expected_error not in errors: raise AssertionError(f'{name}: expected backend Error::{expected_error}, got {errors[:5]}')
            if done_ids!=expected_done_ids: raise AssertionError(f'{name}: recovery done IDs {done_ids}')
        outbytes=recovered.read_bytes()
        expected_recovered=frame*len(expected_done_ids)
        if outbytes!=expected_recovered: raise AssertionError(f'{name}: recovered JPEG bytes differ')
        fb=pathlib.Path(str(events)+'.msf1').read_bytes()
        if len(fb)%32 or any(fb[i:i+4]!=b'MSF1' for i in range(0,len(fb),32)):
            raise AssertionError(f'{name}: malformed MSF1 feedback stream')
        feedback_ids=[int.from_bytes(fb[i+8:i+12],'big') for i in range(0,len(fb),32)]
        feedback_status=[fb[i+5] for i in range(0,len(fb),32)]
        if feedback_ids!=done_ids or any(status!=1 for status in feedback_status):
            raise AssertionError(f'{name}: feedback records do not correspond to actual Rust done events')
        reports.append({'name':name,'expected_backend_error':expected_error,'errors':errors,'done_ids':done_ids,
          'input_packets':len(seq),'recovered_bytes':len(outbytes),'recovered_sha256':sha_bytes(outbytes),
          'events_sha256':sha_file(events),'feedback_bytes':len(fb),'feedback_sha256':sha_bytes(fb),
          'feedback_records':len(fb)//32,'feedback_ids':feedback_ids,'feedback_status':feedback_status})
    bound=d/'bin/packetizer_probe'; result=subprocess.run([bound,'--bounds'],capture_output=True,text=True,check=True); commands.append([str(bound),'--bounds'])
    output={'schema':'v124-native-endpoint-run-v1','classification':'HOST_NATIVE_PACKETIZER_TO_ACTUAL_RUST_RECEIVER_ONLY',
      'source_sha256':{p.relative_to(d).as_posix():sha_file(p) for p in sorted((d/'source').rglob('*')) if p.is_file()},
      'driver_sha256':{'packetizer_probe.cpp':sha_file(d/'src/packetizer_probe.cpp'),'receiver_probe.rs':sha_file(d/'src/receiver_probe.rs')},
      'binary_sha256':{'packetizer_probe':sha_file(d/'bin/packetizer_probe'),'receiver_probe':sha_file(d/'bin/receiver_probe')},
      'native_packet_outputs':{str(size):{'bytes':len(data),'sha256':sha_bytes(data),'datagrams':len(parse_framed(data))} for size,data in streams.items()},
      'golden_1024':{'byte_exact':True,'bytes':len(golden),'sha256':sha_bytes(golden),'datagrams':len(packets)},
      'independent_crc32':{'algorithm':'Python zlib IEEE CRC32','header_crc32':f'{crc:08x}','computed_crc32':f'{zlib.crc32(frame)&0xffffffff:08x}','matches':True},
      'bounds_probe':result.stdout.strip(),'cases':reports,'actual_rust_backend_errors_preserved':True,
      'commands':commands,'limits':{'no_capture_encode_send':True,'no_session_ESP_IDF_CPU_WiFi_QSPI_RTL':True,'no_hardware_claim':True}}
    write_json(d/'out/result.json',output)
    return output


def host_mem():
    m={x.split(':')[0]:int(x.split()[1])*1024 for x in pathlib.Path('/proc/meminfo').read_text().splitlines()}
    psi=next(x for x in pathlib.Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    return {'available_bytes':m['MemAvailable'],'psi_full_avg10':float(psi.split('avg10=')[1].split()[0]),
            'combined_used_fraction':(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal'])}


def inside(attempt):
    d=pathlib.Path(attempt).resolve(); receipt=json.loads((d/'receipt.json').read_text())
    for rel,meta in receipt['source_snapshots'].items():
        if sha_file(d/rel)!=meta['sha256']: raise ValueError('snapshot hash drift: '+rel)
    cxx=['g++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-Isource/sunshine',
         'src/packetizer_probe.cpp','source/sunshine/msv1.cpp','-o','bin/packetizer_probe']
    rust=['/opt/gamebub-tools/cargo/bin/rustc','+stable','--edition=2021','-D','warnings',
          'src/receiver_probe.rs','-o','bin/receiver_probe']
    run(cxx,cwd=d); run(rust,cwd=d)
    result=make_inside_cases(d)
    result['compiler_versions']={'g++':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
       'rustc':subprocess.check_output(['/opt/gamebub-tools/cargo/bin/rustc','+stable','--version'],text=True).strip()}
    result['image_id']=IMAGE
    result['compile_commands']=[cxx,rust]
    write_json(d/'out/result.json',result)
    print(json.dumps({'status':'PASS','cases':len(result['cases']),'native_outputs':result['native_packet_outputs'],'compiler_versions':result['compiler_versions']},indent=2))


def launch(attempt):
    d=pathlib.Path(attempt).resolve(); receipt=json.loads((d/'receipt.json').read_text())
    sample=host_mem(); receipt['resource_samples'].append({'phase':'prelaunch',**sample})
    active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
    active_count=sum(n.startswith('gamebub-v') for n in active)
    if sample['available_bytes']<8*1024**3 or sample['psi_full_avg10']>=1 or sample['combined_used_fraction']>=.85:
        raise RuntimeError('host resource prelaunch gate failed')
    if active_count>=2: raise RuntimeError('two heavy-job slots already occupied')
    actual=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',IMAGE],text=True).strip()
    if actual!=IMAGE: raise RuntimeError(f'immutable image ID mismatch: {actual}')
    receipt['status']='RUNNING'; receipt['image']={'immutable_id':IMAGE,'tag_for_human_reference':IMAGE_TAG,'observed_id':actual}
    receipt['resource_samples'][-1].update(active_heavy_jobs=active_count)
    write_json(d/'receipt.json',receipt)
    container='gamebub-v124-endpoint-'+d.name[-8:]
    cmd=['docker','run','--rm','--init','--name',container,'--network','none','--cpus','2','--memory','8g','--memory-swap','8g',
         '--pids-limit','1024','--mount',f'type=bind,src={TOOL_ROOT},dst=/opt/gamebub-tools,readonly',
         '--mount',f'type=bind,src={d},dst=/attempt','-e','CARGO_HOME=/opt/gamebub-tools/cargo',
         '-e','RUSTUP_HOME=/opt/gamebub-tools/rustup','-w','/attempt',IMAGE,
         'timeout','--kill-after=15s','900s','python3','/attempt/src/run.py','--inside','/attempt']
    receipt['docker_command']=cmd; write_json(d/'receipt.json',receipt)
    start=time.monotonic(); proc=subprocess.Popen(cmd,stdout=(d/'out/container.stdout.log').open('w'),
      stderr=subprocess.STDOUT,text=True)
    stop_reason=None; full_psi_high=0; last_sample=0
    while proc.poll() is None:
        elapsed=time.monotonic()-start
        if elapsed-last_sample>=5:
            sample={'phase':'running','elapsed_seconds':elapsed,**host_mem()}
            receipt['resource_samples'].append(sample); write_json(d/'receipt.json',receipt); last_sample=elapsed
            full_psi_high=full_psi_high+1 if sample['psi_full_avg10']>=5 else 0
            if sample['available_bytes']<4*1024**3 or full_psi_high>=2 or sample['combined_used_fraction']>=.90:
                stop_reason='HOST_RESOURCE_PRESSURE'
            if stop_reason: break
        if elapsed>930: stop_reason='WATCHDOG_TIMEOUT'; break
        time.sleep(.5)
    if stop_reason:
        subprocess.run(['docker','stop','--time','10',container],capture_output=True,text=True,timeout=20)
    code=proc.wait(timeout=30)
    receipt=json.loads((d/'receipt.json').read_text()); receipt['exit_code']=code
    receipt['monitor_stop_reason']=stop_reason
    receipt['wall_seconds']=time.monotonic()-start; receipt['resource_samples'].append({'phase':'postrun',**host_mem()})
    if (d/'out/result.json').exists(): receipt['result_sha256']=sha_file(d/'out/result.json')
    receipt['output_sha256']={p.relative_to(d).as_posix():sha_file(p) for p in sorted((d/'out').rglob('*')) if p.is_file()}
    receipt['status']='PASS' if code==0 and stop_reason is None and (d/'out/result.json').exists() else 'FAILED'
    receipt['limitation']='stdout wall time is container/host process time, not ESP32 capture/encode/send timing.'
    write_json(d/'receipt.json',receipt)
    print(json.dumps({'attempt':str(d.relative_to(ROOT)),'status':receipt['status'],'exit_code':code,'wall_seconds':receipt['wall_seconds'],'result_sha256':receipt.get('result_sha256')},indent=2))
    if receipt['status']!='PASS': raise SystemExit(1)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepare-only',action='store_true')
    ap.add_argument('--run',action='store_true')
    ap.add_argument('--root-grant')
    ap.add_argument('--attempt')
    ap.add_argument('--inside')
    a=ap.parse_args()
    if a.inside: inside(a.inside); return
    if a.run:
        if a.root_grant!='ROOT_V124_ENDPOINT': raise SystemExit('explicit ROOT_V124_ENDPOINT grant required')
        if not a.attempt: raise SystemExit('--attempt from a prepared receipt required')
        launch(a.attempt); return
    if a.attempt: raise SystemExit('--attempt is only valid with --run')
    prepare()
if __name__=='__main__': main()
