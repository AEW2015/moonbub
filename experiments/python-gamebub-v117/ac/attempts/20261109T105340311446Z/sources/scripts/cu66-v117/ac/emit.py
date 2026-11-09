#!/usr/bin/env python3
"""Derive V117 AC payload capture and exact proof wrappers from immutable V116 C."""
import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v117-ac';V=S/'verification'
BASE=R/'fpga/experiments/cu66-v116c-record'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def derive(src,dst,edits):
 t=src.read_text()
 for e in edits:
  assert t.count(e['before'])==1,e['before'][:100]
  t=t.replace(e['before'],e['after'],1)
 dst.write_text(t)
 return dict(original=rel(src),original_sha256=sha(src),candidate=rel(dst),candidate_sha256=sha(dst),edits=edits)
new=r'''    // V117: one selected AC payload on existing acquisition edges. The
    // existing read_address/read_segment/read_band/active_epoch tuple is its
    // physical owner; no queue, public cycle or new cancellation boundary.
    logic [31:0] ac_fetch_address, ac_selected_word;
    logic [18:0] ac_selected_position;
    logic ac_selected_invalid;
    assign ac_fetch_address=starts[read_band]+cursors[read_band]*4;
    // Private payload may capture on a cancelled acquisition edge; state and
    // original read_tag_match prevent consumption, and the next owner replaces
    // it before use. Do not put the late validation/abort cone onto these CEs.
    always_ff @(posedge clk)begin
        if(state==AC_FETCH)begin
            if(prefetch_complete && prefetch_segment==read_band)begin
                // Original prefetch writes this bank on the SAME edge. Forward
                // the response instead of selecting the bank's old contents.
                ac_selected_word<=32'(mem_rsp_data>>(8*ac_fetch_address[3:0]));
                ac_selected_position<=sparse_position(19'(mem_rsp_data>>(8*ac_fetch_address[3:0]+13)));
            end else begin
                ac_selected_word<=32'(cache_data[read_band]>>(8*ac_fetch_address[3:0]));
                ac_selected_position<=cache_positions[read_band][ac_fetch_address[3:0]];
            end
        end else if(state==READ_WAIT && return_state==AC_EXTRACT && mem_rsp_valid)begin
            // A matching successful response is the only route to consumption.
            // Invalid/error responses may overwrite unowned private payload;
            // the original main priority still revokes/drains exactly as before.
            ac_selected_word<=32'(mem_rsp_data>>(8*read_address[3:0]));
            ac_selected_position<=sparse_position(19'(mem_rsp_data>>(8*read_address[3:0]+13)));
        end
    end
    assign ac_selected_invalid=17'(ac_selected_word[31:19])>=blocks ||
        !rank_matches(read_band,ac_selected_position[5:0]) ||
        $signed(ac_selected_word[12:0])==0 || $signed(ac_selected_word[12:0]) < -2048 ||
        $signed(ac_selected_word[12:0]) > 2048 ||
        (cursors[read_band]!=0 && {13'd0,ac_selected_position}<={13'd0,head_positions[read_band]});
`ifndef SYNTHESIS
    // Complete acquisition certificate. These duplicate owner fields are
    // verification-only: hardware already holds them in its existing read
    // transaction registers and advances only at the original consume edge.
    logic ac_cert_mature=0;
    logic [31:0] ac_cert_address,ac_cert_epoch,ac_cert_cursor;
    logic [1:0] ac_cert_segment,ac_cert_band;
    logic [18:0] ac_cert_head_position;
    logic [16:0] ac_cert_blocks;
    always_ff @(posedge clk)begin
        if(state==AC_FETCH || (state==READ_WAIT && return_state==AC_EXTRACT && mem_rsp_valid))begin
            ac_cert_mature<=1;
            ac_cert_address<=state==AC_FETCH ? ac_fetch_address : read_address;
            ac_cert_segment<=state==AC_FETCH ? read_band : read_segment;
            ac_cert_epoch<=active_epoch;ac_cert_band<=read_band;
            ac_cert_cursor<=cursors[read_band];
            ac_cert_head_position<=head_positions[read_band];ac_cert_blocks<=blocks;
        end
        // Mirror original main outer eligibility, including matching response
        // errors without prefetch/write ownership. No !response_failure shortcut.
        if(tile_case_eligible && state==AC_EXTRACT && read_tag_match)begin
            assert(ac_cert_mature && ac_cert_address==read_address &&
                ac_cert_segment==read_segment && ac_cert_epoch==active_epoch && ac_cert_band==read_band &&
                ac_cert_cursor==cursors[read_band] && ac_cert_head_position==head_positions[read_band] &&
                ac_cert_blocks==blocks)else $fatal(1,"V117 selected AC payload mixed acquisition owner");
            assert(ac_selected_word==read_word && ac_selected_position==read_position[18:0])
                else $fatal(1,"V117 selected AC payload differs from original cache selection");
            assert(ac_selected_invalid==ac_bank_invalid[read_segment])
                else $fatal(1,"V117 selected AC validation differs from original bank predicate");
        end
    end
`endif
'''
edits=[dict(before='    // Cursor payload is unowned in IDLE/DRAIN/FINISHED/FAILED.',after=new+'\n    // Cursor payload is unowned in IDLE/DRAIN/FINISHED/FAILED.'),
 dict(before='                    read_segment<=read_band; read_address<=starts[read_band]+cursors[read_band]*4; begin state<=AC_EXTRACT; busy_owned<=1\'b1; end',after='                    read_segment<=read_band; read_address<=ac_fetch_address; begin state<=AC_EXTRACT; busy_owned<=1\'b1; end'),
 dict(before='                        if(ac_bank_invalid[read_segment]) begin',after='                        if(ac_selected_invalid) begin'),
 dict(before='                            heads[read_band]<=read_word;\n                            head_positions[read_band]<=read_position[18:0];',after='                            heads[read_band]<=ac_selected_word;\n                            head_positions[read_band]<=ac_selected_position;')]
recipes=[derive(BASE/'packed_scratch_v91g2.sv',S/'packed_scratch_v91g2.sv',edits)]
for p in (BASE/'verification').iterdir():
 if p.is_file():shutil.copyfile(p,V/p.name)
old=json.loads((BASE/'edit-recipes.json').read_text());adapters=[]
for name,src in [('observed_original.sv',BASE/'packed_scratch_v91g2.sv'),('observed_candidate.sv',S/'packed_scratch_v91g2.sv'),('packed_scratch_reference.sv',BASE/'packed_scratch_v91g2.sv')]:
 olde=next(x for x in old['adapters']if Path(x['candidate']).name==name)
 adapters.append(derive(src,V/name,olde['edits']))
adapters.append(derive(BASE/'verification/tb_record.cpp',V/'record_base.cpp',[dict(before='int main(int argc,char**argv)',after='int inherited_record_main(int argc,char**argv)')]))
# Everything else in the inherited V116 C verification tree remains byte-exact.
# New independent directed cases are additive in tb_ac.cpp, without editing old tests.
manifest=dict(schema='v117-owned-selected-ac-record-capture-v1',recipes=recipes,adapters=adapters,
 unchanged_caller=old['unchanged_caller'],inherited_verification={rel(p):sha(p)for p in (BASE/'verification').iterdir()if p.is_file() and p.name not in ('observed_original.sv','observed_candidate.sv','packed_scratch_reference.sv')},declared_public_cycle_delta=0,scope='Existing AC_FETCH and matching READ_WAIT edges capture one private complete selected payload; original acquisition ownership/state and every old SVA preserved.')
(S/'edit-recipes.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('V117_AC_PREPARED',sha(S/'packed_scratch_v91g2.sv'))
if __name__=='__main__':pass
