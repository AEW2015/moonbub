from pathlib import Path
import argparse,re,json,hashlib,subprocess,os,time
p=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('--out',required=True);args=a.parse_args()
e=p/'evidence'/args.out;e.mkdir(parents=True,exist_ok=False)
receiver=Path('C:/moon/builds/stb1-ce-v001/inputs/fpga/experiments/cu66-v71/metadata-baseline-v022/cu71_receiver_final_v022.sv')
text=receiver.read_text();header=text.split(')(\n',1)[1].split('\n);',1)[0]
inputs=[];direction=None
for item in header.split(','):
 item=item.strip();m=re.match(r'(input|output)\s+logic\s*(?:\[[^]]+\])?\s*(\w+)\s*$',item)
 if m:direction,name=m.groups()
 else:
  assert re.fullmatch(r'\w+',item),item
  name=item
 if direction=='input':inputs.append(name)
connections=','.join('.'+n+'('+n+')'if n in ['clk','rst']else'.'+n+"('0)"for n in inputs)
connections+=',.busy(busy),.error(error),.error_code(error_code),.stage(stage),.done(done)'
tb=r'''`timescale 1ns/1ps
module tb_watchdog;
reg clk=0,rst=1;always #5 clk=~clk;
wire busy,error,done;wire[7:0]error_code,stage;reg[7:0]header[0:59];integer checks=0;
cu71_receiver_final_v022 #(.WATCHDOG_CYCLES(32'd3000000000)) dut(CONNECTIONS);
task tick;begin @(posedge clk);#1;end endtask
task ck(input bit ok,input string s);begin checks++;if(!ok)$fatal(1,"%s code=%02x stage=%0d age=%0d",s,error_code,stage,dut.age);end endtask
task setup(input reg[31:0]age);
 begin
  @(negedge clk);rst=1;tick();@(negedge clk);rst=0;
  // Actual receiver+actual parser. Unrelated bank/base datapaths are explicitly inert.
  dut.state=dut.METADATA;dut.age=age;dut.packet_length=49152;
  dut.parser.state=dut.parser.CHECK_INNER;dut.parser.packet_bytes=49152;dut.parser.inner_bytes=1000;dut.parser.inner_length_total=1000;
  dut.parser.outer_validated=1;dut.parser.inner_validated=0;
  for(integer j=0;j<60;j++)dut.parser.inner_header[j]=header[j];
  dut.parser.metadata_key=header[5][0];dut.parser.metadata_frame_id={header[13],header[12],header[11],header[10]};dut.parser.metadata_reference_id={header[17],header[16],header[15],header[14]};
  for(integer j=0;j<16;j++)dut.parser.metadata_reference_tag[127-8*j-:8]=header[24+j];
  // A known code7-only zero plane length. Code6 remains good.
  for(integer j=0;j<4;j++)dut.parser.inner_header[48+j]=0;
 end
endtask
task cutoff(input reg[31:0]age,input reg[7:0]wanted);
 begin setup(age);tick();tick();tick();
  ck(error&&error_code==wanted,"actual owner cutoff priority");
  $display("WATCHDOG initial_age=%0d code=%02x",age,error_code);
 end
endtask
initial begin
 $readmemh("header.hex",header);
 // These services cannot fire in this focused METADATA control test.
 force dut.bank_error=0;force dut.b_error=0;force dut.b_req_valid=0;force dut.q_rsp_valid=0;
 cutoff(32'd2999999998,8'h17);
`ifdef STAGED
 cutoff(32'd2999999999,8'h7f);
`else
 cutoff(32'd2999999999,8'h17);
`endif
 cutoff(32'd3000000000,8'h7f);
 // Both causes simultaneously true: unchanged parser-error-before-watchdog ordering.
 setup(32'd3000000000);force dut.p_error=1;force dut.p_code=8'd6;tick();
 ck(error&&error_code==8'h16,"simultaneous parser code6 wins watchdog");release dut.p_error;release dut.p_code;
 $display("WATCHDOG_ACTUAL_RECEIVER_CONTROL_PASS checks=%0d",checks);$finish;
end
endmodule
'''.replace('CONNECTIONS',connections)
(e/'tb_watchdog.sv').write_text(tb);(e/'header.hex').write_bytes((p/'fixtures/header.hex').read_bytes())
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp');env.pop('NoDefaultCurrentDirectoryInExePath',None)
records=[]
for label in ['control','candidate']:
 cmd=['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-i']+(['-DSTAGED']if label=='candidate'else[])+['-I',str(p/'fixtures'),'-s','tb_watchdog','-o',str(e/(label+'.vvp')),str(receiver),str(p/label/'cu71_packet_rxstage_v001.sv'),str(e/'tb_watchdog.sv')]
 for phase,argv in [('compile',cmd),('run',['C:/msys64/ucrt64/bin/vvp.exe',str(e/(label+'.vvp'))])]:
  t=time.monotonic();r=subprocess.run(argv,cwd=e,env=env,capture_output=True,text=True,timeout=60);(e/f'{label}-{phase}.log').write_text(r.stdout+r.stderr);records.append(dict(label=label,phase=phase,command=argv,returncode=r.returncode,seconds=time.monotonic()-t));(e/'execution.json').write_text(json.dumps(records,indent=2)+'\n');print(label,phase,r.returncode,flush=True)
  if r.returncode:print(r.stdout[-2500:]+r.stderr[-2500:]);raise SystemExit(1)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
(e/'bindings.json').write_text(json.dumps({str(f):sha(f)for f in[Path(__file__),receiver,p/'control/cu71_packet_rxstage_v001.sv',p/'candidate/cu71_packet_rxstage_v001.sv',e/'tb_watchdog.sv',e/'header.hex']},indent=2)+'\n')
(e/'result.json').write_text(json.dumps({'status':'PASS','watchdog_cycles':3000000000,'source_parameter_unchanged':True,'actual_receiver_and_parser':True,'unrelated_datapaths':'unresolved modules ignored by iverilog -i; explicit bank/base/qmap inert service forces; not full-system simulation','initial_age_2999999999':{'control_code':'17','candidate_code':'7f'},'initial_age_2999999998':'both17','initial_age_3000000000':'both7f','simultaneous_parser6_watchdog':'both16'},indent=2)+'\n');print('WATCHDOG_BOUNDARY_DIFFERENCE_EXPECTED_PASS',flush=True)
