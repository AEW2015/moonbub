#!/usr/bin/env python3
"""Prepare source-exact producer readiness predicates and whole-body pair."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-ready';AREA=ROOT/'experiments/python-gamebub-v110/ready';OLD=ROOT/'fpga/experiments/cu66-v109-fault/cs88_coefficients_v91k.sv';HASH='5f18c913b6f2702e8f1036ba70b3ba7328d7cdbdfbc8810972c577bee167e86b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def main():
 assert sha(OLD)==HASH;s=OLD.read_text();edits=[];inventory=[]
 def edit(before,after):
  nonlocal s
  assert s.count(before)==1,(before,s.count(before));s=s.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
 edit('    logic frame_running, accepted_start;','    logic frame_running, accepted_start;\n    logic frame_running_owned, cache_nonzero_owned;')
 for line in list(dict.fromkeys(x for x in s.splitlines()if re.search(r'\b(state|cache_count)\s*<=',x))):
  def pair(m):
   name,rhs=m.groups();active=rhs not in ('IDLE','FINISHED','FAILED') if name=='state'else None
   expr=("1'b1"if active else"1'b0")if name=='state'else("1'b0"if rhs=='0'else"(11'(cache_count+1)!=0)")
   flag='frame_running_owned'if name=='state'else'cache_nonzero_owned'
   inventory.append(dict(variable=name,rhs=rhs,predicate=flag,predicate_rhs=expr,original_line=OLD.read_text().count('\n',0,OLD.read_text().index(line))+1,classification=('active'if active else'quiescent')if name=='state'else('clear'if rhs=='0'else'increment_11bit_wrap')))
   return 'begin '+m[0]+flag+'<='+expr+'; end '
  edit(line,re.sub(r'\b(state|cache_count)\s*<=\s*([^;]+);',pair,line))
 assert sum(x['variable']=='state'for x in inventory)==31 and sum(x['variable']=='cache_count'for x in inventory)==3
 edit('    assign frame_running=state!=IDLE&&state!=FINISHED&&state!=FAILED;','    assign frame_running=frame_running_owned;')
 edit('    assign busy=frame_running||child_busy||cache_count!=0;','    assign busy=frame_running||child_busy||cache_nonzero_owned;')
 edit('    assign start_ready=!frame_running&&!child_busy&&!child_draining&&cache_count==0&&!reset&&!abort_packet;','    assign start_ready=!frame_running&&!child_busy&&!child_draining&&!cache_nonzero_owned&&!reset&&!abort_packet;')
 addition='''`ifndef SYNTHESIS
    // Once reset/abort has initialized both original and redundant state,
    // compare every edge, including reset, failure, abort, start and sticky hold.
    logic readiness_initialized=0;
    always_ff @(posedge clk)begin
        if(reset||abort_packet)readiness_initialized<=1;
        if(readiness_initialized)begin
            assert(frame_running_owned==(state!=IDLE&&state!=FINISHED&&state!=FAILED)) else $fatal(1,"producer running predicate mismatch");
            assert(cache_nonzero_owned==(cache_count!=0)) else $fatal(1,"producer cache predicate mismatch");
        end
    end
`endif
'''
 edit('endmodule',addition+'endmodule');p=SRC/OLD.name;p.write_text(s);rev=s
 for e in reversed(edits):assert rev.count(e['after'])==1;rev=rev.replace(e['after'],e['before'],1)
 assert rev==OLD.read_text()
 entry=dict(original=str(OLD.relative_to(ROOT)),original_sha256=HASH,candidate=str(p.relative_to(ROOT)),candidate_sha256=sha(p),edits=edits)
 write(SRC/'edit-recipe.json',dict(schema='v110-producer-ready-owned-predicates-v1',status='PREPARED_NOT_RTL_QUALIFIED',production={p.name:entry},all_write_inventory=inventory,added_public_cycles=0,source_rule='Every original state/count assignment receives predicate for its actual next value. Original branch/hold/last-write priority retained; no registered current-state sample.',preserved='All original assertions, public outputs including invalid values, counters, cache writes/tags/errors, fault ack/cancel/abort/start priorities.'))
 out=SRC/'verification';adapters=[]
 for suffix,path in [('original',OLD),('candidate',p)]:
  text=path.read_text();text=text.replace('module cs88_coefficients_v91k #','module ready_'+suffix+' #',1);q=out/('ready_'+suffix+'.sv');q.write_text(text);adapters.append(dict(source=str(path.relative_to(ROOT)),source_sha256=sha(path),path=str(q.relative_to(ROOT)),sha256=sha(q),module_rename=['cs88_coefficients_v91k','ready_'+suffix]))
 header=OLD.read_text().split('\n);',1)[0]+'\n);';body=header.split(') (',1)[1].rsplit(');',1)[0];body=re.sub(r'//[^\n]*','',body);ports=[];inherited=None
 for item in body.split(','):
  item=item.strip();m=re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s+)?(.+)',item,re.S)
  if m:direction,signed,packed,item=m.groups();inherited=(direction,signed or'',packed or'')
  name=re.fullmatch(r'(\w+)(\s*\[\d+:\d+\])?',item);assert name,(item,inherited);ports.append(dict(name=name[1],array=name[2]or'',direction=inherited[0],signed=inherited[1],packed=inherited[2]))
 header=re.sub(r'module cs88_coefficients_v91k #\(parameter integer REFILL_OVERLAP=1\)', 'module ready_probe',header,count=1)
 extra=', output logic probe_public_equal,probe_internal_equal, output logic [10:0] probe_count, output logic [31:0] probe_cached_fid, output logic [63:0] probe_cached_generation, output logic probe_running,probe_nonzero,probe_accepted_start,probe_scale_commit, output logic [10:0] probe_scale_address, output logic [1:0] probe_scale_data, input logic [10:0] verify_scale_index, output logic [1:0] verify_scale_data, output logic probe_scale_equal);'
 lines=[header.replace(');',extra,1)]
 for v in ports:
  if v['direction']=='output':lines.append('logic '+v['signed']+v['packed']+'old_'+v['name']+v['array']+';')
 for suffix in ('original','candidate'):
  lines.append('ready_'+suffix+' '+('old_dut'if suffix=='original'else'new_dut')+'('+','.join('.'+v['name']+'('+('old_'if suffix=='original'and v['direction']=='output'else'')+v['name']+')'for v in ports)+');')
 lines.append('assign probe_public_equal='+'&&'.join('(old_'+v['name']+'=='+v['name']+')'for v in ports if v['direction']=='output')+';')
 internal=['state','frame_epoch','latched_size','last_frame_epoch','child_nonce','plane','tile_cursor','mapped_tile','mapped_cell','producer_cell_cache','mapped_scale','expected_block','refill_cursor','selected_offset','selected_length','selected_blocks','refill_data','child_owned','cache_count','cached_fid','cached_generation','lookup_owner_reconstruct']
 lines.append('assign probe_internal_equal='+'&&'.join('(old_dut.'+n+'==new_dut.'+n+')'for n in internal)+';')
 for a,b in [('probe_count','cache_count'),('probe_cached_fid','cached_fid'),('probe_cached_generation','cached_generation'),('probe_running','frame_running_owned'),('probe_nonzero','cache_nonzero_owned'),('probe_accepted_start','accepted_start')]:lines.append('assign '+a+'=new_dut.'+b+';')
 lines+=['assign probe_scale_commit=new_dut.admission.scale_store.a_commit;','assign probe_scale_address=new_dut.admission.scale_store.a_addr;','assign probe_scale_data=new_dut.admission.scale_store.a_data;','assign verify_scale_data=new_dut.admission.scale_store.words[verify_scale_index];','assign probe_scale_equal=(old_dut.admission.scale_store.words==new_dut.admission.scale_store.words);','endmodule']
 (out/'ready_probe.sv').write_text('\n'.join(lines)+'\n');write(out/'adapters.json',dict(adapters=adapters,ports=ports,internal_comparisons=internal,assertions_removed=False,all_public_outputs_compared=True,all_raw_scale_words_compared=True))
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL',candidate_sha256=sha(p),original_sha256=HASH,recipe_sha256=sha(SRC/'edit-recipe.json'),state_writes=31,cache_count_writes=3))
 write(out/'input-ports.json',[v for v in ports if v['direction']=='input'])
 print('READY_PREPARED_NOT_RUN',sha(p))
if __name__=='__main__':main()
