//-----------------------------------------------------------------
//                      Baseline JPEG Decoder
//                             V0.1
//                       Ultra-Embedded.com
//                        Copyright 2020
//
//                   admin@ultra-embedded.com
//-----------------------------------------------------------------
//                      License: Apache 2.0
// This IP can be freely used in commercial projects, however you may
// want access to unreleased materials such as verification environments,
// or test vectors, as well as changes to the IP for integration purposes.
// If this is the case, contact the above address.
// I am interested to hear how and where this IP is used, so please get
// in touch!
//-----------------------------------------------------------------
// Copyright 2020 Ultra-Embedded.com
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//-----------------------------------------------------------------

module jpeg_output
(
    // Inputs
     input           clk_i
    ,input           rst_i
    ,input           img_start_i
    ,input           img_end_i
    ,input  [ 15:0]  img_width_i
    ,input  [ 15:0]  img_height_i
    ,input  [  1:0]  img_mode_i
    ,input           inport_valid_i
    ,input  [ 31:0]  inport_data_i
    ,input  [  5:0]  inport_idx_i
    ,input  [ 31:0]  inport_id_i
    ,input           outport_accept_i

    // Outputs
    ,output          inport_accept_o
    ,output          outport_valid_o
    ,output [ 15:0]  outport_width_o
    ,output [ 15:0]  outport_height_o
    ,output [ 15:0]  outport_pixel_x_o
    ,output [ 15:0]  outport_pixel_y_o
    ,output [  7:0]  outport_pixel_r_o
    ,output [  7:0]  outport_pixel_g_o
    ,output [  7:0]  outport_pixel_b_o
    ,output          idle_o
);



localparam BLOCK_Y          = 2'd0;
localparam BLOCK_CB         = 2'd1;
localparam BLOCK_CR         = 2'd2;
localparam BLOCK_EOF        = 2'd3;

localparam JPEG_MONOCHROME  = 2'd0;
localparam JPEG_YCBCR_444   = 2'd1;
localparam JPEG_YCBCR_420   = 2'd2;
localparam JPEG_UNSUPPORTED = 2'd3;

reg valid_r;
// Moonshine local integration patch: elastic color pipeline. Original
// RAM->constant multiply->three adds->clamp path failed100MHz timing.
wire output_space_w;

//-----------------------------------------------------------------
// FIFO: Y
//-----------------------------------------------------------------
wire               y_valid_w;
wire signed [31:0] y_value_w;
wire               y_pop_w;
wire [31:0]        y_level_w;

jpeg_output_y_ram
u_ram_y
(
     .clk_i(clk_i)
    ,.rst_i(rst_i)

    ,.flush_i(img_start_i)
    ,.level_o(y_level_w)

    ,.push_i(inport_valid_i && (inport_id_i[31:30] == BLOCK_Y || inport_id_i[31:30] == BLOCK_EOF))
    ,.wr_idx_i(inport_idx_i)
    ,.data_in_i(inport_data_i)

    ,.valid_o(y_valid_w)
    ,.data_out_o(y_value_w)
    ,.pop_i(y_pop_w)
);

//-----------------------------------------------------------------
// FIFO: Cb
//-----------------------------------------------------------------
wire               cb_valid_w;
wire signed [31:0] cb_value_w;
wire               cb_pop_w;
wire [31:0]        cb_level_w;

jpeg_output_cx_ram
u_ram_cb
(
     .clk_i(clk_i)
    ,.rst_i(rst_i)

    ,.flush_i(img_start_i)
    ,.level_o(cb_level_w)
    ,.mode420_i(img_mode_i == JPEG_YCBCR_420)

    ,.push_i(inport_valid_i && (inport_id_i[31:30] == BLOCK_CB || inport_id_i[31:30] == BLOCK_EOF))
    ,.wr_idx_i(inport_idx_i)
    ,.data_in_i(inport_data_i)

    ,.valid_o(cb_valid_w)
    ,.data_out_o(cb_value_w)
    ,.pop_i(cb_pop_w)
);

//-----------------------------------------------------------------
// FIFO: Cr
//-----------------------------------------------------------------
wire               cr_valid_w;
wire signed [31:0] cr_value_w;
wire               cr_pop_w;
wire [31:0]        cr_level_w;

jpeg_output_cx_ram
u_ram_cr
(
     .clk_i(clk_i)
    ,.rst_i(rst_i)

    ,.flush_i(img_start_i)
    ,.level_o(cr_level_w)
    ,.mode420_i(img_mode_i == JPEG_YCBCR_420)

    ,.push_i(inport_valid_i && (inport_id_i[31:30] == BLOCK_CR || inport_id_i[31:30] == BLOCK_EOF))
    ,.wr_idx_i(inport_idx_i)
    ,.data_in_i(inport_data_i)

    ,.valid_o(cr_valid_w)
    ,.data_out_o(cr_value_w)
    ,.pop_i(cr_pop_w)
);

//-----------------------------------------------------------------
// FIFO: Info
//-----------------------------------------------------------------
wire        id_valid_w;
wire [31:0] id_value_w;
wire        id_pop_w;

jpeg_output_fifo
#(
     .WIDTH(32)
    ,.DEPTH(8)
    ,.ADDR_W(3)
)
u_info
(
     .clk_i(clk_i)
    ,.rst_i(rst_i)
    ,.flush_i(img_start_i)
 
    ,.push_i(inport_valid_i && (inport_id_i[31:30] == BLOCK_Y || inport_id_i[31:30] == BLOCK_EOF) && inport_idx_i == 6'd0)
    ,.data_in_i(inport_id_i)
    ,.accept_o()

    ,.valid_o(id_valid_w)
    ,.data_out_o(id_value_w)
    ,.pop_i(id_pop_w)
);

assign inport_accept_o   = (y_level_w <= 32'd384 && cr_level_w <= 32'd128) | idle_o;

//-----------------------------------------------------------------
// Block counter (0 - 63)
//-----------------------------------------------------------------
reg [5:0] idx_q;

always @ (posedge clk_i )
if (rst_i)
    idx_q <= 6'b0;
else if (img_start_i)
    idx_q <= 6'b0;
else if (valid_r && output_space_w)
    idx_q <= idx_q + 6'd1;

//-----------------------------------------------------------------
// Subsampling counter (420 chroma subsampling)
//-----------------------------------------------------------------
reg [1:0] subsmpl_q;

always @ (posedge clk_i )
if (rst_i)
    subsmpl_q <= 2'b0;
else if (img_start_i)
    subsmpl_q <= 2'b0;
else if (valid_r && output_space_w && img_mode_i == JPEG_YCBCR_420 && idx_q == 6'd63)
    subsmpl_q <= subsmpl_q + 2'd1;

//-----------------------------------------------------------------
// YUV -> RGB
//-----------------------------------------------------------------
reg active_q;

always @ (posedge clk_i )
if (rst_i)
    active_q <= 1'b0;
else if (img_start_i)
    active_q <= 1'b0;
else if (!active_q)
begin
    if (img_mode_i == JPEG_MONOCHROME)
        active_q <= (y_level_w >= 32'd64);
    else if (img_mode_i == JPEG_YCBCR_444)
        active_q <= (y_level_w >= 32'd64) && (cb_level_w >= 32'd64) && (cr_level_w >= 32'd64);
    else if (subsmpl_q != 2'b0) // 420
        active_q <= 1'b1;
    else // 420
        active_q <= (y_level_w >= 32'd256) && (cb_level_w >= 32'd256) && (cr_level_w >= 32'd256);
end
else if (valid_r && output_space_w && idx_q == 6'd63)
    active_q <= 1'b0;

always @ * valid_r = active_q;

assign y_pop_w  = output_space_w && active_q;
assign cb_pop_w = output_space_w && active_q;
assign cr_pop_w = output_space_w && active_q;
assign id_pop_w = output_space_w && (idx_q == 6'd63);

//-----------------------------------------------------------------
// Outputs
//-----------------------------------------------------------------
wire [31:0] x_start_w = {13'b0, id_value_w[15:0],3'b0};
wire [31:0] y_start_w = {15'b0, id_value_w[29:16],3'b0};
reg [4:0] pipe_valid;
wire can4 = !pipe_valid[4] || outport_accept_i;
wire can3 = !pipe_valid[3] || can4;
wire can2 = !pipe_valid[2] || can3;
wire can1 = !pipe_valid[1] || can2;
wire can0 = !pipe_valid[0] || can1;
assign output_space_w = can0;
reg [15:0] x0,y0,x1,y1,x2,y2,x3,y3,x4,y4;
reg signed [31:0] sy0,scb0,scr0;
reg mono0;
reg signed [31:0] ybias1,cr5743_1,cr2925_1,cb1410_1,cb7258_1;
reg signed [31:0] r2,g2,b2,crgreen2;
reg signed [31:0] r3,g3,b3;
reg [7:0] r4,g4,b4;
function [7:0] original_clip;
 input signed [31:0] value;
 begin original_clip=(|value[31:8]) ? (value[31:24]^8'hff):value[7:0];end
endfunction
always @(posedge clk_i)begin
 if(rst_i || img_start_i)pipe_valid<=0;
 else begin
  if(can4)begin
   pipe_valid[4]<=pipe_valid[3];
   if(pipe_valid[3])begin x4<=x3;y4<=y3;r4<=original_clip(r3);g4<=original_clip(g3);b4<=original_clip(b3);end
  end
  if(can3)begin
   pipe_valid[3]<=pipe_valid[2];
   if(pipe_valid[2])begin x3<=x2;y3<=y2;r3<=r2;g3<=g2-crgreen2;b3<=b2;end
  end
  if(can2)begin
   pipe_valid[2]<=pipe_valid[1];
   if(pipe_valid[1])begin
    x2<=x1;y2<=y1;r2<=ybias1+(cr5743_1>>>12);
    g2<=ybias1-(cb1410_1>>>12);crgreen2<=cr2925_1>>>12;
    b2<=ybias1+(cb7258_1>>>12);
   end
  end
  if(can1)begin
   pipe_valid[1]<=pipe_valid[0];
   if(pipe_valid[0])begin
    x1<=x0;y1<=y0;ybias1<=32'sd128+sy0;
    //32-bit products and arithmetic shifts exactly preserve the original
    // expression widths/rounding. Only register placement changes.
    cr5743_1<=mono0 ? 32'sd0:scr0*32'sd5743;
    cr2925_1<=mono0 ? 32'sd0:scr0*32'sd2925;
    cb1410_1<=mono0 ? 32'sd0:scb0*32'sd1410;
    cb7258_1<=mono0 ? 32'sd0:scb0*32'sd7258;
   end
  end
  if(can0)begin
   pipe_valid[0]<=valid_r && id_value_w[31:30]!=BLOCK_EOF;
   if(valid_r)begin
    x0<=x_start_w+(idx_q%8);y0<=y_start_w+(idx_q/8);
    sy0<=y_value_w;scb0<=cb_value_w;scr0<=cr_value_w;mono0<=img_mode_i==JPEG_MONOCHROME;
   end
  end
 end
end
assign outport_valid_o   = pipe_valid[4];
assign outport_pixel_x_o = x4;
assign outport_pixel_y_o = y4;
assign outport_width_o   = img_width_i;
assign outport_height_o  = img_height_i;
assign outport_pixel_r_o = r4;
assign outport_pixel_g_o = g4;
assign outport_pixel_b_o = b4;

//-----------------------------------------------------------------
// Idle
//-----------------------------------------------------------------
reg idle_q;

always @ (posedge clk_i )
if (rst_i)
    idle_q <= 1'b1;
else if (img_start_i)
    idle_q <= 1'b0;
else if (id_valid_w && id_value_w[31:30] == BLOCK_EOF)
    idle_q <= 1'b1;

assign idle_o = idle_q;


endmodule
