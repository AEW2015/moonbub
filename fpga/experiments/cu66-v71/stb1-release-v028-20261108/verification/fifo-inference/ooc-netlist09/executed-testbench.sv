`timescale 1ns/1ps
`ifndef STB_DUT
`define STB_DUT cu71_staging_burst_v1
`endif
module tb_stb1_blackbox;
reg clk=0,rst,stall;always #5 clk=~clk;
reg bus_write;reg[11:0]bus_address,bus_read_address;reg[31:0]bus_wdata;
reg transport_fault,begin_packet,scalar_valid;reg[31:0]scalar_word;
reg[63:0]begin_generation;reg[31:0]begin_bytes,begin_crc;
reg seal_valid,activate_valid,release_valid;
wire[63:0]staged_generation;wire[31:0]packet_bytes,written_bytes,actual_crc,native_faults;
wire[2:0]native_capacity,upload_count;wire upload_ready,stage_ready,upload_valid;
wire[31:0]upload_word,rdata,accepted_prefix;wire[8:0]queued_words;
wire fence_ready,blocked,fault,selected,begin_ready,sealed_valid,active;
assign upload_ready=stage_ready&&!stall;
`STB_DUT dut(.clk,.rst,.bus_write,.bus_address,.bus_read_address,.bus_wdata,.transport_fault,.begin_packet,.staged_generation,.packet_bytes,.written_bytes,.actual_crc,.scalar_valid,.scalar_word,.native_capacity,.upload_valid,.upload_word,.upload_count,.upload_ready,.fence_ready,.blocked,.fault,.selected,.rdata,.accepted_prefix,.queued_words);
reg packet_req_valid,packet_rsp_ready;reg[15:0]packet_req_address;
wire packet_req_ready,packet_rsp_valid;wire[7:0]packet_rsp_data;wire[15:0]packet_rsp_address;wire[63:0]packet_rsp_generation;wire[31:0]packet_rsp_sequence;
// External handshake backpressure only. No hierarchy references/force into either DUT.
cu71_packet_staging_safe #(.MAX_BYTES(8192))native_stage(.clk,.rst,.begin_valid(begin_packet),.begin_ready,.begin_generation,.begin_bytes,.begin_crc,.upload_valid(upload_valid&&!stall),.upload_ready(stage_ready),.upload_word,.upload_count,.seal_valid,.activate_valid,.release_valid,.discard_valid(1'b0),.sealed_valid,.active,.generation(staged_generation),.packet_bytes,.written_bytes,.actual_crc,.upload_capacity(native_capacity),.faults(native_faults),.packet_req_valid,.packet_req_ready,.packet_req_address,.packet_req_generation(begin_generation),.packet_req_sequence(32'h0c33ab72),.packet_rsp_valid,.packet_rsp_ready,.packet_rsp_address,.packet_rsp_generation,.packet_rsp_sequence,.packet_rsp_data);
function automatic[7:0]pattern(input integer i);begin pattern=((i*73)^(i>>3)^8'ha7)&255;end endfunction
function automatic[31:0]crc_byte(input[31:0]c,input[7:0]b);reg[31:0]v;integer j;begin v=c^b;for(j=0;j<8;j=j+1)v=v[0]?(v>>1)^32'hedb88320:v>>1;crc_byte=v;end endfunction
function automatic[31:0]gold_crc(input integer n);reg[31:0]v;integer j;begin v=32'hffffffff;for(j=0;j<n;j=j+1)v=crc_byte(v,pattern(j));gold_crc=~v;end endfunction
function automatic[31:0]word_at(input integer n);begin word_at={pattern(n+3),pattern(n+2),pattern(n+1),pattern(n)};end endfunction
integer actual_bytes=0,actual_words=0,total_ram_compared=0,full_events=0,scenarios=0;
always @(posedge clk)begin
 if(rst||begin_packet)begin actual_bytes=0;actual_words=0;end
 else if(upload_valid&&upload_ready)begin
  if(upload_count<1||upload_count>4)$fatal(1,"invalid upload count");
  for(integer b=0;b<4;b=b+1)if(b<upload_count&&upload_word[b*8+:8]!==pattern(actual_bytes+b))$fatal(1,"actual accepted byte mismatch%0d",actual_bytes+b);
  actual_bytes=actual_bytes+upload_count;actual_words=actual_words+1;
 end
end
task reset_all;begin @(negedge clk);rst=0;repeat(2)@(negedge clk);rst=1;stall=0;bus_write=0;scalar_valid=0;transport_fault=0;begin_packet=0;seal_valid=0;activate_valid=0;release_valid=0;packet_req_valid=0;packet_rsp_ready=0;repeat(5)@(negedge clk);rst=0;repeat(3)@(negedge clk);if(fault!==0||queued_words!==0||blocked!==0)$fatal(1,"reset did not clear public state");end endtask
task begin_frame(input integer n,input[63:0]g);begin @(negedge clk);begin_bytes=n;begin_crc=gold_crc(n);begin_generation=g;begin_packet=1;@(negedge clk);begin_packet=0;repeat(3)@(negedge clk);end endtask
task wr(input[11:0]a,input[31:0]v);begin @(negedge clk);bus_address=a;bus_wdata=v;bus_write=1;@(negedge clk);bus_write=0;end endtask
task setup(input integer off,input integer n,input integer ticket,input[63:0]g);begin wr('h720,g[31:0]);wr('h724,g[63:32]);wr('h728,off);wr('h72c,n);bus_read_address='h720;#1;$display("SHADOW g_lo=%h",rdata);bus_read_address='h724;#1;$display("SHADOW g_hi=%h",rdata);bus_read_address='h728;#1;$display("SHADOW off=%h",rdata);bus_read_address='h72c;#1;$display("SHADOW bytes=%h packet=%h written=%h",rdata,packet_bytes,written_bytes);bus_read_address='h718;#1;$display("SHADOW ticket=%h",rdata);bus_read_address='h708;#1;$display("PRE_SETUP flags=%h fence=%b blocked=%b fault=%b ready=%b scalar=%b tf=%b",rdata,fence_ready,blocked,fault,upload_ready,scalar_valid,transport_fault);wr('h730,ticket);end endtask
task drain(input integer n);integer k;begin k=0;while(blocked!==0||fence_ready!==1||written_bytes!==n)begin @(negedge clk);k=k+1;if(k>5000)$fatal(1,"bounded drain timeout n=%0d written=%0d",n,written_bytes);end
 if(actual_bytes!==n||accepted_prefix!==n||actual_crc!==gold_crc(n)||native_faults!==0)$fatal(1,"native prefix/CRC/fault mismatch");
 bus_read_address='h710;#1;if(rdata!==n)$fatal(1,"fenced count mismatch");bus_read_address='h714;#1;if(rdata!==gold_crc(n))$fatal(1,"fenced CRC mismatch");end endtask
task fill(input integer off,input integer n,input integer ticket,input bit hold);integer k;begin
 setup(off,n,ticket,begin_generation);if(fault!==0)$fatal(1,"legal descriptor fault");if(hold)stall=1;
 for(k=0;k<(n+3)/4;k=k+1)wr('hc00+k*4,word_at(off+k*4));
 if(hold)begin if(queued_words!==(n+3)/4||actual_bytes!==off)$fatal(1,"full reservation mismatch queued=%0d expected=%0d bytes=%0d expected_bytes=%0d accepted=%0d fault=%b armed_blocked=%b",queued_words,(n+3)/4,actual_bytes,off,accepted_prefix,fault,blocked);bus_read_address='h710;#1;if(rdata!==0||fence_ready)$fatal(1,"unfenced count leaked");if(n==1024)full_events=full_events+1;stall=0;end
 drain(off+n);end endtask
task check_ram(input integer n);integer k,timeout;begin
 @(negedge clk);seal_valid=1;@(negedge clk);seal_valid=0;if(sealed_valid!==1)$fatal(1,"native seal failed");activate_valid=1;@(negedge clk);activate_valid=0;if(active!==1)$fatal(1,"native activate failed");
 for(k=0;k<n;k=k+1)begin
  packet_req_address=k;packet_req_valid=1;timeout=0;
  do begin @(posedge clk);timeout=timeout+1;if(timeout>100)$fatal(1,"packet request timeout");end while(!packet_req_ready);
  @(negedge clk);packet_req_valid=0;timeout=0;
  while(!packet_rsp_valid)begin @(negedge clk);timeout=timeout+1;if(timeout>100)$fatal(1,"packet response timeout");end
  repeat(k%3)@(negedge clk);
  if(packet_rsp_data!==pattern(k)||packet_rsp_address!==k||packet_rsp_generation!==begin_generation||packet_rsp_sequence!==32'h0c33ab72)$fatal(1,"actual native packet RAM mismatch%0d",k);
  total_ram_compared=total_ram_compared+1;packet_rsp_ready=1;@(negedge clk);packet_rsp_ready=0;
 end
end endtask
always @(posedge clk) if(bus_write && (bus_address==12'h730 || bus_address==12'hc00)) begin #1; $display("PUBLIC_WRITE a=%h data=%h gen=%h capacity=%0d ready=%b accepted=%0d queued=%0d fault=%b blocked=%b",bus_address,bus_wdata,staged_generation,native_capacity,upload_ready,accepted_prefix,queued_words,fault,blocked); end
initial begin
 #1; // Real post-initialization pin transitions, avoiding stale INIT_REG startup events.
 rst=1;stall=0;bus_write=0;bus_address=0;bus_read_address=0;bus_wdata=0;transport_fault=0;begin_packet=0;scalar_valid=0;scalar_word=0;begin_generation=1;begin_bytes=0;begin_crc=0;seal_valid=0;activate_valid=0;release_valid=0;packet_req_valid=0;packet_rsp_ready=0;packet_req_address=0;
end
integer i,tail;initial begin
 #200; // Allow UNISIM glbl GSR startup to settle before the common reset.
 reset_all();begin_frame(1024,1);fill(0,1024,1,1);check_ram(1024);scenarios=scenarios+1;$display("CASE full256 passed");
 reset_all();begin_frame(6147,64'h100000002);
 for(i=0;i<6;i=i+1)fill(i*1024,1024,i+1,1);
 fill(6144,3,7,0);check_ram(6147);scenarios=scenarios+1;$display("CASE multi_descriptor_wrap passed");
 for(tail=1;tail<=3;tail=tail+1)begin reset_all();begin_frame(1024+tail,10+tail);fill(0,1024,1,0);fill(1024,tail,2,0);check_ram(1024+tail);scenarios=scenarios+1;$display("CASE partial_tail%0d passed",tail);end
 reset_all();begin_frame(16,64'h100000033);setup(0,16,1,64'h33);if(fault!==1||accepted_prefix!==0||written_bytes!==0||queued_words!==0)$fatal(1,"stale high generation not rejected");scenarios=scenarios+1;$display("CASE stale_generation passed");
 reset_all();begin_frame(1024,50);setup(0,1024,1,50);stall=1;for(i=0;i<256;i=i+1)wr('hc00+i*4,word_at(i*4));wr('hc00,32'hdeadbeef);if(fault!==1||queued_words!==256||accepted_prefix!==1024)$fatal(1,"extra in-window word not rejected");stall=0;drain(1024);check_ram(1024);scenarios=scenarios+1;$display("CASE in_window_overflow_and_drain passed");
 reset_all();begin_frame(1024,60);setup(0,1024,1,60);stall=1;for(i=0;i<128;i=i+1)wr('hc00+i*4,word_at(i*4));reset_all();begin_frame(1025,61);fill(0,1024,1,1);fill(1024,1,2,0);check_ram(1025);scenarios=scenarios+1;$display("CASE reset_queued_then_reuse passed");
 reset_all();begin_frame(1024,70);setup(0,1024,1,70);stall=1;for(i=0;i<256;i=i+1)wr('hc00+i*4,word_at(i*4));scalar_word=32'hbadbadba;scalar_valid=1;@(negedge clk);scalar_valid=0;if(fault!==1||accepted_prefix!==1024||actual_bytes!==0)$fatal(1,"scalar collision not rejected");stall=0;drain(1024);check_ram(1024);scenarios=scenarios+1;$display("CASE scalar_collision passed");
 reset_all();begin_frame(7,80);scalar_word=word_at(0);scalar_valid=1;@(negedge clk);scalar_valid=0;repeat(4)@(negedge clk);scalar_word=word_at(4);scalar_valid=1;@(negedge clk);scalar_valid=0;drain(7);check_ram(7);scenarios=scenarios+1;$display("CASE scalar_passthrough passed");
 if(full_events<8||scenarios!=10)$fatal(1,"scenario coverage missing");
 $display("STB1_BLACKBOX_PASS scenarios=%0d full_events=%0d actual_RAM_bytes_compared=%0d",scenarios,full_events,total_ram_compared);$finish;
end
initial begin #10000000;$fatal(1,"blackbox watchdog");end
endmodule
