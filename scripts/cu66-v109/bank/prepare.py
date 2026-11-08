#!/usr/bin/env python3
"""Redundant four-bank one-hot cache selection; source/adapter preparation only."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OLD=ROOT/'fpga/experiments/cu66-v109-prefetch/packed_scratch_v91g2.sv';SRC=ROOT/'fpga/experiments/cu66-v109-bank';AREA=ROOT/'experiments/python-gamebub-v109/bank'
HASH='742726be34e0560b72f3cd0026edcd9be44bffbede5200a179edd483c24fca34'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def main():
 assert sha(OLD)==HASH;s=OLD.read_text();edits=[]
 def edit(before,after):
  nonlocal s
  assert s.count(before)==1,(before,s.count(before));s=s.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
 edit('    logic [1:0] read_segment;','''    logic [1:0] read_segment;
    // Redundant decode follows the existing read owner at exactly its two
    // capture edges. Like read_segment, it holds through reset/cancellation.
    logic [3:0] read_segment_oh;
    logic [3:0] read_bank_hits, read_bank_prefetched_hits;
    logic read_cache_hit, read_prefetched_hit;''')
 edit('        read_word=32\'(cache_data[read_segment]>>(8*read_address[3:0]));', '''        // Offset shifts/position lookup are local to each physical bank.
        // The captured one-hot owner selects the current live data/tag/valid;
        // no cached hit/miss decision or extra-cycle forwarding is introduced.
        read_word=0; read_position=0;
        for(integer bank=0;bank<4;bank=bank+1)begin
            read_word=read_word | ({32{read_segment_oh[bank]}} &
                32'(cache_data[bank]>>(8*read_address[3:0])));
            read_position=read_position | ({32{read_segment_oh[bank]}} &
                {13'd0,cache_positions[bank][read_address[3:0]]});
            read_bank_hits[bank]=read_segment_oh[bank] && cache_valid[bank] &&
                cache_address[bank]==18'(read_address & 32'hfffffff0);
            read_bank_prefetched_hits[bank]=read_bank_hits[bank] && prefetched_valid[bank];
        end
        read_cache_hit=|read_bank_hits;
        read_prefetched_hit=|read_bank_prefetched_hits;''')
 edit("        read_position={13'd0,cache_positions[read_segment][read_address[3:0]]};",'        // read_position is selected with the one-hot word owner above.')
 edit("             (state==AC_EXTRACT && cache_valid[read_segment] && prefetched_valid[read_segment] &&\n              cache_address[read_segment]==18'(read_address & 32'hfffffff0)));",'             (state==AC_EXTRACT && read_prefetched_hit));')
 edit('                else prefetched_valid[read_segment]<=0;', '''                else begin
                    for(integer bank=0;bank<4;bank=bank+1)
                        if(read_segment_oh[bank])prefetched_valid[bank]<=0;
                end''')
 edit('                            cache_data[read_segment]<=mem_rsp_data;', '''                            for(integer bank=0;bank<4;bank=bank+1)
                                if(read_segment_oh[bank])cache_data[bank]<=mem_rsp_data;''')
 for bank in range(4):edit(f"                            if(read_segment==2'd{bank})begin",f'                            if(read_segment_oh[{bank}])begin')
 edit('                            cache_address[read_segment]<=transfer_address; cache_valid[read_segment]<=1; prefetched_valid[read_segment]<=0;', '''                            for(integer bank=0;bank<4;bank=bank+1)begin
                                if(read_segment_oh[bank])begin
                                    cache_address[bank]<=transfer_address;
                                    cache_valid[bank]<=1; prefetched_valid[bank]<=0;
                                end
                            end''')
 edit('                    read_segment<=0; state<=DC_EXTRACT;',"                    read_segment<=0; read_segment_oh<=4'b0001; state<=DC_EXTRACT;")
 edit('                    read_segment<=read_band; read_address<=starts[read_band]+cursors[read_band]*4; state<=AC_EXTRACT;',"                    read_segment<=read_band; read_segment_oh<=4'b0001<<read_band; read_address<=starts[read_band]+cursors[read_band]*4; state<=AC_EXTRACT;")
 edit("                    if(!cache_valid[read_segment] || cache_address[read_segment]!=18'(read_address & 32'hfffffff0)) begin",'                    if(!read_cache_hit) begin')
 # Retain all baseline assertions verbatim. Supplement them with the exact
 # redundant-state and live-selection invariants, including invalid cycles.
 assertion='''`ifndef SYNTHESIS
    // Neither read_segment nor its redundant decode has a reset. Before the
    // first original capture, both are unowned; the public FSM cannot consume
    // either. This verification-only flag persists across warm resets too.
    logic read_segment_observed=0;
    always_ff @(posedge clk)begin
        if(!cancel && !response_failure &&
            (state==DC_FETCH || state==RAW_FETCH || state==AC_FETCH))
            read_segment_observed<=1;
        if(read_segment_observed)begin
            assert($onehot(read_segment_oh) && read_segment_oh==(4'b0001<<read_segment))
                else $fatal(1,"scratch redundant bank owner mismatch");
            assert(read_word==32'(cache_data[read_segment]>>(8*read_address[3:0])))
                else $fatal(1,"scratch onehot live word mismatch");
            assert(read_position=={13'd0,cache_positions[read_segment][read_address[3:0]]})
                else $fatal(1,"scratch onehot live position mismatch");
            assert(read_cache_hit==(cache_valid[read_segment] &&
                cache_address[read_segment]==18'(read_address & 32'hfffffff0)))
                else $fatal(1,"scratch onehot live cache hit mismatch");
            assert(read_prefetched_hit==(cache_valid[read_segment] && prefetched_valid[read_segment] &&
                cache_address[read_segment]==18'(read_address & 32'hfffffff0)))
                else $fatal(1,"scratch onehot live prefetch hit mismatch");
        end
    end
`endif
'''
 edit('endmodule',assertion+'endmodule')
 path=SRC/'packed_scratch_v91g2.sv';path.write_text(s);reverse=s
 for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
 assert reverse==OLD.read_text()
 # Every original assignment has a sibling update in precisely the same branch.
 assert len(re.findall(r'read_segment\s*<=',OLD.read_text()))==2
 assert len(re.findall(r'read_segment_oh\s*<=',s))==2
 e=dict(original=str(OLD.relative_to(ROOT)),original_sha256=HASH,candidate=str(path.relative_to(ROOT)),candidate_sha256=sha(path),edits=edits)
 recipe=dict(schema='v109-redundant-cache-bank-onehot-v1',status='PREPARED_NOT_RTL_QUALIFIED',production={path.name:e},added_public_cycles=0,read_segment_original_capture_edges=2,bank_decode_reset='No reset added: redundant decode holds with original binary selector; baseline assertions unchanged, new invariants begin after first original capture.',background_prefetch_owner='Existing prefetch_segment and all background updates unchanged; foreground fixed-bank writes retain original procedural ordering and forwarding priority.')
 write(SRC/'edit-recipe.json',recipe)
 # Only complete direct scratch pair. Original full V106 bench and hazard
 # oracle are byte-identical to their qualified fixture versions.
 obs=json.loads((ROOT/'fpga/experiments/cu66-v106-scratch/adapter.json').read_text());adapters=[]
 for variant,source in [('original',OLD),('candidate',path)]:
  text=source.read_text();changes=[('module packed_scratch_v91g2 ','module observed_'+variant+' '),('\n);',obs['extra_ports']),('\nendmodule',obs['assignments']['candidate']+'\nendmodule')]
  for before,after in changes:assert text.count(before)==1;text=text.replace(before,after,1)
  dest=SRC/'verification'/('observed_'+variant+'.sv');dest.write_text(text);adapters.append(dict(source=str(source.relative_to(ROOT)),path=str(dest.relative_to(ROOT)),source_sha256=sha(source),sha256=sha(dest),renames=changes))
 previous=ROOT/'fpga/experiments/cu66-v109-prefetch/verification';fixtures={}
 for name in ('scratch_probe.sv','tb_scratch.cpp','historical_hazards.cpp'):
  p=previous/name;q=SRC/'verification'/name;q.write_bytes(p.read_bytes());fixtures[str(p.relative_to(ROOT))]=sha(p)
 write(SRC/'verification/adapters.json',dict(schema='v109-bank-lossless-complete-scratch-adapters-v1',adapters=adapters,unchanged_fixtures=fixtures,all_baseline_assertions_and_oracles_retained=True))
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL',production_sha256=sha(path),original_sha256=HASH,recipe_sha256=sha(SRC/'edit-recipe.json'),assignments_paired=2,banks=4,offsets=16,full_original_new_body=True,added_public_cycles=0))
 print('BANK_PREPARED_NOT_RUN',sha(path))
if __name__=='__main__':main()
