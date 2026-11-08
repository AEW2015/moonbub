`timescale 1ns/1ps
// Cause-finding only. Not the black-box qualification harness.
module primitive_startup_diag;
always @(posedge tb_stb1_blackbox.clk) begin
 #0.2;
 if($time<=310)$display("DIAG t=%t rst=%b gsr=%b q=%b D=%b lut_rst=%b LUT=%b INITupper=%h Qout=%b inputs=%b%b%b%b%b",$time,tb_stb1_blackbox.rst,glbl.GSR,tb_stb1_blackbox.dut.fault,tb_stb1_blackbox.dut.fault_reg.D,tb_stb1_blackbox.dut.fault_i_1.I5,tb_stb1_blackbox.dut.fault_i_1.O,tb_stb1_blackbox.dut.fault_i_1.INIT_REG[63:32],tb_stb1_blackbox.dut.fault_reg.Q_out,tb_stb1_blackbox.dut.fault_i_1.I4,tb_stb1_blackbox.dut.fault_i_1.I3,tb_stb1_blackbox.dut.fault_i_1.I2,tb_stb1_blackbox.dut.fault_i_1.I1,tb_stb1_blackbox.dut.fault_i_1.I0);
end
endmodule
