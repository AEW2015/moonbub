#!/usr/bin/env python3
"""Strict Root-dispatched paired proof for held-tuple domain derivation."""
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
SRC=ROOT/'fpga/experiments/cu66-v116b-domain'
AREA=ROOT/'experiments/python-gamebub-v116/domain-b'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
CFLAGS='-std=c++17 -O2 -Wall -Wextra -Werror'
NATIVE=ROOT/'experiments/python-gamebub-v116/native-study/native/20261109T055009881384Z'
GIB=1024**3


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def write(p,x):
    temp=p.with_name(p.name+'.tmp');temp.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');temp.replace(p)


def verify():
    recipe=json.loads((SRC/'edit-recipe.json').read_text())
    for entry in [recipe['production']]+recipe['adapters']:
        old,new=ROOT/entry['original'],ROOT/entry['candidate']
        assert sha(old)==entry['original_sha256'] and sha(new)==entry['candidate_sha256']
        text=old.read_text()
        for edit in entry['edits']:
            assert text.count(edit['before'])==1;text=text.replace(edit['before'],edit['after'],1)
        assert text==new.read_text()
        for edit in reversed(entry['edits']):
            assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'],1)
        assert text==old.read_text()
    old=ROOT/recipe['production']['original'];new=ROOT/recipe['production']['candidate']
    assert old.read_text().split(');',1)[0]==new.read_text().split(');',1)[0]
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',old.read_text(),re.S):assert block in new.read_text()
    assert sha(SRC/'meta_stage_probe.sv')==recipe['probe_sha256']
    ports=recipe['probe_ports_reference'];assert sha(ROOT/ports['path'])==ports['sha256']
    expected=[p['name']for p in json.loads((ROOT/ports['path']).read_text())['stage']if p['direction']=='output']
    assert recipe['compared_public_outputs']==expected
    probe=(SRC/'meta_stage_probe.sv').read_text()
    for name in expected:assert probe.count('(old_'+name+'!='+name+')')==1
    assert 'always @(posedge clk or negedge clk)assert(!mismatch)' in probe
    assert 'domain_shadow_seen<=0' not in new.read_text()
    assert (SRC/'tb_stage.frozen.cpp').read_bytes()==(ROOT/'fpga/experiments/cu66-v107-meta-flags/verification/tb_stage.cpp').read_bytes()
    assert recipe['declared_public_cycle_delta']==0 and recipe['all_original_SVA_blocks_text_exact']
    return recipe


def memory():
    raw=Path('/proc/meminfo').read_text();m={x.split(':')[0]:int(x.split()[1])*1024 for x in raw.splitlines()}
    pressure=Path('/proc/pressure/memory').read_text();full=next(x for x in pressure.splitlines()if x.startswith('full '))
    return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(full.split('avg10=')[1].split()[0]),
                combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']),meminfo=raw,memory_pressure=pressure)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');ap.add_argument('--legacy-exhaustive',action='store_true')
    args=ap.parse_args();recipe=verify()
    if not args.run:print('V116B_DOMAIN_PREPARED_NOT_RUN',recipe['production']['candidate_sha256']);return
    assert args.root_grant,'Root heavy-slot grant required'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v116b-domain-'+stamp);build.mkdir();mapped='/build/'+build.name
    files=sorted(set([p for p in SRC.iterdir()if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+
                     [ROOT/e['original']for e in [recipe['production']]+recipe['adapters']]+[ROOT/recipe['probe_ports_reference']['path'],
                      AREA/'preparation.json',ROOT/'docs/cu66-v116/domain-b.md',NATIVE/'receipt.json',NATIVE/'reports/route-setup-paths.rpt']))
    report=dict(schema='v116b-held-domain-complete-public-exact-pair-v1',status='RUNNING',actual_RTL_run=False,backend='Verilator 5.020',image_id=IMAGE,
                root_grant=args.root_grant,source_sha256={rel(p):sha(p)for p in files},commands=[],runs=[],
                strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,original_assertions_retained=True,
                declared_public_cycle_delta=0,compared_public_outputs=recipe['compared_public_outputs'],pair_skipped_edges=0,
                production=recipe['production'],legacy_bench_byte_exact=True,legacy_exhaustive=bool(args.legacy_exhaustive),
                cflags=CFLAGS,limits=['Exact2-state public behavior every evaluated edge, including invalid and warm-kill views.','Unowned4-state initialization before the first accepted tuple remains unspecified.','No physical timing exception, routed timing improvement, CDC, hardware or throughput claim.'],
                optimization_note='C++ O2 changes host speed only; no modeled-cycle skipping.')
    began=time.monotonic()
    def persist():write(out/'receipt.json',report)
    def command(argv,name,cap,rtl=False):
        gate=memory();assert gate['available_bytes']>=8*GIB and gate['PSI_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
        container='gamebub-v116b-domain-'+stamp.lower()+'-'+str(len(report['commands']))
        cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
        record=dict(argv=cmd,log=name,timeout_seconds=cap,resource_before=gate,simulation=rtl);report['commands'].append(record)
        if rtl:report['actual_RTL_run']=True
        persist()  # Persist true BEFORE any RTL simulation is invoked.
        started=time.monotonic();process=None;high=0
        try:
            with(out/name).open('w')as log,(out/(name+'.resources.jsonl')).open('w')as samples:
                process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
                while process.poll()is None:
                    sample=dict(elapsed_seconds=time.monotonic()-started,**memory());samples.write(json.dumps(sample,sort_keys=True)+'\n');samples.flush()
                    high=high+1 if sample['PSI_full_avg10']>=5 else 0
                    if sample['available_bytes']<4*GIB or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
                        record['resource_stop']=sample;raise RuntimeError('DOMAIN_RESOURCE_STOP_OR_WATCHDOG '+name)
                    time.sleep(1)
                record['exit_code']=process.wait(timeout=15);assert record['exit_code']==0,name
        finally:
            if process is not None and process.poll()is None:
                stopped=subprocess.run(['docker','stop','--time','3',container],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=12);(out/(name+'.stop.log')).write_bytes(stopped.stdout)
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
            record.update(wall_seconds=time.monotonic()-started,resource_after=memory());persist()
    try:
        for p in files:
            snap=out/'sources'/p.relative_to(ROOT);snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snap)
        names=['domain_original.sv','domain_candidate.sv','meta_stage_probe.sv','tb_domain.cpp','tb_stage.frozen.cpp']
        for name in names:shutil.copyfile(SRC/name,build/name)
        report['compiled_source_sha256']={name:sha(build/name)for name in names}
        command(['verilator','--version'],'version.log',30);assert 'Verilator 5.020' in(out/'version.log').read_text()
        command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','--top-module','meta_stage_probe','--Mdir',mapped+'/obj','-CFLAGS',CFLAGS,
                 *[mapped+'/'+n for n in names if n!='tb_stage.frozen.cpp']],'compile.log',900)
        assert '%Warning-'not in(out/'compile.log').read_text();report['binary_sha256']=sha(build/'obj/Vmeta_stage_probe')
        for seed in (116851,116852):
            name='simulation-'+str(seed)+'.log'
            command([mapped+'/obj/Vmeta_stage_probe',str(seed),mapped+'/events-'+str(seed)+'.jsonl',str(int(args.legacy_exhaustive))],name,600,rtl=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()if line.startswith('{')]
            focused=[r for r in rows if r.get('type')=='v116b_domain_verdict'];assert len(focused)==1
            f=focused[0];v=rows[-1]
            assert f['status']==v['status']=='TEST_PASS'and f['signed16_qscale_values']==262144 and f['warm_kill_cases']==1680 and f['raw_checks']>500000
            assert f['paired_evaluations']>=f['focused_edges']*3
            assert v['simultaneous_replace']>1000 and v['held_edges']>1000 and v['flushes']>1000 and v['stalled_final_fences']>0
            if args.legacy_exhaustive:assert v['helper_cases']==32768 and v['metadata_cases']==67108864 and v['domain_cases']==262144
            report['runs'].append(dict(seed=seed,focused_verdict=f,frozen_legacy_verdict=v))
            persist()
        assert report['source_sha256']=={rel(p):sha(p)for p in files},'sources changed during proof'
        report.update(status='PASS',frozen_after_focused_PASS=True)
    except BaseException as exc:report.update(status='FAIL',error_class=type(exc).__name__,error=str(exc));raise
    finally:
        for p in sorted(build.glob('events-*.jsonl*')):
            if p.is_file():(out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
        report['wall_seconds']=time.monotonic()-began
        report['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'}
        persist();write(AREA/'results.json',dict(status=report['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')))
        print('V116B_DOMAIN_FOCUSED',report['status'],out,flush=True)


if __name__=='__main__':main()
