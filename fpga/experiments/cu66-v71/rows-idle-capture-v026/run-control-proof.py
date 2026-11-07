"""Exact RTL projection: controls + payload ownership, not full RAM/output proof."""
from pathlib import Path
import hashlib,json,re,shlex,subprocess,time
p=Path(__file__).resolve().parent;e=p/'proof02';e.mkdir();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
fields='active,input_done,current_frame,current_key,bank_full,bank_last,fill_bank,read_bank,tile_column,write_row,write_address,write_busy,cache_valid,prefix_pending,prefix_index,read_word,read_byte,expected_plane,expected_index,done,error,aborted,error_code,accepted_tiles,emitted_bytes,strip_word_writes,strip_word_reads,input_stall_cycles,output_stall_cycles,ram_write_enable,ram_read_enable,ram_read_bank,ram_read_address,proof_bank_words'
for file,mod in [('cu71_tile_rows_reference.sv','cu71_tile_rows_reference'),('cu71_tile_rows.sv','cu71_tile_rows')]:
 s=(p/file).read_text();s=s.replace('module '+mod+' #(','module '+mod+'_proof #(')
 s,n=re.subn(r'(output logic \[16:0\] expected_index)\n\);',r'\1,output wire[511:0]proof_payload,output wire[511:0]proof_control,output wire proof_validity\n);',s);assert n==1
 appendix='''
wire[19:0]proof_bank_words;
generate if(STRIP_BANKS==2)begin
 assign proof_bank_words={bank_full[1]?bank_words[1]:10'd0,bank_full[0]?bank_words[0]:10'd0};
end else begin
 assign proof_bank_words={10'd0,bank_full[0]?bank_words[0]:10'd0};
end endgenerate
assign proof_payload=captured_tile;
assign proof_validity=(!cache_valid || bank_full[read_bank]);
assign proof_control={'''+fields+'''};
'''
 s=s.replace('endmodule',appendix+'endmodule');(e/file).write_text(s)
top='''module row_miter #(parameter BANKS=1)(input clk,rst,abort_i,start_valid,key,tile_valid,tile_key,tile_last,data_ready,input[31:0]frame_id,tile_frame_id,input[511:0]tile_pixels,input[1:0]tile_plane,input[16:0]tile_index,output ok,owned);
wire[511:0]a_control,b_control,a_payload,b_payload;wire a_busy,b_busy,a_validity,b_validity;
cu71_tile_rows_reference_proof #(.STRIP_BANKS(BANKS)) a(.clk,.rst,.abort_i,.start_valid,.key,.tile_valid,.tile_key,.tile_last,.data_ready,.frame_id,.tile_frame_id,.tile_pixels,.tile_plane,.tile_index,.proof_control(a_control),.proof_payload(a_payload),.proof_validity(a_validity),.write_busy(a_busy));
cu71_tile_rows_proof #(.STRIP_BANKS(BANKS)) b(.clk,.rst,.abort_i,.start_valid,.key,.tile_valid,.tile_key,.tile_last,.data_ready,.frame_id,.tile_frame_id,.tile_pixels,.tile_plane,.tile_index,.proof_control(b_control),.proof_payload(b_payload),.proof_validity(b_validity),.write_busy(b_busy));
assign owned=a_busy;assign ok=a_validity && b_validity && a_control==b_control && a_busy==b_busy && (!a_busy || a_payload==b_payload);
endmodule
'''
(e/'miter.sv').write_text(top)
mutant=(e/'cu71_tile_rows.sv').read_text().replace('if(!write_busy) captured_tile<=tile_pixels;','captured_tile<=tile_pixels;');assert mutant!=(e/'cu71_tile_rows.sv').read_text();(e/'mutant.sv').write_text(mutant)
rows=[];lin=lambda f:'/mnt/c/'+f.as_posix()[3:]
for mode,banks in [('induction',1),('induction',2),('negative',2),('nonvacuity',2)]:
 label=mode+'-banks'+str(banks);d=e/label;d.mkdir();src=[e/'cu71_tile_rows_reference.sv',e/('mutant.sv' if mode=='negative'else 'cu71_tile_rows.sv'),e/'miter.sv']
 ys='read_verilog -sv '+' '.join(lin(f) for f in src)+'; hierarchy -top row_miter -chparam BANKS '+str(banks)+'; proc; flatten; opt; memory_map; opt; '
 if mode=='induction':ys+='sat -seq 2 -set-at 1 rst 1 -prove ok 1 -tempinduct -maxsteps 6 -verify'
 else:ys+='sat -seq 6 -set-at 1 rst 1 '+''.join('-set-at '+str(i)+' rst 0 'for i in range(2,7))+('-prove owned 0' if mode=='nonvacuity'else'-prove ok 1')+' -show owned -show ok -verify'
 (d/'executed.ys').write_text(ys+'\n');cmd=['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && export OMP_NUM_THREADS=1 && timeout 120s yosys -Q -T -s '+shlex.quote(lin(d/'executed.ys'))];start=time.monotonic()
 with(d/'yosys.log').open('x') as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 log=(d/'yosys.log').read_text(errors='replace');expected=mode!='induction';passed=(q.returncode!=0 and 'model found: FAIL!'in log)if expected else(q.returncode==0 and 'Induction step proven: SUCCESS!'in log)
 rows.append(dict(mode=mode,banks=banks,passed=passed,expected_counterexample=expected,returncode=q.returncode,seconds=time.monotonic()-start,cmd=cmd,script_sha256=sha(d/'executed.ys'),log_sha256=sha(d/'yosys.log'),sources_sha256={f.name:sha(f) for f in src}));(e/'execution.json').write_text(json.dumps(rows,indent=2));print(label,passed,q.returncode,flush=True)
 if not passed:print(log[-2200:]);raise SystemExit(1)
(e/'result.json').write_text(json.dumps(dict(status='PASS_EXACT_CONTROL_PROJECTION_AND_OWNED_PAYLOAD_INDUCTION',source_sha256={f:sha(p/f) for f in ['cu71_tile_rows.sv','cu71_tile_rows_reference.sv']},scope='Actual RTL controls, qualified bank metadata, RAM write authority and write_busy=>512-bit payload equality. Unobserved strip RAM/output data optimized away; not full-memory or whole-codec equivalence. Native/full raster checks remain separate.',negative_and_nonvacuity=True),indent=2)+'\n')
