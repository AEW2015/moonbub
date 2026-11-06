`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=1;
reg begin_valid=0,upload_valid=0,seal_valid=0,activate_valid=0,release_valid=0,discard_valid=0;
wire begin_ready,upload_ready,sealed_valid,active;reg[63:0]begin_generation=64'h123456789abcdef0;
reg[31:0]begin_bytes=49152,begin_crc=32'hf360ad7a,upload_word=0;reg[2:0]upload_count=4;
wire[63:0]generation;wire[31:0]packet_bytes,written_bytes,actual_crc,faults;
reg packet_req_valid=0,packet_rsp_ready=0;wire packet_req_ready,packet_rsp_valid;
reg[15:0]packet_req_address=0;reg[63:0]packet_req_generation=64'h123456789abcdef0;
reg[31:0]packet_req_sequence=0;wire[15:0]packet_rsp_address;wire[63:0]packet_rsp_generation;
wire[31:0]packet_rsp_sequence;wire[7:0]packet_rsp_data;
localparam LIMIT=49152;
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
if(newer.remaining_bytes!==packet_bytes-written_bytes || newer.within_packet!==(written_bytes<=packet_bytes) || upload_capacity!==((packet_bytes-written_bytes)>=4?3'd4:(packet_bytes-written_bytes)))$fatal(1,"credit invariant rem=%h packet=%h written=%h cap=%h state=%d held=%d",newer.remaining_bytes,packet_bytes,written_bytes,upload_capacity,newer.state,newer.held_count);comparisons=comparisons+1;end

integer checks=0,i,j;reg[31:0]word_value;reg[7:0]expected;
task tick;begin @(posedge clk);#1;end endtask
task require(input ok,input[511:0]message);begin checks=checks+1;if(ok!==1'b1)$fatal(1,"%0s",message);end endtask
task request(input[15:0]addr,input[31:0]seq,input[7:0]want);
begin
 @(negedge clk);packet_req_address=addr;packet_req_sequence=seq;packet_req_valid=1;
 require(packet_req_ready,"request ready");tick();@(negedge clk);packet_req_valid=0;
 while(!packet_rsp_valid)tick();
 require(packet_rsp_address==addr&&packet_rsp_generation==packet_req_generation&&packet_rsp_sequence==seq,"response identity");
 require(packet_rsp_data==want,"byte data");
 repeat(2)begin tick();require(packet_rsp_valid&&packet_rsp_data==want&&packet_rsp_sequence==seq,"stable held response");end
 @(negedge clk);packet_rsp_ready=1;tick();@(negedge clk);packet_rsp_ready=0;
end endtask
initial begin
 repeat(3)tick();@(negedge clk);rst=0;
 begin_bytes=0;begin_valid=1;tick();@(negedge clk);begin_valid=0;require(begin_ready&&faults[0],"reject empty");
 begin_bytes=49153;begin_valid=1;tick();@(negedge clk);begin_valid=0;require(begin_ready,"reject oversized before allocation");
 begin_bytes=49152;begin_generation=0;begin_valid=1;tick();@(negedge clk);begin_valid=0;require(begin_ready,"reject zero generation");
 begin_generation=64'h123456789abcdef0;begin_valid=1;tick();@(negedge clk);begin_valid=0;
 require(!begin_ready&&upload_ready&&packet_bytes==49152,"bounded allocation");
 seal_valid=1;tick();@(negedge clk);seal_valid=0;require(!sealed_valid&&faults[2],"reject incomplete seal");
 for(i=0;i<49152;i=i+4)begin
  while(!upload_ready)tick();word_value=0;
  for(j=0;j<4;j=j+1)word_value=word_value|((((i+j)*13+7)&255)<<(8*j));
  @(negedge clk);upload_word=word_value;upload_valid=1;tick();@(negedge clk);upload_valid=0;
 end
 while(!upload_ready)tick();require(written_bytes==49152&&actual_crc==32'hf360ad7a,"whole maximum packet crc");
 @(negedge clk);seal_valid=1;tick();@(negedge clk);seal_valid=0;require(sealed_valid,"seal exact whole packet");
 begin_valid=1;upload_valid=1;tick();@(negedge clk);begin_valid=0;upload_valid=0;
 require(sealed_valid&&written_bytes==49152&&faults[1],"sealed immutable");
 activate_valid=1;tick();@(negedge clk);activate_valid=0;require(active&&!upload_ready,"activate immutable");
 discard_valid=1;tick();@(negedge clk);discard_valid=0;require(active&&faults[6],"cannot discard active");
 for(i=0;i<49152;i=i+1)request(i[15:0],i,(i*13+7)&255);
 packet_req_generation=9;request(16'd17,32'd50000,8'd0);require(faults[4],"stale generation retained as fault");
 packet_req_generation=64'h123456789abcdef0;request(16'd49152,32'd50001,8'd0);
 @(negedge clk);packet_req_valid=1;packet_req_address=0;packet_req_sequence=50002;release_valid=1;
 tick();@(negedge clk);packet_req_valid=0;release_valid=0;require(active&&faults[5],"release cannot race accepted request");
 while(!packet_rsp_valid)tick();packet_rsp_ready=1;tick();@(negedge clk);packet_rsp_ready=0;
 release_valid=1;tick();@(negedge clk);release_valid=0;require(begin_ready&&!active,"explicit drained release");
 begin_bytes=3;begin_crc=0;begin_valid=1;tick();@(negedge clk);begin_valid=0;
 upload_count=3;upload_word=32'h00abcdef;upload_valid=1;tick();@(negedge clk);upload_valid=0;
 while(!upload_ready)tick();seal_valid=1;tick();@(negedge clk);seal_valid=0;require(!sealed_valid,"reject corrupt CRC");
 discard_valid=1;tick();@(negedge clk);discard_valid=0;require(begin_ready,"discard unowned corrupt upload");
 $display("CU71_STAGING_PASS checks=%0d bytes=49152 crc=f360ad7a",checks);$finish;
end
initial begin #20000000;$fatal(1,"test watchdog");end
endmodule
