from pathlib import Path
import argparse,hashlib,json,os,shlex,shutil,subprocess,time
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/transport-nonzero/samecycle-v001';p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lin=lambda p:'/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
derivation=json.loads((d/'derivation.json').read_text());parent=Path(derivation['parent']);assert sha(parent)==derivation['parent_sha256'];assert sha(d/'moonshine_top_dy71.sv')==derivation['candidate_sha256'];text=(d/'moonshine_top_dy71.sv').read_text()
for change in reversed(derivation['changes']):assert text.count(change['after'])==1;text=text.replace(change['after'],change['before'])
assert text==parent.read_text()
rootproof=r/'fpga/experiments/cu66-v71/transport-nonzero/evidence/proof02';rp=json.loads((rootproof/'result.json').read_text());assert rp['status']=='PASS_ALL_32_BIT_TWO_STATE_GRAY_NONZERO_EQUIVALENCE';assert sha(rootproof/'miter.sv')==rp['miter_sha256'];assert sha(rootproof/'yosys.log')==rp['log_sha256']
files=[d/'moonshine_top_dy71.sv',d/'transport_samecycle_miter.sv',d/'comb_miter.sv',d/'tb_transport_samecycle.sv',d/'derivation.json',d/'PATCH.diff',Path(__file__)];pins={str(f):sha(f)for f in files+[parent,rootproof/'result.json',rootproof/'miter.sv',rootproof/'yosys.log']}
for f in files:shutil.copy2(f,o/f.name)
(o/'source-freeze.json').write_text(json.dumps(dict(originals=pins,compiled={f.name:sha(o/f.name)for f in files},derived_exact_changes=4,whole_board_compiled=False,hardware=False),indent=2)+'\n');env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,cmd,timeout=120):
 start=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
run('simulation-build',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_transport_samecycle','-o','test.vvp','transport_samecycle_miter.sv','tb_transport_samecycle.sv'])
run('simulation',['C:/msys64/ucrt64/bin/vvp.exe','test.vvp']);sim=(o/'simulation.log').read_text();assert 'TRANSPORT_SAME_EDGE_PASS'in sim and 'FOUR_STATE_SCOPE_EXPECTED_DIFFERENCE'in sim
for label,filename,top,sat in [('all32','comb_miter.sv','transport_comb_miter','sat -prove mismatch 0 -show-inputs -show-outputs'),('sequential-induction','transport_samecycle_miter.sv','transport_samecycle_miter','sat -seq 3 -tempinduct -set-init-zero -prove mismatch 0 -show-inputs -show-outputs')]:
 script='read_verilog -sv '+lin(o/filename)+'; prep -top '+top+' -flatten; '+sat
 command='source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && yosys -Q -T -p '+shlex.quote(script)
 run(label,['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc',command],180)
 log=(o/(label+'.log')).read_text();assert ('SUCCESS!'in log and 'FAIL!'not in log),(label,o)
assert all(sha(Path(f))==h for f,h in pins.items())
result=dict(status='PASS_EXACT_FOUR_CHANGE_TOP_ALL32_TWO_STATE_SEQUENTIAL_INDUCTION_AND_DIRECTED_HISTORIES',candidate_top_sha256=sha(d/'moonshine_top_dy71.sv'),parent_top_sha256=sha(parent),source_freeze_sha256=sha(o/'source-freeze.json'),all32_two_state='SAT exhaustive combinational',sequential='SAT temporal induction from explicit known-zero initialization; includes all meta/sync/counter/quarantine histories, flag relation and fault on every core edge',simulation=sim,no_added_cycle=True,no_CDC_first_stage_use_added=True,counter_RTL_retained=True,counter_external_statistics_interface='None in parent selected top; unused counter can be optimized away. NoKEEP/DONT_TOUCH or new interface.',MAX_FANOUT64='Unmeasured implementation hint; no actual replication/timing result',four_state='Not equivalent under arbitrary X/Z; directed gray000x0001 yields oldfaultX/newfault1 at quarantinestate0. No metastability/MTBF/PVT/physical CDC claim.',whole_board=False,hardware=False,BIT=False,timing=False)
(o/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],result_sha256=sha(o/'result.json'),candidate_sha256=result['candidate_top_sha256']),indent=2))
