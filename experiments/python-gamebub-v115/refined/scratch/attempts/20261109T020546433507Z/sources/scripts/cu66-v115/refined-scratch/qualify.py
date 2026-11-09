#!/usr/bin/env python3
"""Three-edge scratch descriptor and registered read-tag qualification, IV115.S1."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v115-refined-scratch'
AREA=ROOT/'experiments/python-gamebub-v115/refined/scratch'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def memory():
    m={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines()};f=next(l for l in Path('/proc/pressure/memory').read_text().splitlines()if l.startswith('full '))
    return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
    recipe=load(SRC/'edit-recipe.json');s=(ROOT/recipe['original']).read_text()
    assert sha(ROOT/recipe['original'])==recipe['original_sha256']
    for e in recipe['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
    assert s==(ROOT/recipe['candidate']).read_text() and sha(ROOT/recipe['candidate'])==recipe['candidate_sha256']
    for e in reversed(recipe['edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'],1)
    assert s==(ROOT/recipe['original']).read_text()
    adapters=load(SRC/'verification/adapters.json')
    for e in adapters['adapters']:
        p=ROOT/e['source'];assert sha(p)==e['source_sha256'];s=p.read_text()
        for a,b in e['edits']:assert s.count(a)==1;s=s.replace(a,b,1)
        assert s==(ROOT/e['path']).read_text() and sha(ROOT/e['path'])==e['sha256']
    return recipe,adapters
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe,adapters=verify()
    parent=ROOT/'experiments/python-gamebub-v115/scratch/results.json';p=load(parent);raw_parent=ROOT/p['path'];assert p['status']=='PASS' and sha(raw_parent)==p['sha256'];frozen=load(raw_parent);assert frozen['status']=='PASS' and frozen['actual_RTL_run']
    for rel,digest in frozen['source_sha256'].items():assert sha(ROOT/rel)==digest,rel
    if not args.run:print('PREPARED_NOT_RUN',recipe['candidate_sha256']);return
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v115-refined-scratch-'+stamp);build.mkdir();mapped='/build/'+build.name
    files=[Path(__file__).resolve(),ROOT/'scripts/cu66-v115/refined-scratch/prepare.py',ROOT/'scripts/cu66-v115/refined-scratch/verification.py',SRC/'edit-recipe.json',SRC/'verification/adapters.json',ROOT/recipe['original'],ROOT/recipe['candidate'],SRC/'verification/clock_adapter.hpp',SRC/'verification/tb_prepare.cpp',SRC/'verification/tb_slot.cpp']+[ROOT/e['path']for e in adapters['adapters']]+[ROOT/e['source']for e in adapters['adapters']]+[parent,raw_parent]+[ROOT/rel for rel in frozen['source_sha256']]
    files=sorted(set(files))
    r=dict(schema='v115-refined-local-tile-write-all128-visible-logical-cycle-pair-v1',status='FAIL',actual_RTL_run=False,backend='Verilator',source_sha256={str(p.relative_to(ROOT)):sha(p)for p in files},commands=[],runs=[],assertions_disabled_or_downgraded=False,added_begin_commit_edges=3,old_public_cycle_equivalence=False,scope='Actual refined scratch against frozen V114, retaining initial V115 three-edge descriptor adapter and all original public/value/owner/request/raw-view checks; additionally compare all128 raw tile words, finite slot conservation, natural pending-write kill/full retry and declared private storage priority fixtures. No extra public cycle, native timing or complete-parent claim.')
    def command(argv,name,cap):
        before=memory();assert before['available_bytes']>=8*1024**3 and before['PSI_full_avg10']<1,before
        container='gamebub-v115-refined-scratch-'+stamp.lower()+'-'+str(len(r['commands']))
        cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
        row=dict(argv=cmd,resource_before=before);r['commands'].append(row);begin=time.monotonic();high=0
        with(out/name).open('w')as log:
            p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
            while p.poll()is None:
                sample=memory();high=high+1 if sample['PSI_full_avg10']>=5 else 0
                if sample['available_bytes']<4*1024**3 or high>=2 or time.monotonic()-begin>cap+20:
                    row['stopped']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
                time.sleep(2)
            row['exit_code']=p.wait(timeout=20)
        assert row['exit_code']==0 and 'stopped'not in row,name
    try:
        for p in files:
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        for e in adapters['adapters']:shutil.copyfile(ROOT/e['path'],build/Path(e['path']).name)
        for p in [SRC/'verification/clock_adapter.hpp',SRC/'verification/tb_prepare.cpp',SRC/'verification/tb_slot.cpp']:shutil.copyfile(p,build/p.name)
        command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module','scratch_probe','--Mdir',mapped+'/obj',*[mapped+'/'+n for n in ('observed_original.sv','observed_candidate.sv','scratch_probe.sv','tb_slot.cpp')]],'compile.log',600)
        assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'obj/Vscratch_probe')
        for seed in (115801,115802):
            name=f'seed-{seed}.log';command([mapped+'/obj/Vscratch_probe',str(seed),mapped+f'/seed-{seed}.jsonl'],name,180)
            lines=[json.loads(x)for x in(out/name).read_text().splitlines()if x.startswith('{')]
            inherited=[x for x in lines if x.get('type')=='v115_scratch_prepare_verdict'];assert len(inherited)==1
            old=inherited[0];assert old['status']=='TEST_PASS' and old['full_transactions']==72 and old['corrupt_response_cases']==128 and old['read_owner_cases']==4
            assert old['pending_cancel_cases']==12 and old['stale_pending_abort_checks']==12 and old['complete_retry_transactions']==24 and old['dc_line_boundary_transactions']==48
            assert old['paired_candidate_extra_edges']==3*old['paired_accepted_descriptors'] and old['poisoned_tuples']==old['paired_accepted_descriptors']
            verdict=lines[-1];assert verdict['type']=='refined_scratch_slot_verdict' and verdict['status']=='TEST_PASS'
            assert verdict['natural_pending_kills']==8 and verdict['same_object_full_retries']==8 and verdict['private_storage_event_fixtures']==9 and verdict['outer_priority_guard_fixtures']==5 and verdict['ready_bank_hold_edges']==2
            assert verdict['visible_raw_words_compared_per_checked_edge']==128 and verdict['new_public_cycles']==0 and verdict['old_assertions_removed']==0
            verdict['inherited_prepare_verdict']=old
            
            import gzip
            for trace in sorted(build.glob(f'seed-{seed}.jsonl*')):
                if trace.is_file():
                    raw=trace.read_bytes();target=out/(trace.name+'.gz');target.write_bytes(gzip.compress(raw,mtime=0));r.setdefault('trace_sha256',{})[target.name]=dict(raw_sha256=sha(trace),sha256=sha(target))
            r['runs'].append(verdict)
        assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p)for p in files};r.update(status='PASS',actual_RTL_run=True)
    except BaseException as e:r['error']=repr(e);raise
    finally:
        r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],path=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('V115_REFINED_SCRATCH_FOCUSED',r['status'],out)
if __name__=='__main__':main()
