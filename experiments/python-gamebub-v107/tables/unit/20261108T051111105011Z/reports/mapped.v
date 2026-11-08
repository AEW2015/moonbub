// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2026.1 (lin64) Build 6511674 Tue Jun 16 11:01:26 MDT 2026
// Date        : Sun Nov  8 05:11:36 2026
// Host        : geto running 64-bit Ubuntu 22.04.5 LTS
// Command     : write_verilog -force -mode funcsim /build/v107-tables-unit-20261108T051111105011Z/results/mapped.v
// Design      : cu66_tables_unit_v107
// Purpose     : This verilog netlist is a functional simulation representation of the design and should not be modified
//               or synthesized. This netlist cannot be used for SDF annotated simulation.
// Device      : xc7a100tcsg324-1
// --------------------------------------------------------------------------------
`timescale 1 ps / 1 ps

module cu66_mode_store_v107
   (mode_q,
    clk,
    mode_address,
    mode_read_address,
    mode_data,
    mode_read,
    start,
    abort_packet,
    reset,
    mode_write);
  output [1:0]mode_q;
  input clk;
  input [12:0]mode_address;
  input [12:0]mode_read_address;
  input [1:0]mode_data;
  input mode_read;
  input start;
  input abort_packet;
  input reset;
  input mode_write;

  wire abort_packet;
  wire clk;
  wire [12:0]mode_address;
  wire [1:0]mode_data;
  wire [1:0]mode_q;
  wire mode_read;
  wire [12:0]mode_read_address;
  wire mode_write;
  wire reset;
  wire start;
  wire words_reg_i_2_n_0;
  wire write_enable0;
  wire [15:0]NLW_words_reg_DOADO_UNCONNECTED;
  wire [15:2]NLW_words_reg_DOBDO_UNCONNECTED;
  wire [1:0]NLW_words_reg_DOPADOP_UNCONNECTED;
  wire [1:0]NLW_words_reg_DOPBDOP_UNCONNECTED;

  (* \MEM.PORTA.DATA_BIT_LAYOUT  = "p0_d2" *) 
  (* \MEM.PORTB.DATA_BIT_LAYOUT  = "p0_d2" *) 
  (* METHODOLOGY_DRC_VIOS = "{SYNTH-6 {cell *THIS*}}" *) 
  (* RTL_RAM_BITS = "16200" *) 
  (* RTL_RAM_NAME = "cu66_tables_unit_v107/modes/words_reg" *) 
  (* RTL_RAM_STYLE = "block" *) 
  (* RTL_RAM_TYPE = "RAM_SDP" *) 
  (* ram_addr_begin = "0" *) 
  (* ram_addr_end = "8191" *) 
  (* ram_offset = "0" *) 
  (* ram_slice_begin = "0" *) 
  (* ram_slice_end = "1" *) 
  RAMB18E1 #(
    .DOA_REG(0),
    .DOB_REG(0),
    .INIT_A(18'h00000),
    .INIT_B(18'h00000),
    .RAM_MODE("TDP"),
    .RDADDR_COLLISION_HWCONFIG("DELAYED_WRITE"),
    .READ_WIDTH_A(2),
    .READ_WIDTH_B(2),
    .RSTREG_PRIORITY_A("RSTREG"),
    .RSTREG_PRIORITY_B("RSTREG"),
    .SIM_COLLISION_CHECK("ALL"),
    .SIM_DEVICE("7SERIES"),
    .SRVAL_A(18'h00000),
    .SRVAL_B(18'h00000),
    .WRITE_MODE_A("READ_FIRST"),
    .WRITE_MODE_B("WRITE_FIRST"),
    .WRITE_WIDTH_A(2),
    .WRITE_WIDTH_B(2)) 
    words_reg
       (.ADDRARDADDR({mode_address,1'b1}),
        .ADDRBWRADDR({mode_read_address,1'b1}),
        .CLKARDCLK(clk),
        .CLKBWRCLK(clk),
        .DIADI({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,mode_data}),
        .DIBDI({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b1}),
        .DIPADIP({1'b0,1'b0}),
        .DIPBDIP({1'b0,1'b0}),
        .DOADO(NLW_words_reg_DOADO_UNCONNECTED[15:0]),
        .DOBDO({NLW_words_reg_DOBDO_UNCONNECTED[15:2],mode_q}),
        .DOPADOP(NLW_words_reg_DOPADOP_UNCONNECTED[1:0]),
        .DOPBDOP(NLW_words_reg_DOPBDOP_UNCONNECTED[1:0]),
        .ENARDEN(write_enable0),
        .ENBWREN(words_reg_i_2_n_0),
        .REGCEAREGCE(1'b0),
        .REGCEB(1'b0),
        .RSTRAMARSTRAM(1'b0),
        .RSTRAMB(1'b0),
        .RSTREGARSTREG(1'b0),
        .RSTREGB(1'b0),
        .WEA({write_enable0,1'b1}),
        .WEBWE({1'b0,1'b0,1'b0,1'b0}));
  LUT4 #(
    .INIT(16'h0002)) 
    words_reg_i_1__0
       (.I0(mode_write),
        .I1(reset),
        .I2(abort_packet),
        .I3(start),
        .O(write_enable0));
  LUT5 #(
    .INIT(32'h00000002)) 
    words_reg_i_2
       (.I0(mode_read),
        .I1(start),
        .I2(abort_packet),
        .I3(reset),
        .I4(mode_write),
        .O(words_reg_i_2_n_0));
endmodule

module cu66_scale_tdp_v107
   (b_q,
    clk,
    b_addr,
    a_addr,
    b_data,
    a_data,
    b_q_0_sp_1,
    \b_q[0]_0 ,
    b_q_1_sp_1,
    start,
    abort_packet,
    reset,
    b_write,
    a_write);
  output [1:0]b_q;
  input clk;
  input [10:0]b_addr;
  input [10:0]a_addr;
  input [1:0]b_data;
  input [1:0]a_data;
  input b_q_0_sp_1;
  input \b_q[0]_0 ;
  input b_q_1_sp_1;
  input start;
  input abort_packet;
  input reset;
  input b_write;
  input a_write;

  wire [10:0]a_addr;
  wire [1:0]a_data;
  wire a_write;
  wire a_write0;
  wire abort_packet;
  wire [10:0]b_addr;
  wire [1:0]b_data;
  wire [1:0]b_q;
  wire \b_q[0]_0 ;
  wire b_q_0_sn_1;
  wire b_q_1_sn_1;
  wire b_write;
  wire b_write0;
  wire clk;
  wire p_0_in;
  wire p_0_in_carry_i_1_n_0;
  wire p_0_in_carry_i_2_n_0;
  wire p_0_in_carry_i_3_n_0;
  wire p_0_in_carry_i_4_n_0;
  wire p_0_in_carry_n_1;
  wire p_0_in_carry_n_2;
  wire p_0_in_carry_n_3;
  wire p_2_in;
  wire reset;
  wire start;
  wire words_reg_n_14;
  wire words_reg_n_15;
  wire [3:0]NLW_p_0_in_carry_O_UNCONNECTED;
  wire [15:2]NLW_words_reg_DOADO_UNCONNECTED;
  wire [15:0]NLW_words_reg_DOBDO_UNCONNECTED;
  wire [1:0]NLW_words_reg_DOPADOP_UNCONNECTED;
  wire [1:0]NLW_words_reg_DOPBDOP_UNCONNECTED;

  assign b_q_0_sn_1 = b_q_0_sp_1;
  assign b_q_1_sn_1 = b_q_1_sp_1;
  (* SOFT_HLUTNM = "soft_lutpair0" *) 
  LUT3 #(
    .INIT(8'hB8)) 
    \b_q[0]_INST_0 
       (.I0(words_reg_n_15),
        .I1(b_q_0_sn_1),
        .I2(\b_q[0]_0 ),
        .O(b_q[0]));
  (* SOFT_HLUTNM = "soft_lutpair0" *) 
  LUT3 #(
    .INIT(8'hB8)) 
    \b_q[1]_INST_0 
       (.I0(words_reg_n_14),
        .I1(b_q_0_sn_1),
        .I2(b_q_1_sn_1),
        .O(b_q[1]));
  CARRY4 p_0_in_carry
       (.CI(1'b0),
        .CO({p_0_in,p_0_in_carry_n_1,p_0_in_carry_n_2,p_0_in_carry_n_3}),
        .CYINIT(1'b1),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(NLW_p_0_in_carry_O_UNCONNECTED[3:0]),
        .S({p_0_in_carry_i_1_n_0,p_0_in_carry_i_2_n_0,p_0_in_carry_i_3_n_0,p_0_in_carry_i_4_n_0}));
  LUT4 #(
    .INIT(16'h9009)) 
    p_0_in_carry_i_1
       (.I0(a_addr[9]),
        .I1(b_addr[9]),
        .I2(a_addr[10]),
        .I3(b_addr[10]),
        .O(p_0_in_carry_i_1_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    p_0_in_carry_i_2
       (.I0(a_addr[6]),
        .I1(b_addr[6]),
        .I2(b_addr[8]),
        .I3(a_addr[8]),
        .I4(b_addr[7]),
        .I5(a_addr[7]),
        .O(p_0_in_carry_i_2_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    p_0_in_carry_i_3
       (.I0(a_addr[3]),
        .I1(b_addr[3]),
        .I2(b_addr[5]),
        .I3(a_addr[5]),
        .I4(b_addr[4]),
        .I5(a_addr[4]),
        .O(p_0_in_carry_i_3_n_0));
  LUT6 #(
    .INIT(64'h9009000000009009)) 
    p_0_in_carry_i_4
       (.I0(a_addr[0]),
        .I1(b_addr[0]),
        .I2(b_addr[2]),
        .I3(a_addr[2]),
        .I4(b_addr[1]),
        .I5(a_addr[1]),
        .O(p_0_in_carry_i_4_n_0));
  (* \MEM.PORTA.DATA_BIT_LAYOUT  = "p0_d2" *) 
  (* \MEM.PORTB.DATA_BIT_LAYOUT  = "p0_d2" *) 
  (* METHODOLOGY_DRC_VIOS = "{SYNTH-6 {cell *THIS*}} {SYNTH-7 {cell *THIS*}}" *) 
  (* RTL_RAM_BITS = "2700" *) 
  (* RTL_RAM_NAME = "cu66_tables_unit_v107/scales/words_reg" *) 
  (* RTL_RAM_STYLE = "block" *) 
  (* RTL_RAM_TYPE = "RAM_TDP" *) 
  (* ram_addr_begin = "0" *) 
  (* ram_addr_end = "2047" *) 
  (* ram_offset = "0" *) 
  (* ram_slice_begin = "0" *) 
  (* ram_slice_end = "1" *) 
  RAMB18E1 #(
    .DOA_REG(0),
    .DOB_REG(0),
    .INIT_A(18'h00000),
    .INIT_B(18'h00000),
    .RAM_MODE("TDP"),
    .RDADDR_COLLISION_HWCONFIG("DELAYED_WRITE"),
    .READ_WIDTH_A(9),
    .READ_WIDTH_B(9),
    .RSTREG_PRIORITY_A("RSTREG"),
    .RSTREG_PRIORITY_B("RSTREG"),
    .SIM_COLLISION_CHECK("ALL"),
    .SIM_DEVICE("7SERIES"),
    .SRVAL_A(18'h00000),
    .SRVAL_B(18'h00000),
    .WRITE_MODE_A("READ_FIRST"),
    .WRITE_MODE_B("READ_FIRST"),
    .WRITE_WIDTH_A(9),
    .WRITE_WIDTH_B(9)) 
    words_reg
       (.ADDRARDADDR({b_addr,1'b1,1'b1,1'b1}),
        .ADDRBWRADDR({a_addr,1'b1,1'b1,1'b1}),
        .CLKARDCLK(clk),
        .CLKBWRCLK(clk),
        .DIADI({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,b_data}),
        .DIBDI({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,a_data}),
        .DIPADIP({1'b0,1'b0}),
        .DIPBDIP({1'b0,1'b0}),
        .DOADO({NLW_words_reg_DOADO_UNCONNECTED[15:2],words_reg_n_14,words_reg_n_15}),
        .DOBDO(NLW_words_reg_DOBDO_UNCONNECTED[15:0]),
        .DOPADOP(NLW_words_reg_DOPADOP_UNCONNECTED[1:0]),
        .DOPBDOP(NLW_words_reg_DOPBDOP_UNCONNECTED[1:0]),
        .ENARDEN(1'b1),
        .ENBWREN(a_write0),
        .REGCEAREGCE(1'b0),
        .REGCEB(1'b0),
        .RSTRAMARSTRAM(1'b0),
        .RSTRAMB(1'b0),
        .RSTREGARSTREG(1'b0),
        .RSTREGB(1'b0),
        .WEA({b_write0,b_write0}),
        .WEBWE({1'b0,1'b0,p_2_in,p_2_in}));
  LUT4 #(
    .INIT(16'h0002)) 
    words_reg_i_1
       (.I0(a_write),
        .I1(reset),
        .I2(abort_packet),
        .I3(start),
        .O(a_write0));
  LUT4 #(
    .INIT(16'h0002)) 
    words_reg_i_2__0
       (.I0(b_write),
        .I1(reset),
        .I2(abort_packet),
        .I3(start),
        .O(b_write0));
  LUT5 #(
    .INIT(32'hFEFFFFFF)) 
    words_reg_i_3
       (.I0(start),
        .I1(abort_packet),
        .I2(reset),
        .I3(b_write),
        .I4(p_0_in),
        .O(p_2_in));
endmodule

(* NotValidForBitStream *)
module cu66_tables_unit_v107
   (clk,
    reset,
    start,
    abort_packet,
    a_write,
    a_addr,
    a_data,
    b_write,
    b_read,
    b_addr,
    b_data,
    b_q,
    mode_write,
    mode_read,
    mode_address,
    mode_read_address,
    mode_data,
    mode_q);
  input clk;
  input reset;
  input start;
  input abort_packet;
  input a_write;
  input [10:0]a_addr;
  input [1:0]a_data;
  input b_write;
  input b_read;
  input [10:0]b_addr;
  input [1:0]b_data;
  output [1:0]b_q;
  input mode_write;
  input mode_read;
  input [12:0]mode_address;
  input [12:0]mode_read_address;
  input [1:0]mode_data;
  output [1:0]mode_q;

  wire [10:0]a_addr;
  wire [1:0]a_data;
  wire a_write;
  wire abort_packet;
  wire [10:0]b_addr;
  wire [1:0]b_data;
  wire [1:0]b_q;
  wire \b_q[0]_INST_0_i_1_n_0 ;
  wire \b_q[1]_INST_0_i_1_n_0 ;
  wire \b_q[1]_INST_0_i_2_n_0 ;
  wire \b_q[1]_INST_0_i_3_n_0 ;
  wire b_read;
  wire b_write;
  wire clk;
  wire [12:0]mode_address;
  wire [1:0]mode_data;
  wire [1:0]mode_q;
  wire mode_read;
  wire [12:0]mode_read_address;
  wire mode_write;
  wire reset;
  wire start;

  FDRE \b_q[0]_INST_0_i_1 
       (.C(clk),
        .CE(1'b1),
        .D(b_q[0]),
        .Q(\b_q[0]_INST_0_i_1_n_0 ),
        .R(1'b0));
  FDRE #(
    .INIT(1'b1)) 
    \b_q[1]_INST_0_i_1 
       (.C(clk),
        .CE(1'b1),
        .D(\b_q[1]_INST_0_i_3_n_0 ),
        .Q(\b_q[1]_INST_0_i_1_n_0 ),
        .R(1'b0));
  FDRE \b_q[1]_INST_0_i_2 
       (.C(clk),
        .CE(1'b1),
        .D(b_q[1]),
        .Q(\b_q[1]_INST_0_i_2_n_0 ),
        .R(1'b0));
  LUT5 #(
    .INIT(32'h00000002)) 
    \b_q[1]_INST_0_i_3 
       (.I0(b_read),
        .I1(start),
        .I2(abort_packet),
        .I3(reset),
        .I4(b_write),
        .O(\b_q[1]_INST_0_i_3_n_0 ));
  cu66_mode_store_v107 modes
       (.abort_packet(abort_packet),
        .clk(clk),
        .mode_address(mode_address),
        .mode_data(mode_data),
        .mode_q(mode_q),
        .mode_read(mode_read),
        .mode_read_address(mode_read_address),
        .mode_write(mode_write),
        .reset(reset),
        .start(start));
  cu66_scale_tdp_v107 scales
       (.a_addr(a_addr),
        .a_data(a_data),
        .a_write(a_write),
        .abort_packet(abort_packet),
        .b_addr(b_addr),
        .b_data(b_data),
        .b_q(b_q),
        .\b_q[0]_0 (\b_q[0]_INST_0_i_1_n_0 ),
        .b_q_0_sp_1(\b_q[1]_INST_0_i_1_n_0 ),
        .b_q_1_sp_1(\b_q[1]_INST_0_i_2_n_0 ),
        .b_write(b_write),
        .clk(clk),
        .reset(reset),
        .start(start));
endmodule
`ifndef GLBL
`define GLBL
`timescale  1 ps / 1 ps

module glbl ();

    parameter ROC_WIDTH = 100000;
    parameter TOC_WIDTH = 0;
    parameter GRES_WIDTH = 10000;
    parameter GRES_START = 10000;

//--------   STARTUP Globals --------------
    wire GSR;
    wire GTS;
    wire GWE;
    wire PRLD;
    wire GRESTORE;
    tri1 p_up_tmp;
    tri (weak1, strong0) PLL_LOCKG = p_up_tmp;

    wire PROGB_GLBL;
    wire CCLKO_GLBL;
    wire FCSBO_GLBL;
    wire [3:0] DO_GLBL;
    wire [3:0] DI_GLBL;
   
    reg GSR_int;
    reg GTS_int;
    reg PRLD_int;
    reg GRESTORE_int;

//--------   JTAG Globals --------------
    wire JTAG_TDO_GLBL;
    wire JTAG_TCK_GLBL;
    wire JTAG_TDI_GLBL;
    wire JTAG_TMS_GLBL;
    wire JTAG_TRST_GLBL;

    reg JTAG_CAPTURE_GLBL;
    reg JTAG_RESET_GLBL;
    reg JTAG_SHIFT_GLBL;
    reg JTAG_UPDATE_GLBL;
    reg JTAG_RUNTEST_GLBL;

    reg JTAG_SEL1_GLBL = 0;
    reg JTAG_SEL2_GLBL = 0 ;
    reg JTAG_SEL3_GLBL = 0;
    reg JTAG_SEL4_GLBL = 0;

    reg JTAG_USER_TDO1_GLBL = 1'bz;
    reg JTAG_USER_TDO2_GLBL = 1'bz;
    reg JTAG_USER_TDO3_GLBL = 1'bz;
    reg JTAG_USER_TDO4_GLBL = 1'bz;

    assign (strong1, weak0) GSR = GSR_int;
    assign (strong1, weak0) GTS = GTS_int;
    assign (weak1, weak0) PRLD = PRLD_int;
    assign (strong1, weak0) GRESTORE = GRESTORE_int;

    initial begin
	GSR_int = 1'b1;
	PRLD_int = 1'b1;
	#(ROC_WIDTH)
	GSR_int = 1'b0;
	PRLD_int = 1'b0;
    end

    initial begin
	GTS_int = 1'b1;
	#(TOC_WIDTH)
	GTS_int = 1'b0;
    end

    initial begin 
	GRESTORE_int = 1'b0;
	#(GRES_START);
	GRESTORE_int = 1'b1;
	#(GRES_WIDTH);
	GRESTORE_int = 1'b0;
    end

endmodule
`endif
