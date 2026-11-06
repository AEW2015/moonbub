"""Minimal exact PLL/MMCM/reset+20IOBUF shell; no decoder or implementation."""
from pathlib import Path
parent=Path(__file__).with_name('probe_constraint_directory.py');s=parent.read_text()
new='''header=text[:text.index(' wire[11:0]buttons=')]
outputs=outputs.replace('mcu_irq_n,','').replace('lcd_dotclk,','').replace('sdram_clk,','')
body='''+repr('''
reg[7:0] count=0,spicount=0,panelcount=0;
wire[15:0] sdram_i;
genvar j;generate for(j=0;j<16;j=j+1)begin:sd_io
 IOBUF io(.IO(sdram_dq[j]),.I(count[j%8]),.O(sdram_i[j]),.T(count[1]));
end endgenerate
assign dq_o=count[3:0];assign dq_oe={4{count[1]}};assign irq=count[0];
always @(posedge clk100)if(rst)count<=0;else count<=count+{7'd0,(^dq_i)^(^sdram_i)^mcu_spi_clk^mcu_spi_cs_n^btn_a^btn_b^btn_x^btn_y^btn_up^btn_down^btn_left^btn_right^btn_l^btn_r^btn_start^btn_select};
always @(posedge clk200)if(joint_spi_reset[3])spicount<=0;else spicount<=spicount+count;
always @(posedge pclk)if(joint_pixel_reset[3])panelcount<=0;else panelcount<=panelcount+count;
assign lcd_dotclk=pclk;assign sdram_clk=read_clk100;
assign {OUTPUTS}={200{count[0]^spicount[0]^panelcount[0]}};
endmodule
''')+'''.replace('OUTPUTS',outputs)
'''
needle="(o/'minimal.sv').write_text(header+body,newline='\\n');"
assert s.count(needle)==1;s=s.replace(needle,new+needle)
s=s.replace("minimal_source_sha256=sha(o/'minimal.sv'),","minimal_source_sha256=sha(o/'minimal.sv'),exact_prefix_parent_end='wire[11:0]buttons',exact_PLL_MMCM_reset_shell=True,IOBUF_count=20,")
exec(compile(s,str(parent),'exec'),globals())
