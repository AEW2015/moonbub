#!/usr/bin/env python3
"""Derive a three-edge private scratch descriptor preparation stage, IV115.S1."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'fpga/experiments/cu66-v114-prefetch/packed_scratch_v91g2.sv'
SRC=ROOT/'fpga/experiments/cu66-v115-scratch'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert sha(OLD)=='332da2058fd3e6413e8cc6336c1aab13eba7cddaaa76bb9d49c8426b1727854a'
 s=OLD.read_text();edits=[]
 def change(before,after):
  nonlocal s
  assert s.count(before)==1,before[:100]
  s=s.replace(before,after,1);edits.append(dict(before=before,after=after))
 change('FINISHED, FAILED, DRAIN, FLUSH_LINE, PREFETCH_DRAIN, BANK_WAIT, PREP_DONE} state_t;',
        'FINISHED, FAILED, DRAIN, FLUSH_LINE, PREFETCH_DRAIN, BANK_WAIT, PREP_DONE, BEGIN_PLAN, BEGIN_COMMIT} state_t;')
 # All accepted begin payload fields retain their original widths.
 fields=[('16:0','blocks'),('','raw'),('','serial_clear'),('','overlap'),('','prefetch'),('','tile_overlap'),('31:0','count1'),('31:0','count2'),('31:0','count3'),('31:0','epoch'),('31:0','prefix1'),('31:0','prefix12'),('31:0','prefix123'),('31:0','threshold1'),('31:0','threshold2'),('31:0','threshold3'),('31:0','capacity_upper'),('31:0','capacity_lower'),('','capacity_wrap')]
 decl='\n    // IV115.S1: one bounded accepted descriptor, no physical request before commit.\n'
 for width,name in fields:decl+='    logic '+('['+width+'] ' if width else '')+'queued_'+name+';\n'
 decl+='''    logic prepare_mature=0;
    logic prepared_bad_epoch, prepared_bad_geometry;
    logic [31:0] prepared_start1, prepared_start2, prepared_start3, prepared_used;
    logic preparing_begin;
    assign preparing_begin=state==BEGIN_PLAN || state==BEGIN_COMMIT;
    // Payload is private until BEGIN_COMMIT; do not reset wide payload registers.
    always_ff @(posedge clk)begin
        if(state==IDLE && begin_valid && !cancel && !response_failure)begin
'''
 for width,name in fields:decl+='            queued_'+name+'<=begin_'+name+';\n'
 decl+='''        end
        // First preparation edge computes the base and validation. Second edge
        // computes the dependent addresses; each wide sum has its own register.
        prepared_start1<=32+aligned(32'(queued_blocks)*2);
        prepared_start2<=prepared_start1+queued_prefix1;
        prepared_start3<=prepared_start1+queued_prefix12;
        prepared_used<=queued_raw ? 32+32'(queued_blocks)*128 : prepared_start1+queued_prefix123;
        prepared_bad_epoch<=epoch_seen && queued_epoch<=last_epoch;
        prepared_bad_geometry<=queued_blocks==0 || queued_blocks>8192 ||
            32'(queued_blocks)<queued_threshold1 || 32'(queued_blocks)<queued_threshold2 ||
            32'(queued_blocks)<queued_threshold3 ||
            (queued_raw && (queued_count1!=0 || queued_count2!=0 || queued_count3!=0)) ||
            (queued_raw ? queued_blocks>17'd2047 :
                (32'(queued_blocks)>queued_capacity_upper ||
                 (queued_capacity_wrap && 32'(queued_blocks)<=queued_capacity_lower)));
    end
'''
 # Place after all declarations/functions, before original controller logic.
 change('    always_ff @(posedge clk) begin\n        // A reset is cancellation,',decl+'\n    always_ff @(posedge clk) begin\n        // A reset is cancellation,')
 change('cancel=reset || (abort_valid && abort_epoch==active_epoch);',
        'cancel=reset || (abort_valid && abort_epoch==(preparing_begin ? queued_epoch : active_epoch));')
 change('if(reset || (abort_valid && abort_epoch==active_epoch)) begin\n            sealed<=0;',
        'if(cancel) begin\n            prepare_mature<=0;\n            sealed<=0;')
 before=s[s.index('                IDLE: if(begin_valid) begin'):s.index('                INGEST: begin')]
 after=before
 # The original acceptance behavior is moved intact to the commit edge, using
 # captured payload and registered plans/flags. Public error timing is explicit.
 after=after.replace('                IDLE: if(begin_valid) begin','                BEGIN_COMMIT: begin',1)
 after=after.replace('                    sealed<=0; done<=0; error<=0;\n','',1)
 after=after.replace('if(epoch_seen && begin_epoch<=last_epoch)','if(prepared_bad_epoch)',1)
 bad='''else if(begin_blocks==0 || begin_blocks>8192 ||
                        32'(begin_blocks)<begin_threshold1 || 32'(begin_blocks)<begin_threshold2 ||
                        32'(begin_blocks)<begin_threshold3 ||
                        (begin_raw && (begin_count1!=0 || begin_count2!=0 || begin_count3!=0)) ||
                        capacity_bad)'''
 assert bad in after;after=after.replace(bad,'else if(prepared_bad_geometry)',1)
 for width,name in sorted(fields,key=lambda x:len(x[1]),reverse=True):after=after.replace('begin_'+name,'queued_'+name)
 for a,b in [('plan_start1','prepared_start1'),('plan_start2','prepared_start2'),('plan_start3','prepared_start3'),('plan_used','prepared_used')]:after=after.replace(a,b)
 after='''                IDLE: if(begin_valid)begin
                    sealed<=0; done<=0; error<=0; prepare_mature<=0; active_epoch<=begin_epoch;
                    begin state<=BEGIN_PLAN; busy_owned<=1'b1; end
                end
                BEGIN_PLAN: begin
                    prepare_mature<=1;
                    if(prepare_mature)begin state<=BEGIN_COMMIT; busy_owned<=1'b1; end
                end
'''+after
 change(before,after)
 # Preserve all original input algebra assertions. The two now-private plan
 # values would otherwise be unused by the Verilator assertion build.
 point='''        assert(capacity_bad==(plan_used>32'd262144))else $fatal(1,"scratch capacity predicate mismatch");'''
 change(point,point+'''
        assert(plan_start2==plan_start1+begin_prefix1 && plan_start3==plan_start1+begin_prefix12)
            else $fatal(1,"original live plan equations changed");''')
 check='''    // IV115.S1: validate every consumed staged descriptor against full-width
    // original algebra. Prepare edges own no data or physical memory transfer.
    always_ff @(posedge clk)if(preparing_begin && !cancel && !response_failure)begin
        assert(active_epoch==queued_epoch && busy && !begin_ready && !coef_ready && !band_end_ready && !seal_ready &&
            !dense_valid && !mem_req_valid && !outstanding && !sealed && !done && error==0)
            else $fatal(1,"scratch preparation leaked eligibility/debt");
        if(state==BEGIN_COMMIT)begin
            assert(prepared_start1==32+aligned(32'(queued_blocks)*2));
            assert(prepared_start2==prepared_start1+queued_prefix1);
            assert(prepared_start3==prepared_start1+queued_prefix12);
            assert(prepared_used==(queued_raw ? 32+32'(queued_blocks)*128 : prepared_start1+queued_prefix123));
            assert(prepared_bad_epoch==(epoch_seen && queued_epoch<=last_epoch));
        end
    end
'''
 change('    // Compare prepared values with the old full-width algebra precisely where',check+'    // Compare prepared values with the old full-width algebra precisely where')
 tagprep='''
    // Read-address/tag comparison matures on the existing fetch edge. No new
    // read-service edge: matching READ_WAIT response forwards the hit result.
    logic read_tag_match;
    logic [17:0] current_dc_line, selected_raw_line;
    always_ff @(posedge clk)begin
        current_dc_line<=18'((32+(tile_mode ? 32'(prepare_block) : 32'(output_block))*2)&32'hfffffff0);
        if(state==DESC1)selected_raw_line<=18'd32;
        else if(state==RAW_EXTRACT && dense_ready && !cancel && !response_failure)
            selected_raw_line<=prepared_raw_line;
        if(!cancel && !response_failure)begin
            if(state==DC_FETCH)read_tag_match<=cache_valid[0] && cache_address[0]==current_dc_line;
            if(state==RAW_FETCH)read_tag_match<=cache_valid[0] && cache_address[0]==selected_raw_line;
            if(state==AC_FETCH)read_tag_match<=cache_valid[read_band] && cache_address[read_band]==prepared_ac_line[read_band];
            if(state==READ_WAIT && outstanding && mem_rsp_valid &&
                (return_state==DC_EXTRACT || return_state==AC_EXTRACT))read_tag_match<=1;
        end
    end
'''
 change('    always_ff @(posedge clk) begin\n        // A reset is cancellation,',tagprep+'\n    always_ff @(posedge clk) begin\n        // A reset is cancellation,')
 change("DC_EXTRACT: begin\n                    if(!cache_valid[0] || cache_address[0]!=18'(read_address & 32'hfffffff0)) begin",'DC_EXTRACT: begin\n                    if(!read_tag_match) begin')
 change("AC_EXTRACT: begin\n                    if(!cache_valid[read_segment] || cache_address[read_segment]!=18'(read_address & 32'hfffffff0)) begin",'AC_EXTRACT: begin\n                    if(!read_tag_match) begin')
 tagcheck='''    // Check every registered read decision at its exact consumption edge.
    always_ff @(posedge clk)if(!cancel && !response_failure)begin
        if(state==DC_FETCH)assert(current_dc_line==18'((32+(tile_mode ? 32'(prepare_block) : 32'(output_block))*2)&32'hfffffff0));
        if(state==RAW_FETCH)assert(selected_raw_line==18'((32+(32'(output_block)*64+32'(output_index))*2)&32'hfffffff0));
        if(state==AC_FETCH)assert(prepared_ac_line[read_band]==18'((starts[read_band]+cursors[read_band]*4)&32'hfffffff0));
        if(state==DC_EXTRACT)assert(read_tag_match==(cache_valid[0] && cache_address[0]==18'(read_address & 32'hfffffff0)))
            else $fatal(1,"registered DC cache tag decision differs");
        if(state==AC_EXTRACT)assert(read_tag_match==(cache_valid[read_segment] && cache_address[read_segment]==18'(read_address & 32'hfffffff0)))
            else $fatal(1,"registered AC cache tag decision differs");
    end
'''
 change('    // Compare prepared values with the old full-width algebra precisely where',tagcheck+'    // Compare prepared values with the old full-width algebra precisely where')
 target=SRC/'packed_scratch_v91g2.sv';target.write_text(s)
 reversed_source=s
 for e in reversed(edits):assert reversed_source.count(e['after'])==1;reversed_source=reversed_source.replace(e['after'],e['before'],1)
 assert reversed_source==OLD.read_text()
 recipe=dict(schema='v115-scratch-descriptor-preparation-v1',original=str(OLD.relative_to(ROOT)),original_sha256=sha(OLD),candidate=str(target.relative_to(ROOT)),candidate_sha256=sha(target),contract='IV115.S1: begin acceptance reserves one captured descriptor; three candidate clock edges prepare then commit. active_epoch exposes the reserved tag from acceptance for actual parent abort routing. Cancel before commit has no admitted anti-replay epoch or physical effects. Parent frame epoch remains monotonic.',added_begin_commit_edges=3,old_state_ids_preserved=True,edits=edits)
 (SRC/'edit-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');print('PREPARED_SCRATCH',recipe['candidate_sha256'])
if __name__=='__main__':main()
