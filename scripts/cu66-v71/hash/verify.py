"""Bind all original+new SHA fixtures, actual public cycles and OOC reports."""
from pathlib import Path
import hashlib,json,re,zlib
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/hash';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();wanted=sha(d/'cu71_sha256_bytes_lookahead.sv');proof=json.loads((d/'source-proof.json').read_text());assert proof['candidate_sha256']==wanted
fixtures=json.loads((d/'fixtures.json').read_text());assert fixtures['original_cases']==98 and fixtures['new_cases']==210 and fixtures['total_cases']==308
for file,h in fixtures['source_sha256'].items():assert sha(Path(file))==h
for file,h in fixtures['assets'].items():assert sha(d/file)==h
for line in(d/'fixtures.tsv').read_text().splitlines():
    name,file,size,digest=line.split('\t');raw=zlib.decompress((d/file).read_bytes());assert len(raw)==int(size)and hashlib.sha256(raw).hexdigest()==digest
runs=[];timing=[]
for name in ['banks1-01','banks2-02','synth1-01','synth2-01']:
    p=d/'evidence'/name;result=json.loads((p/'result.json').read_text());assert result['source_sha256']==wanted
    freeze=json.loads((p/'source-freeze.json').read_text())
    for file,h in freeze['originals'].items():assert sha(Path(file))==h
    for file,h in freeze['actual'].items():assert sha(p/file)==h
    execution=json.loads((p/'execution.json').read_text());assert all(x['returncode']==0 for x in execution)
    if name.startswith('banks'):
        for seed,randomize in [(7101,0),(7101,1),(7102,1),(7103,1)]:
            log=(p/f'seed{seed}-random{randomize}.log').read_text()
            assert 'TEST_PASS'in log and 'fixtures=308'in log and 'TEST_FAIL'not in log and 'CONTROL_PASS'in log
            assert 'ALL_ROUND_CANCEL_PASS aborts=64 resets=64 public_cycle_compare=1'in log
            m=re.search(r'STARTUP_WORDS reference=(\d+) candidate=(\d+)',log);assert m and int(m[1])!=0 and int(m[2])!=0 and m[1]!=m[2]
    else:
        lines=(p/'timing.rpt').read_text().splitlines();i=next(i for i,x in enumerate(lines)if x.strip().startswith('WNS(ns)'));v=lines[i+2].split();assert float(v[0])>0 and int(v[2])==0
        timing.append(dict(banks=result['banks'],setup_WNS_ns=float(v[0]),hold_WHS_ns=float(v[4]),hold_failing=int(v[6]),part='xc7a100tcsg324-1',clock_ns=10,IO_max_ns=1,IO_min_ns=0,routed=False))
    runs.append(dict(path=str(p),result=result,bindings={file:sha(p/file)for file in ['source-freeze.json','execution.json','result.json']}))
report=dict(status='PASS_EXACT_PUBLIC_CYCLES_HASHLIB_AND_SETUP_ESTIMATES_ROUTE_PENDING',source_sha256=wanted,parent_sha256=proof['parent_sha256'],source_proof_sha256=sha(d/'source-proof.json'),fixtures_sha256=sha(d/'fixtures.json'),fixture_cases=308,original_fixtures_retained=98,independent_new_hashlib_cases=210,configurations=[1,2],runs_per_configuration=4,total_fixture_runs=2464,all_round_aborts=512,all_round_resets=512,public_fields_compared_each_halfcycle=16,rounds_per_block=64,extra_round_or_public_latency_cycles=0,private_word_zero_assumptions=False,timing=timing,runs=runs,scope='Actual old/new RTL pair cycle comparison and full256bit hashlib goldens, with randomized distinct private memory initialization; exactdeviceOOC estimates. No full-board route or physical hardware proof.',hardware=False,BIT=False)
q=d/'qualification.json';assert not q.exists();q.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],sha(q))
