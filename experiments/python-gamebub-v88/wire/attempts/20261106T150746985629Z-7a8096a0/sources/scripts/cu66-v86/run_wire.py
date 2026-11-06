#!/usr/bin/env python3
"""Build actual CS86 packets and verify them with an independent native receiver."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import struct
import subprocess
import sys
import tarfile
import time
import uuid
import zlib

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v86'
CONTAINER='gamebub-cu66-v69-build'
CAPS=(256,65536)
CONFIGS=[dict(name=f'{kind}_cap{cap}',kind=kind,cap=cap) for cap in CAPS for kind in ('copy_v2','copy_group','all_visible')]
PREFIX=struct.Struct('>4sBBBBIIQHHHHIIIII')
C2_CONTROL=ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
CONTEXT=hashlib.sha256(b'{"geometry":[720,480,5400,1350,1350],"granularity":16,"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"}').digest()
MASK=bytes.fromhex('e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result)
    return result


def stats(values):
    return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def frame_packet(frame,native,control,config,old_codec,new_codec):
    cap=config['cap'];kind=config['kind']
    operations=[1 if hidden else 0 if kind!='all_visible' and not frame['key'] and zero=='1' else 2
                for hidden,zero in zip(native['hidden_mask'],frame['zero_mask'],strict=True)]
    if kind=='copy_v2':
        nested=old_codec.encode(operations,native['hidden_mask'],key=frame['key'])
        method,mode=nested[5],nested[20:]
    else:
        method,mode=new_codec.encode_body(operations,native['hidden_mask'],key=frame['key'])
    encoded=bytearray();chunks=0;ab_bytes=0
    for plane in frame['variants'][str(cap)]:
        encoded.extend(struct.pack('>I',len(plane)))
        for chunk in plane:
            encoded.extend(struct.pack('>II',chunk['blocks'],len(chunk['data'])));encoded.extend(chunk['data'])
            chunks+=1;ab_bytes+=len(chunk['data'])
    assert len(frame['qmap'])==338 and len(mode)<=976
    prefix=PREFIX.pack(b'CS86',1,int(frame['key']),16,method,frame['fid'],frame['refid'],frame['ordinal']+1,
                       720,480,frame['block_size'],0,cap,len(mode),338,len(frame['hud']),len(encoded))
    assert len(prefix)==52
    # Context/mask are fixed by CS86. The receiver obtains previous root from
    # accepted state and computes HUD semantics; the C2 seal binds both.
    header=prefix+bytes.fromhex(control['root'])+bytes.fromhex(control['seal'])+bytes(12)
    assert len(header)==128
    body=header+mode+frame['qmap']+bytes(encoded)+frame['hud']
    packet=body+struct.pack('>I',zlib.crc32(body));assert len(packet)<=2*1024*1024
    counts=dict(header=128,mode_body=len(mode),qmap=338,chunk_directory=12+8*chunks,
                AB38_payloads=ab_bytes,HUD=len(frame['hud']),outer_CRC=4)
    assert sum(counts.values())==len(packet)
    return packet,counts,method


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=0);args=parser.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'wire-attempts'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True)
    index=json.loads((ROOT/'experiments/python-gamebub-v85/residual/index.json').read_text())
    sources=[Path(__file__).resolve(),AREA/'receiver.cpp',ROOT/'experiments/python-gamebub-v85/residual/data.py',ROOT/'experiments/python-gamebub-v85/residual/index.json',
             AREA/'controls/data.py',AREA/'controls/index.json',ROOT/'scripts/cu66-v86/prototype_maps.py',
             ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py',
             ROOT/'experiments/python-gamebub-v82/native/data.py',ROOT/'experiments/python-gamebub-v82/native/index.json',C2_CONTROL]
    sources+=sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    sources+=sorted((ROOT/'experiments/python-gamebub-v82/native/data').glob('*.gz'))
    # The residual loader validates its compressed/raw input internally; bind the
    # actual data path without assuming the collector's report layout.
    sources += sorted((ROOT/'experiments/python-gamebub-v85/residual/attempts').glob('*/data.bin.gz'))
    sources += sorted((AREA/'controls/attempts').glob('*/data.bin.gz'))
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(out/'sources.tar.gz','w:gz') as tar:
        for path in sources:
            if path.suffix!='.gz':tar.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
    report=dict(schema='cu66-v86-full-wire-v1',status='FAIL',source_sha256=pins,
                source_archive_sha256=sha(out/'sources.tar.gz'),smoke_limit=args.limit,
                residual_index_sha256=sha(ROOT/'experiments/python-gamebub-v85/residual/index.json'),configurations=CONFIGS,controls_index_sha256=sha(AREA/'controls/index.json'),research_packet_limit=2*1024*1024,
                compatibility_packet_limit=49152,timing_is_FPGA=False,commands=[])
    binary='/build/v86-receiver-'+stamp;processes={};started=time.monotonic()
    try:
        command=['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'receiver.cpp'),'-o',binary]
        report['commands'].append(command);compiled=subprocess.run(command,capture_output=True,text=True)
        (out/'compile.log').write_text(compiled.stdout+compiled.stderr);assert compiled.returncode==0,'native receiver compile'
        copied=subprocess.run(['docker','cp',f'{CONTAINER}:{binary}',str(out/'receiver.bin')],capture_output=True,text=True)
        (out/'copy.log').write_text(copied.stdout+copied.stderr);assert copied.returncode==0
        residual=load('cu86_residual_data',ROOT/'experiments/python-gamebub-v85/residual/data.py')
        controls_data=load('cu86_controls_data',AREA/'controls/data.py')
        native=load('cu86_native_data',ROOT/'experiments/python-gamebub-v82/native/data.py')
        codec=load('cu86_mode_codec',ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
        group_codec=load('cu86_group_codec',ROOT/'scripts/cu66-v86/prototype_maps.py')
        controls={(r['cohort'],r['fid']):r for r in map(json.loads,C2_CONTROL.read_text().splitlines())}
        previous_roots={};rows=[];count=0
        for config in CONFIGS:
            name=config['name']
            log=(out/f'receiver-{name}.stderr').open('wb');command=['docker','exec','-i',CONTAINER,binary]
            report['commands'].append(command)
            process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log)
            processes[name]=(process,log)
        with (out/'frames.jsonl').open('w') as stream:
            for frame,all_visible,original in zip(residual.iter_frames(),controls_data.iter_frames(),native.iter_frames(),strict=True):
                if args.limit and count>=args.limit:break
                for field in ('cohort','ordinal','fid','key','packet_sha256','canonical_sha256','hud_sha256','display_sha256'):
                    assert frame[field]==all_visible[field]==original[field],('input identity',field)
                assert frame['qmap']==all_visible['qmap'] and frame['hud']==all_visible['hud']
                assert frame['canonical_coefficients_sha256']==all_visible['canonical_coefficients_sha256']
                control=dict(controls[(frame['cohort'],frame['fid'])])
                control['previous_root']=previous_roots.get(frame['cohort'],'00'*32)
                previous_roots[frame['cohort']]=control['root']
                pending={}
                for config in CONFIGS:
                    name=config['name'];input_frame=all_visible if config['kind']=='all_visible' else frame
                    packet,counts,method=frame_packet(input_frame,original,control,config,codec,group_codec)
                    pending[name]=(packet,counts,method)
                    process=processes[name][0];process.stdin.write(struct.pack('>II',frame['cohort'],len(packet))+packet);process.stdin.flush()
                for config in CONFIGS:
                    name=config['name'];packet,counts,method=pending[name];process=processes[name][0];line=process.stdout.readline()
                    assert line,('receiver ended',name,process.poll())
                    decoded=json.loads(line);assert decoded['accepted'],decoded
                    assert not decoded['replayed'] and decoded['fid']==frame['fid']
                    for field in ('canonical_sha256','hud_sha256','display_sha256'):
                        assert decoded[field]==frame[field],('native picture mismatch',name,field)
                    assert decoded['coefficient_sha256']==frame['canonical_coefficients_sha256']
                    assert decoded['root']==control['root'] and decoded['seal']==control['seal']
                    assert decoded['wire_bytes']==len(packet) and decoded['generation']==frame['ordinal']+1
                    row=dict(configuration=name,kind=config['kind'],cap=config['cap'],map_method=method,
                             cohort=frame['cohort'],ordinal=frame['ordinal'],fid=frame['fid'],key=frame['key'],
                             wire_bytes=len(packet),original_packet_bytes=frame['packet_bytes'],
                             byte_delta=len(packet)-frame['packet_bytes'],fits_49152=len(packet)<=49152,
                             components=counts,packet_sha256=hashlib.sha256(packet).hexdigest(),decoded=decoded)
                    stream.write(json.dumps(row,separators=(',',':'))+'\n');rows.append(row)
                    if ((frame['cohort']==0 and frame['ordinal'] in (0,1)) or (frame['cohort']==3 and frame['ordinal'] in (0,1)) or (frame['cohort']==3 and frame['fid']==50)) and config['kind']=='copy_group':
                        fixture=out/f"c{frame['cohort']}-f{frame['fid']}-{name}.cs86";fixture.write_bytes(packet)
                count+=1
                if count==1 or count%25==0:print('V86_WIRE_PROGRESS',count,flush=True)
        report['receiver_exit_codes']={}
        for name,(process,log) in processes.items():
            process.stdin.close();code=process.wait();log.close();report['receiver_exit_codes'][name]=code;assert code==0
        assert count==(args.limit or 457)
        assert pins=={name:sha(ROOT/name) for name in pins},'executed sources changed'
        summaries=[]
        for config in CONFIGS:
            selected=[r for r in rows if r['configuration']==config['name']]
            summaries.append(dict(configuration=config['name'],kind=config['kind'],cap=config['cap'],sources=len(selected),
                                  wire_bytes=stats([r['wire_bytes'] for r in selected]),
                                  original_packet_bytes=stats([r['original_packet_bytes'] for r in selected]),
                                  paired_byte_delta=stats([r['byte_delta'] for r in selected]),
                                  smaller=sum(r['byte_delta']<0 for r in selected),equal=sum(r['byte_delta']==0 for r in selected),
                                  larger=sum(r['byte_delta']>0 for r in selected),fits_49152=sum(r['fits_49152'] for r in selected)))
        report.update(status='PASS_SMOKE_ONLY' if args.limit else 'PASS_NATIVE_FULL_FRAME_PARITY',sources=count,received_packets=len(rows),summaries=summaries,binary=binary,
                      artifacts_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='results.json'},
                      scope=['Actual compact header/embeddedmap/qmap/chunk framing/AB38/HUD/CRC bytes all included.',
                             'Native full coefficient/canonical/HUD/display/root/seal parity; no original CU66 repack adapter.',
                             'Research receiver2MiB cap is not the existing FPGA receive limit.49152compatibility reported separately.',
                             'New framing and content commitment differ from original CU66. All-visible controls use the same new envelope/encoder and are actually receiver-tested.',
                             'No FPGA/ESP32 timing, sustained30fps, sub10ms or HEVC/AV1 superiority proof.'])
    except BaseException as exc:
        report['failure']=repr(exc)
        for process,log in processes.values():
            if process.poll() is None:process.terminate();process.wait()
            if not log.closed:log.close()
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V86_WIRE_REPORT',out/'results.json',report['status'],flush=True)


if __name__=='__main__':main()
