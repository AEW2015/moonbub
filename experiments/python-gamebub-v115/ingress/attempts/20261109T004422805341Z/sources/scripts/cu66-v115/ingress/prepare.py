#!/usr/bin/env python3
"""Reversible private ingress descriptors and exact-cycle parser cache preparation."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v115-ingress'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 records=[]
 def make(name,original,changes):
  old=ROOT/original;text=old.read_text();edits=[]
  for before,after in changes:
   count=text.count(before);assert count==(2 if before=='            cached_replay_remaining<=0;\n            descriptor_ready<=0;' else 1),(name,before,count);text=text.replace(before,after);edits.append(dict(before=before,after=after,occurrences=count))
  new=SRC/name;new.write_text(text);records.append(dict(original=original,original_sha256=sha(old),candidate=str(new.relative_to(ROOT)),candidate_sha256=sha(new),edits=edits));return text
 make('br88_packet_ingress_sync_v91h.sv','fpga/experiments/cu66-v110-count-domain/br88_packet_ingress_sync_v91h.sv',[
 ('METADATA=9, CONTEXT_END=10, RAW_END=11, FETCH_REQ=12, FETCH_WAIT=13;', 'METADATA=9, CONTEXT_END=10, RAW_END=11, FETCH_REQ=12, FETCH_WAIT=13, SELECT_BAND=14;'),
 ('    logic prepared_request_in_bounds;','''    logic prepared_request_in_bounds;
    // IV115 ingress: a private owned descriptor is selected one edge before
    // either descriptor validation or context delivery. Payload is unreset;
    // SELECT_BAND + context start/packet cancellation qualify every use.
    logic selection_context;
    logic [1:0] active_band;
    logic [31:0] active_length, active_length_minus1, active_count;
    logic [31:0] active_size, active_offset, descriptor_last_addr;
    logic [7:0] active_k0, active_k1;
    logic active_descriptor_bad;
    logic replay_nonzero;
    logic [5:0] replay_fetch_bits, replay_word_bits;
    logic replay_word_last;'''),
 ('next_request_addr=fetch_base+lengths[band]-1;', 'next_request_addr=descriptor_last_addr;'),
 ('always_ff @(posedge clk)if(state==FETCH_REQ)expected_fetch_addr<=fetch_address;', 'always_ff @(posedge clk)if(state==FETCH_REQ)expected_fetch_addr<=prepared_request_addr;'),
 ('            prepared_request_addr<=base;','''            if(kind==F_DESCRIPTOR)descriptor_last_addr<=base+active_length_minus1;
            prepared_request_addr<=base;'''),
 ('        ctx_bits=6\'(cached_replay_remaining<(mode16 ? 16 : 32) ? cached_replay_remaining : (mode16 ? 16 : 32));\n        ctx_last=cached_replay_remaining==32\'(ctx_bits);\n        ctx_valid=state==CONTEXT_RUN && word_valid && replay_bits<sizes[band] && !cancelled && !context_failure;', '''        replay_fetch_bits=6'(cached_replay_remaining<(mode16 ? 16 : 32) ? cached_replay_remaining : (mode16 ? 16 : 32));
        ctx_bits=replay_word_bits;
        ctx_last=replay_word_last;
        ctx_valid=state==CONTEXT_RUN && word_valid && replay_nonzero && !cancelled && !context_failure;'''),
 ('.band({6\'d0,band}), .k0(k0s[band]), .k1(k1s[band]),\n        .event_count(counts[band]), .stream_bits(sizes[band]), .epoch(context_epoch),', ".band({6'd0,active_band}), .k0(active_k0), .k1(active_k1),\n        .event_count(active_count), .stream_bits(active_size), .epoch(context_epoch),"),
 ('        if(state==FETCH_WAIT) begin\n            prepared_request_addr<=next_request_addr;', '''        if(state==FETCH_WAIT) begin
            if(fetch_kind==F_REPLAY)begin
                replay_word_bits<=replay_fetch_bits;
                replay_word_last<=cached_replay_remaining==32'(replay_fetch_bits);
            end
            prepared_request_addr<=next_request_addr;'''),
 ('            cached_replay_remaining<=0;\n            descriptor_ready<=0;', '            cached_replay_remaining<=0; replay_nonzero<=0; selection_context<=0;\n            descriptor_ready<=0;'),
 ('                        end else state<=DESCRIPTOR;', '                        end else begin selection_context<=0;state<=SELECT_BAND;end'),
 ('                DESCRIPTOR: begin\n                    if(!descriptor_ready) begin\n                        if(lengths[band]<6 || cursor>size_bytes-4 || lengths[band]>size_bytes-4-cursor) fail_packet(4);', '''                SELECT_BAND:begin
                    active_band<=band;active_length<=lengths[band];
                    active_length_minus1<=lengths[band]-1;
                    active_count<=counts[band];active_size<=sizes[band];active_offset<=offsets[band];
                    active_k0<=k0s[band];active_k1<=k1s[band];active_descriptor_bad<=descriptor_count_bad;
                    state<=selection_context?CONTEXT_START:DESCRIPTOR;
                end
                DESCRIPTOR: begin
                    if(!descriptor_ready) begin
                        if(active_length<6 || cursor>size_bytes-4 || active_length>size_bytes-4-cursor) fail_packet(4);'''),
 ('descriptor_bytes!=lengths[band]-6', 'descriptor_bytes!=active_length-6'),
 ('fetch_bytes[1]>11 || descriptor_count_bad', 'fetch_bytes[1]>11 || active_descriptor_bad'),
 ('else if(band!=0 && counts[band]==0 && descriptor_bits!=0)', 'else if(band!=0 && active_count==0 && descriptor_bits!=0)'),
 ('cursor<=cursor+lengths[band];', 'cursor<=cursor+active_length;'),
 ('                            else band<=band+1\'b1;', "                            else begin band<=band+1'b1;selection_context<=0;state<=SELECT_BAND;end"),
 ('                METADATA: if(meta_valid && meta_ready) state<=raw_mode ? RAW : CONTEXT_START;\n                CONTEXT_START: begin replay_bits<=0; cached_replay_remaining<=sizes[band]; word_valid<=0; context_active<=1; state<=CONTEXT_RUN; end', '''                METADATA: if(meta_valid && meta_ready)begin
                    if(raw_mode)state<=RAW;
                    else begin selection_context<=1;state<=SELECT_BAND;end
                end
                CONTEXT_START: begin replay_bits<=0; cached_replay_remaining<=active_size;
                    replay_nonzero<=active_size!=0;word_valid<=0; context_active<=1; state<=CONTEXT_RUN; end'''),
 ('cached_replay_remaining<=cached_replay_remaining-32\'(ctx_bits); word_valid<=0;', "cached_replay_remaining<=cached_replay_remaining-32'(ctx_bits); replay_nonzero<=cached_replay_remaining!=32'(ctx_bits);word_valid<=0;"),
 ('else if(!word_valid && replay_bits<sizes[band])\n                        begin_fetch(F_REPLAY,6\'((32\'(ctx_bits)+7)>>3),offsets[band]+(replay_bits>>3),CONTEXT_RUN);', "else if(!word_valid && replay_nonzero)\n                        begin_fetch(F_REPLAY,6'((32'(replay_fetch_bits)+7)>>3),active_offset+(replay_bits>>3),CONTEXT_RUN);"),
 ("else begin band<=band+1'b1; state<=CONTEXT_START; end", "else begin band<=band+1'b1;selection_context<=1;state<=SELECT_BAND;end"),
 ('    // Independent mathematical caller contract, evaluated only on actual start.', '''    always_ff @(posedge clk)if(!cancelled)begin
        if(state==CONTEXT_START)begin
            assert(active_band==band && active_count==counts[band] && active_size==sizes[band] &&
                active_offset==offsets[band] && active_k0==k0s[band] && active_k1==k1s[band])
                else $fatal(1,"V115 context descriptor ownership mismatch");
        end
        if(state==DESCRIPTOR)begin
            assert(active_length==lengths[band] && active_length_minus1==lengths[band]-1 &&
                active_descriptor_bad==descriptor_count_bad)
                else $fatal(1,"V115 descriptor validation ownership mismatch");
        end
        if(context_active && !context_failure && !ctx_done)begin
            assert(replay_nonzero==(cached_replay_remaining!=0))else $fatal(1,"V115 replay nonzero mismatch");
            if(word_valid)begin
                assert(ctx_bits==replay_fetch_bits && ctx_last==(cached_replay_remaining==32'(replay_fetch_bits)))
                    else $fatal(1,"V115 replay word tuple mismatch");
            end
        end
    end
    // Independent mathematical caller contract, evaluated only on actual start.''')
 ])
 make('br88_rice_elastic.sv','fpga/experiments/cu66-v110-prefix/br88_rice_elastic.sv',[
 ('    logic [31:0] cached_remaining, cached_load_remaining;', '''    logic [31:0] cached_remaining, cached_load_remaining;
    // Exact bounded predicates avoid a live32-bit remaining path through the
    // PREFIX priority/consume controller. IDLE/request supplies the warm-up.
    logic [5:0] prefix_window;
    logic remaining_nonzero, load_nonzero;
    always_ff @(posedge clk)prefix_window<=cached_remaining<15?6'(cached_remaining):6'd15;'''),
 ("        window = remaining < 15 ? 6'(remaining) : 6'd15;", "        window = state==PREFIX&&!serial ? prefix_window : (remaining<15?6'(remaining):6'd15);"),
 ('        prefix_empty = window==0;', '        prefix_empty = !remaining_nonzero;'),
 ('                 loaded<size_bits && !(state==IDLE && req_valid) &&', '                 load_nonzero && !(state==IDLE && req_valid) &&'),
 ('            cached_remaining<=stream_bits; cached_load_remaining<=stream_bits;', '            cached_remaining<=stream_bits; cached_load_remaining<=stream_bits;\n            remaining_nonzero<=stream_bits!=0;load_nonzero<=stream_bits!=0;'),
 ('                    cached_load_remaining<=cached_load_remaining-32\'(in_bits);', "                    cached_load_remaining<=cached_load_remaining-32'(in_bits);\n                    load_nonzero<=cached_load_remaining!=32'(in_bits);"),
 ('                    cached_remaining<=cached_remaining-32\'(take_bits);\n                    count_bits<=count_bits+64\'(take_bits);\n                    if (!serial && !found_one', "                    cached_remaining<=cached_remaining-32'(take_bits);\n                    remaining_nonzero<=cached_remaining!=32'(take_bits);\n                    count_bits<=count_bits+64'(take_bits);\n                    if (!serial && !found_one"),
 ('                    cached_remaining<=cached_remaining-32\'(take_bits);\n                    count_bits<=count_bits+64\'(take_bits);\n                    if (!serial || suffix_left', "                    cached_remaining<=cached_remaining-32'(take_bits);\n                    remaining_nonzero<=cached_remaining!=32'(take_bits);\n                    count_bits<=count_bits+64'(take_bits);\n                    if (!serial || suffix_left"),
 ('    // Only SUFFIX selects this combinational result;', '''    always_ff @(posedge clk)if(!reset&&!stream_start&&active)begin
        assert(remaining_nonzero==(cached_remaining!=0))else $fatal(1,"V115 remaining eligibility mismatch");
        assert(load_nonzero==(loaded<size_bits))else $fatal(1,"V115 load eligibility mismatch");
        if(state==PREFIX&&!serial)
            assert(prefix_window==(cached_remaining<15?6'(cached_remaining):6'd15))
                else $fatal(1,"V115 prefix request warmup mismatch");
    end
    // Only SUFFIX selects this combinational result;''')
 ])
 (SRC/'edit-recipe.json').write_text(json.dumps(dict(schema='v115-ingress-descriptor-parser-caches-v1',production=records,contract='IV115.ingress: +one private SELECT_BAND edge per selected descriptor/context; parser same public cycles; all original assertions retained, original source/checkers untouched.'),indent=2)+'\n')
 return records
if __name__=='__main__':
 for r in prepare():print(r['candidate'],r['candidate_sha256'])
