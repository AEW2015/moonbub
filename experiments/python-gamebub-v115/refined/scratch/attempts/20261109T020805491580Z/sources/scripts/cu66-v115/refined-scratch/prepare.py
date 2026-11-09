#!/usr/bin/env python3
"""One local tile-write tuple with same-cycle visible forwarding; no controller edit."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-refined-scratch';A=R/'experiments/python-gamebub-v115/refined/scratch'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=R/'fpga/experiments/cu66-v115-scratch/packed_scratch_v91g2.sv';assert sha(old)=='559cb6d4aa7f97c1b0ee4b347d9f098b617123d855c19d2a6f76b945be11c6c3'
 text=old.read_text();edits=[]
 def edit(before,after):
  nonlocal text
  assert text.count(before)==1,before[:100];text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
 edit('    logic signed [15:0] tile[0:1][0:63];','''    // IV115.S2: tile is the original visible raw view, including the latest
    // accepted write. A single local tuple retires into private payload on the
    // next edge; forwarding preserves every original visible cycle/value.
    logic signed [15:0] tile[0:1][0:63];
    logic signed [15:0] tile_payload[0:1][0:63];
    logic tile_pending_valid=0, tile_pending_bank;
    logic [5:0] tile_pending_index;
    logic signed [15:0] tile_pending_value;
    logic tile_event_valid, tile_event_bank;
    logic [5:0] tile_event_index;
    logic signed [15:0] tile_event_value;
    logic tile_case_eligible;
'''.rstrip())
 edit('    always_ff @(posedge clk) begin\n        // A reset is cancellation, not permission to discard an accepted write.','''    // Mirror the ORIGINAL outer main-branch priority, not !response_failure.
    // A matching response error without a prefetch/write owner can still reach
    // these case writes in the frozen source; preserve its raw payload effects.
    always_comb begin
        tile_case_eligible=!cancel &&
            !(mem_rsp_valid && (!outstanding || mem_rsp_epoch!=request_epoch)) &&
            state!=DRAIN &&
            !(prefetch_offer && outstanding && mem_rsp_valid && mem_rsp_error) &&
            !(overlap_mode && write_slot_valid && outstanding && mem_rsp_valid && mem_rsp_error);
        tile_event_valid=0;tile_event_bank=prep_bank;
        tile_event_index=0;tile_event_value=0;
        if(tile_case_eligible)begin
            case(state)
                CLEAR_TILE:if(serial_clear)begin
                    tile_event_valid=1;tile_event_index=clear_index;
                end
                DC_EXTRACT:if(read_tag_match && !(read_half < -2048 || read_half > 2048) && !raw_mode)begin
                    tile_event_valid=1;
                    tile_event_value=16'(cache_data[0]>>(8*read_address[3:0]));
                end
                AC_CHECK:if(!(!head_valid[read_band] && cursors[read_band]<counts[read_band]) &&
                    head_valid[read_band] && heads[read_band][31:19]==
                        (tile_mode ? prepare_block[12:0] : output_block[12:0]))begin
                    tile_event_valid=1;tile_event_index=heads[read_band][18:13];
                    tile_event_value={{3{heads[read_band][12]}},heads[read_band][12:0]};
                end
                default:begin end
            endcase
        end
    end
    // Retire the old tuple even on reset/cancel: its value was already visible
    // before the edge, and the original raw tile did not erase it on a kill.
    always_ff @(posedge clk)begin
        tile_pending_valid<=tile_event_valid;
        if(tile_event_valid)begin
            tile_pending_bank<=tile_event_bank;
            tile_pending_index<=tile_event_index;
            tile_pending_value<=tile_event_value;
        end
    end
    for(genvar payload_bank=0;payload_bank<2;payload_bank=payload_bank+1)begin: local_tile_bank
        for(genvar payload_word=0;payload_word<64;payload_word=payload_word+1)begin: local_tile_word
            wire pending_match=tile_pending_valid && tile_pending_bank==1'(payload_bank) &&
                tile_pending_index==6'(payload_word);
            always_ff @(posedge clk)if(pending_match)
                tile_payload[payload_bank][payload_word]<=tile_pending_value;
            assign tile[payload_bank][payload_word]=pending_match ? tile_pending_value :
                tile_payload[payload_bank][payload_word];
        end
    end
`ifndef SYNTHESIS
    // No disable on reset/abort: retirement of an already-visible write is
    // required across those edges, including immediate replacement on retry.
    assert property(@(posedge clk) tile_pending_valid |=>
        tile_payload[$past(tile_pending_bank)][$past(tile_pending_index)]==$past(tile_pending_value))
        else $fatal(1,"visible tile write was not physically retired");
    assert property(@(posedge clk) tile_event_valid |=> tile_pending_valid &&
        tile_pending_bank==$past(tile_event_bank) && tile_pending_index==$past(tile_event_index) &&
        tile_pending_value==$past(tile_event_value))
        else $fatal(1,"tile write tuple lost or mixed owner/value");
    assert property(@(posedge clk) !tile_event_valid |=> !tile_pending_valid)
        else $fatal(1,"tile slot created a write without an event");
`endif

    always_ff @(posedge clk) begin
        // A reset is cancellation, not permission to discard an accepted write.''')
 edit('                    if(serial_clear) tile[prep_bank][clear_index]<=0;','                    // Payload write is captured by the local forwarded tuple.')
 edit("                        tile[prep_bank][0]<=16'(cache_data[0]>>(8*read_address[3:0])); tile_valid[prep_bank][0]<=1;",'                        tile_valid[prep_bank][0]<=1;')
 edit('                        tile[prep_bank][heads[read_band][18:13]]<={{3{heads[read_band][12]}},heads[read_band][12:0]};','                        // Payload write is captured by the local forwarded tuple.')
 candidate=S/'packed_scratch_v91g2.sv';candidate.write_text(text);reverse=text
 for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
 assert reverse==old.read_text()
 recipe=dict(schema='v115-refined-local-forwarded-tile-write-v1',original=str(old.relative_to(R)),original_sha256=sha(old),candidate=str(candidate.relative_to(R)),candidate_sha256=sha(candidate),edits=edits,contract='IV115.S2: one23-bit local tuple plus initialized valid, one event/edge, prior tuple always retires; tile name exposes forwarding. Public cycles/visible raw tile values match initialV115 exactly. Descriptor3-edge contract unchanged.',controller_or_valid_writes_changed=False,old_assertions_removed=0,status='PREPARED_FOR_ROOT_REVIEW_NOT_RUN')
 (S/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n');A.mkdir(parents=True,exist_ok=True);(A/'preparation.json').write_text(json.dumps(dict(status='PREPARED_FOR_ROOT_REVIEW_NOT_RUN',source_sha256=sha(candidate),recipe_sha256=sha(S/'edit-recipe.json')),indent=2)+'\n');print('PREPARED',recipe['candidate_sha256'])
if __name__=='__main__':main()
