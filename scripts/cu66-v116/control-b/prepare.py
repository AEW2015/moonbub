#!/usr/bin/env python3
"""Reversible exact owned-target feedback cut, with faithful paired adapters."""
import argparse,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v116b-control';V=S/'verification'
OLD=R/'fpga/experiments/cu66-v115-refined-scratch';CALLER=R/'fpga/experiments/cu66-v108-capacity/br88_pipeline_v91h.sv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def transform(t,edits):
 for b,a in edits:assert t.count(b)==1,(b,t.count(b));t=t.replace(b,a,1)
 return t
SCRATCH=[
 ('    output logic [31:0] active_epoch=0, output logic [18:0] used_bytes,','    output logic [31:0] owned_abort_epoch,\n    output logic [31:0] active_epoch=0, output logic [18:0] used_bytes,'),
 ('    logic cancel;','    logic cancel;\n    // Exact existing target; generic foreign-epoch abort semantics are unchanged.\n    assign owned_abort_epoch=preparing_begin ? queued_epoch : active_epoch;'),
 ('cancel=reset || (abort_valid && abort_epoch==(preparing_begin ? queued_epoch : active_epoch));','cancel=reset || (abort_valid && abort_epoch==owned_abort_epoch);'),
 ('endmodule','''`ifndef SYNTHESIS
    // No reset/abort/response_failure disable: prove the owner relation through
    // the cancellation edge itself, including rejected descriptors and drains.
    always_ff @(posedge clk)begin
        if(state==IDLE)assert(!outstanding)
            else $fatal(1,"V116B IDLE retained physical debt");
        if(preparing_begin)begin
            assert(active_epoch==queued_epoch)
                else $fatal(1,"V116B preparing owner epochs diverged");
            assert(!outstanding)
                else $fatal(1,"V116B preparation acquired physical debt");
        end
        assert(owned_abort_epoch==(preparing_begin ? queued_epoch : active_epoch))
            else $fatal(1,"V116B selected abort target mismatch");
        assert(cancel==(reset || (abort_valid && abort_epoch==(preparing_begin ? queued_epoch : active_epoch))))
            else $fatal(1,"V116B generic abort-epoch semantics changed");
    end
`endif
endmodule''')]
CALL_EDITS=[
 ('    logic [31:0] store_epoch;','    logic [31:0] store_epoch;\n    logic [31:0] store_owned_abort_epoch;'),
 ('        .abort_valid(store_abort), .abort_epoch(store_epoch),','        .abort_valid(store_abort), .abort_epoch(store_owned_abort_epoch),\n        .owned_abort_epoch(store_owned_abort_epoch),'),
 ('endmodule','''`ifndef SYNTHESIS
    // This caller formerly fed back active_epoch. Check the exact substitution
    // precondition on every real abort, including reset/start/fault/drain edges.
    always_ff @(posedge clk)if(store_abort)
        assert(store_epoch==store_owned_abort_epoch)
            else $fatal(1,"V116B caller changed abort ownership");
`endif
endmodule''')]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();recipes=[];adapters=[]
 def emit(src,dst,edits,production=False):
  text=transform(src.read_text(),edits)
  if a.write:dst.write_text(text)
  assert dst.read_text()==text
  for b,c in reversed(edits):assert text.count(c)==1;text=text.replace(c,b,1)
  assert text==src.read_text()
  row=dict(original=rel(src),original_sha256=sha(src),candidate=rel(dst),candidate_sha256=sha(dst),edits=[dict(before=b,after=c)for b,c in edits])
  (recipes if production else adapters).append(row)
 assert sha(OLD/'packed_scratch_v91g2.sv')=='2b9dbaf7fb25d7fdc8219a69dc59588b4c1bb2e7da374c6edaf223a5c1ac52d1'
 assert sha(CALLER)=='cb440ed9c12c6fa3eac579aea99f2c03716e33b97ce50822ab00b93de08a4360'
 emit(OLD/'packed_scratch_v91g2.sv',S/'packed_scratch_v91g2.sv',SCRATCH,True)
 emit(CALLER,S/'br88_pipeline_v91h.sv',CALL_EDITS,True)
 for row in recipes:
  for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',(R/row['original']).read_text(),re.S):assert block in(R/row['candidate']).read_text()
 # Same current V115 reference and candidate instrumentation; no historical
 # reference schedule differences and no candidate-only comparison intervals.
 meta=json.loads((OLD/'verification/adapters.json').read_text())
 edits=next(x['edits']for x in meta['adapters']if Path(x['path']).name=='observed_candidate.sv')
 emit(OLD/'packed_scratch_v91g2.sv',V/'observed_original.sv',[(b,c.replace('observed_candidate','observed_original'))for b,c in edits])
 emit(S/'packed_scratch_v91g2.sv',V/'observed_candidate.sv',edits)
 probe=(OLD/'verification/scratch_probe.sv').read_text()
 # Add explicit new output connection only on the candidate instantiation.
 marker='observed_candidate candidate (';assert marker in probe
 at=probe.index(marker);tail=probe[at:];connection='.abort_valid(abort_valid)';assert connection in tail
 replacement=tail.replace(connection,'.owned_abort_epoch(candidate_owned_abort_target), '+connection,1)
 emit(OLD/'verification/scratch_probe.sv',V/'scratch_probe.sv',[
  (tail,replacement),
  ('    logic  old_begin_ready;','    logic [31:0] candidate_owned_abort_target;\n    logic  old_begin_ready;'),
  ('endmodule','''    // Check the live new port against the exact old private target every edge.
    // No reset/abort/response-failure mask and no unused observability wire.
    always_ff @(posedge clk)begin
        assert(candidate_owned_abort_target==(original.preparing_begin ? original.queued_epoch : original.active_epoch))
            else $fatal(1,"V116B probe selected abort target differs from old target");
    end
endmodule''')])
 for n in ('tb_scratch.cpp','tb_bank.cpp','historical_hazards.cpp','tb_prepare.cpp'):
  emit(OLD/'verification'/n,V/n,[])
 emit(OLD/'verification/tb_slot.cpp',V/'tb_slot.cpp',[
  ('NEW(read_tag_match)=1;','BOTH(read_tag_match,1);'),
  ('int main(int argc,char**argv)','int inherited_slot_main(int argc,char**argv)')])
 # Separate caller reference uses frozen scratch, while candidate uses new one.
 emit(OLD/'packed_scratch_v91g2.sv',V/'packed_scratch_reference.sv',[('module packed_scratch_v91g2 (','module packed_scratch_reference (')])
 emit(CALLER,V/'br88_pipeline_reference.sv',[
  ('module br88_pipeline_v91h #(','module br88_pipeline_reference #('),
  ('    packed_scratch_v91g2 scratch (','    packed_scratch_reference scratch (')])
 emit(S/'br88_pipeline_v91h.sv',V/'br88_pipeline_candidate.sv',[('module br88_pipeline_v91h #(','module br88_pipeline_candidate #(')])
 emit(R/'fpga/experiments/cu66-v91h/tb_pipeline.cpp',V/'tb_pipeline.cpp',[
  ('using Pipeline=Vbr88_pipeline_v91h;','#include "pair_adapter.hpp"\nusing Pipeline=Pipeline_checked;'),
  ('int main(int argc,char** argv) {','#include "caller_prepare.cpp"\nint main(int argc,char** argv) {'),
  ('        unsigned checks=sim.directed(*simple,*raw);','        const unsigned caller_prepare_checks=caller_prepare_cancels(sim,*simple,*raw);\n        unsigned checks=sim.directed(*simple,*raw);'),
  ('<<",\\\"sync_staging_checks\\\":"<<staging_checks','<<",\\\"caller_prepare_checks\\\":"<<caller_prepare_checks<<",\\\"sync_staging_checks\\\":"<<staging_checks')])
 # Generate full original port and array comparison, with no excluded raw output.
 head=CALLER.read_text().split('module br88_pipeline_v91h #(parameter integer SYNC_STAGING=1) (',1)[1].split('\n);',1)[0]
 direction=None;width='';ports=[]
 for segment in re.split(r',(?=\s*(?:input|output)\b)|,',head):
  segment=segment.strip()
  m=re.match(r'(input|output)\s+logic\s*(signed\s*)?(\[[^]]+\]\s*)?(.*)',segment,re.S)
  if m:direction=m.group(1);width=(m.group(2)or'')+(m.group(3)or'');names=m.group(4)
  else:names=segment
  if names:ports.append((direction,width,*re.match(r'(\w+)\s*(\[[^]]+\])?$',names).groups()))
 lines=['module br88_pipeline_v91h #(parameter integer SYNC_STAGING=1) ('+head+',\n    output logic pair_equal, output logic [63:0] pair_edges\n);']
 checks=[]
 for d,w,n,array in ports:
  if d=='output':
   lines.append('    logic '+w+'old_'+n+(' '+array if array else '')+';')
   if array:
    lim=int(array.strip('[]').split(':')[1]);checks += [f'(old_{n}[{i}]==={n}[{i}])'for i in range(lim+1)]
   else:checks.append(f'(old_{n}==={n})')
 for module,instance,old in [('br88_pipeline_candidate','candidate',False),('br88_pipeline_reference','reference',True)]:
  conns=[f'.{n}({"old_"if old and d=="output"else""}{n})'for d,w,n,array in ports]
  lines.append(f'    {module} #(.SYNC_STAGING(SYNC_STAGING)) {instance}('+','.join(conns)+');')
 lines += ['    assign pair_equal='+' &&\n        '.join(checks)+';','    initial pair_edges=0;','    always_ff @(posedge clk)begin','        pair_edges<=pair_edges+1;','        assert(pair_equal)else $fatal(1,"V116B exact caller public-output mismatch");','    end','endmodule']
 wrapper='\n'.join(lines)+'\n'
 if a.write:(V/'br88_pipeline_pair.sv').write_text(wrapper)
 assert(V/'br88_pipeline_pair.sv').read_text()==wrapper
 manifest=dict(schema='v116b-private-selected-abort-feedback-v1',declared_public_cycle_delta=0,recipes=recipes,adapters=adapters,caller_compared_outputs=len(checks),caller_ports_source_sha256=sha(CALLER))
 if a.write:write(S/'edit-recipes.json',manifest)
 else:assert json.loads((S/'edit-recipes.json').read_text())==manifest
 print('V116B_PREPARED_NOT_RUN',json.dumps({Path(x['candidate']).name:x['candidate_sha256']for x in recipes}))
if __name__=='__main__':main()
