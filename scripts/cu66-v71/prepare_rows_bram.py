"""Bank-explicit synchronous RAM successor; preserve all qualified control logic."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2];p=r/'fpga/experiments/cu66-v69/rows/cu66_tile_rows.sv'
d=r/'fpga/experiments/cu66-v71/rows';d.mkdir(parents=True,exist_ok=True)
f=d/'cu71_tile_rows.sv';assert not f.exists()
s=p.read_text().replace('module cu66_tile_rows #(','module cu71_tile_rows #(',1)
old='    logic [63:0] strip [0:STRIP_BANKS-1][0:719];'
assert s.count(old)==1
s=s.replace(old,'    wire [63:0] bank_output [0:STRIP_BANKS-1];\n    logic selected_read_bank;')
old='    always_ff @(posedge clk)if(ram_read_enable)output_word<=strip[ram_read_bank][ram_read_address];'
assert s.count(old)==1
new='''    // Each bank has one explicit synchronous read/write RAM. No data reset.
    wire ram_write_enable=active&&!rst&&!abort_i&&!bad_tile&&write_busy;
    genvar bank_number;
    generate for(bank_number=0;bank_number<STRIP_BANKS;bank_number=bank_number+1)begin:strip_bank
        (* ram_style="block" *) logic [63:0] memory [0:719];
        logic [63:0] read_data;
        always_ff @(posedge clk)begin
            if(ram_write_enable&&fill_bank==bank_number)
                memory[write_address]<=captured_tile[{write_row,6'd0}+:64];
            if(ram_read_enable)read_data<=memory[ram_read_address];
        end
        assign bank_output[bank_number]=read_data;
    end endgenerate
    always_ff @(posedge clk)if(ram_read_enable)selected_read_bank<=ram_read_bank;
    generate if(STRIP_BANKS==1)begin:single_bank
        always_comb output_word=bank_output[0];
    end else begin:two_banks
        always_comb output_word=bank_output[selected_read_bank];
    end endgenerate'''
s=s.replace(old,new)
old='                    strip[fill_bank][write_address]<=captured_tile[{write_row,6\'d0}+:64];strip_word_writes<=strip_word_writes+1;'
assert s.count(old)==1
s=s.replace(old,'                    strip_word_writes<=strip_word_writes+1;')
f.write_text(s,newline='\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(d/'derivation.json').write_text(json.dumps(dict(parent=str(p.relative_to(r)),parent_sha256=sha(p),candidate_sha256=sha(f),scope='Explicit single-clock bank RAM ports, synchronous output and metadata-only reset; same-cycle public equivalence pending'),indent=2)+'\n')
print(f)
