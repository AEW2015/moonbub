"""Four-state isolated prefix/error-priority and new-state reset/abort proof."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/packet-prefix-v001';s=r/'fpga/experiments/cu66-v69/packet'
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=r/a.output;o.mkdir(parents=True,exist_ok=False)
for n in ['cu71_packet_prefix.sv','tb_prefix.sv']:shutil.copyfile(d/n,o/n)
shutil.copyfile(__file__,o/'executed-runner.py');shutil.copyfile(s/'cu66_profile.svh',o/'cu66_profile.svh')
fixture=s/(s/'cases.tsv').read_text().splitlines()[0].split('\t')[1];packet=fixture.read_bytes();(o/'header.hex').write_text('\n'.join(f'{x:02x}'for x in packet[76:136])+'\n',newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={n:sha(o/n)for n in ['cu71_packet_prefix.sv','tb_prefix.sv','cu66_profile.svh','header.hex']}
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_prefix','-I',str(o),'-o',str(o/'sim.vvp'),str(o/'cu71_packet_prefix.sv'),str(o/'tb_prefix.sv')]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe',str(o/'sim.vvp')])]:
 q=subprocess.run(cmd,cwd=o,env=env,capture_output=True);(o/(label+'.log')).write_bytes(q.stdout+q.stderr);steps.append(dict(label=label,command=cmd,returncode=q.returncode));assert q.returncode==0,(label,o)
assert 'PACKET_PREFIX_FOCUSED_PASS checks=18090'in(o/'simulation.log').read_text()
(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');(o/'source-freeze.json').write_text(json.dumps(sources,indent=2)+'\n')
(o/'result.json').write_text(json.dumps(dict(status='PASS_FOUR_STATE_PREFIX_ARITHMETIC_EXACT_ERROR_PRIORITY_RESET_ABORT',checks=18090,sources=sources,fixture_sha256=sha(fixture),hardware=False,scope='Header-state injection plus independent modular arithmetic; native byte-RAM fixture regression is a separate gate'),indent=2)+'\n')
print('PACKET_PREFIX_FOCUSED_PASS',o)
