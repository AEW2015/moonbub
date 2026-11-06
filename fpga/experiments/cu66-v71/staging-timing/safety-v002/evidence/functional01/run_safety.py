"""Safety successor tests; ordinary equivalence and adversarial invariants differ."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/staging-timing';d=p/'safety-v002';a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();b=r/'fpga/experiments/cu66-v71/bus-split';base=p/'evidence/functional08'
sources=list(d.glob('*.sv'))+[r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv',b/'cu71_bus_cdc_split.sv',r/'fpga/experiments/cu66-v71/board/source-v007/moonshine_bus_cdc.sv',r/'fpga/experiments/cu66-v71/system/cu71_local_control.sv',r/'fpga/experiments/cu66-v71/direct-system/local-control/dy71_local_control.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_arbiter.sv',r/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',Path(__file__).resolve()]
for f in sources:shutil.copyfile(f,o/f.name)
maxtext=(base/'tb_max.sv').read_text().replace('cu71_packet_staging_credit','cu71_packet_staging_safe');(o/'tb_max.sv').write_text(maxtext,newline='\n')
random=(base/'tb_random.sv').read_text();start=random.index('wire[2:0]upload_capacity;');end=random.index('integer i,j,n;',start);inst=random[random.index('cu71_packet_staging_credit #',start):random.index('integer comparisons=',start)].replace('cu71_packet_staging_credit','cu71_packet_staging_safe')
observer='''wire[2:0]upload_capacity;
'''+inst+'''
integer comparisons=0;
always @(negedge clk)if(!rst)begin
 if(newer.state==0 && newer.held_count!=0)$fatal(1,"EMPTY retained bytes");
 if(written_bytes>packet_bytes)$fatal(1,"written exceeds packet");
 comparisons=comparisons+1;
end
always @(posedge clk)if(!rst&&newer.state==1&&newer.held_count!=0)begin
 if(written_bytes>=packet_bytes || written_bytes>=LIMIT)$fatal(1,"out-of-packet physical byte write");
end
''';random=random[:start]+observer+random[end:];start=random.index(' // Preserve parent malformed-input');end=random.index(' // Full arbitrary32-bit',start);random=random[:start]+random[end:];random=random.replace('STAGING_CREDIT_DIFFERENTIAL_PASS','STAGING_SAFE_INVARIANTS_PASS');(o/'tb_random.sv').write_text(random,newline='\n')
control=(b/'tb_bus_pair.sv').read_text().replace('cu71_local_control_split','cu71_local_control_safe').replace('dy71_local_control_split','dy71_local_control_safe');(o/'tb_bus_pair.sv').write_text(control,newline='\n')
edge=(p/'evidence/control-edge01/tb.sv').read_text().replace('dy71_local_control_split','dy71_local_control_safe')
edge=edge.replace('if(dut.staging.state!=0 || dut.staging.held_count!=3)','if(dut.staging.state!=1 || dut.staging.held_count!=3 || dut.ack_status!=32\'h80000005)')
edge=edge.replace('if(dut.written_bytes!=3 || dut.packet_bytes!=1)','if(dut.written_bytes!=3 || dut.packet_bytes!=3 || dut.staging.state!=1)')
edge=edge.replace('ACTUAL_SPLIT_CSR_EDGE_REPRODUCED','ACTUAL_SAFE_CSR_DISCARD_REJECTED_NO_OVERSHOOT');(o/'tb_edge.sv').write_text(edge,newline='\n')
(o/'source-freeze.json').write_text(json.dumps({'originals':{str(f):sha(f)for f in sources},'compiled':{f.name:sha(f)for f in o.glob('*.sv')},'parent_test_inputs':{str(f):sha(f)for f in [base/'tb_max.sv',base/'tb_random.sv',b/'tb_bus_pair.sv',p/'evidence/control-edge01/tb.sv']},'transform':'Versioned safe module bindings; max and typed normal compare all public outputs; random asserts safety instead of old malformed equivalence; edge expects ACK rejection and bounded bytes'},indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[];iv='C:/msys64/ucrt64/bin/iverilog.exe';vvp='C:/msys64/ucrt64/bin/vvp.exe'
def run(label,cmd):
 start=time.monotonic()
 with(o/(label+'.log')).open('w')as log:q=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,label
src=[f.name for f in sources if f.suffix=='.sv']
for limit in [1,3,17,49152,65536]:
 label='invariants-'+str(limit);run(label+'-compile',[iv,'-g2012','-I.','-s','tb_random','-Ptb_random.LIMIT='+str(limit),'-o',label+'.vvp','tb_random.sv']+src);run(label,[vvp,label+'.vvp']);assert 'SAFE_INVARIANTS_PASS'in(o/(label+'.log')).read_text()
for top,file,label in [('tb','tb_max.sv','maximum'),('tb','tb_edge.sv','edge')]:
 run(label+'-compile',[iv,'-g2012','-I.','-s',top,'-o',label+'.vvp',file]+src);run(label,[vvp,label+'.vvp'])
for phase in ['0.0','2.3']:
 for dy in [0,1]:
  label=f'control-{phase}-{dy}';run(label+'-compile',[iv,'-g2012','-I.','-s','tb_bus_pair','-Ptb_bus_pair.PHASE='+phase,'-Ptb_bus_pair.DY='+str(dy),'-o',label+'.vvp','tb_bus_pair.sv']+src);run(label,[vvp,label+'.vvp']);assert 'ACTUAL_CSR_BRIDGE_PAIR_PASS'in(o/(label+'.log')).read_text()
(o/'result.json').write_text(json.dumps({'status':'PASS_SAFE_RANDOM_INVARIANTS_NORMAL_MAX_AND_TYPED_EQUIVALENCE_ACK_REJECTION','random_cycles':900000,'MAX_BYTES':[1,3,17,49152,65536],'normal_cycle_equivalence':True,'malformed_behavior_changed':True,'actual_CSR_discard_ACK':'80000005','general_equivalence':False,'hardware':False,'Vivado':False},indent=2)+'\n')
