#!/usr/bin/env python3
"""Compose only proven V105 mode-port extraction onto frozen SCALE1956."""
from pathlib import Path
import difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'fpga/experiments/cu66-v107-scale';DST=ROOT/'fpga/experiments/cu66-v107-tables'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 source=(BASE/'cs88_admission_v91i2a.sv').read_bytes();assert sha(source)=='1956b84f3253ae688674744cd68952e21d8404318b0f4f7b69cf13e1207abfb3'
 old=json.loads((ROOT/'fpga/experiments/cu66-v105-memory/edit-proof.json').read_text());canonical=old['edits'][0]['after'].split('    // FINISHED lookups',1)[0]
 # Preserve the V105 five-way write address/data/guard logic byte-for-byte.
 lookup='''    cu66_mode_store_v107 mode_store(.clk(clk),.write_enable(mode_write_enable),
        .write_address(mode_write_address),.write_data(mode_write_data),
        .read_enable(lookup_req&&state==FINISHED&&!reset&&!start&&!abort_packet),
        .read_address(lookup_tile),.q(lookup_mode));

'''
 helper='''module cu66_mode_store_v107 (
    input wire clk,write_enable,input wire [12:0] write_address,input wire [1:0] write_data,
    input wire read_enable,input wire [12:0] read_address,output reg [1:0] q
);
    (* ram_style="block" *) reg [1:0] words [0:8099];
    // Parser writes and FINISHED reads are mutually exclusive in the caller.
    // Preserve the last registered lookup value across every parser write.
    always @(posedge clk)begin
        if(write_enable)words[write_address]<=write_data;
        else if(read_enable)q<=words[read_address];
    end
endmodule
'''
 edits=[('    logic [1:0] modes [0:8099];\n',''),('    assign replay_ready=',canonical+lookup+'    assign replay_ready='),('        if(lookup_req&&state==FINISHED&&!reset&&!start&&!abort_packet)begin\n            lookup_mode<=modes[lookup_tile];\n        end\n','')]
 for e in old['edits'][2:]:edits.append((e['before'],e['after']))
 def apply(text):
  for before,after in edits:assert text.count(before)==1,before;text=text.replace(before,after,1)
  return text+helper
 candidate=apply(source.decode());(DST/'cs88_admission_v91i2a.sv').write_text(candidate)
 original=(BASE/'admission_candidate.sv').read_text();(DST/'admission_original.sv').write_text(original.replace('module admission_candidate (','module admission_original (',1))
 (DST/'admission_candidate.sv').write_text(apply(original))
 for name in ('admission_probe.sv','adapter.json','ports.json','tb_admission.cpp'):(DST/name).write_bytes((BASE/name).read_bytes())
 recipe=dict(schema='v107-tables-exact-mode-composition-v1',baseline=str((BASE/'cs88_admission_v91i2a.sv').relative_to(ROOT)),baseline_sha256=sha(source),candidate=str((DST/'cs88_admission_v91i2a.sv').relative_to(ROOT)),candidate_sha256=sha(candidate.encode()),V105_mode_recipe_sha256=sha((ROOT/'fpga/experiments/cu66-v105-memory/edit-proof.json').read_bytes()),canonical_mode_generator_sha256=sha(canonical.encode()),changes=[dict(start=i,end=j,old=source.decode()[i:j],new=candidate[k:l]) for tag,i,j,k,l in difflib.SequenceMatcher(None,source.decode(),candidate,autojunk=False).get_opcodes() if tag!='equal'])
 (DST/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
 # Every untouched SCALE helper byte remains identical, with a separate second helper.
 offset=source.index(b'module cu66_scale_tdp_v107 (');scale=source[offset:];raw=candidate.encode();a=raw.index(b'module cu66_scale_tdp_v107 (');b=raw.index(b'module cu66_mode_store_v107 (');assert raw[a:b]==scale
 chunks=[('cs88_admission_v91i2a.sv',raw[:a]),('cu66_scale_tdp_v107.sv',raw[a:b]),('cu66_mode_store_v107.sv',raw[b:])];assert b''.join(x[1] for x in chunks)==raw
 (DST/'packaging.json').write_text(json.dumps(dict(schema='v107-tables-lossless-packaging-v1',production_sha256=sha(raw),split_byte_offsets=[a,b],fragments=[dict(filename=n,sha256=sha(v),bytes=len(v)) for n,v in chunks],scale_helper_unchanged_sha256=sha(scale),parent_compiler_file_delta_from_SCALE=1,native_production_file_delta_from_SCALE=0),indent=2,sort_keys=True)+'\n')
 print('TABLES_PREPARED',recipe['candidate_sha256'])
if __name__=='__main__':main()
