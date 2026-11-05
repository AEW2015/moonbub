`timescale 1ns/1ps
// Read-only final-RGB stream observer. No ready/backpressure or pixel mutation.
module cpl_canvas_crc #(parameter integer WIDTH=720,HEIGHT=480)(
 input wire clk,reset,word_valid,input wire[15:0]word_data,input wire[9:0]word_x,word_y,
 output reg[31:0]canvas_sequence,last_crc,last_word_count,current_word_count,sequence_errors,
 output wire[31:0]flags
);
 localparam integer WORDS=WIDTH*HEIGHT;
 reg active,current_gap,ever_gap,exhausted,last_valid;
 reg[9:0]expected_x,expected_y;reg[31:0]running_crc;
 assign flags={27'd0,exhausted,ever_gap,current_gap,active,last_valid};
 initial if(WIDTH<1||WIDTH>1024||HEIGHT<2||HEIGHT>1024)$fatal(1,"unsupported observer geometry");
 function automatic[31:0]step16(input[31:0]crc,input[15:0]data);
  reg[31:0]v;integer i;
  begin v=crc^{16'd0,data};for(i=0;i<16;i=i+1)v=v[0]?(v>>1)^32'hedb88320:v>>1;step16=v;end
 endfunction
 task mark_gap;
  begin
   current_gap<=1;ever_gap<=1;last_valid<=0;
   if(sequence_errors>=32'hfffffffe)begin sequence_errors<=32'hffffffff;exhausted<=1;end
   else sequence_errors<=sequence_errors+1'b1;
  end
 endtask
 always @(posedge clk)begin
  if(reset)begin
   canvas_sequence<=0;last_crc<=0;last_word_count<=0;current_word_count<=0;sequence_errors<=0;
   active<=0;current_gap<=0;ever_gap<=0;exhausted<=0;last_valid<=0;expected_x<=0;expected_y<=0;running_crc<=32'hffffffff;
  end else if(word_valid)begin
   if(word_x==0&&word_y==0)begin
    if(active)mark_gap();else current_gap<=0;
    active<=1;current_word_count<=1;running_crc<=step16(32'hffffffff,word_data);expected_x<=0;expected_y<=1;
   end else if(active&&word_x==expected_x&&word_y==expected_y&&word_x<WIDTH&&word_y<HEIGHT)begin
    running_crc<=step16(running_crc,word_data);current_word_count<=current_word_count+1'b1;
    if(word_x==WIDTH-1&&word_y==HEIGHT-1)begin
     active<=0;
     if(current_word_count==WORDS-1&&!current_gap)begin
      last_crc<=~step16(running_crc,word_data);last_word_count<=WORDS;
      last_valid<=!ever_gap&&!exhausted&&canvas_sequence<32'hfffffffe;
      if(canvas_sequence>=32'hfffffffe)begin canvas_sequence<=32'hffffffff;exhausted<=1;end
      else canvas_sequence<=canvas_sequence+1'b1;
     end else mark_gap();
    end else if(word_y==HEIGHT-1)begin expected_x<=word_x+1'b1;expected_y<=0;end
    else begin expected_x<=word_x;expected_y<=word_y+1'b1;end
   end else begin active<=0;mark_gap();end
  end
 end
endmodule
