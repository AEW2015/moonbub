`timescale 1ns/1ps
module tb;
parameter integer BANKS=1;
reg clk=0;always #5 clk=~clk;
reg rst=1,abort_i=0,start_valid=0,key=1,tile_valid=0,tile_key=1,tile_last=0,data_ready=0;
reg[31:0]frame_id=17,tile_frame_id=17;reg[511:0]tile_pixels=0;reg[1:0]tile_plane=0;reg[16:0]tile_index=0;
wire start_ready_a,start_ready_b;
wire tile_ready_a,tile_ready_b;
wire data_valid_a,data_valid_b;
wire [7:0] data_a,data_b;
wire data_last_a,data_last_b;
wire busy_a,busy_b;
wire done_a,done_b;
wire error_a,error_b;
wire aborted_a,aborted_b;
wire [7:0] error_code_a,error_code_b;
wire [31:0] accepted_tiles_a,accepted_tiles_b;
wire [31:0] emitted_bytes_a,emitted_bytes_b;
wire [31:0] strip_word_writes_a,strip_word_writes_b;
wire [31:0] strip_word_reads_a,strip_word_reads_b;
wire [31:0] input_stall_cycles_a,input_stall_cycles_b;
wire [31:0] output_stall_cycles_a,output_stall_cycles_b;
wire write_busy_a,write_busy_b;
wire [1:0] expected_plane_a,expected_plane_b;
wire [16:0] expected_index_a,expected_index_b;
cu66_tile_rows #(.STRIP_BANKS(BANKS)) reference(.clk,.rst,.abort_i,.start_valid,.frame_id,.key,.tile_valid,.tile_pixels,.tile_frame_id,.tile_key,.tile_plane,.tile_index,.tile_last,.data_ready,.start_ready(start_ready_a),.tile_ready(tile_ready_a),.data_valid(data_valid_a),.data(data_a),.data_last(data_last_a),.busy(busy_a),.done(done_a),.error(error_a),.aborted(aborted_a),.error_code(error_code_a),.accepted_tiles(accepted_tiles_a),.emitted_bytes(emitted_bytes_a),.strip_word_writes(strip_word_writes_a),.strip_word_reads(strip_word_reads_a),.input_stall_cycles(input_stall_cycles_a),.output_stall_cycles(output_stall_cycles_a),.write_busy(write_busy_a),.expected_plane(expected_plane_a),.expected_index(expected_index_a));
cu71_tile_rows #(.STRIP_BANKS(BANKS)) candidate(.clk,.rst,.abort_i,.start_valid,.frame_id,.key,.tile_valid,.tile_pixels,.tile_frame_id,.tile_key,.tile_plane,.tile_index,.tile_last,.data_ready,.start_ready(start_ready_b),.tile_ready(tile_ready_b),.data_valid(data_valid_b),.data(data_b),.data_last(data_last_b),.busy(busy_b),.done(done_b),.error(error_b),.aborted(aborted_b),.error_code(error_code_b),.accepted_tiles(accepted_tiles_b),.emitted_bytes(emitted_bytes_b),.strip_word_writes(strip_word_writes_b),.strip_word_reads(strip_word_reads_b),.input_stall_cycles(input_stall_cycles_b),.output_stall_cycles(output_stall_cycles_b),.write_busy(write_busy_b),.expected_plane(expected_plane_b),.expected_index(expected_index_b));
integer cycles=0,checks=0,position=0,plane,p,input_index,index,byte_index,width,y,x,tile_id,expected,sendcount=0;
reg[31:0]random_state=32'h13579bdf;
always @(negedge clk)begin
 random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
 data_ready=random_state[2:0]!=0;
end
always @(posedge clk)if(!rst)begin
 cycles=cycles+1;checks=checks+1;
 if({start_ready_a,tile_ready_a,data_valid_a,data_last_a,busy_a,done_a,error_a,aborted_a,error_code_a,accepted_tiles_a,emitted_bytes_a,strip_word_writes_a,strip_word_reads_a,input_stall_cycles_a,output_stall_cycles_a,write_busy_a,expected_plane_a,expected_index_a}!=={start_ready_b,tile_ready_b,data_valid_b,data_last_b,busy_b,done_b,error_b,aborted_b,error_code_b,accepted_tiles_b,emitted_bytes_b,strip_word_writes_b,strip_word_reads_b,input_stall_cycles_b,output_stall_cycles_b,write_busy_b,expected_plane_b,expected_index_b})$fatal(1,"public control/counter mismatch cycle%0d",cycles);
 if(data_valid_a)begin
  if(data_a!==data_b)$fatal(1,"stream byte mismatch");
  if(data_ready)begin
   if(position<4)case(position)0:expected='hd0;1:expected=2;2:expected='he0;3:expected=1;endcase
   else begin
    index=position-4;plane=0;width=720;
    if(index>=345600)begin index=index-345600;plane=1;width=360;if(index>=86400)begin index=index-86400;plane=2;end end
    y=index/width;x=index%width;tile_id=(y/8)*(width/8)+x/8;
    expected=(plane*17+tile_id*3+(y%8)*8+x%8)&255;
   end
   if(data_a!==expected[7:0])$fatal(1,"independent canonical oracle offset%0d got%h expected%h",position,data_a,expected);
   position=position+1;
  end
 end
end
task tick;begin @(posedge clk);#1;end endtask
task start;begin @(negedge clk);start_valid=1;tick();@(negedge clk);start_valid=0;end endtask
initial begin
 repeat(3)tick();@(negedge clk);rst=0;start();
 for(p=0;p<3;p=p+1)begin
  for(input_index=0;input_index<(p==0?5400:1350);input_index=input_index+1)begin
   while(!tile_ready_a)tick();
   @(negedge clk);tile_plane=p;tile_index=input_index;tile_last=p==2&&input_index==1349;
   for(byte_index=0;byte_index<64;byte_index=byte_index+1)tile_pixels[byte_index*8+:8]=(p*17+input_index*3+byte_index)&255;
   tile_valid=1;tick();sendcount=sendcount+1;@(negedge clk);tile_valid=0;
  end
 end
 while(!done_a)tick();
 if(position!=518404||sendcount!=8100||error_a)$fatal(1,"full stream totals");
 // Abort/reset with populated RAM must not expose stale ownership.
 @(negedge clk);abort_i=1;tick();@(negedge clk);abort_i=0;frame_id=18;tile_frame_id=18;start();
 repeat(5)tick();@(negedge clk);abort_i=1;tick();@(negedge clk);abort_i=0;
 repeat(3)tick();@(negedge clk);rst=1;tick();@(negedge clk);rst=0;
 repeat(3)tick();
 $display("CU71_ROWS_BRAM_PASS banks=%0d cycles=%0d checks=%0d oraclebytes=518404 tiles=8100",BANKS,cycles,checks);$finish;
end
initial begin #20000000;$fatal(1,"watchdog");end
endmodule
