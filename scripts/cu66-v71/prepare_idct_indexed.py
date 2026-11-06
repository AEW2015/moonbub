"""Use bounded word indices instead of wide bit-offset arithmetic; same schedule."""
from pathlib import Path
import hashlib,json

root=Path(__file__).resolve().parents[2]
parent=root/'fpga/experiments/cu66-v71/inverse-reset/cu71_idct_resetlight.sv'
out=root/'fpga/experiments/cu66-v71/inverse-index'
out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(parent)=='eb17556b9e49c625c12da463a7ba717020e7e65c9da85ddd1ac45d254be2ed98'
text=parent.read_text()
changes=[
 ('module cu71_idct_resetlight (','module cu71_idct_indexed ('),
 ('    logic [1279:0] source_tile;', '''    // Every source/output word is written before its valid use; no bulk reset.
    logic signed [19:0] source_coeff [0:63];
    logic signed [23:0] result_word [0:63];
    for(genvar output_word=0;output_word<64;output_word=output_word+1)begin:g_output
        assign out_tile[output_word*24 +:24]=result_word[output_word];
    end'''),
 ('''                samples[l]={{4{source_tile[((int'(group_index)*2+l/4)*8+int'(k))*20+19]}},
                    source_tile[((int'(group_index)*2+l/4)*8+int'(k))*20 +:20]};''',
  "                samples[l]=$signed(source_coeff[{group_index,1'(l/4),k}]);"),
 ("samples[l]=intermediate[int'(k)*8+int'(group_index)*2+l/4];",
  "samples[l]=intermediate[{k,group_index,1'(l/4)}];"),
 ("samples[l]={{4{source_tile[19]}}, source_tile[19:0]};", "samples[l]=$signed(source_coeff[0]);"),
 ('                    source_tile<=in_tile;',
  '                    for(index=0;index<64;index=index+1)source_coeff[index]<=in_tile[index*20 +:20];'),
 ('                        out_tile<=0;',
  '                        for(index=0;index<64;index=index+1)result_word[index]<=0;'),
 ('out_tile[index*24 +:24]<=rounded', 'result_word[index]<=rounded'),
 ("intermediate[(int'(group_index)*2+lane/4)*8+lane%4]",
  "intermediate[{group_index,1'(lane/4),3'(lane%4)}]"),
 ("intermediate[(int'(group_index)*2+lane/4)*8+7-lane%4]",
  "intermediate[{group_index,1'(lane/4),3'(7-lane%4)}]"),
 ("out_tile[((lane%4)*8+int'(group_index)*2+lane/4)*24 +:24]",
  "result_word[{3'(lane%4),group_index,1'(lane/4)}]"),
 ("out_tile[((7-lane%4)*8+int'(group_index)*2+lane/4)*24 +:24]",
  "result_word[{3'(7-lane%4),group_index,1'(lane/4)}]"),
]
for old,new in changes:
 assert text.count(old)==1,old
 text=text.replace(old,new)
assert 'source_tile'not in text and 'int\'(group_index)'not in text
target=out/'cu71_idct_indexed.sv';target.write_text(text,newline='\n')
(out/'derivation.json').write_text(json.dumps(dict(status='DERIVED_BOUNDED_INDEX_REGRESSION_PENDING',
 parent=parent.relative_to(root).as_posix(),parent_sha256=sha(parent),candidate_sha256=sha(target),
 schedule='Same MUL/ACC/DC/OUTPUT states; no added clocks or stalls',
 indexing='Six-bit concatenations address64words; original signed20 coefficient/sample24/rounding unchanged',
 reset='Valid-fenced payload remains unreset, control/id/error reset unchanged',hardware=False),indent=2)+'\n')
print(out)
