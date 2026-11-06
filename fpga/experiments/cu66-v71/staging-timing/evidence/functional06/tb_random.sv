`timescale 1ns/1ps
module tb_random;
parameter integer LIMIT=49152;
reg  clk=0;
reg  rst=0;
reg  begin_valid=0;
wire  begin_ready;
reg [63:0] begin_generation=0;
reg [31:0] begin_bytes=0;
reg [31:0] begin_crc=0;
reg  upload_valid=0;
wire  upload_ready;
reg [31:0] upload_word=0;
reg [2:0] upload_count=0;
reg  seal_valid=0;
reg  activate_valid=0;
reg  release_valid=0;
reg  discard_valid=0;
wire  sealed_valid;
wire  active;
wire [63:0] generation;
wire [31:0] packet_bytes;
wire [31:0] written_bytes;
wire [31:0] actual_crc;
wire [31:0] faults;
reg  packet_req_valid=0;
wire  packet_req_ready;
reg [15:0] packet_req_address=0;
reg [63:0] packet_req_generation=0;
reg [31:0] packet_req_sequence=0;
wire  packet_rsp_valid;
reg  packet_rsp_ready=0;
wire [15:0] packet_rsp_address;
wire [63:0] packet_rsp_generation;
wire [31:0] packet_rsp_sequence;
wire [7:0] packet_rsp_data;
always #5 clk=~clk;

wire[2:0]upload_capacity;
wire  old_begin_ready;
wire  old_upload_ready;
wire  old_sealed_valid;
wire  old_active;
wire [63:0] old_generation;
wire [31:0] old_packet_bytes;
wire [31:0] old_written_bytes;
wire [31:0] old_actual_crc;
wire [31:0] old_faults;
wire  old_packet_req_ready;
wire  old_packet_rsp_valid;
wire [15:0] old_packet_rsp_address;
wire [63:0] old_packet_rsp_generation;
wire [31:0] old_packet_rsp_sequence;
wire [7:0] old_packet_rsp_data;
cu71_packet_staging #(.MAX_BYTES(LIMIT)) old(.clk(clk),.rst(rst),.begin_valid(begin_valid),.begin_ready(old_begin_ready),.begin_generation(begin_generation),.begin_bytes(begin_bytes),.begin_crc(begin_crc),.upload_valid(upload_valid),.upload_ready(old_upload_ready),.upload_word(upload_word),.upload_count(upload_count),.seal_valid(seal_valid),.activate_valid(activate_valid),.release_valid(release_valid),.discard_valid(discard_valid),.sealed_valid(old_sealed_valid),.active(old_active),.generation(old_generation),.packet_bytes(old_packet_bytes),.written_bytes(old_written_bytes),.actual_crc(old_actual_crc),.faults(old_faults),.packet_req_valid(packet_req_valid),.packet_req_ready(old_packet_req_ready),.packet_req_address(packet_req_address),.packet_req_generation(packet_req_generation),.packet_req_sequence(packet_req_sequence),.packet_rsp_valid(old_packet_rsp_valid),.packet_rsp_ready(packet_rsp_ready),.packet_rsp_address(old_packet_rsp_address),.packet_rsp_generation(old_packet_rsp_generation),.packet_rsp_sequence(old_packet_rsp_sequence),.packet_rsp_data(old_packet_rsp_data));
cu71_packet_staging_credit #(.MAX_BYTES(LIMIT)) newer(.clk(clk),.rst(rst),.begin_valid(begin_valid),.begin_ready(begin_ready),.begin_generation(begin_generation),.begin_bytes(begin_bytes),.begin_crc(begin_crc),.upload_valid(upload_valid),.upload_ready(upload_ready),.upload_word(upload_word),.upload_count(upload_count),.seal_valid(seal_valid),.activate_valid(activate_valid),.release_valid(release_valid),.discard_valid(discard_valid),.sealed_valid(sealed_valid),.active(active),.generation(generation),.packet_bytes(packet_bytes),.written_bytes(written_bytes),.actual_crc(actual_crc),.faults(faults),.packet_req_valid(packet_req_valid),.packet_req_ready(packet_req_ready),.packet_req_address(packet_req_address),.packet_req_generation(packet_req_generation),.packet_req_sequence(packet_req_sequence),.packet_rsp_valid(packet_rsp_valid),.packet_rsp_ready(packet_rsp_ready),.packet_rsp_address(packet_rsp_address),.packet_rsp_generation(packet_rsp_generation),.packet_rsp_sequence(packet_rsp_sequence),.packet_rsp_data(packet_rsp_data),.upload_capacity(upload_capacity));
integer comparisons=0; always @(negedge clk) if(!rst)begin
if($time>853000 && $time<853330)$display("DBG t=%0t state=%d packet=%h written=%h rem=%h cap=%d held=%d begin=%d bytes=%h upload=%d count=%d seal=%d act=%d disc=%d rel=%d",$time,newer.state,packet_bytes,written_bytes,newer.remaining_bytes,upload_capacity,newer.held_count,begin_valid,begin_bytes,upload_valid,upload_count,seal_valid,activate_valid,discard_valid,release_valid);
if(begin_ready!==old_begin_ready)$fatal(1,"MISMATCH begin_ready at %0t",$time);
if(upload_ready!==old_upload_ready)$fatal(1,"MISMATCH upload_ready at %0t",$time);
if(sealed_valid!==old_sealed_valid)$fatal(1,"MISMATCH sealed_valid at %0t",$time);
if(active!==old_active)$fatal(1,"MISMATCH active at %0t",$time);
if(generation!==old_generation)$fatal(1,"MISMATCH generation at %0t",$time);
if(packet_bytes!==old_packet_bytes)$fatal(1,"MISMATCH packet_bytes at %0t",$time);
if(written_bytes!==old_written_bytes)$fatal(1,"MISMATCH written_bytes at %0t",$time);
if(actual_crc!==old_actual_crc)$fatal(1,"MISMATCH actual_crc at %0t",$time);
if(faults!==old_faults)$fatal(1,"MISMATCH faults at %0t",$time);
if(packet_req_ready!==old_packet_req_ready)$fatal(1,"MISMATCH packet_req_ready at %0t",$time);
if(packet_rsp_valid!==old_packet_rsp_valid)$fatal(1,"MISMATCH packet_rsp_valid at %0t",$time);
if(packet_rsp_address!==old_packet_rsp_address)$fatal(1,"MISMATCH packet_rsp_address at %0t",$time);
if(packet_rsp_generation!==old_packet_rsp_generation)$fatal(1,"MISMATCH packet_rsp_generation at %0t",$time);
if(packet_rsp_sequence!==old_packet_rsp_sequence)$fatal(1,"MISMATCH packet_rsp_sequence at %0t",$time);
if(packet_rsp_data!==old_packet_rsp_data)$fatal(1,"MISMATCH packet_rsp_data at %0t",$time);
if(newer.remaining_bytes!==packet_bytes-written_bytes || upload_capacity!==((packet_bytes-written_bytes)>=4?3'd4:(packet_bytes-written_bytes)))$fatal(1,"credit invariant rem=%h packet=%h written=%h cap=%h state=%d held=%d",newer.remaining_bytes,packet_bytes,written_bytes,upload_capacity,newer.state,newer.held_count);comparisons=comparisons+1;end

integer i,j,n;reg[31:0]seed=32'h10ade321;reg[31:0]rv;
task step;begin @(posedge clk);#1;@(negedge clk);#1;end endtask
task clear_inputs;begin begin_valid=0;upload_valid=0;seal_valid=0;activate_valid=0;release_valid=0;discard_valid=0;packet_req_valid=0;packet_rsp_ready=0;end endtask
initial begin
 rst=1;repeat(3)step();rst=0;clear_inputs();
 // Every accepted length modulo4 and every raw count0..7, including overflow.
 for(n=1;n<=17;n=n+1)begin
  begin_valid=1;begin_bytes=n;begin_generation=n;begin_crc=0;step();begin_valid=0;
  for(j=0;j<8;j=j+1)begin upload_count=j;upload_word=32'hff00a511;upload_valid=1;step();upload_valid=0;repeat(5)step();end
  discard_valid=1;step();discard_valid=0;
 end
 // Full arbitrary32-bit begins/requests and simultaneous invalid commands.
 for(i=0;i<180000;i=i+1)begin
  rv=$random(seed);rst=(rv[15:0]==0);
  begin_valid=(rv[5:0]==0);upload_valid=rv[6];seal_valid=(rv[10:7]==0);activate_valid=(rv[14:11]==0);
  release_valid=(rv[18:15]==0);discard_valid=(rv[22:19]==0);packet_req_valid=rv[23];packet_rsp_ready=rv[24];
  begin_generation={$random(seed),$random(seed)};begin_bytes=(rv[25]?$random(seed):($unsigned($random(seed))%23));begin_crc=$random(seed);
  upload_word=$random(seed);upload_count=rv[28:26];packet_req_address=$random(seed);packet_req_generation=$random(seed);packet_req_sequence=$random(seed);
  step();
 end
 $display("STAGING_CREDIT_DIFFERENTIAL_PASS limit=%0d comparisons=%0d",LIMIT,comparisons);$finish;
end
initial begin #3000000;$fatal(1,"watchdog");end
endmodule
