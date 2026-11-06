from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/event-retime-v001';p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=r/a.output;o.mkdir(parents=True,exist_ok=False)
names=['event_old.sv','event_new.sv','tb_event.sv'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in names:shutil.copyfile(d/n,o/n)
shutil.copyfile(__file__,o/'executed-runner.py');shutil.copyfile(d/'patch.json',o/'patch.json')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_event','-o',str(o/'test.vvp'),*[str(o/n)for n in names]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe',str(o/'test.vvp')])]:
 q=subprocess.run(cmd,cwd=o,env=env,capture_output=True);(o/(label+'.log')).write_bytes(q.stdout+q.stderr);steps.append(dict(label=label,command=cmd,returncode=q.returncode));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
assert 'EVENT_RETIME_FOURSTATE_PASS'in(o/'simulation.log').read_text();sources={n:sha(o/n)for n in names};(o/'source-freeze.json').write_text(json.dumps(sources,indent=2)+'\n')
(o/'result.json').write_text(json.dumps(dict(status='PASS_FOUR_STATE_EXACT_EVENT_RING_RETIME_BYPASS_RESET_WRAP',summary=(o/'simulation.log').read_text().strip(),sources=sources,receiver_sha256=sha(d/'cu71_receiver_eventpipe.sv'),scope='Exactextractedold/newstorage+eventdiag64words/counters/all1024addresses; nonringreceivercontrolrequiresseparatenativeintegration',hardware=False),indent=2)+'\n')
