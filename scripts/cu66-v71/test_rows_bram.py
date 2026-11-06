"""Full canonical stream and exact-cycle control comparison at both bank counts."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path(__file__).resolve().parents[2];old=r/'fpga/experiments/cu66-v69/rows/cu66_tile_rows.sv';new=r/'fpga/experiments/cu66-v71/rows/cu71_tile_rows.sv'
o=r/'fpga/experiments/cu66-v71/rows/evidence/equivalence03';o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ports='''start_ready tile_ready data_valid data data_last busy done error aborted error_code accepted_tiles emitted_bytes strip_word_writes strip_word_reads input_stall_cycles output_stall_cycles write_busy expected_plane expected_index'''.split()
widths={'data':8,'error_code':8,'expected_plane':2,'expected_index':17}
for n in ['accepted_tiles','emitted_bytes','strip_word_writes','strip_word_reads','input_stall_cycles','output_stall_cycles']:widths[n]=32
decl='\n'.join('wire '+('['+str(widths[n]-1)+':0] ' if n in widths else '')+n+'_a,'+n+'_b;' for n in ports)
common='''.clk,.rst,.abort_i,.start_valid,.frame_id,.key,.tile_valid,.tile_pixels,.tile_frame_id,.tile_key,.tile_plane,.tile_index,.tile_last,.data_ready'''
instances='\n'.join(module+' #(.STRIP_BANKS(BANKS)) '+name+'('+common+','+','.join('.'+n+'('+n+suffix+')' for n in ports)+');' for module,name,suffix in [('cu66_tile_rows','reference','_a'),('cu71_tile_rows','candidate','_b')])
controls=[n for n in ports if n!='data']
check='if({'+','.join(n+'_a' for n in controls)+'}!=={'+','.join(n+'_b' for n in controls)+'})$fatal(1,"public control/counter mismatch cycle%0d",cycles);'
tb=r'''`timescale 1ns/1ps
module tb;
parameter integer BANKS=1;
reg clk=0;always #5 clk=~clk;
reg rst=1,abort_i=0,start_valid=0,key=1,tile_valid=0,tile_key=1,tile_last=0,data_ready=0;
reg[31:0]frame_id=17,tile_frame_id=17;reg[511:0]tile_pixels=0;reg[1:0]tile_plane=0;reg[16:0]tile_index=0;
@DECL@
@INST@
integer cycles=0,checks=0,position=0,plane,p,index,byte_index,width,y,x,tile_id,expected,sendcount=0;
reg[31:0]random_state=32'h13579bdf;
always @(negedge clk)begin
 random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
 data_ready=random_state[2:0]!=0;
end
always @(posedge clk)if(!rst)begin
 cycles=cycles+1;checks=checks+1;
 @CHECK@
 if(data_valid_a)begin
  if(data_a!==data_b)$fatal(1,"stream byte mismatch");
  if(data_ready)begin
   if(position<4)case(position)0:expected='hd0;1:expected=2;2:expected='he0;3:expected=1;endcase
   else begin
    index=position-4;plane=0;width=720;
    if(index>=345600)begin index=index-345600;plane=1;width=360;if(index>=86400)begin index=index-86400;plane=2;end end
    y=index/width;x=index%width;tile_id=(y/8)*(width/8)+x/8;
    expected=(plane*17+tile_id*3+(y%8)*8+x%8)&255;
   end
   if(data_a!==expected[7:0])$fatal(1,"independent canonical oracle offset%0d got%h expected%h",position,data_a,expected);
   position=position+1;
  end
 end
end
task tick;begin @(posedge clk);#1;end endtask
task start;begin @(negedge clk);start_valid=1;tick();@(negedge clk);start_valid=0;end endtask
initial begin
 repeat(3)tick();@(negedge clk);rst=0;start();
 for(p=0;p<3;p=p+1)begin
  for(index=0;index<(p==0?5400:1350);index=index+1)begin
   while(!tile_ready_a)tick();
   @(negedge clk);tile_plane=p;tile_index=index;tile_last=p==2&&index==1349;
   for(byte_index=0;byte_index<64;byte_index=byte_index+1)tile_pixels[byte_index*8+:8]=(p*17+index*3+byte_index)&255;
   tile_valid=1;tick();sendcount=sendcount+1;@(negedge clk);tile_valid=0;
  end
 end
 while(!done_a)tick();
 if(position!=518404||sendcount!=8100||error_a)$fatal(1,"full stream totals");
 // Abort/reset with populated RAM must not expose stale ownership.
 @(negedge clk);abort_i=1;tick();@(negedge clk);abort_i=0;frame_id=18;tile_frame_id=18;position=0;start();
 repeat(5)tick();@(negedge clk);abort_i=1;tick();@(negedge clk);abort_i=0;
 repeat(3)tick();@(negedge clk);rst=1;tick();@(negedge clk);rst=0;
 repeat(3)tick();
 $display("CU71_ROWS_BRAM_PASS banks=%0d cycles=%0d checks=%0d oraclebytes=518404 tiles=8100",BANKS,cycles,checks);$finish;
end
initial begin #20000000;$fatal(1,"watchdog");end
endmodule
'''.replace('@DECL@',decl).replace('@INST@',instances).replace('@CHECK@',check)
# Use separate loop variables for the asynchronous consumer and input producer.
tb=tb.replace('integer cycles=0,checks=0,position=0,plane,p,index,','integer cycles=0,checks=0,position=0,plane,p,input_index,index,')
tb=tb.replace('for(index=0;index<(p==0?5400:1350);index=index+1)', 'for(input_index=0;input_index<(p==0?5400:1350);input_index=input_index+1)')
tb=tb.replace('tile_index=index;tile_last=p==2&&index==1349','tile_index=input_index;tile_last=p==2&&input_index==1349').replace('(p*17+index*3+byte_index)','(p*17+input_index*3+byte_index)')
(o/'tb.sv').write_text(tb,newline='\n')
for p in [old,new]:shutil.copyfile(p,o/p.name)
pins={str(p.relative_to(r)):sha(p) for p in [old,new]};env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','');steps=[]
for banks in [1,2]:
 for stage,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb','-Ptb.BANKS='+str(banks),'-o',str(o/f'test{banks}.vvp'),str(old),str(new),str(o/'tb.sv')]),('run',['C:/msys64/ucrt64/bin/vvp.exe',str(o/f'test{banks}.vvp')])]:
  with (o/f'{stage}{banks}.log').open('wb')as log:p=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
  steps.append(dict(banks=banks,stage=stage,command=cmd,returncode=p.returncode));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');assert p.returncode==0,(stage,banks,o)
 assert 'CU71_ROWS_BRAM_PASS' in (o/f'run{banks}.log').read_text()
assert pins=={str(p.relative_to(r)):sha(p) for p in [old,new]}
(o/'result.json').write_text(json.dumps(dict(status='PASS_EXACT_CYCLE_ROWS_AND_INDEPENDENT_FULL_STREAM',source_sha256=pins,bank_counts=[1,2],oracle_bytes_per_frame=518404,tiles_per_frame=8100,hardware=False),indent=2)+'\n')
print('\n'.join((o/f'run{b}.log').read_text() for b in [1,2]))
