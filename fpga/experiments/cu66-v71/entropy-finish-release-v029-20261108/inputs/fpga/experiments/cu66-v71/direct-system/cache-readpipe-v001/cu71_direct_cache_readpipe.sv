// Two cache contexts. Each holds two8-column Y groups, two8-column chroma
// groups per plane and the complete row-major HUD. The owner supplies page
// validity/generation; this block enforces bounds and active-reader hazards.
`timescale 1ns/1ps
`default_nettype none
module cu71_direct_cache_readpipe(
 input wire clk,rst,
 input wire wr_valid,wr_allow,wr_context,wr_bank,input wire[1:0]wr_kind,
 input wire[8:0]wr_row,input wire[63:0]wr_data,input wire[14:0]wr_hud_index,
 input wire[15:0]wr_hud_word,output reg wr_error,
 input wire front_valid,front_context,render_live,render_context,
 input wire[9:0]render_u,
 input wire rd_valid,rd_context,input wire[9:0]rd_u,input wire[8:0]rd_v,
 input wire rd_hud_hit,input wire[14:0]rd_hud_index,input wire[31:0]rd_tag,
 output reg out_valid,out_error,output reg[31:0]out_tag,
 output wire[7:0]out_y,out_cb_t0,out_cb_t1,out_cb_b0,out_cb_b1,
 output wire[7:0]out_cr_t0,out_cr_t1,out_cr_b0,out_cr_b1,
 output wire out_x_odd,out_y_odd,output wire[15:0]out_hud_word,
 output reg out_hud_hit,output wire read_busy
);
 // Caller owns the selected front read banks/HUD from acceptance through
 // the RAM read/result. Uncoordinated read/write races are not equivalent.
 reg rd_valid_stage,rd_context_stage,rd_hud_hit_stage;
 reg[9:0]rd_u_stage;reg[8:0]rd_v_stage;reg[14:0]rd_hud_index_stage;
 reg[31:0]rd_tag_stage;
 always @(posedge clk)begin
  if(rst)rd_valid_stage<=0;else rd_valid_stage<=rd_valid;
  // Private request payload is validity-fenced and does not need reset.
  rd_context_stage<=rd_context;rd_u_stage<=rd_u;rd_v_stage<=rd_v;
  rd_hud_hit_stage<=rd_hud_hit;rd_hud_index_stage<=rd_hud_index;rd_tag_stage<=rd_tag;
 end
 assign read_busy=rd_valid_stage||out_valid;

 // Power-of-two context strides avoid a wide multiply/add on the read port.
 // Chroma replicas provide independent cy/cy+1 reads while DMA writes.
 (* ram_style="block" *) reg[127:0]y_mem[0:1023];
 (* ram_style="block" *) reg[127:0]cb_top_mem[0:511],cb_bottom_mem[0:511];
 (* ram_style="block" *) reg[127:0]cr_top_mem[0:511],cr_bottom_mem[0:511];
 (* ram_style="block" *) reg[15:0]hud_mem[0:42239];
 reg[127:0]y_q,cb_top_q,cb_bottom_q,cr_top_q,cr_bottom_q;
 reg[15:0]hud_q;
 reg[9:0]u_q;reg y_odd_q;
 wire[7:0]cy=rd_v_stage[8:1];
 wire[7:0]cy1=cy==239?8'd239:cy+1'b1;
 wire read_bad=rd_u_stage>=720||rd_v_stage>=480||(rd_hud_hit_stage&&rd_hud_index_stage>=21120);
 wire[9:0]ya={rd_context_stage,(rd_v_stage<480?rd_v_stage:9'd0)};
 wire[8:0]ca0={rd_context_stage,(cy<240?cy:8'd0)},ca1={rd_context_stage,(cy1<240?cy1:8'd0)};
 wire[15:0]ha=(rd_context_stage?16'd21120:16'd0)+(rd_hud_index_stage<21120?{1'b0,rd_hud_index_stage}:16'd0);
 wire[9:0]yw={wr_context,wr_row};
 wire[8:0]cw={wr_context,wr_row[7:0]};
 wire[15:0]hw=(wr_context?16'd21120:16'd0)+{1'b0,wr_hud_index};
 wire chroma_next=render_u[0]&&render_u[3:1]==7&&render_u!=719;
 wire y_hazard=render_live&&wr_context==render_context&&wr_bank==render_u[3];
 wire c_hazard=render_live&&wr_context==render_context&&(wr_bank==render_u[4]||chroma_next);
 wire h_hazard=front_valid&&wr_context==front_context;
 wire bad_write=!wr_allow||
  (wr_kind==0&&(wr_row>=480||y_hazard))||
  ((wr_kind==1||wr_kind==2)&&(wr_row>=240||c_hazard))||
  (wr_kind==3&&(wr_hud_index>=21120||h_hazard));
 wire do_write=wr_valid&&!rst&&!bad_write;
 // All data arrays use synchronous unreset write/read ports. A64-bit half
 // enable selects the group; page metadata stays in the transaction owner.
 always @(posedge clk)begin
  if(do_write&&wr_kind==0)begin
   if(wr_bank)y_mem[yw][127:64]<=wr_data;else y_mem[yw][63:0]<=wr_data;
  end
  y_q<=y_mem[ya];
  if(do_write&&wr_kind==1)begin
   if(wr_bank)begin cb_top_mem[cw][127:64]<=wr_data;cb_bottom_mem[cw][127:64]<=wr_data;end
   else begin cb_top_mem[cw][63:0]<=wr_data;cb_bottom_mem[cw][63:0]<=wr_data;end
  end
  cb_top_q<=cb_top_mem[ca0];cb_bottom_q<=cb_bottom_mem[ca1];
  if(do_write&&wr_kind==2)begin
   if(wr_bank)begin cr_top_mem[cw][127:64]<=wr_data;cr_bottom_mem[cw][127:64]<=wr_data;end
   else begin cr_top_mem[cw][63:0]<=wr_data;cr_bottom_mem[cw][63:0]<=wr_data;end
  end
  cr_top_q<=cr_top_mem[ca0];cr_bottom_q<=cr_bottom_mem[ca1];
  if(do_write&&wr_kind==3)hud_mem[hw]<=wr_hud_word;
  hud_q<=hud_mem[ha];
  if(rst)begin out_valid<=0;out_error<=0;wr_error<=0;out_hud_hit<=0;end
  else begin out_valid<=rd_valid_stage;out_error<=rd_valid_stage&&read_bad;wr_error<=wr_valid&&bad_write;out_hud_hit<=rd_hud_hit_stage;end
  u_q<=rd_u_stage;y_odd_q<=rd_v_stage[0];out_tag<=rd_tag_stage;
 end
 wire[2:0]cx=u_q[3:1];
 wire[2:0]cx1=cx==7?(u_q==719?3'd7:3'd0):cx+1'b1;
 wire next_bank=(cx==7&&u_q!=719)?!u_q[4]:u_q[4];
 wire[6:0]yi={u_q[3],u_q[2:0],3'b000};
 wire[6:0]ci0={u_q[4],cx,3'b000},ci1={next_bank,cx1,3'b000};
 assign out_y=y_q[yi+:8];
 assign out_cb_t0=cb_top_q[ci0+:8];assign out_cb_t1=cb_top_q[ci1+:8];
 assign out_cb_b0=cb_bottom_q[ci0+:8];assign out_cb_b1=cb_bottom_q[ci1+:8];
 assign out_cr_t0=cr_top_q[ci0+:8];assign out_cr_t1=cr_top_q[ci1+:8];
 assign out_cr_b0=cr_bottom_q[ci0+:8];assign out_cr_b1=cr_bottom_q[ci1+:8];
 assign out_x_odd=u_q[0];assign out_y_odd=y_odd_q;
 assign out_hud_word=out_hud_hit?hud_q:16'd0;
endmodule
`default_nettype wire
