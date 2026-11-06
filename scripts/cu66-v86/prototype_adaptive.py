#!/usr/bin/env python3
"""Rate-only offline selection among six qualified CS86 wire spellings."""
import argparse
import collections
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

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v86'
DEFAULT_WIRE=AREA/'wire-attempts/20261106T135235884295Z-2a73a26a/results.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return str(path.resolve().relative_to(ROOT))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module
def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wire-report',default=str(DEFAULT_WIRE));args=parser.parse_args()
    wire_path=Path(args.wire_report).resolve();wire=json.loads(wire_path.read_text())
    assert wire['status']=='PASS_NATIVE_FULL_FRAME_PARITY' and wire['sources']==457 and wire['received_packets']==2742 and wire['smoke_limit']==0
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'adaptive/attempts'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True)
    sources={**wire['source_sha256'],rel(wire_path):sha(wire_path),rel(wire_path.parent/'frames.jsonl'):sha(wire_path.parent/'frames.jsonl'),rel(Path(__file__)):sha(Path(__file__))}
    assert all(sha(ROOT/name)==digest for name,digest in sources.items())
    binary_hash=wire['artifacts_sha256']['receiver.bin'];assert sha(wire_path.parent/'receiver.bin')==binary_hash
    with tarfile.open(out/'sources.tar.gz','w:gz') as archive:
        for name in sources:
            if not name.endswith('.gz'):archive.add(ROOT/name,arcname=name,recursive=False)
    report=dict(schema='cu66-v86-rate-only-adaptive-v1',status='FAIL',source_sha256=sources,
                wire_report=rel(wire_path),wire_report_sha256=sha(wire_path),source_archive_sha256=sha(out/'sources.tar.gz'),
                receiver_binary_sha256=binary_hash,binary=wire['binary'],commands=[],configuration_order=wire['configurations'],
                tie_rule='Minimum complete packet bytes, then first configuration in qualified CONFIGS order.',
                physical_30fps_proven=False,validated_under10ms_proven=False,esp32_simulated=False,
                scope=['All six complete packets are actually built per source from frozen offline encoded components; this is not a live encoder benchmark.',
                       'Selection minimizes application packet bytes only: no decode-cost, memory, latency or energy objective.',
                       'The same qualified CS86 native software receiver processes one mixed-variant history plus exact immediate replay.',
                       'All-visible choices are outside the COPY-only prospective context timing model. No FPGA/ESP32/transport/latency claim.',
                       'Only CS86 spellings compete; no original CU66 fallback or new opcode/quality mode.'])
    started=time.monotonic();process=None;stderr=None
    try:
        command=['docker','exec','gamebub-cu66-v69-build','sha256sum',wire['binary']];report['commands'].append(command)
        check=subprocess.run(command,text=True,capture_output=True)
        (out/'binary-check.log').write_text(check.stdout+check.stderr);assert check.returncode==0 and check.stdout.split()[0]==binary_hash
        framer=load('cu86_adaptive_framer',ROOT/'scripts/cu66-v86/run_wire.py')
        residual=load('cu86_adaptive_residual',ROOT/'experiments/python-gamebub-v85/residual/data.py')
        controls=load('cu86_adaptive_controls',AREA/'controls/data.py')
        native=load('cu86_adaptive_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
        old_codec=load('cu86_adaptive_old_map',ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
        new_codec=load('cu86_adaptive_group_map',ROOT/'scripts/cu66-v86/prototype_maps.py')
        qualified=[json.loads(line) for line in (wire_path.parent/'frames.jsonl').read_text().splitlines()]
        lookup={(r['cohort'],r['fid'],r['configuration']):r for r in qualified};assert len(lookup)==2742
        c2={(r['cohort'],r['fid']):r for r in map(json.loads,framer.C2_CONTROL.read_text().splitlines())}
        assert framer.CONFIGS==wire['configurations']
        command=['docker','exec','-i','gamebub-cu66-v69-build',wire['binary']];report['commands'].append(command)
        stderr=(out/'receiver.stderr').open('wb');process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr)
        rows=[];previous={};transitions=[];fixtures=[];candidate_total=0
        def receive(cohort,packet):
            process.stdin.write(struct.pack('>II',cohort,len(packet))+packet);process.stdin.flush()
            line=process.stdout.readline();assert line,('receiver terminated',process.poll());return json.loads(line)
        with (out/'frames.jsonl').open('w') as stream:
            for frame,all_visible,original in zip(residual.iter_frames(),controls.iter_frames(),native.iter_frames(),strict=True):
                for field in ('cohort','ordinal','fid','key','packet_sha256','canonical_sha256','hud_sha256','display_sha256'):
                    assert frame[field]==all_visible[field]==original[field]
                assert frame['qmap']==all_visible['qmap'] and frame['hud']==all_visible['hud']
                assert frame['canonical_coefficients_sha256']==all_visible['canonical_coefficients_sha256']
                identity=(frame['cohort'],frame['fid']);control=c2[identity];built=[]
                for config in framer.CONFIGS:
                    source=all_visible if config['kind']=='all_visible' else frame
                    packet,components,method=framer.frame_packet(source,original,control,config,old_codec,new_codec)
                    baseline=lookup[(*identity,config['name'])];digest=hashlib.sha256(packet).hexdigest()
                    assert (len(packet),digest,components,method)==(baseline['wire_bytes'],baseline['packet_sha256'],baseline['components'],baseline['map_method'])
                    built.append((config,packet,baseline));candidate_total+=1
                config,packet,baseline=min(built,key=lambda entry:len(entry[1]))
                decoded=receive(frame['cohort'],packet);assert decoded==baseline['decoded']
                replay=receive(frame['cohort'],packet);assert replay==dict(decoded,replayed=True)
                row=dict(cohort=frame['cohort'],ordinal=frame['ordinal'],fid=frame['fid'],key=frame['key'],
                         configuration=config['name'],kind=config['kind'],cap=config['cap'],wire_bytes=len(packet),
                         packet_sha256=hashlib.sha256(packet).hexdigest(),components=baseline['components'],
                         candidates=[dict(configuration=c['name'],wire_bytes=len(p),packet_sha256=hashlib.sha256(p).hexdigest()) for c,p,_ in built],
                         decoded=decoded,replayed=replay)
                prior=previous.get(frame['cohort'])
                if prior is not None and prior!=config['name']:
                    transitions.append(dict(cohort=frame['cohort'],fid=frame['fid'],previous_configuration=prior,configuration=config['name']))
                    if len(fixtures)<8:
                        name=f'c{frame["cohort"]}-f{frame["fid"]}-{config["name"]}.cs86';(out/name).write_bytes(packet)
                        fixtures.append(dict(path=rel(out/name),packet_sha256=sha(out/name),cohort=frame['cohort'],fid=frame['fid'],configuration=config['name']))
                previous[frame['cohort']]=config['name'];rows.append(row);stream.write(json.dumps(row,separators=(',',':'))+'\n')
                if len(rows)==1 or len(rows)%100==0:print('V86_ADAPTIVE_PROGRESS',len(rows),flush=True)
        assert len(rows)==457 and candidate_total==2742
        process.stdin.close();code=process.wait();stderr.close();assert code==0
        assert sources=={name:sha(ROOT/name) for name in sources}
        comparisons=[]
        for config in framer.CONFIGS:
            differences=[lookup[(r['cohort'],r['fid'],config['name'])]['wire_bytes']-r['wire_bytes'] for r in rows]
            total=sum(lookup[(r['cohort'],r['fid'],config['name'])]['wire_bytes'] for r in rows)
            assert min(differences)>=0
            comparisons.append(dict(reference=config['name'],reference_wire_bytes=total,saved_bytes=stats(differences),
                                    improved=sum(v>0 for v in differences),equal=sum(v==0 for v in differences),regressed=sum(v<0 for v in differences),percent_saved=100*sum(differences)/total))
        original_total=sum(frame['original_packet_bytes'] for frame in qualified if frame['configuration']==framer.CONFIGS[0]['name'])
        report.update(status='PASS_NATIVE_RATE_ONLY_MIXED_HISTORY_AND_REPLAY',native_sources=457,candidates_constructed=2742,
                      accepted_new_packets=457,accepted_exact_replays=457,unique_content_frames=457,receiver_exit_code=code,
                      selected_wire_bytes=stats([r['wire_bytes'] for r in rows]),choices=dict(collections.Counter(r['configuration'] for r in rows)),
                      compatibility_fits_49152=sum(r['wire_bytes']<=49152 for r in rows),cross_variant_transitions=transitions,fixtures=fixtures,
                      paired_comparisons=comparisons,original_CU66_wire_bytes=original_total,
                      original_CU66_saved_bytes=original_total-sum(r['wire_bytes'] for r in rows),
                      artifacts_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='results.json'})
    except BaseException as exc:
        report['failure']=repr(exc)
        if process and process.poll() is None:process.terminate();process.wait()
        if stderr and not stderr.closed:stderr.close()
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started;(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V86_ADAPTIVE_REPORT',out/'results.json',report['status'],flush=True)
    selected=dict(report,selected_report=rel(out/'results.json'))
    with (AREA/'adaptive/results.json').open('x') as stream:stream.write(json.dumps(selected,indent=2)+'\n')


if __name__=='__main__':main()
