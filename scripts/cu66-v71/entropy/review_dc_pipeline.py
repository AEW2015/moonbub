"""Independent exact-source DC split review: actual DUT differential and algebra SAT."""
from pathlib import Path
import hashlib,json,os,re,shlex,subprocess
r=Path(__file__).resolve().parents[3]
d=r/'fpga/experiments/cu66-v71/entropy-dcpipe'
o=d/'evidence/independent-review01';o.mkdir(parents=True,exist_ok=False)
old=r/'fpga/experiments/cu66-v71/entropy-headerpipe/cu71_ab38_decoder_headerpipe_v5.sv'
new=d/'cu71_ab38_decoder_dcpipe_v6.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old)=='8715c9f29c481d8a02bfa3e86eccb57efdea21b3fb1d4cc36110724a85d02893'
assert sha(new)=='cb8573f9f467305dd66754d82005dd23df01bbf505a7623cc78f198765f1b777'
for p in (old,new):(o/p.name).write_bytes(p.read_bytes())
unzig=re.search(r'    function automatic signed \[31:0\] unzigzag.*?    endfunction',old.read_text(),re.S).group()
assert unzig in new.read_text()
expression="(dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value)"
assert old.read_text().count(expression)==4
assert new.read_text().count(expression)==1
miter='''module dc_math(input [8:0] dc_column,input signed [31:0] previous_dc,input [31:0] rice_value,output same);
FUNCTION
wire signed [31:0] captured=EXPRESSION;
wire old_fail=(EXPRESSION)<-2048 || (EXPRESSION)>2048;
wire new_fail=captured<-2048 || captured>2048;
wire signed [31:0] old_previous=EXPRESSION;
wire [15:0] old_tile=16'(EXPRESSION);
assign same=(old_fail==new_fail) && (old_previous==captured) && (old_tile==16'(captured));
endmodule
'''.replace('FUNCTION',unzig).replace('EXPRESSION',expression)
(o/'math.sv').write_text(miter,newline='\n')
tb='''module tb;
reg clk=0,rst=0,abort_i=0,cfg_valid=0;
wire [7:0] ns,os;
cu71_ab38_decoder_headerpipe_v5 p(.clk(clk),.rst(rst),.abort_i(abort_i),.cfg_valid(cfg_valid),.cfg_dispatch(3'd5),.cfg_packet_bytes(16'd46),.cfg_blocks(17'd1),.cfg_blocks_w(9'd1),.rd_req_ready(1'b0),.rd_rsp_valid(1'b0),.rd_rsp_data(8'd0),.tile_ready(1'b1),.debug_state(os));
cu71_ab38_decoder_dcpipe_v6 n(.clk(clk),.rst(rst),.abort_i(abort_i),.cfg_valid(cfg_valid),.cfg_dispatch(3'd5),.cfg_packet_bytes(16'd46),.cfg_blocks(17'd1),.cfg_blocks_w(9'd1),.rd_req_ready(1'b0),.rd_rsp_valid(1'b0),.rd_rsp_data(8'd0),.tile_ready(1'b1),.debug_state(ns));
task tick;begin #5;clk=1;#1;clk=0;#4;end endtask
integer count=0,j,k,failcases=0,passcases=0;
reg signed [31:0] expect_prev;reg [15:0] expect_tile;reg expect_error;reg [7:0] expect_code;
task differential(input signed [31:0] prev,input [31:0] rice,input [8:0] col);
begin
rst=1;tick;rst=0;
p.state=p.DC_VALUE;n.state=n.DC_VALUE;p.busy=1;n.busy=1;
p.previous_dc=prev;n.previous_dc=prev;p.rice_value=rice;n.rice_value=rice;p.dc_column=col;n.dc_column=col;
p.tile[0]=16'h4a5a;n.tile[0]=16'h4a5a;n.dc_prediction=32'h89abcdef;
tick;
if(ns!==56 || n.previous_dc!==prev || n.tile[0]!==16'h4a5a || n.error!==0)$fatal(1,"new first stage committed");
expect_prev=p.previous_dc;expect_tile=p.tile[0];expect_error=p.error;expect_code=p.error_code;
// Freeze parent state only after sampling its actual original DC decision.
p.state=p.IDLE;
tick;
if(n.previous_dc!==expect_prev || n.tile[0]!==expect_tile || n.error!==expect_error || n.error_code!==expect_code)$fatal(1,"differential prev=%h rice=%h col=%h",prev,rice,col);
if(expect_error===1)begin if(expect_code!==8'h12)$fatal(1,"wrong DC reason");failcases=failcases+1;end
else passcases=passcases+1;
count=count+1;
end endtask
reg signed [31:0] values[0:10];
initial begin
values[0]=-2049;values[1]=-2048;values[2]=-2047;values[3]=-1;values[4]=0;values[5]=1;values[6]=2047;values[7]=2048;values[8]=2049;values[9]=32'h7fffffff;values[10]=32'h80000000;
for(j=0;j<11;j=j+1)begin
 // Zigzag maps signed32 range except most-negative (represented by ffffffff).
 differential(0,values[j]<0 ? ((-values[j]-1)<<1)|1 : values[j]<<1,1);
 differential(values[j],0,1);differential(values[j],32'hffffffff,1);differential(values[j],32'hfffffffe,511);
end
for(j=0;j<2000;j=j+1)differential($random,$random,$random);
// Four-state payloads preserve original procedural-if semantics after staging.
differential(32'hxxxxxxxx,0,1);differential(0,32'hzzzzzzzz,1);differential(32'hffffffff,0,9'bxxxxxxxxx);
// Direct RESET in DC_CHECK with dirty payload and all352 retained probability bytes.
rst=1;tick;rst=0;n.state=n.DC_CHECK;n.busy=1;n.dc_prediction=32'h7fffffff;n.previous_dc=123;n.tile[0]=456;
for(k=0;k<352;k=k+1)n.probabilities[k]=8'(k^8'h5a);
rst=1;abort_i=1;tick;
if(ns!==0 || n.busy!==0 || n.error!==0 || n.aborted!==0 || n.previous_dc!==0 || n.tile[0]!==0)$fatal(1,"reset56 priority/control");
for(k=0;k<352;k=k+1)if(n.probabilities[k]!==8'(k^8'h5a))$fatal(1,"reset changed probability RAM");
// The private staged payload deliberately remains dirty; IDLE fences it.
if(n.dc_prediction!==32'h7fffffff)$fatal(1,"unexpected payload reset");
rst=0;abort_i=0;cfg_valid=1;tick;cfg_valid=0;
if(ns!==42 || n.busy!==1 || n.error!==0)$fatal(1,"valid retry not admitted");
repeat(17)tick;
if(ns!==4 || n.error!==0)$fatal(1,"valid retry CFG pipeline");
// Known-good DC transaction overwrites dirty staged value before use.
differential(23,6,1);
// Abort in new stage must outrank invalid DC and produce no commit/error.
n.state=n.DC_CHECK;n.busy=1;n.dc_prediction=32'h7fffffff;n.previous_dc=77;n.tile[0]=88;abort_i=1;tick;
if(ns!==0 || n.aborted!==1 || n.error!==0 || n.previous_dc!==77 || n.tile[0]!==88)$fatal(1,"abort56 priority");
$display("ACTUAL_DC_DIFFERENTIAL_PASS cases=%0d fail12=%0d accepted=%0d RESET56_DIRTY_RETAINED_RAM_RETRY_PASS ABORT56_PRIORITY_PASS",count,failcases,passcases);$finish;
end
endmodule
'''
(o/'tb.sv').write_text(tb,newline='\n')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];commands=[]
def run(label,args,env=None):
 with(o/(label+'.log')).open('w')as f:q=subprocess.run(args,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
 commands.append(dict(label=label,command=args,returncode=q.returncode));assert q.returncode==0,(label,(o/(label+'.log')).read_text()[-4000:])
run('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb','-o','sim',old.name,new.name,'tb.sv'],env)
run('actual',['C:/msys64/ucrt64/bin/vvp.exe','sim'],env)
lin=lambda p:'/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
ys='read_verilog -sv '+lin(o/'math.sv')+'; prep -top dc_math -flatten; sat -verify -prove same 1 -show-inputs -show-outputs'
(o/'executed.ys').write_text(ys+'\n')
run('sat',['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && yosys -p '+shlex.quote(ys)])
assert 'SUCCESS' in(o/'sat.log').read_text()
files=[p for p in o.iterdir()if p.is_file()]
(o/'result.json').write_text(json.dumps(dict(status='PASS_INDEPENDENT_DC_MATH_AND_ACTUAL_PARENT_DIFFERENTIAL_RESET',sources={str(p.relative_to(r)):sha(p)for p in(old,new)},artifacts={p.name:sha(p)for p in files},commands=commands,scope='All binary signed/wrapped32-bit math SAT, actual parent/new latency-aligned DC stage across boundaries/random/XZ. Direct newstate reset+dirty payload+probability retention+configuration/DC retry and abort priority. Full packet retry covered separately by actual native campaign.',hardware=False),indent=2)+'\n')
print((o/'actual.log').read_text());print('SAT_DC_MATH_PASS')
