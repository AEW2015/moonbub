#!/usr/bin/env python3
"""Frozen whole-production admission comparison and independent coordinate replay."""
import datetime,gzip,hashlib,importlib.util,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FPGA=ROOT/'fpga/experiments/cu66-v105-admission'
AREA=ROOT/'experiments/python-gamebub-v105/admission'
SRC=ROOT/'fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv'
BASELINE='afc073e36f813cbcedaec9b21b61cda239453a5b'
CONTAINER='gamebub-cu66-v69-build'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def replay(path,vectors):
    spec=importlib.util.spec_from_file_location('admission_model',ROOT/'experiments/python-gamebub-v91i/admission-model.py')
    model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    mask=model.fixed_hidden_mask();expected={}
    for line in vectors.read_text().splitlines():
        v=line.split();packet=bytes.fromhex(v[2])
        if int(v[1])==0:
            ops=model.decode_modes(packet,128,int.from_bytes(packet[36:40],'big'),packet[5]==1,packet[7],mask)
            coords=[]
            for absolute,op in enumerate(ops):
                if op!=2:continue
                p,t=(0,absolute) if absolute<5400 else ((1,absolute-5400) if absolute<6750 else (2,absolute-6750))
                coords.append((p,t))
            expected[v[0]]=coords
    n=marks=scans=sentinels=jumps=0;active=set();case=None;at=0;previous=None;checked_cases=set()
    for line in path.open():
        r=json.loads(line)
        if 'begin' in r:
            case=r['begin'];active=set();at=0;previous=None;continue
        n+=1
        if r['kill']:
            active=set();at=0;previous=None;continue
        if r['valid']:
            p,t=r['plane'],r['tile'];limit=5400 if p==0 else 1350
            assert p<=2 and 0<=t<=limit,r
            cell=(t//180)*45+(t%90)//2 if p==0 else t
            assert r['cell']==cell,r
            assert r['column']==(t%90 if p==0 else 0),r
            assert r['odd']==((t//90)%2 if p==0 else 0),r
            assert r['base']==((t//180)*45 if p==0 else 0),r
            if t==limit:sentinels+=1
            if previous and previous['plane']==p and t>previous['tile']+1:jumps+=1
            previous=r
            if r['residual']:
                assert t<limit and cell<1350
                active.add(cell);marks+=1
                if case in expected:
                    assert (p,t)==expected[case][at],(case,at,p,t,expected[case][at]);at+=1
        if r['state']==13:
            index=r['active_index']
            if index<1350:
                assert r['active']==int(index in active),(case,index,r['active']);scans+=1
            if case in expected:
                assert at==len(expected[case]),(case,at,len(expected[case]));checked_cases.add(case)
    assert marks>10000 and scans>10000 and jumps>0 and sentinels>0
    return dict(status='PASS',rows=n,residual_marks=marks,active_bits_compared=scans,end_sentinels=sentinels,group_jumps=jumps,
                positive_packet_mode_oracles=len(checked_cases),oracle='Independent packet mode decoder, integer geometry, residual-coordinate sequence and active-bit set replay.')

def main():
    started=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True,exist_ok=False)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v105-admission-'+stamp);build.mkdir(exist_ok=False)
    vectors=ROOT/'experiments/python-gamebub-v91i/vectors/vectors.txt'
    files=[SRC,*sorted(FPGA.glob('*.*')),Path(__file__).resolve(),vectors,ROOT/'experiments/python-gamebub-v91i/admission-model.py',ROOT/'experiments/cu66-native-v69/generated_constants.hpp']
    report=dict(schema='v105-admission-clocked-coordinate-v1',status='FAIL',baseline_revision=BASELINE,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],actual_RTL_run=False,
        strict_warnings=True,assertions_disabled_or_downgraded=False,
        limits=['Reachable-state behavioral equivalence under retained clocked corpus; not formal arbitrary internal-state equivalence.',
                'No routed timing, hardware 30fps, or complete decode under10ms qualification.'])
    def command(argv,name,timeout):
        entry=dict(argv=argv,timeout_seconds=timeout,resource_gate=resources());report['commands'].append(entry)
        began=time.monotonic()
        with (out/name).open('w') as log:r=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+10)
        entry.update(exit_code=r.returncode,wall_seconds=time.monotonic()-began)
        if r.returncode:raise RuntimeError('failed '+name)
    try:
        report['resource_gate']=resources()
        assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+str(SRC.relative_to(ROOT))],cwd=ROOT)).hexdigest()==sha(SRC)
        recipe=json.loads((FPGA/'edit-recipe.json').read_text());s=SRC.read_text()
        for e in recipe['edits']:
            assert s.count(e['before'])==e['expected_occurrences'];s=s.replace(e['before'],e['after'])
        assert s==(FPGA/SRC.name).read_text()
        adapter=json.loads((FPGA/'adapter.json').read_text())
        for variant,production in [('original',SRC),('candidate',FPGA/SRC.name)]:
            text=(FPGA/('admission_'+variant+'.sv')).read_text().replace('module admission_'+variant+' (','module cs88_admission_v91i2a (',1)
            text=text.replace(adapter['extra_ports'],'\n);',1).replace(adapter['assignments'][variant],'',1)
            assert text==production.read_text(),'adapter changed production body '+variant
        report['complete_production_body_preserved_by_adapters']=True
        for p in files:
            target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','admission_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[copy(FPGA/n) for n in ('admission_original.sv','admission_candidate.sv','admission_probe.sv','tb_admission.cpp')]],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vadmission_probe'],'binary.log',30)
        report['binary_sha256']=(out/'binary.log').read_text().split()[0]
        command(['docker','exec','-w',str(out),CONTAINER,'timeout','--kill-after=5s','180s',mapped+'/Vadmission_probe',copy(vectors),'105101'],'simulation.jsonl',180)
        rows=[json.loads(l) for l in (out/'simulation.jsonl').read_text().splitlines()]
        verdict=rows[-1];assert verdict['status']=='TEST_PASS'
        report.update(terminal_verdict=verdict,actual_RTL_run=True)
        trace=out/'trace.jsonl';report['trace_replay']=replay(trace,vectors)
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files},'sources changed during run'
        report['candidate']=dict(path=str((FPGA/SRC.name).relative_to(ROOT)),sha256=sha(FPGA/SRC.name),frozen_after_focused_PASS=True)
        report['status']='PASS'
    except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        trace=out/'trace.jsonl'
        if trace.exists():
            report['raw_trace_sha256']=sha(trace)
            with trace.open('rb') as src,(out/'trace.jsonl.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink()
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',report);write(AREA/'results.json',dict(report,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V105_ADMISSION',report['status'],out,flush=True)
if __name__=='__main__':main()
