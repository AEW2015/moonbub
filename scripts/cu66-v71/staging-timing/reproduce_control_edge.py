"""Actual split CSR adversarial bus sequencing; not firmware-driver behavior."""
from pathlib import Path
import ast,hashlib,json,os,re,shutil,subprocess
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/staging-timing';o=d/'evidence/control-edge01';o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
h=r/'scripts/cu66-v71/direct-system/board-math/prepare_shell_proposal.py';node=next(n for n in ast.parse(h.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='ports');exec(compile(ast.Module(body=[node],type_ignores=[]),str(h),'exec'),globals())
p=r/'fpga/experiments/cu66-v71/bus-split/dy71_local_control_split.sv';ps=ports(p)
decl='\n'.join(('reg'if direction=='input'else'wire')+' '+width+' '+n+('=0'if direction=='input'else'')+';'for n,(direction,width)in ps.items())
tb='`timescale 1ns/1ps\nmodule tb;\n'+decl+'\nalways #5 clk=~clk;\ndy71_local_control_split dut('+','.join('.'+n+'('+n+')'for n in ps)+');\n'
tb+='''
task step;begin @(posedge clk);#1;@(negedge clk);#1;end endtask
task put(input[11:0]a,input[31:0]v);begin bus_write=1;bus_address=a;bus_wdata=v;step();bus_write=0;end endtask
initial begin
 rst=1;repeat(3)step();rst=0;
 put('h40,1);put('h44,0);put('h50,3);put('h54,0);put('h20,1);put('h24,1);step();
 if(!dut.upload_ready)$fatal(1,"begin setup");
 put('h20,2);put('h24,4);
 // Next consecutive bus beat lands while DISCARD_PACKET executes.
 put('h100,32'h00030201);
 if(dut.staging.state!=0 || dut.staging.held_count!=3)$fatal(1,"CSR did not retain upload after discard");
 $display("CSR_EDGE_EMPTY_WITH_STALE_UPLOAD state=%0d held=%0d ack=%0d",dut.staging.state,dut.staging.held_count,dut.ack_status);
 put('h40,2);put('h50,1);put('h20,3);put('h24,1);step();repeat(3)step();
 if(dut.written_bytes!=3 || dut.packet_bytes!=1)$fatal(1,"subsequent smaller begin did not overshoot");
 $display("ACTUAL_SPLIT_CSR_EDGE_REPRODUCED written=%0d packet=%0d faults=%h",dut.written_bytes,dut.packet_bytes,dut.staging_faults);$finish;
end
initial begin #10000;$fatal(1,"watchdog");end
endmodule
'''
(o/'tb.sv').write_text(tb,newline='\n')
sources=[p,r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_arbiter.sv',r/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',Path(__file__).resolve()]
for f in sources:shutil.copyfile(f,o/f.name)
(o/'source-freeze.json').write_text(json.dumps({str(f):sha(f)for f in sources},indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'])
cmd=['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-I.','-s','tb','-o','test.vvp','tb.sv']+[f.name for f in sources if f.suffix=='.sv']
for label,command in [('compile',cmd),('run',['C:/msys64/ucrt64/bin/vvp.exe','test.vvp'])]:
 with(o/(label+'.log')).open('w')as log:q=subprocess.run(command,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
 assert q.returncode==0,label
assert 'ACTUAL_SPLIT_CSR_EDGE_REPRODUCED'in(o/'run.log').read_text()
(o/'result.json').write_text(json.dumps({'status':'EXISTING_MALFORMED_BUS_SEQUENCE_REPRODUCED','actual_split_CSR':True,'driver_trace':False,'physical_bridge_trace':False,'accepted_discard_and_upload_same_core_cycle':True,'new_begin_packet_bytes':1,'actual_written_bytes':3,'selected_sources_modified':False,'hardware':False},indent=2)+'\n')
print((o/'run.log').read_text())
