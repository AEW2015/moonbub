#!/usr/bin/env python3
"""Actual CS88 mixed AB38/BR88 packets with complete-byte feedback policies."""
import datetime
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import statistics
import struct
import subprocess
import sys
import time
import uuid
import zlib

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v88/wire'
ENTROPY=ROOT/'experiments/python-gamebub-v88/entropy'
CONTAINER='gamebub-cu66-v69-build'
POLICIES=('AB38_control','byte_min','feedback_overhead5','feedback_overhead15','all_BR88')


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result)
    return result


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def select(candidates,baseline_bytes,policy):
    if policy=='AB38_control':return next(c for c in candidates if c['mask']==0)
    if policy=='all_BR88':return max(candidates,key=lambda c:c['mask'])
    if policy=='byte_min':return min(candidates,key=lambda c:(c['wire_bytes'],c['remaining_decisions'],c['mask']))
    if policy not in ('feedback_overhead5','feedback_overhead15'):raise ValueError('unknown policy')
    percent=105 if policy=='feedback_overhead5' else 115
    budget=min(49152,baseline_bytes*percent//100)
    feasible=[c for c in candidates if c['wire_bytes']<=budget]
    if not feasible:raise ValueError('control exceeds negotiated budget')
    return min(feasible,key=lambda c:(c['remaining_decisions'],c['wire_bytes'],c['mask']))


def cs88(packet,qblock):
    header=bytearray(packet[:128]);header[:4]=b'CS88'
    start=128+int.from_bytes(header[36:40],'big')
    struct.pack_into('>I',header,40,len(qblock))
    content=bytes(header)+packet[128:start]+qblock+packet[start+338:-4]
    return content+struct.pack('>I',zlib.crc32(content))


def candidates(frame,native,commitment,qblock,wire,oldmap,groupmap):
    flat=[chunk for plane in frame['variants']['65536'] for chunk in plane]
    assert len(flat)<=3,'whole-plane stream limit'
    result=[]
    for mask in range(1<<len(flat)):
        remaining_decisions=remaining_renorm=plain_bits=plain_values=plain_events=switched=0
        planes=[];at=0
        for plane in frame['variants']['65536']:
            selected=[]
            for chunk in plane:
                plain=bool(mask&(1<<at));at+=1
                selected.append(dict(blocks=chunk['blocks'],data=chunk['br88'] if plain else chunk['data']))
                if plain:
                    switched+=1;plain_bits+=sum(chunk['br88_bits']);plain_values+=sum(chunk['rice_values']);plain_events+=sum(chunk['events'])
                else:
                    remaining_decisions+=sum(chunk['old_decisions']);remaining_renorm+=sum(chunk['old_renorm'])
            planes.append(selected)
        source=dict(frame,variants={'65536':planes})
        packet,components,_=wire.frame_packet(source,native,commitment,dict(kind='copy_group',cap=65536),oldmap,groupmap)
        packet=cs88(packet,qblock)
        components=dict(components,qmap=len(qblock));components['chunk_payloads']=components.pop('AB38_payloads')
        assert sum(components.values())==len(packet)
        result.append(dict(mask=mask,packet=packet,wire_bytes=len(packet),components=components,
                           packet_sha256=hashlib.sha256(packet).hexdigest(),remaining_decisions=remaining_decisions,
                           remaining_renorm=remaining_renorm,BR88_bits=plain_bits,BR88_rice_values=plain_values,
                           BR88_events=plain_events,BR88_chunks=switched))
    return result


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    wire=load('v88_wire86',ROOT/'scripts/cu66-v86/run_wire.py')
    q87=load('v88_q87',ROOT/'scripts/cu66-v87/prototype_quantizers.py')
    qcodec=load('v88_qcodec',ROOT/'scripts/cu66-v87/quantizer_codec.py')
    data=load('v88_new_chunks',ENTROPY/'data.py')
    native=load('v88_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    oldmap=load('v88_old_map',ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
    groupmap=load('v88_group_map',ROOT/'scripts/cu66-v86/prototype_maps.py')
    previous_report=json.loads((ROOT/'experiments/python-gamebub-v87/quantizers/results.json').read_text())
    qualified=ROOT/previous_report['selected_report']
    oldrows={(r['cohort'],r['fid']):r for r in map(json.loads,qualified.with_name('frames.jsonl').read_text().splitlines()) if r['configuration']=='copy_group_cap65536'}
    commitments={(r['cohort'],r['fid']):r for r in map(json.loads,wire.C2_CONTROL.read_text().splitlines())}
    sources=[Path(__file__).resolve(),AREA/'receiver.cpp',ENTROPY/'data.py',ENTROPY/'index.json',ENTROPY/'codec.hpp',ENTROPY/'codec.py',
             ROOT/'scripts/cu66-v86/run_wire.py',ROOT/'scripts/cu66-v87/prototype_quantizers.py',ROOT/'scripts/cu66-v87/quantizer_codec.py',
             ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py',ROOT/'scripts/cu66-v86/prototype_maps.py',qualified,qualified.with_name('frames.jsonl'),wire.C2_CONTROL]
    sources+=sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    for path in sources:
        if path.suffix in ('.py','.cpp','.hpp'):
            dest=out/'sources'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
    report=dict(schema='cu66-v88-mixed-wire-v1',status='FAIL',source_sha256=pins,policies=list(POLICIES),commands=[],
                scope=['Actual complete CS88 packets and native reconstruction, same quantized picture and QM87 accepted cache.',
                       'Policy minimizes remaining observed adaptive decisions under complete-byte budgets. BR88 bit reads are separate actual work, not zero-time decoding.',
                       'Host components are pre-encoded; no live host30fps, ESP32, physical FPGA or calibrated timing claim.'],physical_30fps_proven=False,validated_under10ms_proven=False)
    binary='/build/v88-wire-'+stamp;processes={};rows=[];qcache={};started=time.monotonic()
    try:
        command=['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'receiver.cpp'),'-o',binary]
        compiled=subprocess.run(command,capture_output=True,text=True);(out/'compile.log').write_text(compiled.stdout+compiled.stderr)
        report['commands'].append(dict(argv=command,observed_exit_code=compiled.returncode));assert compiled.returncode==0,compiled.stderr
        command=['docker','cp',CONTAINER+':'+binary,str(out/'receiver.bin')]
        copied=subprocess.run(command,capture_output=True,text=True);(out/'copy.log').write_text(copied.stdout+copied.stderr)
        report['commands'].append(dict(argv=command,observed_exit_code=copied.returncode));assert copied.returncode==0
        for name in POLICIES:
            log=(out/(name+'.stderr')).open('wb');command=['docker','exec','-i',CONTAINER,binary]
            report['commands'].append(dict(argv=command));processes[name]=(subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log),log)
        with (out/'frames.jsonl').open('w') as output,(out/'candidates.jsonl').open('w') as all_output:
            for ordinal,(frame,original) in enumerate(zip(data.iter_frames(),native.iter_frames(),strict=True)):
                ident=frame['cohort'],frame['fid'];ground=oldrows[ident]
                assert all(frame[k]==original[k]==ground[k] for k in ('cohort','fid','ordinal','key'))
                operations=[1 if h else 0 if not frame['key'] and frame['zero_mask'][t]=='1' else 2 for t,h in enumerate(original['hidden_mask'])]
                scales=qcodec.unpacked(frame['qmap'],1350);previous=None if frame['key'] else qcache.get(frame['cohort'])
                qblock=qcodec.encode(scales,operations,previous);qcache[frame['cohort']]=qcodec.decode(qblock,operations,previous)
                oldpacket,_,_=wire.frame_packet(frame,original,commitments[ident],dict(kind='copy_group',cap=65536),oldmap,groupmap)
                oldpacket=q87.replace_quantizers(oldpacket,qblock)
                assert hashlib.sha256(oldpacket).hexdigest()==ground['packet_sha256'],'qualified CS87 control bytes'
                options=candidates(frame,original,commitments[ident],qblock,wire,oldmap,groupmap)
                baseline=options[0];assert baseline['wire_bytes']==ground['wire_bytes']
                for option in options:
                    all_output.write(json.dumps(dict(cohort=frame['cohort'],fid=frame['fid'],ordinal=frame['ordinal'],**{k:v for k,v in option.items() if k!='packet'}),separators=(',',':'))+'\n')
                for name in POLICIES:
                    chosen=select(options,baseline['wire_bytes'],name);packet=chosen['packet'];process=processes[name][0]
                    process.stdin.write(struct.pack('>II',frame['cohort'],len(packet))+packet);process.stdin.flush();decoded=json.loads(process.stdout.readline())
                    assert decoded['accepted'] and not decoded['replayed'],(name,ident,decoded)
                    for key in ('canonical_sha256','hud_sha256','display_sha256','coefficient_sha256','root','seal','generation','fid'):
                        assert decoded[key]==ground['decoded'][key],(name,ident,key)
                    assert decoded['wire_bytes']==len(packet)
                    row=dict(policy=name,cohort=frame['cohort'],fid=frame['fid'],ordinal=frame['ordinal'],key=frame['key'],CS87_wire_bytes=baseline['wire_bytes'],
                             original_packet_bytes=frame['packet_bytes'],CS87_decisions=baseline['remaining_decisions'],CS87_renorm=baseline['remaining_renorm'],
                             qmap_sha256=hashlib.sha256(qblock).hexdigest(),fits_49152=len(packet)<=49152,decoded=decoded,
                             **{k:v for k,v in chosen.items() if k!='packet'})
                    output.write(json.dumps(row,separators=(',',':'))+'\n');rows.append(row)
                    if frame['cohort'] in (0,3) and frame['ordinal'] in (0,1,2) or ident==(3,50):
                        (out/f"c{frame['cohort']}-f{frame['fid']}-{name}.cs88").write_bytes(packet)
                if ordinal%50==0:print('V88_WIRE_PROGRESS',ordinal+1,flush=True)
        report['receiver_exit_codes']={}
        for name,(process,log) in processes.items():
            process.stdin.close();code=process.wait();log.close();report['receiver_exit_codes'][name]=code;assert code==0
        assert len(rows)==457*len(POLICIES)
        summaries=[]
        for name in POLICIES:
            selected=[r for r in rows if r['policy']==name]
            summaries.append(dict(policy=name,sources=len(selected),wire_bytes=stats([r['wire_bytes'] for r in selected]),
                                  wire_delta_vs_CS87=sum(r['wire_bytes']-r['CS87_wire_bytes'] for r in selected),
                                  remaining_adaptive_decisions=sum(r['remaining_decisions'] for r in selected),
                                  eliminated_adaptive_decisions=sum(r['CS87_decisions']-r['remaining_decisions'] for r in selected),
                                  remaining_renorm=sum(r['remaining_renorm'] for r in selected),BR88_bits=sum(r['BR88_bits'] for r in selected),
                                  BR88_chunks=sum(r['BR88_chunks'] for r in selected),fits_49152=sum(r['fits_49152'] for r in selected)))
        assert pins=={name:sha(ROOT/name) for name in pins},'executed sources changed'
        report.update(status='PASS_FULL_NATIVE_MIXED_CODEC_PARITY',native_sources=457,received_packets=len(rows),summaries=summaries,binary=binary)
    finally:
        for process,log in processes.values():
            if process.poll() is None:process.terminate();process.wait()
            if not log.closed:log.close()
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('V88_WIRE_REPORT',out/'results.json',report['status'],flush=True)
    (AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')


if __name__=='__main__':main()
