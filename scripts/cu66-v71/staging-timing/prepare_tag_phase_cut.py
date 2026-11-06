"""Narrow reachable-state qualifier; original fail decision/error priority untouched."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003';d=r/'fpga/experiments/cu66-v71/direct-system/tag-phase-cut-v003';assert not d.exists();d.mkdir();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();source=p/'cu71_base_pipeline_math.sv';old=source.read_text();new=old.replace('logic fail_now,kill,','logic fail_now,fail_for_tag_valid,kill,').replace('assign tag_valid=fs==RESULT_HOLD&&!kill&&!fail_now;','assign tag_valid=fs==RESULT_HOLD&&!kill&&!fail_for_tag_valid;')
qualifier='''    // Reachable RESULT_HOLD always has no accepted write outstanding.
    // Independently compute only errors that can qualify tag_valid there.
    // Keep the actual fail_now/fail_code priority chain below unchanged.
    always_comb begin
        fail_for_tag_valid=0;
        if(fs!=IDLE&&fs!=DRAIN)begin
            if(fs==RUN_PLANE&&e_error)fail_for_tag_valid=1;
            else if(s_error)fail_for_tag_valid=1;
            else if(dq_valid&&dq_error)fail_for_tag_valid=1;
            else if(idct_valid&&idct_error)fail_for_tag_valid=1;
            else if(recon_valid&&(recon_error||recon_id!=tid))fail_for_tag_valid=1;
            else if(rows_error)fail_for_tag_valid=1;
        end
    end
'''
needle='    always_comb begin\n        fail_now=0;fail_code=0;';assert new.count(needle)==1;new=new.replace(needle,qualifier+needle);assert new.replace(qualifier,'').replace('logic fail_now,fail_for_tag_valid,kill,','logic fail_now,kill,').replace('assign tag_valid=fs==RESULT_HOLD&&!kill&&!fail_for_tag_valid;','assign tag_valid=fs==RESULT_HOLD&&!kill&&!fail_now;')==old
f=d/'cu71_base_pipeline_math.sv';f.write_text(new,newline='\n');m=json.loads((p/'sources.json').read_text());m['sources']=[f.relative_to(r).as_posix()if n==source.relative_to(r).as_posix()else n for n in m['sources']];m['sources_sha256']={n:sha(r/n)for n in m['sources']};m['parent_manifest_sha256']=sha(p/'sources.json');m['derivation']='Only independent tag_valid phase qualifier omits write/hash conditions; original fail_now/code unchanged; relies on separately proved RESULT_HOLD=>!write_pending; no added states/registers/cycles';(d/'sources.json').write_text(json.dumps(m,indent=2)+'\n');(d/'qualifier-logic.txt').write_text(qualifier,newline='\n');wrapper=r/'fpga/experiments/cu66-v71/direct-system/tag-equality-v001/cu71_tag_feedback_ooc.sv';(d/wrapper.name).write_bytes(wrapper.read_bytes());(d/'derivation.json').write_text(json.dumps({'parent_source_sha256':sha(source),'source_sha256':sha(f),'main_fail_now_code_logic_verbatim':True,'qualifier':'All original nonwrite/nontag error conditions, procedural-if X behavior preserved','required_invariant':'RESULT_HOLD->!write_pending, proved on complete original RTL under unconstrained child outputs','unreachable_counterexample_expected':'Arbitrary forced RESULT_HOLD with write_pending1 and write_error1 can differ; not claimed full Cartesian equivalence','no_new_states_FFs_or_cycles':True,'balanced_limb_version_not_used':True,'hardware':False,'proofs':'PENDING'},indent=2)+'\n');print(sha(f))
