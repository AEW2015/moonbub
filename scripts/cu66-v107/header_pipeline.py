#!/usr/bin/env python3
"""Compare a fresh HEADER candidate with immutable, same-seed actual elastic results.

Only the HEADER candidate is compiled/run here. Control streams come from the
already-qualified two-seed elastic candidate; they are never counted as fresh runs.
"""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v107/header-pipeline'
sys.path.insert(0, str(ROOT / 'scripts/cu66-v100'))
from run_rtl import resources


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def main():
    focus = json.loads((ROOT/'experiments/python-gamebub-v107/header/results.json').read_text())
    assert focus['status'] == 'PASS' and focus['actual_RTL_run']
    qualified = ROOT/'experiments/python-gamebub-v107/elastic-pipeline/results.json'
    old = json.loads(qualified.read_text())
    assert old['status']=='PASS' and old['actual_RTL_run']
    baseline = ROOT/old['selected_report']
    recorded = json.loads(baseline.read_text())
    assert {k:v for k,v in old.items() if k!='selected_report'} == recorded
    contract_path = ROOT/'experiments/python-gamebub-v107/elastic-pipeline/native-input-contract.json'
    contract=json.loads(contract_path.read_text())
    assert sha(baseline)==contract['canonical_receipt_sha256']
    bench=ROOT/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
    candidate=ROOT/'fpga/experiments/cu66-v107-header/cs88_admission_v91i2a.sv'
    original=ROOT/'fpga/experiments/cu66-v107-quant/cs88_admission_v91i2a.sv'
    for name,digest in old['source_sha256'].items():assert sha(ROOT/name)==digest,name
    for name,digest in focus['source_sha256'].items():assert sha(ROOT/name)==digest,name
    sources=[ROOT/name for name in contract['rtl_sources']+contract['include_headers']]
    assert original in sources
    sources[sources.index(original)]=candidate
    assert len(sources)==18 and len([x for x in sources if x.suffix=='.sv'])==17
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v107-header-pipeline-'+stamp);build.mkdir()
    mapped='/build/'+build.name
    inputs={}
    for item in ('cases.tsv','transform_tiles.tsv','canonical_goldens.tsv'):
        meta=old['inputs'][item];source=ROOT/meta['source']
        assert sha(source)==meta['sha256']
        target=out/item
        target.write_bytes(gzip.decompress(source.read_bytes()) if source.suffix=='.gz' else source.read_bytes())
        assert sha(target)==meta['expanded_sha256']
        inputs[item]=dict(meta)
    files=sorted(set(sources+[bench,Path(__file__).resolve(),contract_path,qualified]))
    r=dict(schema='v107-header-zero-extra-cycle-canonical-v1',status='FAIL',
        baseline_reference=dict(path=str(baseline.relative_to(ROOT)),sha256=sha(baseline)),
        baseline_reused_actual_RTL=True,baseline_recompiled_or_rerun=False,
        source_sha256={str(x.relative_to(ROOT)):sha(x) for x in files},inputs=inputs,
        seeds=old['seeds'],runs=[],commands=[],actual_RTL_run=False,
        newly_executed_candidate_case_profiles=0,newly_executed_candidate_directed_checks=0,
        full_frame_publication=False,hardware_contact=False,
        limits=['Same-seed control streams reused from actual qualified elastic RTL; no new control execution counted.',
                'Every candidate case/profile/error/cancellation/ownership/golden check remains active.',
                'Exact events/cycles/canonical bytes required; no timing, hardwareFPS or under10ms conclusion.'])
    began=time.monotonic()
    def command(argv,name,cap):
        record=dict(argv=argv,timeout_seconds=cap,resource_gate=resources());r['commands'].append(record)
        with (out/name).open('w') as f:proc=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,timeout=cap+15)
        record['exit_code']=proc.returncode
        assert proc.returncode==0,name
    try:
        for f in files:
            target=out/'sources'/f.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
        snapshot=lambda f:str(out/'sources'/f.relative_to(ROOT))
        command(['docker','exec','gamebub-cu66-v69-build','timeout','--kill-after=5s','600s',
                 'verilator','--cc','--exe','--build','-j','1','--output-split','10000',
                 '--output-split-cfuncs','1000','--assert','-Wall','--public-flat-rw',
                 '--language','1800-2017','--top-module','cs88_pipeline_v91k','--Mdir',mapped,
                 '-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),
                 '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror -DELASTIC=1',
                 *[snapshot(f) for f in sources if f.suffix=='.sv'],snapshot(bench)],'compile.log',600)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['docker','exec','gamebub-cu66-v69-build','sha256sum',mapped+'/Vcs88_pipeline_v91k'],'binary.log',30)
        r['binary_sha256']=(out/'binary.log').read_text().split()[0]
        for run in old['runs']:
            seed=run['seed'];prefix='candidate-'+str(seed)
            events=out/(prefix+'-events.jsonl');canonical=out/(prefix+'-canonical.tsv')
            command(['docker','exec','gamebub-cu66-v69-build','timeout','--kill-after=5s','900s',
                     mapped+'/Vcs88_pipeline_v91k',str(out/'cases.tsv'),str(out/'transform_tiles.tsv'),
                     str(out/'canonical_goldens.tsv'),str(seed),str(events),str(canonical)],prefix+'-simulation.jsonl',900)
            records=[json.loads(l) for l in (out/(prefix+'-simulation.jsonl')).read_text().splitlines()]
            verdict=[v for v in records if v['type']=='verdict']
            assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS' and verdict[0]['cases']==22 and verdict[0]['directed_checks']==21
            assert sha(out/(prefix+'-simulation.jsonl'))==sha(baseline.parent/(prefix+'-simulation.jsonl')),'exact stdout/cycle divergence'
            row=dict(seed=seed,verdict=verdict[0],exact_stdout_events_cycles_and_canonical=True,artifacts={})
            for key,path in [('events',events),('canonical_actual',canonical)]:
                meta=run['variants']['candidate'][key]
                reference=baseline.parent/meta['path'];assert sha(reference)==meta['sha256']
                original_data=gzip.decompress(reference.read_bytes());assert hashlib.sha256(original_data).hexdigest()==meta['raw_sha256']
                assert sha(path)==meta['raw_sha256'],'exact stream divergence '+key
                packed=path.with_suffix(path.suffix+'.gz');packed.write_bytes(gzip.compress(path.read_bytes(),mtime=0))
                row['artifacts'][key]=dict(path=packed.name,sha256=sha(packed),raw_sha256=sha(path),reference=dict(path=str(reference.relative_to(ROOT)),sha256=sha(reference)))
                path.unlink()
            r['runs'].append(row);r['actual_RTL_run']=True
            r['newly_executed_candidate_case_profiles']+=22;r['newly_executed_candidate_directed_checks']+=21
        assert r['source_sha256']=={str(x.relative_to(ROOT)):sha(x) for x in files}
        r['status']='PASS_EXACT_HEADER_CANONICAL'
    finally:
        for name in inputs:(out/name).unlink(missing_ok=True)
        r['wall_seconds']=time.monotonic()-began
        r['artifact_sha256']={str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file()}
        write(out/'receipt.json',r);write(AREA/'results.json',dict(r,selected_receipt=str((out/'receipt.json').relative_to(ROOT))))
        print('V107_HEADER_CANONICAL',r['status'],out,flush=True)
    assert r['status']=='PASS_EXACT_HEADER_CANONICAL'


if __name__=='__main__':main()
