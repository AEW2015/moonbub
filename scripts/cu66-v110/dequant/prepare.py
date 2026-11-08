#!/usr/bin/env python3
"""Prepare multiplier operands at existing dequant input/group edges."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'fpga/experiments/cu66-v107-payload-reset/cu66_dequant.sv'
SRC=ROOT/'fpga/experiments/cu66-v110-dequant';AREA=ROOT/'experiments/python-gamebub-v110/dequant'
HASH='579cb5d397e6638c0533fd54250e161612bdaed74117a29475afbab648aec7fb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def main():
 assert sha(OLD)==HASH;s=OLD.read_text();edits=[]
 def edit(before,after):
  nonlocal s
  assert s.count(before)==1,(before,s.count(before));s=s.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
 edit('    logic signed [24:0] products [0:7];','''    logic signed [24:0] products [0:7];
    // Prepare the next owned beat on an existing edge. The input acceptance
    // edge supplies group zero; each result edge supplies the following group.
    // These private payload registers need no reset or new public valid state.
    logic signed [15:0] operand_coefficients [0:7];
    logic [7:0] operand_quantizers [0:7];
    logic signed [24:0] operand_products [0:7];
    function automatic logic [7:0] prepared_quant(input logic chr,
        input logic [1:0] sc,input logic [5:0] position);
        logic [8:0] value;
        case(sc)
            0:value=({1'b0,base_quant(chr,position)}+9'd1)>>1;
            1:value={1'b0,base_quant(chr,position)};
            2:value={base_quant(chr,position),1'b0};
            default:value=0;
        endcase
        prepared_quant=(value>255)?8'hff:value[7:0];
    endfunction
    for(genvar lane=0;lane<8;lane=lane+1)begin: prepared_operands
        assign operand_products[lane]=$signed(operand_coefficients[lane]) *
                                      $signed({1'b0,operand_quantizers[lane]});
        always_ff @(posedge clk)begin
            if(state==IDLE)begin
                operand_coefficients[lane]<=in_coefficients[lane*16 +:16];
                operand_quantizers[lane]<=prepared_quant(in_chroma,in_scale_code,6'(lane));
            end else if(state==MULTIPLY && group_index!=7)begin
                operand_coefficients[lane]<=coefficients[((int'(group_index)+1)*8+lane)*16 +:16];
                operand_quantizers[lane]<=prepared_quant(chroma,scale_code,{(group_index+3'd1),3'(lane)});
            end
        end
    end''')
 edit("out_dequantized[(int'(group_index)*8+lane)*20 +:20]<=20'(products[lane]);","out_dequantized[(int'(group_index)*8+lane)*20 +:20]<=20'(operand_products[lane]);")
 assertion='''`ifndef SYNTHESIS
    // The original quantizer/selection/product expressions remain independent
    // reference expressions. Only owned MULTIPLY cycles consume operands.
    always_ff @(posedge clk)if(state==MULTIPLY && !rst && !abort_i)begin
        for(integer lane=0;lane<8;lane=lane+1)begin
            assert(operand_coefficients[lane]==coefficients[(int'(group_index)*8+lane)*16 +:16])
                else $fatal(1,"dequant prepared coefficient owner mismatch");
            assert(operand_quantizers[lane]==q[lane])
                else $fatal(1,"dequant prepared quantizer owner mismatch");
            assert(operand_products[lane]==products[lane])
                else $fatal(1,"dequant prepared signed product mismatch");
        end
    end
`endif
'''
 edit('endmodule',assertion+'endmodule')
 p=SRC/'cu66_dequant.sv';p.write_text(s);reverse=s
 for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
 assert reverse==OLD.read_text()
 entry=dict(original=str(OLD.relative_to(ROOT)),original_sha256=HASH,candidate=str(p.relative_to(ROOT)),candidate_sha256=sha(p),edits=edits)
 write(SRC/'edit-recipe.json',dict(schema='v110-dequant-existing-edge-operands-v1',status='PREPARED_NOT_RTL_QUALIFIED',production={p.name:entry},added_public_cycles=0,owned_operand_invariant='Every non-killed MULTIPLY cycle: coefficient, fully scaled/clamped quantizer and signed25 product match original current-group expressions.',first_group='Live in_* on original IDLE capture edge, matching original coefficient/chroma/scale RF captures including invalid/kill edges.',next_group='Saved owned payload at MULTIPLY group<7 edge while original current-group output writes on its unchanged edge.',original_private_payload_capture_unchanged=True,public_partial_invalid_output_schedule_unchanged=True))
 adapters=[]
 for variant,source in [('original',OLD),('candidate',p)]:
  body=source.read_text();before='module cu66_dequant (';after='module dequant_'+variant+' ('
  assert body.count(before)==1;dest=SRC/('dequant_'+variant+'.sv');dest.write_text(body.replace(before,after,1))
  adapters.append(dict(source=str(source.relative_to(ROOT)),path=str(dest.relative_to(ROOT)),source_sha256=sha(source),sha256=sha(dest),renames=[(before,after)]))
 fixtures={}
 for name in ('dequant_probe.sv','tb_dequant.cpp'):
  source=OLD.parent/name;(SRC/name).write_bytes(source.read_bytes());fixtures[str(source.relative_to(ROOT))]=sha(source)
 write(SRC/'adapters.json',dict(adapters=adapters,unchanged_fixtures=fixtures))
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL',candidate_sha256=sha(p),original_sha256=HASH,recipe_sha256=sha(SRC/'edit-recipe.json'),added_public_cycles=0))
 print('DEQUANT_PREPARED_NOT_RUN',sha(p))
if __name__=='__main__':main()
