// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2026.1 (lin64) Build 6511674 Tue Jun 16 11:01:26 MDT 2026
// Date        : Sun Nov  8 07:21:03 2026
// Host        : geto running 64-bit Ubuntu 22.04.5 LTS
// Command     : write_verilog -force -mode funcsim /build/v107-threshold-unit-20261108T072036746798Z/results/mapped.v
// Design      : threshold_math_probe
// Purpose     : This verilog netlist is a functional simulation representation of the design and should not be modified
//               or synthesized. This netlist cannot be used for SDF annotated simulation.
// Device      : xc7a100tcsg324-1
// --------------------------------------------------------------------------------
`timescale 1 ps / 1 ps

(* NotValidForBitStream *)
module threshold_math_probe
   (clk,
    reset,
    take,
    selected,
    numerator,
    blocks,
    meta_threshold1,
    meta_threshold2,
    meta_threshold3,
    live,
    bad,
    selected_bad);
  input clk;
  input reset;
  input take;
  input [1:0]selected;
  input [31:0]numerator;
  input [16:0]blocks;
  output [31:0]meta_threshold1;
  output [31:0]meta_threshold2;
  output [31:0]meta_threshold3;
  output [2:0]live;
  output [2:0]bad;
  output selected_bad;

  wire \<const0> ;
  wire [15:0]A;
  wire [2:0]bad;
  wire \bad[0]_INST_0_i_10_n_0 ;
  wire \bad[0]_INST_0_i_10_n_1 ;
  wire \bad[0]_INST_0_i_10_n_2 ;
  wire \bad[0]_INST_0_i_10_n_3 ;
  wire \bad[0]_INST_0_i_11_n_0 ;
  wire \bad[0]_INST_0_i_12_n_0 ;
  wire \bad[0]_INST_0_i_13_n_0 ;
  wire \bad[0]_INST_0_i_14_n_0 ;
  wire \bad[0]_INST_0_i_15_n_0 ;
  wire \bad[0]_INST_0_i_16_n_0 ;
  wire \bad[0]_INST_0_i_17_n_0 ;
  wire \bad[0]_INST_0_i_18_n_0 ;
  wire \bad[0]_INST_0_i_19_n_0 ;
  wire \bad[0]_INST_0_i_19_n_1 ;
  wire \bad[0]_INST_0_i_19_n_2 ;
  wire \bad[0]_INST_0_i_19_n_3 ;
  wire \bad[0]_INST_0_i_1_n_0 ;
  wire \bad[0]_INST_0_i_1_n_1 ;
  wire \bad[0]_INST_0_i_1_n_2 ;
  wire \bad[0]_INST_0_i_1_n_3 ;
  wire \bad[0]_INST_0_i_20_n_0 ;
  wire \bad[0]_INST_0_i_21_n_0 ;
  wire \bad[0]_INST_0_i_22_n_0 ;
  wire \bad[0]_INST_0_i_23_n_0 ;
  wire \bad[0]_INST_0_i_24_n_0 ;
  wire \bad[0]_INST_0_i_25_n_0 ;
  wire \bad[0]_INST_0_i_26_n_0 ;
  wire \bad[0]_INST_0_i_27_n_0 ;
  wire \bad[0]_INST_0_i_28_n_0 ;
  wire \bad[0]_INST_0_i_29_n_0 ;
  wire \bad[0]_INST_0_i_2_n_0 ;
  wire \bad[0]_INST_0_i_30_n_0 ;
  wire \bad[0]_INST_0_i_31_n_0 ;
  wire \bad[0]_INST_0_i_32_n_0 ;
  wire \bad[0]_INST_0_i_33_n_0 ;
  wire \bad[0]_INST_0_i_34_n_0 ;
  wire \bad[0]_INST_0_i_35_n_0 ;
  wire \bad[0]_INST_0_i_3_n_0 ;
  wire \bad[0]_INST_0_i_4_n_0 ;
  wire \bad[0]_INST_0_i_5_n_0 ;
  wire \bad[0]_INST_0_i_6_n_0 ;
  wire \bad[0]_INST_0_i_7_n_0 ;
  wire \bad[0]_INST_0_i_8_n_0 ;
  wire \bad[0]_INST_0_i_9_n_0 ;
  wire \bad[0]_INST_0_n_1 ;
  wire \bad[0]_INST_0_n_2 ;
  wire \bad[0]_INST_0_n_3 ;
  wire \bad[1]_INST_0_i_10_n_0 ;
  wire \bad[1]_INST_0_i_11_n_0 ;
  wire \bad[1]_INST_0_i_12_n_0 ;
  wire \bad[1]_INST_0_i_13_n_0 ;
  wire \bad[1]_INST_0_i_14_n_0 ;
  wire \bad[1]_INST_0_i_15_n_0 ;
  wire \bad[1]_INST_0_i_16_n_0 ;
  wire \bad[1]_INST_0_i_17_n_0 ;
  wire \bad[1]_INST_0_i_18_n_0 ;
  wire \bad[1]_INST_0_i_18_n_1 ;
  wire \bad[1]_INST_0_i_18_n_2 ;
  wire \bad[1]_INST_0_i_18_n_3 ;
  wire \bad[1]_INST_0_i_19_n_0 ;
  wire \bad[1]_INST_0_i_1_n_0 ;
  wire \bad[1]_INST_0_i_1_n_1 ;
  wire \bad[1]_INST_0_i_1_n_2 ;
  wire \bad[1]_INST_0_i_1_n_3 ;
  wire \bad[1]_INST_0_i_20_n_0 ;
  wire \bad[1]_INST_0_i_21_n_0 ;
  wire \bad[1]_INST_0_i_22_n_0 ;
  wire \bad[1]_INST_0_i_23_n_0 ;
  wire \bad[1]_INST_0_i_24_n_0 ;
  wire \bad[1]_INST_0_i_25_n_0 ;
  wire \bad[1]_INST_0_i_26_n_0 ;
  wire \bad[1]_INST_0_i_27_n_0 ;
  wire \bad[1]_INST_0_i_28_n_0 ;
  wire \bad[1]_INST_0_i_29_n_0 ;
  wire \bad[1]_INST_0_i_2_n_0 ;
  wire \bad[1]_INST_0_i_30_n_0 ;
  wire \bad[1]_INST_0_i_31_n_0 ;
  wire \bad[1]_INST_0_i_32_n_0 ;
  wire \bad[1]_INST_0_i_33_n_0 ;
  wire \bad[1]_INST_0_i_34_n_0 ;
  wire \bad[1]_INST_0_i_3_n_0 ;
  wire \bad[1]_INST_0_i_4_n_0 ;
  wire \bad[1]_INST_0_i_5_n_0 ;
  wire \bad[1]_INST_0_i_6_n_0 ;
  wire \bad[1]_INST_0_i_7_n_0 ;
  wire \bad[1]_INST_0_i_8_n_0 ;
  wire \bad[1]_INST_0_i_9_n_0 ;
  wire \bad[1]_INST_0_i_9_n_1 ;
  wire \bad[1]_INST_0_i_9_n_2 ;
  wire \bad[1]_INST_0_i_9_n_3 ;
  wire \bad[1]_INST_0_n_1 ;
  wire \bad[1]_INST_0_n_2 ;
  wire \bad[1]_INST_0_n_3 ;
  wire \bad[2]_INST_0_i_10_n_0 ;
  wire \bad[2]_INST_0_i_11_n_0 ;
  wire \bad[2]_INST_0_i_12_n_0 ;
  wire \bad[2]_INST_0_i_13_n_0 ;
  wire \bad[2]_INST_0_i_14_n_0 ;
  wire \bad[2]_INST_0_i_15_n_0 ;
  wire \bad[2]_INST_0_i_16_n_0 ;
  wire \bad[2]_INST_0_i_16_n_1 ;
  wire \bad[2]_INST_0_i_16_n_2 ;
  wire \bad[2]_INST_0_i_16_n_3 ;
  wire \bad[2]_INST_0_i_17_n_0 ;
  wire \bad[2]_INST_0_i_18_n_0 ;
  wire \bad[2]_INST_0_i_19_n_0 ;
  wire \bad[2]_INST_0_i_1_n_0 ;
  wire \bad[2]_INST_0_i_1_n_1 ;
  wire \bad[2]_INST_0_i_1_n_2 ;
  wire \bad[2]_INST_0_i_1_n_3 ;
  wire \bad[2]_INST_0_i_20_n_0 ;
  wire \bad[2]_INST_0_i_21_n_0 ;
  wire \bad[2]_INST_0_i_22_n_0 ;
  wire \bad[2]_INST_0_i_23_n_0 ;
  wire \bad[2]_INST_0_i_24_n_0 ;
  wire \bad[2]_INST_0_i_25_n_0 ;
  wire \bad[2]_INST_0_i_26_n_0 ;
  wire \bad[2]_INST_0_i_27_n_0 ;
  wire \bad[2]_INST_0_i_28_n_0 ;
  wire \bad[2]_INST_0_i_29_n_0 ;
  wire \bad[2]_INST_0_i_2_n_0 ;
  wire \bad[2]_INST_0_i_30_n_0 ;
  wire \bad[2]_INST_0_i_31_n_0 ;
  wire \bad[2]_INST_0_i_32_n_0 ;
  wire \bad[2]_INST_0_i_3_n_0 ;
  wire \bad[2]_INST_0_i_4_n_0 ;
  wire \bad[2]_INST_0_i_5_n_0 ;
  wire \bad[2]_INST_0_i_6_n_0 ;
  wire \bad[2]_INST_0_i_7_n_0 ;
  wire \bad[2]_INST_0_i_7_n_1 ;
  wire \bad[2]_INST_0_i_7_n_2 ;
  wire \bad[2]_INST_0_i_7_n_3 ;
  wire \bad[2]_INST_0_i_8_n_0 ;
  wire \bad[2]_INST_0_i_9_n_0 ;
  wire \bad[2]_INST_0_n_2 ;
  wire \bad[2]_INST_0_n_3 ;
  wire [16:0]blocks;
  wire clk;
  wire descriptor_count_bad0;
  wire [2:0]live;
  wire [31:0]meta_threshold1;
  wire [30:0]\^meta_threshold2 ;
  wire [28:0]\^meta_threshold3 ;
  wire [31:0]numerator;
  wire p_0_in;
  wire [31:0]p_0_in1_in;
  wire [0:0]p_1_out;
  wire [28:0]partial_product1_return__0;
  wire [29:0]partial_product_return__0;
  wire reset;
  wire [1:0]selected;
  wire selected_bad;
  wire selected_bad_INST_0_i_10_n_0;
  wire selected_bad_INST_0_i_11_n_0;
  wire selected_bad_INST_0_i_11_n_1;
  wire selected_bad_INST_0_i_11_n_2;
  wire selected_bad_INST_0_i_11_n_3;
  wire selected_bad_INST_0_i_12_n_0;
  wire selected_bad_INST_0_i_13_n_0;
  wire selected_bad_INST_0_i_14_n_0;
  wire selected_bad_INST_0_i_15_n_0;
  wire selected_bad_INST_0_i_16_n_0;
  wire selected_bad_INST_0_i_17_n_0;
  wire selected_bad_INST_0_i_18_n_0;
  wire selected_bad_INST_0_i_19_n_0;
  wire selected_bad_INST_0_i_1_n_1;
  wire selected_bad_INST_0_i_1_n_2;
  wire selected_bad_INST_0_i_1_n_3;
  wire selected_bad_INST_0_i_20_n_0;
  wire selected_bad_INST_0_i_20_n_1;
  wire selected_bad_INST_0_i_20_n_2;
  wire selected_bad_INST_0_i_20_n_3;
  wire selected_bad_INST_0_i_21_n_0;
  wire selected_bad_INST_0_i_22_n_0;
  wire selected_bad_INST_0_i_23_n_0;
  wire selected_bad_INST_0_i_24_n_0;
  wire selected_bad_INST_0_i_25_n_0;
  wire selected_bad_INST_0_i_26_n_0;
  wire selected_bad_INST_0_i_27_n_0;
  wire selected_bad_INST_0_i_28_n_0;
  wire selected_bad_INST_0_i_29_n_0;
  wire selected_bad_INST_0_i_2_n_0;
  wire selected_bad_INST_0_i_2_n_1;
  wire selected_bad_INST_0_i_2_n_2;
  wire selected_bad_INST_0_i_2_n_3;
  wire selected_bad_INST_0_i_30_n_0;
  wire selected_bad_INST_0_i_31_n_0;
  wire selected_bad_INST_0_i_32_n_0;
  wire selected_bad_INST_0_i_33_n_0;
  wire selected_bad_INST_0_i_34_n_0;
  wire selected_bad_INST_0_i_35_n_0;
  wire selected_bad_INST_0_i_36_n_0;
  wire selected_bad_INST_0_i_3_n_0;
  wire selected_bad_INST_0_i_4_n_0;
  wire selected_bad_INST_0_i_5_n_0;
  wire selected_bad_INST_0_i_6_n_0;
  wire selected_bad_INST_0_i_7_n_0;
  wire selected_bad_INST_0_i_8_n_0;
  wire selected_bad_INST_0_i_9_n_0;
  wire take;
  wire \threshold_pipes[0].check_hi_reg_i_1_n_1 ;
  wire \threshold_pipes[0].check_hi_reg_i_1_n_3 ;
  wire \threshold_pipes[0].check_hi_reg_i_1_n_6 ;
  wire \threshold_pipes[0].check_hi_reg_i_1_n_7 ;
  wire \threshold_pipes[0].check_hi_reg_i_2_n_0 ;
  wire \threshold_pipes[0].check_hi_reg_i_2_n_1 ;
  wire \threshold_pipes[0].check_hi_reg_i_2_n_2 ;
  wire \threshold_pipes[0].check_hi_reg_i_2_n_3 ;
  wire \threshold_pipes[0].check_hi_reg_i_2_n_4 ;
  wire \threshold_pipes[0].check_hi_reg_i_2_n_5 ;
  wire \threshold_pipes[0].check_hi_reg_i_2_n_6 ;
  wire \threshold_pipes[0].check_hi_reg_i_2_n_7 ;
  wire \threshold_pipes[0].check_hi_reg_i_3_n_0 ;
  wire \threshold_pipes[0].check_hi_reg_i_3_n_1 ;
  wire \threshold_pipes[0].check_hi_reg_i_3_n_2 ;
  wire \threshold_pipes[0].check_hi_reg_i_3_n_3 ;
  wire \threshold_pipes[0].check_hi_reg_i_3_n_4 ;
  wire \threshold_pipes[0].check_hi_reg_i_3_n_5 ;
  wire \threshold_pipes[0].check_hi_reg_i_3_n_6 ;
  wire \threshold_pipes[0].check_hi_reg_i_3_n_7 ;
  wire \threshold_pipes[0].check_hi_reg_i_4_n_0 ;
  wire \threshold_pipes[0].check_hi_reg_i_4_n_1 ;
  wire \threshold_pipes[0].check_hi_reg_i_4_n_2 ;
  wire \threshold_pipes[0].check_hi_reg_i_4_n_3 ;
  wire \threshold_pipes[0].check_hi_reg_i_4_n_4 ;
  wire \threshold_pipes[0].check_hi_reg_i_4_n_5 ;
  wire \threshold_pipes[0].check_hi_reg_i_4_n_6 ;
  wire \threshold_pipes[0].check_hi_reg_i_4_n_7 ;
  wire \threshold_pipes[0].check_hi_reg_n_100 ;
  wire \threshold_pipes[0].check_hi_reg_n_101 ;
  wire \threshold_pipes[0].check_hi_reg_n_102 ;
  wire \threshold_pipes[0].check_hi_reg_n_103 ;
  wire \threshold_pipes[0].check_hi_reg_n_104 ;
  wire \threshold_pipes[0].check_hi_reg_n_105 ;
  wire \threshold_pipes[0].check_hi_reg_n_90 ;
  wire \threshold_pipes[0].check_hi_reg_n_91 ;
  wire \threshold_pipes[0].check_hi_reg_n_92 ;
  wire \threshold_pipes[0].check_hi_reg_n_93 ;
  wire \threshold_pipes[0].check_hi_reg_n_94 ;
  wire \threshold_pipes[0].check_hi_reg_n_95 ;
  wire \threshold_pipes[0].check_hi_reg_n_96 ;
  wire \threshold_pipes[0].check_hi_reg_n_97 ;
  wire \threshold_pipes[0].check_hi_reg_n_98 ;
  wire \threshold_pipes[0].check_hi_reg_n_99 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_10_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_11_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_12_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_13_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_14_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_15_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_2_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_3_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_4_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_5_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_6_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_7_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_8_n_0 ;
  wire \threshold_pipes[0].count_threshold[0][3]_i_9_n_0 ;
  wire \threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_0 ;
  wire \threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_1 ;
  wire \threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_2 ;
  wire \threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_3 ;
  wire \threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_0 ;
  wire \threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_1 ;
  wire \threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_2 ;
  wire \threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_3 ;
  wire \threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_0 ;
  wire \threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_1 ;
  wire \threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_2 ;
  wire \threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_3 ;
  wire \threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_0 ;
  wire \threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_1 ;
  wire \threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_2 ;
  wire \threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_3 ;
  wire \threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_0 ;
  wire \threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_1 ;
  wire \threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_2 ;
  wire \threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_3 ;
  wire \threshold_pipes[0].count_threshold_reg[0][31]_i_1_n_2 ;
  wire \threshold_pipes[0].count_threshold_reg[0][31]_i_1_n_3 ;
  wire \threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_0 ;
  wire \threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_1 ;
  wire \threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_2 ;
  wire \threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_3 ;
  wire \threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_0 ;
  wire \threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_1 ;
  wire \threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_2 ;
  wire \threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_3 ;
  wire [15:0]\threshold_pipes[0].cross_carry_s2 ;
  wire [31:16]\threshold_pipes[0].cross_carry_s21 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_10_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_12_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_13_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_14_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_15_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_16_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_17_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_18_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_19_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_4_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_5_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_7_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_8_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2[3]_i_9_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_1 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_2 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_3 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[15]_i_1_n_2 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[15]_i_1_n_3 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_1 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_2 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_3 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_1 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_2 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_3 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_1 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_2 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_3 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_1 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_2 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_3 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_1 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_2 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_3 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_0 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_1 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_2 ;
  wire \threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_3 ;
  wire \threshold_pipes[0].cross_s1_reg_n_100 ;
  wire \threshold_pipes[0].cross_s1_reg_n_101 ;
  wire \threshold_pipes[0].cross_s1_reg_n_102 ;
  wire \threshold_pipes[0].cross_s1_reg_n_103 ;
  wire \threshold_pipes[0].cross_s1_reg_n_104 ;
  wire \threshold_pipes[0].cross_s1_reg_n_105 ;
  wire \threshold_pipes[0].cross_s1_reg_n_75 ;
  wire \threshold_pipes[0].cross_s1_reg_n_76 ;
  wire \threshold_pipes[0].cross_s1_reg_n_77 ;
  wire \threshold_pipes[0].cross_s1_reg_n_78 ;
  wire \threshold_pipes[0].cross_s1_reg_n_79 ;
  wire \threshold_pipes[0].cross_s1_reg_n_80 ;
  wire \threshold_pipes[0].cross_s1_reg_n_81 ;
  wire \threshold_pipes[0].cross_s1_reg_n_82 ;
  wire \threshold_pipes[0].cross_s1_reg_n_83 ;
  wire \threshold_pipes[0].cross_s1_reg_n_84 ;
  wire \threshold_pipes[0].cross_s1_reg_n_85 ;
  wire \threshold_pipes[0].cross_s1_reg_n_86 ;
  wire \threshold_pipes[0].cross_s1_reg_n_87 ;
  wire \threshold_pipes[0].cross_s1_reg_n_88 ;
  wire \threshold_pipes[0].cross_s1_reg_n_89 ;
  wire \threshold_pipes[0].cross_s1_reg_n_90 ;
  wire \threshold_pipes[0].cross_s1_reg_n_91 ;
  wire \threshold_pipes[0].cross_s1_reg_n_92 ;
  wire \threshold_pipes[0].cross_s1_reg_n_93 ;
  wire \threshold_pipes[0].cross_s1_reg_n_94 ;
  wire \threshold_pipes[0].cross_s1_reg_n_95 ;
  wire \threshold_pipes[0].cross_s1_reg_n_96 ;
  wire \threshold_pipes[0].cross_s1_reg_n_97 ;
  wire \threshold_pipes[0].cross_s1_reg_n_98 ;
  wire \threshold_pipes[0].cross_s1_reg_n_99 ;
  wire \threshold_pipes[0].high_s1_reg_n_100 ;
  wire \threshold_pipes[0].high_s1_reg_n_101 ;
  wire \threshold_pipes[0].high_s1_reg_n_102 ;
  wire \threshold_pipes[0].high_s1_reg_n_103 ;
  wire \threshold_pipes[0].high_s1_reg_n_104 ;
  wire \threshold_pipes[0].high_s1_reg_n_105 ;
  wire \threshold_pipes[0].high_s1_reg_n_76 ;
  wire \threshold_pipes[0].high_s1_reg_n_77 ;
  wire \threshold_pipes[0].high_s1_reg_n_78 ;
  wire \threshold_pipes[0].high_s1_reg_n_79 ;
  wire \threshold_pipes[0].high_s1_reg_n_80 ;
  wire \threshold_pipes[0].high_s1_reg_n_81 ;
  wire \threshold_pipes[0].high_s1_reg_n_82 ;
  wire \threshold_pipes[0].high_s1_reg_n_83 ;
  wire \threshold_pipes[0].high_s1_reg_n_84 ;
  wire \threshold_pipes[0].high_s1_reg_n_85 ;
  wire \threshold_pipes[0].high_s1_reg_n_86 ;
  wire \threshold_pipes[0].high_s1_reg_n_87 ;
  wire \threshold_pipes[0].high_s1_reg_n_88 ;
  wire \threshold_pipes[0].high_s1_reg_n_89 ;
  wire \threshold_pipes[0].high_s1_reg_n_90 ;
  wire \threshold_pipes[0].high_s1_reg_n_91 ;
  wire \threshold_pipes[0].high_s1_reg_n_92 ;
  wire \threshold_pipes[0].high_s1_reg_n_93 ;
  wire \threshold_pipes[0].high_s1_reg_n_94 ;
  wire \threshold_pipes[0].high_s1_reg_n_95 ;
  wire \threshold_pipes[0].high_s1_reg_n_96 ;
  wire \threshold_pipes[0].high_s1_reg_n_97 ;
  wire \threshold_pipes[0].high_s1_reg_n_98 ;
  wire \threshold_pipes[0].high_s1_reg_n_99 ;
  wire [29:0]\threshold_pipes[0].high_s2 ;
  wire [13:0]\threshold_pipes[0].low_carry_s1 ;
  wire [13:0]\threshold_pipes[0].mul00_hi ;
  wire \threshold_pipes[0].n_delay_reg[4][0]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][10]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][11]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][12]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][13]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][14]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][15]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][16]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][17]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][18]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][19]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][1]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][20]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][21]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][22]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][23]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][24]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][25]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][26]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][27]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][28]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][29]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][2]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][30]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][31]_srl5_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][3]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][4]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][5]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][6]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][7]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][8]_srl6_n_0 ;
  wire \threshold_pipes[0].n_delay_reg[4][9]_srl6_n_0 ;
  wire [31:0]\threshold_pipes[0].n_delay_reg[5] ;
  wire [31:0]\threshold_pipes[0].product_s5_reg__0 ;
  wire \threshold_pipes[0].product_s5_reg_i_10_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_11_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_12_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_13_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_14_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_15_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_16_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_17_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_18_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_19_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_1_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_1_n_1 ;
  wire \threshold_pipes[0].product_s5_reg_i_1_n_2 ;
  wire \threshold_pipes[0].product_s5_reg_i_1_n_3 ;
  wire \threshold_pipes[0].product_s5_reg_i_1_n_4 ;
  wire \threshold_pipes[0].product_s5_reg_i_1_n_5 ;
  wire \threshold_pipes[0].product_s5_reg_i_1_n_6 ;
  wire \threshold_pipes[0].product_s5_reg_i_1_n_7 ;
  wire \threshold_pipes[0].product_s5_reg_i_20_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_2_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_2_n_1 ;
  wire \threshold_pipes[0].product_s5_reg_i_2_n_2 ;
  wire \threshold_pipes[0].product_s5_reg_i_2_n_3 ;
  wire \threshold_pipes[0].product_s5_reg_i_2_n_4 ;
  wire \threshold_pipes[0].product_s5_reg_i_2_n_5 ;
  wire \threshold_pipes[0].product_s5_reg_i_2_n_6 ;
  wire \threshold_pipes[0].product_s5_reg_i_2_n_7 ;
  wire \threshold_pipes[0].product_s5_reg_i_3_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_3_n_1 ;
  wire \threshold_pipes[0].product_s5_reg_i_3_n_2 ;
  wire \threshold_pipes[0].product_s5_reg_i_3_n_3 ;
  wire \threshold_pipes[0].product_s5_reg_i_3_n_4 ;
  wire \threshold_pipes[0].product_s5_reg_i_3_n_5 ;
  wire \threshold_pipes[0].product_s5_reg_i_3_n_6 ;
  wire \threshold_pipes[0].product_s5_reg_i_3_n_7 ;
  wire \threshold_pipes[0].product_s5_reg_i_4_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_4_n_1 ;
  wire \threshold_pipes[0].product_s5_reg_i_4_n_2 ;
  wire \threshold_pipes[0].product_s5_reg_i_4_n_3 ;
  wire \threshold_pipes[0].product_s5_reg_i_4_n_4 ;
  wire \threshold_pipes[0].product_s5_reg_i_4_n_5 ;
  wire \threshold_pipes[0].product_s5_reg_i_4_n_6 ;
  wire \threshold_pipes[0].product_s5_reg_i_4_n_7 ;
  wire \threshold_pipes[0].product_s5_reg_i_5_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_6_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_7_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_8_n_0 ;
  wire \threshold_pipes[0].product_s5_reg_i_9_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[0]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[10]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[11]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[12]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[13]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[14]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[15]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[16]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[17]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[18]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[19]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[1]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[20]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[21]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[22]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[23]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[24]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[25]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[26]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[27]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[28]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[29]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[2]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[30]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[3]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[4]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[5]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[6]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[7]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[8]_srl3_n_0 ;
  wire \threshold_pipes[0].q_s5_reg[9]_srl3_n_0 ;
  wire [30:0]\threshold_pipes[0].q_s6 ;
  wire [31:0]\threshold_pipes[0].remainder_s6 ;
  wire [31:0]\threshold_pipes[0].remainder_s602_out ;
  wire \threshold_pipes[0].remainder_s6[11]_i_2_n_0 ;
  wire \threshold_pipes[0].remainder_s6[11]_i_3_n_0 ;
  wire \threshold_pipes[0].remainder_s6[11]_i_4_n_0 ;
  wire \threshold_pipes[0].remainder_s6[11]_i_5_n_0 ;
  wire \threshold_pipes[0].remainder_s6[15]_i_2_n_0 ;
  wire \threshold_pipes[0].remainder_s6[15]_i_3_n_0 ;
  wire \threshold_pipes[0].remainder_s6[15]_i_4_n_0 ;
  wire \threshold_pipes[0].remainder_s6[15]_i_5_n_0 ;
  wire \threshold_pipes[0].remainder_s6[19]_i_2_n_0 ;
  wire \threshold_pipes[0].remainder_s6[19]_i_3_n_0 ;
  wire \threshold_pipes[0].remainder_s6[19]_i_4_n_0 ;
  wire \threshold_pipes[0].remainder_s6[19]_i_5_n_0 ;
  wire \threshold_pipes[0].remainder_s6[23]_i_2_n_0 ;
  wire \threshold_pipes[0].remainder_s6[23]_i_3_n_0 ;
  wire \threshold_pipes[0].remainder_s6[23]_i_4_n_0 ;
  wire \threshold_pipes[0].remainder_s6[23]_i_5_n_0 ;
  wire \threshold_pipes[0].remainder_s6[27]_i_2_n_0 ;
  wire \threshold_pipes[0].remainder_s6[27]_i_3_n_0 ;
  wire \threshold_pipes[0].remainder_s6[27]_i_4_n_0 ;
  wire \threshold_pipes[0].remainder_s6[27]_i_5_n_0 ;
  wire \threshold_pipes[0].remainder_s6[31]_i_2_n_0 ;
  wire \threshold_pipes[0].remainder_s6[31]_i_3_n_0 ;
  wire \threshold_pipes[0].remainder_s6[31]_i_4_n_0 ;
  wire \threshold_pipes[0].remainder_s6[31]_i_5_n_0 ;
  wire \threshold_pipes[0].remainder_s6[3]_i_2_n_0 ;
  wire \threshold_pipes[0].remainder_s6[3]_i_3_n_0 ;
  wire \threshold_pipes[0].remainder_s6[3]_i_4_n_0 ;
  wire \threshold_pipes[0].remainder_s6[3]_i_5_n_0 ;
  wire \threshold_pipes[0].remainder_s6[7]_i_2_n_0 ;
  wire \threshold_pipes[0].remainder_s6[7]_i_3_n_0 ;
  wire \threshold_pipes[0].remainder_s6[7]_i_4_n_0 ;
  wire \threshold_pipes[0].remainder_s6[7]_i_5_n_0 ;
  wire \threshold_pipes[0].remainder_s6_reg[11]_i_1_n_0 ;
  wire \threshold_pipes[0].remainder_s6_reg[11]_i_1_n_1 ;
  wire \threshold_pipes[0].remainder_s6_reg[11]_i_1_n_2 ;
  wire \threshold_pipes[0].remainder_s6_reg[11]_i_1_n_3 ;
  wire \threshold_pipes[0].remainder_s6_reg[15]_i_1_n_0 ;
  wire \threshold_pipes[0].remainder_s6_reg[15]_i_1_n_1 ;
  wire \threshold_pipes[0].remainder_s6_reg[15]_i_1_n_2 ;
  wire \threshold_pipes[0].remainder_s6_reg[15]_i_1_n_3 ;
  wire \threshold_pipes[0].remainder_s6_reg[19]_i_1_n_0 ;
  wire \threshold_pipes[0].remainder_s6_reg[19]_i_1_n_1 ;
  wire \threshold_pipes[0].remainder_s6_reg[19]_i_1_n_2 ;
  wire \threshold_pipes[0].remainder_s6_reg[19]_i_1_n_3 ;
  wire \threshold_pipes[0].remainder_s6_reg[23]_i_1_n_0 ;
  wire \threshold_pipes[0].remainder_s6_reg[23]_i_1_n_1 ;
  wire \threshold_pipes[0].remainder_s6_reg[23]_i_1_n_2 ;
  wire \threshold_pipes[0].remainder_s6_reg[23]_i_1_n_3 ;
  wire \threshold_pipes[0].remainder_s6_reg[27]_i_1_n_0 ;
  wire \threshold_pipes[0].remainder_s6_reg[27]_i_1_n_1 ;
  wire \threshold_pipes[0].remainder_s6_reg[27]_i_1_n_2 ;
  wire \threshold_pipes[0].remainder_s6_reg[27]_i_1_n_3 ;
  wire \threshold_pipes[0].remainder_s6_reg[31]_i_1_n_1 ;
  wire \threshold_pipes[0].remainder_s6_reg[31]_i_1_n_2 ;
  wire \threshold_pipes[0].remainder_s6_reg[31]_i_1_n_3 ;
  wire \threshold_pipes[0].remainder_s6_reg[3]_i_1_n_0 ;
  wire \threshold_pipes[0].remainder_s6_reg[3]_i_1_n_1 ;
  wire \threshold_pipes[0].remainder_s6_reg[3]_i_1_n_2 ;
  wire \threshold_pipes[0].remainder_s6_reg[3]_i_1_n_3 ;
  wire \threshold_pipes[0].remainder_s6_reg[7]_i_1_n_0 ;
  wire \threshold_pipes[0].remainder_s6_reg[7]_i_1_n_1 ;
  wire \threshold_pipes[0].remainder_s6_reg[7]_i_1_n_2 ;
  wire \threshold_pipes[0].remainder_s6_reg[7]_i_1_n_3 ;
  wire \threshold_pipes[0].threshold_live[0]_i_1_n_0 ;
  wire \threshold_pipes[0].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ;
  wire \threshold_pipes[0].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ;
  wire \threshold_pipes[1].check_hi_reg_i_1_n_2 ;
  wire \threshold_pipes[1].check_hi_reg_i_1_n_7 ;
  wire \threshold_pipes[1].check_hi_reg_i_2_n_0 ;
  wire \threshold_pipes[1].check_hi_reg_i_2_n_1 ;
  wire \threshold_pipes[1].check_hi_reg_i_2_n_2 ;
  wire \threshold_pipes[1].check_hi_reg_i_2_n_3 ;
  wire \threshold_pipes[1].check_hi_reg_i_2_n_4 ;
  wire \threshold_pipes[1].check_hi_reg_i_2_n_5 ;
  wire \threshold_pipes[1].check_hi_reg_i_2_n_6 ;
  wire \threshold_pipes[1].check_hi_reg_i_2_n_7 ;
  wire \threshold_pipes[1].check_hi_reg_i_3_n_0 ;
  wire \threshold_pipes[1].check_hi_reg_i_3_n_1 ;
  wire \threshold_pipes[1].check_hi_reg_i_3_n_2 ;
  wire \threshold_pipes[1].check_hi_reg_i_3_n_3 ;
  wire \threshold_pipes[1].check_hi_reg_i_3_n_4 ;
  wire \threshold_pipes[1].check_hi_reg_i_3_n_5 ;
  wire \threshold_pipes[1].check_hi_reg_i_3_n_6 ;
  wire \threshold_pipes[1].check_hi_reg_i_3_n_7 ;
  wire \threshold_pipes[1].check_hi_reg_i_4_n_0 ;
  wire \threshold_pipes[1].check_hi_reg_i_4_n_1 ;
  wire \threshold_pipes[1].check_hi_reg_i_4_n_2 ;
  wire \threshold_pipes[1].check_hi_reg_i_4_n_3 ;
  wire \threshold_pipes[1].check_hi_reg_i_4_n_4 ;
  wire \threshold_pipes[1].check_hi_reg_i_4_n_5 ;
  wire \threshold_pipes[1].check_hi_reg_i_4_n_6 ;
  wire \threshold_pipes[1].check_hi_reg_i_4_n_7 ;
  wire \threshold_pipes[1].check_hi_reg_n_100 ;
  wire \threshold_pipes[1].check_hi_reg_n_101 ;
  wire \threshold_pipes[1].check_hi_reg_n_102 ;
  wire \threshold_pipes[1].check_hi_reg_n_103 ;
  wire \threshold_pipes[1].check_hi_reg_n_104 ;
  wire \threshold_pipes[1].check_hi_reg_n_105 ;
  wire \threshold_pipes[1].check_hi_reg_n_90 ;
  wire \threshold_pipes[1].check_hi_reg_n_91 ;
  wire \threshold_pipes[1].check_hi_reg_n_92 ;
  wire \threshold_pipes[1].check_hi_reg_n_93 ;
  wire \threshold_pipes[1].check_hi_reg_n_94 ;
  wire \threshold_pipes[1].check_hi_reg_n_95 ;
  wire \threshold_pipes[1].check_hi_reg_n_96 ;
  wire \threshold_pipes[1].check_hi_reg_n_97 ;
  wire \threshold_pipes[1].check_hi_reg_n_98 ;
  wire \threshold_pipes[1].check_hi_reg_n_99 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_10_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_11_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_12_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_13_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_2_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_3_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_4_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_5_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_6_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_7_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_8_n_0 ;
  wire \threshold_pipes[1].count_threshold[1][3]_i_9_n_0 ;
  wire \threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_0 ;
  wire \threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_1 ;
  wire \threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_2 ;
  wire \threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_3 ;
  wire \threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_4 ;
  wire \threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_5 ;
  wire \threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_6 ;
  wire \threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_7 ;
  wire \threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_0 ;
  wire \threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_1 ;
  wire \threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_2 ;
  wire \threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_3 ;
  wire \threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_4 ;
  wire \threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_5 ;
  wire \threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_6 ;
  wire \threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_7 ;
  wire \threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_0 ;
  wire \threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_1 ;
  wire \threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_2 ;
  wire \threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_3 ;
  wire \threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_4 ;
  wire \threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_5 ;
  wire \threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_6 ;
  wire \threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_7 ;
  wire \threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_0 ;
  wire \threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_1 ;
  wire \threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_2 ;
  wire \threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_3 ;
  wire \threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_4 ;
  wire \threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_5 ;
  wire \threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_6 ;
  wire \threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_7 ;
  wire \threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_0 ;
  wire \threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_1 ;
  wire \threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_2 ;
  wire \threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_3 ;
  wire \threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_4 ;
  wire \threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_5 ;
  wire \threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_6 ;
  wire \threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_7 ;
  wire \threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_1 ;
  wire \threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_3 ;
  wire \threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_6 ;
  wire \threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_7 ;
  wire \threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_0 ;
  wire \threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_1 ;
  wire \threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_2 ;
  wire \threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_3 ;
  wire \threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_4 ;
  wire \threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_5 ;
  wire \threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_6 ;
  wire \threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_7 ;
  wire \threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_0 ;
  wire \threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_1 ;
  wire \threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_2 ;
  wire \threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_3 ;
  wire \threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_4 ;
  wire \threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_5 ;
  wire \threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_6 ;
  wire \threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_7 ;
  wire [14:0]\threshold_pipes[1].cross_carry_s2 ;
  wire [30:16]\threshold_pipes[1].cross_carry_s21 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_11_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_12_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_13_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_14_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_15_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_16_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_17_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_18_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_4_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_6_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_7_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_8_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2[3]_i_9_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_1 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_2 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_3 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[14]_i_1_n_3 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_1 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_2 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_3 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_1 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_2 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_3 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_1 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_2 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_3 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_1 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_2 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_3 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_1 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_2 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_3 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_0 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_1 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_2 ;
  wire \threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_3 ;
  wire \threshold_pipes[1].cross_s1_reg_n_100 ;
  wire \threshold_pipes[1].cross_s1_reg_n_101 ;
  wire \threshold_pipes[1].cross_s1_reg_n_102 ;
  wire \threshold_pipes[1].cross_s1_reg_n_103 ;
  wire \threshold_pipes[1].cross_s1_reg_n_104 ;
  wire \threshold_pipes[1].cross_s1_reg_n_105 ;
  wire \threshold_pipes[1].cross_s1_reg_n_76 ;
  wire \threshold_pipes[1].cross_s1_reg_n_77 ;
  wire \threshold_pipes[1].cross_s1_reg_n_78 ;
  wire \threshold_pipes[1].cross_s1_reg_n_79 ;
  wire \threshold_pipes[1].cross_s1_reg_n_80 ;
  wire \threshold_pipes[1].cross_s1_reg_n_81 ;
  wire \threshold_pipes[1].cross_s1_reg_n_82 ;
  wire \threshold_pipes[1].cross_s1_reg_n_83 ;
  wire \threshold_pipes[1].cross_s1_reg_n_84 ;
  wire \threshold_pipes[1].cross_s1_reg_n_85 ;
  wire \threshold_pipes[1].cross_s1_reg_n_86 ;
  wire \threshold_pipes[1].cross_s1_reg_n_87 ;
  wire \threshold_pipes[1].cross_s1_reg_n_88 ;
  wire \threshold_pipes[1].cross_s1_reg_n_89 ;
  wire \threshold_pipes[1].cross_s1_reg_n_90 ;
  wire \threshold_pipes[1].cross_s1_reg_n_91 ;
  wire \threshold_pipes[1].cross_s1_reg_n_92 ;
  wire \threshold_pipes[1].cross_s1_reg_n_93 ;
  wire \threshold_pipes[1].cross_s1_reg_n_94 ;
  wire \threshold_pipes[1].cross_s1_reg_n_95 ;
  wire \threshold_pipes[1].cross_s1_reg_n_96 ;
  wire \threshold_pipes[1].cross_s1_reg_n_97 ;
  wire \threshold_pipes[1].cross_s1_reg_n_98 ;
  wire \threshold_pipes[1].cross_s1_reg_n_99 ;
  wire \threshold_pipes[1].high_s1_reg_n_100 ;
  wire \threshold_pipes[1].high_s1_reg_n_101 ;
  wire \threshold_pipes[1].high_s1_reg_n_102 ;
  wire \threshold_pipes[1].high_s1_reg_n_103 ;
  wire \threshold_pipes[1].high_s1_reg_n_104 ;
  wire \threshold_pipes[1].high_s1_reg_n_105 ;
  wire \threshold_pipes[1].high_s1_reg_n_77 ;
  wire \threshold_pipes[1].high_s1_reg_n_78 ;
  wire \threshold_pipes[1].high_s1_reg_n_79 ;
  wire \threshold_pipes[1].high_s1_reg_n_80 ;
  wire \threshold_pipes[1].high_s1_reg_n_81 ;
  wire \threshold_pipes[1].high_s1_reg_n_82 ;
  wire \threshold_pipes[1].high_s1_reg_n_83 ;
  wire \threshold_pipes[1].high_s1_reg_n_84 ;
  wire \threshold_pipes[1].high_s1_reg_n_85 ;
  wire \threshold_pipes[1].high_s1_reg_n_86 ;
  wire \threshold_pipes[1].high_s1_reg_n_87 ;
  wire \threshold_pipes[1].high_s1_reg_n_88 ;
  wire \threshold_pipes[1].high_s1_reg_n_89 ;
  wire \threshold_pipes[1].high_s1_reg_n_90 ;
  wire \threshold_pipes[1].high_s1_reg_n_91 ;
  wire \threshold_pipes[1].high_s1_reg_n_92 ;
  wire \threshold_pipes[1].high_s1_reg_n_93 ;
  wire \threshold_pipes[1].high_s1_reg_n_94 ;
  wire \threshold_pipes[1].high_s1_reg_n_95 ;
  wire \threshold_pipes[1].high_s1_reg_n_96 ;
  wire \threshold_pipes[1].high_s1_reg_n_97 ;
  wire \threshold_pipes[1].high_s1_reg_n_98 ;
  wire \threshold_pipes[1].high_s1_reg_n_99 ;
  wire [28:0]\threshold_pipes[1].high_s2 ;
  wire [12:0]\threshold_pipes[1].low_carry_s1 ;
  wire [12:0]\threshold_pipes[1].mul00_hi ;
  wire [31:0]\threshold_pipes[1].product_s5_reg__0 ;
  wire \threshold_pipes[1].product_s5_reg_i_10_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_11_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_12_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_13_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_14_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_15_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_16_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_17_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_18_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_19_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_1_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_1_n_1 ;
  wire \threshold_pipes[1].product_s5_reg_i_1_n_2 ;
  wire \threshold_pipes[1].product_s5_reg_i_1_n_3 ;
  wire \threshold_pipes[1].product_s5_reg_i_1_n_4 ;
  wire \threshold_pipes[1].product_s5_reg_i_1_n_5 ;
  wire \threshold_pipes[1].product_s5_reg_i_1_n_6 ;
  wire \threshold_pipes[1].product_s5_reg_i_1_n_7 ;
  wire \threshold_pipes[1].product_s5_reg_i_2_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_2_n_1 ;
  wire \threshold_pipes[1].product_s5_reg_i_2_n_2 ;
  wire \threshold_pipes[1].product_s5_reg_i_2_n_3 ;
  wire \threshold_pipes[1].product_s5_reg_i_2_n_4 ;
  wire \threshold_pipes[1].product_s5_reg_i_2_n_5 ;
  wire \threshold_pipes[1].product_s5_reg_i_2_n_6 ;
  wire \threshold_pipes[1].product_s5_reg_i_2_n_7 ;
  wire \threshold_pipes[1].product_s5_reg_i_3_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_3_n_1 ;
  wire \threshold_pipes[1].product_s5_reg_i_3_n_2 ;
  wire \threshold_pipes[1].product_s5_reg_i_3_n_3 ;
  wire \threshold_pipes[1].product_s5_reg_i_3_n_4 ;
  wire \threshold_pipes[1].product_s5_reg_i_3_n_5 ;
  wire \threshold_pipes[1].product_s5_reg_i_3_n_6 ;
  wire \threshold_pipes[1].product_s5_reg_i_3_n_7 ;
  wire \threshold_pipes[1].product_s5_reg_i_4_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_4_n_1 ;
  wire \threshold_pipes[1].product_s5_reg_i_4_n_2 ;
  wire \threshold_pipes[1].product_s5_reg_i_4_n_3 ;
  wire \threshold_pipes[1].product_s5_reg_i_4_n_4 ;
  wire \threshold_pipes[1].product_s5_reg_i_4_n_5 ;
  wire \threshold_pipes[1].product_s5_reg_i_4_n_6 ;
  wire \threshold_pipes[1].product_s5_reg_i_4_n_7 ;
  wire \threshold_pipes[1].product_s5_reg_i_5_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_6_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_7_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_8_n_0 ;
  wire \threshold_pipes[1].product_s5_reg_i_9_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[0]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[10]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[11]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[12]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[13]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[14]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[15]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[16]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[17]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[18]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[19]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[1]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[20]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[21]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[22]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[23]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[24]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[25]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[26]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[27]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[28]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[29]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[2]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[3]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[4]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[5]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[6]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[7]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[8]_srl3_n_0 ;
  wire \threshold_pipes[1].q_s5_reg[9]_srl3_n_0 ;
  wire [29:0]\threshold_pipes[1].q_s6 ;
  wire [31:0]\threshold_pipes[1].remainder_s6 ;
  wire [31:0]\threshold_pipes[1].remainder_s601_out ;
  wire \threshold_pipes[1].remainder_s6[11]_i_2_n_0 ;
  wire \threshold_pipes[1].remainder_s6[11]_i_3_n_0 ;
  wire \threshold_pipes[1].remainder_s6[11]_i_4_n_0 ;
  wire \threshold_pipes[1].remainder_s6[11]_i_5_n_0 ;
  wire \threshold_pipes[1].remainder_s6[15]_i_2_n_0 ;
  wire \threshold_pipes[1].remainder_s6[15]_i_3_n_0 ;
  wire \threshold_pipes[1].remainder_s6[15]_i_4_n_0 ;
  wire \threshold_pipes[1].remainder_s6[15]_i_5_n_0 ;
  wire \threshold_pipes[1].remainder_s6[19]_i_2_n_0 ;
  wire \threshold_pipes[1].remainder_s6[19]_i_3_n_0 ;
  wire \threshold_pipes[1].remainder_s6[19]_i_4_n_0 ;
  wire \threshold_pipes[1].remainder_s6[19]_i_5_n_0 ;
  wire \threshold_pipes[1].remainder_s6[23]_i_2_n_0 ;
  wire \threshold_pipes[1].remainder_s6[23]_i_3_n_0 ;
  wire \threshold_pipes[1].remainder_s6[23]_i_4_n_0 ;
  wire \threshold_pipes[1].remainder_s6[23]_i_5_n_0 ;
  wire \threshold_pipes[1].remainder_s6[27]_i_2_n_0 ;
  wire \threshold_pipes[1].remainder_s6[27]_i_3_n_0 ;
  wire \threshold_pipes[1].remainder_s6[27]_i_4_n_0 ;
  wire \threshold_pipes[1].remainder_s6[27]_i_5_n_0 ;
  wire \threshold_pipes[1].remainder_s6[31]_i_2_n_0 ;
  wire \threshold_pipes[1].remainder_s6[31]_i_3_n_0 ;
  wire \threshold_pipes[1].remainder_s6[31]_i_4_n_0 ;
  wire \threshold_pipes[1].remainder_s6[31]_i_5_n_0 ;
  wire \threshold_pipes[1].remainder_s6[3]_i_2_n_0 ;
  wire \threshold_pipes[1].remainder_s6[3]_i_3_n_0 ;
  wire \threshold_pipes[1].remainder_s6[3]_i_4_n_0 ;
  wire \threshold_pipes[1].remainder_s6[3]_i_5_n_0 ;
  wire \threshold_pipes[1].remainder_s6[7]_i_2_n_0 ;
  wire \threshold_pipes[1].remainder_s6[7]_i_3_n_0 ;
  wire \threshold_pipes[1].remainder_s6[7]_i_4_n_0 ;
  wire \threshold_pipes[1].remainder_s6[7]_i_5_n_0 ;
  wire \threshold_pipes[1].remainder_s6_reg[11]_i_1_n_0 ;
  wire \threshold_pipes[1].remainder_s6_reg[11]_i_1_n_1 ;
  wire \threshold_pipes[1].remainder_s6_reg[11]_i_1_n_2 ;
  wire \threshold_pipes[1].remainder_s6_reg[11]_i_1_n_3 ;
  wire \threshold_pipes[1].remainder_s6_reg[15]_i_1_n_0 ;
  wire \threshold_pipes[1].remainder_s6_reg[15]_i_1_n_1 ;
  wire \threshold_pipes[1].remainder_s6_reg[15]_i_1_n_2 ;
  wire \threshold_pipes[1].remainder_s6_reg[15]_i_1_n_3 ;
  wire \threshold_pipes[1].remainder_s6_reg[19]_i_1_n_0 ;
  wire \threshold_pipes[1].remainder_s6_reg[19]_i_1_n_1 ;
  wire \threshold_pipes[1].remainder_s6_reg[19]_i_1_n_2 ;
  wire \threshold_pipes[1].remainder_s6_reg[19]_i_1_n_3 ;
  wire \threshold_pipes[1].remainder_s6_reg[23]_i_1_n_0 ;
  wire \threshold_pipes[1].remainder_s6_reg[23]_i_1_n_1 ;
  wire \threshold_pipes[1].remainder_s6_reg[23]_i_1_n_2 ;
  wire \threshold_pipes[1].remainder_s6_reg[23]_i_1_n_3 ;
  wire \threshold_pipes[1].remainder_s6_reg[27]_i_1_n_0 ;
  wire \threshold_pipes[1].remainder_s6_reg[27]_i_1_n_1 ;
  wire \threshold_pipes[1].remainder_s6_reg[27]_i_1_n_2 ;
  wire \threshold_pipes[1].remainder_s6_reg[27]_i_1_n_3 ;
  wire \threshold_pipes[1].remainder_s6_reg[31]_i_1_n_1 ;
  wire \threshold_pipes[1].remainder_s6_reg[31]_i_1_n_2 ;
  wire \threshold_pipes[1].remainder_s6_reg[31]_i_1_n_3 ;
  wire \threshold_pipes[1].remainder_s6_reg[3]_i_1_n_0 ;
  wire \threshold_pipes[1].remainder_s6_reg[3]_i_1_n_1 ;
  wire \threshold_pipes[1].remainder_s6_reg[3]_i_1_n_2 ;
  wire \threshold_pipes[1].remainder_s6_reg[3]_i_1_n_3 ;
  wire \threshold_pipes[1].remainder_s6_reg[7]_i_1_n_0 ;
  wire \threshold_pipes[1].remainder_s6_reg[7]_i_1_n_1 ;
  wire \threshold_pipes[1].remainder_s6_reg[7]_i_1_n_2 ;
  wire \threshold_pipes[1].remainder_s6_reg[7]_i_1_n_3 ;
  wire \threshold_pipes[1].threshold_live[1]_i_1_n_0 ;
  wire [7:7]\threshold_pipes[1].valid_pipe__0 ;
  wire \threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1_n_0 ;
  wire \threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ;
  wire \threshold_pipes[1].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ;
  wire \threshold_pipes[2].check_hi_reg_n_100 ;
  wire \threshold_pipes[2].check_hi_reg_n_101 ;
  wire \threshold_pipes[2].check_hi_reg_n_102 ;
  wire \threshold_pipes[2].check_hi_reg_n_103 ;
  wire \threshold_pipes[2].check_hi_reg_n_104 ;
  wire \threshold_pipes[2].check_hi_reg_n_105 ;
  wire \threshold_pipes[2].check_hi_reg_n_90 ;
  wire \threshold_pipes[2].check_hi_reg_n_91 ;
  wire \threshold_pipes[2].check_hi_reg_n_92 ;
  wire \threshold_pipes[2].check_hi_reg_n_93 ;
  wire \threshold_pipes[2].check_hi_reg_n_94 ;
  wire \threshold_pipes[2].check_hi_reg_n_95 ;
  wire \threshold_pipes[2].check_hi_reg_n_96 ;
  wire \threshold_pipes[2].check_hi_reg_n_97 ;
  wire \threshold_pipes[2].check_hi_reg_n_98 ;
  wire \threshold_pipes[2].check_hi_reg_n_99 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_10_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_11_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_12_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_13_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_2_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_3_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_4_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_5_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_6_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_7_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_8_n_0 ;
  wire \threshold_pipes[2].count_threshold[2][3]_i_9_n_0 ;
  wire \threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_0 ;
  wire \threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_1 ;
  wire \threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_2 ;
  wire \threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_3 ;
  wire \threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_4 ;
  wire \threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_5 ;
  wire \threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_6 ;
  wire \threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_7 ;
  wire \threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_0 ;
  wire \threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_1 ;
  wire \threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_2 ;
  wire \threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_3 ;
  wire \threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_4 ;
  wire \threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_5 ;
  wire \threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_6 ;
  wire \threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_7 ;
  wire \threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_0 ;
  wire \threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_1 ;
  wire \threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_2 ;
  wire \threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_3 ;
  wire \threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_4 ;
  wire \threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_5 ;
  wire \threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_6 ;
  wire \threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_7 ;
  wire \threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_0 ;
  wire \threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_1 ;
  wire \threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_2 ;
  wire \threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_3 ;
  wire \threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_4 ;
  wire \threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_5 ;
  wire \threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_6 ;
  wire \threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_7 ;
  wire \threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_0 ;
  wire \threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_1 ;
  wire \threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_2 ;
  wire \threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_3 ;
  wire \threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_4 ;
  wire \threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_5 ;
  wire \threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_6 ;
  wire \threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_7 ;
  wire \threshold_pipes[2].count_threshold_reg[2][28]_i_1_n_3 ;
  wire \threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_0 ;
  wire \threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_1 ;
  wire \threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_2 ;
  wire \threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_3 ;
  wire \threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_4 ;
  wire \threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_5 ;
  wire \threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_6 ;
  wire \threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_7 ;
  wire \threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_0 ;
  wire \threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_1 ;
  wire \threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_2 ;
  wire \threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_3 ;
  wire \threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_4 ;
  wire \threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_5 ;
  wire \threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_6 ;
  wire \threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_7 ;
  wire [30:16]\threshold_pipes[2].cross_carry_s21 ;
  wire \threshold_pipes[2].cross_s1_reg_n_100 ;
  wire \threshold_pipes[2].cross_s1_reg_n_101 ;
  wire \threshold_pipes[2].cross_s1_reg_n_102 ;
  wire \threshold_pipes[2].cross_s1_reg_n_103 ;
  wire \threshold_pipes[2].cross_s1_reg_n_104 ;
  wire \threshold_pipes[2].cross_s1_reg_n_105 ;
  wire \threshold_pipes[2].cross_s1_reg_n_76 ;
  wire \threshold_pipes[2].cross_s1_reg_n_77 ;
  wire \threshold_pipes[2].cross_s1_reg_n_78 ;
  wire \threshold_pipes[2].cross_s1_reg_n_79 ;
  wire \threshold_pipes[2].cross_s1_reg_n_80 ;
  wire \threshold_pipes[2].cross_s1_reg_n_81 ;
  wire \threshold_pipes[2].cross_s1_reg_n_82 ;
  wire \threshold_pipes[2].cross_s1_reg_n_83 ;
  wire \threshold_pipes[2].cross_s1_reg_n_84 ;
  wire \threshold_pipes[2].cross_s1_reg_n_85 ;
  wire \threshold_pipes[2].cross_s1_reg_n_86 ;
  wire \threshold_pipes[2].cross_s1_reg_n_87 ;
  wire \threshold_pipes[2].cross_s1_reg_n_88 ;
  wire \threshold_pipes[2].cross_s1_reg_n_89 ;
  wire \threshold_pipes[2].cross_s1_reg_n_90 ;
  wire \threshold_pipes[2].cross_s1_reg_n_91 ;
  wire \threshold_pipes[2].cross_s1_reg_n_92 ;
  wire \threshold_pipes[2].cross_s1_reg_n_93 ;
  wire \threshold_pipes[2].cross_s1_reg_n_94 ;
  wire \threshold_pipes[2].cross_s1_reg_n_95 ;
  wire \threshold_pipes[2].cross_s1_reg_n_96 ;
  wire \threshold_pipes[2].cross_s1_reg_n_97 ;
  wire \threshold_pipes[2].cross_s1_reg_n_98 ;
  wire \threshold_pipes[2].cross_s1_reg_n_99 ;
  wire [12:0]\threshold_pipes[2].low_carry_s1 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_100 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_101 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_102 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_103 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_104 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_105 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_90 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_91 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_92 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_93 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_94 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_95 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_96 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_97 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_98 ;
  wire \threshold_pipes[2].mul00_hi_reg_n_99 ;
  wire \threshold_pipes[2].mul01_reg_n_100 ;
  wire \threshold_pipes[2].mul01_reg_n_101 ;
  wire \threshold_pipes[2].mul01_reg_n_102 ;
  wire \threshold_pipes[2].mul01_reg_n_103 ;
  wire \threshold_pipes[2].mul01_reg_n_104 ;
  wire \threshold_pipes[2].mul01_reg_n_105 ;
  wire \threshold_pipes[2].mul01_reg_n_106 ;
  wire \threshold_pipes[2].mul01_reg_n_107 ;
  wire \threshold_pipes[2].mul01_reg_n_108 ;
  wire \threshold_pipes[2].mul01_reg_n_109 ;
  wire \threshold_pipes[2].mul01_reg_n_110 ;
  wire \threshold_pipes[2].mul01_reg_n_111 ;
  wire \threshold_pipes[2].mul01_reg_n_112 ;
  wire \threshold_pipes[2].mul01_reg_n_113 ;
  wire \threshold_pipes[2].mul01_reg_n_114 ;
  wire \threshold_pipes[2].mul01_reg_n_115 ;
  wire \threshold_pipes[2].mul01_reg_n_116 ;
  wire \threshold_pipes[2].mul01_reg_n_117 ;
  wire \threshold_pipes[2].mul01_reg_n_118 ;
  wire \threshold_pipes[2].mul01_reg_n_119 ;
  wire \threshold_pipes[2].mul01_reg_n_120 ;
  wire \threshold_pipes[2].mul01_reg_n_121 ;
  wire \threshold_pipes[2].mul01_reg_n_122 ;
  wire \threshold_pipes[2].mul01_reg_n_123 ;
  wire \threshold_pipes[2].mul01_reg_n_124 ;
  wire \threshold_pipes[2].mul01_reg_n_125 ;
  wire \threshold_pipes[2].mul01_reg_n_126 ;
  wire \threshold_pipes[2].mul01_reg_n_127 ;
  wire \threshold_pipes[2].mul01_reg_n_128 ;
  wire \threshold_pipes[2].mul01_reg_n_129 ;
  wire \threshold_pipes[2].mul01_reg_n_130 ;
  wire \threshold_pipes[2].mul01_reg_n_131 ;
  wire \threshold_pipes[2].mul01_reg_n_132 ;
  wire \threshold_pipes[2].mul01_reg_n_133 ;
  wire \threshold_pipes[2].mul01_reg_n_134 ;
  wire \threshold_pipes[2].mul01_reg_n_135 ;
  wire \threshold_pipes[2].mul01_reg_n_136 ;
  wire \threshold_pipes[2].mul01_reg_n_137 ;
  wire \threshold_pipes[2].mul01_reg_n_138 ;
  wire \threshold_pipes[2].mul01_reg_n_139 ;
  wire \threshold_pipes[2].mul01_reg_n_140 ;
  wire \threshold_pipes[2].mul01_reg_n_141 ;
  wire \threshold_pipes[2].mul01_reg_n_142 ;
  wire \threshold_pipes[2].mul01_reg_n_143 ;
  wire \threshold_pipes[2].mul01_reg_n_144 ;
  wire \threshold_pipes[2].mul01_reg_n_145 ;
  wire \threshold_pipes[2].mul01_reg_n_146 ;
  wire \threshold_pipes[2].mul01_reg_n_147 ;
  wire \threshold_pipes[2].mul01_reg_n_148 ;
  wire \threshold_pipes[2].mul01_reg_n_149 ;
  wire \threshold_pipes[2].mul01_reg_n_150 ;
  wire \threshold_pipes[2].mul01_reg_n_151 ;
  wire \threshold_pipes[2].mul01_reg_n_152 ;
  wire \threshold_pipes[2].mul01_reg_n_153 ;
  wire \threshold_pipes[2].mul01_reg_n_79 ;
  wire \threshold_pipes[2].mul01_reg_n_80 ;
  wire \threshold_pipes[2].mul01_reg_n_81 ;
  wire \threshold_pipes[2].mul01_reg_n_82 ;
  wire \threshold_pipes[2].mul01_reg_n_83 ;
  wire \threshold_pipes[2].mul01_reg_n_84 ;
  wire \threshold_pipes[2].mul01_reg_n_85 ;
  wire \threshold_pipes[2].mul01_reg_n_86 ;
  wire \threshold_pipes[2].mul01_reg_n_87 ;
  wire \threshold_pipes[2].mul01_reg_n_88 ;
  wire \threshold_pipes[2].mul01_reg_n_89 ;
  wire \threshold_pipes[2].mul01_reg_n_90 ;
  wire \threshold_pipes[2].mul01_reg_n_91 ;
  wire \threshold_pipes[2].mul01_reg_n_92 ;
  wire \threshold_pipes[2].mul01_reg_n_93 ;
  wire \threshold_pipes[2].mul01_reg_n_94 ;
  wire \threshold_pipes[2].mul01_reg_n_95 ;
  wire \threshold_pipes[2].mul01_reg_n_96 ;
  wire \threshold_pipes[2].mul01_reg_n_97 ;
  wire \threshold_pipes[2].mul01_reg_n_98 ;
  wire \threshold_pipes[2].mul01_reg_n_99 ;
  wire [31:0]\threshold_pipes[2].product_s5_reg__0 ;
  wire \threshold_pipes[2].q_s3_reg_i_10_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_11_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_12_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_13_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_13_n_1 ;
  wire \threshold_pipes[2].q_s3_reg_i_13_n_2 ;
  wire \threshold_pipes[2].q_s3_reg_i_13_n_3 ;
  wire \threshold_pipes[2].q_s3_reg_i_14_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_15_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_16_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_17_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_18_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_19_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_1_n_3 ;
  wire \threshold_pipes[2].q_s3_reg_i_20_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_21_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_2_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_2_n_1 ;
  wire \threshold_pipes[2].q_s3_reg_i_2_n_2 ;
  wire \threshold_pipes[2].q_s3_reg_i_2_n_3 ;
  wire \threshold_pipes[2].q_s3_reg_i_3_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_3_n_1 ;
  wire \threshold_pipes[2].q_s3_reg_i_3_n_2 ;
  wire \threshold_pipes[2].q_s3_reg_i_3_n_3 ;
  wire \threshold_pipes[2].q_s3_reg_i_4_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_4_n_1 ;
  wire \threshold_pipes[2].q_s3_reg_i_4_n_2 ;
  wire \threshold_pipes[2].q_s3_reg_i_4_n_3 ;
  wire \threshold_pipes[2].q_s3_reg_i_5_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_5_n_1 ;
  wire \threshold_pipes[2].q_s3_reg_i_5_n_2 ;
  wire \threshold_pipes[2].q_s3_reg_i_5_n_3 ;
  wire \threshold_pipes[2].q_s3_reg_i_6_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_6_n_1 ;
  wire \threshold_pipes[2].q_s3_reg_i_6_n_2 ;
  wire \threshold_pipes[2].q_s3_reg_i_6_n_3 ;
  wire \threshold_pipes[2].q_s3_reg_i_7_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_8_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_i_8_n_1 ;
  wire \threshold_pipes[2].q_s3_reg_i_8_n_2 ;
  wire \threshold_pipes[2].q_s3_reg_i_8_n_3 ;
  wire \threshold_pipes[2].q_s3_reg_i_9_n_0 ;
  wire \threshold_pipes[2].q_s3_reg_n_100 ;
  wire \threshold_pipes[2].q_s3_reg_n_101 ;
  wire \threshold_pipes[2].q_s3_reg_n_102 ;
  wire \threshold_pipes[2].q_s3_reg_n_103 ;
  wire \threshold_pipes[2].q_s3_reg_n_104 ;
  wire \threshold_pipes[2].q_s3_reg_n_105 ;
  wire \threshold_pipes[2].q_s3_reg_n_78 ;
  wire \threshold_pipes[2].q_s3_reg_n_79 ;
  wire \threshold_pipes[2].q_s3_reg_n_80 ;
  wire \threshold_pipes[2].q_s3_reg_n_81 ;
  wire \threshold_pipes[2].q_s3_reg_n_82 ;
  wire \threshold_pipes[2].q_s3_reg_n_83 ;
  wire \threshold_pipes[2].q_s3_reg_n_84 ;
  wire \threshold_pipes[2].q_s3_reg_n_85 ;
  wire \threshold_pipes[2].q_s3_reg_n_86 ;
  wire \threshold_pipes[2].q_s3_reg_n_87 ;
  wire \threshold_pipes[2].q_s3_reg_n_88 ;
  wire \threshold_pipes[2].q_s3_reg_n_89 ;
  wire \threshold_pipes[2].q_s3_reg_n_90 ;
  wire \threshold_pipes[2].q_s3_reg_n_91 ;
  wire \threshold_pipes[2].q_s3_reg_n_92 ;
  wire \threshold_pipes[2].q_s3_reg_n_93 ;
  wire \threshold_pipes[2].q_s3_reg_n_94 ;
  wire \threshold_pipes[2].q_s3_reg_n_95 ;
  wire \threshold_pipes[2].q_s3_reg_n_96 ;
  wire \threshold_pipes[2].q_s3_reg_n_97 ;
  wire \threshold_pipes[2].q_s3_reg_n_98 ;
  wire \threshold_pipes[2].q_s3_reg_n_99 ;
  wire \threshold_pipes[2].q_s5_reg[0]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[10]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[11]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[12]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[13]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[14]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[15]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[16]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[17]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[18]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[19]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[1]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[20]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[21]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[22]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[23]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[24]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[25]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[26]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[27]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[2]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[3]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[4]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[5]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[6]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[7]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[8]_srl2_n_0 ;
  wire \threshold_pipes[2].q_s5_reg[9]_srl2_n_0 ;
  wire [27:0]\threshold_pipes[2].q_s6 ;
  wire [31:0]\threshold_pipes[2].remainder_s6 ;
  wire [31:0]\threshold_pipes[2].remainder_s600_out ;
  wire \threshold_pipes[2].remainder_s6[11]_i_2_n_0 ;
  wire \threshold_pipes[2].remainder_s6[11]_i_3_n_0 ;
  wire \threshold_pipes[2].remainder_s6[11]_i_4_n_0 ;
  wire \threshold_pipes[2].remainder_s6[11]_i_5_n_0 ;
  wire \threshold_pipes[2].remainder_s6[15]_i_2_n_0 ;
  wire \threshold_pipes[2].remainder_s6[15]_i_3_n_0 ;
  wire \threshold_pipes[2].remainder_s6[15]_i_4_n_0 ;
  wire \threshold_pipes[2].remainder_s6[15]_i_5_n_0 ;
  wire \threshold_pipes[2].remainder_s6[19]_i_2_n_0 ;
  wire \threshold_pipes[2].remainder_s6[19]_i_3_n_0 ;
  wire \threshold_pipes[2].remainder_s6[19]_i_4_n_0 ;
  wire \threshold_pipes[2].remainder_s6[19]_i_5_n_0 ;
  wire \threshold_pipes[2].remainder_s6[23]_i_2_n_0 ;
  wire \threshold_pipes[2].remainder_s6[23]_i_3_n_0 ;
  wire \threshold_pipes[2].remainder_s6[23]_i_4_n_0 ;
  wire \threshold_pipes[2].remainder_s6[23]_i_5_n_0 ;
  wire \threshold_pipes[2].remainder_s6[27]_i_2_n_0 ;
  wire \threshold_pipes[2].remainder_s6[27]_i_3_n_0 ;
  wire \threshold_pipes[2].remainder_s6[27]_i_4_n_0 ;
  wire \threshold_pipes[2].remainder_s6[27]_i_5_n_0 ;
  wire \threshold_pipes[2].remainder_s6[31]_i_2_n_0 ;
  wire \threshold_pipes[2].remainder_s6[31]_i_3_n_0 ;
  wire \threshold_pipes[2].remainder_s6[31]_i_4_n_0 ;
  wire \threshold_pipes[2].remainder_s6[31]_i_5_n_0 ;
  wire \threshold_pipes[2].remainder_s6[3]_i_2_n_0 ;
  wire \threshold_pipes[2].remainder_s6[3]_i_3_n_0 ;
  wire \threshold_pipes[2].remainder_s6[3]_i_4_n_0 ;
  wire \threshold_pipes[2].remainder_s6[3]_i_5_n_0 ;
  wire \threshold_pipes[2].remainder_s6[7]_i_2_n_0 ;
  wire \threshold_pipes[2].remainder_s6[7]_i_3_n_0 ;
  wire \threshold_pipes[2].remainder_s6[7]_i_4_n_0 ;
  wire \threshold_pipes[2].remainder_s6[7]_i_5_n_0 ;
  wire \threshold_pipes[2].remainder_s6_reg[11]_i_1_n_0 ;
  wire \threshold_pipes[2].remainder_s6_reg[11]_i_1_n_1 ;
  wire \threshold_pipes[2].remainder_s6_reg[11]_i_1_n_2 ;
  wire \threshold_pipes[2].remainder_s6_reg[11]_i_1_n_3 ;
  wire \threshold_pipes[2].remainder_s6_reg[15]_i_1_n_0 ;
  wire \threshold_pipes[2].remainder_s6_reg[15]_i_1_n_1 ;
  wire \threshold_pipes[2].remainder_s6_reg[15]_i_1_n_2 ;
  wire \threshold_pipes[2].remainder_s6_reg[15]_i_1_n_3 ;
  wire \threshold_pipes[2].remainder_s6_reg[19]_i_1_n_0 ;
  wire \threshold_pipes[2].remainder_s6_reg[19]_i_1_n_1 ;
  wire \threshold_pipes[2].remainder_s6_reg[19]_i_1_n_2 ;
  wire \threshold_pipes[2].remainder_s6_reg[19]_i_1_n_3 ;
  wire \threshold_pipes[2].remainder_s6_reg[23]_i_1_n_0 ;
  wire \threshold_pipes[2].remainder_s6_reg[23]_i_1_n_1 ;
  wire \threshold_pipes[2].remainder_s6_reg[23]_i_1_n_2 ;
  wire \threshold_pipes[2].remainder_s6_reg[23]_i_1_n_3 ;
  wire \threshold_pipes[2].remainder_s6_reg[27]_i_1_n_0 ;
  wire \threshold_pipes[2].remainder_s6_reg[27]_i_1_n_1 ;
  wire \threshold_pipes[2].remainder_s6_reg[27]_i_1_n_2 ;
  wire \threshold_pipes[2].remainder_s6_reg[27]_i_1_n_3 ;
  wire \threshold_pipes[2].remainder_s6_reg[31]_i_1_n_1 ;
  wire \threshold_pipes[2].remainder_s6_reg[31]_i_1_n_2 ;
  wire \threshold_pipes[2].remainder_s6_reg[31]_i_1_n_3 ;
  wire \threshold_pipes[2].remainder_s6_reg[3]_i_1_n_0 ;
  wire \threshold_pipes[2].remainder_s6_reg[3]_i_1_n_1 ;
  wire \threshold_pipes[2].remainder_s6_reg[3]_i_1_n_2 ;
  wire \threshold_pipes[2].remainder_s6_reg[3]_i_1_n_3 ;
  wire \threshold_pipes[2].remainder_s6_reg[7]_i_1_n_0 ;
  wire \threshold_pipes[2].remainder_s6_reg[7]_i_1_n_1 ;
  wire \threshold_pipes[2].remainder_s6_reg[7]_i_1_n_2 ;
  wire \threshold_pipes[2].remainder_s6_reg[7]_i_1_n_3 ;
  wire \threshold_pipes[2].threshold_live[2]_i_1_n_0 ;
  wire [7:7]\threshold_pipes[2].valid_pipe__0 ;
  wire \threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1_n_0 ;
  wire \threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ;
  wire \threshold_pipes[2].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ;
  wire threshold_pipes_gate__0_n_0;
  wire threshold_pipes_gate__1_n_0;
  wire threshold_pipes_gate_n_0;
  wire threshold_pipes_r_0_n_0;
  wire threshold_pipes_r_1_n_0;
  wire threshold_pipes_r_2_n_0;
  wire threshold_pipes_r_3_n_0;
  wire threshold_pipes_r_4_n_0;
  wire threshold_pipes_r_5_n_0;
  wire threshold_pipes_r_n_0;
  wire [3:0]\NLW_bad[0]_INST_0_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[0]_INST_0_i_1_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[0]_INST_0_i_10_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[0]_INST_0_i_19_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[1]_INST_0_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[1]_INST_0_i_1_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[1]_INST_0_i_18_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[1]_INST_0_i_9_O_UNCONNECTED ;
  wire [3:3]\NLW_bad[2]_INST_0_CO_UNCONNECTED ;
  wire [3:0]\NLW_bad[2]_INST_0_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[2]_INST_0_i_1_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[2]_INST_0_i_16_O_UNCONNECTED ;
  wire [3:0]\NLW_bad[2]_INST_0_i_7_O_UNCONNECTED ;
  wire NLW_partial_product1_return_CARRYCASCOUT_UNCONNECTED;
  wire NLW_partial_product1_return_MULTSIGNOUT_UNCONNECTED;
  wire NLW_partial_product1_return_OVERFLOW_UNCONNECTED;
  wire NLW_partial_product1_return_PATTERNBDETECT_UNCONNECTED;
  wire NLW_partial_product1_return_PATTERNDETECT_UNCONNECTED;
  wire NLW_partial_product1_return_UNDERFLOW_UNCONNECTED;
  wire [29:0]NLW_partial_product1_return_ACOUT_UNCONNECTED;
  wire [17:0]NLW_partial_product1_return_BCOUT_UNCONNECTED;
  wire [3:0]NLW_partial_product1_return_CARRYOUT_UNCONNECTED;
  wire [47:29]NLW_partial_product1_return_P_UNCONNECTED;
  wire [47:0]NLW_partial_product1_return_PCOUT_UNCONNECTED;
  wire NLW_partial_product_return_CARRYCASCOUT_UNCONNECTED;
  wire NLW_partial_product_return_MULTSIGNOUT_UNCONNECTED;
  wire NLW_partial_product_return_OVERFLOW_UNCONNECTED;
  wire NLW_partial_product_return_PATTERNBDETECT_UNCONNECTED;
  wire NLW_partial_product_return_PATTERNDETECT_UNCONNECTED;
  wire NLW_partial_product_return_UNDERFLOW_UNCONNECTED;
  wire [29:0]NLW_partial_product_return_ACOUT_UNCONNECTED;
  wire [17:0]NLW_partial_product_return_BCOUT_UNCONNECTED;
  wire [3:0]NLW_partial_product_return_CARRYOUT_UNCONNECTED;
  wire [47:30]NLW_partial_product_return_P_UNCONNECTED;
  wire [47:0]NLW_partial_product_return_PCOUT_UNCONNECTED;
  wire [3:0]NLW_selected_bad_INST_0_i_1_O_UNCONNECTED;
  wire [3:0]NLW_selected_bad_INST_0_i_11_O_UNCONNECTED;
  wire [3:0]NLW_selected_bad_INST_0_i_2_O_UNCONNECTED;
  wire [3:0]NLW_selected_bad_INST_0_i_20_O_UNCONNECTED;
  wire \NLW_threshold_pipes[0].check_hi_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].check_hi_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].check_hi_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].check_hi_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].check_hi_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].check_hi_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[0].check_hi_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[0].check_hi_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[0].check_hi_reg_CARRYOUT_UNCONNECTED ;
  wire [47:16]\NLW_threshold_pipes[0].check_hi_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[0].check_hi_reg_PCOUT_UNCONNECTED ;
  wire [3:1]\NLW_threshold_pipes[0].check_hi_reg_i_1_CO_UNCONNECTED ;
  wire [3:2]\NLW_threshold_pipes[0].check_hi_reg_i_1_O_UNCONNECTED ;
  wire [2:2]\NLW_threshold_pipes[0].count_threshold_reg[0][31]_i_1_CO_UNCONNECTED ;
  wire [3:3]\NLW_threshold_pipes[0].count_threshold_reg[0][31]_i_1_O_UNCONNECTED ;
  wire [2:2]\NLW_threshold_pipes[0].cross_carry_s2_reg[15]_i_1_CO_UNCONNECTED ;
  wire [3:3]\NLW_threshold_pipes[0].cross_carry_s2_reg[15]_i_1_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[0].cross_carry_s2_reg[3]_i_11_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[0].cross_carry_s2_reg[3]_i_2_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[0].cross_carry_s2_reg[3]_i_3_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[0].cross_carry_s2_reg[3]_i_6_O_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].cross_s1_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].cross_s1_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].cross_s1_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].cross_s1_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].cross_s1_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].cross_s1_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[0].cross_s1_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[0].cross_s1_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[0].cross_s1_reg_CARRYOUT_UNCONNECTED ;
  wire [47:31]\NLW_threshold_pipes[0].cross_s1_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[0].cross_s1_reg_PCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].high_s1_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].high_s1_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].high_s1_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].high_s1_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].high_s1_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].high_s1_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[0].high_s1_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[0].high_s1_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[0].high_s1_reg_CARRYOUT_UNCONNECTED ;
  wire [47:30]\NLW_threshold_pipes[0].high_s1_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[0].high_s1_reg_PCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].product_s5_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].product_s5_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].product_s5_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].product_s5_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].product_s5_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[0].product_s5_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[0].product_s5_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[0].product_s5_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[0].product_s5_reg_CARRYOUT_UNCONNECTED ;
  wire [47:32]\NLW_threshold_pipes[0].product_s5_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[0].product_s5_reg_PCOUT_UNCONNECTED ;
  wire [3:3]\NLW_threshold_pipes[0].remainder_s6_reg[31]_i_1_CO_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].check_hi_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].check_hi_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].check_hi_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].check_hi_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].check_hi_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].check_hi_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[1].check_hi_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[1].check_hi_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].check_hi_reg_CARRYOUT_UNCONNECTED ;
  wire [47:16]\NLW_threshold_pipes[1].check_hi_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[1].check_hi_reg_PCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].check_hi_reg_i_1_CO_UNCONNECTED ;
  wire [3:1]\NLW_threshold_pipes[1].check_hi_reg_i_1_O_UNCONNECTED ;
  wire [3:1]\NLW_threshold_pipes[1].count_threshold_reg[1][30]_i_1_CO_UNCONNECTED ;
  wire [3:2]\NLW_threshold_pipes[1].count_threshold_reg[1][30]_i_1_O_UNCONNECTED ;
  wire [3:1]\NLW_threshold_pipes[1].cross_carry_s2_reg[14]_i_1_CO_UNCONNECTED ;
  wire [3:2]\NLW_threshold_pipes[1].cross_carry_s2_reg[14]_i_1_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].cross_carry_s2_reg[3]_i_10_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].cross_carry_s2_reg[3]_i_2_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].cross_carry_s2_reg[3]_i_3_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].cross_carry_s2_reg[3]_i_5_O_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].cross_s1_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].cross_s1_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].cross_s1_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].cross_s1_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].cross_s1_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].cross_s1_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[1].cross_s1_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[1].cross_s1_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].cross_s1_reg_CARRYOUT_UNCONNECTED ;
  wire [47:30]\NLW_threshold_pipes[1].cross_s1_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[1].cross_s1_reg_PCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].high_s1_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].high_s1_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].high_s1_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].high_s1_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].high_s1_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].high_s1_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[1].high_s1_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[1].high_s1_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].high_s1_reg_CARRYOUT_UNCONNECTED ;
  wire [47:29]\NLW_threshold_pipes[1].high_s1_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[1].high_s1_reg_PCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].product_s5_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].product_s5_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].product_s5_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].product_s5_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].product_s5_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[1].product_s5_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[1].product_s5_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[1].product_s5_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[1].product_s5_reg_CARRYOUT_UNCONNECTED ;
  wire [47:32]\NLW_threshold_pipes[1].product_s5_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[1].product_s5_reg_PCOUT_UNCONNECTED ;
  wire [3:3]\NLW_threshold_pipes[1].remainder_s6_reg[31]_i_1_CO_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].check_hi_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].check_hi_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].check_hi_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].check_hi_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].check_hi_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].check_hi_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[2].check_hi_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[2].check_hi_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].check_hi_reg_CARRYOUT_UNCONNECTED ;
  wire [47:16]\NLW_threshold_pipes[2].check_hi_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[2].check_hi_reg_PCOUT_UNCONNECTED ;
  wire [3:1]\NLW_threshold_pipes[2].count_threshold_reg[2][28]_i_1_CO_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].count_threshold_reg[2][28]_i_1_O_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].cross_s1_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].cross_s1_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].cross_s1_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].cross_s1_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].cross_s1_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].cross_s1_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[2].cross_s1_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[2].cross_s1_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].cross_s1_reg_CARRYOUT_UNCONNECTED ;
  wire [47:30]\NLW_threshold_pipes[2].cross_s1_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[2].cross_s1_reg_PCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul00_hi_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul00_hi_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul00_hi_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul00_hi_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul00_hi_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul00_hi_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[2].mul00_hi_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[2].mul00_hi_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].mul00_hi_reg_CARRYOUT_UNCONNECTED ;
  wire [47:29]\NLW_threshold_pipes[2].mul00_hi_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[2].mul00_hi_reg_PCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul01_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul01_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul01_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul01_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul01_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].mul01_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[2].mul01_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[2].mul01_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].mul01_reg_CARRYOUT_UNCONNECTED ;
  wire [47:27]\NLW_threshold_pipes[2].mul01_reg_P_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].product_s5_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].product_s5_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].product_s5_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].product_s5_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].product_s5_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].product_s5_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[2].product_s5_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[2].product_s5_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].product_s5_reg_CARRYOUT_UNCONNECTED ;
  wire [47:32]\NLW_threshold_pipes[2].product_s5_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[2].product_s5_reg_PCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].q_s3_reg_CARRYCASCOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].q_s3_reg_MULTSIGNOUT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].q_s3_reg_OVERFLOW_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].q_s3_reg_PATTERNBDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].q_s3_reg_PATTERNDETECT_UNCONNECTED ;
  wire \NLW_threshold_pipes[2].q_s3_reg_UNDERFLOW_UNCONNECTED ;
  wire [29:0]\NLW_threshold_pipes[2].q_s3_reg_ACOUT_UNCONNECTED ;
  wire [17:0]\NLW_threshold_pipes[2].q_s3_reg_BCOUT_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].q_s3_reg_CARRYOUT_UNCONNECTED ;
  wire [47:28]\NLW_threshold_pipes[2].q_s3_reg_P_UNCONNECTED ;
  wire [47:0]\NLW_threshold_pipes[2].q_s3_reg_PCOUT_UNCONNECTED ;
  wire [3:1]\NLW_threshold_pipes[2].q_s3_reg_i_1_CO_UNCONNECTED ;
  wire [3:2]\NLW_threshold_pipes[2].q_s3_reg_i_1_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].q_s3_reg_i_13_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].q_s3_reg_i_5_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].q_s3_reg_i_6_O_UNCONNECTED ;
  wire [3:0]\NLW_threshold_pipes[2].q_s3_reg_i_8_O_UNCONNECTED ;
  wire [3:3]\NLW_threshold_pipes[2].remainder_s6_reg[31]_i_1_CO_UNCONNECTED ;

  assign meta_threshold2[31] = \<const0> ;
  assign meta_threshold2[30:0] = \^meta_threshold2 [30:0];
  assign meta_threshold3[31] = \<const0> ;
  assign meta_threshold3[30] = \<const0> ;
  assign meta_threshold3[29] = \<const0> ;
  assign meta_threshold3[28:0] = \^meta_threshold3 [28:0];
  GND GND
       (.G(\<const0> ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[0]_INST_0 
       (.CI(\bad[0]_INST_0_i_1_n_0 ),
        .CO({bad[0],\bad[0]_INST_0_n_1 ,\bad[0]_INST_0_n_2 ,\bad[0]_INST_0_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[0]_INST_0_i_2_n_0 ,\bad[0]_INST_0_i_3_n_0 ,\bad[0]_INST_0_i_4_n_0 ,\bad[0]_INST_0_i_5_n_0 }),
        .O(\NLW_bad[0]_INST_0_O_UNCONNECTED [3:0]),
        .S({\bad[0]_INST_0_i_6_n_0 ,\bad[0]_INST_0_i_7_n_0 ,\bad[0]_INST_0_i_8_n_0 ,\bad[0]_INST_0_i_9_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[0]_INST_0_i_1 
       (.CI(\bad[0]_INST_0_i_10_n_0 ),
        .CO({\bad[0]_INST_0_i_1_n_0 ,\bad[0]_INST_0_i_1_n_1 ,\bad[0]_INST_0_i_1_n_2 ,\bad[0]_INST_0_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[0]_INST_0_i_11_n_0 ,\bad[0]_INST_0_i_12_n_0 ,\bad[0]_INST_0_i_13_n_0 ,\bad[0]_INST_0_i_14_n_0 }),
        .O(\NLW_bad[0]_INST_0_i_1_O_UNCONNECTED [3:0]),
        .S({\bad[0]_INST_0_i_15_n_0 ,\bad[0]_INST_0_i_16_n_0 ,\bad[0]_INST_0_i_17_n_0 ,\bad[0]_INST_0_i_18_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[0]_INST_0_i_10 
       (.CI(\bad[0]_INST_0_i_19_n_0 ),
        .CO({\bad[0]_INST_0_i_10_n_0 ,\bad[0]_INST_0_i_10_n_1 ,\bad[0]_INST_0_i_10_n_2 ,\bad[0]_INST_0_i_10_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[0]_INST_0_i_20_n_0 ,\bad[0]_INST_0_i_21_n_0 ,\bad[0]_INST_0_i_22_n_0 ,\bad[0]_INST_0_i_23_n_0 }),
        .O(\NLW_bad[0]_INST_0_i_10_O_UNCONNECTED [3:0]),
        .S({\bad[0]_INST_0_i_24_n_0 ,\bad[0]_INST_0_i_25_n_0 ,\bad[0]_INST_0_i_26_n_0 ,\bad[0]_INST_0_i_27_n_0 }));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[0]_INST_0_i_11 
       (.I0(meta_threshold1[22]),
        .I1(meta_threshold1[23]),
        .O(\bad[0]_INST_0_i_11_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[0]_INST_0_i_12 
       (.I0(meta_threshold1[20]),
        .I1(meta_threshold1[21]),
        .O(\bad[0]_INST_0_i_12_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[0]_INST_0_i_13 
       (.I0(meta_threshold1[18]),
        .I1(meta_threshold1[19]),
        .O(\bad[0]_INST_0_i_13_n_0 ));
  LUT3 #(
    .INIT(8'hF2)) 
    \bad[0]_INST_0_i_14 
       (.I0(meta_threshold1[16]),
        .I1(blocks[16]),
        .I2(meta_threshold1[17]),
        .O(\bad[0]_INST_0_i_14_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[0]_INST_0_i_15 
       (.I0(meta_threshold1[22]),
        .I1(meta_threshold1[23]),
        .O(\bad[0]_INST_0_i_15_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[0]_INST_0_i_16 
       (.I0(meta_threshold1[20]),
        .I1(meta_threshold1[21]),
        .O(\bad[0]_INST_0_i_16_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[0]_INST_0_i_17 
       (.I0(meta_threshold1[18]),
        .I1(meta_threshold1[19]),
        .O(\bad[0]_INST_0_i_17_n_0 ));
  LUT3 #(
    .INIT(8'h09)) 
    \bad[0]_INST_0_i_18 
       (.I0(meta_threshold1[16]),
        .I1(blocks[16]),
        .I2(meta_threshold1[17]),
        .O(\bad[0]_INST_0_i_18_n_0 ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[0]_INST_0_i_19 
       (.CI(1'b0),
        .CO({\bad[0]_INST_0_i_19_n_0 ,\bad[0]_INST_0_i_19_n_1 ,\bad[0]_INST_0_i_19_n_2 ,\bad[0]_INST_0_i_19_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[0]_INST_0_i_28_n_0 ,\bad[0]_INST_0_i_29_n_0 ,\bad[0]_INST_0_i_30_n_0 ,\bad[0]_INST_0_i_31_n_0 }),
        .O(\NLW_bad[0]_INST_0_i_19_O_UNCONNECTED [3:0]),
        .S({\bad[0]_INST_0_i_32_n_0 ,\bad[0]_INST_0_i_33_n_0 ,\bad[0]_INST_0_i_34_n_0 ,\bad[0]_INST_0_i_35_n_0 }));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[0]_INST_0_i_2 
       (.I0(meta_threshold1[30]),
        .I1(meta_threshold1[31]),
        .O(\bad[0]_INST_0_i_2_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[0]_INST_0_i_20 
       (.I0(meta_threshold1[14]),
        .I1(blocks[14]),
        .I2(blocks[15]),
        .I3(meta_threshold1[15]),
        .O(\bad[0]_INST_0_i_20_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[0]_INST_0_i_21 
       (.I0(meta_threshold1[12]),
        .I1(blocks[12]),
        .I2(blocks[13]),
        .I3(meta_threshold1[13]),
        .O(\bad[0]_INST_0_i_21_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[0]_INST_0_i_22 
       (.I0(meta_threshold1[10]),
        .I1(blocks[10]),
        .I2(blocks[11]),
        .I3(meta_threshold1[11]),
        .O(\bad[0]_INST_0_i_22_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[0]_INST_0_i_23 
       (.I0(meta_threshold1[8]),
        .I1(blocks[8]),
        .I2(blocks[9]),
        .I3(meta_threshold1[9]),
        .O(\bad[0]_INST_0_i_23_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[0]_INST_0_i_24 
       (.I0(meta_threshold1[14]),
        .I1(blocks[14]),
        .I2(meta_threshold1[15]),
        .I3(blocks[15]),
        .O(\bad[0]_INST_0_i_24_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[0]_INST_0_i_25 
       (.I0(meta_threshold1[12]),
        .I1(blocks[12]),
        .I2(meta_threshold1[13]),
        .I3(blocks[13]),
        .O(\bad[0]_INST_0_i_25_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[0]_INST_0_i_26 
       (.I0(meta_threshold1[10]),
        .I1(blocks[10]),
        .I2(meta_threshold1[11]),
        .I3(blocks[11]),
        .O(\bad[0]_INST_0_i_26_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[0]_INST_0_i_27 
       (.I0(meta_threshold1[8]),
        .I1(blocks[8]),
        .I2(meta_threshold1[9]),
        .I3(blocks[9]),
        .O(\bad[0]_INST_0_i_27_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[0]_INST_0_i_28 
       (.I0(meta_threshold1[6]),
        .I1(blocks[6]),
        .I2(blocks[7]),
        .I3(meta_threshold1[7]),
        .O(\bad[0]_INST_0_i_28_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[0]_INST_0_i_29 
       (.I0(meta_threshold1[4]),
        .I1(blocks[4]),
        .I2(blocks[5]),
        .I3(meta_threshold1[5]),
        .O(\bad[0]_INST_0_i_29_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[0]_INST_0_i_3 
       (.I0(meta_threshold1[28]),
        .I1(meta_threshold1[29]),
        .O(\bad[0]_INST_0_i_3_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[0]_INST_0_i_30 
       (.I0(meta_threshold1[2]),
        .I1(blocks[2]),
        .I2(blocks[3]),
        .I3(meta_threshold1[3]),
        .O(\bad[0]_INST_0_i_30_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[0]_INST_0_i_31 
       (.I0(meta_threshold1[0]),
        .I1(blocks[0]),
        .I2(blocks[1]),
        .I3(meta_threshold1[1]),
        .O(\bad[0]_INST_0_i_31_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[0]_INST_0_i_32 
       (.I0(meta_threshold1[6]),
        .I1(blocks[6]),
        .I2(meta_threshold1[7]),
        .I3(blocks[7]),
        .O(\bad[0]_INST_0_i_32_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[0]_INST_0_i_33 
       (.I0(meta_threshold1[4]),
        .I1(blocks[4]),
        .I2(meta_threshold1[5]),
        .I3(blocks[5]),
        .O(\bad[0]_INST_0_i_33_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[0]_INST_0_i_34 
       (.I0(meta_threshold1[2]),
        .I1(blocks[2]),
        .I2(meta_threshold1[3]),
        .I3(blocks[3]),
        .O(\bad[0]_INST_0_i_34_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[0]_INST_0_i_35 
       (.I0(meta_threshold1[0]),
        .I1(blocks[0]),
        .I2(meta_threshold1[1]),
        .I3(blocks[1]),
        .O(\bad[0]_INST_0_i_35_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[0]_INST_0_i_4 
       (.I0(meta_threshold1[26]),
        .I1(meta_threshold1[27]),
        .O(\bad[0]_INST_0_i_4_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[0]_INST_0_i_5 
       (.I0(meta_threshold1[24]),
        .I1(meta_threshold1[25]),
        .O(\bad[0]_INST_0_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[0]_INST_0_i_6 
       (.I0(meta_threshold1[30]),
        .I1(meta_threshold1[31]),
        .O(\bad[0]_INST_0_i_6_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[0]_INST_0_i_7 
       (.I0(meta_threshold1[28]),
        .I1(meta_threshold1[29]),
        .O(\bad[0]_INST_0_i_7_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[0]_INST_0_i_8 
       (.I0(meta_threshold1[26]),
        .I1(meta_threshold1[27]),
        .O(\bad[0]_INST_0_i_8_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[0]_INST_0_i_9 
       (.I0(meta_threshold1[24]),
        .I1(meta_threshold1[25]),
        .O(\bad[0]_INST_0_i_9_n_0 ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[1]_INST_0 
       (.CI(\bad[1]_INST_0_i_1_n_0 ),
        .CO({bad[1],\bad[1]_INST_0_n_1 ,\bad[1]_INST_0_n_2 ,\bad[1]_INST_0_n_3 }),
        .CYINIT(1'b0),
        .DI({\^meta_threshold2 [30],\bad[1]_INST_0_i_2_n_0 ,\bad[1]_INST_0_i_3_n_0 ,\bad[1]_INST_0_i_4_n_0 }),
        .O(\NLW_bad[1]_INST_0_O_UNCONNECTED [3:0]),
        .S({\bad[1]_INST_0_i_5_n_0 ,\bad[1]_INST_0_i_6_n_0 ,\bad[1]_INST_0_i_7_n_0 ,\bad[1]_INST_0_i_8_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[1]_INST_0_i_1 
       (.CI(\bad[1]_INST_0_i_9_n_0 ),
        .CO({\bad[1]_INST_0_i_1_n_0 ,\bad[1]_INST_0_i_1_n_1 ,\bad[1]_INST_0_i_1_n_2 ,\bad[1]_INST_0_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[1]_INST_0_i_10_n_0 ,\bad[1]_INST_0_i_11_n_0 ,\bad[1]_INST_0_i_12_n_0 ,\bad[1]_INST_0_i_13_n_0 }),
        .O(\NLW_bad[1]_INST_0_i_1_O_UNCONNECTED [3:0]),
        .S({\bad[1]_INST_0_i_14_n_0 ,\bad[1]_INST_0_i_15_n_0 ,\bad[1]_INST_0_i_16_n_0 ,\bad[1]_INST_0_i_17_n_0 }));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[1]_INST_0_i_10 
       (.I0(\^meta_threshold2 [22]),
        .I1(\^meta_threshold2 [23]),
        .O(\bad[1]_INST_0_i_10_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[1]_INST_0_i_11 
       (.I0(\^meta_threshold2 [20]),
        .I1(\^meta_threshold2 [21]),
        .O(\bad[1]_INST_0_i_11_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[1]_INST_0_i_12 
       (.I0(\^meta_threshold2 [18]),
        .I1(\^meta_threshold2 [19]),
        .O(\bad[1]_INST_0_i_12_n_0 ));
  LUT3 #(
    .INIT(8'hF2)) 
    \bad[1]_INST_0_i_13 
       (.I0(\^meta_threshold2 [16]),
        .I1(blocks[16]),
        .I2(\^meta_threshold2 [17]),
        .O(\bad[1]_INST_0_i_13_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[1]_INST_0_i_14 
       (.I0(\^meta_threshold2 [22]),
        .I1(\^meta_threshold2 [23]),
        .O(\bad[1]_INST_0_i_14_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[1]_INST_0_i_15 
       (.I0(\^meta_threshold2 [20]),
        .I1(\^meta_threshold2 [21]),
        .O(\bad[1]_INST_0_i_15_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[1]_INST_0_i_16 
       (.I0(\^meta_threshold2 [18]),
        .I1(\^meta_threshold2 [19]),
        .O(\bad[1]_INST_0_i_16_n_0 ));
  LUT3 #(
    .INIT(8'h09)) 
    \bad[1]_INST_0_i_17 
       (.I0(\^meta_threshold2 [16]),
        .I1(blocks[16]),
        .I2(\^meta_threshold2 [17]),
        .O(\bad[1]_INST_0_i_17_n_0 ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[1]_INST_0_i_18 
       (.CI(1'b0),
        .CO({\bad[1]_INST_0_i_18_n_0 ,\bad[1]_INST_0_i_18_n_1 ,\bad[1]_INST_0_i_18_n_2 ,\bad[1]_INST_0_i_18_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[1]_INST_0_i_27_n_0 ,\bad[1]_INST_0_i_28_n_0 ,\bad[1]_INST_0_i_29_n_0 ,\bad[1]_INST_0_i_30_n_0 }),
        .O(\NLW_bad[1]_INST_0_i_18_O_UNCONNECTED [3:0]),
        .S({\bad[1]_INST_0_i_31_n_0 ,\bad[1]_INST_0_i_32_n_0 ,\bad[1]_INST_0_i_33_n_0 ,\bad[1]_INST_0_i_34_n_0 }));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[1]_INST_0_i_19 
       (.I0(\^meta_threshold2 [14]),
        .I1(blocks[14]),
        .I2(blocks[15]),
        .I3(\^meta_threshold2 [15]),
        .O(\bad[1]_INST_0_i_19_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[1]_INST_0_i_2 
       (.I0(\^meta_threshold2 [28]),
        .I1(\^meta_threshold2 [29]),
        .O(\bad[1]_INST_0_i_2_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[1]_INST_0_i_20 
       (.I0(\^meta_threshold2 [12]),
        .I1(blocks[12]),
        .I2(blocks[13]),
        .I3(\^meta_threshold2 [13]),
        .O(\bad[1]_INST_0_i_20_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[1]_INST_0_i_21 
       (.I0(\^meta_threshold2 [10]),
        .I1(blocks[10]),
        .I2(blocks[11]),
        .I3(\^meta_threshold2 [11]),
        .O(\bad[1]_INST_0_i_21_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[1]_INST_0_i_22 
       (.I0(\^meta_threshold2 [8]),
        .I1(blocks[8]),
        .I2(blocks[9]),
        .I3(\^meta_threshold2 [9]),
        .O(\bad[1]_INST_0_i_22_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[1]_INST_0_i_23 
       (.I0(\^meta_threshold2 [14]),
        .I1(blocks[14]),
        .I2(\^meta_threshold2 [15]),
        .I3(blocks[15]),
        .O(\bad[1]_INST_0_i_23_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[1]_INST_0_i_24 
       (.I0(\^meta_threshold2 [12]),
        .I1(blocks[12]),
        .I2(\^meta_threshold2 [13]),
        .I3(blocks[13]),
        .O(\bad[1]_INST_0_i_24_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[1]_INST_0_i_25 
       (.I0(\^meta_threshold2 [10]),
        .I1(blocks[10]),
        .I2(\^meta_threshold2 [11]),
        .I3(blocks[11]),
        .O(\bad[1]_INST_0_i_25_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[1]_INST_0_i_26 
       (.I0(\^meta_threshold2 [8]),
        .I1(blocks[8]),
        .I2(\^meta_threshold2 [9]),
        .I3(blocks[9]),
        .O(\bad[1]_INST_0_i_26_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[1]_INST_0_i_27 
       (.I0(\^meta_threshold2 [6]),
        .I1(blocks[6]),
        .I2(blocks[7]),
        .I3(\^meta_threshold2 [7]),
        .O(\bad[1]_INST_0_i_27_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[1]_INST_0_i_28 
       (.I0(\^meta_threshold2 [4]),
        .I1(blocks[4]),
        .I2(blocks[5]),
        .I3(\^meta_threshold2 [5]),
        .O(\bad[1]_INST_0_i_28_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[1]_INST_0_i_29 
       (.I0(\^meta_threshold2 [2]),
        .I1(blocks[2]),
        .I2(blocks[3]),
        .I3(\^meta_threshold2 [3]),
        .O(\bad[1]_INST_0_i_29_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[1]_INST_0_i_3 
       (.I0(\^meta_threshold2 [26]),
        .I1(\^meta_threshold2 [27]),
        .O(\bad[1]_INST_0_i_3_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[1]_INST_0_i_30 
       (.I0(\^meta_threshold2 [0]),
        .I1(blocks[0]),
        .I2(blocks[1]),
        .I3(\^meta_threshold2 [1]),
        .O(\bad[1]_INST_0_i_30_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[1]_INST_0_i_31 
       (.I0(\^meta_threshold2 [6]),
        .I1(blocks[6]),
        .I2(\^meta_threshold2 [7]),
        .I3(blocks[7]),
        .O(\bad[1]_INST_0_i_31_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[1]_INST_0_i_32 
       (.I0(\^meta_threshold2 [4]),
        .I1(blocks[4]),
        .I2(\^meta_threshold2 [5]),
        .I3(blocks[5]),
        .O(\bad[1]_INST_0_i_32_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[1]_INST_0_i_33 
       (.I0(\^meta_threshold2 [2]),
        .I1(blocks[2]),
        .I2(\^meta_threshold2 [3]),
        .I3(blocks[3]),
        .O(\bad[1]_INST_0_i_33_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[1]_INST_0_i_34 
       (.I0(\^meta_threshold2 [0]),
        .I1(blocks[0]),
        .I2(\^meta_threshold2 [1]),
        .I3(blocks[1]),
        .O(\bad[1]_INST_0_i_34_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[1]_INST_0_i_4 
       (.I0(\^meta_threshold2 [24]),
        .I1(\^meta_threshold2 [25]),
        .O(\bad[1]_INST_0_i_4_n_0 ));
  LUT1 #(
    .INIT(2'h1)) 
    \bad[1]_INST_0_i_5 
       (.I0(\^meta_threshold2 [30]),
        .O(\bad[1]_INST_0_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[1]_INST_0_i_6 
       (.I0(\^meta_threshold2 [28]),
        .I1(\^meta_threshold2 [29]),
        .O(\bad[1]_INST_0_i_6_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[1]_INST_0_i_7 
       (.I0(\^meta_threshold2 [26]),
        .I1(\^meta_threshold2 [27]),
        .O(\bad[1]_INST_0_i_7_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[1]_INST_0_i_8 
       (.I0(\^meta_threshold2 [24]),
        .I1(\^meta_threshold2 [25]),
        .O(\bad[1]_INST_0_i_8_n_0 ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[1]_INST_0_i_9 
       (.CI(\bad[1]_INST_0_i_18_n_0 ),
        .CO({\bad[1]_INST_0_i_9_n_0 ,\bad[1]_INST_0_i_9_n_1 ,\bad[1]_INST_0_i_9_n_2 ,\bad[1]_INST_0_i_9_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[1]_INST_0_i_19_n_0 ,\bad[1]_INST_0_i_20_n_0 ,\bad[1]_INST_0_i_21_n_0 ,\bad[1]_INST_0_i_22_n_0 }),
        .O(\NLW_bad[1]_INST_0_i_9_O_UNCONNECTED [3:0]),
        .S({\bad[1]_INST_0_i_23_n_0 ,\bad[1]_INST_0_i_24_n_0 ,\bad[1]_INST_0_i_25_n_0 ,\bad[1]_INST_0_i_26_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[2]_INST_0 
       (.CI(\bad[2]_INST_0_i_1_n_0 ),
        .CO({\NLW_bad[2]_INST_0_CO_UNCONNECTED [3],bad[2],\bad[2]_INST_0_n_2 ,\bad[2]_INST_0_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,\^meta_threshold3 [28],\bad[2]_INST_0_i_2_n_0 ,\bad[2]_INST_0_i_3_n_0 }),
        .O(\NLW_bad[2]_INST_0_O_UNCONNECTED [3:0]),
        .S({1'b0,\bad[2]_INST_0_i_4_n_0 ,\bad[2]_INST_0_i_5_n_0 ,\bad[2]_INST_0_i_6_n_0 }));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[2]_INST_0_i_1 
       (.CI(\bad[2]_INST_0_i_7_n_0 ),
        .CO({\bad[2]_INST_0_i_1_n_0 ,\bad[2]_INST_0_i_1_n_1 ,\bad[2]_INST_0_i_1_n_2 ,\bad[2]_INST_0_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[2]_INST_0_i_8_n_0 ,\bad[2]_INST_0_i_9_n_0 ,\bad[2]_INST_0_i_10_n_0 ,\bad[2]_INST_0_i_11_n_0 }),
        .O(\NLW_bad[2]_INST_0_i_1_O_UNCONNECTED [3:0]),
        .S({\bad[2]_INST_0_i_12_n_0 ,\bad[2]_INST_0_i_13_n_0 ,\bad[2]_INST_0_i_14_n_0 ,\bad[2]_INST_0_i_15_n_0 }));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[2]_INST_0_i_10 
       (.I0(\^meta_threshold3 [18]),
        .I1(\^meta_threshold3 [19]),
        .O(\bad[2]_INST_0_i_10_n_0 ));
  LUT3 #(
    .INIT(8'hF2)) 
    \bad[2]_INST_0_i_11 
       (.I0(\^meta_threshold3 [16]),
        .I1(blocks[16]),
        .I2(\^meta_threshold3 [17]),
        .O(\bad[2]_INST_0_i_11_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[2]_INST_0_i_12 
       (.I0(\^meta_threshold3 [22]),
        .I1(\^meta_threshold3 [23]),
        .O(\bad[2]_INST_0_i_12_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[2]_INST_0_i_13 
       (.I0(\^meta_threshold3 [20]),
        .I1(\^meta_threshold3 [21]),
        .O(\bad[2]_INST_0_i_13_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[2]_INST_0_i_14 
       (.I0(\^meta_threshold3 [18]),
        .I1(\^meta_threshold3 [19]),
        .O(\bad[2]_INST_0_i_14_n_0 ));
  LUT3 #(
    .INIT(8'h09)) 
    \bad[2]_INST_0_i_15 
       (.I0(\^meta_threshold3 [16]),
        .I1(blocks[16]),
        .I2(\^meta_threshold3 [17]),
        .O(\bad[2]_INST_0_i_15_n_0 ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[2]_INST_0_i_16 
       (.CI(1'b0),
        .CO({\bad[2]_INST_0_i_16_n_0 ,\bad[2]_INST_0_i_16_n_1 ,\bad[2]_INST_0_i_16_n_2 ,\bad[2]_INST_0_i_16_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[2]_INST_0_i_25_n_0 ,\bad[2]_INST_0_i_26_n_0 ,\bad[2]_INST_0_i_27_n_0 ,\bad[2]_INST_0_i_28_n_0 }),
        .O(\NLW_bad[2]_INST_0_i_16_O_UNCONNECTED [3:0]),
        .S({\bad[2]_INST_0_i_29_n_0 ,\bad[2]_INST_0_i_30_n_0 ,\bad[2]_INST_0_i_31_n_0 ,\bad[2]_INST_0_i_32_n_0 }));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[2]_INST_0_i_17 
       (.I0(\^meta_threshold3 [14]),
        .I1(blocks[14]),
        .I2(blocks[15]),
        .I3(\^meta_threshold3 [15]),
        .O(\bad[2]_INST_0_i_17_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[2]_INST_0_i_18 
       (.I0(\^meta_threshold3 [12]),
        .I1(blocks[12]),
        .I2(blocks[13]),
        .I3(\^meta_threshold3 [13]),
        .O(\bad[2]_INST_0_i_18_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[2]_INST_0_i_19 
       (.I0(\^meta_threshold3 [10]),
        .I1(blocks[10]),
        .I2(blocks[11]),
        .I3(\^meta_threshold3 [11]),
        .O(\bad[2]_INST_0_i_19_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[2]_INST_0_i_2 
       (.I0(\^meta_threshold3 [26]),
        .I1(\^meta_threshold3 [27]),
        .O(\bad[2]_INST_0_i_2_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[2]_INST_0_i_20 
       (.I0(\^meta_threshold3 [8]),
        .I1(blocks[8]),
        .I2(blocks[9]),
        .I3(\^meta_threshold3 [9]),
        .O(\bad[2]_INST_0_i_20_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[2]_INST_0_i_21 
       (.I0(\^meta_threshold3 [14]),
        .I1(blocks[14]),
        .I2(\^meta_threshold3 [15]),
        .I3(blocks[15]),
        .O(\bad[2]_INST_0_i_21_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[2]_INST_0_i_22 
       (.I0(\^meta_threshold3 [12]),
        .I1(blocks[12]),
        .I2(\^meta_threshold3 [13]),
        .I3(blocks[13]),
        .O(\bad[2]_INST_0_i_22_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[2]_INST_0_i_23 
       (.I0(\^meta_threshold3 [10]),
        .I1(blocks[10]),
        .I2(\^meta_threshold3 [11]),
        .I3(blocks[11]),
        .O(\bad[2]_INST_0_i_23_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[2]_INST_0_i_24 
       (.I0(\^meta_threshold3 [8]),
        .I1(blocks[8]),
        .I2(\^meta_threshold3 [9]),
        .I3(blocks[9]),
        .O(\bad[2]_INST_0_i_24_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[2]_INST_0_i_25 
       (.I0(\^meta_threshold3 [6]),
        .I1(blocks[6]),
        .I2(blocks[7]),
        .I3(\^meta_threshold3 [7]),
        .O(\bad[2]_INST_0_i_25_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[2]_INST_0_i_26 
       (.I0(\^meta_threshold3 [4]),
        .I1(blocks[4]),
        .I2(blocks[5]),
        .I3(\^meta_threshold3 [5]),
        .O(\bad[2]_INST_0_i_26_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[2]_INST_0_i_27 
       (.I0(\^meta_threshold3 [2]),
        .I1(blocks[2]),
        .I2(blocks[3]),
        .I3(\^meta_threshold3 [3]),
        .O(\bad[2]_INST_0_i_27_n_0 ));
  LUT4 #(
    .INIT(16'h2F02)) 
    \bad[2]_INST_0_i_28 
       (.I0(\^meta_threshold3 [0]),
        .I1(blocks[0]),
        .I2(blocks[1]),
        .I3(\^meta_threshold3 [1]),
        .O(\bad[2]_INST_0_i_28_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[2]_INST_0_i_29 
       (.I0(\^meta_threshold3 [6]),
        .I1(blocks[6]),
        .I2(\^meta_threshold3 [7]),
        .I3(blocks[7]),
        .O(\bad[2]_INST_0_i_29_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[2]_INST_0_i_3 
       (.I0(\^meta_threshold3 [24]),
        .I1(\^meta_threshold3 [25]),
        .O(\bad[2]_INST_0_i_3_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[2]_INST_0_i_30 
       (.I0(\^meta_threshold3 [4]),
        .I1(blocks[4]),
        .I2(\^meta_threshold3 [5]),
        .I3(blocks[5]),
        .O(\bad[2]_INST_0_i_30_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[2]_INST_0_i_31 
       (.I0(\^meta_threshold3 [2]),
        .I1(blocks[2]),
        .I2(\^meta_threshold3 [3]),
        .I3(blocks[3]),
        .O(\bad[2]_INST_0_i_31_n_0 ));
  LUT4 #(
    .INIT(16'h9009)) 
    \bad[2]_INST_0_i_32 
       (.I0(\^meta_threshold3 [0]),
        .I1(blocks[0]),
        .I2(\^meta_threshold3 [1]),
        .I3(blocks[1]),
        .O(\bad[2]_INST_0_i_32_n_0 ));
  LUT1 #(
    .INIT(2'h1)) 
    \bad[2]_INST_0_i_4 
       (.I0(\^meta_threshold3 [28]),
        .O(\bad[2]_INST_0_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[2]_INST_0_i_5 
       (.I0(\^meta_threshold3 [26]),
        .I1(\^meta_threshold3 [27]),
        .O(\bad[2]_INST_0_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h1)) 
    \bad[2]_INST_0_i_6 
       (.I0(\^meta_threshold3 [24]),
        .I1(\^meta_threshold3 [25]),
        .O(\bad[2]_INST_0_i_6_n_0 ));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 \bad[2]_INST_0_i_7 
       (.CI(\bad[2]_INST_0_i_16_n_0 ),
        .CO({\bad[2]_INST_0_i_7_n_0 ,\bad[2]_INST_0_i_7_n_1 ,\bad[2]_INST_0_i_7_n_2 ,\bad[2]_INST_0_i_7_n_3 }),
        .CYINIT(1'b0),
        .DI({\bad[2]_INST_0_i_17_n_0 ,\bad[2]_INST_0_i_18_n_0 ,\bad[2]_INST_0_i_19_n_0 ,\bad[2]_INST_0_i_20_n_0 }),
        .O(\NLW_bad[2]_INST_0_i_7_O_UNCONNECTED [3:0]),
        .S({\bad[2]_INST_0_i_21_n_0 ,\bad[2]_INST_0_i_22_n_0 ,\bad[2]_INST_0_i_23_n_0 ,\bad[2]_INST_0_i_24_n_0 }));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[2]_INST_0_i_8 
       (.I0(\^meta_threshold3 [22]),
        .I1(\^meta_threshold3 [23]),
        .O(\bad[2]_INST_0_i_8_n_0 ));
  LUT2 #(
    .INIT(4'hE)) 
    \bad[2]_INST_0_i_9 
       (.I0(\^meta_threshold3 [20]),
        .I1(\^meta_threshold3 [21]),
        .O(\bad[2]_INST_0_i_9_n_0 ));
  (* METHODOLOGY_DRC_VIOS = "{SYNTH-11 {cell *THIS*}}" *) 
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(0),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(0),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    partial_product1_return
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[15:0]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(NLW_partial_product1_return_ACOUT_UNCONNECTED[29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(NLW_partial_product1_return_BCOUT_UNCONNECTED[17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(NLW_partial_product1_return_CARRYCASCOUT_UNCONNECTED),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(NLW_partial_product1_return_CARRYOUT_UNCONNECTED[3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b0),
        .CEP(1'b0),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(NLW_partial_product1_return_MULTSIGNOUT_UNCONNECTED),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(NLW_partial_product1_return_OVERFLOW_UNCONNECTED),
        .P({NLW_partial_product1_return_P_UNCONNECTED[47:29],partial_product1_return__0}),
        .PATTERNBDETECT(NLW_partial_product1_return_PATTERNBDETECT_UNCONNECTED),
        .PATTERNDETECT(NLW_partial_product1_return_PATTERNDETECT_UNCONNECTED),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(NLW_partial_product1_return_PCOUT_UNCONNECTED[47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(NLW_partial_product1_return_UNDERFLOW_UNCONNECTED));
  (* METHODOLOGY_DRC_VIOS = "{SYNTH-11 {cell *THIS*}}" *) 
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(0),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(0),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    partial_product_return
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[15:0]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(NLW_partial_product_return_ACOUT_UNCONNECTED[29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(NLW_partial_product_return_BCOUT_UNCONNECTED[17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(NLW_partial_product_return_CARRYCASCOUT_UNCONNECTED),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(NLW_partial_product_return_CARRYOUT_UNCONNECTED[3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b0),
        .CEP(1'b0),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(NLW_partial_product_return_MULTSIGNOUT_UNCONNECTED),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(NLW_partial_product_return_OVERFLOW_UNCONNECTED),
        .P({NLW_partial_product_return_P_UNCONNECTED[47:30],partial_product_return__0}),
        .PATTERNBDETECT(NLW_partial_product_return_PATTERNBDETECT_UNCONNECTED),
        .PATTERNDETECT(NLW_partial_product_return_PATTERNDETECT_UNCONNECTED),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(NLW_partial_product_return_PCOUT_UNCONNECTED[47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(NLW_partial_product_return_UNDERFLOW_UNCONNECTED));
  LUT6 #(
    .INIT(64'hF0FFAACCF000AACC)) 
    selected_bad_INST_0
       (.I0(bad[1]),
        .I1(bad[0]),
        .I2(descriptor_count_bad0),
        .I3(selected[0]),
        .I4(selected[1]),
        .I5(bad[2]),
        .O(selected_bad));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 selected_bad_INST_0_i_1
       (.CI(selected_bad_INST_0_i_2_n_0),
        .CO({descriptor_count_bad0,selected_bad_INST_0_i_1_n_1,selected_bad_INST_0_i_1_n_2,selected_bad_INST_0_i_1_n_3}),
        .CYINIT(1'b0),
        .DI({selected_bad_INST_0_i_3_n_0,selected_bad_INST_0_i_4_n_0,selected_bad_INST_0_i_5_n_0,selected_bad_INST_0_i_6_n_0}),
        .O(NLW_selected_bad_INST_0_i_1_O_UNCONNECTED[3:0]),
        .S({selected_bad_INST_0_i_7_n_0,selected_bad_INST_0_i_8_n_0,selected_bad_INST_0_i_9_n_0,selected_bad_INST_0_i_10_n_0}));
  LUT2 #(
    .INIT(4'h1)) 
    selected_bad_INST_0_i_10
       (.I0(numerator[24]),
        .I1(numerator[25]),
        .O(selected_bad_INST_0_i_10_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 selected_bad_INST_0_i_11
       (.CI(selected_bad_INST_0_i_20_n_0),
        .CO({selected_bad_INST_0_i_11_n_0,selected_bad_INST_0_i_11_n_1,selected_bad_INST_0_i_11_n_2,selected_bad_INST_0_i_11_n_3}),
        .CYINIT(1'b0),
        .DI({selected_bad_INST_0_i_21_n_0,selected_bad_INST_0_i_22_n_0,selected_bad_INST_0_i_23_n_0,selected_bad_INST_0_i_24_n_0}),
        .O(NLW_selected_bad_INST_0_i_11_O_UNCONNECTED[3:0]),
        .S({selected_bad_INST_0_i_25_n_0,selected_bad_INST_0_i_26_n_0,selected_bad_INST_0_i_27_n_0,selected_bad_INST_0_i_28_n_0}));
  LUT2 #(
    .INIT(4'hE)) 
    selected_bad_INST_0_i_12
       (.I0(numerator[22]),
        .I1(numerator[23]),
        .O(selected_bad_INST_0_i_12_n_0));
  LUT2 #(
    .INIT(4'hE)) 
    selected_bad_INST_0_i_13
       (.I0(numerator[20]),
        .I1(numerator[21]),
        .O(selected_bad_INST_0_i_13_n_0));
  LUT2 #(
    .INIT(4'hE)) 
    selected_bad_INST_0_i_14
       (.I0(numerator[18]),
        .I1(numerator[19]),
        .O(selected_bad_INST_0_i_14_n_0));
  LUT3 #(
    .INIT(8'hF2)) 
    selected_bad_INST_0_i_15
       (.I0(numerator[16]),
        .I1(blocks[16]),
        .I2(numerator[17]),
        .O(selected_bad_INST_0_i_15_n_0));
  LUT2 #(
    .INIT(4'h1)) 
    selected_bad_INST_0_i_16
       (.I0(numerator[22]),
        .I1(numerator[23]),
        .O(selected_bad_INST_0_i_16_n_0));
  LUT2 #(
    .INIT(4'h1)) 
    selected_bad_INST_0_i_17
       (.I0(numerator[20]),
        .I1(numerator[21]),
        .O(selected_bad_INST_0_i_17_n_0));
  LUT2 #(
    .INIT(4'h1)) 
    selected_bad_INST_0_i_18
       (.I0(numerator[18]),
        .I1(numerator[19]),
        .O(selected_bad_INST_0_i_18_n_0));
  LUT3 #(
    .INIT(8'h09)) 
    selected_bad_INST_0_i_19
       (.I0(numerator[16]),
        .I1(blocks[16]),
        .I2(numerator[17]),
        .O(selected_bad_INST_0_i_19_n_0));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 selected_bad_INST_0_i_2
       (.CI(selected_bad_INST_0_i_11_n_0),
        .CO({selected_bad_INST_0_i_2_n_0,selected_bad_INST_0_i_2_n_1,selected_bad_INST_0_i_2_n_2,selected_bad_INST_0_i_2_n_3}),
        .CYINIT(1'b0),
        .DI({selected_bad_INST_0_i_12_n_0,selected_bad_INST_0_i_13_n_0,selected_bad_INST_0_i_14_n_0,selected_bad_INST_0_i_15_n_0}),
        .O(NLW_selected_bad_INST_0_i_2_O_UNCONNECTED[3:0]),
        .S({selected_bad_INST_0_i_16_n_0,selected_bad_INST_0_i_17_n_0,selected_bad_INST_0_i_18_n_0,selected_bad_INST_0_i_19_n_0}));
  (* COMPARATOR_THRESHOLD = "11" *) 
  CARRY4 selected_bad_INST_0_i_20
       (.CI(1'b0),
        .CO({selected_bad_INST_0_i_20_n_0,selected_bad_INST_0_i_20_n_1,selected_bad_INST_0_i_20_n_2,selected_bad_INST_0_i_20_n_3}),
        .CYINIT(1'b0),
        .DI({selected_bad_INST_0_i_29_n_0,selected_bad_INST_0_i_30_n_0,selected_bad_INST_0_i_31_n_0,selected_bad_INST_0_i_32_n_0}),
        .O(NLW_selected_bad_INST_0_i_20_O_UNCONNECTED[3:0]),
        .S({selected_bad_INST_0_i_33_n_0,selected_bad_INST_0_i_34_n_0,selected_bad_INST_0_i_35_n_0,selected_bad_INST_0_i_36_n_0}));
  LUT4 #(
    .INIT(16'h2F02)) 
    selected_bad_INST_0_i_21
       (.I0(numerator[14]),
        .I1(blocks[14]),
        .I2(blocks[15]),
        .I3(numerator[15]),
        .O(selected_bad_INST_0_i_21_n_0));
  LUT4 #(
    .INIT(16'h2F02)) 
    selected_bad_INST_0_i_22
       (.I0(numerator[12]),
        .I1(blocks[12]),
        .I2(blocks[13]),
        .I3(numerator[13]),
        .O(selected_bad_INST_0_i_22_n_0));
  LUT4 #(
    .INIT(16'h2F02)) 
    selected_bad_INST_0_i_23
       (.I0(numerator[10]),
        .I1(blocks[10]),
        .I2(blocks[11]),
        .I3(numerator[11]),
        .O(selected_bad_INST_0_i_23_n_0));
  LUT4 #(
    .INIT(16'h2F02)) 
    selected_bad_INST_0_i_24
       (.I0(numerator[8]),
        .I1(blocks[8]),
        .I2(blocks[9]),
        .I3(numerator[9]),
        .O(selected_bad_INST_0_i_24_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    selected_bad_INST_0_i_25
       (.I0(numerator[14]),
        .I1(blocks[14]),
        .I2(numerator[15]),
        .I3(blocks[15]),
        .O(selected_bad_INST_0_i_25_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    selected_bad_INST_0_i_26
       (.I0(numerator[12]),
        .I1(blocks[12]),
        .I2(numerator[13]),
        .I3(blocks[13]),
        .O(selected_bad_INST_0_i_26_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    selected_bad_INST_0_i_27
       (.I0(numerator[10]),
        .I1(blocks[10]),
        .I2(numerator[11]),
        .I3(blocks[11]),
        .O(selected_bad_INST_0_i_27_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    selected_bad_INST_0_i_28
       (.I0(numerator[8]),
        .I1(blocks[8]),
        .I2(numerator[9]),
        .I3(blocks[9]),
        .O(selected_bad_INST_0_i_28_n_0));
  LUT4 #(
    .INIT(16'h2F02)) 
    selected_bad_INST_0_i_29
       (.I0(numerator[6]),
        .I1(blocks[6]),
        .I2(blocks[7]),
        .I3(numerator[7]),
        .O(selected_bad_INST_0_i_29_n_0));
  LUT2 #(
    .INIT(4'hE)) 
    selected_bad_INST_0_i_3
       (.I0(numerator[30]),
        .I1(numerator[31]),
        .O(selected_bad_INST_0_i_3_n_0));
  LUT4 #(
    .INIT(16'h2F02)) 
    selected_bad_INST_0_i_30
       (.I0(numerator[4]),
        .I1(blocks[4]),
        .I2(blocks[5]),
        .I3(numerator[5]),
        .O(selected_bad_INST_0_i_30_n_0));
  LUT4 #(
    .INIT(16'h2F02)) 
    selected_bad_INST_0_i_31
       (.I0(numerator[2]),
        .I1(blocks[2]),
        .I2(blocks[3]),
        .I3(numerator[3]),
        .O(selected_bad_INST_0_i_31_n_0));
  LUT4 #(
    .INIT(16'h2F02)) 
    selected_bad_INST_0_i_32
       (.I0(numerator[0]),
        .I1(blocks[0]),
        .I2(blocks[1]),
        .I3(numerator[1]),
        .O(selected_bad_INST_0_i_32_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    selected_bad_INST_0_i_33
       (.I0(numerator[6]),
        .I1(blocks[6]),
        .I2(numerator[7]),
        .I3(blocks[7]),
        .O(selected_bad_INST_0_i_33_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    selected_bad_INST_0_i_34
       (.I0(numerator[4]),
        .I1(blocks[4]),
        .I2(numerator[5]),
        .I3(blocks[5]),
        .O(selected_bad_INST_0_i_34_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    selected_bad_INST_0_i_35
       (.I0(numerator[2]),
        .I1(blocks[2]),
        .I2(numerator[3]),
        .I3(blocks[3]),
        .O(selected_bad_INST_0_i_35_n_0));
  LUT4 #(
    .INIT(16'h9009)) 
    selected_bad_INST_0_i_36
       (.I0(numerator[0]),
        .I1(blocks[0]),
        .I2(numerator[1]),
        .I3(blocks[1]),
        .O(selected_bad_INST_0_i_36_n_0));
  LUT2 #(
    .INIT(4'hE)) 
    selected_bad_INST_0_i_4
       (.I0(numerator[28]),
        .I1(numerator[29]),
        .O(selected_bad_INST_0_i_4_n_0));
  LUT2 #(
    .INIT(4'hE)) 
    selected_bad_INST_0_i_5
       (.I0(numerator[26]),
        .I1(numerator[27]),
        .O(selected_bad_INST_0_i_5_n_0));
  LUT2 #(
    .INIT(4'hE)) 
    selected_bad_INST_0_i_6
       (.I0(numerator[24]),
        .I1(numerator[25]),
        .O(selected_bad_INST_0_i_6_n_0));
  LUT2 #(
    .INIT(4'h1)) 
    selected_bad_INST_0_i_7
       (.I0(numerator[30]),
        .I1(numerator[31]),
        .O(selected_bad_INST_0_i_7_n_0));
  LUT2 #(
    .INIT(4'h1)) 
    selected_bad_INST_0_i_8
       (.I0(numerator[28]),
        .I1(numerator[29]),
        .O(selected_bad_INST_0_i_8_n_0));
  LUT2 #(
    .INIT(4'h1)) 
    selected_bad_INST_0_i_9
       (.I0(numerator[26]),
        .I1(numerator[27]),
        .O(selected_bad_INST_0_i_9_n_0));
  FDRE \threshold_pipes[0].captured_count_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[16]),
        .Q(A[0]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[17]),
        .Q(A[1]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[18]),
        .Q(A[2]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[19]),
        .Q(A[3]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[20]),
        .Q(A[4]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[21]),
        .Q(A[5]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[22]),
        .Q(A[6]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[23]),
        .Q(A[7]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[24]),
        .Q(A[8]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[25]),
        .Q(A[9]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[26]),
        .Q(A[10]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[27]),
        .Q(A[11]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[28]),
        .Q(A[12]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[29] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[29]),
        .Q(A[13]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[30] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[30]),
        .Q(A[14]),
        .R(1'b0));
  FDRE \threshold_pipes[0].captured_count_reg[31] 
       (.C(clk),
        .CE(1'b1),
        .D(numerator[31]),
        .Q(A[15]),
        .R(1'b0));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(0),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(0),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[0].check_hi_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[0].check_hi_reg_i_1_n_1 ,\threshold_pipes[0].check_hi_reg_i_1_n_6 ,\threshold_pipes[0].check_hi_reg_i_1_n_7 ,\threshold_pipes[0].check_hi_reg_i_2_n_4 ,\threshold_pipes[0].check_hi_reg_i_2_n_5 ,\threshold_pipes[0].check_hi_reg_i_2_n_6 ,\threshold_pipes[0].check_hi_reg_i_2_n_7 ,\threshold_pipes[0].check_hi_reg_i_3_n_4 ,\threshold_pipes[0].check_hi_reg_i_3_n_5 ,\threshold_pipes[0].check_hi_reg_i_3_n_6 ,\threshold_pipes[0].check_hi_reg_i_3_n_7 ,\threshold_pipes[0].check_hi_reg_i_4_n_4 ,\threshold_pipes[0].check_hi_reg_i_4_n_5 ,\threshold_pipes[0].check_hi_reg_i_4_n_6 ,\threshold_pipes[0].check_hi_reg_i_4_n_7 }),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[0].check_hi_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[0].check_hi_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[0].check_hi_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[0].check_hi_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b0),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[0].check_hi_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[0].check_hi_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[0].check_hi_reg_P_UNCONNECTED [47:16],\threshold_pipes[0].check_hi_reg_n_90 ,\threshold_pipes[0].check_hi_reg_n_91 ,\threshold_pipes[0].check_hi_reg_n_92 ,\threshold_pipes[0].check_hi_reg_n_93 ,\threshold_pipes[0].check_hi_reg_n_94 ,\threshold_pipes[0].check_hi_reg_n_95 ,\threshold_pipes[0].check_hi_reg_n_96 ,\threshold_pipes[0].check_hi_reg_n_97 ,\threshold_pipes[0].check_hi_reg_n_98 ,\threshold_pipes[0].check_hi_reg_n_99 ,\threshold_pipes[0].check_hi_reg_n_100 ,\threshold_pipes[0].check_hi_reg_n_101 ,\threshold_pipes[0].check_hi_reg_n_102 ,\threshold_pipes[0].check_hi_reg_n_103 ,\threshold_pipes[0].check_hi_reg_n_104 ,\threshold_pipes[0].check_hi_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[0].check_hi_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[0].check_hi_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[0].check_hi_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[0].check_hi_reg_UNDERFLOW_UNCONNECTED ));
  CARRY4 \threshold_pipes[0].check_hi_reg_i_1 
       (.CI(\threshold_pipes[0].check_hi_reg_i_2_n_0 ),
        .CO({\NLW_threshold_pipes[0].check_hi_reg_i_1_CO_UNCONNECTED [3],\threshold_pipes[0].check_hi_reg_i_1_n_1 ,\NLW_threshold_pipes[0].check_hi_reg_i_1_CO_UNCONNECTED [1],\threshold_pipes[0].check_hi_reg_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_threshold_pipes[0].check_hi_reg_i_1_O_UNCONNECTED [3:2],\threshold_pipes[0].check_hi_reg_i_1_n_6 ,\threshold_pipes[0].check_hi_reg_i_1_n_7 }),
        .S({1'b0,1'b1,\threshold_pipes[0].high_s2 [29:28]}));
  CARRY4 \threshold_pipes[0].check_hi_reg_i_2 
       (.CI(\threshold_pipes[0].check_hi_reg_i_3_n_0 ),
        .CO({\threshold_pipes[0].check_hi_reg_i_2_n_0 ,\threshold_pipes[0].check_hi_reg_i_2_n_1 ,\threshold_pipes[0].check_hi_reg_i_2_n_2 ,\threshold_pipes[0].check_hi_reg_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[0].check_hi_reg_i_2_n_4 ,\threshold_pipes[0].check_hi_reg_i_2_n_5 ,\threshold_pipes[0].check_hi_reg_i_2_n_6 ,\threshold_pipes[0].check_hi_reg_i_2_n_7 }),
        .S(\threshold_pipes[0].high_s2 [27:24]));
  CARRY4 \threshold_pipes[0].check_hi_reg_i_3 
       (.CI(\threshold_pipes[0].check_hi_reg_i_4_n_0 ),
        .CO({\threshold_pipes[0].check_hi_reg_i_3_n_0 ,\threshold_pipes[0].check_hi_reg_i_3_n_1 ,\threshold_pipes[0].check_hi_reg_i_3_n_2 ,\threshold_pipes[0].check_hi_reg_i_3_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[0].check_hi_reg_i_3_n_4 ,\threshold_pipes[0].check_hi_reg_i_3_n_5 ,\threshold_pipes[0].check_hi_reg_i_3_n_6 ,\threshold_pipes[0].check_hi_reg_i_3_n_7 }),
        .S(\threshold_pipes[0].high_s2 [23:20]));
  CARRY4 \threshold_pipes[0].check_hi_reg_i_4 
       (.CI(\threshold_pipes[0].product_s5_reg_i_1_n_0 ),
        .CO({\threshold_pipes[0].check_hi_reg_i_4_n_0 ,\threshold_pipes[0].check_hi_reg_i_4_n_1 ,\threshold_pipes[0].check_hi_reg_i_4_n_2 ,\threshold_pipes[0].check_hi_reg_i_4_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[0].check_hi_reg_i_4_n_4 ,\threshold_pipes[0].check_hi_reg_i_4_n_5 ,\threshold_pipes[0].check_hi_reg_i_4_n_6 ,\threshold_pipes[0].check_hi_reg_i_4_n_7 }),
        .S(\threshold_pipes[0].high_s2 [19:16]));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[0].count_threshold[0][3]_i_10 
       (.I0(\threshold_pipes[0].remainder_s6 [22]),
        .I1(\threshold_pipes[0].remainder_s6 [23]),
        .I2(\threshold_pipes[0].remainder_s6 [20]),
        .I3(\threshold_pipes[0].remainder_s6 [21]),
        .I4(\threshold_pipes[0].remainder_s6 [25]),
        .I5(\threshold_pipes[0].remainder_s6 [24]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_10_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[0].count_threshold[0][3]_i_11 
       (.I0(\threshold_pipes[0].remainder_s6 [10]),
        .I1(\threshold_pipes[0].remainder_s6 [11]),
        .I2(\threshold_pipes[0].remainder_s6 [8]),
        .I3(\threshold_pipes[0].remainder_s6 [9]),
        .I4(\threshold_pipes[0].remainder_s6 [13]),
        .I5(\threshold_pipes[0].remainder_s6 [12]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_11_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[0].count_threshold[0][3]_i_12 
       (.I0(\threshold_pipes[0].remainder_s6 [16]),
        .I1(\threshold_pipes[0].remainder_s6 [17]),
        .I2(\threshold_pipes[0].remainder_s6 [14]),
        .I3(\threshold_pipes[0].remainder_s6 [15]),
        .I4(\threshold_pipes[0].remainder_s6 [19]),
        .I5(\threshold_pipes[0].remainder_s6 [18]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_12_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair0" *) 
  LUT2 #(
    .INIT(4'hE)) 
    \threshold_pipes[0].count_threshold[0][3]_i_13 
       (.I0(\threshold_pipes[0].remainder_s6 [4]),
        .I1(\threshold_pipes[0].remainder_s6 [5]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_13_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[0].count_threshold[0][3]_i_14 
       (.I0(\threshold_pipes[0].remainder_s6 [14]),
        .I1(\threshold_pipes[0].remainder_s6 [15]),
        .I2(\threshold_pipes[0].remainder_s6 [12]),
        .I3(\threshold_pipes[0].remainder_s6 [13]),
        .I4(\threshold_pipes[0].remainder_s6 [11]),
        .I5(\threshold_pipes[0].remainder_s6 [10]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_14_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair0" *) 
  LUT5 #(
    .INIT(32'h00000001)) 
    \threshold_pipes[0].count_threshold[0][3]_i_15 
       (.I0(\threshold_pipes[0].remainder_s6 [3]),
        .I1(\threshold_pipes[0].remainder_s6 [4]),
        .I2(\threshold_pipes[0].remainder_s6 [5]),
        .I3(\threshold_pipes[0].remainder_s6 [7]),
        .I4(\threshold_pipes[0].remainder_s6 [6]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_15_n_0 ));
  LUT6 #(
    .INIT(64'h5555555555555556)) 
    \threshold_pipes[0].count_threshold[0][3]_i_2 
       (.I0(\threshold_pipes[0].q_s6 [1]),
        .I1(\threshold_pipes[0].count_threshold[0][3]_i_4_n_0 ),
        .I2(\threshold_pipes[0].count_threshold[0][3]_i_5_n_0 ),
        .I3(\threshold_pipes[0].count_threshold[0][3]_i_6_n_0 ),
        .I4(\threshold_pipes[0].remainder_s6 [3]),
        .I5(\threshold_pipes[0].count_threshold[0][3]_i_7_n_0 ),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'h6AAAAAAAAAAAAAAA)) 
    \threshold_pipes[0].count_threshold[0][3]_i_3 
       (.I0(\threshold_pipes[0].q_s6 [0]),
        .I1(\threshold_pipes[0].count_threshold[0][3]_i_8_n_0 ),
        .I2(\threshold_pipes[0].count_threshold[0][3]_i_9_n_0 ),
        .I3(\threshold_pipes[0].count_threshold[0][3]_i_10_n_0 ),
        .I4(\threshold_pipes[0].count_threshold[0][3]_i_11_n_0 ),
        .I5(\threshold_pipes[0].count_threshold[0][3]_i_12_n_0 ),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_3_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[0].count_threshold[0][3]_i_4 
       (.I0(\threshold_pipes[0].count_threshold[0][3]_i_13_n_0 ),
        .I1(\threshold_pipes[0].remainder_s6 [7]),
        .I2(\threshold_pipes[0].remainder_s6 [6]),
        .I3(\threshold_pipes[0].remainder_s6 [9]),
        .I4(\threshold_pipes[0].remainder_s6 [8]),
        .I5(\threshold_pipes[0].count_threshold[0][3]_i_14_n_0 ),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_4_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[0].count_threshold[0][3]_i_5 
       (.I0(\threshold_pipes[0].remainder_s6 [26]),
        .I1(\threshold_pipes[0].remainder_s6 [27]),
        .I2(\threshold_pipes[0].remainder_s6 [24]),
        .I3(\threshold_pipes[0].remainder_s6 [25]),
        .I4(\threshold_pipes[0].remainder_s6 [23]),
        .I5(\threshold_pipes[0].remainder_s6 [22]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_5_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[0].count_threshold[0][3]_i_6 
       (.I0(\threshold_pipes[0].remainder_s6 [20]),
        .I1(\threshold_pipes[0].remainder_s6 [21]),
        .I2(\threshold_pipes[0].remainder_s6 [18]),
        .I3(\threshold_pipes[0].remainder_s6 [19]),
        .I4(\threshold_pipes[0].remainder_s6 [17]),
        .I5(\threshold_pipes[0].remainder_s6 [16]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_6_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFF8)) 
    \threshold_pipes[0].count_threshold[0][3]_i_7 
       (.I0(\threshold_pipes[0].remainder_s6 [1]),
        .I1(\threshold_pipes[0].remainder_s6 [2]),
        .I2(\threshold_pipes[0].remainder_s6 [30]),
        .I3(\threshold_pipes[0].remainder_s6 [31]),
        .I4(\threshold_pipes[0].remainder_s6 [29]),
        .I5(\threshold_pipes[0].remainder_s6 [28]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_7_n_0 ));
  LUT4 #(
    .INIT(16'h22A8)) 
    \threshold_pipes[0].count_threshold[0][3]_i_8 
       (.I0(\threshold_pipes[0].count_threshold[0][3]_i_15_n_0 ),
        .I1(\threshold_pipes[0].remainder_s6 [2]),
        .I2(\threshold_pipes[0].remainder_s6 [0]),
        .I3(\threshold_pipes[0].remainder_s6 [1]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_8_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[0].count_threshold[0][3]_i_9 
       (.I0(\threshold_pipes[0].remainder_s6 [28]),
        .I1(\threshold_pipes[0].remainder_s6 [29]),
        .I2(\threshold_pipes[0].remainder_s6 [26]),
        .I3(\threshold_pipes[0].remainder_s6 [27]),
        .I4(\threshold_pipes[0].remainder_s6 [31]),
        .I5(\threshold_pipes[0].remainder_s6 [30]),
        .O(\threshold_pipes[0].count_threshold[0][3]_i_9_n_0 ));
  FDRE \threshold_pipes[0].count_threshold_reg[0][0] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[0]),
        .Q(meta_threshold1[0]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][10] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[10]),
        .Q(meta_threshold1[10]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][11] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[11]),
        .Q(meta_threshold1[11]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].count_threshold_reg[0][11]_i_1 
       (.CI(\threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_0 ),
        .CO({\threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_0 ,\threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_1 ,\threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_2 ,\threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(p_0_in1_in[11:8]),
        .S(\threshold_pipes[0].q_s6 [11:8]));
  FDRE \threshold_pipes[0].count_threshold_reg[0][12] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[12]),
        .Q(meta_threshold1[12]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][13] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[13]),
        .Q(meta_threshold1[13]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][14] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[14]),
        .Q(meta_threshold1[14]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][15] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[15]),
        .Q(meta_threshold1[15]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].count_threshold_reg[0][15]_i_1 
       (.CI(\threshold_pipes[0].count_threshold_reg[0][11]_i_1_n_0 ),
        .CO({\threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_0 ,\threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_1 ,\threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_2 ,\threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(p_0_in1_in[15:12]),
        .S(\threshold_pipes[0].q_s6 [15:12]));
  FDRE \threshold_pipes[0].count_threshold_reg[0][16] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[16]),
        .Q(meta_threshold1[16]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][17] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[17]),
        .Q(meta_threshold1[17]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][18] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[18]),
        .Q(meta_threshold1[18]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][19] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[19]),
        .Q(meta_threshold1[19]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].count_threshold_reg[0][19]_i_1 
       (.CI(\threshold_pipes[0].count_threshold_reg[0][15]_i_1_n_0 ),
        .CO({\threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_0 ,\threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_1 ,\threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_2 ,\threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(p_0_in1_in[19:16]),
        .S(\threshold_pipes[0].q_s6 [19:16]));
  FDRE \threshold_pipes[0].count_threshold_reg[0][1] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[1]),
        .Q(meta_threshold1[1]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][20] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[20]),
        .Q(meta_threshold1[20]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][21] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[21]),
        .Q(meta_threshold1[21]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][22] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[22]),
        .Q(meta_threshold1[22]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][23] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[23]),
        .Q(meta_threshold1[23]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].count_threshold_reg[0][23]_i_1 
       (.CI(\threshold_pipes[0].count_threshold_reg[0][19]_i_1_n_0 ),
        .CO({\threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_0 ,\threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_1 ,\threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_2 ,\threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(p_0_in1_in[23:20]),
        .S(\threshold_pipes[0].q_s6 [23:20]));
  FDRE \threshold_pipes[0].count_threshold_reg[0][24] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[24]),
        .Q(meta_threshold1[24]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][25] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[25]),
        .Q(meta_threshold1[25]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][26] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[26]),
        .Q(meta_threshold1[26]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][27] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[27]),
        .Q(meta_threshold1[27]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].count_threshold_reg[0][27]_i_1 
       (.CI(\threshold_pipes[0].count_threshold_reg[0][23]_i_1_n_0 ),
        .CO({\threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_0 ,\threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_1 ,\threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_2 ,\threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(p_0_in1_in[27:24]),
        .S(\threshold_pipes[0].q_s6 [27:24]));
  FDRE \threshold_pipes[0].count_threshold_reg[0][28] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[28]),
        .Q(meta_threshold1[28]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][29] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[29]),
        .Q(meta_threshold1[29]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][2] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[2]),
        .Q(meta_threshold1[2]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][30] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[30]),
        .Q(meta_threshold1[30]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][31] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[31]),
        .Q(meta_threshold1[31]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].count_threshold_reg[0][31]_i_1 
       (.CI(\threshold_pipes[0].count_threshold_reg[0][27]_i_1_n_0 ),
        .CO({p_0_in1_in[31],\NLW_threshold_pipes[0].count_threshold_reg[0][31]_i_1_CO_UNCONNECTED [2],\threshold_pipes[0].count_threshold_reg[0][31]_i_1_n_2 ,\threshold_pipes[0].count_threshold_reg[0][31]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_threshold_pipes[0].count_threshold_reg[0][31]_i_1_O_UNCONNECTED [3],p_0_in1_in[30:28]}),
        .S({1'b1,\threshold_pipes[0].q_s6 [30:28]}));
  FDRE \threshold_pipes[0].count_threshold_reg[0][3] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[3]),
        .Q(meta_threshold1[3]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].count_threshold_reg[0][3]_i_1 
       (.CI(1'b0),
        .CO({\threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_0 ,\threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_1 ,\threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_2 ,\threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,\threshold_pipes[0].q_s6 [1:0]}),
        .O(p_0_in1_in[3:0]),
        .S({\threshold_pipes[0].q_s6 [3:2],\threshold_pipes[0].count_threshold[0][3]_i_2_n_0 ,\threshold_pipes[0].count_threshold[0][3]_i_3_n_0 }));
  FDRE \threshold_pipes[0].count_threshold_reg[0][4] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[4]),
        .Q(meta_threshold1[4]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][5] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[5]),
        .Q(meta_threshold1[5]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][6] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[6]),
        .Q(meta_threshold1[6]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][7] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[7]),
        .Q(meta_threshold1[7]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].count_threshold_reg[0][7]_i_1 
       (.CI(\threshold_pipes[0].count_threshold_reg[0][3]_i_1_n_0 ),
        .CO({\threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_0 ,\threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_1 ,\threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_2 ,\threshold_pipes[0].count_threshold_reg[0][7]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(p_0_in1_in[7:4]),
        .S(\threshold_pipes[0].q_s6 [7:4]));
  FDRE \threshold_pipes[0].count_threshold_reg[0][8] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[8]),
        .Q(meta_threshold1[8]),
        .R(1'b0));
  FDRE \threshold_pipes[0].count_threshold_reg[0][9] 
       (.C(clk),
        .CE(p_0_in),
        .D(p_0_in1_in[9]),
        .Q(meta_threshold1[9]),
        .R(1'b0));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_10 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_97 ),
        .I1(\threshold_pipes[0].low_carry_s1 [8]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_10_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_12 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_98 ),
        .I1(\threshold_pipes[0].low_carry_s1 [7]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_12_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_13 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_99 ),
        .I1(\threshold_pipes[0].low_carry_s1 [6]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_13_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_14 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_100 ),
        .I1(\threshold_pipes[0].low_carry_s1 [5]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_14_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_15 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_101 ),
        .I1(\threshold_pipes[0].low_carry_s1 [4]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_15_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_16 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_102 ),
        .I1(\threshold_pipes[0].low_carry_s1 [3]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_16_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_17 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_103 ),
        .I1(\threshold_pipes[0].low_carry_s1 [2]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_17_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_18 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_104 ),
        .I1(\threshold_pipes[0].low_carry_s1 [1]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_18_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_19 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_105 ),
        .I1(\threshold_pipes[0].low_carry_s1 [0]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_19_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_4 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_92 ),
        .I1(\threshold_pipes[0].low_carry_s1 [13]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_5 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_93 ),
        .I1(\threshold_pipes[0].low_carry_s1 [12]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_7 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_94 ),
        .I1(\threshold_pipes[0].low_carry_s1 [11]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_7_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_8 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_95 ),
        .I1(\threshold_pipes[0].low_carry_s1 [10]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_8_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].cross_carry_s2[3]_i_9 
       (.I0(\threshold_pipes[0].cross_s1_reg_n_96 ),
        .I1(\threshold_pipes[0].low_carry_s1 [9]),
        .O(\threshold_pipes[0].cross_carry_s2[3]_i_9_n_0 ));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [16]),
        .Q(\threshold_pipes[0].cross_carry_s2 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [26]),
        .Q(\threshold_pipes[0].cross_carry_s2 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [27]),
        .Q(\threshold_pipes[0].cross_carry_s2 [11]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].cross_carry_s2_reg[11]_i_1 
       (.CI(\threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_0 ),
        .CO({\threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_0 ,\threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_1 ,\threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_2 ,\threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[0].cross_carry_s21 [27:24]),
        .S({\threshold_pipes[0].cross_s1_reg_n_78 ,\threshold_pipes[0].cross_s1_reg_n_79 ,\threshold_pipes[0].cross_s1_reg_n_80 ,\threshold_pipes[0].cross_s1_reg_n_81 }));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [28]),
        .Q(\threshold_pipes[0].cross_carry_s2 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [29]),
        .Q(\threshold_pipes[0].cross_carry_s2 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [30]),
        .Q(\threshold_pipes[0].cross_carry_s2 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [31]),
        .Q(\threshold_pipes[0].cross_carry_s2 [15]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].cross_carry_s2_reg[15]_i_1 
       (.CI(\threshold_pipes[0].cross_carry_s2_reg[11]_i_1_n_0 ),
        .CO({\threshold_pipes[0].cross_carry_s21 [31],\NLW_threshold_pipes[0].cross_carry_s2_reg[15]_i_1_CO_UNCONNECTED [2],\threshold_pipes[0].cross_carry_s2_reg[15]_i_1_n_2 ,\threshold_pipes[0].cross_carry_s2_reg[15]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_threshold_pipes[0].cross_carry_s2_reg[15]_i_1_O_UNCONNECTED [3],\threshold_pipes[0].cross_carry_s21 [30:28]}),
        .S({1'b1,\threshold_pipes[0].cross_s1_reg_n_75 ,\threshold_pipes[0].cross_s1_reg_n_76 ,\threshold_pipes[0].cross_s1_reg_n_77 }));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [17]),
        .Q(\threshold_pipes[0].cross_carry_s2 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [18]),
        .Q(\threshold_pipes[0].cross_carry_s2 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [19]),
        .Q(\threshold_pipes[0].cross_carry_s2 [3]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].cross_carry_s2_reg[3]_i_1 
       (.CI(\threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_0 ),
        .CO({\threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_0 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_1 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_2 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[0].cross_carry_s21 [19:16]),
        .S({\threshold_pipes[0].cross_s1_reg_n_86 ,\threshold_pipes[0].cross_s1_reg_n_87 ,\threshold_pipes[0].cross_s1_reg_n_88 ,\threshold_pipes[0].cross_s1_reg_n_89 }));
  CARRY4 \threshold_pipes[0].cross_carry_s2_reg[3]_i_11 
       (.CI(1'b0),
        .CO({\threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_0 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_1 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_2 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[0].cross_s1_reg_n_102 ,\threshold_pipes[0].cross_s1_reg_n_103 ,\threshold_pipes[0].cross_s1_reg_n_104 ,\threshold_pipes[0].cross_s1_reg_n_105 }),
        .O(\NLW_threshold_pipes[0].cross_carry_s2_reg[3]_i_11_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[0].cross_carry_s2[3]_i_16_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_17_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_18_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_19_n_0 }));
  CARRY4 \threshold_pipes[0].cross_carry_s2_reg[3]_i_2 
       (.CI(\threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_0 ),
        .CO({\threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_0 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_1 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_2 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,\threshold_pipes[0].cross_s1_reg_n_92 ,\threshold_pipes[0].cross_s1_reg_n_93 }),
        .O(\NLW_threshold_pipes[0].cross_carry_s2_reg[3]_i_2_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[0].cross_s1_reg_n_90 ,\threshold_pipes[0].cross_s1_reg_n_91 ,\threshold_pipes[0].cross_carry_s2[3]_i_4_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_5_n_0 }));
  CARRY4 \threshold_pipes[0].cross_carry_s2_reg[3]_i_3 
       (.CI(\threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_0 ),
        .CO({\threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_0 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_1 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_2 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_3_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[0].cross_s1_reg_n_94 ,\threshold_pipes[0].cross_s1_reg_n_95 ,\threshold_pipes[0].cross_s1_reg_n_96 ,\threshold_pipes[0].cross_s1_reg_n_97 }),
        .O(\NLW_threshold_pipes[0].cross_carry_s2_reg[3]_i_3_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[0].cross_carry_s2[3]_i_7_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_8_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_9_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_10_n_0 }));
  CARRY4 \threshold_pipes[0].cross_carry_s2_reg[3]_i_6 
       (.CI(\threshold_pipes[0].cross_carry_s2_reg[3]_i_11_n_0 ),
        .CO({\threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_0 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_1 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_2 ,\threshold_pipes[0].cross_carry_s2_reg[3]_i_6_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[0].cross_s1_reg_n_98 ,\threshold_pipes[0].cross_s1_reg_n_99 ,\threshold_pipes[0].cross_s1_reg_n_100 ,\threshold_pipes[0].cross_s1_reg_n_101 }),
        .O(\NLW_threshold_pipes[0].cross_carry_s2_reg[3]_i_6_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[0].cross_carry_s2[3]_i_12_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_13_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_14_n_0 ,\threshold_pipes[0].cross_carry_s2[3]_i_15_n_0 }));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [20]),
        .Q(\threshold_pipes[0].cross_carry_s2 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [21]),
        .Q(\threshold_pipes[0].cross_carry_s2 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [22]),
        .Q(\threshold_pipes[0].cross_carry_s2 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [23]),
        .Q(\threshold_pipes[0].cross_carry_s2 [7]),
        .R(1'b0));
  CARRY4 \threshold_pipes[0].cross_carry_s2_reg[7]_i_1 
       (.CI(\threshold_pipes[0].cross_carry_s2_reg[3]_i_1_n_0 ),
        .CO({\threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_0 ,\threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_1 ,\threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_2 ,\threshold_pipes[0].cross_carry_s2_reg[7]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[0].cross_carry_s21 [23:20]),
        .S({\threshold_pipes[0].cross_s1_reg_n_82 ,\threshold_pipes[0].cross_s1_reg_n_83 ,\threshold_pipes[0].cross_s1_reg_n_84 ,\threshold_pipes[0].cross_s1_reg_n_85 }));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [24]),
        .Q(\threshold_pipes[0].cross_carry_s2 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[0].cross_carry_s2_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].cross_carry_s21 [25]),
        .Q(\threshold_pipes[0].cross_carry_s2 [9]),
        .R(1'b0));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[0].cross_s1_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[31:16]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[0].cross_s1_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[0].cross_s1_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,partial_product_return__0}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[0].cross_s1_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[0].cross_s1_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b1),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[0].cross_s1_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b1,1'b1,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[0].cross_s1_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[0].cross_s1_reg_P_UNCONNECTED [47:31],\threshold_pipes[0].cross_s1_reg_n_75 ,\threshold_pipes[0].cross_s1_reg_n_76 ,\threshold_pipes[0].cross_s1_reg_n_77 ,\threshold_pipes[0].cross_s1_reg_n_78 ,\threshold_pipes[0].cross_s1_reg_n_79 ,\threshold_pipes[0].cross_s1_reg_n_80 ,\threshold_pipes[0].cross_s1_reg_n_81 ,\threshold_pipes[0].cross_s1_reg_n_82 ,\threshold_pipes[0].cross_s1_reg_n_83 ,\threshold_pipes[0].cross_s1_reg_n_84 ,\threshold_pipes[0].cross_s1_reg_n_85 ,\threshold_pipes[0].cross_s1_reg_n_86 ,\threshold_pipes[0].cross_s1_reg_n_87 ,\threshold_pipes[0].cross_s1_reg_n_88 ,\threshold_pipes[0].cross_s1_reg_n_89 ,\threshold_pipes[0].cross_s1_reg_n_90 ,\threshold_pipes[0].cross_s1_reg_n_91 ,\threshold_pipes[0].cross_s1_reg_n_92 ,\threshold_pipes[0].cross_s1_reg_n_93 ,\threshold_pipes[0].cross_s1_reg_n_94 ,\threshold_pipes[0].cross_s1_reg_n_95 ,\threshold_pipes[0].cross_s1_reg_n_96 ,\threshold_pipes[0].cross_s1_reg_n_97 ,\threshold_pipes[0].cross_s1_reg_n_98 ,\threshold_pipes[0].cross_s1_reg_n_99 ,\threshold_pipes[0].cross_s1_reg_n_100 ,\threshold_pipes[0].cross_s1_reg_n_101 ,\threshold_pipes[0].cross_s1_reg_n_102 ,\threshold_pipes[0].cross_s1_reg_n_103 ,\threshold_pipes[0].cross_s1_reg_n_104 ,\threshold_pipes[0].cross_s1_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[0].cross_s1_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[0].cross_s1_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[0].cross_s1_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[0].cross_s1_reg_UNDERFLOW_UNCONNECTED ));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[0].high_s1_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[31:16]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[0].high_s1_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1,1'b0,1'b0,1'b1,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[0].high_s1_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[0].high_s1_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[0].high_s1_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[0].high_s1_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[0].high_s1_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[0].high_s1_reg_P_UNCONNECTED [47:30],\threshold_pipes[0].high_s1_reg_n_76 ,\threshold_pipes[0].high_s1_reg_n_77 ,\threshold_pipes[0].high_s1_reg_n_78 ,\threshold_pipes[0].high_s1_reg_n_79 ,\threshold_pipes[0].high_s1_reg_n_80 ,\threshold_pipes[0].high_s1_reg_n_81 ,\threshold_pipes[0].high_s1_reg_n_82 ,\threshold_pipes[0].high_s1_reg_n_83 ,\threshold_pipes[0].high_s1_reg_n_84 ,\threshold_pipes[0].high_s1_reg_n_85 ,\threshold_pipes[0].high_s1_reg_n_86 ,\threshold_pipes[0].high_s1_reg_n_87 ,\threshold_pipes[0].high_s1_reg_n_88 ,\threshold_pipes[0].high_s1_reg_n_89 ,\threshold_pipes[0].high_s1_reg_n_90 ,\threshold_pipes[0].high_s1_reg_n_91 ,\threshold_pipes[0].high_s1_reg_n_92 ,\threshold_pipes[0].high_s1_reg_n_93 ,\threshold_pipes[0].high_s1_reg_n_94 ,\threshold_pipes[0].high_s1_reg_n_95 ,\threshold_pipes[0].high_s1_reg_n_96 ,\threshold_pipes[0].high_s1_reg_n_97 ,\threshold_pipes[0].high_s1_reg_n_98 ,\threshold_pipes[0].high_s1_reg_n_99 ,\threshold_pipes[0].high_s1_reg_n_100 ,\threshold_pipes[0].high_s1_reg_n_101 ,\threshold_pipes[0].high_s1_reg_n_102 ,\threshold_pipes[0].high_s1_reg_n_103 ,\threshold_pipes[0].high_s1_reg_n_104 ,\threshold_pipes[0].high_s1_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[0].high_s1_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[0].high_s1_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[0].high_s1_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[0].high_s1_reg_UNDERFLOW_UNCONNECTED ));
  FDRE \threshold_pipes[0].high_s2_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_105 ),
        .Q(\threshold_pipes[0].high_s2 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_95 ),
        .Q(\threshold_pipes[0].high_s2 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_94 ),
        .Q(\threshold_pipes[0].high_s2 [11]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_93 ),
        .Q(\threshold_pipes[0].high_s2 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_92 ),
        .Q(\threshold_pipes[0].high_s2 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_91 ),
        .Q(\threshold_pipes[0].high_s2 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_90 ),
        .Q(\threshold_pipes[0].high_s2 [15]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_89 ),
        .Q(\threshold_pipes[0].high_s2 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_88 ),
        .Q(\threshold_pipes[0].high_s2 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_87 ),
        .Q(\threshold_pipes[0].high_s2 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_86 ),
        .Q(\threshold_pipes[0].high_s2 [19]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_104 ),
        .Q(\threshold_pipes[0].high_s2 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_85 ),
        .Q(\threshold_pipes[0].high_s2 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_84 ),
        .Q(\threshold_pipes[0].high_s2 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_83 ),
        .Q(\threshold_pipes[0].high_s2 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_82 ),
        .Q(\threshold_pipes[0].high_s2 [23]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_81 ),
        .Q(\threshold_pipes[0].high_s2 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_80 ),
        .Q(\threshold_pipes[0].high_s2 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_79 ),
        .Q(\threshold_pipes[0].high_s2 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_78 ),
        .Q(\threshold_pipes[0].high_s2 [27]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_77 ),
        .Q(\threshold_pipes[0].high_s2 [28]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[29] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_76 ),
        .Q(\threshold_pipes[0].high_s2 [29]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_103 ),
        .Q(\threshold_pipes[0].high_s2 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_102 ),
        .Q(\threshold_pipes[0].high_s2 [3]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_101 ),
        .Q(\threshold_pipes[0].high_s2 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_100 ),
        .Q(\threshold_pipes[0].high_s2 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_99 ),
        .Q(\threshold_pipes[0].high_s2 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_98 ),
        .Q(\threshold_pipes[0].high_s2 [7]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_97 ),
        .Q(\threshold_pipes[0].high_s2 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[0].high_s2_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].high_s1_reg_n_96 ),
        .Q(\threshold_pipes[0].high_s2 [9]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [0]),
        .Q(\threshold_pipes[0].low_carry_s1 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [10]),
        .Q(\threshold_pipes[0].low_carry_s1 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [11]),
        .Q(\threshold_pipes[0].low_carry_s1 [11]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [12]),
        .Q(\threshold_pipes[0].low_carry_s1 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [13]),
        .Q(\threshold_pipes[0].low_carry_s1 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [1]),
        .Q(\threshold_pipes[0].low_carry_s1 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [2]),
        .Q(\threshold_pipes[0].low_carry_s1 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [3]),
        .Q(\threshold_pipes[0].low_carry_s1 [3]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [4]),
        .Q(\threshold_pipes[0].low_carry_s1 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [5]),
        .Q(\threshold_pipes[0].low_carry_s1 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [6]),
        .Q(\threshold_pipes[0].low_carry_s1 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [7]),
        .Q(\threshold_pipes[0].low_carry_s1 [7]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [8]),
        .Q(\threshold_pipes[0].low_carry_s1 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[0].low_carry_s1_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].mul00_hi [9]),
        .Q(\threshold_pipes[0].low_carry_s1 [9]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[16]),
        .Q(\threshold_pipes[0].mul00_hi [0]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[26]),
        .Q(\threshold_pipes[0].mul00_hi [10]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[27]),
        .Q(\threshold_pipes[0].mul00_hi [11]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[28]),
        .Q(\threshold_pipes[0].mul00_hi [12]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[29]),
        .Q(\threshold_pipes[0].mul00_hi [13]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[17]),
        .Q(\threshold_pipes[0].mul00_hi [1]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[18]),
        .Q(\threshold_pipes[0].mul00_hi [2]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[19]),
        .Q(\threshold_pipes[0].mul00_hi [3]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[20]),
        .Q(\threshold_pipes[0].mul00_hi [4]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[21]),
        .Q(\threshold_pipes[0].mul00_hi [5]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[22]),
        .Q(\threshold_pipes[0].mul00_hi [6]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[23]),
        .Q(\threshold_pipes[0].mul00_hi [7]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[24]),
        .Q(\threshold_pipes[0].mul00_hi [8]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[0].mul00_hi_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product_return__0[25]),
        .Q(\threshold_pipes[0].mul00_hi [9]),
        .R(1'b0));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][0]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][0]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[0]),
        .Q(\threshold_pipes[0].n_delay_reg[4][0]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][10]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][10]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[10]),
        .Q(\threshold_pipes[0].n_delay_reg[4][10]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][11]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][11]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[11]),
        .Q(\threshold_pipes[0].n_delay_reg[4][11]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][12]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][12]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[12]),
        .Q(\threshold_pipes[0].n_delay_reg[4][12]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][13]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][13]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[13]),
        .Q(\threshold_pipes[0].n_delay_reg[4][13]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][14]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][14]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[14]),
        .Q(\threshold_pipes[0].n_delay_reg[4][14]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][15]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][15]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[15]),
        .Q(\threshold_pipes[0].n_delay_reg[4][15]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][16]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][16]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[0]),
        .Q(\threshold_pipes[0].n_delay_reg[4][16]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][17]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][17]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[1]),
        .Q(\threshold_pipes[0].n_delay_reg[4][17]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][18]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][18]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[2]),
        .Q(\threshold_pipes[0].n_delay_reg[4][18]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][19]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][19]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[3]),
        .Q(\threshold_pipes[0].n_delay_reg[4][19]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][1]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][1]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[1]),
        .Q(\threshold_pipes[0].n_delay_reg[4][1]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][20]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][20]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[4]),
        .Q(\threshold_pipes[0].n_delay_reg[4][20]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][21]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][21]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[5]),
        .Q(\threshold_pipes[0].n_delay_reg[4][21]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][22]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][22]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[6]),
        .Q(\threshold_pipes[0].n_delay_reg[4][22]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][23]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][23]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[7]),
        .Q(\threshold_pipes[0].n_delay_reg[4][23]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][24]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][24]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[8]),
        .Q(\threshold_pipes[0].n_delay_reg[4][24]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][25]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][25]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[9]),
        .Q(\threshold_pipes[0].n_delay_reg[4][25]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][26]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][26]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[10]),
        .Q(\threshold_pipes[0].n_delay_reg[4][26]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][27]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][27]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[11]),
        .Q(\threshold_pipes[0].n_delay_reg[4][27]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][28]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][28]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[12]),
        .Q(\threshold_pipes[0].n_delay_reg[4][28]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][29]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][29]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[13]),
        .Q(\threshold_pipes[0].n_delay_reg[4][29]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][2]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][2]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[2]),
        .Q(\threshold_pipes[0].n_delay_reg[4][2]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][30]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][30]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[14]),
        .Q(\threshold_pipes[0].n_delay_reg[4][30]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][31]_srl5 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][31]_srl5 
       (.A0(1'b0),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(A[15]),
        .Q(\threshold_pipes[0].n_delay_reg[4][31]_srl5_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][3]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][3]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[3]),
        .Q(\threshold_pipes[0].n_delay_reg[4][3]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][4]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][4]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[4]),
        .Q(\threshold_pipes[0].n_delay_reg[4][4]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][5]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][5]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[5]),
        .Q(\threshold_pipes[0].n_delay_reg[4][5]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][6]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][6]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[6]),
        .Q(\threshold_pipes[0].n_delay_reg[4][6]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][7]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][7]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[7]),
        .Q(\threshold_pipes[0].n_delay_reg[4][7]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][8]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][8]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[8]),
        .Q(\threshold_pipes[0].n_delay_reg[4][8]_srl6_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].n_delay_reg[4] " *) 
  (* srl_name = "\\threshold_pipes[0].n_delay_reg[4][9]_srl6 " *) 
  SRL16E \threshold_pipes[0].n_delay_reg[4][9]_srl6 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(numerator[9]),
        .Q(\threshold_pipes[0].n_delay_reg[4][9]_srl6_n_0 ));
  FDRE \threshold_pipes[0].n_delay_reg[5][0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][0]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [0]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][10]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [10]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][11]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [11]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][12]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [12]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][13]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [13]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][14]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [14]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][15]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [15]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][16]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [16]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][17]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [17]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][18]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [18]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][19]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [19]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][1]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [1]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][20]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [20]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][21]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [21]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][22]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [22]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][23]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [23]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][24]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [24]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][25]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [25]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][26]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [26]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][27]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [27]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][28] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][28]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [28]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][29] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][29]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [29]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][2]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [2]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][30] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][30]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [30]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][31] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][31]_srl5_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [31]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][3]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [3]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][4]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [4]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][5]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [5]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][6]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [6]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][7]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [7]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][8]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [8]),
        .R(1'b0));
  FDRE \threshold_pipes[0].n_delay_reg[5][9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].n_delay_reg[4][9]_srl6_n_0 ),
        .Q(\threshold_pipes[0].n_delay_reg[5] [9]),
        .R(1'b0));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(0),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[0].product_s5_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[0].product_s5_reg_i_1_n_4 ,\threshold_pipes[0].product_s5_reg_i_1_n_5 ,\threshold_pipes[0].product_s5_reg_i_1_n_6 ,\threshold_pipes[0].product_s5_reg_i_1_n_7 ,\threshold_pipes[0].product_s5_reg_i_2_n_4 ,\threshold_pipes[0].product_s5_reg_i_2_n_5 ,\threshold_pipes[0].product_s5_reg_i_2_n_6 ,\threshold_pipes[0].product_s5_reg_i_2_n_7 ,\threshold_pipes[0].product_s5_reg_i_3_n_4 ,\threshold_pipes[0].product_s5_reg_i_3_n_5 ,\threshold_pipes[0].product_s5_reg_i_3_n_6 ,\threshold_pipes[0].product_s5_reg_i_3_n_7 ,\threshold_pipes[0].product_s5_reg_i_4_n_4 ,\threshold_pipes[0].product_s5_reg_i_4_n_5 ,\threshold_pipes[0].product_s5_reg_i_4_n_6 ,\threshold_pipes[0].product_s5_reg_i_4_n_7 }),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[0].product_s5_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[0].product_s5_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[0].check_hi_reg_n_90 ,\threshold_pipes[0].check_hi_reg_n_91 ,\threshold_pipes[0].check_hi_reg_n_92 ,\threshold_pipes[0].check_hi_reg_n_93 ,\threshold_pipes[0].check_hi_reg_n_94 ,\threshold_pipes[0].check_hi_reg_n_95 ,\threshold_pipes[0].check_hi_reg_n_96 ,\threshold_pipes[0].check_hi_reg_n_97 ,\threshold_pipes[0].check_hi_reg_n_98 ,\threshold_pipes[0].check_hi_reg_n_99 ,\threshold_pipes[0].check_hi_reg_n_100 ,\threshold_pipes[0].check_hi_reg_n_101 ,\threshold_pipes[0].check_hi_reg_n_102 ,\threshold_pipes[0].check_hi_reg_n_103 ,\threshold_pipes[0].check_hi_reg_n_104 ,\threshold_pipes[0].check_hi_reg_n_105 ,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[0].product_s5_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[0].product_s5_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[0].product_s5_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b1,1'b1,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[0].product_s5_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[0].product_s5_reg_P_UNCONNECTED [47:32],\threshold_pipes[0].product_s5_reg__0 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[0].product_s5_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[0].product_s5_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[0].product_s5_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[0].product_s5_reg_UNDERFLOW_UNCONNECTED ));
  CARRY4 \threshold_pipes[0].product_s5_reg_i_1 
       (.CI(\threshold_pipes[0].product_s5_reg_i_2_n_0 ),
        .CO({\threshold_pipes[0].product_s5_reg_i_1_n_0 ,\threshold_pipes[0].product_s5_reg_i_1_n_1 ,\threshold_pipes[0].product_s5_reg_i_1_n_2 ,\threshold_pipes[0].product_s5_reg_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].high_s2 [15:12]),
        .O({\threshold_pipes[0].product_s5_reg_i_1_n_4 ,\threshold_pipes[0].product_s5_reg_i_1_n_5 ,\threshold_pipes[0].product_s5_reg_i_1_n_6 ,\threshold_pipes[0].product_s5_reg_i_1_n_7 }),
        .S({\threshold_pipes[0].product_s5_reg_i_5_n_0 ,\threshold_pipes[0].product_s5_reg_i_6_n_0 ,\threshold_pipes[0].product_s5_reg_i_7_n_0 ,\threshold_pipes[0].product_s5_reg_i_8_n_0 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_10 
       (.I0(\threshold_pipes[0].high_s2 [10]),
        .I1(\threshold_pipes[0].cross_carry_s2 [10]),
        .O(\threshold_pipes[0].product_s5_reg_i_10_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_11 
       (.I0(\threshold_pipes[0].high_s2 [9]),
        .I1(\threshold_pipes[0].cross_carry_s2 [9]),
        .O(\threshold_pipes[0].product_s5_reg_i_11_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_12 
       (.I0(\threshold_pipes[0].high_s2 [8]),
        .I1(\threshold_pipes[0].cross_carry_s2 [8]),
        .O(\threshold_pipes[0].product_s5_reg_i_12_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_13 
       (.I0(\threshold_pipes[0].high_s2 [7]),
        .I1(\threshold_pipes[0].cross_carry_s2 [7]),
        .O(\threshold_pipes[0].product_s5_reg_i_13_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_14 
       (.I0(\threshold_pipes[0].high_s2 [6]),
        .I1(\threshold_pipes[0].cross_carry_s2 [6]),
        .O(\threshold_pipes[0].product_s5_reg_i_14_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_15 
       (.I0(\threshold_pipes[0].high_s2 [5]),
        .I1(\threshold_pipes[0].cross_carry_s2 [5]),
        .O(\threshold_pipes[0].product_s5_reg_i_15_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_16 
       (.I0(\threshold_pipes[0].high_s2 [4]),
        .I1(\threshold_pipes[0].cross_carry_s2 [4]),
        .O(\threshold_pipes[0].product_s5_reg_i_16_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_17 
       (.I0(\threshold_pipes[0].high_s2 [3]),
        .I1(\threshold_pipes[0].cross_carry_s2 [3]),
        .O(\threshold_pipes[0].product_s5_reg_i_17_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_18 
       (.I0(\threshold_pipes[0].high_s2 [2]),
        .I1(\threshold_pipes[0].cross_carry_s2 [2]),
        .O(\threshold_pipes[0].product_s5_reg_i_18_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_19 
       (.I0(\threshold_pipes[0].high_s2 [1]),
        .I1(\threshold_pipes[0].cross_carry_s2 [1]),
        .O(\threshold_pipes[0].product_s5_reg_i_19_n_0 ));
  CARRY4 \threshold_pipes[0].product_s5_reg_i_2 
       (.CI(\threshold_pipes[0].product_s5_reg_i_3_n_0 ),
        .CO({\threshold_pipes[0].product_s5_reg_i_2_n_0 ,\threshold_pipes[0].product_s5_reg_i_2_n_1 ,\threshold_pipes[0].product_s5_reg_i_2_n_2 ,\threshold_pipes[0].product_s5_reg_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].high_s2 [11:8]),
        .O({\threshold_pipes[0].product_s5_reg_i_2_n_4 ,\threshold_pipes[0].product_s5_reg_i_2_n_5 ,\threshold_pipes[0].product_s5_reg_i_2_n_6 ,\threshold_pipes[0].product_s5_reg_i_2_n_7 }),
        .S({\threshold_pipes[0].product_s5_reg_i_9_n_0 ,\threshold_pipes[0].product_s5_reg_i_10_n_0 ,\threshold_pipes[0].product_s5_reg_i_11_n_0 ,\threshold_pipes[0].product_s5_reg_i_12_n_0 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_20 
       (.I0(\threshold_pipes[0].high_s2 [0]),
        .I1(\threshold_pipes[0].cross_carry_s2 [0]),
        .O(\threshold_pipes[0].product_s5_reg_i_20_n_0 ));
  CARRY4 \threshold_pipes[0].product_s5_reg_i_3 
       (.CI(\threshold_pipes[0].product_s5_reg_i_4_n_0 ),
        .CO({\threshold_pipes[0].product_s5_reg_i_3_n_0 ,\threshold_pipes[0].product_s5_reg_i_3_n_1 ,\threshold_pipes[0].product_s5_reg_i_3_n_2 ,\threshold_pipes[0].product_s5_reg_i_3_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].high_s2 [7:4]),
        .O({\threshold_pipes[0].product_s5_reg_i_3_n_4 ,\threshold_pipes[0].product_s5_reg_i_3_n_5 ,\threshold_pipes[0].product_s5_reg_i_3_n_6 ,\threshold_pipes[0].product_s5_reg_i_3_n_7 }),
        .S({\threshold_pipes[0].product_s5_reg_i_13_n_0 ,\threshold_pipes[0].product_s5_reg_i_14_n_0 ,\threshold_pipes[0].product_s5_reg_i_15_n_0 ,\threshold_pipes[0].product_s5_reg_i_16_n_0 }));
  CARRY4 \threshold_pipes[0].product_s5_reg_i_4 
       (.CI(1'b0),
        .CO({\threshold_pipes[0].product_s5_reg_i_4_n_0 ,\threshold_pipes[0].product_s5_reg_i_4_n_1 ,\threshold_pipes[0].product_s5_reg_i_4_n_2 ,\threshold_pipes[0].product_s5_reg_i_4_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].high_s2 [3:0]),
        .O({\threshold_pipes[0].product_s5_reg_i_4_n_4 ,\threshold_pipes[0].product_s5_reg_i_4_n_5 ,\threshold_pipes[0].product_s5_reg_i_4_n_6 ,\threshold_pipes[0].product_s5_reg_i_4_n_7 }),
        .S({\threshold_pipes[0].product_s5_reg_i_17_n_0 ,\threshold_pipes[0].product_s5_reg_i_18_n_0 ,\threshold_pipes[0].product_s5_reg_i_19_n_0 ,\threshold_pipes[0].product_s5_reg_i_20_n_0 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_5 
       (.I0(\threshold_pipes[0].high_s2 [15]),
        .I1(\threshold_pipes[0].cross_carry_s2 [15]),
        .O(\threshold_pipes[0].product_s5_reg_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_6 
       (.I0(\threshold_pipes[0].high_s2 [14]),
        .I1(\threshold_pipes[0].cross_carry_s2 [14]),
        .O(\threshold_pipes[0].product_s5_reg_i_6_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_7 
       (.I0(\threshold_pipes[0].high_s2 [13]),
        .I1(\threshold_pipes[0].cross_carry_s2 [13]),
        .O(\threshold_pipes[0].product_s5_reg_i_7_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_8 
       (.I0(\threshold_pipes[0].high_s2 [12]),
        .I1(\threshold_pipes[0].cross_carry_s2 [12]),
        .O(\threshold_pipes[0].product_s5_reg_i_8_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[0].product_s5_reg_i_9 
       (.I0(\threshold_pipes[0].high_s2 [11]),
        .I1(\threshold_pipes[0].cross_carry_s2 [11]),
        .O(\threshold_pipes[0].product_s5_reg_i_9_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[0]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[0]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_4_n_7 ),
        .Q(\threshold_pipes[0].q_s5_reg[0]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[10]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[10]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_2_n_5 ),
        .Q(\threshold_pipes[0].q_s5_reg[10]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[11]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[11]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_2_n_4 ),
        .Q(\threshold_pipes[0].q_s5_reg[11]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[12]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[12]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_1_n_7 ),
        .Q(\threshold_pipes[0].q_s5_reg[12]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[13]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[13]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_1_n_6 ),
        .Q(\threshold_pipes[0].q_s5_reg[13]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[14]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[14]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_1_n_5 ),
        .Q(\threshold_pipes[0].q_s5_reg[14]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[15]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[15]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_1_n_4 ),
        .Q(\threshold_pipes[0].q_s5_reg[15]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[16]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[16]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_4_n_7 ),
        .Q(\threshold_pipes[0].q_s5_reg[16]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[17]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[17]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_4_n_6 ),
        .Q(\threshold_pipes[0].q_s5_reg[17]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[18]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[18]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_4_n_5 ),
        .Q(\threshold_pipes[0].q_s5_reg[18]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[19]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[19]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_4_n_4 ),
        .Q(\threshold_pipes[0].q_s5_reg[19]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[1]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[1]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_4_n_6 ),
        .Q(\threshold_pipes[0].q_s5_reg[1]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[20]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[20]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_3_n_7 ),
        .Q(\threshold_pipes[0].q_s5_reg[20]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[21]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[21]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_3_n_6 ),
        .Q(\threshold_pipes[0].q_s5_reg[21]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[22]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[22]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_3_n_5 ),
        .Q(\threshold_pipes[0].q_s5_reg[22]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[23]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[23]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_3_n_4 ),
        .Q(\threshold_pipes[0].q_s5_reg[23]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[24]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[24]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_2_n_7 ),
        .Q(\threshold_pipes[0].q_s5_reg[24]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[25]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[25]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_2_n_6 ),
        .Q(\threshold_pipes[0].q_s5_reg[25]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[26]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[26]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_2_n_5 ),
        .Q(\threshold_pipes[0].q_s5_reg[26]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[27]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[27]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_2_n_4 ),
        .Q(\threshold_pipes[0].q_s5_reg[27]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[28]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[28]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_1_n_7 ),
        .Q(\threshold_pipes[0].q_s5_reg[28]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[29]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[29]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_1_n_6 ),
        .Q(\threshold_pipes[0].q_s5_reg[29]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[2]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[2]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_4_n_5 ),
        .Q(\threshold_pipes[0].q_s5_reg[2]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[30]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[30]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].check_hi_reg_i_1_n_1 ),
        .Q(\threshold_pipes[0].q_s5_reg[30]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[3]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[3]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_4_n_4 ),
        .Q(\threshold_pipes[0].q_s5_reg[3]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[4]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[4]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_3_n_7 ),
        .Q(\threshold_pipes[0].q_s5_reg[4]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[5]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[5]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_3_n_6 ),
        .Q(\threshold_pipes[0].q_s5_reg[5]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[6]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[6]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_3_n_5 ),
        .Q(\threshold_pipes[0].q_s5_reg[6]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[7]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[7]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_3_n_4 ),
        .Q(\threshold_pipes[0].q_s5_reg[7]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[8]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[8]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_2_n_7 ),
        .Q(\threshold_pipes[0].q_s5_reg[8]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[0].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[0].q_s5_reg[9]_srl3 " *) 
  SRL16E \threshold_pipes[0].q_s5_reg[9]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[0].product_s5_reg_i_2_n_6 ),
        .Q(\threshold_pipes[0].q_s5_reg[9]_srl3_n_0 ));
  FDRE \threshold_pipes[0].q_s6_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[0]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[10]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[11]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [11]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[12]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[13]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[14]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[15]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [15]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[16]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[17]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[18]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[19]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [19]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[1]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[20]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[21]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[22]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[23]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [23]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[24]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[25]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[26]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[27]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [27]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[28]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [28]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[29] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[29]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [29]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[2]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[30] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[30]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [30]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[3]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [3]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[4]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[5]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[6]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[7]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [7]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[8]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[0].q_s6_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].q_s5_reg[9]_srl3_n_0 ),
        .Q(\threshold_pipes[0].q_s6 [9]),
        .R(1'b0));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[11]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [11]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [11]),
        .O(\threshold_pipes[0].remainder_s6[11]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[11]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [10]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [10]),
        .O(\threshold_pipes[0].remainder_s6[11]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[11]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [9]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [9]),
        .O(\threshold_pipes[0].remainder_s6[11]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[11]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [8]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [8]),
        .O(\threshold_pipes[0].remainder_s6[11]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[15]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [15]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [15]),
        .O(\threshold_pipes[0].remainder_s6[15]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[15]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [14]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [14]),
        .O(\threshold_pipes[0].remainder_s6[15]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[15]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [13]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [13]),
        .O(\threshold_pipes[0].remainder_s6[15]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[15]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [12]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [12]),
        .O(\threshold_pipes[0].remainder_s6[15]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[19]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [19]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [19]),
        .O(\threshold_pipes[0].remainder_s6[19]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[19]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [18]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [18]),
        .O(\threshold_pipes[0].remainder_s6[19]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[19]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [17]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [17]),
        .O(\threshold_pipes[0].remainder_s6[19]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[19]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [16]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [16]),
        .O(\threshold_pipes[0].remainder_s6[19]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[23]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [23]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [23]),
        .O(\threshold_pipes[0].remainder_s6[23]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[23]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [22]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [22]),
        .O(\threshold_pipes[0].remainder_s6[23]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[23]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [21]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [21]),
        .O(\threshold_pipes[0].remainder_s6[23]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[23]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [20]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [20]),
        .O(\threshold_pipes[0].remainder_s6[23]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[27]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [27]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [27]),
        .O(\threshold_pipes[0].remainder_s6[27]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[27]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [26]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [26]),
        .O(\threshold_pipes[0].remainder_s6[27]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[27]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [25]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [25]),
        .O(\threshold_pipes[0].remainder_s6[27]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[27]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [24]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [24]),
        .O(\threshold_pipes[0].remainder_s6[27]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[31]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [31]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [31]),
        .O(\threshold_pipes[0].remainder_s6[31]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[31]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [30]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [30]),
        .O(\threshold_pipes[0].remainder_s6[31]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[31]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [29]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [29]),
        .O(\threshold_pipes[0].remainder_s6[31]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[31]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [28]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [28]),
        .O(\threshold_pipes[0].remainder_s6[31]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[3]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [3]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [3]),
        .O(\threshold_pipes[0].remainder_s6[3]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[3]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [2]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [2]),
        .O(\threshold_pipes[0].remainder_s6[3]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[3]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [1]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [1]),
        .O(\threshold_pipes[0].remainder_s6[3]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[3]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [0]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [0]),
        .O(\threshold_pipes[0].remainder_s6[3]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[7]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [7]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [7]),
        .O(\threshold_pipes[0].remainder_s6[7]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[7]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [6]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [6]),
        .O(\threshold_pipes[0].remainder_s6[7]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[7]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [5]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [5]),
        .O(\threshold_pipes[0].remainder_s6[7]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[0].remainder_s6[7]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [4]),
        .I1(\threshold_pipes[0].product_s5_reg__0 [4]),
        .O(\threshold_pipes[0].remainder_s6[7]_i_5_n_0 ));
  FDRE \threshold_pipes[0].remainder_s6_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [0]),
        .Q(\threshold_pipes[0].remainder_s6 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [10]),
        .Q(\threshold_pipes[0].remainder_s6 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [11]),
        .Q(\threshold_pipes[0].remainder_s6 [11]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[0].remainder_s6_reg[11]_i_1 
       (.CI(\threshold_pipes[0].remainder_s6_reg[7]_i_1_n_0 ),
        .CO({\threshold_pipes[0].remainder_s6_reg[11]_i_1_n_0 ,\threshold_pipes[0].remainder_s6_reg[11]_i_1_n_1 ,\threshold_pipes[0].remainder_s6_reg[11]_i_1_n_2 ,\threshold_pipes[0].remainder_s6_reg[11]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [11:8]),
        .O(\threshold_pipes[0].remainder_s602_out [11:8]),
        .S({\threshold_pipes[0].remainder_s6[11]_i_2_n_0 ,\threshold_pipes[0].remainder_s6[11]_i_3_n_0 ,\threshold_pipes[0].remainder_s6[11]_i_4_n_0 ,\threshold_pipes[0].remainder_s6[11]_i_5_n_0 }));
  FDRE \threshold_pipes[0].remainder_s6_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [12]),
        .Q(\threshold_pipes[0].remainder_s6 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [13]),
        .Q(\threshold_pipes[0].remainder_s6 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [14]),
        .Q(\threshold_pipes[0].remainder_s6 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [15]),
        .Q(\threshold_pipes[0].remainder_s6 [15]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[0].remainder_s6_reg[15]_i_1 
       (.CI(\threshold_pipes[0].remainder_s6_reg[11]_i_1_n_0 ),
        .CO({\threshold_pipes[0].remainder_s6_reg[15]_i_1_n_0 ,\threshold_pipes[0].remainder_s6_reg[15]_i_1_n_1 ,\threshold_pipes[0].remainder_s6_reg[15]_i_1_n_2 ,\threshold_pipes[0].remainder_s6_reg[15]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [15:12]),
        .O(\threshold_pipes[0].remainder_s602_out [15:12]),
        .S({\threshold_pipes[0].remainder_s6[15]_i_2_n_0 ,\threshold_pipes[0].remainder_s6[15]_i_3_n_0 ,\threshold_pipes[0].remainder_s6[15]_i_4_n_0 ,\threshold_pipes[0].remainder_s6[15]_i_5_n_0 }));
  FDRE \threshold_pipes[0].remainder_s6_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [16]),
        .Q(\threshold_pipes[0].remainder_s6 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [17]),
        .Q(\threshold_pipes[0].remainder_s6 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [18]),
        .Q(\threshold_pipes[0].remainder_s6 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [19]),
        .Q(\threshold_pipes[0].remainder_s6 [19]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[0].remainder_s6_reg[19]_i_1 
       (.CI(\threshold_pipes[0].remainder_s6_reg[15]_i_1_n_0 ),
        .CO({\threshold_pipes[0].remainder_s6_reg[19]_i_1_n_0 ,\threshold_pipes[0].remainder_s6_reg[19]_i_1_n_1 ,\threshold_pipes[0].remainder_s6_reg[19]_i_1_n_2 ,\threshold_pipes[0].remainder_s6_reg[19]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [19:16]),
        .O(\threshold_pipes[0].remainder_s602_out [19:16]),
        .S({\threshold_pipes[0].remainder_s6[19]_i_2_n_0 ,\threshold_pipes[0].remainder_s6[19]_i_3_n_0 ,\threshold_pipes[0].remainder_s6[19]_i_4_n_0 ,\threshold_pipes[0].remainder_s6[19]_i_5_n_0 }));
  FDRE \threshold_pipes[0].remainder_s6_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [1]),
        .Q(\threshold_pipes[0].remainder_s6 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [20]),
        .Q(\threshold_pipes[0].remainder_s6 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [21]),
        .Q(\threshold_pipes[0].remainder_s6 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [22]),
        .Q(\threshold_pipes[0].remainder_s6 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [23]),
        .Q(\threshold_pipes[0].remainder_s6 [23]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[0].remainder_s6_reg[23]_i_1 
       (.CI(\threshold_pipes[0].remainder_s6_reg[19]_i_1_n_0 ),
        .CO({\threshold_pipes[0].remainder_s6_reg[23]_i_1_n_0 ,\threshold_pipes[0].remainder_s6_reg[23]_i_1_n_1 ,\threshold_pipes[0].remainder_s6_reg[23]_i_1_n_2 ,\threshold_pipes[0].remainder_s6_reg[23]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [23:20]),
        .O(\threshold_pipes[0].remainder_s602_out [23:20]),
        .S({\threshold_pipes[0].remainder_s6[23]_i_2_n_0 ,\threshold_pipes[0].remainder_s6[23]_i_3_n_0 ,\threshold_pipes[0].remainder_s6[23]_i_4_n_0 ,\threshold_pipes[0].remainder_s6[23]_i_5_n_0 }));
  FDRE \threshold_pipes[0].remainder_s6_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [24]),
        .Q(\threshold_pipes[0].remainder_s6 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [25]),
        .Q(\threshold_pipes[0].remainder_s6 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [26]),
        .Q(\threshold_pipes[0].remainder_s6 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [27]),
        .Q(\threshold_pipes[0].remainder_s6 [27]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[0].remainder_s6_reg[27]_i_1 
       (.CI(\threshold_pipes[0].remainder_s6_reg[23]_i_1_n_0 ),
        .CO({\threshold_pipes[0].remainder_s6_reg[27]_i_1_n_0 ,\threshold_pipes[0].remainder_s6_reg[27]_i_1_n_1 ,\threshold_pipes[0].remainder_s6_reg[27]_i_1_n_2 ,\threshold_pipes[0].remainder_s6_reg[27]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [27:24]),
        .O(\threshold_pipes[0].remainder_s602_out [27:24]),
        .S({\threshold_pipes[0].remainder_s6[27]_i_2_n_0 ,\threshold_pipes[0].remainder_s6[27]_i_3_n_0 ,\threshold_pipes[0].remainder_s6[27]_i_4_n_0 ,\threshold_pipes[0].remainder_s6[27]_i_5_n_0 }));
  FDRE \threshold_pipes[0].remainder_s6_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [28]),
        .Q(\threshold_pipes[0].remainder_s6 [28]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[29] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [29]),
        .Q(\threshold_pipes[0].remainder_s6 [29]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [2]),
        .Q(\threshold_pipes[0].remainder_s6 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[30] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [30]),
        .Q(\threshold_pipes[0].remainder_s6 [30]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[31] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [31]),
        .Q(\threshold_pipes[0].remainder_s6 [31]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[0].remainder_s6_reg[31]_i_1 
       (.CI(\threshold_pipes[0].remainder_s6_reg[27]_i_1_n_0 ),
        .CO({\NLW_threshold_pipes[0].remainder_s6_reg[31]_i_1_CO_UNCONNECTED [3],\threshold_pipes[0].remainder_s6_reg[31]_i_1_n_1 ,\threshold_pipes[0].remainder_s6_reg[31]_i_1_n_2 ,\threshold_pipes[0].remainder_s6_reg[31]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,\threshold_pipes[0].n_delay_reg[5] [30:28]}),
        .O(\threshold_pipes[0].remainder_s602_out [31:28]),
        .S({\threshold_pipes[0].remainder_s6[31]_i_2_n_0 ,\threshold_pipes[0].remainder_s6[31]_i_3_n_0 ,\threshold_pipes[0].remainder_s6[31]_i_4_n_0 ,\threshold_pipes[0].remainder_s6[31]_i_5_n_0 }));
  FDRE \threshold_pipes[0].remainder_s6_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [3]),
        .Q(\threshold_pipes[0].remainder_s6 [3]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[0].remainder_s6_reg[3]_i_1 
       (.CI(1'b0),
        .CO({\threshold_pipes[0].remainder_s6_reg[3]_i_1_n_0 ,\threshold_pipes[0].remainder_s6_reg[3]_i_1_n_1 ,\threshold_pipes[0].remainder_s6_reg[3]_i_1_n_2 ,\threshold_pipes[0].remainder_s6_reg[3]_i_1_n_3 }),
        .CYINIT(1'b1),
        .DI(\threshold_pipes[0].n_delay_reg[5] [3:0]),
        .O(\threshold_pipes[0].remainder_s602_out [3:0]),
        .S({\threshold_pipes[0].remainder_s6[3]_i_2_n_0 ,\threshold_pipes[0].remainder_s6[3]_i_3_n_0 ,\threshold_pipes[0].remainder_s6[3]_i_4_n_0 ,\threshold_pipes[0].remainder_s6[3]_i_5_n_0 }));
  FDRE \threshold_pipes[0].remainder_s6_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [4]),
        .Q(\threshold_pipes[0].remainder_s6 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [5]),
        .Q(\threshold_pipes[0].remainder_s6 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [6]),
        .Q(\threshold_pipes[0].remainder_s6 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [7]),
        .Q(\threshold_pipes[0].remainder_s6 [7]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[0].remainder_s6_reg[7]_i_1 
       (.CI(\threshold_pipes[0].remainder_s6_reg[3]_i_1_n_0 ),
        .CO({\threshold_pipes[0].remainder_s6_reg[7]_i_1_n_0 ,\threshold_pipes[0].remainder_s6_reg[7]_i_1_n_1 ,\threshold_pipes[0].remainder_s6_reg[7]_i_1_n_2 ,\threshold_pipes[0].remainder_s6_reg[7]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [7:4]),
        .O(\threshold_pipes[0].remainder_s602_out [7:4]),
        .S({\threshold_pipes[0].remainder_s6[7]_i_2_n_0 ,\threshold_pipes[0].remainder_s6[7]_i_3_n_0 ,\threshold_pipes[0].remainder_s6[7]_i_4_n_0 ,\threshold_pipes[0].remainder_s6[7]_i_5_n_0 }));
  FDRE \threshold_pipes[0].remainder_s6_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [8]),
        .Q(\threshold_pipes[0].remainder_s6 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[0].remainder_s6_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].remainder_s602_out [9]),
        .Q(\threshold_pipes[0].remainder_s6 [9]),
        .R(1'b0));
  LUT2 #(
    .INIT(4'hE)) 
    \threshold_pipes[0].threshold_live[0]_i_1 
       (.I0(p_0_in),
        .I1(live[0]),
        .O(\threshold_pipes[0].threshold_live[0]_i_1_n_0 ));
  FDRE \threshold_pipes[0].threshold_live_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].threshold_live[0]_i_1_n_0 ),
        .Q(live[0]),
        .R(reset));
  (* srl_bus_name = "\\threshold_pipes[0].valid_pipe_reg " *) 
  (* srl_name = "\\threshold_pipes[0].valid_pipe_reg[5]_srl6___threshold_pipes_r_4 " *) 
  SRL16E \threshold_pipes[0].valid_pipe_reg[5]_srl6___threshold_pipes_r_4 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(p_1_out),
        .Q(\threshold_pipes[0].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair1" *) 
  LUT3 #(
    .INIT(8'h02)) 
    \threshold_pipes[0].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1 
       (.I0(take),
        .I1(selected[1]),
        .I2(selected[0]),
        .O(p_1_out));
  FDRE \threshold_pipes[0].valid_pipe_reg[6]_threshold_pipes_r_5 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[0].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ),
        .Q(\threshold_pipes[0].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ),
        .R(1'b0));
  FDRE \threshold_pipes[0].valid_pipe_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_gate_n_0),
        .Q(p_0_in),
        .R(reset));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(0),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(0),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[1].check_hi_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[1].check_hi_reg_i_1_n_2 ,\threshold_pipes[1].check_hi_reg_i_1_n_7 ,\threshold_pipes[1].check_hi_reg_i_2_n_4 ,\threshold_pipes[1].check_hi_reg_i_2_n_5 ,\threshold_pipes[1].check_hi_reg_i_2_n_6 ,\threshold_pipes[1].check_hi_reg_i_2_n_7 ,\threshold_pipes[1].check_hi_reg_i_3_n_4 ,\threshold_pipes[1].check_hi_reg_i_3_n_5 ,\threshold_pipes[1].check_hi_reg_i_3_n_6 ,\threshold_pipes[1].check_hi_reg_i_3_n_7 ,\threshold_pipes[1].check_hi_reg_i_4_n_4 ,\threshold_pipes[1].check_hi_reg_i_4_n_5 ,\threshold_pipes[1].check_hi_reg_i_4_n_6 ,\threshold_pipes[1].check_hi_reg_i_4_n_7 }),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[1].check_hi_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b1,1'b1,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[1].check_hi_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[1].check_hi_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[1].check_hi_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b0),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[1].check_hi_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[1].check_hi_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[1].check_hi_reg_P_UNCONNECTED [47:16],\threshold_pipes[1].check_hi_reg_n_90 ,\threshold_pipes[1].check_hi_reg_n_91 ,\threshold_pipes[1].check_hi_reg_n_92 ,\threshold_pipes[1].check_hi_reg_n_93 ,\threshold_pipes[1].check_hi_reg_n_94 ,\threshold_pipes[1].check_hi_reg_n_95 ,\threshold_pipes[1].check_hi_reg_n_96 ,\threshold_pipes[1].check_hi_reg_n_97 ,\threshold_pipes[1].check_hi_reg_n_98 ,\threshold_pipes[1].check_hi_reg_n_99 ,\threshold_pipes[1].check_hi_reg_n_100 ,\threshold_pipes[1].check_hi_reg_n_101 ,\threshold_pipes[1].check_hi_reg_n_102 ,\threshold_pipes[1].check_hi_reg_n_103 ,\threshold_pipes[1].check_hi_reg_n_104 ,\threshold_pipes[1].check_hi_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[1].check_hi_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[1].check_hi_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[1].check_hi_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[1].check_hi_reg_UNDERFLOW_UNCONNECTED ));
  CARRY4 \threshold_pipes[1].check_hi_reg_i_1 
       (.CI(\threshold_pipes[1].check_hi_reg_i_2_n_0 ),
        .CO({\NLW_threshold_pipes[1].check_hi_reg_i_1_CO_UNCONNECTED [3:2],\threshold_pipes[1].check_hi_reg_i_1_n_2 ,\NLW_threshold_pipes[1].check_hi_reg_i_1_CO_UNCONNECTED [0]}),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_threshold_pipes[1].check_hi_reg_i_1_O_UNCONNECTED [3:1],\threshold_pipes[1].check_hi_reg_i_1_n_7 }),
        .S({1'b0,1'b0,1'b1,\threshold_pipes[1].high_s2 [28]}));
  CARRY4 \threshold_pipes[1].check_hi_reg_i_2 
       (.CI(\threshold_pipes[1].check_hi_reg_i_3_n_0 ),
        .CO({\threshold_pipes[1].check_hi_reg_i_2_n_0 ,\threshold_pipes[1].check_hi_reg_i_2_n_1 ,\threshold_pipes[1].check_hi_reg_i_2_n_2 ,\threshold_pipes[1].check_hi_reg_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].check_hi_reg_i_2_n_4 ,\threshold_pipes[1].check_hi_reg_i_2_n_5 ,\threshold_pipes[1].check_hi_reg_i_2_n_6 ,\threshold_pipes[1].check_hi_reg_i_2_n_7 }),
        .S(\threshold_pipes[1].high_s2 [27:24]));
  CARRY4 \threshold_pipes[1].check_hi_reg_i_3 
       (.CI(\threshold_pipes[1].check_hi_reg_i_4_n_0 ),
        .CO({\threshold_pipes[1].check_hi_reg_i_3_n_0 ,\threshold_pipes[1].check_hi_reg_i_3_n_1 ,\threshold_pipes[1].check_hi_reg_i_3_n_2 ,\threshold_pipes[1].check_hi_reg_i_3_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].check_hi_reg_i_3_n_4 ,\threshold_pipes[1].check_hi_reg_i_3_n_5 ,\threshold_pipes[1].check_hi_reg_i_3_n_6 ,\threshold_pipes[1].check_hi_reg_i_3_n_7 }),
        .S(\threshold_pipes[1].high_s2 [23:20]));
  CARRY4 \threshold_pipes[1].check_hi_reg_i_4 
       (.CI(\threshold_pipes[1].product_s5_reg_i_1_n_0 ),
        .CO({\threshold_pipes[1].check_hi_reg_i_4_n_0 ,\threshold_pipes[1].check_hi_reg_i_4_n_1 ,\threshold_pipes[1].check_hi_reg_i_4_n_2 ,\threshold_pipes[1].check_hi_reg_i_4_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].check_hi_reg_i_4_n_4 ,\threshold_pipes[1].check_hi_reg_i_4_n_5 ,\threshold_pipes[1].check_hi_reg_i_4_n_6 ,\threshold_pipes[1].check_hi_reg_i_4_n_7 }),
        .S(\threshold_pipes[1].high_s2 [19:16]));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[1].count_threshold[1][3]_i_10 
       (.I0(\threshold_pipes[1].remainder_s6 [16]),
        .I1(\threshold_pipes[1].remainder_s6 [17]),
        .I2(\threshold_pipes[1].remainder_s6 [14]),
        .I3(\threshold_pipes[1].remainder_s6 [15]),
        .I4(\threshold_pipes[1].remainder_s6 [19]),
        .I5(\threshold_pipes[1].remainder_s6 [18]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_10_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[1].count_threshold[1][3]_i_11 
       (.I0(\threshold_pipes[1].remainder_s6 [22]),
        .I1(\threshold_pipes[1].remainder_s6 [23]),
        .I2(\threshold_pipes[1].remainder_s6 [20]),
        .I3(\threshold_pipes[1].remainder_s6 [21]),
        .I4(\threshold_pipes[1].remainder_s6 [25]),
        .I5(\threshold_pipes[1].remainder_s6 [24]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_11_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[1].count_threshold[1][3]_i_12 
       (.I0(\threshold_pipes[1].remainder_s6 [28]),
        .I1(\threshold_pipes[1].remainder_s6 [29]),
        .I2(\threshold_pipes[1].remainder_s6 [26]),
        .I3(\threshold_pipes[1].remainder_s6 [27]),
        .I4(\threshold_pipes[1].remainder_s6 [31]),
        .I5(\threshold_pipes[1].remainder_s6 [30]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_12_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[1].count_threshold[1][3]_i_13 
       (.I0(\threshold_pipes[1].remainder_s6 [10]),
        .I1(\threshold_pipes[1].remainder_s6 [11]),
        .I2(\threshold_pipes[1].remainder_s6 [8]),
        .I3(\threshold_pipes[1].remainder_s6 [9]),
        .I4(\threshold_pipes[1].remainder_s6 [13]),
        .I5(\threshold_pipes[1].remainder_s6 [12]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_13_n_0 ));
  LUT6 #(
    .INIT(64'h5555555555555556)) 
    \threshold_pipes[1].count_threshold[1][3]_i_2 
       (.I0(\threshold_pipes[1].q_s6 [1]),
        .I1(\threshold_pipes[1].count_threshold[1][3]_i_4_n_0 ),
        .I2(\threshold_pipes[1].count_threshold[1][3]_i_5_n_0 ),
        .I3(\threshold_pipes[1].count_threshold[1][3]_i_6_n_0 ),
        .I4(\threshold_pipes[1].count_threshold[1][3]_i_7_n_0 ),
        .I5(\threshold_pipes[1].count_threshold[1][3]_i_8_n_0 ),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_2_n_0 ));
  LUT5 #(
    .INIT(32'h6AAAAAAA)) 
    \threshold_pipes[1].count_threshold[1][3]_i_3 
       (.I0(\threshold_pipes[1].q_s6 [0]),
        .I1(\threshold_pipes[1].count_threshold[1][3]_i_9_n_0 ),
        .I2(\threshold_pipes[1].count_threshold[1][3]_i_10_n_0 ),
        .I3(\threshold_pipes[1].count_threshold[1][3]_i_11_n_0 ),
        .I4(\threshold_pipes[1].count_threshold[1][3]_i_12_n_0 ),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_3_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \threshold_pipes[1].count_threshold[1][3]_i_4 
       (.I0(\threshold_pipes[1].remainder_s6 [5]),
        .I1(\threshold_pipes[1].remainder_s6 [4]),
        .I2(\threshold_pipes[1].remainder_s6 [7]),
        .I3(\threshold_pipes[1].remainder_s6 [6]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_4_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[1].count_threshold[1][3]_i_5 
       (.I0(\threshold_pipes[1].remainder_s6 [30]),
        .I1(\threshold_pipes[1].remainder_s6 [31]),
        .I2(\threshold_pipes[1].remainder_s6 [28]),
        .I3(\threshold_pipes[1].remainder_s6 [29]),
        .I4(\threshold_pipes[1].remainder_s6 [27]),
        .I5(\threshold_pipes[1].remainder_s6 [26]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_5_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[1].count_threshold[1][3]_i_6 
       (.I0(\threshold_pipes[1].remainder_s6 [24]),
        .I1(\threshold_pipes[1].remainder_s6 [25]),
        .I2(\threshold_pipes[1].remainder_s6 [22]),
        .I3(\threshold_pipes[1].remainder_s6 [23]),
        .I4(\threshold_pipes[1].remainder_s6 [21]),
        .I5(\threshold_pipes[1].remainder_s6 [20]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_6_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[1].count_threshold[1][3]_i_7 
       (.I0(\threshold_pipes[1].remainder_s6 [12]),
        .I1(\threshold_pipes[1].remainder_s6 [13]),
        .I2(\threshold_pipes[1].remainder_s6 [10]),
        .I3(\threshold_pipes[1].remainder_s6 [11]),
        .I4(\threshold_pipes[1].remainder_s6 [9]),
        .I5(\threshold_pipes[1].remainder_s6 [8]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_7_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[1].count_threshold[1][3]_i_8 
       (.I0(\threshold_pipes[1].remainder_s6 [18]),
        .I1(\threshold_pipes[1].remainder_s6 [19]),
        .I2(\threshold_pipes[1].remainder_s6 [16]),
        .I3(\threshold_pipes[1].remainder_s6 [17]),
        .I4(\threshold_pipes[1].remainder_s6 [15]),
        .I5(\threshold_pipes[1].remainder_s6 [14]),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_8_n_0 ));
  LUT6 #(
    .INIT(64'h0000FFFE00000000)) 
    \threshold_pipes[1].count_threshold[1][3]_i_9 
       (.I0(\threshold_pipes[1].remainder_s6 [1]),
        .I1(\threshold_pipes[1].remainder_s6 [0]),
        .I2(\threshold_pipes[1].remainder_s6 [3]),
        .I3(\threshold_pipes[1].remainder_s6 [2]),
        .I4(\threshold_pipes[1].count_threshold[1][3]_i_4_n_0 ),
        .I5(\threshold_pipes[1].count_threshold[1][3]_i_13_n_0 ),
        .O(\threshold_pipes[1].count_threshold[1][3]_i_9_n_0 ));
  FDRE \threshold_pipes[1].count_threshold_reg[1][0] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_7 ),
        .Q(\^meta_threshold2 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][10] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_5 ),
        .Q(\^meta_threshold2 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][11] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_4 ),
        .Q(\^meta_threshold2 [11]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].count_threshold_reg[1][11]_i_1 
       (.CI(\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_0 ),
        .CO({\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_0 ,\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_1 ,\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_2 ,\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_4 ,\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_5 ,\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_6 ,\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_7 }),
        .S(\threshold_pipes[1].q_s6 [11:8]));
  FDRE \threshold_pipes[1].count_threshold_reg[1][12] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_7 ),
        .Q(\^meta_threshold2 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][13] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_6 ),
        .Q(\^meta_threshold2 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][14] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_5 ),
        .Q(\^meta_threshold2 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][15] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_4 ),
        .Q(\^meta_threshold2 [15]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].count_threshold_reg[1][15]_i_1 
       (.CI(\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_0 ),
        .CO({\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_0 ,\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_1 ,\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_2 ,\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_4 ,\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_5 ,\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_6 ,\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_7 }),
        .S(\threshold_pipes[1].q_s6 [15:12]));
  FDRE \threshold_pipes[1].count_threshold_reg[1][16] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_7 ),
        .Q(\^meta_threshold2 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][17] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_6 ),
        .Q(\^meta_threshold2 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][18] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_5 ),
        .Q(\^meta_threshold2 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][19] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_4 ),
        .Q(\^meta_threshold2 [19]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].count_threshold_reg[1][19]_i_1 
       (.CI(\threshold_pipes[1].count_threshold_reg[1][15]_i_1_n_0 ),
        .CO({\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_0 ,\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_1 ,\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_2 ,\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_4 ,\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_5 ,\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_6 ,\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_7 }),
        .S(\threshold_pipes[1].q_s6 [19:16]));
  FDRE \threshold_pipes[1].count_threshold_reg[1][1] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_6 ),
        .Q(\^meta_threshold2 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][20] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_7 ),
        .Q(\^meta_threshold2 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][21] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_6 ),
        .Q(\^meta_threshold2 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][22] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_5 ),
        .Q(\^meta_threshold2 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][23] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_4 ),
        .Q(\^meta_threshold2 [23]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].count_threshold_reg[1][23]_i_1 
       (.CI(\threshold_pipes[1].count_threshold_reg[1][19]_i_1_n_0 ),
        .CO({\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_0 ,\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_1 ,\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_2 ,\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_4 ,\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_5 ,\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_6 ,\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_7 }),
        .S(\threshold_pipes[1].q_s6 [23:20]));
  FDRE \threshold_pipes[1].count_threshold_reg[1][24] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_7 ),
        .Q(\^meta_threshold2 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][25] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_6 ),
        .Q(\^meta_threshold2 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][26] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_5 ),
        .Q(\^meta_threshold2 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][27] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_4 ),
        .Q(\^meta_threshold2 [27]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].count_threshold_reg[1][27]_i_1 
       (.CI(\threshold_pipes[1].count_threshold_reg[1][23]_i_1_n_0 ),
        .CO({\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_0 ,\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_1 ,\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_2 ,\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_4 ,\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_5 ,\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_6 ,\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_7 }),
        .S(\threshold_pipes[1].q_s6 [27:24]));
  FDRE \threshold_pipes[1].count_threshold_reg[1][28] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_7 ),
        .Q(\^meta_threshold2 [28]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][29] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_6 ),
        .Q(\^meta_threshold2 [29]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][2] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_5 ),
        .Q(\^meta_threshold2 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][30] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_1 ),
        .Q(\^meta_threshold2 [30]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].count_threshold_reg[1][30]_i_1 
       (.CI(\threshold_pipes[1].count_threshold_reg[1][27]_i_1_n_0 ),
        .CO({\NLW_threshold_pipes[1].count_threshold_reg[1][30]_i_1_CO_UNCONNECTED [3],\threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_1 ,\NLW_threshold_pipes[1].count_threshold_reg[1][30]_i_1_CO_UNCONNECTED [1],\threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_threshold_pipes[1].count_threshold_reg[1][30]_i_1_O_UNCONNECTED [3:2],\threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_6 ,\threshold_pipes[1].count_threshold_reg[1][30]_i_1_n_7 }),
        .S({1'b0,1'b1,\threshold_pipes[1].q_s6 [29:28]}));
  FDRE \threshold_pipes[1].count_threshold_reg[1][3] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_4 ),
        .Q(\^meta_threshold2 [3]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].count_threshold_reg[1][3]_i_1 
       (.CI(1'b0),
        .CO({\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_0 ,\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_1 ,\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_2 ,\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,\threshold_pipes[1].q_s6 [1:0]}),
        .O({\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_4 ,\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_5 ,\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_6 ,\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_7 }),
        .S({\threshold_pipes[1].q_s6 [3:2],\threshold_pipes[1].count_threshold[1][3]_i_2_n_0 ,\threshold_pipes[1].count_threshold[1][3]_i_3_n_0 }));
  FDRE \threshold_pipes[1].count_threshold_reg[1][4] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_7 ),
        .Q(\^meta_threshold2 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][5] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_6 ),
        .Q(\^meta_threshold2 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][6] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_5 ),
        .Q(\^meta_threshold2 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][7] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_4 ),
        .Q(\^meta_threshold2 [7]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].count_threshold_reg[1][7]_i_1 
       (.CI(\threshold_pipes[1].count_threshold_reg[1][3]_i_1_n_0 ),
        .CO({\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_0 ,\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_1 ,\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_2 ,\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_4 ,\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_5 ,\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_6 ,\threshold_pipes[1].count_threshold_reg[1][7]_i_1_n_7 }),
        .S(\threshold_pipes[1].q_s6 [7:4]));
  FDRE \threshold_pipes[1].count_threshold_reg[1][8] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_7 ),
        .Q(\^meta_threshold2 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[1].count_threshold_reg[1][9] 
       (.C(clk),
        .CE(\threshold_pipes[1].valid_pipe__0 ),
        .D(\threshold_pipes[1].count_threshold_reg[1][11]_i_1_n_6 ),
        .Q(\^meta_threshold2 [9]),
        .R(1'b0));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_11 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_98 ),
        .I1(\threshold_pipes[1].low_carry_s1 [7]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_11_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_12 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_99 ),
        .I1(\threshold_pipes[1].low_carry_s1 [6]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_12_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_13 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_100 ),
        .I1(\threshold_pipes[1].low_carry_s1 [5]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_13_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_14 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_101 ),
        .I1(\threshold_pipes[1].low_carry_s1 [4]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_14_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_15 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_102 ),
        .I1(\threshold_pipes[1].low_carry_s1 [3]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_15_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_16 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_103 ),
        .I1(\threshold_pipes[1].low_carry_s1 [2]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_16_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_17 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_104 ),
        .I1(\threshold_pipes[1].low_carry_s1 [1]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_17_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_18 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_105 ),
        .I1(\threshold_pipes[1].low_carry_s1 [0]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_18_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_4 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_93 ),
        .I1(\threshold_pipes[1].low_carry_s1 [12]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_6 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_94 ),
        .I1(\threshold_pipes[1].low_carry_s1 [11]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_6_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_7 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_95 ),
        .I1(\threshold_pipes[1].low_carry_s1 [10]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_7_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_8 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_96 ),
        .I1(\threshold_pipes[1].low_carry_s1 [9]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_8_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].cross_carry_s2[3]_i_9 
       (.I0(\threshold_pipes[1].cross_s1_reg_n_97 ),
        .I1(\threshold_pipes[1].low_carry_s1 [8]),
        .O(\threshold_pipes[1].cross_carry_s2[3]_i_9_n_0 ));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [16]),
        .Q(\threshold_pipes[1].cross_carry_s2 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [26]),
        .Q(\threshold_pipes[1].cross_carry_s2 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [27]),
        .Q(\threshold_pipes[1].cross_carry_s2 [11]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].cross_carry_s2_reg[11]_i_1 
       (.CI(\threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_0 ),
        .CO({\threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_0 ,\threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_1 ,\threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_2 ,\threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[1].cross_carry_s21 [27:24]),
        .S({\threshold_pipes[1].cross_s1_reg_n_78 ,\threshold_pipes[1].cross_s1_reg_n_79 ,\threshold_pipes[1].cross_s1_reg_n_80 ,\threshold_pipes[1].cross_s1_reg_n_81 }));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [28]),
        .Q(\threshold_pipes[1].cross_carry_s2 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [29]),
        .Q(\threshold_pipes[1].cross_carry_s2 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [30]),
        .Q(\threshold_pipes[1].cross_carry_s2 [14]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].cross_carry_s2_reg[14]_i_1 
       (.CI(\threshold_pipes[1].cross_carry_s2_reg[11]_i_1_n_0 ),
        .CO({\NLW_threshold_pipes[1].cross_carry_s2_reg[14]_i_1_CO_UNCONNECTED [3],\threshold_pipes[1].cross_carry_s21 [30],\NLW_threshold_pipes[1].cross_carry_s2_reg[14]_i_1_CO_UNCONNECTED [1],\threshold_pipes[1].cross_carry_s2_reg[14]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_threshold_pipes[1].cross_carry_s2_reg[14]_i_1_O_UNCONNECTED [3:2],\threshold_pipes[1].cross_carry_s21 [29:28]}),
        .S({1'b0,1'b1,\threshold_pipes[1].cross_s1_reg_n_76 ,\threshold_pipes[1].cross_s1_reg_n_77 }));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [17]),
        .Q(\threshold_pipes[1].cross_carry_s2 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [18]),
        .Q(\threshold_pipes[1].cross_carry_s2 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [19]),
        .Q(\threshold_pipes[1].cross_carry_s2 [3]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].cross_carry_s2_reg[3]_i_1 
       (.CI(\threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_0 ),
        .CO({\threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_0 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_1 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_2 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[1].cross_carry_s21 [19:16]),
        .S({\threshold_pipes[1].cross_s1_reg_n_86 ,\threshold_pipes[1].cross_s1_reg_n_87 ,\threshold_pipes[1].cross_s1_reg_n_88 ,\threshold_pipes[1].cross_s1_reg_n_89 }));
  CARRY4 \threshold_pipes[1].cross_carry_s2_reg[3]_i_10 
       (.CI(1'b0),
        .CO({\threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_0 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_1 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_2 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[1].cross_s1_reg_n_102 ,\threshold_pipes[1].cross_s1_reg_n_103 ,\threshold_pipes[1].cross_s1_reg_n_104 ,\threshold_pipes[1].cross_s1_reg_n_105 }),
        .O(\NLW_threshold_pipes[1].cross_carry_s2_reg[3]_i_10_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[1].cross_carry_s2[3]_i_15_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_16_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_17_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_18_n_0 }));
  CARRY4 \threshold_pipes[1].cross_carry_s2_reg[3]_i_2 
       (.CI(\threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_0 ),
        .CO({\threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_0 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_1 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_2 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,\threshold_pipes[1].cross_s1_reg_n_93 }),
        .O(\NLW_threshold_pipes[1].cross_carry_s2_reg[3]_i_2_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[1].cross_s1_reg_n_90 ,\threshold_pipes[1].cross_s1_reg_n_91 ,\threshold_pipes[1].cross_s1_reg_n_92 ,\threshold_pipes[1].cross_carry_s2[3]_i_4_n_0 }));
  CARRY4 \threshold_pipes[1].cross_carry_s2_reg[3]_i_3 
       (.CI(\threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_0 ),
        .CO({\threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_0 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_1 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_2 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_3_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[1].cross_s1_reg_n_94 ,\threshold_pipes[1].cross_s1_reg_n_95 ,\threshold_pipes[1].cross_s1_reg_n_96 ,\threshold_pipes[1].cross_s1_reg_n_97 }),
        .O(\NLW_threshold_pipes[1].cross_carry_s2_reg[3]_i_3_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[1].cross_carry_s2[3]_i_6_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_7_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_8_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_9_n_0 }));
  CARRY4 \threshold_pipes[1].cross_carry_s2_reg[3]_i_5 
       (.CI(\threshold_pipes[1].cross_carry_s2_reg[3]_i_10_n_0 ),
        .CO({\threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_0 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_1 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_2 ,\threshold_pipes[1].cross_carry_s2_reg[3]_i_5_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[1].cross_s1_reg_n_98 ,\threshold_pipes[1].cross_s1_reg_n_99 ,\threshold_pipes[1].cross_s1_reg_n_100 ,\threshold_pipes[1].cross_s1_reg_n_101 }),
        .O(\NLW_threshold_pipes[1].cross_carry_s2_reg[3]_i_5_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[1].cross_carry_s2[3]_i_11_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_12_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_13_n_0 ,\threshold_pipes[1].cross_carry_s2[3]_i_14_n_0 }));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [20]),
        .Q(\threshold_pipes[1].cross_carry_s2 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [21]),
        .Q(\threshold_pipes[1].cross_carry_s2 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [22]),
        .Q(\threshold_pipes[1].cross_carry_s2 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [23]),
        .Q(\threshold_pipes[1].cross_carry_s2 [7]),
        .R(1'b0));
  CARRY4 \threshold_pipes[1].cross_carry_s2_reg[7]_i_1 
       (.CI(\threshold_pipes[1].cross_carry_s2_reg[3]_i_1_n_0 ),
        .CO({\threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_0 ,\threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_1 ,\threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_2 ,\threshold_pipes[1].cross_carry_s2_reg[7]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[1].cross_carry_s21 [23:20]),
        .S({\threshold_pipes[1].cross_s1_reg_n_82 ,\threshold_pipes[1].cross_s1_reg_n_83 ,\threshold_pipes[1].cross_s1_reg_n_84 ,\threshold_pipes[1].cross_s1_reg_n_85 }));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [24]),
        .Q(\threshold_pipes[1].cross_carry_s2 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[1].cross_carry_s2_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].cross_carry_s21 [25]),
        .Q(\threshold_pipes[1].cross_carry_s2 [9]),
        .R(1'b0));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[1].cross_s1_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[31:16]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[1].cross_s1_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[1].cross_s1_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,partial_product1_return__0}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[1].cross_s1_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[1].cross_s1_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b1),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[1].cross_s1_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b1,1'b1,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[1].cross_s1_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[1].cross_s1_reg_P_UNCONNECTED [47:30],\threshold_pipes[1].cross_s1_reg_n_76 ,\threshold_pipes[1].cross_s1_reg_n_77 ,\threshold_pipes[1].cross_s1_reg_n_78 ,\threshold_pipes[1].cross_s1_reg_n_79 ,\threshold_pipes[1].cross_s1_reg_n_80 ,\threshold_pipes[1].cross_s1_reg_n_81 ,\threshold_pipes[1].cross_s1_reg_n_82 ,\threshold_pipes[1].cross_s1_reg_n_83 ,\threshold_pipes[1].cross_s1_reg_n_84 ,\threshold_pipes[1].cross_s1_reg_n_85 ,\threshold_pipes[1].cross_s1_reg_n_86 ,\threshold_pipes[1].cross_s1_reg_n_87 ,\threshold_pipes[1].cross_s1_reg_n_88 ,\threshold_pipes[1].cross_s1_reg_n_89 ,\threshold_pipes[1].cross_s1_reg_n_90 ,\threshold_pipes[1].cross_s1_reg_n_91 ,\threshold_pipes[1].cross_s1_reg_n_92 ,\threshold_pipes[1].cross_s1_reg_n_93 ,\threshold_pipes[1].cross_s1_reg_n_94 ,\threshold_pipes[1].cross_s1_reg_n_95 ,\threshold_pipes[1].cross_s1_reg_n_96 ,\threshold_pipes[1].cross_s1_reg_n_97 ,\threshold_pipes[1].cross_s1_reg_n_98 ,\threshold_pipes[1].cross_s1_reg_n_99 ,\threshold_pipes[1].cross_s1_reg_n_100 ,\threshold_pipes[1].cross_s1_reg_n_101 ,\threshold_pipes[1].cross_s1_reg_n_102 ,\threshold_pipes[1].cross_s1_reg_n_103 ,\threshold_pipes[1].cross_s1_reg_n_104 ,\threshold_pipes[1].cross_s1_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[1].cross_s1_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[1].cross_s1_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[1].cross_s1_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[1].cross_s1_reg_UNDERFLOW_UNCONNECTED ));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[1].high_s1_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[31:16]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[1].high_s1_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1,1'b0,1'b0,1'b0,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[1].high_s1_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[1].high_s1_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[1].high_s1_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[1].high_s1_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[1].high_s1_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[1].high_s1_reg_P_UNCONNECTED [47:29],\threshold_pipes[1].high_s1_reg_n_77 ,\threshold_pipes[1].high_s1_reg_n_78 ,\threshold_pipes[1].high_s1_reg_n_79 ,\threshold_pipes[1].high_s1_reg_n_80 ,\threshold_pipes[1].high_s1_reg_n_81 ,\threshold_pipes[1].high_s1_reg_n_82 ,\threshold_pipes[1].high_s1_reg_n_83 ,\threshold_pipes[1].high_s1_reg_n_84 ,\threshold_pipes[1].high_s1_reg_n_85 ,\threshold_pipes[1].high_s1_reg_n_86 ,\threshold_pipes[1].high_s1_reg_n_87 ,\threshold_pipes[1].high_s1_reg_n_88 ,\threshold_pipes[1].high_s1_reg_n_89 ,\threshold_pipes[1].high_s1_reg_n_90 ,\threshold_pipes[1].high_s1_reg_n_91 ,\threshold_pipes[1].high_s1_reg_n_92 ,\threshold_pipes[1].high_s1_reg_n_93 ,\threshold_pipes[1].high_s1_reg_n_94 ,\threshold_pipes[1].high_s1_reg_n_95 ,\threshold_pipes[1].high_s1_reg_n_96 ,\threshold_pipes[1].high_s1_reg_n_97 ,\threshold_pipes[1].high_s1_reg_n_98 ,\threshold_pipes[1].high_s1_reg_n_99 ,\threshold_pipes[1].high_s1_reg_n_100 ,\threshold_pipes[1].high_s1_reg_n_101 ,\threshold_pipes[1].high_s1_reg_n_102 ,\threshold_pipes[1].high_s1_reg_n_103 ,\threshold_pipes[1].high_s1_reg_n_104 ,\threshold_pipes[1].high_s1_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[1].high_s1_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[1].high_s1_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[1].high_s1_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[1].high_s1_reg_UNDERFLOW_UNCONNECTED ));
  FDRE \threshold_pipes[1].high_s2_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_105 ),
        .Q(\threshold_pipes[1].high_s2 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_95 ),
        .Q(\threshold_pipes[1].high_s2 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_94 ),
        .Q(\threshold_pipes[1].high_s2 [11]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_93 ),
        .Q(\threshold_pipes[1].high_s2 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_92 ),
        .Q(\threshold_pipes[1].high_s2 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_91 ),
        .Q(\threshold_pipes[1].high_s2 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_90 ),
        .Q(\threshold_pipes[1].high_s2 [15]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_89 ),
        .Q(\threshold_pipes[1].high_s2 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_88 ),
        .Q(\threshold_pipes[1].high_s2 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_87 ),
        .Q(\threshold_pipes[1].high_s2 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_86 ),
        .Q(\threshold_pipes[1].high_s2 [19]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_104 ),
        .Q(\threshold_pipes[1].high_s2 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_85 ),
        .Q(\threshold_pipes[1].high_s2 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_84 ),
        .Q(\threshold_pipes[1].high_s2 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_83 ),
        .Q(\threshold_pipes[1].high_s2 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_82 ),
        .Q(\threshold_pipes[1].high_s2 [23]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_81 ),
        .Q(\threshold_pipes[1].high_s2 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_80 ),
        .Q(\threshold_pipes[1].high_s2 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_79 ),
        .Q(\threshold_pipes[1].high_s2 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_78 ),
        .Q(\threshold_pipes[1].high_s2 [27]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_77 ),
        .Q(\threshold_pipes[1].high_s2 [28]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_103 ),
        .Q(\threshold_pipes[1].high_s2 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_102 ),
        .Q(\threshold_pipes[1].high_s2 [3]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_101 ),
        .Q(\threshold_pipes[1].high_s2 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_100 ),
        .Q(\threshold_pipes[1].high_s2 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_99 ),
        .Q(\threshold_pipes[1].high_s2 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_98 ),
        .Q(\threshold_pipes[1].high_s2 [7]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_97 ),
        .Q(\threshold_pipes[1].high_s2 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[1].high_s2_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].high_s1_reg_n_96 ),
        .Q(\threshold_pipes[1].high_s2 [9]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [0]),
        .Q(\threshold_pipes[1].low_carry_s1 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [10]),
        .Q(\threshold_pipes[1].low_carry_s1 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [11]),
        .Q(\threshold_pipes[1].low_carry_s1 [11]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [12]),
        .Q(\threshold_pipes[1].low_carry_s1 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [1]),
        .Q(\threshold_pipes[1].low_carry_s1 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [2]),
        .Q(\threshold_pipes[1].low_carry_s1 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [3]),
        .Q(\threshold_pipes[1].low_carry_s1 [3]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [4]),
        .Q(\threshold_pipes[1].low_carry_s1 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [5]),
        .Q(\threshold_pipes[1].low_carry_s1 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [6]),
        .Q(\threshold_pipes[1].low_carry_s1 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [7]),
        .Q(\threshold_pipes[1].low_carry_s1 [7]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [8]),
        .Q(\threshold_pipes[1].low_carry_s1 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[1].low_carry_s1_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].mul00_hi [9]),
        .Q(\threshold_pipes[1].low_carry_s1 [9]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[16]),
        .Q(\threshold_pipes[1].mul00_hi [0]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[26]),
        .Q(\threshold_pipes[1].mul00_hi [10]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[27]),
        .Q(\threshold_pipes[1].mul00_hi [11]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[28]),
        .Q(\threshold_pipes[1].mul00_hi [12]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[17]),
        .Q(\threshold_pipes[1].mul00_hi [1]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[18]),
        .Q(\threshold_pipes[1].mul00_hi [2]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[19]),
        .Q(\threshold_pipes[1].mul00_hi [3]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[20]),
        .Q(\threshold_pipes[1].mul00_hi [4]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[21]),
        .Q(\threshold_pipes[1].mul00_hi [5]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[22]),
        .Q(\threshold_pipes[1].mul00_hi [6]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[23]),
        .Q(\threshold_pipes[1].mul00_hi [7]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[24]),
        .Q(\threshold_pipes[1].mul00_hi [8]),
        .R(1'b0));
  (* USE_DSP = "YES" *) 
  FDRE \threshold_pipes[1].mul00_hi_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(partial_product1_return__0[25]),
        .Q(\threshold_pipes[1].mul00_hi [9]),
        .R(1'b0));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(0),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[1].product_s5_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[1].product_s5_reg_i_1_n_4 ,\threshold_pipes[1].product_s5_reg_i_1_n_5 ,\threshold_pipes[1].product_s5_reg_i_1_n_6 ,\threshold_pipes[1].product_s5_reg_i_1_n_7 ,\threshold_pipes[1].product_s5_reg_i_2_n_4 ,\threshold_pipes[1].product_s5_reg_i_2_n_5 ,\threshold_pipes[1].product_s5_reg_i_2_n_6 ,\threshold_pipes[1].product_s5_reg_i_2_n_7 ,\threshold_pipes[1].product_s5_reg_i_3_n_4 ,\threshold_pipes[1].product_s5_reg_i_3_n_5 ,\threshold_pipes[1].product_s5_reg_i_3_n_6 ,\threshold_pipes[1].product_s5_reg_i_3_n_7 ,\threshold_pipes[1].product_s5_reg_i_4_n_4 ,\threshold_pipes[1].product_s5_reg_i_4_n_5 ,\threshold_pipes[1].product_s5_reg_i_4_n_6 ,\threshold_pipes[1].product_s5_reg_i_4_n_7 }),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[1].product_s5_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b1,1'b1,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[1].product_s5_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[1].check_hi_reg_n_90 ,\threshold_pipes[1].check_hi_reg_n_91 ,\threshold_pipes[1].check_hi_reg_n_92 ,\threshold_pipes[1].check_hi_reg_n_93 ,\threshold_pipes[1].check_hi_reg_n_94 ,\threshold_pipes[1].check_hi_reg_n_95 ,\threshold_pipes[1].check_hi_reg_n_96 ,\threshold_pipes[1].check_hi_reg_n_97 ,\threshold_pipes[1].check_hi_reg_n_98 ,\threshold_pipes[1].check_hi_reg_n_99 ,\threshold_pipes[1].check_hi_reg_n_100 ,\threshold_pipes[1].check_hi_reg_n_101 ,\threshold_pipes[1].check_hi_reg_n_102 ,\threshold_pipes[1].check_hi_reg_n_103 ,\threshold_pipes[1].check_hi_reg_n_104 ,\threshold_pipes[1].check_hi_reg_n_105 ,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[1].product_s5_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[1].product_s5_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[1].product_s5_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b1,1'b1,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[1].product_s5_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[1].product_s5_reg_P_UNCONNECTED [47:32],\threshold_pipes[1].product_s5_reg__0 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[1].product_s5_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[1].product_s5_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[1].product_s5_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[1].product_s5_reg_UNDERFLOW_UNCONNECTED ));
  CARRY4 \threshold_pipes[1].product_s5_reg_i_1 
       (.CI(\threshold_pipes[1].product_s5_reg_i_2_n_0 ),
        .CO({\threshold_pipes[1].product_s5_reg_i_1_n_0 ,\threshold_pipes[1].product_s5_reg_i_1_n_1 ,\threshold_pipes[1].product_s5_reg_i_1_n_2 ,\threshold_pipes[1].product_s5_reg_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,\threshold_pipes[1].high_s2 [14:12]}),
        .O({\threshold_pipes[1].product_s5_reg_i_1_n_4 ,\threshold_pipes[1].product_s5_reg_i_1_n_5 ,\threshold_pipes[1].product_s5_reg_i_1_n_6 ,\threshold_pipes[1].product_s5_reg_i_1_n_7 }),
        .S({\threshold_pipes[1].high_s2 [15],\threshold_pipes[1].product_s5_reg_i_5_n_0 ,\threshold_pipes[1].product_s5_reg_i_6_n_0 ,\threshold_pipes[1].product_s5_reg_i_7_n_0 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_10 
       (.I0(\threshold_pipes[1].high_s2 [9]),
        .I1(\threshold_pipes[1].cross_carry_s2 [9]),
        .O(\threshold_pipes[1].product_s5_reg_i_10_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_11 
       (.I0(\threshold_pipes[1].high_s2 [8]),
        .I1(\threshold_pipes[1].cross_carry_s2 [8]),
        .O(\threshold_pipes[1].product_s5_reg_i_11_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_12 
       (.I0(\threshold_pipes[1].high_s2 [7]),
        .I1(\threshold_pipes[1].cross_carry_s2 [7]),
        .O(\threshold_pipes[1].product_s5_reg_i_12_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_13 
       (.I0(\threshold_pipes[1].high_s2 [6]),
        .I1(\threshold_pipes[1].cross_carry_s2 [6]),
        .O(\threshold_pipes[1].product_s5_reg_i_13_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_14 
       (.I0(\threshold_pipes[1].high_s2 [5]),
        .I1(\threshold_pipes[1].cross_carry_s2 [5]),
        .O(\threshold_pipes[1].product_s5_reg_i_14_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_15 
       (.I0(\threshold_pipes[1].high_s2 [4]),
        .I1(\threshold_pipes[1].cross_carry_s2 [4]),
        .O(\threshold_pipes[1].product_s5_reg_i_15_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_16 
       (.I0(\threshold_pipes[1].high_s2 [3]),
        .I1(\threshold_pipes[1].cross_carry_s2 [3]),
        .O(\threshold_pipes[1].product_s5_reg_i_16_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_17 
       (.I0(\threshold_pipes[1].high_s2 [2]),
        .I1(\threshold_pipes[1].cross_carry_s2 [2]),
        .O(\threshold_pipes[1].product_s5_reg_i_17_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_18 
       (.I0(\threshold_pipes[1].high_s2 [1]),
        .I1(\threshold_pipes[1].cross_carry_s2 [1]),
        .O(\threshold_pipes[1].product_s5_reg_i_18_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_19 
       (.I0(\threshold_pipes[1].high_s2 [0]),
        .I1(\threshold_pipes[1].cross_carry_s2 [0]),
        .O(\threshold_pipes[1].product_s5_reg_i_19_n_0 ));
  CARRY4 \threshold_pipes[1].product_s5_reg_i_2 
       (.CI(\threshold_pipes[1].product_s5_reg_i_3_n_0 ),
        .CO({\threshold_pipes[1].product_s5_reg_i_2_n_0 ,\threshold_pipes[1].product_s5_reg_i_2_n_1 ,\threshold_pipes[1].product_s5_reg_i_2_n_2 ,\threshold_pipes[1].product_s5_reg_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[1].high_s2 [11:8]),
        .O({\threshold_pipes[1].product_s5_reg_i_2_n_4 ,\threshold_pipes[1].product_s5_reg_i_2_n_5 ,\threshold_pipes[1].product_s5_reg_i_2_n_6 ,\threshold_pipes[1].product_s5_reg_i_2_n_7 }),
        .S({\threshold_pipes[1].product_s5_reg_i_8_n_0 ,\threshold_pipes[1].product_s5_reg_i_9_n_0 ,\threshold_pipes[1].product_s5_reg_i_10_n_0 ,\threshold_pipes[1].product_s5_reg_i_11_n_0 }));
  CARRY4 \threshold_pipes[1].product_s5_reg_i_3 
       (.CI(\threshold_pipes[1].product_s5_reg_i_4_n_0 ),
        .CO({\threshold_pipes[1].product_s5_reg_i_3_n_0 ,\threshold_pipes[1].product_s5_reg_i_3_n_1 ,\threshold_pipes[1].product_s5_reg_i_3_n_2 ,\threshold_pipes[1].product_s5_reg_i_3_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[1].high_s2 [7:4]),
        .O({\threshold_pipes[1].product_s5_reg_i_3_n_4 ,\threshold_pipes[1].product_s5_reg_i_3_n_5 ,\threshold_pipes[1].product_s5_reg_i_3_n_6 ,\threshold_pipes[1].product_s5_reg_i_3_n_7 }),
        .S({\threshold_pipes[1].product_s5_reg_i_12_n_0 ,\threshold_pipes[1].product_s5_reg_i_13_n_0 ,\threshold_pipes[1].product_s5_reg_i_14_n_0 ,\threshold_pipes[1].product_s5_reg_i_15_n_0 }));
  CARRY4 \threshold_pipes[1].product_s5_reg_i_4 
       (.CI(1'b0),
        .CO({\threshold_pipes[1].product_s5_reg_i_4_n_0 ,\threshold_pipes[1].product_s5_reg_i_4_n_1 ,\threshold_pipes[1].product_s5_reg_i_4_n_2 ,\threshold_pipes[1].product_s5_reg_i_4_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[1].high_s2 [3:0]),
        .O({\threshold_pipes[1].product_s5_reg_i_4_n_4 ,\threshold_pipes[1].product_s5_reg_i_4_n_5 ,\threshold_pipes[1].product_s5_reg_i_4_n_6 ,\threshold_pipes[1].product_s5_reg_i_4_n_7 }),
        .S({\threshold_pipes[1].product_s5_reg_i_16_n_0 ,\threshold_pipes[1].product_s5_reg_i_17_n_0 ,\threshold_pipes[1].product_s5_reg_i_18_n_0 ,\threshold_pipes[1].product_s5_reg_i_19_n_0 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_5 
       (.I0(\threshold_pipes[1].high_s2 [14]),
        .I1(\threshold_pipes[1].cross_carry_s2 [14]),
        .O(\threshold_pipes[1].product_s5_reg_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_6 
       (.I0(\threshold_pipes[1].high_s2 [13]),
        .I1(\threshold_pipes[1].cross_carry_s2 [13]),
        .O(\threshold_pipes[1].product_s5_reg_i_6_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_7 
       (.I0(\threshold_pipes[1].high_s2 [12]),
        .I1(\threshold_pipes[1].cross_carry_s2 [12]),
        .O(\threshold_pipes[1].product_s5_reg_i_7_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_8 
       (.I0(\threshold_pipes[1].high_s2 [11]),
        .I1(\threshold_pipes[1].cross_carry_s2 [11]),
        .O(\threshold_pipes[1].product_s5_reg_i_8_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[1].product_s5_reg_i_9 
       (.I0(\threshold_pipes[1].high_s2 [10]),
        .I1(\threshold_pipes[1].cross_carry_s2 [10]),
        .O(\threshold_pipes[1].product_s5_reg_i_9_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[0]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[0]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_4_n_7 ),
        .Q(\threshold_pipes[1].q_s5_reg[0]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[10]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[10]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_2_n_5 ),
        .Q(\threshold_pipes[1].q_s5_reg[10]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[11]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[11]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_2_n_4 ),
        .Q(\threshold_pipes[1].q_s5_reg[11]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[12]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[12]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_1_n_7 ),
        .Q(\threshold_pipes[1].q_s5_reg[12]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[13]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[13]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_1_n_6 ),
        .Q(\threshold_pipes[1].q_s5_reg[13]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[14]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[14]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_1_n_5 ),
        .Q(\threshold_pipes[1].q_s5_reg[14]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[15]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[15]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_1_n_4 ),
        .Q(\threshold_pipes[1].q_s5_reg[15]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[16]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[16]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_4_n_7 ),
        .Q(\threshold_pipes[1].q_s5_reg[16]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[17]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[17]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_4_n_6 ),
        .Q(\threshold_pipes[1].q_s5_reg[17]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[18]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[18]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_4_n_5 ),
        .Q(\threshold_pipes[1].q_s5_reg[18]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[19]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[19]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_4_n_4 ),
        .Q(\threshold_pipes[1].q_s5_reg[19]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[1]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[1]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_4_n_6 ),
        .Q(\threshold_pipes[1].q_s5_reg[1]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[20]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[20]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_3_n_7 ),
        .Q(\threshold_pipes[1].q_s5_reg[20]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[21]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[21]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_3_n_6 ),
        .Q(\threshold_pipes[1].q_s5_reg[21]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[22]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[22]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_3_n_5 ),
        .Q(\threshold_pipes[1].q_s5_reg[22]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[23]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[23]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_3_n_4 ),
        .Q(\threshold_pipes[1].q_s5_reg[23]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[24]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[24]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_2_n_7 ),
        .Q(\threshold_pipes[1].q_s5_reg[24]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[25]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[25]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_2_n_6 ),
        .Q(\threshold_pipes[1].q_s5_reg[25]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[26]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[26]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_2_n_5 ),
        .Q(\threshold_pipes[1].q_s5_reg[26]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[27]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[27]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_2_n_4 ),
        .Q(\threshold_pipes[1].q_s5_reg[27]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[28]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[28]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_1_n_7 ),
        .Q(\threshold_pipes[1].q_s5_reg[28]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[29]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[29]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].check_hi_reg_i_1_n_2 ),
        .Q(\threshold_pipes[1].q_s5_reg[29]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[2]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[2]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_4_n_5 ),
        .Q(\threshold_pipes[1].q_s5_reg[2]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[3]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[3]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_4_n_4 ),
        .Q(\threshold_pipes[1].q_s5_reg[3]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[4]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[4]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_3_n_7 ),
        .Q(\threshold_pipes[1].q_s5_reg[4]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[5]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[5]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_3_n_6 ),
        .Q(\threshold_pipes[1].q_s5_reg[5]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[6]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[6]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_3_n_5 ),
        .Q(\threshold_pipes[1].q_s5_reg[6]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[7]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[7]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_3_n_4 ),
        .Q(\threshold_pipes[1].q_s5_reg[7]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[8]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[8]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_2_n_7 ),
        .Q(\threshold_pipes[1].q_s5_reg[8]_srl3_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[1].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[1].q_s5_reg[9]_srl3 " *) 
  SRL16E \threshold_pipes[1].q_s5_reg[9]_srl3 
       (.A0(1'b0),
        .A1(1'b1),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].product_s5_reg_i_2_n_6 ),
        .Q(\threshold_pipes[1].q_s5_reg[9]_srl3_n_0 ));
  FDRE \threshold_pipes[1].q_s6_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[0]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[10]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[11]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [11]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[12]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[13]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[14]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[15]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [15]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[16]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[17]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[18]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[19]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [19]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[1]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[20]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[21]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[22]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[23]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [23]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[24]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[25]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[26]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[27]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [27]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[28]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [28]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[29] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[29]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [29]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[2]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[3]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [3]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[4]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[5]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[6]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[7]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [7]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[8]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[1].q_s6_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].q_s5_reg[9]_srl3_n_0 ),
        .Q(\threshold_pipes[1].q_s6 [9]),
        .R(1'b0));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[11]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [11]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [11]),
        .O(\threshold_pipes[1].remainder_s6[11]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[11]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [10]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [10]),
        .O(\threshold_pipes[1].remainder_s6[11]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[11]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [9]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [9]),
        .O(\threshold_pipes[1].remainder_s6[11]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[11]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [8]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [8]),
        .O(\threshold_pipes[1].remainder_s6[11]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[15]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [15]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [15]),
        .O(\threshold_pipes[1].remainder_s6[15]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[15]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [14]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [14]),
        .O(\threshold_pipes[1].remainder_s6[15]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[15]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [13]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [13]),
        .O(\threshold_pipes[1].remainder_s6[15]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[15]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [12]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [12]),
        .O(\threshold_pipes[1].remainder_s6[15]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[19]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [19]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [19]),
        .O(\threshold_pipes[1].remainder_s6[19]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[19]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [18]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [18]),
        .O(\threshold_pipes[1].remainder_s6[19]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[19]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [17]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [17]),
        .O(\threshold_pipes[1].remainder_s6[19]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[19]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [16]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [16]),
        .O(\threshold_pipes[1].remainder_s6[19]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[23]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [23]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [23]),
        .O(\threshold_pipes[1].remainder_s6[23]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[23]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [22]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [22]),
        .O(\threshold_pipes[1].remainder_s6[23]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[23]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [21]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [21]),
        .O(\threshold_pipes[1].remainder_s6[23]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[23]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [20]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [20]),
        .O(\threshold_pipes[1].remainder_s6[23]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[27]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [27]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [27]),
        .O(\threshold_pipes[1].remainder_s6[27]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[27]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [26]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [26]),
        .O(\threshold_pipes[1].remainder_s6[27]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[27]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [25]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [25]),
        .O(\threshold_pipes[1].remainder_s6[27]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[27]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [24]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [24]),
        .O(\threshold_pipes[1].remainder_s6[27]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[31]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [31]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [31]),
        .O(\threshold_pipes[1].remainder_s6[31]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[31]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [30]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [30]),
        .O(\threshold_pipes[1].remainder_s6[31]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[31]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [29]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [29]),
        .O(\threshold_pipes[1].remainder_s6[31]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[31]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [28]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [28]),
        .O(\threshold_pipes[1].remainder_s6[31]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[3]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [3]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [3]),
        .O(\threshold_pipes[1].remainder_s6[3]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[3]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [2]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [2]),
        .O(\threshold_pipes[1].remainder_s6[3]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[3]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [1]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [1]),
        .O(\threshold_pipes[1].remainder_s6[3]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[3]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [0]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [0]),
        .O(\threshold_pipes[1].remainder_s6[3]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[7]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [7]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [7]),
        .O(\threshold_pipes[1].remainder_s6[7]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[7]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [6]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [6]),
        .O(\threshold_pipes[1].remainder_s6[7]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[7]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [5]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [5]),
        .O(\threshold_pipes[1].remainder_s6[7]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[1].remainder_s6[7]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [4]),
        .I1(\threshold_pipes[1].product_s5_reg__0 [4]),
        .O(\threshold_pipes[1].remainder_s6[7]_i_5_n_0 ));
  FDRE \threshold_pipes[1].remainder_s6_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [0]),
        .Q(\threshold_pipes[1].remainder_s6 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [10]),
        .Q(\threshold_pipes[1].remainder_s6 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [11]),
        .Q(\threshold_pipes[1].remainder_s6 [11]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[1].remainder_s6_reg[11]_i_1 
       (.CI(\threshold_pipes[1].remainder_s6_reg[7]_i_1_n_0 ),
        .CO({\threshold_pipes[1].remainder_s6_reg[11]_i_1_n_0 ,\threshold_pipes[1].remainder_s6_reg[11]_i_1_n_1 ,\threshold_pipes[1].remainder_s6_reg[11]_i_1_n_2 ,\threshold_pipes[1].remainder_s6_reg[11]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [11:8]),
        .O(\threshold_pipes[1].remainder_s601_out [11:8]),
        .S({\threshold_pipes[1].remainder_s6[11]_i_2_n_0 ,\threshold_pipes[1].remainder_s6[11]_i_3_n_0 ,\threshold_pipes[1].remainder_s6[11]_i_4_n_0 ,\threshold_pipes[1].remainder_s6[11]_i_5_n_0 }));
  FDRE \threshold_pipes[1].remainder_s6_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [12]),
        .Q(\threshold_pipes[1].remainder_s6 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [13]),
        .Q(\threshold_pipes[1].remainder_s6 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [14]),
        .Q(\threshold_pipes[1].remainder_s6 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [15]),
        .Q(\threshold_pipes[1].remainder_s6 [15]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[1].remainder_s6_reg[15]_i_1 
       (.CI(\threshold_pipes[1].remainder_s6_reg[11]_i_1_n_0 ),
        .CO({\threshold_pipes[1].remainder_s6_reg[15]_i_1_n_0 ,\threshold_pipes[1].remainder_s6_reg[15]_i_1_n_1 ,\threshold_pipes[1].remainder_s6_reg[15]_i_1_n_2 ,\threshold_pipes[1].remainder_s6_reg[15]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [15:12]),
        .O(\threshold_pipes[1].remainder_s601_out [15:12]),
        .S({\threshold_pipes[1].remainder_s6[15]_i_2_n_0 ,\threshold_pipes[1].remainder_s6[15]_i_3_n_0 ,\threshold_pipes[1].remainder_s6[15]_i_4_n_0 ,\threshold_pipes[1].remainder_s6[15]_i_5_n_0 }));
  FDRE \threshold_pipes[1].remainder_s6_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [16]),
        .Q(\threshold_pipes[1].remainder_s6 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [17]),
        .Q(\threshold_pipes[1].remainder_s6 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [18]),
        .Q(\threshold_pipes[1].remainder_s6 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [19]),
        .Q(\threshold_pipes[1].remainder_s6 [19]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[1].remainder_s6_reg[19]_i_1 
       (.CI(\threshold_pipes[1].remainder_s6_reg[15]_i_1_n_0 ),
        .CO({\threshold_pipes[1].remainder_s6_reg[19]_i_1_n_0 ,\threshold_pipes[1].remainder_s6_reg[19]_i_1_n_1 ,\threshold_pipes[1].remainder_s6_reg[19]_i_1_n_2 ,\threshold_pipes[1].remainder_s6_reg[19]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [19:16]),
        .O(\threshold_pipes[1].remainder_s601_out [19:16]),
        .S({\threshold_pipes[1].remainder_s6[19]_i_2_n_0 ,\threshold_pipes[1].remainder_s6[19]_i_3_n_0 ,\threshold_pipes[1].remainder_s6[19]_i_4_n_0 ,\threshold_pipes[1].remainder_s6[19]_i_5_n_0 }));
  FDRE \threshold_pipes[1].remainder_s6_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [1]),
        .Q(\threshold_pipes[1].remainder_s6 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [20]),
        .Q(\threshold_pipes[1].remainder_s6 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [21]),
        .Q(\threshold_pipes[1].remainder_s6 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [22]),
        .Q(\threshold_pipes[1].remainder_s6 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [23]),
        .Q(\threshold_pipes[1].remainder_s6 [23]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[1].remainder_s6_reg[23]_i_1 
       (.CI(\threshold_pipes[1].remainder_s6_reg[19]_i_1_n_0 ),
        .CO({\threshold_pipes[1].remainder_s6_reg[23]_i_1_n_0 ,\threshold_pipes[1].remainder_s6_reg[23]_i_1_n_1 ,\threshold_pipes[1].remainder_s6_reg[23]_i_1_n_2 ,\threshold_pipes[1].remainder_s6_reg[23]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [23:20]),
        .O(\threshold_pipes[1].remainder_s601_out [23:20]),
        .S({\threshold_pipes[1].remainder_s6[23]_i_2_n_0 ,\threshold_pipes[1].remainder_s6[23]_i_3_n_0 ,\threshold_pipes[1].remainder_s6[23]_i_4_n_0 ,\threshold_pipes[1].remainder_s6[23]_i_5_n_0 }));
  FDRE \threshold_pipes[1].remainder_s6_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [24]),
        .Q(\threshold_pipes[1].remainder_s6 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [25]),
        .Q(\threshold_pipes[1].remainder_s6 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [26]),
        .Q(\threshold_pipes[1].remainder_s6 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [27]),
        .Q(\threshold_pipes[1].remainder_s6 [27]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[1].remainder_s6_reg[27]_i_1 
       (.CI(\threshold_pipes[1].remainder_s6_reg[23]_i_1_n_0 ),
        .CO({\threshold_pipes[1].remainder_s6_reg[27]_i_1_n_0 ,\threshold_pipes[1].remainder_s6_reg[27]_i_1_n_1 ,\threshold_pipes[1].remainder_s6_reg[27]_i_1_n_2 ,\threshold_pipes[1].remainder_s6_reg[27]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [27:24]),
        .O(\threshold_pipes[1].remainder_s601_out [27:24]),
        .S({\threshold_pipes[1].remainder_s6[27]_i_2_n_0 ,\threshold_pipes[1].remainder_s6[27]_i_3_n_0 ,\threshold_pipes[1].remainder_s6[27]_i_4_n_0 ,\threshold_pipes[1].remainder_s6[27]_i_5_n_0 }));
  FDRE \threshold_pipes[1].remainder_s6_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [28]),
        .Q(\threshold_pipes[1].remainder_s6 [28]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[29] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [29]),
        .Q(\threshold_pipes[1].remainder_s6 [29]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [2]),
        .Q(\threshold_pipes[1].remainder_s6 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[30] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [30]),
        .Q(\threshold_pipes[1].remainder_s6 [30]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[31] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [31]),
        .Q(\threshold_pipes[1].remainder_s6 [31]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[1].remainder_s6_reg[31]_i_1 
       (.CI(\threshold_pipes[1].remainder_s6_reg[27]_i_1_n_0 ),
        .CO({\NLW_threshold_pipes[1].remainder_s6_reg[31]_i_1_CO_UNCONNECTED [3],\threshold_pipes[1].remainder_s6_reg[31]_i_1_n_1 ,\threshold_pipes[1].remainder_s6_reg[31]_i_1_n_2 ,\threshold_pipes[1].remainder_s6_reg[31]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,\threshold_pipes[0].n_delay_reg[5] [30:28]}),
        .O(\threshold_pipes[1].remainder_s601_out [31:28]),
        .S({\threshold_pipes[1].remainder_s6[31]_i_2_n_0 ,\threshold_pipes[1].remainder_s6[31]_i_3_n_0 ,\threshold_pipes[1].remainder_s6[31]_i_4_n_0 ,\threshold_pipes[1].remainder_s6[31]_i_5_n_0 }));
  FDRE \threshold_pipes[1].remainder_s6_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [3]),
        .Q(\threshold_pipes[1].remainder_s6 [3]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[1].remainder_s6_reg[3]_i_1 
       (.CI(1'b0),
        .CO({\threshold_pipes[1].remainder_s6_reg[3]_i_1_n_0 ,\threshold_pipes[1].remainder_s6_reg[3]_i_1_n_1 ,\threshold_pipes[1].remainder_s6_reg[3]_i_1_n_2 ,\threshold_pipes[1].remainder_s6_reg[3]_i_1_n_3 }),
        .CYINIT(1'b1),
        .DI(\threshold_pipes[0].n_delay_reg[5] [3:0]),
        .O(\threshold_pipes[1].remainder_s601_out [3:0]),
        .S({\threshold_pipes[1].remainder_s6[3]_i_2_n_0 ,\threshold_pipes[1].remainder_s6[3]_i_3_n_0 ,\threshold_pipes[1].remainder_s6[3]_i_4_n_0 ,\threshold_pipes[1].remainder_s6[3]_i_5_n_0 }));
  FDRE \threshold_pipes[1].remainder_s6_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [4]),
        .Q(\threshold_pipes[1].remainder_s6 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [5]),
        .Q(\threshold_pipes[1].remainder_s6 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [6]),
        .Q(\threshold_pipes[1].remainder_s6 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [7]),
        .Q(\threshold_pipes[1].remainder_s6 [7]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[1].remainder_s6_reg[7]_i_1 
       (.CI(\threshold_pipes[1].remainder_s6_reg[3]_i_1_n_0 ),
        .CO({\threshold_pipes[1].remainder_s6_reg[7]_i_1_n_0 ,\threshold_pipes[1].remainder_s6_reg[7]_i_1_n_1 ,\threshold_pipes[1].remainder_s6_reg[7]_i_1_n_2 ,\threshold_pipes[1].remainder_s6_reg[7]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [7:4]),
        .O(\threshold_pipes[1].remainder_s601_out [7:4]),
        .S({\threshold_pipes[1].remainder_s6[7]_i_2_n_0 ,\threshold_pipes[1].remainder_s6[7]_i_3_n_0 ,\threshold_pipes[1].remainder_s6[7]_i_4_n_0 ,\threshold_pipes[1].remainder_s6[7]_i_5_n_0 }));
  FDRE \threshold_pipes[1].remainder_s6_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [8]),
        .Q(\threshold_pipes[1].remainder_s6 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[1].remainder_s6_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].remainder_s601_out [9]),
        .Q(\threshold_pipes[1].remainder_s6 [9]),
        .R(1'b0));
  LUT2 #(
    .INIT(4'hE)) 
    \threshold_pipes[1].threshold_live[1]_i_1 
       (.I0(\threshold_pipes[1].valid_pipe__0 ),
        .I1(live[1]),
        .O(\threshold_pipes[1].threshold_live[1]_i_1_n_0 ));
  FDRE \threshold_pipes[1].threshold_live_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].threshold_live[1]_i_1_n_0 ),
        .Q(live[1]),
        .R(reset));
  (* srl_bus_name = "\\threshold_pipes[1].valid_pipe_reg " *) 
  (* srl_name = "\\threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4 " *) 
  SRL16E \threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1_n_0 ),
        .Q(\threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ));
  LUT3 #(
    .INIT(8'h08)) 
    \threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1 
       (.I0(take),
        .I1(selected[0]),
        .I2(selected[1]),
        .O(\threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1_n_0 ));
  FDRE \threshold_pipes[1].valid_pipe_reg[6]_threshold_pipes_r_5 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[1].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ),
        .Q(\threshold_pipes[1].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ),
        .R(1'b0));
  FDRE \threshold_pipes[1].valid_pipe_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_gate__0_n_0),
        .Q(\threshold_pipes[1].valid_pipe__0 ),
        .R(reset));
  (* METHODOLOGY_DRC_VIOS = "{SYNTH-12 {cell *THIS*}}" *) 
  DSP48E1 #(
    .ACASCREG(0),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(0),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(0),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(0),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[2].check_hi_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[2].q_s3_reg_n_78 ,\threshold_pipes[2].q_s3_reg_n_79 ,\threshold_pipes[2].q_s3_reg_n_80 ,\threshold_pipes[2].q_s3_reg_n_81 ,\threshold_pipes[2].q_s3_reg_n_82 ,\threshold_pipes[2].q_s3_reg_n_83 ,\threshold_pipes[2].q_s3_reg_n_84 ,\threshold_pipes[2].q_s3_reg_n_85 ,\threshold_pipes[2].q_s3_reg_n_86 ,\threshold_pipes[2].q_s3_reg_n_87 ,\threshold_pipes[2].q_s3_reg_n_88 ,\threshold_pipes[2].q_s3_reg_n_89 }),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[2].check_hi_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1,1'b0,1'b1,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[2].check_hi_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[2].check_hi_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[2].check_hi_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b0),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b0),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[2].check_hi_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[2].check_hi_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[2].check_hi_reg_P_UNCONNECTED [47:16],\threshold_pipes[2].check_hi_reg_n_90 ,\threshold_pipes[2].check_hi_reg_n_91 ,\threshold_pipes[2].check_hi_reg_n_92 ,\threshold_pipes[2].check_hi_reg_n_93 ,\threshold_pipes[2].check_hi_reg_n_94 ,\threshold_pipes[2].check_hi_reg_n_95 ,\threshold_pipes[2].check_hi_reg_n_96 ,\threshold_pipes[2].check_hi_reg_n_97 ,\threshold_pipes[2].check_hi_reg_n_98 ,\threshold_pipes[2].check_hi_reg_n_99 ,\threshold_pipes[2].check_hi_reg_n_100 ,\threshold_pipes[2].check_hi_reg_n_101 ,\threshold_pipes[2].check_hi_reg_n_102 ,\threshold_pipes[2].check_hi_reg_n_103 ,\threshold_pipes[2].check_hi_reg_n_104 ,\threshold_pipes[2].check_hi_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[2].check_hi_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[2].check_hi_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[2].check_hi_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[2].check_hi_reg_UNDERFLOW_UNCONNECTED ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \threshold_pipes[2].count_threshold[2][3]_i_10 
       (.I0(\threshold_pipes[2].remainder_s6 [25]),
        .I1(\threshold_pipes[2].remainder_s6 [26]),
        .I2(\threshold_pipes[2].remainder_s6 [13]),
        .I3(\threshold_pipes[2].remainder_s6 [14]),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_10_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \threshold_pipes[2].count_threshold[2][3]_i_11 
       (.I0(\threshold_pipes[2].remainder_s6 [18]),
        .I1(\threshold_pipes[2].remainder_s6 [28]),
        .I2(\threshold_pipes[2].remainder_s6 [6]),
        .I3(\threshold_pipes[2].remainder_s6 [10]),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_11_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \threshold_pipes[2].count_threshold[2][3]_i_12 
       (.I0(\threshold_pipes[2].remainder_s6 [19]),
        .I1(\threshold_pipes[2].remainder_s6 [20]),
        .I2(\threshold_pipes[2].remainder_s6 [15]),
        .I3(\threshold_pipes[2].remainder_s6 [16]),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_12_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \threshold_pipes[2].count_threshold[2][3]_i_13 
       (.I0(\threshold_pipes[2].remainder_s6 [4]),
        .I1(\threshold_pipes[2].remainder_s6 [2]),
        .I2(\threshold_pipes[2].remainder_s6 [12]),
        .I3(\threshold_pipes[2].remainder_s6 [23]),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_13_n_0 ));
  LUT5 #(
    .INIT(32'h55555559)) 
    \threshold_pipes[2].count_threshold[2][3]_i_2 
       (.I0(\threshold_pipes[2].q_s6 [1]),
        .I1(\threshold_pipes[2].count_threshold[2][3]_i_4_n_0 ),
        .I2(\threshold_pipes[2].count_threshold[2][3]_i_5_n_0 ),
        .I3(\threshold_pipes[2].count_threshold[2][3]_i_6_n_0 ),
        .I4(\threshold_pipes[2].count_threshold[2][3]_i_7_n_0 ),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_2_n_0 ));
  LUT6 #(
    .INIT(64'hAAA9AAAAAAAAAAAA)) 
    \threshold_pipes[2].count_threshold[2][3]_i_3 
       (.I0(\threshold_pipes[2].q_s6 [0]),
        .I1(\threshold_pipes[2].count_threshold[2][3]_i_7_n_0 ),
        .I2(\threshold_pipes[2].count_threshold[2][3]_i_6_n_0 ),
        .I3(\threshold_pipes[2].count_threshold[2][3]_i_5_n_0 ),
        .I4(\threshold_pipes[2].count_threshold[2][3]_i_4_n_0 ),
        .I5(\threshold_pipes[2].count_threshold[2][3]_i_8_n_0 ),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_3_n_0 ));
  LUT6 #(
    .INIT(64'h0000000000000001)) 
    \threshold_pipes[2].count_threshold[2][3]_i_4 
       (.I0(\threshold_pipes[2].remainder_s6 [27]),
        .I1(\threshold_pipes[2].remainder_s6 [21]),
        .I2(\threshold_pipes[2].remainder_s6 [29]),
        .I3(\threshold_pipes[2].remainder_s6 [8]),
        .I4(\threshold_pipes[2].count_threshold[2][3]_i_9_n_0 ),
        .I5(\threshold_pipes[2].count_threshold[2][3]_i_10_n_0 ),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_4_n_0 ));
  LUT4 #(
    .INIT(16'hA888)) 
    \threshold_pipes[2].count_threshold[2][3]_i_5 
       (.I0(\threshold_pipes[2].remainder_s6 [5]),
        .I1(\threshold_pipes[2].remainder_s6 [4]),
        .I2(\threshold_pipes[2].remainder_s6 [2]),
        .I3(\threshold_pipes[2].remainder_s6 [3]),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_5_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[2].count_threshold[2][3]_i_6 
       (.I0(\threshold_pipes[2].remainder_s6 [16]),
        .I1(\threshold_pipes[2].remainder_s6 [15]),
        .I2(\threshold_pipes[2].remainder_s6 [20]),
        .I3(\threshold_pipes[2].remainder_s6 [19]),
        .I4(\threshold_pipes[2].remainder_s6 [12]),
        .I5(\threshold_pipes[2].remainder_s6 [23]),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_6_n_0 ));
  LUT5 #(
    .INIT(32'hFFFFFFFE)) 
    \threshold_pipes[2].count_threshold[2][3]_i_7 
       (.I0(\threshold_pipes[2].remainder_s6 [31]),
        .I1(\threshold_pipes[2].remainder_s6 [17]),
        .I2(\threshold_pipes[2].remainder_s6 [9]),
        .I3(\threshold_pipes[2].remainder_s6 [7]),
        .I4(\threshold_pipes[2].count_threshold[2][3]_i_11_n_0 ),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_7_n_0 ));
  LUT6 #(
    .INIT(64'hFFFFFFFFFFFFFFFE)) 
    \threshold_pipes[2].count_threshold[2][3]_i_8 
       (.I0(\threshold_pipes[2].count_threshold[2][3]_i_12_n_0 ),
        .I1(\threshold_pipes[2].count_threshold[2][3]_i_13_n_0 ),
        .I2(\threshold_pipes[2].remainder_s6 [0]),
        .I3(\threshold_pipes[2].remainder_s6 [3]),
        .I4(\threshold_pipes[2].remainder_s6 [1]),
        .I5(\threshold_pipes[2].remainder_s6 [5]),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_8_n_0 ));
  LUT4 #(
    .INIT(16'hFFFE)) 
    \threshold_pipes[2].count_threshold[2][3]_i_9 
       (.I0(\threshold_pipes[2].remainder_s6 [24]),
        .I1(\threshold_pipes[2].remainder_s6 [30]),
        .I2(\threshold_pipes[2].remainder_s6 [11]),
        .I3(\threshold_pipes[2].remainder_s6 [22]),
        .O(\threshold_pipes[2].count_threshold[2][3]_i_9_n_0 ));
  FDRE \threshold_pipes[2].count_threshold_reg[2][0] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_7 ),
        .Q(\^meta_threshold3 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][10] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_5 ),
        .Q(\^meta_threshold3 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][11] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_4 ),
        .Q(\^meta_threshold3 [11]),
        .R(1'b0));
  CARRY4 \threshold_pipes[2].count_threshold_reg[2][11]_i_1 
       (.CI(\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_0 ),
        .CO({\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_0 ,\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_1 ,\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_2 ,\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_4 ,\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_5 ,\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_6 ,\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_7 }),
        .S(\threshold_pipes[2].q_s6 [11:8]));
  FDRE \threshold_pipes[2].count_threshold_reg[2][12] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_7 ),
        .Q(\^meta_threshold3 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][13] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_6 ),
        .Q(\^meta_threshold3 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][14] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_5 ),
        .Q(\^meta_threshold3 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][15] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_4 ),
        .Q(\^meta_threshold3 [15]),
        .R(1'b0));
  CARRY4 \threshold_pipes[2].count_threshold_reg[2][15]_i_1 
       (.CI(\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_0 ),
        .CO({\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_0 ,\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_1 ,\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_2 ,\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_4 ,\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_5 ,\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_6 ,\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_7 }),
        .S(\threshold_pipes[2].q_s6 [15:12]));
  FDRE \threshold_pipes[2].count_threshold_reg[2][16] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_7 ),
        .Q(\^meta_threshold3 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][17] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_6 ),
        .Q(\^meta_threshold3 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][18] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_5 ),
        .Q(\^meta_threshold3 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][19] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_4 ),
        .Q(\^meta_threshold3 [19]),
        .R(1'b0));
  CARRY4 \threshold_pipes[2].count_threshold_reg[2][19]_i_1 
       (.CI(\threshold_pipes[2].count_threshold_reg[2][15]_i_1_n_0 ),
        .CO({\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_0 ,\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_1 ,\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_2 ,\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_4 ,\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_5 ,\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_6 ,\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_7 }),
        .S(\threshold_pipes[2].q_s6 [19:16]));
  FDRE \threshold_pipes[2].count_threshold_reg[2][1] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_6 ),
        .Q(\^meta_threshold3 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][20] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_7 ),
        .Q(\^meta_threshold3 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][21] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_6 ),
        .Q(\^meta_threshold3 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][22] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_5 ),
        .Q(\^meta_threshold3 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][23] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_4 ),
        .Q(\^meta_threshold3 [23]),
        .R(1'b0));
  CARRY4 \threshold_pipes[2].count_threshold_reg[2][23]_i_1 
       (.CI(\threshold_pipes[2].count_threshold_reg[2][19]_i_1_n_0 ),
        .CO({\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_0 ,\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_1 ,\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_2 ,\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_4 ,\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_5 ,\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_6 ,\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_7 }),
        .S(\threshold_pipes[2].q_s6 [23:20]));
  FDRE \threshold_pipes[2].count_threshold_reg[2][24] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_7 ),
        .Q(\^meta_threshold3 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][25] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_6 ),
        .Q(\^meta_threshold3 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][26] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_5 ),
        .Q(\^meta_threshold3 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][27] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_4 ),
        .Q(\^meta_threshold3 [27]),
        .R(1'b0));
  CARRY4 \threshold_pipes[2].count_threshold_reg[2][27]_i_1 
       (.CI(\threshold_pipes[2].count_threshold_reg[2][23]_i_1_n_0 ),
        .CO({\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_0 ,\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_1 ,\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_2 ,\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_4 ,\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_5 ,\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_6 ,\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_7 }),
        .S(\threshold_pipes[2].q_s6 [27:24]));
  FDRE \threshold_pipes[2].count_threshold_reg[2][28] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][28]_i_1_n_3 ),
        .Q(\^meta_threshold3 [28]),
        .R(1'b0));
  CARRY4 \threshold_pipes[2].count_threshold_reg[2][28]_i_1 
       (.CI(\threshold_pipes[2].count_threshold_reg[2][27]_i_1_n_0 ),
        .CO({\NLW_threshold_pipes[2].count_threshold_reg[2][28]_i_1_CO_UNCONNECTED [3:1],\threshold_pipes[2].count_threshold_reg[2][28]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\NLW_threshold_pipes[2].count_threshold_reg[2][28]_i_1_O_UNCONNECTED [3:0]),
        .S({1'b0,1'b0,1'b0,1'b1}));
  FDRE \threshold_pipes[2].count_threshold_reg[2][2] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_5 ),
        .Q(\^meta_threshold3 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][3] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_4 ),
        .Q(\^meta_threshold3 [3]),
        .R(1'b0));
  CARRY4 \threshold_pipes[2].count_threshold_reg[2][3]_i_1 
       (.CI(1'b0),
        .CO({\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_0 ,\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_1 ,\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_2 ,\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,\threshold_pipes[2].q_s6 [1:0]}),
        .O({\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_4 ,\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_5 ,\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_6 ,\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_7 }),
        .S({\threshold_pipes[2].q_s6 [3:2],\threshold_pipes[2].count_threshold[2][3]_i_2_n_0 ,\threshold_pipes[2].count_threshold[2][3]_i_3_n_0 }));
  FDRE \threshold_pipes[2].count_threshold_reg[2][4] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_7 ),
        .Q(\^meta_threshold3 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][5] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_6 ),
        .Q(\^meta_threshold3 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][6] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_5 ),
        .Q(\^meta_threshold3 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][7] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_4 ),
        .Q(\^meta_threshold3 [7]),
        .R(1'b0));
  CARRY4 \threshold_pipes[2].count_threshold_reg[2][7]_i_1 
       (.CI(\threshold_pipes[2].count_threshold_reg[2][3]_i_1_n_0 ),
        .CO({\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_0 ,\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_1 ,\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_2 ,\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_4 ,\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_5 ,\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_6 ,\threshold_pipes[2].count_threshold_reg[2][7]_i_1_n_7 }),
        .S(\threshold_pipes[2].q_s6 [7:4]));
  FDRE \threshold_pipes[2].count_threshold_reg[2][8] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_7 ),
        .Q(\^meta_threshold3 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[2].count_threshold_reg[2][9] 
       (.C(clk),
        .CE(\threshold_pipes[2].valid_pipe__0 ),
        .D(\threshold_pipes[2].count_threshold_reg[2][11]_i_1_n_6 ),
        .Q(\^meta_threshold3 [9]),
        .R(1'b0));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[2].cross_s1_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[31:16]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[2].cross_s1_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1,1'b1,1'b1,1'b1,1'b1,1'b0,1'b1,1'b0,1'b0,1'b0,1'b0}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[2].cross_s1_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[2].cross_s1_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[2].cross_s1_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[2].cross_s1_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b0,1'b1,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[2].cross_s1_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[2].cross_s1_reg_P_UNCONNECTED [47:30],\threshold_pipes[2].cross_s1_reg_n_76 ,\threshold_pipes[2].cross_s1_reg_n_77 ,\threshold_pipes[2].cross_s1_reg_n_78 ,\threshold_pipes[2].cross_s1_reg_n_79 ,\threshold_pipes[2].cross_s1_reg_n_80 ,\threshold_pipes[2].cross_s1_reg_n_81 ,\threshold_pipes[2].cross_s1_reg_n_82 ,\threshold_pipes[2].cross_s1_reg_n_83 ,\threshold_pipes[2].cross_s1_reg_n_84 ,\threshold_pipes[2].cross_s1_reg_n_85 ,\threshold_pipes[2].cross_s1_reg_n_86 ,\threshold_pipes[2].cross_s1_reg_n_87 ,\threshold_pipes[2].cross_s1_reg_n_88 ,\threshold_pipes[2].cross_s1_reg_n_89 ,\threshold_pipes[2].cross_s1_reg_n_90 ,\threshold_pipes[2].cross_s1_reg_n_91 ,\threshold_pipes[2].cross_s1_reg_n_92 ,\threshold_pipes[2].cross_s1_reg_n_93 ,\threshold_pipes[2].cross_s1_reg_n_94 ,\threshold_pipes[2].cross_s1_reg_n_95 ,\threshold_pipes[2].cross_s1_reg_n_96 ,\threshold_pipes[2].cross_s1_reg_n_97 ,\threshold_pipes[2].cross_s1_reg_n_98 ,\threshold_pipes[2].cross_s1_reg_n_99 ,\threshold_pipes[2].cross_s1_reg_n_100 ,\threshold_pipes[2].cross_s1_reg_n_101 ,\threshold_pipes[2].cross_s1_reg_n_102 ,\threshold_pipes[2].cross_s1_reg_n_103 ,\threshold_pipes[2].cross_s1_reg_n_104 ,\threshold_pipes[2].cross_s1_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[2].cross_s1_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[2].cross_s1_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({\threshold_pipes[2].mul01_reg_n_106 ,\threshold_pipes[2].mul01_reg_n_107 ,\threshold_pipes[2].mul01_reg_n_108 ,\threshold_pipes[2].mul01_reg_n_109 ,\threshold_pipes[2].mul01_reg_n_110 ,\threshold_pipes[2].mul01_reg_n_111 ,\threshold_pipes[2].mul01_reg_n_112 ,\threshold_pipes[2].mul01_reg_n_113 ,\threshold_pipes[2].mul01_reg_n_114 ,\threshold_pipes[2].mul01_reg_n_115 ,\threshold_pipes[2].mul01_reg_n_116 ,\threshold_pipes[2].mul01_reg_n_117 ,\threshold_pipes[2].mul01_reg_n_118 ,\threshold_pipes[2].mul01_reg_n_119 ,\threshold_pipes[2].mul01_reg_n_120 ,\threshold_pipes[2].mul01_reg_n_121 ,\threshold_pipes[2].mul01_reg_n_122 ,\threshold_pipes[2].mul01_reg_n_123 ,\threshold_pipes[2].mul01_reg_n_124 ,\threshold_pipes[2].mul01_reg_n_125 ,\threshold_pipes[2].mul01_reg_n_126 ,\threshold_pipes[2].mul01_reg_n_127 ,\threshold_pipes[2].mul01_reg_n_128 ,\threshold_pipes[2].mul01_reg_n_129 ,\threshold_pipes[2].mul01_reg_n_130 ,\threshold_pipes[2].mul01_reg_n_131 ,\threshold_pipes[2].mul01_reg_n_132 ,\threshold_pipes[2].mul01_reg_n_133 ,\threshold_pipes[2].mul01_reg_n_134 ,\threshold_pipes[2].mul01_reg_n_135 ,\threshold_pipes[2].mul01_reg_n_136 ,\threshold_pipes[2].mul01_reg_n_137 ,\threshold_pipes[2].mul01_reg_n_138 ,\threshold_pipes[2].mul01_reg_n_139 ,\threshold_pipes[2].mul01_reg_n_140 ,\threshold_pipes[2].mul01_reg_n_141 ,\threshold_pipes[2].mul01_reg_n_142 ,\threshold_pipes[2].mul01_reg_n_143 ,\threshold_pipes[2].mul01_reg_n_144 ,\threshold_pipes[2].mul01_reg_n_145 ,\threshold_pipes[2].mul01_reg_n_146 ,\threshold_pipes[2].mul01_reg_n_147 ,\threshold_pipes[2].mul01_reg_n_148 ,\threshold_pipes[2].mul01_reg_n_149 ,\threshold_pipes[2].mul01_reg_n_150 ,\threshold_pipes[2].mul01_reg_n_151 ,\threshold_pipes[2].mul01_reg_n_152 ,\threshold_pipes[2].mul01_reg_n_153 }),
        .PCOUT(\NLW_threshold_pipes[2].cross_s1_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[2].cross_s1_reg_UNDERFLOW_UNCONNECTED ));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[2].mul00_hi_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[15:0]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[2].mul00_hi_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1,1'b1,1'b1,1'b1,1'b1,1'b0,1'b1,1'b0,1'b0,1'b0,1'b0}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[2].mul00_hi_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[2].mul00_hi_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[2].mul00_hi_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[2].mul00_hi_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[2].mul00_hi_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[2].mul00_hi_reg_P_UNCONNECTED [47:29],\threshold_pipes[2].low_carry_s1 ,\threshold_pipes[2].mul00_hi_reg_n_90 ,\threshold_pipes[2].mul00_hi_reg_n_91 ,\threshold_pipes[2].mul00_hi_reg_n_92 ,\threshold_pipes[2].mul00_hi_reg_n_93 ,\threshold_pipes[2].mul00_hi_reg_n_94 ,\threshold_pipes[2].mul00_hi_reg_n_95 ,\threshold_pipes[2].mul00_hi_reg_n_96 ,\threshold_pipes[2].mul00_hi_reg_n_97 ,\threshold_pipes[2].mul00_hi_reg_n_98 ,\threshold_pipes[2].mul00_hi_reg_n_99 ,\threshold_pipes[2].mul00_hi_reg_n_100 ,\threshold_pipes[2].mul00_hi_reg_n_101 ,\threshold_pipes[2].mul00_hi_reg_n_102 ,\threshold_pipes[2].mul00_hi_reg_n_103 ,\threshold_pipes[2].mul00_hi_reg_n_104 ,\threshold_pipes[2].mul00_hi_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[2].mul00_hi_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[2].mul00_hi_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[2].mul00_hi_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[2].mul00_hi_reg_UNDERFLOW_UNCONNECTED ));
  DSP48E1 #(
    .ACASCREG(1),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(1),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(0),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(0),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[2].mul01_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,numerator[15:0]}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[2].mul01_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1,1'b1,1'b1,1'b1,1'b1,1'b0,1'b1,1'b0,1'b0}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[2].mul01_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1,1'b1}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[2].mul01_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[2].mul01_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b0),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[2].mul01_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[2].mul01_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[2].mul01_reg_P_UNCONNECTED [47:27],\threshold_pipes[2].mul01_reg_n_79 ,\threshold_pipes[2].mul01_reg_n_80 ,\threshold_pipes[2].mul01_reg_n_81 ,\threshold_pipes[2].mul01_reg_n_82 ,\threshold_pipes[2].mul01_reg_n_83 ,\threshold_pipes[2].mul01_reg_n_84 ,\threshold_pipes[2].mul01_reg_n_85 ,\threshold_pipes[2].mul01_reg_n_86 ,\threshold_pipes[2].mul01_reg_n_87 ,\threshold_pipes[2].mul01_reg_n_88 ,\threshold_pipes[2].mul01_reg_n_89 ,\threshold_pipes[2].mul01_reg_n_90 ,\threshold_pipes[2].mul01_reg_n_91 ,\threshold_pipes[2].mul01_reg_n_92 ,\threshold_pipes[2].mul01_reg_n_93 ,\threshold_pipes[2].mul01_reg_n_94 ,\threshold_pipes[2].mul01_reg_n_95 ,\threshold_pipes[2].mul01_reg_n_96 ,\threshold_pipes[2].mul01_reg_n_97 ,\threshold_pipes[2].mul01_reg_n_98 ,\threshold_pipes[2].mul01_reg_n_99 ,\threshold_pipes[2].mul01_reg_n_100 ,\threshold_pipes[2].mul01_reg_n_101 ,\threshold_pipes[2].mul01_reg_n_102 ,\threshold_pipes[2].mul01_reg_n_103 ,\threshold_pipes[2].mul01_reg_n_104 ,\threshold_pipes[2].mul01_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[2].mul01_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[2].mul01_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT({\threshold_pipes[2].mul01_reg_n_106 ,\threshold_pipes[2].mul01_reg_n_107 ,\threshold_pipes[2].mul01_reg_n_108 ,\threshold_pipes[2].mul01_reg_n_109 ,\threshold_pipes[2].mul01_reg_n_110 ,\threshold_pipes[2].mul01_reg_n_111 ,\threshold_pipes[2].mul01_reg_n_112 ,\threshold_pipes[2].mul01_reg_n_113 ,\threshold_pipes[2].mul01_reg_n_114 ,\threshold_pipes[2].mul01_reg_n_115 ,\threshold_pipes[2].mul01_reg_n_116 ,\threshold_pipes[2].mul01_reg_n_117 ,\threshold_pipes[2].mul01_reg_n_118 ,\threshold_pipes[2].mul01_reg_n_119 ,\threshold_pipes[2].mul01_reg_n_120 ,\threshold_pipes[2].mul01_reg_n_121 ,\threshold_pipes[2].mul01_reg_n_122 ,\threshold_pipes[2].mul01_reg_n_123 ,\threshold_pipes[2].mul01_reg_n_124 ,\threshold_pipes[2].mul01_reg_n_125 ,\threshold_pipes[2].mul01_reg_n_126 ,\threshold_pipes[2].mul01_reg_n_127 ,\threshold_pipes[2].mul01_reg_n_128 ,\threshold_pipes[2].mul01_reg_n_129 ,\threshold_pipes[2].mul01_reg_n_130 ,\threshold_pipes[2].mul01_reg_n_131 ,\threshold_pipes[2].mul01_reg_n_132 ,\threshold_pipes[2].mul01_reg_n_133 ,\threshold_pipes[2].mul01_reg_n_134 ,\threshold_pipes[2].mul01_reg_n_135 ,\threshold_pipes[2].mul01_reg_n_136 ,\threshold_pipes[2].mul01_reg_n_137 ,\threshold_pipes[2].mul01_reg_n_138 ,\threshold_pipes[2].mul01_reg_n_139 ,\threshold_pipes[2].mul01_reg_n_140 ,\threshold_pipes[2].mul01_reg_n_141 ,\threshold_pipes[2].mul01_reg_n_142 ,\threshold_pipes[2].mul01_reg_n_143 ,\threshold_pipes[2].mul01_reg_n_144 ,\threshold_pipes[2].mul01_reg_n_145 ,\threshold_pipes[2].mul01_reg_n_146 ,\threshold_pipes[2].mul01_reg_n_147 ,\threshold_pipes[2].mul01_reg_n_148 ,\threshold_pipes[2].mul01_reg_n_149 ,\threshold_pipes[2].mul01_reg_n_150 ,\threshold_pipes[2].mul01_reg_n_151 ,\threshold_pipes[2].mul01_reg_n_152 ,\threshold_pipes[2].mul01_reg_n_153 }),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[2].mul01_reg_UNDERFLOW_UNCONNECTED ));
  (* METHODOLOGY_DRC_VIOS = "{SYNTH-12 {cell *THIS*}}" *) 
  DSP48E1 #(
    .ACASCREG(0),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(0),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(0),
    .BREG(0),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(0),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[2].product_s5_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[2].q_s3_reg_n_90 ,\threshold_pipes[2].q_s3_reg_n_91 ,\threshold_pipes[2].q_s3_reg_n_92 ,\threshold_pipes[2].q_s3_reg_n_93 ,\threshold_pipes[2].q_s3_reg_n_94 ,\threshold_pipes[2].q_s3_reg_n_95 ,\threshold_pipes[2].q_s3_reg_n_96 ,\threshold_pipes[2].q_s3_reg_n_97 ,\threshold_pipes[2].q_s3_reg_n_98 ,\threshold_pipes[2].q_s3_reg_n_99 ,\threshold_pipes[2].q_s3_reg_n_100 ,\threshold_pipes[2].q_s3_reg_n_101 ,\threshold_pipes[2].q_s3_reg_n_102 ,\threshold_pipes[2].q_s3_reg_n_103 ,\threshold_pipes[2].q_s3_reg_n_104 ,\threshold_pipes[2].q_s3_reg_n_105 }),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[2].product_s5_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1,1'b0,1'b1,1'b1}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[2].product_s5_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[2].check_hi_reg_n_90 ,\threshold_pipes[2].check_hi_reg_n_91 ,\threshold_pipes[2].check_hi_reg_n_92 ,\threshold_pipes[2].check_hi_reg_n_93 ,\threshold_pipes[2].check_hi_reg_n_94 ,\threshold_pipes[2].check_hi_reg_n_95 ,\threshold_pipes[2].check_hi_reg_n_96 ,\threshold_pipes[2].check_hi_reg_n_97 ,\threshold_pipes[2].check_hi_reg_n_98 ,\threshold_pipes[2].check_hi_reg_n_99 ,\threshold_pipes[2].check_hi_reg_n_100 ,\threshold_pipes[2].check_hi_reg_n_101 ,\threshold_pipes[2].check_hi_reg_n_102 ,\threshold_pipes[2].check_hi_reg_n_103 ,\threshold_pipes[2].check_hi_reg_n_104 ,\threshold_pipes[2].check_hi_reg_n_105 ,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[2].product_s5_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[2].product_s5_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b0),
        .CEA2(1'b0),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b0),
        .CEB2(1'b0),
        .CEC(1'b0),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[2].product_s5_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b1,1'b1,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[2].product_s5_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[2].product_s5_reg_P_UNCONNECTED [47:32],\threshold_pipes[2].product_s5_reg__0 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[2].product_s5_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[2].product_s5_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[2].product_s5_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[2].product_s5_reg_UNDERFLOW_UNCONNECTED ));
  DSP48E1 #(
    .ACASCREG(2),
    .ADREG(1),
    .ALUMODEREG(0),
    .AREG(2),
    .AUTORESET_PATDET("NO_RESET"),
    .A_INPUT("DIRECT"),
    .BCASCREG(2),
    .BREG(2),
    .B_INPUT("DIRECT"),
    .CARRYINREG(0),
    .CARRYINSELREG(0),
    .CREG(1),
    .DREG(1),
    .INMODEREG(0),
    .MASK(48'h3FFFFFFFFFFF),
    .MREG(1),
    .OPMODEREG(0),
    .PATTERN(48'h000000000000),
    .PREG(1),
    .SEL_MASK("MASK"),
    .SEL_PATTERN("PATTERN"),
    .USE_DPORT("FALSE"),
    .USE_MULT("MULTIPLY"),
    .USE_PATTERN_DETECT("NO_PATDET"),
    .USE_SIMD("ONE48")) 
    \threshold_pipes[2].q_s3_reg 
       (.A({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,A}),
        .ACIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .ACOUT(\NLW_threshold_pipes[2].q_s3_reg_ACOUT_UNCONNECTED [29:0]),
        .ALUMODE({1'b0,1'b0,1'b0,1'b0}),
        .B({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b1,1'b0,1'b1,1'b1,1'b1,1'b1,1'b1,1'b0,1'b1,1'b0,1'b0}),
        .BCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .BCOUT(\NLW_threshold_pipes[2].q_s3_reg_BCOUT_UNCONNECTED [17:0]),
        .C({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,\threshold_pipes[2].cross_carry_s21 }),
        .CARRYCASCIN(1'b0),
        .CARRYCASCOUT(\NLW_threshold_pipes[2].q_s3_reg_CARRYCASCOUT_UNCONNECTED ),
        .CARRYIN(1'b0),
        .CARRYINSEL({1'b0,1'b0,1'b0}),
        .CARRYOUT(\NLW_threshold_pipes[2].q_s3_reg_CARRYOUT_UNCONNECTED [3:0]),
        .CEA1(1'b1),
        .CEA2(1'b1),
        .CEAD(1'b0),
        .CEALUMODE(1'b0),
        .CEB1(1'b1),
        .CEB2(1'b1),
        .CEC(1'b1),
        .CECARRYIN(1'b0),
        .CECTRL(1'b0),
        .CED(1'b0),
        .CEINMODE(1'b0),
        .CEM(1'b1),
        .CEP(1'b1),
        .CLK(clk),
        .D({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .INMODE({1'b0,1'b0,1'b0,1'b0,1'b0}),
        .MULTSIGNIN(1'b0),
        .MULTSIGNOUT(\NLW_threshold_pipes[2].q_s3_reg_MULTSIGNOUT_UNCONNECTED ),
        .OPMODE({1'b0,1'b1,1'b1,1'b0,1'b1,1'b0,1'b1}),
        .OVERFLOW(\NLW_threshold_pipes[2].q_s3_reg_OVERFLOW_UNCONNECTED ),
        .P({\NLW_threshold_pipes[2].q_s3_reg_P_UNCONNECTED [47:28],\threshold_pipes[2].q_s3_reg_n_78 ,\threshold_pipes[2].q_s3_reg_n_79 ,\threshold_pipes[2].q_s3_reg_n_80 ,\threshold_pipes[2].q_s3_reg_n_81 ,\threshold_pipes[2].q_s3_reg_n_82 ,\threshold_pipes[2].q_s3_reg_n_83 ,\threshold_pipes[2].q_s3_reg_n_84 ,\threshold_pipes[2].q_s3_reg_n_85 ,\threshold_pipes[2].q_s3_reg_n_86 ,\threshold_pipes[2].q_s3_reg_n_87 ,\threshold_pipes[2].q_s3_reg_n_88 ,\threshold_pipes[2].q_s3_reg_n_89 ,\threshold_pipes[2].q_s3_reg_n_90 ,\threshold_pipes[2].q_s3_reg_n_91 ,\threshold_pipes[2].q_s3_reg_n_92 ,\threshold_pipes[2].q_s3_reg_n_93 ,\threshold_pipes[2].q_s3_reg_n_94 ,\threshold_pipes[2].q_s3_reg_n_95 ,\threshold_pipes[2].q_s3_reg_n_96 ,\threshold_pipes[2].q_s3_reg_n_97 ,\threshold_pipes[2].q_s3_reg_n_98 ,\threshold_pipes[2].q_s3_reg_n_99 ,\threshold_pipes[2].q_s3_reg_n_100 ,\threshold_pipes[2].q_s3_reg_n_101 ,\threshold_pipes[2].q_s3_reg_n_102 ,\threshold_pipes[2].q_s3_reg_n_103 ,\threshold_pipes[2].q_s3_reg_n_104 ,\threshold_pipes[2].q_s3_reg_n_105 }),
        .PATTERNBDETECT(\NLW_threshold_pipes[2].q_s3_reg_PATTERNBDETECT_UNCONNECTED ),
        .PATTERNDETECT(\NLW_threshold_pipes[2].q_s3_reg_PATTERNDETECT_UNCONNECTED ),
        .PCIN({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .PCOUT(\NLW_threshold_pipes[2].q_s3_reg_PCOUT_UNCONNECTED [47:0]),
        .RSTA(1'b0),
        .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0),
        .RSTB(1'b0),
        .RSTC(1'b0),
        .RSTCTRL(1'b0),
        .RSTD(1'b0),
        .RSTINMODE(1'b0),
        .RSTM(1'b0),
        .RSTP(1'b0),
        .UNDERFLOW(\NLW_threshold_pipes[2].q_s3_reg_UNDERFLOW_UNCONNECTED ));
  CARRY4 \threshold_pipes[2].q_s3_reg_i_1 
       (.CI(\threshold_pipes[2].q_s3_reg_i_2_n_0 ),
        .CO({\NLW_threshold_pipes[2].q_s3_reg_i_1_CO_UNCONNECTED [3],\threshold_pipes[2].cross_carry_s21 [30],\NLW_threshold_pipes[2].q_s3_reg_i_1_CO_UNCONNECTED [1],\threshold_pipes[2].q_s3_reg_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O({\NLW_threshold_pipes[2].q_s3_reg_i_1_O_UNCONNECTED [3:2],\threshold_pipes[2].cross_carry_s21 [29:28]}),
        .S({1'b0,1'b1,\threshold_pipes[2].cross_s1_reg_n_76 ,\threshold_pipes[2].cross_s1_reg_n_77 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_10 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_95 ),
        .I1(\threshold_pipes[2].low_carry_s1 [10]),
        .O(\threshold_pipes[2].q_s3_reg_i_10_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_11 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_96 ),
        .I1(\threshold_pipes[2].low_carry_s1 [9]),
        .O(\threshold_pipes[2].q_s3_reg_i_11_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_12 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_97 ),
        .I1(\threshold_pipes[2].low_carry_s1 [8]),
        .O(\threshold_pipes[2].q_s3_reg_i_12_n_0 ));
  CARRY4 \threshold_pipes[2].q_s3_reg_i_13 
       (.CI(1'b0),
        .CO({\threshold_pipes[2].q_s3_reg_i_13_n_0 ,\threshold_pipes[2].q_s3_reg_i_13_n_1 ,\threshold_pipes[2].q_s3_reg_i_13_n_2 ,\threshold_pipes[2].q_s3_reg_i_13_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[2].cross_s1_reg_n_102 ,\threshold_pipes[2].cross_s1_reg_n_103 ,\threshold_pipes[2].cross_s1_reg_n_104 ,\threshold_pipes[2].cross_s1_reg_n_105 }),
        .O(\NLW_threshold_pipes[2].q_s3_reg_i_13_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[2].q_s3_reg_i_18_n_0 ,\threshold_pipes[2].q_s3_reg_i_19_n_0 ,\threshold_pipes[2].q_s3_reg_i_20_n_0 ,\threshold_pipes[2].q_s3_reg_i_21_n_0 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_14 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_98 ),
        .I1(\threshold_pipes[2].low_carry_s1 [7]),
        .O(\threshold_pipes[2].q_s3_reg_i_14_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_15 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_99 ),
        .I1(\threshold_pipes[2].low_carry_s1 [6]),
        .O(\threshold_pipes[2].q_s3_reg_i_15_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_16 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_100 ),
        .I1(\threshold_pipes[2].low_carry_s1 [5]),
        .O(\threshold_pipes[2].q_s3_reg_i_16_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_17 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_101 ),
        .I1(\threshold_pipes[2].low_carry_s1 [4]),
        .O(\threshold_pipes[2].q_s3_reg_i_17_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_18 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_102 ),
        .I1(\threshold_pipes[2].low_carry_s1 [3]),
        .O(\threshold_pipes[2].q_s3_reg_i_18_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_19 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_103 ),
        .I1(\threshold_pipes[2].low_carry_s1 [2]),
        .O(\threshold_pipes[2].q_s3_reg_i_19_n_0 ));
  CARRY4 \threshold_pipes[2].q_s3_reg_i_2 
       (.CI(\threshold_pipes[2].q_s3_reg_i_3_n_0 ),
        .CO({\threshold_pipes[2].q_s3_reg_i_2_n_0 ,\threshold_pipes[2].q_s3_reg_i_2_n_1 ,\threshold_pipes[2].q_s3_reg_i_2_n_2 ,\threshold_pipes[2].q_s3_reg_i_2_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[2].cross_carry_s21 [27:24]),
        .S({\threshold_pipes[2].cross_s1_reg_n_78 ,\threshold_pipes[2].cross_s1_reg_n_79 ,\threshold_pipes[2].cross_s1_reg_n_80 ,\threshold_pipes[2].cross_s1_reg_n_81 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_20 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_104 ),
        .I1(\threshold_pipes[2].low_carry_s1 [1]),
        .O(\threshold_pipes[2].q_s3_reg_i_20_n_0 ));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_21 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_105 ),
        .I1(\threshold_pipes[2].low_carry_s1 [0]),
        .O(\threshold_pipes[2].q_s3_reg_i_21_n_0 ));
  CARRY4 \threshold_pipes[2].q_s3_reg_i_3 
       (.CI(\threshold_pipes[2].q_s3_reg_i_4_n_0 ),
        .CO({\threshold_pipes[2].q_s3_reg_i_3_n_0 ,\threshold_pipes[2].q_s3_reg_i_3_n_1 ,\threshold_pipes[2].q_s3_reg_i_3_n_2 ,\threshold_pipes[2].q_s3_reg_i_3_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[2].cross_carry_s21 [23:20]),
        .S({\threshold_pipes[2].cross_s1_reg_n_82 ,\threshold_pipes[2].cross_s1_reg_n_83 ,\threshold_pipes[2].cross_s1_reg_n_84 ,\threshold_pipes[2].cross_s1_reg_n_85 }));
  CARRY4 \threshold_pipes[2].q_s3_reg_i_4 
       (.CI(\threshold_pipes[2].q_s3_reg_i_5_n_0 ),
        .CO({\threshold_pipes[2].q_s3_reg_i_4_n_0 ,\threshold_pipes[2].q_s3_reg_i_4_n_1 ,\threshold_pipes[2].q_s3_reg_i_4_n_2 ,\threshold_pipes[2].q_s3_reg_i_4_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,1'b0}),
        .O(\threshold_pipes[2].cross_carry_s21 [19:16]),
        .S({\threshold_pipes[2].cross_s1_reg_n_86 ,\threshold_pipes[2].cross_s1_reg_n_87 ,\threshold_pipes[2].cross_s1_reg_n_88 ,\threshold_pipes[2].cross_s1_reg_n_89 }));
  CARRY4 \threshold_pipes[2].q_s3_reg_i_5 
       (.CI(\threshold_pipes[2].q_s3_reg_i_6_n_0 ),
        .CO({\threshold_pipes[2].q_s3_reg_i_5_n_0 ,\threshold_pipes[2].q_s3_reg_i_5_n_1 ,\threshold_pipes[2].q_s3_reg_i_5_n_2 ,\threshold_pipes[2].q_s3_reg_i_5_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,1'b0,1'b0,\threshold_pipes[2].cross_s1_reg_n_93 }),
        .O(\NLW_threshold_pipes[2].q_s3_reg_i_5_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[2].cross_s1_reg_n_90 ,\threshold_pipes[2].cross_s1_reg_n_91 ,\threshold_pipes[2].cross_s1_reg_n_92 ,\threshold_pipes[2].q_s3_reg_i_7_n_0 }));
  CARRY4 \threshold_pipes[2].q_s3_reg_i_6 
       (.CI(\threshold_pipes[2].q_s3_reg_i_8_n_0 ),
        .CO({\threshold_pipes[2].q_s3_reg_i_6_n_0 ,\threshold_pipes[2].q_s3_reg_i_6_n_1 ,\threshold_pipes[2].q_s3_reg_i_6_n_2 ,\threshold_pipes[2].q_s3_reg_i_6_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[2].cross_s1_reg_n_94 ,\threshold_pipes[2].cross_s1_reg_n_95 ,\threshold_pipes[2].cross_s1_reg_n_96 ,\threshold_pipes[2].cross_s1_reg_n_97 }),
        .O(\NLW_threshold_pipes[2].q_s3_reg_i_6_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[2].q_s3_reg_i_9_n_0 ,\threshold_pipes[2].q_s3_reg_i_10_n_0 ,\threshold_pipes[2].q_s3_reg_i_11_n_0 ,\threshold_pipes[2].q_s3_reg_i_12_n_0 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_7 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_93 ),
        .I1(\threshold_pipes[2].low_carry_s1 [12]),
        .O(\threshold_pipes[2].q_s3_reg_i_7_n_0 ));
  CARRY4 \threshold_pipes[2].q_s3_reg_i_8 
       (.CI(\threshold_pipes[2].q_s3_reg_i_13_n_0 ),
        .CO({\threshold_pipes[2].q_s3_reg_i_8_n_0 ,\threshold_pipes[2].q_s3_reg_i_8_n_1 ,\threshold_pipes[2].q_s3_reg_i_8_n_2 ,\threshold_pipes[2].q_s3_reg_i_8_n_3 }),
        .CYINIT(1'b0),
        .DI({\threshold_pipes[2].cross_s1_reg_n_98 ,\threshold_pipes[2].cross_s1_reg_n_99 ,\threshold_pipes[2].cross_s1_reg_n_100 ,\threshold_pipes[2].cross_s1_reg_n_101 }),
        .O(\NLW_threshold_pipes[2].q_s3_reg_i_8_O_UNCONNECTED [3:0]),
        .S({\threshold_pipes[2].q_s3_reg_i_14_n_0 ,\threshold_pipes[2].q_s3_reg_i_15_n_0 ,\threshold_pipes[2].q_s3_reg_i_16_n_0 ,\threshold_pipes[2].q_s3_reg_i_17_n_0 }));
  LUT2 #(
    .INIT(4'h6)) 
    \threshold_pipes[2].q_s3_reg_i_9 
       (.I0(\threshold_pipes[2].cross_s1_reg_n_94 ),
        .I1(\threshold_pipes[2].low_carry_s1 [11]),
        .O(\threshold_pipes[2].q_s3_reg_i_9_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[0]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[0]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_105 ),
        .Q(\threshold_pipes[2].q_s5_reg[0]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[10]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[10]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_95 ),
        .Q(\threshold_pipes[2].q_s5_reg[10]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[11]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[11]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_94 ),
        .Q(\threshold_pipes[2].q_s5_reg[11]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[12]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[12]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_93 ),
        .Q(\threshold_pipes[2].q_s5_reg[12]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[13]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[13]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_92 ),
        .Q(\threshold_pipes[2].q_s5_reg[13]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[14]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[14]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_91 ),
        .Q(\threshold_pipes[2].q_s5_reg[14]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[15]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[15]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_90 ),
        .Q(\threshold_pipes[2].q_s5_reg[15]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[16]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[16]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_89 ),
        .Q(\threshold_pipes[2].q_s5_reg[16]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[17]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[17]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_88 ),
        .Q(\threshold_pipes[2].q_s5_reg[17]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[18]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[18]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_87 ),
        .Q(\threshold_pipes[2].q_s5_reg[18]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[19]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[19]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_86 ),
        .Q(\threshold_pipes[2].q_s5_reg[19]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[1]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[1]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_104 ),
        .Q(\threshold_pipes[2].q_s5_reg[1]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[20]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[20]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_85 ),
        .Q(\threshold_pipes[2].q_s5_reg[20]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[21]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[21]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_84 ),
        .Q(\threshold_pipes[2].q_s5_reg[21]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[22]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[22]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_83 ),
        .Q(\threshold_pipes[2].q_s5_reg[22]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[23]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[23]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_82 ),
        .Q(\threshold_pipes[2].q_s5_reg[23]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[24]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[24]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_81 ),
        .Q(\threshold_pipes[2].q_s5_reg[24]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[25]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[25]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_80 ),
        .Q(\threshold_pipes[2].q_s5_reg[25]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[26]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[26]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_79 ),
        .Q(\threshold_pipes[2].q_s5_reg[26]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[27]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[27]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_78 ),
        .Q(\threshold_pipes[2].q_s5_reg[27]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[2]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[2]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_103 ),
        .Q(\threshold_pipes[2].q_s5_reg[2]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[3]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[3]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_102 ),
        .Q(\threshold_pipes[2].q_s5_reg[3]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[4]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[4]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_101 ),
        .Q(\threshold_pipes[2].q_s5_reg[4]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[5]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[5]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_100 ),
        .Q(\threshold_pipes[2].q_s5_reg[5]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[6]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[6]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_99 ),
        .Q(\threshold_pipes[2].q_s5_reg[6]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[7]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[7]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_98 ),
        .Q(\threshold_pipes[2].q_s5_reg[7]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[8]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[8]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_97 ),
        .Q(\threshold_pipes[2].q_s5_reg[8]_srl2_n_0 ));
  (* srl_bus_name = "\\threshold_pipes[2].q_s5_reg " *) 
  (* srl_name = "\\threshold_pipes[2].q_s5_reg[9]_srl2 " *) 
  SRL16E \threshold_pipes[2].q_s5_reg[9]_srl2 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b0),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].q_s3_reg_n_96 ),
        .Q(\threshold_pipes[2].q_s5_reg[9]_srl2_n_0 ));
  FDRE \threshold_pipes[2].q_s6_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[0]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[10]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[11]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [11]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[12]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[13]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[14]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[15]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [15]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[16]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[17]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[18]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[19]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [19]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[1]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[20]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[21]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[22]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[23]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [23]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[24]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[25]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[26]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[27]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [27]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[2]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[3]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [3]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[4]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[5]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[6]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[7]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [7]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[8]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[2].q_s6_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].q_s5_reg[9]_srl2_n_0 ),
        .Q(\threshold_pipes[2].q_s6 [9]),
        .R(1'b0));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[11]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [11]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [11]),
        .O(\threshold_pipes[2].remainder_s6[11]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[11]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [10]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [10]),
        .O(\threshold_pipes[2].remainder_s6[11]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[11]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [9]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [9]),
        .O(\threshold_pipes[2].remainder_s6[11]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[11]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [8]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [8]),
        .O(\threshold_pipes[2].remainder_s6[11]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[15]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [15]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [15]),
        .O(\threshold_pipes[2].remainder_s6[15]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[15]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [14]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [14]),
        .O(\threshold_pipes[2].remainder_s6[15]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[15]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [13]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [13]),
        .O(\threshold_pipes[2].remainder_s6[15]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[15]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [12]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [12]),
        .O(\threshold_pipes[2].remainder_s6[15]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[19]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [19]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [19]),
        .O(\threshold_pipes[2].remainder_s6[19]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[19]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [18]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [18]),
        .O(\threshold_pipes[2].remainder_s6[19]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[19]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [17]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [17]),
        .O(\threshold_pipes[2].remainder_s6[19]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[19]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [16]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [16]),
        .O(\threshold_pipes[2].remainder_s6[19]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[23]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [23]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [23]),
        .O(\threshold_pipes[2].remainder_s6[23]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[23]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [22]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [22]),
        .O(\threshold_pipes[2].remainder_s6[23]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[23]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [21]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [21]),
        .O(\threshold_pipes[2].remainder_s6[23]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[23]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [20]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [20]),
        .O(\threshold_pipes[2].remainder_s6[23]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[27]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [27]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [27]),
        .O(\threshold_pipes[2].remainder_s6[27]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[27]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [26]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [26]),
        .O(\threshold_pipes[2].remainder_s6[27]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[27]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [25]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [25]),
        .O(\threshold_pipes[2].remainder_s6[27]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[27]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [24]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [24]),
        .O(\threshold_pipes[2].remainder_s6[27]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[31]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [31]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [31]),
        .O(\threshold_pipes[2].remainder_s6[31]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[31]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [30]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [30]),
        .O(\threshold_pipes[2].remainder_s6[31]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[31]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [29]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [29]),
        .O(\threshold_pipes[2].remainder_s6[31]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[31]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [28]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [28]),
        .O(\threshold_pipes[2].remainder_s6[31]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[3]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [3]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [3]),
        .O(\threshold_pipes[2].remainder_s6[3]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[3]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [2]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [2]),
        .O(\threshold_pipes[2].remainder_s6[3]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[3]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [1]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [1]),
        .O(\threshold_pipes[2].remainder_s6[3]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[3]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [0]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [0]),
        .O(\threshold_pipes[2].remainder_s6[3]_i_5_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[7]_i_2 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [7]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [7]),
        .O(\threshold_pipes[2].remainder_s6[7]_i_2_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[7]_i_3 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [6]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [6]),
        .O(\threshold_pipes[2].remainder_s6[7]_i_3_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[7]_i_4 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [5]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [5]),
        .O(\threshold_pipes[2].remainder_s6[7]_i_4_n_0 ));
  LUT2 #(
    .INIT(4'h9)) 
    \threshold_pipes[2].remainder_s6[7]_i_5 
       (.I0(\threshold_pipes[0].n_delay_reg[5] [4]),
        .I1(\threshold_pipes[2].product_s5_reg__0 [4]),
        .O(\threshold_pipes[2].remainder_s6[7]_i_5_n_0 ));
  FDRE \threshold_pipes[2].remainder_s6_reg[0] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [0]),
        .Q(\threshold_pipes[2].remainder_s6 [0]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[10] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [10]),
        .Q(\threshold_pipes[2].remainder_s6 [10]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[11] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [11]),
        .Q(\threshold_pipes[2].remainder_s6 [11]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[2].remainder_s6_reg[11]_i_1 
       (.CI(\threshold_pipes[2].remainder_s6_reg[7]_i_1_n_0 ),
        .CO({\threshold_pipes[2].remainder_s6_reg[11]_i_1_n_0 ,\threshold_pipes[2].remainder_s6_reg[11]_i_1_n_1 ,\threshold_pipes[2].remainder_s6_reg[11]_i_1_n_2 ,\threshold_pipes[2].remainder_s6_reg[11]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [11:8]),
        .O(\threshold_pipes[2].remainder_s600_out [11:8]),
        .S({\threshold_pipes[2].remainder_s6[11]_i_2_n_0 ,\threshold_pipes[2].remainder_s6[11]_i_3_n_0 ,\threshold_pipes[2].remainder_s6[11]_i_4_n_0 ,\threshold_pipes[2].remainder_s6[11]_i_5_n_0 }));
  FDRE \threshold_pipes[2].remainder_s6_reg[12] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [12]),
        .Q(\threshold_pipes[2].remainder_s6 [12]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[13] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [13]),
        .Q(\threshold_pipes[2].remainder_s6 [13]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[14] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [14]),
        .Q(\threshold_pipes[2].remainder_s6 [14]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[15] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [15]),
        .Q(\threshold_pipes[2].remainder_s6 [15]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[2].remainder_s6_reg[15]_i_1 
       (.CI(\threshold_pipes[2].remainder_s6_reg[11]_i_1_n_0 ),
        .CO({\threshold_pipes[2].remainder_s6_reg[15]_i_1_n_0 ,\threshold_pipes[2].remainder_s6_reg[15]_i_1_n_1 ,\threshold_pipes[2].remainder_s6_reg[15]_i_1_n_2 ,\threshold_pipes[2].remainder_s6_reg[15]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [15:12]),
        .O(\threshold_pipes[2].remainder_s600_out [15:12]),
        .S({\threshold_pipes[2].remainder_s6[15]_i_2_n_0 ,\threshold_pipes[2].remainder_s6[15]_i_3_n_0 ,\threshold_pipes[2].remainder_s6[15]_i_4_n_0 ,\threshold_pipes[2].remainder_s6[15]_i_5_n_0 }));
  FDRE \threshold_pipes[2].remainder_s6_reg[16] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [16]),
        .Q(\threshold_pipes[2].remainder_s6 [16]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[17] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [17]),
        .Q(\threshold_pipes[2].remainder_s6 [17]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[18] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [18]),
        .Q(\threshold_pipes[2].remainder_s6 [18]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[19] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [19]),
        .Q(\threshold_pipes[2].remainder_s6 [19]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[2].remainder_s6_reg[19]_i_1 
       (.CI(\threshold_pipes[2].remainder_s6_reg[15]_i_1_n_0 ),
        .CO({\threshold_pipes[2].remainder_s6_reg[19]_i_1_n_0 ,\threshold_pipes[2].remainder_s6_reg[19]_i_1_n_1 ,\threshold_pipes[2].remainder_s6_reg[19]_i_1_n_2 ,\threshold_pipes[2].remainder_s6_reg[19]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [19:16]),
        .O(\threshold_pipes[2].remainder_s600_out [19:16]),
        .S({\threshold_pipes[2].remainder_s6[19]_i_2_n_0 ,\threshold_pipes[2].remainder_s6[19]_i_3_n_0 ,\threshold_pipes[2].remainder_s6[19]_i_4_n_0 ,\threshold_pipes[2].remainder_s6[19]_i_5_n_0 }));
  FDRE \threshold_pipes[2].remainder_s6_reg[1] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [1]),
        .Q(\threshold_pipes[2].remainder_s6 [1]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[20] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [20]),
        .Q(\threshold_pipes[2].remainder_s6 [20]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[21] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [21]),
        .Q(\threshold_pipes[2].remainder_s6 [21]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[22] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [22]),
        .Q(\threshold_pipes[2].remainder_s6 [22]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[23] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [23]),
        .Q(\threshold_pipes[2].remainder_s6 [23]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[2].remainder_s6_reg[23]_i_1 
       (.CI(\threshold_pipes[2].remainder_s6_reg[19]_i_1_n_0 ),
        .CO({\threshold_pipes[2].remainder_s6_reg[23]_i_1_n_0 ,\threshold_pipes[2].remainder_s6_reg[23]_i_1_n_1 ,\threshold_pipes[2].remainder_s6_reg[23]_i_1_n_2 ,\threshold_pipes[2].remainder_s6_reg[23]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [23:20]),
        .O(\threshold_pipes[2].remainder_s600_out [23:20]),
        .S({\threshold_pipes[2].remainder_s6[23]_i_2_n_0 ,\threshold_pipes[2].remainder_s6[23]_i_3_n_0 ,\threshold_pipes[2].remainder_s6[23]_i_4_n_0 ,\threshold_pipes[2].remainder_s6[23]_i_5_n_0 }));
  FDRE \threshold_pipes[2].remainder_s6_reg[24] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [24]),
        .Q(\threshold_pipes[2].remainder_s6 [24]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[25] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [25]),
        .Q(\threshold_pipes[2].remainder_s6 [25]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[26] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [26]),
        .Q(\threshold_pipes[2].remainder_s6 [26]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[27] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [27]),
        .Q(\threshold_pipes[2].remainder_s6 [27]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[2].remainder_s6_reg[27]_i_1 
       (.CI(\threshold_pipes[2].remainder_s6_reg[23]_i_1_n_0 ),
        .CO({\threshold_pipes[2].remainder_s6_reg[27]_i_1_n_0 ,\threshold_pipes[2].remainder_s6_reg[27]_i_1_n_1 ,\threshold_pipes[2].remainder_s6_reg[27]_i_1_n_2 ,\threshold_pipes[2].remainder_s6_reg[27]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [27:24]),
        .O(\threshold_pipes[2].remainder_s600_out [27:24]),
        .S({\threshold_pipes[2].remainder_s6[27]_i_2_n_0 ,\threshold_pipes[2].remainder_s6[27]_i_3_n_0 ,\threshold_pipes[2].remainder_s6[27]_i_4_n_0 ,\threshold_pipes[2].remainder_s6[27]_i_5_n_0 }));
  FDRE \threshold_pipes[2].remainder_s6_reg[28] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [28]),
        .Q(\threshold_pipes[2].remainder_s6 [28]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[29] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [29]),
        .Q(\threshold_pipes[2].remainder_s6 [29]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [2]),
        .Q(\threshold_pipes[2].remainder_s6 [2]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[30] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [30]),
        .Q(\threshold_pipes[2].remainder_s6 [30]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[31] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [31]),
        .Q(\threshold_pipes[2].remainder_s6 [31]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[2].remainder_s6_reg[31]_i_1 
       (.CI(\threshold_pipes[2].remainder_s6_reg[27]_i_1_n_0 ),
        .CO({\NLW_threshold_pipes[2].remainder_s6_reg[31]_i_1_CO_UNCONNECTED [3],\threshold_pipes[2].remainder_s6_reg[31]_i_1_n_1 ,\threshold_pipes[2].remainder_s6_reg[31]_i_1_n_2 ,\threshold_pipes[2].remainder_s6_reg[31]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI({1'b0,\threshold_pipes[0].n_delay_reg[5] [30:28]}),
        .O(\threshold_pipes[2].remainder_s600_out [31:28]),
        .S({\threshold_pipes[2].remainder_s6[31]_i_2_n_0 ,\threshold_pipes[2].remainder_s6[31]_i_3_n_0 ,\threshold_pipes[2].remainder_s6[31]_i_4_n_0 ,\threshold_pipes[2].remainder_s6[31]_i_5_n_0 }));
  FDRE \threshold_pipes[2].remainder_s6_reg[3] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [3]),
        .Q(\threshold_pipes[2].remainder_s6 [3]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[2].remainder_s6_reg[3]_i_1 
       (.CI(1'b0),
        .CO({\threshold_pipes[2].remainder_s6_reg[3]_i_1_n_0 ,\threshold_pipes[2].remainder_s6_reg[3]_i_1_n_1 ,\threshold_pipes[2].remainder_s6_reg[3]_i_1_n_2 ,\threshold_pipes[2].remainder_s6_reg[3]_i_1_n_3 }),
        .CYINIT(1'b1),
        .DI(\threshold_pipes[0].n_delay_reg[5] [3:0]),
        .O(\threshold_pipes[2].remainder_s600_out [3:0]),
        .S({\threshold_pipes[2].remainder_s6[3]_i_2_n_0 ,\threshold_pipes[2].remainder_s6[3]_i_3_n_0 ,\threshold_pipes[2].remainder_s6[3]_i_4_n_0 ,\threshold_pipes[2].remainder_s6[3]_i_5_n_0 }));
  FDRE \threshold_pipes[2].remainder_s6_reg[4] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [4]),
        .Q(\threshold_pipes[2].remainder_s6 [4]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[5] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [5]),
        .Q(\threshold_pipes[2].remainder_s6 [5]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[6] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [6]),
        .Q(\threshold_pipes[2].remainder_s6 [6]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [7]),
        .Q(\threshold_pipes[2].remainder_s6 [7]),
        .R(1'b0));
  (* ADDER_THRESHOLD = "35" *) 
  CARRY4 \threshold_pipes[2].remainder_s6_reg[7]_i_1 
       (.CI(\threshold_pipes[2].remainder_s6_reg[3]_i_1_n_0 ),
        .CO({\threshold_pipes[2].remainder_s6_reg[7]_i_1_n_0 ,\threshold_pipes[2].remainder_s6_reg[7]_i_1_n_1 ,\threshold_pipes[2].remainder_s6_reg[7]_i_1_n_2 ,\threshold_pipes[2].remainder_s6_reg[7]_i_1_n_3 }),
        .CYINIT(1'b0),
        .DI(\threshold_pipes[0].n_delay_reg[5] [7:4]),
        .O(\threshold_pipes[2].remainder_s600_out [7:4]),
        .S({\threshold_pipes[2].remainder_s6[7]_i_2_n_0 ,\threshold_pipes[2].remainder_s6[7]_i_3_n_0 ,\threshold_pipes[2].remainder_s6[7]_i_4_n_0 ,\threshold_pipes[2].remainder_s6[7]_i_5_n_0 }));
  FDRE \threshold_pipes[2].remainder_s6_reg[8] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [8]),
        .Q(\threshold_pipes[2].remainder_s6 [8]),
        .R(1'b0));
  FDRE \threshold_pipes[2].remainder_s6_reg[9] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].remainder_s600_out [9]),
        .Q(\threshold_pipes[2].remainder_s6 [9]),
        .R(1'b0));
  LUT2 #(
    .INIT(4'hE)) 
    \threshold_pipes[2].threshold_live[2]_i_1 
       (.I0(\threshold_pipes[2].valid_pipe__0 ),
        .I1(live[2]),
        .O(\threshold_pipes[2].threshold_live[2]_i_1_n_0 ));
  FDRE \threshold_pipes[2].threshold_live_reg[2] 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].threshold_live[2]_i_1_n_0 ),
        .Q(live[2]),
        .R(reset));
  (* srl_bus_name = "\\threshold_pipes[2].valid_pipe_reg " *) 
  (* srl_name = "\\threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4 " *) 
  SRL16E \threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4 
       (.A0(1'b1),
        .A1(1'b0),
        .A2(1'b1),
        .A3(1'b0),
        .CE(1'b1),
        .CLK(clk),
        .D(\threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1_n_0 ),
        .Q(\threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ));
  (* SOFT_HLUTNM = "soft_lutpair1" *) 
  LUT3 #(
    .INIT(8'h20)) 
    \threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1 
       (.I0(take),
        .I1(selected[0]),
        .I2(selected[1]),
        .O(\threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_i_1_n_0 ));
  FDRE \threshold_pipes[2].valid_pipe_reg[6]_threshold_pipes_r_5 
       (.C(clk),
        .CE(1'b1),
        .D(\threshold_pipes[2].valid_pipe_reg[5]_srl6___threshold_pipes_r_4_n_0 ),
        .Q(\threshold_pipes[2].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ),
        .R(1'b0));
  FDRE \threshold_pipes[2].valid_pipe_reg[7] 
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_gate__1_n_0),
        .Q(\threshold_pipes[2].valid_pipe__0 ),
        .R(reset));
  (* SOFT_HLUTNM = "soft_lutpair2" *) 
  LUT2 #(
    .INIT(4'h8)) 
    threshold_pipes_gate
       (.I0(\threshold_pipes[0].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ),
        .I1(threshold_pipes_r_5_n_0),
        .O(threshold_pipes_gate_n_0));
  (* SOFT_HLUTNM = "soft_lutpair2" *) 
  LUT2 #(
    .INIT(4'h8)) 
    threshold_pipes_gate__0
       (.I0(\threshold_pipes[1].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ),
        .I1(threshold_pipes_r_5_n_0),
        .O(threshold_pipes_gate__0_n_0));
  LUT2 #(
    .INIT(4'h8)) 
    threshold_pipes_gate__1
       (.I0(\threshold_pipes[2].valid_pipe_reg[6]_threshold_pipes_r_5_n_0 ),
        .I1(threshold_pipes_r_5_n_0),
        .O(threshold_pipes_gate__1_n_0));
  FDRE threshold_pipes_r
       (.C(clk),
        .CE(1'b1),
        .D(1'b1),
        .Q(threshold_pipes_r_n_0),
        .R(reset));
  FDRE threshold_pipes_r_0
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_r_n_0),
        .Q(threshold_pipes_r_0_n_0),
        .R(reset));
  FDRE threshold_pipes_r_1
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_r_0_n_0),
        .Q(threshold_pipes_r_1_n_0),
        .R(reset));
  FDRE threshold_pipes_r_2
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_r_1_n_0),
        .Q(threshold_pipes_r_2_n_0),
        .R(reset));
  FDRE threshold_pipes_r_3
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_r_2_n_0),
        .Q(threshold_pipes_r_3_n_0),
        .R(reset));
  FDRE threshold_pipes_r_4
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_r_3_n_0),
        .Q(threshold_pipes_r_4_n_0),
        .R(reset));
  FDRE threshold_pipes_r_5
       (.C(clk),
        .CE(1'b1),
        .D(threshold_pipes_r_4_n_0),
        .Q(threshold_pipes_r_5_n_0),
        .R(reset));
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
