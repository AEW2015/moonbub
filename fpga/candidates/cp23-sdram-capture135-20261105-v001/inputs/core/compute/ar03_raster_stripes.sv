`timescale 1ns/1ps
// Private block-major to canonical plane/raster adapter. No publication.
module ar03_raster_stripes #(
 parameter MAX_WIDTH=720, MAX_HEIGHT=480, MAX_PIXELS=345600
)(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,
 input wire [63:0] start_owner,input wire [31:0] start_epoch,start_frame,
 input wire [15:0] start_width,start_height,
 input wire in_valid,output wire in_ready,input wire [7:0] in_sample,
 input wire [63:0] in_owner,input wire [31:0] in_epoch,in_frame,in_block,
 input wire [1:0] in_plane,input wire [15:0] in_x,in_y,input wire in_last,
 output wire out_valid,input wire out_ready,output reg [7:0] out_sample,
 output wire [63:0] out_owner,output wire [31:0] out_epoch,out_frame,
 output reg [1:0] out_plane,output reg [15:0] out_x,out_y,output reg out_last,
 output wire done_valid,input wire done_ready,
 output wire error_valid,input wire error_ready,output reg [2:0] error_code
);
 localparam IDLE=0,RUN=1,DONE=2,ERROR=3;
 reg [1:0] state;
 reg [63:0] owner;reg [31:0] epoch,frame;
 // Only validated geometry is stored. Widen carry-bearing sums explicitly.
 reg [9:0] width,pw,bx;reg [8:0] height,ph,sy;reg [2:0] lx,ly;
 reg [31:0] block_index;
 reg [1:0] plane;
 reg wb,rb;reg [1:0] full;
 reg [9:0] bank_width[0:1];reg [3:0] bank_rows[0:1];reg [8:0] bank_y[0:1];
 reg [1:0] bank_plane[0:1];
 reg bank_final[0:1];
 reg [9:0] rx;reg [2:0] ry;
 reg input_done,ov;
 // Two separate single-write/synchronous-read byte memories; no clear.
 (* ram_style="block" *) reg [7:0] ram0[0:MAX_WIDTH*8-1];
 (* ram_style="block" *) reg [7:0] ram1[0:MAX_WIDTH*8-1];
 reg [7:0] ram0_q,ram1_q;reg read_bank;
 // Current tile extents are invariant until its accepted final sample.
 reg [3:0] cols,rows;
 function automatic [3:0] limit_columns(input [10:0] value);
 begin limit_columns=(|value[10:3]) ? 4'd8 : {1'b0,value[2:0]};end
 endfunction
 function automatic [3:0] limit_rows(input [9:0] value);
 begin limit_rows=(|value[9:3]) ? 4'd8 : {1'b0,value[2:0]};end
 endfunction
 wire [10:0] next_block_x={1'b0,bx}+{7'd0,cols};
 wire [9:0] next_stripe_y={1'b0,sy}+{6'd0,rows};
 wire [10:0] next_columns_remaining={1'b0,pw}-next_block_x;
 wire [9:0] next_rows_remaining={1'b0,ph}-next_stripe_y;
 wire [10:0] absolute_in_x={1'b0,bx}+{8'd0,lx};
 wire [9:0] absolute_in_y={1'b0,sy}+{7'd0,ly};
 wire [9:0] read_absolute_y={1'b0,bank_y[rb]}+{7'd0,ry};
 wire end_block=lx==cols-4'd1 && ly==rows-4'd1;
 wire end_stripe=end_block && next_block_x=={1'b0,pw};
 wire plane_end=next_stripe_y=={1'b0,ph};
 wire final_input=end_stripe && plane_end && plane==2;
 wire correct_identity=in_owner==owner && in_epoch==epoch && in_frame==frame;
 wire correct_order=in_plane==plane && in_block==block_index &&
  in_x=={5'd0,absolute_in_x} && in_y=={6'd0,absolute_in_y};
 wire correct_last=in_last==final_input;
 wire accept=in_valid && in_ready;
 wire read_enable=state==RUN && full[rb] && (!ov || out_ready) && !reset && !abort;
 wire last_read=rx==bank_width[rb]-10'd1 && ry==bank_rows[rb]-4'd1;
 // Admission bounds prove actual byte addresses0..5759 and next row<=5760.
 // Invalid admission initializes these to zero and never enables RAM access.
 reg [12:0] write_address_q,read_address_q,next_row_base;
 wire [31:0] write_address={19'd0,write_address_q};
 wire [31:0] read_address={19'd0,read_address_q};
 wire valid_admission=start_width>=2 && start_height>=2 && !start_width[0] && !start_height[0] &&
  start_width<=MAX_WIDTH && start_height<=MAX_HEIGHT && start_width<=720 && start_height<=480 &&
  ({16'd0,start_width}*{16'd0,start_height})<=MAX_PIXELS;
 assign start_ready=state==IDLE && !reset && !abort;
 assign in_ready=state==RUN && !input_done && !full[wb] && !reset && !abort;
 assign out_valid=state==RUN && ov && !reset && !abort;
 assign out_owner=owner;assign out_epoch=epoch;assign out_frame=frame;
 assign done_valid=state==DONE && !reset && !abort;
 assign error_valid=state==ERROR && !reset && !abort;
 // No reset on data registers: reset/abort only invalidates their ownership.
 // Keep each RAM output register on its own synchronous read port.
 // A held output owns its bank_q even after the bank memory is released.
 always @(posedge clk)begin
  if(accept && correct_identity && correct_order && correct_last && !wb)ram0[write_address]<=in_sample;
  if(read_enable && !rb)ram0_q<=ram0[read_address];
 end
 always @(posedge clk)begin
  if(accept && correct_identity && correct_order && correct_last && wb)ram1[write_address]<=in_sample;
  if(read_enable && rb)ram1_q<=ram1[read_address];
 end
 always @(posedge clk)if(read_enable)read_bank<=rb;
 always @* out_sample=read_bank?ram1_q:ram0_q;
 always @(posedge clk)begin
  if(reset || abort)begin
   state<=IDLE;owner<=0;epoch<=0;frame<=0;full<=0;wb<=0;rb<=0;ov<=0;input_done<=0;
   width<=0;height<=0;pw<=0;ph<=0;bx<=0;sy<=0;lx<=0;ly<=0;plane<=0;block_index<=0;
   rx<=0;ry<=0;out_plane<=0;out_x<=0;out_y<=0;out_last<=0;error_code<=0;
   write_address_q<=0;read_address_q<=0;next_row_base<=0;cols<=0;rows<=0;
  end else case(state)
   IDLE:if(start_valid)begin
    owner<=start_owner;epoch<=start_epoch;frame<=start_frame;
    write_address_q<=0;read_address_q<=0;
    next_row_base<=valid_admission?{3'd0,start_width[9:0]}:13'd0;
    cols<=valid_admission ? limit_columns({1'b0,start_width[9:0]}) : 4'd0;
    rows<=valid_admission ? limit_rows({1'b0,start_height[8:0]}) : 4'd0;
    width<=valid_admission?start_width[9:0]:10'd0;height<=valid_admission?start_height[8:0]:9'd0;
    pw<=valid_admission?start_width[9:0]:10'd0;ph<=valid_admission?start_height[8:0]:9'd0;
    full<=0;wb<=0;rb<=0;ov<=0;input_done<=0;bx<=0;sy<=0;lx<=0;ly<=0;plane<=0;block_index<=0;rx<=0;ry<=0;
    if(!valid_admission)begin state<=ERROR;error_code<=1;end
    else state<=RUN;
   end
   RUN:begin
    if(ov && out_ready)ov<=0;
    if(read_enable)begin
     read_address_q<=last_read?13'd0:read_address_q+1'b1;
     ov<=1;out_plane<=bank_plane[rb];out_x<={6'd0,rx};out_y<={6'd0,read_absolute_y};
     out_last<=last_read && bank_final[rb];
     if(last_read)begin full[rb]<=0;rb<=!rb;rx<=0;ry<=0;end
     else if(rx==bank_width[rb]-10'd1)begin rx<=0;ry<=ry+1'b1;end
     else rx<=rx+1'b1;
    end
    if(accept)begin
     if(!correct_identity || !correct_order || !correct_last)begin
      state<=ERROR;error_code<=!correct_identity?2:!correct_order?3:4;
      full<=0;ov<=0;input_done<=1;
     end else begin
      if(end_block)begin
       // Remaining sums are <= their validated plane bounds. The branches
       // below consume them only when nonzero, or select the next plane.
       if(end_stripe)begin
        if(plane_end)begin
         cols<=limit_columns({2'b0,width[9:1]});
         rows<=limit_rows({2'b0,height[8:1]});
        end else begin
         cols<=limit_columns({1'b0,pw});rows<=limit_rows(next_rows_remaining);
        end
       end else cols<=limit_columns(next_columns_remaining);
       write_address_q<=end_stripe?13'd0:{2'd0,next_block_x};
       next_row_base<=(end_stripe && plane_end)?{4'd0,width[9:1]}:{3'd0,pw};
      end else if(lx==cols-4'd1)begin
       write_address_q<=next_row_base+{3'd0,bx[9:0]};
       next_row_base<=next_row_base+{3'd0,pw[9:0]};
      end else write_address_q<=write_address_q+1'b1;
      if(lx==cols-4'd1)begin
       lx<=0;
       if(ly==rows-4'd1)begin
        ly<=0;block_index<=block_index+1'b1;
        if(end_stripe)begin
         full[wb]<=1;bank_width[wb]<=pw;bank_rows[wb]<=rows;
         bank_y[wb]<=sy;bank_plane[wb]<=plane;bank_final[wb]<=final_input;wb<=!wb;bx<=0;
         if(plane_end)begin
          sy<=0;plane<=plane+1'b1;pw<=width>>1;ph<=height>>1;block_index<=0;
          if(final_input)input_done<=1;
         end else sy<=next_stripe_y[8:0];
        end else bx<=next_block_x[9:0];
       end else ly<=ly+1'b1;
      end else lx<=lx+1'b1;
     end
    end
    if(input_done && full==0 && !ov)state<=DONE;
   end
   DONE:if(done_ready)begin state<=IDLE;owner<=0;epoch<=0;frame<=0;end
   ERROR:if(error_ready)begin state<=IDLE;owner<=0;epoch<=0;frame<=0;end
   default:state<=IDLE;
  endcase
 end
endmodule
