from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/tag-equality-v001';assert not d.exists();d.mkdir();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();parent=r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/cu71_base_pipeline_math.sv';old=parent.read_text()
logic='''
    // Exact same128-bit logical equality, kept limb boundaries and balanced tree.
    (* KEEP="TRUE" *) wire [7:0] tag_limb_equal;
    (* KEEP="TRUE" *) wire [3:0] tag_pair_equal;
    (* KEEP="TRUE" *) wire [1:0] tag_quad_equal;
    wire tag_equal_balanced;
    for(genvar tag_limb=0;tag_limb<8;tag_limb=tag_limb+1)begin:g_tag_equal
        assign tag_limb_equal[tag_limb]=hash_value[128+tag_limb*16+:16]==wanted_tag[tag_limb*16+:16];
    end
    assign tag_pair_equal={tag_limb_equal[7]&tag_limb_equal[6],tag_limb_equal[5]&tag_limb_equal[4],tag_limb_equal[3]&tag_limb_equal[2],tag_limb_equal[1]&tag_limb_equal[0]};
    assign tag_quad_equal={tag_pair_equal[3]&tag_pair_equal[2],tag_pair_equal[1]&tag_pair_equal[0]};
    assign tag_equal_balanced=tag_quad_equal[1]&tag_quad_equal[0];
'''
assert old.count('    logic [255:0] hash_value;')==1;assert old.count('hash_value[255:128]!=wanted_tag')==1
new=old.replace('    logic [255:0] hash_value;','    logic [255:0] hash_value;'+logic).replace('hash_value[255:128]!=wanted_tag','!tag_equal_balanced');assert new.replace('    logic [255:0] hash_value;'+logic,'    logic [255:0] hash_value;').replace('!tag_equal_balanced','hash_value[255:128]!=wanted_tag')==old
candidate=d/'cu71_base_pipeline_math.sv';candidate.write_text(new,newline='\n');manifest=r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/sources.json';m=json.loads(manifest.read_text());assert m['sources_sha256'][parent.relative_to(r).as_posix()]==sha(parent);m['sources']=[candidate.relative_to(r).as_posix()if n==parent.relative_to(r).as_posix()else n for n in m['sources']];m['sources_sha256']={n:sha(r/n)for n in m['sources']};m['derivation']='Only kept balanced8x16 tag equality; no new state/cycle/latency; same operands, comparison/error priority; not hardware-selected';m['parent_manifest_sha256']=sha(manifest);(d/'sources.json').write_text(json.dumps(m,indent=2)+'\n');(d/'derivation.json').write_text(json.dumps({'parent_source':parent.relative_to(r).as_posix(),'parent_sha256':sha(parent),'candidate_sha256':sha(candidate),'only_change':'128-bit != comparison replaced by inverted balanced AND of8kept16-bit == limbs','sequential_state_changes':False,'error_priority_changes':False,'hardware':False,'proofs':'PENDING'},indent=2)+'\n');(d/'comparator-logic.txt').write_text(logic,newline='\n');print(sha(candidate))
