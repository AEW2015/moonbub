#!/usr/bin/env python3
"""Reversible two-bank representation of one existing pending record tuple."""
import argparse,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v116c-record';V=S/'verification';B=R/'fpga/experiments/cu66-v116b-control'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def transform(t,edits):
 for b,a in edits:assert t.count(b)==1,(b,t.count(b));t=t.replace(b,a,1)
 return t
STORAGE='''    logic [31:0] pending_record;
    logic [2:0] pending_bytes;
    logic [31:0] pending_position;
    // Two physical speculative banks represent ONE logical pending tuple.
    // Only the small view selector sees the original acceptance/kill priority.
    logic record_view_bank=0, record_view_seen=0;
    logic [31:0] record_payload [0:1], position_payload [0:1];
    logic [2:0] bytes_payload [0:1];
    logic [66:0] prospective_record;
    assign prospective_record={
        (raw_mode || phase==0 ? {16'd0,coef_value} : {coef_block[12:0],coef_index,coef_value[12:0]}),
        (raw_mode || phase==0 ? 3'd2 : 3'd4),input_position};
    for(genvar record_bank=0;record_bank<2;record_bank=record_bank+1)begin: pending_storage
        // Continuously refresh only the inactive bank. No reset, cancel,
        // input_bad, coef_valid, phase or format predicate gates this write.
        always_ff @(posedge clk)if(record_view_bank!=1'(record_bank))
            {record_payload[record_bank],bytes_payload[record_bank],position_payload[record_bank]}<=prospective_record;
    end
    // Before the first original write, the initialized two-state view is zero.
    // All warm reset/abort/error edges retain this logical view exactly.
    assign pending_record=record_view_seen ? record_payload[record_view_bank] : 32'd0;
    assign pending_bytes=record_view_seen ? bytes_payload[record_view_bank] : 3'd0;
    assign pending_position=record_view_seen ? position_payload[record_view_bank] : 32'd0;'''
OLDWRITE='''                            pending_record<=raw_mode || phase==0 ? {16'd0,coef_value} :
                                {coef_block[12:0],coef_index,coef_value[12:0]};
                            pending_bytes<=raw_mode || phase==0 ? 2 : 4;
                            pending_position<=input_position; begin state<=APPEND; busy_owned<=1'b1; end'''
NEWWRITE='''                            record_view_bank<=!record_view_bank; record_view_seen<=1;
                            begin state<=APPEND; busy_owned<=1'b1; end'''
ASSERTIONS='''`ifndef SYNTHESIS
    // Frozen old three-field shadow. Its eligibility independently spells out
    // the ORIGINAL main outer priority; response_failure is deliberately not
    // used because a matching error without prefetch/write ownership falls in.
    logic [31:0] record_shadow=0,position_shadow=0;
    logic [2:0] bytes_shadow=0;
    logic record_shadow_event;
    logic record_check_initialized=0,record_previous_bank,record_previous_event;
    logic [66:0] record_previous_prospective;
    logic [66:0] record_previous_physical [0:1];
    always_comb record_shadow_event=!cancel &&
        !(mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch)) &&
        state!=DRAIN &&
        !(prefetch_offer && outstanding && mem_rsp_valid && mem_rsp_error) &&
        !(overlap_mode && write_slot_valid && outstanding && mem_rsp_valid && mem_rsp_error) &&
        state==INGEST && coef_valid && !input_bad;
    always_ff @(posedge clk)begin
        assert({pending_record,pending_bytes,pending_position}=={record_shadow,bytes_shadow,position_shadow})
            else $fatal(1,"V116C exact old pending tuple shadow mismatch");
        if(record_check_initialized)begin
            assert(record_view_bank==(record_previous_bank^record_previous_event))
                else $fatal(1,"V116C view selector changed outside original write");
            for(integer n=0;n<2;n=n+1)begin
                if(1'(n)==record_previous_bank)
                    assert({record_payload[n],bytes_payload[n],position_payload[n]}==record_previous_physical[n])
                        else $fatal(1,"V116C selected physical tuple was overwritten");
                else
                    assert({record_payload[n],bytes_payload[n],position_payload[n]}==record_previous_prospective)
                        else $fatal(1,"V116C inactive bank missed complete speculative tuple");
            end
            if(record_previous_event)assert(record_view_seen)
                else $fatal(1,"V116C original pending write not made visible");
        end
        if(record_shadow_event)begin
            record_shadow<=raw_mode || phase==0 ? {16'd0,coef_value} :
                {coef_block[12:0],coef_index,coef_value[12:0]};
            bytes_shadow<=raw_mode || phase==0 ? 2 : 4;
            position_shadow<=input_position;
        end
        record_check_initialized<=1;
        record_previous_bank<=record_view_bank;record_previous_event<=record_shadow_event;
        record_previous_prospective<=prospective_record;
        for(integer n=0;n<2;n=n+1)
            record_previous_physical[n]<={record_payload[n],bytes_payload[n],position_payload[n]};
    end
`endif
'''
EDITS=[('    logic [31:0] pending_record;\n    logic [2:0] pending_bytes;\n    logic [31:0] pending_position;',STORAGE),(OLDWRITE,NEWWRITE),('endmodule',ASSERTIONS+'endmodule')]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();recipes=[];adapters=[]
 def emit(src,dst,edits,production=False):
  t=transform(src.read_text(),edits)
  if a.write:dst.write_text(t)
  assert dst.read_text()==t
  for b,c in reversed(edits):assert t.count(c)==1;t=t.replace(c,b,1)
  assert t==src.read_text()
  row=dict(original=rel(src),original_sha256=sha(src),candidate=rel(dst),candidate_sha256=sha(dst),edits=[dict(before=b,after=c)for b,c in edits]);(recipes if production else adapters).append(row)
 old=B/'packed_scratch_v91g2.sv';new=S/old.name
 assert sha(old)=='98060d865bb74de8e8430a3d0d2edb6f7a8670772f52106dc79e404d8f48a87a'
 emit(old,new,EDITS,True)
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',old.read_text(),re.S):assert block in new.read_text()
 # Preserve B's exact observability edits, now both references use current B.
 previous=json.loads((B/'edit-recipes.json').read_text())
 instrumentation=next(e['edits']for e in previous['adapters']if e['candidate'].endswith('/observed_candidate.sv'))
 instrumentation=[(e['before'],e['after'])for e in instrumentation]
 emit(old,V/'observed_original.sv',[(b,c.replace('observed_candidate','observed_original'))for b,c in instrumentation])
 emit(new,V/'observed_candidate.sv',instrumentation)
 # All generic old port/body checkers remain present. Connect the now-common
 # owned-target port explicitly, and compare all three old logical private names.
 probe=B/'verification/scratch_probe.sv'
 text=probe.read_text();mark='observed_original original (';tail=text[text.index(mark):text.index('observed_candidate candidate (')]
 changed=tail.replace('.abort_valid(abort_valid),','.owned_abort_epoch(reference_owned_abort_target), .abort_valid(abort_valid),',1)
 emit(probe,V/'scratch_probe.sv',[
  (tail,changed),
  ('    logic [31:0] candidate_owned_abort_target;','    logic [31:0] candidate_owned_abort_target,reference_owned_abort_target;'),
  ('endmodule','''    always_ff @(posedge clk)begin
        assert(reference_owned_abort_target==candidate_owned_abort_target)
            else $fatal(1,"V116C exact generic abort target pair mismatch");
        assert({original.pending_record,original.pending_bytes,original.pending_position}==
            {candidate.pending_record,candidate.pending_bytes,candidate.pending_position})
            else $fatal(1,"V116C exact generic private pending tuple pair mismatch");
    end
endmodule''')])
 for n in ('clock_adapter.hpp','historical_hazards.cpp','tb_scratch.cpp','tb_bank.cpp','tb_prepare.cpp','tb_slot.cpp','pair_adapter.hpp','caller_prepare.cpp','tb_pipeline.cpp'):
  emit(B/'verification'/n,V/n,[])
 emit(B/'verification/tb_control.cpp',V/'tb_control.cpp',[('int main(int argc,char**argv)','int inherited_control_main(int argc,char**argv)')])
 emit(B/'verification/br88_pipeline_pair.sv',V/'br88_pipeline_pair.sv',[
  ('endmodule','''    always_ff @(posedge clk)
        assert({reference.scratch.pending_record,reference.scratch.pending_bytes,reference.scratch.pending_position}==
            {candidate.scratch.pending_record,candidate.scratch.pending_bytes,candidate.scratch.pending_position})
            else $fatal(1,"V116C exact real-caller private pending tuple mismatch");
endmodule''')])
 # Actual selected B caller is unchanged; only scratch implementation differs.
 caller=B/'br88_pipeline_v91h.sv';assert sha(caller)=='2eef50dfe32a5c84cebf207dc9c56ac69b933ea0371e0b7e372681adacc4ad0e'
 emit(old,V/'packed_scratch_reference.sv',[('module packed_scratch_v91g2 (','module packed_scratch_reference (')])
 emit(caller,V/'br88_pipeline_reference.sv',[
  ('module br88_pipeline_v91h #(','module br88_pipeline_reference #('),
  ('    packed_scratch_v91g2 scratch (','    packed_scratch_reference scratch (')])
 emit(caller,V/'br88_pipeline_candidate.sv',[('module br88_pipeline_v91h #(','module br88_pipeline_candidate #(')])
 q=dict(schema='v116c-two-bank-one-logical-record-v1',declared_public_cycle_delta=0,logical_pending_capacity=1,physical_banks=2,recipes=recipes,adapters=adapters,unchanged_caller=dict(path=rel(caller),sha256=sha(caller)))
 if a.write:write(S/'edit-recipes.json',q)
 else:assert json.loads((S/'edit-recipes.json').read_text())==q
 print('V116C_RECORD_PREPARED_NOT_RUN',sha(new))
if __name__=='__main__':main()
