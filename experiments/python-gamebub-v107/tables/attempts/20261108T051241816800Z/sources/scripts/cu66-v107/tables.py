#!/usr/bin/env python3
"""Frozen whole-production admission comparison and independent coordinate replay."""
import datetime,gzip,hashlib,importlib.util,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FPGA=ROOT/'fpga/experiments/cu66-v107-tables'
AREA=ROOT/'experiments/python-gamebub-v107/tables'
SRC=ROOT/'fpga/experiments/cu66-v107-scale/cs88_admission_v91i2a.sv'
BASELINE='frozen SCALE 1956b84f3253ae688674744cd68952e21d8404318b0f4f7b69cf13e1207abfb3'
CONTAINER='gamebub-cu66-v69-build'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources
sys.path.insert(0,str(ROOT/'scripts/cu66-v107/header'))
sys.path.insert(0,str(ROOT/'scripts/cu66-v107/tables'))
from mode_replay import mode_replay
from replay import quant_replay

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
        if r.get('quant'):continue
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

def scale_replay(path):
    memory=[None]*1350;held=None;rows=collision=dual=priority=kills=holds=0
    for line in path.open():
        cycle,state,aw,a,ad,bw,b,bd,br,kill,out=map(int,line.strip().split(','))
        assert cycle==rows and 0<=a<1350 and 0<=b<1350
        read=br and state==26 and not kill
        expected=memory[b] if read else held
        if expected is not None:assert out==expected,(cycle,out,expected)
        if read:held=expected
        elif held is not None:holds+=1
        if not kill:
            collision+=int(aw and read and a==b);dual+=int(aw and bw and a!=b);priority+=int(aw and bw and a==b)
            if aw:memory[a]=ad
            if bw:memory[b]=bd
        else:kills+=1
        rows+=1
    assert rows==40585 and collision==5400 and dual==5400 and priority==5400 and kills==42
    return dict(status='PASS',rows=rows,old_data_collisions=collision,distinct_dual_writes=dual,same_address_Q_FILL_priority=priority,cancelled_edges=kills,hold_edges=holds,scope='Every valid1350-word location, four data values, full32 Q_FILL counter with valid low11 address; prepared states not packet reachability.')

def main():
    started=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True,exist_ok=False)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v107-tables-'+stamp);build.mkdir(exist_ok=False)
    vectors=ROOT/'experiments/python-gamebub-v91i/vectors/vectors.txt'
    files=[SRC,*sorted(FPGA.glob('*.*')),Path(__file__).resolve(),vectors,ROOT/'experiments/python-gamebub-v91i/admission-model.py',ROOT/'experiments/cu66-native-v69/generated_constants.hpp',ROOT/'experiments/python-gamebub-v107/header/model-results.json',*sorted((ROOT/'scripts/cu66-v107/header').glob('*.py')),*sorted((ROOT/'scripts/cu66-v107/tables').glob('*.py'))]
    report=dict(schema='v107-tables-two-ram-cycle-parity-v1',status='FAIL',baseline_revision=BASELINE,
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
        recipe=json.loads((FPGA/'edit-recipe.json').read_text());s=SRC.read_text()
        assert sha(SRC)==recipe['baseline_sha256']
        for e in reversed(recipe['changes']):
            assert s[e['start']:e['end']]==e['old'];s=s[:e['start']]+e['new']+s[e['end']:]
        assert s==(FPGA/SRC.name).read_text()
        adapter=json.loads((FPGA/'adapter.json').read_text())
        for variant,production in [('original',SRC),('candidate',FPGA/SRC.name)]:
            text=(FPGA/('admission_'+variant+'.sv')).read_text().replace(' /* verilator public_flat_rw */','').replace('module admission_'+variant+' (','module cs88_admission_v91i2a (',1)
            text=text.replace(adapter['extra_ports'],'\n);',1).replace(adapter['assignments'][variant],'',1)
            assert text==production.read_text(),'adapter changed production body '+variant
        report['complete_production_body_preserved_by_adapters']=True
        for p in files:
            target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        package=out/'compile-package';package.mkdir()
        complete=(out/'sources'/FPGA.relative_to(ROOT)/'admission_candidate.sv').read_text()
        first=complete.index('module cu66_scale_tdp_v107 (');second=complete.index('module cu66_mode_store_v107 (')
        fragments=[('admission_candidate.sv',complete[:first]),('cu66_scale_tdp_v107.sv',complete[first:second]),('cu66_mode_store_v107.sv',complete[second:])]
        for name,body in fragments:(package/name).write_text(body)
        original=(out/'sources'/FPGA.relative_to(ROOT)/'admission_original.sv').read_text();cut=original.index('module cu66_scale_tdp_v107 (')
        assert original[cut:]==complete[first:second]
        (package/'admission_original.sv').write_text(original[:cut])
        assert ''.join((package/name).read_text() for name,body in fragments)==complete
        report['compile_packaging']='Lossless main/scale/mode module split; identical shared SCALE helper compiled once, no warning suppression.'
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--public-flat-rw','--language','1800-2017','--top-module','admission_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',str(package/'admission_original.sv'),*[str(package/name) for name,body in fragments],copy(FPGA/'admission_probe.sv'),copy(FPGA/'tb_admission.cpp')],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vadmission_probe'],'binary.log',30)
        report['binary_sha256']=(out/'binary.log').read_text().split()[0]
        report['runs']=[]
        for seed in [107701,107702]:
            command(['docker','exec','-w',str(out),CONTAINER,'timeout','--kill-after=5s','180s',mapped+'/Vadmission_probe',copy(vectors),str(seed)],'simulation-'+str(seed)+'.jsonl',180)
            rows=[json.loads(l) for l in (out/('simulation-'+str(seed)+'.jsonl')).read_text().splitlines()]
            verdict=rows[-1];assert verdict['status']=='TEST_PASS' and verdict['prepared_edges']==348673 and verdict['header_prepared_edges']==738933 and verdict['scale_prepared_edges']==40585 and verdict['mode_prepared_edges']==158230
            trace=out/('trace-'+str(seed)+'.jsonl');(out/'trace.jsonl').rename(trace)
            modes=out/('mode-ports-'+str(seed)+'.jsonl');(out/'mode-ports.jsonl').rename(modes)
            ports=out/('scale-ports-'+str(seed)+'.csv');(out/'scale-ports.csv').rename(ports)
            report['runs'].append(dict(seed=seed,terminal_verdict=verdict,trace_replay=replay(trace,vectors),quant_replay=quant_replay(trace,vectors),scale_port_replay=scale_replay(ports),mode_port_replay=mode_replay(modes,seed)))
        report.update(terminal_verdict=verdict,actual_RTL_run=True)
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files},'sources changed during run'
        report['candidate']=dict(path=str((FPGA/SRC.name).relative_to(ROOT)),sha256=sha(FPGA/SRC.name),frozen_after_focused_PASS=True)
        report['status']='PASS'
    except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        report['trace_sha256']={}
        for trace in sorted([*out.glob('trace*.jsonl'),*out.glob('scale-ports-*.csv'),*out.glob('mode-ports-*.jsonl')]):
            report['trace_sha256'][trace.name]=sha(trace)
            with trace.open('rb') as src,(out/(trace.name+'.gz')).open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink()
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',report);write(AREA/'results.json',dict(report,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V107_TABLES',report['status'],out,flush=True)
if __name__=='__main__':main()
