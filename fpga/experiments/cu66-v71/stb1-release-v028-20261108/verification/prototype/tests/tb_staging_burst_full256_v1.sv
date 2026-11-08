`timescale 1ns/1ps
module tb_staging_burst_full256_v1;
reg clk=0,rst=1,random_stall=0;reg[31:0]lfsr=32'h73c16a25;always #5 clk=~clk;
reg bw=0;reg[11:0]ba=0,br=0;reg[31:0]wd=0;reg tf=0,begin_v=0,scalar=0,seal=0,activate=0,release_v=0;
reg[63:0]gen=1;reg[31:0]length=0,expected_crc=0;
wire uv,ur,fr,blocked,fault,selected,begin_ready,sealed,active;wire[31:0]uw,rd,accepted,written,packet_bytes,crc,native_faults;wire[2:0]uc,cap;wire[8:0]queued;wire[63:0]native_gen;
reg req=0,rspready=0;reg[15:0]addr=0;wire reqready,rspvalid;wire[7:0]rspdata;wire[15:0]rspaddr;wire[63:0]rspgen;wire[31:0]rspseq;
cu71_staging_burst_v1 #(.DEPTH(256))dut(.clk,.rst,.bus_write(bw),.bus_address(ba),.bus_read_address(br),.bus_wdata(wd),.transport_fault(tf),.begin_packet(begin_v),.staged_generation(native_gen),.packet_bytes,.written_bytes(written),.actual_crc(crc),.scalar_valid(scalar),.scalar_word(wd),.native_capacity(cap),.upload_valid(uv),.upload_word(uw),.upload_count(uc),.upload_ready(ur),.fence_ready(fr),.blocked,.fault,.selected,.rdata(rd),.accepted_prefix(accepted),.queued_words(queued));
cu71_packet_staging_safe #(.MAX_BYTES(2048))stage(.clk,.rst,.begin_valid(begin_v),.begin_ready,.begin_generation(gen),.begin_bytes(length),.begin_crc(expected_crc),.upload_valid(uv),.upload_ready(ur),.upload_word(uw),.upload_count(uc),.seal_valid(seal),.activate_valid(activate),.release_valid(release_v),.discard_valid(1'b0),.sealed_valid(sealed),.active,.generation(native_gen),.packet_bytes,.written_bytes(written),.actual_crc(crc),.upload_capacity(cap),.faults(native_faults),.packet_req_valid(req),.packet_req_ready(reqready),.packet_req_address(addr),.packet_req_generation(gen),.packet_req_sequence(32'd99),.packet_rsp_valid(rspvalid),.packet_rsp_ready(rspready),.packet_rsp_address(rspaddr),.packet_rsp_generation(rspgen),.packet_rsp_sequence(rspseq),.packet_rsp_data(rspdata));
function automatic[7:0]pattern(input integer i);begin pattern=((i*73)^(i>>3)^8'ha7)&255;end endfunction
function automatic[31:0]crc_byte(input[31:0]c,input[7:0]b);reg[31:0]v;integer j;begin v=c^b;for(j=0;j<8;j=j+1)v=v[0]?(v>>1)^32'hedb88320:v>>1;crc_byte=v;end endfunction
function automatic[31:0]gold_crc(input integer n);reg[31:0]v;integer j;begin v=32'hffffffff;for(j=0;j<n;j=j+1)v=crc_byte(v,pattern(j));gold_crc=~v;end endfunction
function automatic[31:0]word_at(input integer off);begin word_at={pattern(off+3),pattern(off+2),pattern(off+1),pattern(off)};end endfunction
always @(negedge clk)if(random_stall)begin lfsr={lfsr[30:0],lfsr[31]^lfsr[21]^lfsr[1]^lfsr[0]};if(lfsr[1:0]==0)begin force stage.upload_ready=0;stall_events=stall_events+1;end else release stage.upload_ready;end
integer actual_bytes=0,actual_words=0,max_queue=0,stall_events=0;realtime worst_drain_ns=0;
always @(posedge clk)if(rst)begin actual_bytes=0;actual_words=0;max_queue=0;end else begin
 if(queued>max_queue)max_queue=queued;
 if(uv&&ur)begin
  for(integer b=0;b<4;b=b+1)if(b<uc&&uw[b*8+:8]!==pattern(actual_bytes+b))$fatal(1,"native accepted wrong byte%0d",actual_bytes+b);
  actual_bytes=actual_bytes+uc;actual_words=actual_words+1;
 end
end
task reset_all;begin @(negedge clk);rst=1;bw=0;scalar=0;tf=0;begin_v=0;seal=0;activate=0;req=0;rspready=0;repeat(4)@(negedge clk);rst=0;repeat(2)@(negedge clk);end endtask
task begin_frame(input integer bytes,input integer generation);begin @(negedge clk);gen=generation;length=bytes;expected_crc=gold_crc(bytes);begin_v=1;@(negedge clk);begin_v=0;repeat(2)@(negedge clk);end endtask
task wr(input[11:0]a,input[31:0]v);begin @(negedge clk);ba=a;wd=v;bw=1;@(negedge clk);bw=0;end endtask
task setup(input integer off,input integer n,input integer ticket,input integer g);begin wr('h720,g);wr('h724,0);wr('h728,off);wr('h72c,n);wr('h730,ticket);end endtask
task wait_drain(input integer prefix);integer count;realtime began,elapsed;begin count=0;began=$realtime;while(!fr||written!=prefix)begin @(negedge clk);count=count+1;if(count>2000)$fatal(1,"drain timeout");end if(crc!==gold_crc(prefix)||actual_bytes!==prefix||native_faults!==0)$fatal(1,"native prefix/CRC fault got%h expected%h faults%h",crc,gold_crc(prefix),native_faults);elapsed=$realtime-began;if(elapsed>worst_drain_ns)worst_drain_ns=elapsed;end endtask
task check_ram(input integer bytes);integer k;begin
 @(negedge clk);seal=1;@(negedge clk);seal=0;if(!sealed)$fatal(1,"seal failed");activate=1;@(negedge clk);activate=0;if(!active)$fatal(1,"activate failed");
 for(k=0;k<bytes;k=k+1)begin
  addr=k;req=1;do @(posedge clk);while(!reqready);@(negedge clk);req=0;
  while(!rspvalid)@(negedge clk);repeat(k%7)@(negedge clk);
  if(rspdata!==pattern(k)||rspaddr!==k||rspgen!==gen||rspseq!==99)$fatal(1,"actual byteRAM response mismatch%0d",k);
  rspready=1;@(negedge clk);rspready=0;
 end
end endtask
integer i;initial begin
 reset_all();begin_frame(1024,1);setup(0,1024,1,1);force stage.upload_ready=0;
 for(i=0;i<256;i=i+1)wr('hc00+i*4,word_at(i*4));
 if(queued!==256||accepted!==1024||actual_bytes!==0)$fatal(1,"default256 full reservation not reached");
 br='h710;#1;if(rd!==0||fr)$fatal(1,"full256 unfenced prefix leaked");
 wr('hc00,word_at(1024));if(!fault||queued!==256||accepted!==1024)$fatal(1,"default256 overflow did not reject without overwrite");
 release stage.upload_ready;wait_drain(1024);
 for(i=0;i<1024;i=i+1)if(stage.bytes[i]!==pattern(i))$fatal(1,"default256 actual native byteRAM mismatch%0d",i);
 if(dut.wp!==0||dut.rp!==0||actual_words!==256||native_faults!==0)$fatal(1,"default256 pointerwrap/native count failed");
 $display("STAGING_BURST_FULL256_METRICS drain_after_release_ns=%0f",worst_drain_ns);
 $display("STAGING_BURST_FULL256_PASS queued256 overflow_rejected acceptedwords256 actual_nativeRAM1024 CRC pointer_wrap noactivation");$finish;
end
initial begin #1000000;$fatal(1,"full256 watchdog");end
endmodule
