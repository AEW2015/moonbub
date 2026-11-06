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
cu71_packet_staging_safe #(.MAX_BYTES(LIMIT)) newer(.clk(clk),.rst(rst),.begin_valid(begin_valid),.begin_ready(begin_ready),.begin_generation(begin_generation),.begin_bytes(begin_bytes),.begin_crc(begin_crc),.upload_valid(upload_valid),.upload_ready(upload_ready),.upload_word(upload_word),.upload_count(upload_count),.seal_valid(seal_valid),.activate_valid(activate_valid),.release_valid(release_valid),.discard_valid(discard_valid),.sealed_valid(sealed_valid),.active(active),.generation(generation),.packet_bytes(packet_bytes),.written_bytes(written_bytes),.actual_crc(actual_crc),.faults(faults),.packet_req_valid(packet_req_valid),.packet_req_ready(packet_req_ready),.packet_req_address(packet_req_address),.packet_req_generation(packet_req_generation),.packet_req_sequence(packet_req_sequence),.packet_rsp_valid(packet_rsp_valid),.packet_rsp_ready(packet_rsp_ready),.packet_rsp_address(packet_rsp_address),.packet_rsp_generation(packet_rsp_generation),.packet_rsp_sequence(packet_rsp_sequence),.packet_rsp_data(packet_rsp_data),.upload_capacity(upload_capacity));

integer comparisons=0;
always @(negedge clk)if(!rst)begin
 if(newer.state==0 && newer.held_count!=0)$fatal(1,"EMPTY retained bytes");
 if(written_bytes>packet_bytes)$fatal(1,"written exceeds packet");
 comparisons=comparisons+1;
end
always @(posedge clk)if(!rst&&newer.state==1&&newer.held_count!=0)begin
 if(written_bytes>=packet_bytes || written_bytes>=LIMIT)$fatal(1,"out-of-packet physical byte write");
end
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
 $display("STAGING_SAFE_INVARIANTS_PASS limit=%0d comparisons=%0d",LIMIT,comparisons);$finish;
end
initial begin #3000000;$fatal(1,"watchdog");end
endmodule
