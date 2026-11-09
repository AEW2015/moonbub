#!/usr/bin/env python3
"""Retain old three-edge pair and every original oracle, adding all-word views."""
import pathlib,json,hashlib,sys
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-refined-scratch';V=S/'verification';OLD=R/'fpga/experiments/cu66-v115-scratch/verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 V.mkdir(parents=True,exist_ok=True);recipes=[]
 def derive(old,name,edits):
  text=old.read_text()
  for before,after in edits:assert text.count(before)==1,(str(old),before[:80]);text=text.replace(before,after,1)
  p=V/name;p.write_text(text);reverse=text
  for before,after in reversed(edits):assert reverse.count(after)==1;reverse=reverse.replace(after,before,1)
  assert reverse==old.read_text();recipes.append(dict(source=str(old.relative_to(R)),source_sha256=sha(old),path=str(p.relative_to(R)),sha256=sha(p),edits=edits))
 for name in ['observed_original.sv','clock_adapter.hpp','tb_scratch.cpp','tb_bank.cpp','historical_hazards.cpp']:derive(OLD/name,name,[])
 adapters=json.loads((OLD/'adapters.json').read_text());view=next(x for x in adapters['adapters']if x['path'].endswith('observed_candidate.sv'))['edits'];derive(S/'packed_scratch_v91g2.sv','observed_candidate.sv',view)
 ports='''    output logic [2047:0] verify_tile_visible, verify_tile_private,
    output logic verify_tile_slot_valid, verify_tile_slot_bank,
    output logic [5:0] verify_tile_slot_index,
    output logic [15:0] verify_tile_slot_value,
    output logic verify_tile_event_valid,
    output logic [31:0] verify_tile_events, verify_tile_commits,
    output logic [31:0] verify_tile_back_to_back, verify_tile_zero_events, verify_tile_data_events,
'''
 additions='''    // Additive raw-array equivalence includes every inactive word, not only
    // selected dense data. No original public/owner/raw check is removed.
    logic all_tile_words_equal;
    always_comb begin
        all_tile_words_equal=1;
        for(integer b=0;b<2;b=b+1)for(integer w=0;w<64;w=w+1)
            all_tile_words_equal=all_tile_words_equal && original.tile[b][w]==candidate.tile[b][w];
    end
    for(genvar b=0;b<2;b=b+1)begin: additional_tile_views
        for(genvar w=0;w<64;w=w+1)begin: word_view
            assign verify_tile_visible[(b*64+w)*16+:16]=candidate.tile[b][w];
            assign verify_tile_private[(b*64+w)*16+:16]=candidate.tile_payload[b][w];
        end
    end
    assign verify_tile_slot_valid=candidate.tile_pending_valid;
    assign verify_tile_slot_bank=candidate.tile_pending_bank;
    assign verify_tile_slot_index=candidate.tile_pending_index;
    assign verify_tile_slot_value=candidate.tile_pending_value;
    assign verify_tile_event_valid=candidate.tile_event_valid;
    initial begin verify_tile_events=0;verify_tile_commits=0;verify_tile_back_to_back=0;
        verify_tile_zero_events=0;verify_tile_data_events=0;end
    always_ff @(posedge clk)begin
        if(candidate.tile_event_valid)begin
            verify_tile_events<=verify_tile_events+1;
            if(candidate.tile_event_value==0)verify_tile_zero_events<=verify_tile_zero_events+1;
            else verify_tile_data_events<=verify_tile_data_events+1;
        end
        if(candidate.tile_pending_valid)verify_tile_commits<=verify_tile_commits+1;
        if(candidate.tile_pending_valid && candidate.tile_event_valid)
            verify_tile_back_to_back<=verify_tile_back_to_back+1;
        assert(verify_tile_events==verify_tile_commits+32'(candidate.tile_pending_valid))
            else $fatal(1,"finite tile slot conservation differs");
        if(candidate.tile_pending_valid)
            assert(candidate.tile[candidate.tile_pending_bank][candidate.tile_pending_index]==candidate.tile_pending_value)
                else $fatal(1,"newest visible tile write not forwarded");
    end
'''
 derive(OLD/'scratch_probe.sv','scratch_probe.sv',[('    output logic mismatch,',ports+'    output logic mismatch,'),('    assign mismatch=pair_enable && !((old_begin_ready==begin_ready)',additions+'    assign mismatch=pair_enable && !(all_tile_words_equal && (old_begin_ready==begin_ready)')])
 derive(OLD/'tb_prepare.cpp','tb_prepare.cpp',[('int main(int argc,char**argv)','int inherited_prepare_main(int argc,char**argv)')])
 (V/'adapters.json').write_text(json.dumps(dict(schema='v115-refined-all128-raw-forward-pair-v1',adapters=recipes,old_assertions_removed=0,descriptor_extra_edges_unchanged=3),indent=2,sort_keys=True)+'\n');print('PREPARED',len(recipes),'reversible verification adapters')
if __name__=='__main__':main()
