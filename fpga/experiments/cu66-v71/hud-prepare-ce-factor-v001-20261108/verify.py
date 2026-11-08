from pathlib import Path
import re,hashlib,json,subprocess,os,time,itertools
p=Path(__file__).resolve().parent;e=p/'evidence';e.mkdir(exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
ports=[('[3:0]','state'),('','rst'),('','abort_i'),('','abort_allowed'),('','hud_pending'),('','hud_requested'),('','p_error'),('','bank_error'),('','b_error'),('[7:0]','p_code'),('[7:0]','bank_code'),('[7:0]','b_code'),('','hud_result_valid'),('[63:0]','hud_result_generation'),('[31:0]','hud_result_frame_id'),('[31:0]','hud_result_reference_id'),('[127:0]','hud_result_tag'),('[15:0]','hud_result_words'),('','hud_result_success'),('','hud_drain_valid'),('[63:0]','hud_drain_generation'),('[31:0]','hud_drain_frame_id'),('[1:0]','hud_drain_bank'),('[127:0]','hud_drain_tag'),('[15:0]','hud_drain_words'),('','hud_drain_success'),('[63:0]','active_generation'),('[31:0]','fid'),('[31:0]','rid'),('[127:0]','hud_expected'),('[1:0]','bank_write'),('','cache_prepare_result_valid'),('','cache_prepare_match'),('','cache_prepare_result_success'),('','ref_rsp_valid'),('','ref_match'),('','ref_rsp_error'),('','q_rsp_valid'),('[10:0]','q_rsp_index'),('[10:0]','q_expected_index'),('','packet_pending'),('','p_req_valid'),('','b_req_valid'),('[16:0]','calculated_packet_address'),('[15:0]','packet_length'),('[31:0]','age')]
extracts={}
for label in ['control','candidate']:
 text=(p/label/'cu71_receiver_final_v022.sv').read_text()
 enum=re.search(r'typedef enum logic \[3:0\] \{(.*?)\} state_t;',text,re.S).group(1)
 states=[name.strip()for name in enum.split(',')]
 assigns=[re.search(r'assign '+name+r'=.*?;',text,re.S).group(0)for name in ['kill','hud_match','hud_write_match','hud_prepare_valid']]
 start=text.index('        fatal=0;fatal_code=0;');end=text.index('    // HUD comparisons cannot',start)
 fatal='always_comb begin\n'+text[start:end].strip()+'\n'
 start=text.index('    always_comb begin\n        fatal_non_hud=0;');end=text.index('    logic payload_start_clear;',start)
 nonhud=text[start:end];fragments='\n'.join(assigns)+'\n'+fatal+'\n'+nonhud
 extracts[label]={'states':states,'extracted_sha256':hashlib.sha256(fragments.encode()).hexdigest(),'source_sha256':sha(p/label/'cu71_receiver_final_v022.sv')}
 local='localparam [3:0] '+','.join(n+"=4'd"+str(i)for i,n in enumerate(states))+';\n'
 declarations=','.join('input wire '+w+' '+n for w,n in ports)
 wrapper='`timescale 1ns/1ps\nmodule ce_'+label+" #(parameter integer WATCHDOG_CYCLES=32'd3000000000)("+declarations+',output wire hud_prepare_valid,output logic fatal,output logic [7:0]fatal_code,output logic fatal_non_hud,output wire capture_effective);\n'+local+'wire kill,hud_match,hud_write_match;\n'+fragments+'\nassign capture_effective=!rst&&hud_prepare_valid&&!hud_pending;\nendmodule\n'
 (e/(label+'-extracted.sv')).write_text(wrapper)
assert extracts['control']['states']==extracts['candidate']['states']
regs='\n'.join('reg '+w+' '+n+';'for w,n in ports);connect=','.join('.'+n+'('+n+')'for _,n in ports);models=''
for i,wd in enumerate([0,1,3000000000]):
 for label,prefix in [('control','old'),('candidate','new')]:
  models+='ce_'+label+" #(.WATCHDOG_CYCLES(32'd"+str(wd)+')) '+label+str(i)+'('+connect+',.hud_prepare_valid('+prefix+'_p['+str(i)+']),.fatal('+prefix+'_f['+str(i)+']),.fatal_code('+prefix+'_code['+str(i)+']),.fatal_non_hud('+prefix+'_nh['+str(i)+']),.capture_effective('+prefix+'_ce['+str(i)+']));\n'
defaults=''.join(n+"=0;"for _,n in ports)
tb='`timescale 1ns/1ps\nmodule tb;\n'+regs+'\nwire[2:0]old_p,new_p,old_f,new_f,old_nh,new_nh,old_ce,new_ce;wire[7:0]old_code[0:2],new_code[0:2];\n'+models+r'''
integer checked=0,unknown_cases=0,st,mask,flags,i;
task defaults;begin
DEFAULT_ASSIGNMENTS
abort_allowed=1;active_generation=64'h1234567800000042;fid=37;rid=36;hud_expected=128'h123456789abcdef013579bdf2468ace0;bank_write=1;
hud_result_generation=active_generation;hud_result_frame_id=fid;hud_result_reference_id=rid;hud_result_tag=hud_expected;hud_result_words=21120;hud_result_success=1;
hud_drain_generation=active_generation;hud_drain_frame_id=fid;hud_drain_bank=bank_write;hud_drain_tag=hud_expected;hud_drain_words=21120;hud_drain_success=1;
cache_prepare_match=1;cache_prepare_result_success=1;ref_match=1;q_rsp_index=5;q_expected_index=5;packet_pending=1;packet_length=1024;calculated_packet_address=512;
p_code=8'h08;bank_code=8'h07;b_code=8'h39;
end endtask
task check;integer n;begin
 #1;
 for(n=0;n<3;n=n+1)begin
  if(old_p[n]!==new_p[n]||old_ce[n]!==new_ce[n]||old_f[n]!==new_f[n]||old_code[n]!==new_code[n]||old_nh[n]!==new_nh[n])
   $fatal(1,"miter mismatch state=%b mask=%h flags=%h wdcase=%0d oldprep=%b newprep=%b oldfatal=%b newfatal=%b",state,mask,flags,n,old_p[n],new_p[n],old_f[n],new_f[n]);
 end
 checked=checked+1;
end endtask
initial begin
 defaults();
 // Every encoded state, eight independent non-HUD fault drivers, two HUD
 // failure drivers and requested/abort/reset/pending combinations.
 for(st=0;st<16;st=st+1)begin
  state=st;
  for(mask=0;mask<1024;mask=mask+1)begin
   p_error=mask[0];bank_error=mask[1];b_error=mask[2];
   cache_prepare_result_valid=mask[3];cache_prepare_result_success=!mask[3];
   ref_rsp_valid=mask[4];ref_rsp_error=mask[4];q_rsp_valid=mask[5];q_rsp_index=mask[5]?6:5;
   packet_pending=!mask[6];p_req_valid=mask[6];calculated_packet_address=mask[6]?1024:512;
   age=mask[7]?32'd3000000000:0;hud_result_valid=mask[8];hud_result_success=!mask[8];hud_drain_valid=mask[9];hud_drain_success=!mask[9];
   for(flags=0;flags<16;flags=flags+1)begin hud_requested=flags[0];abort_i=flags[1];rst=flags[2];hud_pending=flags[3];check();end
  end
 end
 $display("CE_EXHAUSTIVE_PASS states16 fault_masks1024 control_flags16 checked=%0d watchdog_profiles3",checked);
 for(st=0;st<16;st=st+1)for(i=0;i<17;i=i+1)for(flags=0;flags<16;flags=flags+1)begin
  defaults();state=st;hud_requested=flags[0];abort_i=flags[1];rst=flags[2];hud_pending=flags[3];hud_result_valid=1;hud_drain_valid=1;
  case(i)
   0:hud_result_generation^=64'd1;1:hud_result_generation^=64'h8000000000000000;
   2:hud_result_frame_id^=1;3:hud_result_frame_id^=32'h80000000;
   4:hud_result_reference_id^=1;5:hud_result_words=21119;6:hud_result_words=21121;
   7:hud_result_tag^=128'd1;8:hud_result_tag^=128'h80000000000000000000000000000000;
   9:hud_drain_generation^=1;10:hud_drain_frame_id^=1;11:hud_drain_bank=3;
   12:hud_drain_tag^=1;13:hud_drain_words=0;14:age=1;15:age=32'd2999999999;16:age=32'hffffffff;
  endcase
  ref_rsp_valid=flags[1];ref_rsp_error=flags[1];check();
 end
 for(st=0;st<16;st=st+1)begin defaults();state=st;abort_i=1;abort_allowed=0;b_req_valid=1;packet_pending=0;calculated_packet_address=1024;check();end
 // Directed four-state checks are NOT an exhaustive X/Z formal proof.
 for(st=0;st<16;st=st+1)for(i=0;i<12;i=i+1)begin
  defaults();state=st;hud_result_valid=1;hud_drain_valid=1;
  case(i)
   0:hud_requested=1'bx;1:hud_requested=1'bz;2:abort_i=1'bx;3:rst=1'bx;
   4:state=4'bx101;5:state=4'bz100;6:hud_pending=1'bx;7:hud_result_generation=64'bx;
   8:hud_drain_generation=64'bx;9:hud_result_success=1'bx;10:q_rsp_valid=1'bx;11:p_error=1'bx;
  endcase
  check();unknown_cases=unknown_cases+1;
 end
 $display("CE_DIRECTED_PASS identity_classes17 unknown_cases=%0d total_stimuli=%0d watchdog_profiles3",unknown_cases,checked);
 $display("CE_SOURCE_EXTRACTED_MITER_PASS no_latency_change full_fatal_code_preserved");$finish;
end
initial begin #10000000;$fatal(1,"miter watchdog");end
endmodule
'''
tb=tb.replace('DEFAULT_ASSIGNMENTS',defaults);(e/'tb.sv').write_text(tb)
rows=0
for base,requested,kill,nonhud,hres,hdrain in itertools.product([False,True],repeat=6):
 full=nonhud or(requested and hres)or(requested and hdrain)
 assert(base and not requested and not kill and not full)==(base and not requested and not kill and not nonhud);rows+=1
(e/'boolean-proof.json').write_text(json.dumps({'status':'PASS','exhaustive_independent_boolean_rows':rows,'algebra':'B & !R & !K & !(N | (R & H1) | (R & H2)) == B & !R & !K & !N','scope':'two-state universal reduced Boolean proof; source HUD matches include requested; fatal priority/code unchanged'},indent=2))
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp');env.pop('NoDefaultCurrentDirectoryInExePath',None)
commands=[['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb','-o',str(e/'miter.vvp'),str(e/'control-extracted.sv'),str(e/'candidate-extracted.sv'),str(e/'tb.sv')],['C:/msys64/ucrt64/bin/vvp.exe',str(e/'miter.vvp')]];records=[]
for label,cmd in zip(['compile','run'],commands):
 started=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=240);(e/(label+'.log')).write_text(r.stdout+r.stderr);records.append({'phase':label,'command':cmd,'returncode':r.returncode,'seconds':time.monotonic()-started});(e/'execution.json').write_text(json.dumps({'extracts':extracts,'commands':records},indent=2));print(label,r.returncode,flush=True)
 if r.returncode:print(r.stdout+r.stderr);raise SystemExit(1)
assert 'CE_SOURCE_EXTRACTED_MITER_PASS'in(e/'run.log').read_text()
(e/'bindings.json').write_text(json.dumps({str(f):sha(f)for f in [Path(__file__),p/'control/cu71_receiver_final_v022.sv',p/'candidate/cu71_receiver_final_v022.sv']+list(e.glob('*.sv'))+list(e.glob('*.json'))+list(e.glob('*.log'))},indent=2))
print('CE_FACTOR_OFFLINE_PASS',flush=True)
