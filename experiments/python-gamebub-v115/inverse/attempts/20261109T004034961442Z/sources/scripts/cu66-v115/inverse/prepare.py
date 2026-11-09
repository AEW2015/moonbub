#!/usr/bin/env python3
"""Derive IV115.1 helper preparation/visibility cuts from immutable V114 origins."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'fpga/experiments/cu66-v115-inverse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive(old_name,new_name,edits):
 old=ROOT/old_name;new=OUT/new_name;s=old.read_text();original=s
 for before,after in edits:
  assert s.count(before)==1,(old_name,before[:100],s.count(before));s=s.replace(before,after,1)
 if new.exists():assert new.read_text()==s,'Refuse silent overwrite of candidate'
 else:new.write_text(s)
 back=s
 for before,after in reversed(edits):assert back.count(after)==1;back=back.replace(after,before,1)
 assert back==original
 return dict(original=old_name,original_sha256=sha(old),derived=str(new.relative_to(ROOT)),derived_sha256=sha(new),edits=[dict(before=a,after=b)for a,b in edits])
OUT.mkdir(parents=True,exist_ok=True)
idct=[]
idct.append(('DC_SECOND_ACC, OUTPUT_TILE} state_t;','DC_SECOND_ACC, OUTPUT_TILE, PREPARE} state_t;'))
idct.append(('    logic input_bad;','''    logic input_bad;
    // IV115.1: eight local groups are captured with the retained source tile.
    // Only PREPARE consumes them, after an actual accepted IDLE edge. Payload
    // and flags are unowned in IDLE and need no reset/cancel fanout.
    logic [7:0] prepared_bad, prepared_nonzero, prepared_ac_nonzero;
    logic tile_zero, tile_dc;
    function automatic logic outside_domain(input logic [19:0] value);
        // Exact [-522240,+522240] over signed20, no wide subtract/comparison.
        outside_domain=(value[19:11]==9'b100000000)||
            (value[19:11]==9'b011111111&&(|value[10:0]));
    endfunction
    for(genvar g=0;g<8;g=g+1)begin: input_preparation
        logic bad, nonzero, ac_nonzero;
        always_comb begin
            bad=0;nonzero=0;ac_nonzero=0;
            for(integer j=0;j<8;j=j+1)begin
                bad=bad|outside_domain(in_tile[(g*8+j)*20+:20]);
                nonzero=nonzero|(|in_tile[(g*8+j)*20+:20]);
                if(g!=0||j!=0)ac_nonzero=ac_nonzero|(|in_tile[(g*8+j)*20+:20]);
            end
        end
        always_ff @(posedge clk)if(state==IDLE)begin
            prepared_bad[g]<=bad;prepared_nonzero[g]<=nonzero;
            prepared_ac_nonzero[g]<=ac_nonzero;
        end
    end
    assign tile_zero=!(|prepared_nonzero);
    assign tile_dc=!(|prepared_ac_nonzero);'''))
idct.append(('''        if(state==IDLE)begin
            prefetch_enable=in_valid && in_ready && !input_bad && in_tile!=0;
            prefetch_group=0;prefetch_k=0;prefetch_dc=in_tile[1279:20]==0;''','''        if(state==PREPARE)begin
            prefetch_enable=!input_bad&&!tile_zero;
            prefetch_group=0;prefetch_k=0;prefetch_dc=tile_dc;'''))
idct.append(('''            if(state==IDLE)
                next_samples[row]={{4{in_tile[(row*8)*20+19]}},in_tile[(row*8)*20+:20]};''','''            if(state==PREPARE)
                next_samples[row]={{4{source_tile[(row*8)*20+19]}},source_tile[(row*8)*20+:20]};'''))
idct.append(('''        input_bad=1'b0;
        for (integer n=0; n<64; n=n+1)
            if ($signed(in_tile[n*20 +:20]) > 20'sd522240 ||
                $signed(in_tile[n*20 +:20]) < -20'sd522240)
                input_bad=1'b1;''','''        input_bad=|prepared_bad;'''))
idct.append(('''                    out_error<=input_bad;
                    active_cycles<=0;''','''                    out_error<=0;
                    active_cycles<=0;'''))
idct.append(('''                    if (input_bad || in_tile==0) begin
                        out_written<=0;
                        state<=OUTPUT_TILE;
                    end else if (in_tile[1279:20]==0) state<=DC_FIRST_MUL;
                    else state<=FIRST_MUL;
                end
                FIRST_MUL''','''                    state<=PREPARE;
                end
                PREPARE:begin
                    out_error<=input_bad;
                    if(input_bad||tile_zero)begin out_written<=0;state<=OUTPUT_TILE;end
                    else if(tile_dc)state<=DC_FIRST_MUL;
                    else state<=FIRST_MUL;
                end
                FIRST_MUL'''))
idct.append(('''    always_ff @(posedge clk)if(state==IDLE)source_tile<=in_tile;''','''    always_ff @(posedge clk)if(state==IDLE)source_tile<=in_tile;
`ifndef SYNTHESIS
    logic reference_bad;
    always_comb begin
        reference_bad=0;
        for(integer n=0;n<64;n=n+1)
            if($signed(source_tile[n*20+:20])>20'sd522240 ||
               $signed(source_tile[n*20+:20])< -20'sd522240)reference_bad=1;
    end
    always_ff @(posedge clk)if(!rst&&!abort_frame&&state==PREPARE)begin
        assert(input_bad==reference_bad)else $fatal(1,"IDCT prepared range differs");
        assert(tile_zero==(source_tile==0))else $fatal(1,"IDCT prepared zero differs");
        assert(tile_dc==(source_tile[1279:20]==0))else $fatal(1,"IDCT prepared DC differs");
    end
`endif'''))
dq=[]
dq.append(('typedef enum logic [1:0] {IDLE, MULTIPLY, HOLD_TILE} state_t;','typedef enum logic [1:0] {IDLE, MULTIPLY, HOLD_TILE, PREPARE} state_t;'))
dq.append(('    logic input_bad;','''    logic input_bad;
    logic [7:0] prepared_bad, prepared_nonzero, output_written;
    logic prepared_scale_bad, tile_zero;
    for(genvar g=0;g<8;g=g+1)begin: input_preparation
        logic bad,nonzero;
        always_comb begin
            bad=0;nonzero=0;
            for(integer j=0;j<8;j=j+1)begin
                bad=bad|!((in_coefficients[(g*8+j)*16+11+:5]==5'd0)||
                    (in_coefficients[(g*8+j)*16+11+:5]==5'd31)||
                    (in_coefficients[(g*8+j)*16+:16]==16'h0800));
                nonzero=nonzero|(|in_coefficients[(g*8+j)*16+:16]);
            end
        end
        always_ff @(posedge clk)if(state==IDLE)begin
            prepared_bad[g]<=bad;prepared_nonzero[g]<=nonzero;
        end
    end
    always_ff @(posedge clk)if(state==IDLE)prepared_scale_bad<=in_scale_code==3;
    assign tile_zero=!(|prepared_nonzero);
    // The payload words use only registered local group ownership as CE.
    // Eight visibility bits provide the existing reset/invalid/zero contents;
    // a canceled speculative write cannot expose old or partial output.
    for(genvar w=0;w<64;w=w+1)begin: output_words
        logic [19:0] payload;
        always_ff @(posedge clk)if(state==MULTIPLY&&group_index==3'(w/8))
            payload<=20'(operand_products[w%8]);
        assign out_dequantized[w*20+:20]=output_written[w/8]?payload:20'd0;
    end'''))
dq.append(('''        input_bad=(in_scale_code==3);
        for(integer i=0;i<64;i=i+1)
            if($signed(in_coefficients[i*16 +:16]) < -16'sd2048 ||
               $signed(in_coefficients[i*16 +:16]) > 16'sd2048)input_bad=1;''','''        input_bad=prepared_scale_bad||(|prepared_bad);'''))
dq.append(('''            group_index<=0;out_id<=0;out_error<=0;out_dequantized<=0;''','''            group_index<=0;out_id<=0;out_error<=0;output_written<=0;'''))
dq.append(('''                out_id<=in_id;out_error<=input_bad;group_index<=0;
                if(input_bad||in_coefficients==0)begin out_dequantized<=0;state<=HOLD_TILE;end
                else state<=MULTIPLY;
            end
            MULTIPLY:begin
                for(integer lane=0;lane<8;lane=lane+1)
                    out_dequantized[(int'(group_index)*8+lane)*20 +:20]<=20'(operand_products[lane]);''','''                out_id<=in_id;out_error<=0;group_index<=0;state<=PREPARE;
            end
            PREPARE:begin
                out_error<=input_bad;
                if(input_bad||tile_zero)begin output_written<=0;state<=HOLD_TILE;end
                else state<=MULTIPLY;
            end
            MULTIPLY:begin
                output_written[group_index]<=1;'''))
dq.append(('''    // The original quantizer/selection/product expressions remain independent''','''    logic reference_bad;
    always_comb begin
        reference_bad=scale_code==3;
        for(integer n=0;n<64;n=n+1)
            if($signed(coefficients[n*16+:16])< -16'sd2048 ||
               $signed(coefficients[n*16+:16])>16'sd2048)reference_bad=1;
    end
    always_ff @(posedge clk)if(state==PREPARE&&!rst&&!abort_i)begin
        assert(input_bad==reference_bad)else $fatal(1,"DQ prepared range differs");
        assert(tile_zero==(coefficients==0))else $fatal(1,"DQ prepared zero differs");
    end
    for(genvar g=0;g<8;g=g+1)begin: output_ownership_assertions
        assert property(@(posedge clk)disable iff(rst||abort_i)
            $rose(output_written[g])|->$past(state==MULTIPLY&&group_index==3'(g)))
            else $fatal(1,"DQ output group exposed without replacement");
    end
    always_ff @(posedge clk)if(out_valid&&!out_error&&!tile_zero&&!rst&&!abort_i)
        assert(&output_written)else $fatal(1,"DQ complete tile has unwritten group");
    // The original quantizer/selection/product expressions remain independent'''))
recipes=[derive('fpga/experiments/cu66-v108-outtile/cu66_idct8x8.sv','cu66_idct8x8.sv',idct),derive('fpga/experiments/cu66-v110-dequant/cu66_dequant.sv','cu66_dequant.sv',dq)]
manifest=dict(schema='v115-inverse-IV115.1-reversible-edit-v1',contract='One registered PREPARE edge per accepted DQ tile and one per accepted IDCT tile; valid content/order/owners unchanged; invalid diagnostic phase shifted, no exact-old-cycle claim.',all_original_assertions_retained=True,recipes=recipes)
p=OUT/'edit-recipe.json';body=json.dumps(manifest,indent=2)+'\n'
if p.exists():assert p.read_text()==body
else:p.write_text(body)
print('V115_INVERSE_PREPARED',[(x['derived'],x['derived_sha256'])for x in recipes])
