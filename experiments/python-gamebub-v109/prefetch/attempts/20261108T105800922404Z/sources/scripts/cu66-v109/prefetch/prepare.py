#!/usr/bin/env python3
"""Prepare exact existing-edge prefetch arithmetic; never invoke RTL tools."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'fpga/experiments/cu66-v108-capacity/packed_scratch_v91g2.sv'
OUT=ROOT/'fpga/experiments/cu66-v109-prefetch'
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 old=BASE.read_text();assert digest(old)=='5c4e6fc665c81920a2f907bb87d34e78f0eac22a114f75633a1f1dc2ddd33676',digest(old)
 text=old;edits=[]
 def edit(a,b):
  nonlocal text
  assert text.count(a)==1,a;text=text.replace(a,b,1);edits.append(dict(before=a,after=b,expected_occurrences=1))
 edit('    logic [31:0] candidate_word_address;', '''    // Owned arithmetic is prepared on existing fetch/check edges. Cache tags,
    // validity and response ownership remain live at the original launch edge.
    logic [17:0] prefetch_line0, prefetch_lines[1:3];
    logic prefetch_next_block, prefetch_next_raw;
    logic [3:1] prefetch_remaining;''')
 start=text.index('        candidate_word_address=0;')
 end=text.index('        debug_prefetch_use=',start)
 edit(text[start:end],'''        if(prefetch_mode && !tile_mode && sealed && !prefetch_offer && !outstanding && !cancel && error==0) begin
            if(state==EMIT && !raw_mode && prefetch_next_block) begin
                if(!cache_valid[0] || cache_address[0]!=prefetch_line0) begin
                    candidate_valid=1; candidate_segment=0;
                    candidate_address=prefetch_line0;
                end
                for(integer b=1;b<=3;b=b+1) begin
                    if(!candidate_valid && prefetch_remaining[b] &&
                       (!cache_valid[b] || cache_address[b]!=prefetch_lines[b])) begin
                        candidate_valid=1; candidate_segment=2'(b);
                        candidate_address=prefetch_lines[b];
                    end
                end
            end else if(state==RAW_EXTRACT && raw_mode && prefetch_next_raw) begin
                if(!cache_valid[0] || cache_address[0]!=prefetch_line0) begin
                    candidate_valid=1; candidate_segment=0;
                    candidate_address=prefetch_line0;
                end
            end
        end
''')
 edit('                DC_FETCH, RAW_FETCH: begin\n', '''                DC_FETCH, RAW_FETCH: begin
                    // Full-width original expressions, captured before extraction.
                    prefetch_line0<=18'((32+(raw_mode ?
                        (32'(output_block)*64+32'(output_index)+1)*2 :
                        (32'(output_block)+1)*2)) & 32'hfffffff0);
                    prefetch_next_block<=17'(output_block)+1<blocks;
                    prefetch_next_raw<=32'(output_block)*64+32'(output_index)+1<32'(blocks)*64;
''')
 edit('                AC_CHECK: begin\n', '''                AC_CHECK: begin
                    // Cursors are unchanged on this edge. Every cursor increment
                    // returns here before EMIT, including the last sparse band.
                    for(integer b=1;b<=3;b=b+1) begin
                        prefetch_lines[b]<=18'((starts[b]+cursors[b]*4) & 32'hfffffff0);
                        prefetch_remaining[b]<=cursors[b]<counts[b];
                    end
''')
 edit('`ifndef SYNTHESIS\n', '''`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!cancel && !response_failure && !tile_mode)begin
        if(state==EMIT && !raw_mode)begin
            assert(prefetch_next_block==(17'(output_block)+1<blocks));
            assert(prefetch_line0==18'((32+(32'(output_block)+1)*2)&32'hfffffff0));
            for(integer b=1;b<=3;b=b+1)begin
                assert(prefetch_lines[b]==18'((starts[b]+cursors[b]*4)&32'hfffffff0));
                assert(prefetch_remaining[b]==(cursors[b]<counts[b]));
            end
        end
        if(state==RAW_EXTRACT && raw_mode)begin
            assert(prefetch_next_raw==(32'(output_block)*64+32'(output_index)+1<32'(blocks)*64));
            assert(prefetch_line0==18'((32+(32'(output_block)*64+32'(output_index)+1)*2)&32'hfffffff0));
        end
    end
''')
 candidate=OUT/BASE.name;candidate.write_text(text)
 reconstructed=old
 for e in edits:reconstructed=reconstructed.replace(e['before'],e['after'],1)
 assert reconstructed==text
 for e in reversed(edits):assert reconstructed.count(e['after'])==1;reconstructed=reconstructed.replace(e['after'],e['before'],1)
 assert reconstructed==old
 recipe=dict(schema='v109-prefetch-existing-edge-v1',status='PREPARED_NOT_RTL_QUALIFIED',hypothesis='prefetch address/range arithmetic on existing DC_FETCH/RAW_FETCH/AC_CHECK edges',public_added_cycles=0,live_decisions=['cache_valid','cache_address','outstanding','prefetch_offer','cancel','error','response_failure','prefetch_complete'],production={BASE.name:dict(original=str(BASE.relative_to(ROOT)),original_sha256=digest(old),candidate_sha256=digest(text),edits=edits)})
 (OUT/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
 print(json.dumps(dict(status=recipe['status'],candidate_sha256=digest(text)),indent=2))
if __name__=='__main__':main()
