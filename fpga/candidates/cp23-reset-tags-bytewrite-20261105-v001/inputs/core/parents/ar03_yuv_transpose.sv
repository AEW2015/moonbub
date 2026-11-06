`timescale 1ns/1ps
// BANKS1 is the exact sealed single-bank leaf, renamed only. BANKS2 is additive.
module ar03_yuv_transpose #(
 parameter integer BANKS=2,
 parameter[23:0]APERTURE_BASE=24'h100000,parameter integer APERTURE_WORDS=262144
)(
 input wire clk,reset,
 input wire start_valid,output wire start_ready,start_rejected,
 input wire[63:0]start_owner,input wire[31:0]start_epoch,start_frame,
 input wire[15:0]start_width,start_height,input wire[23:0]start_base,
 input wire in_valid,output wire in_ready,input wire[23:0]in_address,input wire[15:0]in_data,
 input wire[63:0]in_owner,input wire[31:0]in_epoch,in_frame,
 input wire upstream_flush,upstream_discard,abort,fault,
 output wire pixel_valid,input wire pixel_ready,output wire[23:0]pixel_address,output wire[15:0]pixel_data,
 output wire force_flush,discard,input wire memory_idle,
 output wire store_idle,done,failed,aborted,
 input wire release_valid,input wire[63:0]release_owner,input wire[31:0]release_epoch,release_frame,
 output wire release_rejected,
 output wire[63:0]owner,output wire[31:0]input_words,processed_bytes,output_words,stripe_high_water,
 output wire[3:0]error_code,state,
 output wire[1:0]owned_banks,full_banks,output wire[31:0]reserved_bytes
);
 initial if(BANKS!=1&&BANKS!=2)$fatal(1,"BANKS must be1or2");
 generate if(BANKS==1)begin:g_single
  ar03_yuv_transpose_single #(.APERTURE_BASE(APERTURE_BASE),.APERTURE_WORDS(APERTURE_WORDS))core(.*);
  assign owned_banks={1'b0,core.stripe_bytes!=0};assign full_banks={1'b0,core.state==2};assign reserved_bytes=core.stripe_bytes;
 end else begin:g_double
  ar03_yuv_transpose_double #(.APERTURE_BASE(APERTURE_BASE),.APERTURE_WORDS(APERTURE_WORDS))core(.*);
 end endgenerate
endmodule
