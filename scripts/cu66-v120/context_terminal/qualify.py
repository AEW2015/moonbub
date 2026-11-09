#!/usr/bin/env python3
"""Root-only current-context and full32 terminal-owner qualification."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v120-context-terminal'
VER=SRC/'verification'
AREA=ROOT/'experiments/python-gamebub-v120/context-terminal'
POLICY=ROOT/'experiments/python-gamebub-v120/study-policy.json'
BASE=ROOT/'experiments/python-gamebub-v119/handoff.json'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
CFLAGS='-std=c++17 -O2 -Wall -Wextra -Werror'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def rel(path):return str(path.relative_to(ROOT))
def write(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def memory():
    fields={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
    full=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
    return dict(available_bytes=fields['MemAvailable'],psi_full_avg10=float(full.split('avg10=')[1].split()[0]),
        combined_used_ratio=(fields['MemTotal']-fields['MemAvailable']+fields['SwapTotal']-fields['SwapFree'])/(fields['MemTotal']+fields['SwapTotal']))


def verify():
    recipe=load(SRC/'edit-recipe.json')
    old,new=ROOT/recipe['original'],ROOT/recipe['candidate']
    assert sha(old)==recipe['original_sha256'] and sha(new)==recipe['candidate_sha256']
    text=old.read_text()
    for e in recipe['edits']:assert text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
    assert text==new.read_text()
    for e in reversed(recipe['edits']):assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'],1)
    assert text==old.read_text()
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',old.read_text(),re.S):assert block in new.read_text()
    for e in recipe['adapters']:
        old_adapter,new_adapter=ROOT/e['source'],ROOT/e['path'];assert sha(old_adapter)==e['source_sha256'] and sha(new_adapter)==e['sha256']
        text=old_adapter.read_text()
        for before,after in e['edits']:assert text.count(before)==1;text=text.replace(before,after,1)
        assert text==new_adapter.read_text()
    for name,h in recipe['unchanged_verification'].items():assert sha(ROOT/name)==h and (ROOT/name).read_bytes()==(VER/Path(name).name).read_bytes()
    for name,h in recipe['new_verification_files'].items():assert sha(ROOT/name)==h
    manifest=load(BASE);alias='fpga/experiments/cu66-v91b/br88_context.sv';assert manifest['source_origins'][alias]==dict(path=recipe['original'],sha256=recipe['original_sha256'])
    parser=ROOT/manifest['source_origins']['fpga/experiments/cu66-v91/br88_rice_elastic.sv']['path'];assert sha(parser)==manifest['source_origins']['fpga/experiments/cu66-v91/br88_rice_elastic.sv']['sha256']
    assert recipe['added_source_payload_bits']==1 and recipe['added_public_cycles']==0 and recipe['existing_private_value_contract_changes']==0
    return recipe,parser


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');args=ap.parse_args();recipe,parser=verify()
    if not args.run:print('V120_CONTEXT_TERMINAL_PREPARED_NOT_RUN',recipe['candidate_sha256']);return
    assert args.root_grant,'Root coordinating-agent dispatch label required'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v120-context-terminal-'+stamp);build.mkdir();mapped='/build/'+build.name
    vectors=ROOT/'experiments/python-gamebub-v91b/context-vectors/contexts.jsonl.gz'
    files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+
        [ROOT/recipe['original'],parser,vectors,BASE,POLICY,ROOT/'docs/cu66-v120/context-terminal.md']+
        [ROOT/e['source']for e in recipe['adapters']]+[ROOT/n for n in recipe['unchanged_verification']]))
    r=dict(schema='v120-current-context-owned-terminal-focus-v1',status='FAIL',actual_RTL_run=False,image_id=IMAGE,cflags=CFLAGS,
        source_sha256={rel(p):sha(p)for p in files},commands=[],runs=[],memory_samples=[],root_grant=args.root_grant,
        assertions_disabled_or_downgraded=False,old_exact_checker_modified=False,all_old_natural_oracles_retained=True,
        existing_private_value_contract_changes=0,added_source_payload_bits=1,public_latency_delta_cycles=0,
        scope='Current V119 context reference and current Rice parser; generic/specialized old context/count-domain/geometry/error/cancel oracles unchanged. Added full32 prepared count/epoch deposits at actual DC/RUN/LEVEL request edges are not natural frames. One new phase-local unreset payload bit; no physical clock, FPS or hardware claim.',
        candidate_model_reused=False,fresh_candidate_model_required=True)
    began=time.monotonic()
    def persist():write(out/'receipt.json',r)
    def command(argv,name,cap,rtl=False):
        active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert sum(n.startswith('gamebub-v')for n in active)<2,active
        gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
        container='gamebub-v120-context-terminal-'+stamp.lower()+'-'+str(len(r['commands']))
        cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0',
            '--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
        row=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);r['commands'].append(row)
        if rtl:r['actual_RTL_run']=True
        persist();start=time.monotonic();high=0
        with(out/name).open('w')as log:
            process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
            while process.poll()is None:
                sample=dict(command=name,elapsed_seconds=time.monotonic()-start,**memory());r['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
                if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
                    row['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
                time.sleep(2)
            row.update(exit_code=process.wait(timeout=20),wall_seconds=time.monotonic()-start)
        persist();assert row['exit_code']==0 and'resource_stop'not in row,name
    try:
        for p in files:
            q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
        for p in VER.iterdir():
            if p.is_file():shutil.copyfile(p,build/p.name)
        shutil.copyfile(parser,build/'br88_rice_elastic.sv')
        contexts=[json.loads(x)for x in gzip.decompress(vectors.read_bytes()).splitlines()]
        with(build/'context-vectors.txt').open('w')as f:
            for c in contexts:
                expected=c['expected'];f.write(' '.join(map(str,(c['id'],c['blocks'],c['band'],c['k0'],c['k1'],c['event_count'],c['bit_size'],c['data_hex']or'-',c.get('expected_error',0),len(expected))))+'\n')
                for coefficient in expected:f.write(' '.join(map(str,coefficient))+'\n')
        shutil.copyfile(build/'context-vectors.txt',out/'context-vectors.txt')
        command(['verilator','--version'],'version.log',30);assert 'Verilator 5.020'in(out/'version.log').read_text()
        command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--flatten',
            '--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS',CFLAGS,
            '--top-module','context_probe','--Mdir',mapped+'/obj',*[mapped+'/'+n for n in
                ['context_original.sv','context_candidate.sv','context_probe.sv','br88_rice_elastic.sv','tb_terminal.cpp']]],'compile.log',1200)
        assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'obj/Vcontext_probe')
        for seed in (120401,120402):
            name=f'context-{seed}.log';command([mapped+'/obj/Vcontext_probe',mapped+'/context-vectors.txt',str(seed),mapped+f'/geometry-{seed}.tsv'],name,900,rtl=True)
            rows=[json.loads(x)for x in(out/name).read_text().splitlines()if x.startswith('{')]
            edge=next(x for x in rows if x.get('type')=='edge_verdict');domain=next(x for x in rows if x.get('type')=='domain_start_verdict');geometry=next(x for x in rows if x.get('type')=='geometry_verdict')
            inherited=next(x for x in rows if x.get('status')=='TEST_PASS'and x.get('cases')==55);extra=rows[-1]
            assert edge['minimum_success_request_response_gap']==3 and edge['zero_stream_error_gap']==2
            assert domain['cases']==8064 and geometry['cases']==4260918
            assert inherited['configurations']==8 and inherited['directed_checks']==172 and inherited['outputs_per_configuration']==84265
            assert extra['type']=='v120_terminal_owner_verdict'and extra['status']=='TEST_PASS'and extra['prepared_capture_cases']==99216 and extra['random_full32']==98304 and extra['owned_wait_edges']==264576
            assert extra['dc_requests']==extra['run_requests']==extra['level_requests']==33072 and extra['wrapped_true_cases']>0
            assert extra['public_cycle_delta']==0 and extra['prepared_contexts_are_natural_frames']is False
            trace=build/f'geometry-{seed}.tsv';assert sha(trace)=='8254dd9da380dfbffb8446fc8d699e536314572f90c84ba9ef98c5e24353c33d'
            r['runs'].append(dict(seed=seed,edge=edge,domain=domain,geometry=geometry,inherited=inherited,terminal=extra,geometry_raw_sha256=sha(trace)));persist()
        assert r['source_sha256']=={rel(p):sha(p)for p in files};r['status']='PASS'
    except BaseException as error:r['error']=repr(error);raise
    finally:
        for p in build.glob('*.tsv'):
            with p.open('rb')as source,(out/(p.name+'.gz')).open('wb')as dest:
                with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0)as stream:shutil.copyfileobj(source,stream)
        r['wall_seconds']=time.monotonic()-began;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'}
        persist();write(AREA/'results.json',dict(status=r['status'],actual_RTL_run=r['actual_RTL_run'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')))
        print('V120_CONTEXT_TERMINAL',r['status'],out,flush=True)


if __name__=='__main__':main()
