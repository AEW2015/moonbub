#!/usr/bin/env python3
"""Prepare exact count-prefix shadow experiment; never edits selected sources."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'fpga/experiments/cu66-v107-plan-prefix'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 entries=[]
 def save(relative,edits):
  p=ROOT/relative;s=p.read_text()
  for e in edits:assert s.count(e['before'])==e.get('expected_occurrences',1),(relative,e['before']);s=s.replace(e['before'],e['after'],1)
  q=OUT/p.name;q.write_text(s);entries.append(dict(original=relative,original_sha256=sha(p),candidate=str(q.relative_to(ROOT)),candidate_sha256=sha(q),edits=edits))
 def edit(before,after):return dict(before=before,after=after,expected_occurrences=1)
 ingress='fpga/experiments/cu66-v107-guard-dsp/br88_packet_ingress_sync_v91h.sv'
 extra='''    // Unowned until this packet reaches METADATA; no payload reset.
    logic [31:0] plan_align1, plan_align2, plan_align3;
    logic [31:0] plan_prefix12, plan_prefix123;
    logic prefix_header_capture;
    function automatic logic [31:0] count_aligned(input logic [31:0] n);
        return ((n<<2)+32'd15)&32'hfffffff0;
    endfunction
    assign meta_prefix1=plan_align1;
    assign meta_prefix12=plan_prefix12;
    assign meta_prefix123=plan_prefix123;
    // Match the actual FETCH_WAIT store guard, including wrong-response and
    // active context done/failure priority. Forward the current high byte.
    assign prefix_header_capture=!cancelled&&!context_failure&&
        !(context_active&&ctx_done)&&state==FETCH_WAIT&&stage_read_rsp&&
        ram_epoch==context_epoch&&ram_addr==fetch_address&&fetch_kind==F_HEADER;
    always_ff @(posedge clk)begin
        if(prefix_header_capture)begin
            if(fetch_index==6'd33)plan_align1<=count_aligned({ram_data,fetch_bytes[32],fetch_bytes[31],fetch_bytes[30]});
            if(fetch_index==6'd37)plan_align2<=count_aligned({ram_data,fetch_bytes[36],fetch_bytes[35],fetch_bytes[34]});
            if(fetch_index==6'd41)plan_align3<=count_aligned({ram_data,fetch_bytes[40],fetch_bytes[39],fetch_bytes[38]});
        end
        plan_prefix12<=plan_align1+plan_align2;
        plan_prefix123<=plan_prefix12+plan_align3;
    end
'''
 save(ingress,[edit('    output logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch,','    output logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch,\n    output logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123,'),edit('    function automatic logic [31:0] cached32(input integer at);',extra+'\n    function automatic logic [31:0] cached32(input integer at);'),edit('`ifndef SYNTHESIS\n','''`ifndef SYNTHESIS
    always_ff @(posedge clk)if(meta_valid)begin
        assert(meta_prefix1==count_aligned(meta_count1))else $fatal(1,"prefix1 stale metadata owner");
        assert(meta_prefix12==count_aligned(meta_count1)+count_aligned(meta_count2))else $fatal(1,"prefix12 stale metadata owner");
        assert(meta_prefix123==count_aligned(meta_count1)+count_aligned(meta_count2)+count_aligned(meta_count3))else $fatal(1,"prefix123 stale metadata owner");
    end
    assert property (@(posedge clk)disable iff(cancelled)
        meta_valid&&!meta_ready |=> cancelled || (meta_valid&&$stable({meta_prefix1,meta_prefix12,meta_prefix123})))
        else $fatal(1,"held metadata prefixes changed");
''')])
 save('fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv',[
 edit('    output logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch,','    output logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch,\n    output logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123,'),
 edit("        assign stage_read_req='0;","""        // Legacy branch has no header-fetch cache; preserve exact count algebra.
        assign meta_prefix1=((meta_count1<<2)+32'd15)&32'hfffffff0;
        assign meta_prefix12=meta_prefix1+(((meta_count2<<2)+32'd15)&32'hfffffff0);
        assign meta_prefix123=meta_prefix12+(((meta_count3<<2)+32'd15)&32'hfffffff0);
        assign stage_read_req='0;"""),
 edit('        br88_packet_ingress_sync_v91h #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) ingress (','        br88_packet_ingress_sync_v91h #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) ingress (\n            .meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),')])
 save('fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv',[
 edit('    logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch;','    logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch;\n    logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123;'),
 edit('        .meta_count3(meta_count3), .meta_epoch(meta_epoch), .meta_raw(meta_raw),','        .meta_count3(meta_count3), .meta_epoch(meta_epoch), .meta_raw(meta_raw),\n        .meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),'),
 edit('        .begin_count1(meta_count1), .begin_count2(meta_count2), .begin_count3(meta_count3),','        .begin_count1(meta_count1), .begin_count2(meta_count2), .begin_count3(meta_count3),\n        .begin_prefix1(meta_prefix1),.begin_prefix12(meta_prefix12),.begin_prefix123(meta_prefix123),')])
 save('fpga/experiments/cu66-v107-guard-dsp/packed_scratch_v91g2.sv',[
 edit('    input logic [31:0] begin_count1, begin_count2, begin_count3, begin_epoch,','    input logic [31:0] begin_count1, begin_count2, begin_count3, begin_epoch,\n    input logic [31:0] begin_prefix1, begin_prefix12, begin_prefix123,'),
 edit("plan_start2=sum3(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4));","plan_start2=plan_start1+begin_prefix1;"),
 edit("plan_start3=sum4(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4),aligned(begin_count2*4));","plan_start3=plan_start1+begin_prefix12;"),
 edit("sum5(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4),aligned(begin_count2*4),aligned(begin_count3*4));","plan_start1+begin_prefix123;"),
 edit('`ifndef SYNTHESIS\n',"""`ifndef SYNTHESIS
    always_ff @(posedge clk)if(begin_valid&&begin_ready)begin
        assert(begin_prefix1==aligned(begin_count1*4))else $fatal(1,"scratch prefix1 ownership mismatch");
        assert(begin_prefix12==aligned(begin_count1*4)+aligned(begin_count2*4))else $fatal(1,"scratch prefix12 ownership mismatch");
        assert(begin_prefix123==aligned(begin_count1*4)+aligned(begin_count2*4)+aligned(begin_count3*4))else $fatal(1,"scratch prefix123 ownership mismatch");
    end
""")])
 result=dict(schema='v107-plan-count-prefix-recipe-v1',status='PREPARED_NOT_QUALIFIED',files=entries,public_added_cycles=0,private_unreset_data_bits=160,metadata_prefix_ports=3,rtl_files_required=4,precondition='METADATA cache freshness invariant from actual full-header fetch; private outputs outside owned metadata unspecified; full32 count/epoch/blocks guards retained.')
 (OUT/'edit-recipe.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps([{k:e[k] for k in ('candidate','candidate_sha256')} for e in entries],indent=2))
if __name__=='__main__':main()
