`timescale 1ns/1ps
module tb_staging_burst_unit_v1;
reg clk=0,rst=1,random_stall=0;reg[31:0]lfsr=32'h73c16a25;always #5 clk=~clk;
reg bw=0;reg[11:0]ba=0,br=0;reg[31:0]wd=0;reg tf=0,begin_v=0,scalar=0,seal=0,activate=0,release_v=0;
reg[63:0]gen=1;reg[31:0]length=0,expected_crc=0;
wire uv,ur,fr,blocked,fault,selected,begin_ready,sealed,active;wire[31:0]uw,rd,accepted,written,packet_bytes,crc,native_faults;wire[2:0]uc,cap;wire[8:0]queued;wire[63:0]native_gen;
reg req=0,rspready=0;reg[15:0]addr=0;wire reqready,rspvalid;wire[7:0]rspdata;wire[15:0]rspaddr;wire[63:0]rspgen;wire[31:0]rspseq;
cu71_staging_burst_v1 #(.DEPTH(8))dut(.clk,.rst,.bus_write(bw),.bus_address(ba),.bus_read_address(br),.bus_wdata(wd),.transport_fault(tf),.begin_packet(begin_v),.staged_generation(native_gen),.packet_bytes,.written_bytes(written),.actual_crc(crc),.scalar_valid(scalar),.scalar_word(wd),.native_capacity(cap),.upload_valid(uv),.upload_word(uw),.upload_count(uc),.upload_ready(ur),.fence_ready(fr),.blocked,.fault,.selected,.rdata(rd),.accepted_prefix(accepted),.queued_words(queued));
cu71_packet_staging_safe #(.MAX_BYTES(2048))stage(.clk,.rst,.begin_valid(begin_v),.begin_ready,.begin_generation(gen),.begin_bytes(length),.begin_crc(expected_crc),.upload_valid(uv),.upload_ready(ur),.upload_word(uw),.upload_count(uc),.seal_valid(seal),.activate_valid(activate),.release_valid(release_v),.discard_valid(1'b0),.sealed_valid(sealed),.active,.generation(native_gen),.packet_bytes,.written_bytes(written),.actual_crc(crc),.upload_capacity(cap),.faults(native_faults),.packet_req_valid(req),.packet_req_ready(reqready),.packet_req_address(addr),.packet_req_generation(gen),.packet_req_sequence(32'd99),.packet_rsp_valid(rspvalid),.packet_rsp_ready(rspready),.packet_rsp_address(rspaddr),.packet_rsp_generation(rspgen),.packet_rsp_sequence(rspseq),.packet_rsp_data(rspdata));
function automatic[7:0]pattern(input integer i);begin pattern=((i*73)^(i>>3)^8'ha7)&255;end endfunction
function automatic[31:0]crc_byte(input[31:0]c,input[7:0]b);reg[31:0]v;integer j;begin v=c^b;for(j=0;j<8;j=j+1)v=v[0]?(v>>1)^32'hedb88320:v>>1;crc_byte=v;end endfunction
function automatic[31:0]gold_crc(input integer n);reg[31:0]v;integer j;begin v=32'hffffffff;for(j=0;j<n;j=j+1)v=crc_byte(v,pattern(j));gold_crc=~v;end endfunction
function automatic[31:0]word_at(input integer off);begin word_at={pattern(off+3),pattern(off+2),pattern(off+1),pattern(off)};end endfunction
always @(negedge clk)if(random_stall)begin lfsr={lfsr[30:0],lfsr[31]^lfsr[21]^lfsr[1]^lfsr[0]};if(lfsr[1:0]==0)begin force stage.upload_ready=0;stall_events=stall_events+1;endelse release stage.upload_ready;end
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
 reset_all();begin_frame(67,1);
 setup(0,32,1,1);random_stall=1;for(i=0;i<8;i=i+1)wr('hc00+i*4,word_at(i*4));wait_drain(32);random_stall=0;release stage.upload_ready;while(blocked)@(negedge clk);
 setup(32,32,2,1);for(i=0;i<8;i=i+1)wr('hc00+i*4,word_at(32+i*4));wait_drain(64);while(blocked)@(negedge clk);
 setup(64,3,3,1);wr('hc00,word_at(64));wait_drain(67);while(blocked)@(negedge clk);
 if(fault||max_queue==0||stall_events==0)$fatal(1,"successful bounded burst queued/fault");check_ram(67);
 $display("UNIT_CASE_PASS native67 actualRAM randomized_rsp_stalls partialtail3 queuepeak%0d",max_queue);
 reset_all();begin_frame(16,2);setup(0,16,1,1);if(!fault)$fatal(1,"stale generation accepted");wr('hc00,word_at(0));if(accepted!==0||actual_bytes!==0)$fatal(1,"stale data forwarded");
 $display("UNIT_CASE_PASS stale_generation");
 reset_all();begin_frame(16,3);setup(0,16,1,3);wr('hc00,word_at(0));wr('hc08,word_at(8));wait_drain(4);if(!fault||accepted!==4)$fatal(1,"skipped alias offset not rejected");
 $display("UNIT_CASE_PASS out_of_order_alias preserves_accepted_prefix");
 reset_all();begin_frame(32,4);setup(0,32,1,4);force stage.upload_ready=0;
 for(i=0;i<8;i=i+1)wr('hc00+i*4,word_at(i*4));br='h710;#1;if(rd!==0||fr||queued!==8)$fatal(1,"unfenced prefix leaked");br='h70c;#1;if(rd!==0)$fatal(1,"unfenced credit leaked");
 wr('hc00,word_at(32));if(!fault||accepted!==32||queued!==8)$fatal(1,"overflow/extra word not failclosed");release stage.upload_ready;wait_drain(32);
 $display("UNIT_CASE_PASS full_FIFO_overflow drain_all_preaccepted nativeCRC32");
 reset_all();begin_frame(32,5);setup(0,32,1,5);force stage.upload_ready=0;for(i=0;i<4;i=i+1)wr('hc00+i*4,word_at(i*4));
 reset_all();release stage.upload_ready;begin_frame(3,9);setup(0,3,1,9);wr('hc00,word_at(0));wait_drain(3);if(fault||actual_words!==1)$fatal(1,"reset retained stale accepted writes");check_ram(3);
 $display("UNIT_CASE_PASS reset_cancels_old_epoch no_stale_RAM_exposure");
 reset_all();begin_frame(16,10);setup(0,16,1,10);@(negedge clk);scalar=1;wd=word_at(0);@(negedge clk);scalar=0;if(!fault||actual_bytes!==0)$fatal(1,"scalar collision not rejected");
 $display("UNIT_CASE_PASS scalar_burst_collision");
 reset_all();begin_frame(16,11);setup(0,16,1,11);force stage.upload_ready=0;wr('hc00,word_at(0));wr('hc04,word_at(4));tf=1;@(negedge clk);release stage.upload_ready;wait_drain(8);if(!fault||actual_bytes!==8)$fatal(1,"transportfault failed to drain preaccepted writes");
 $display("UNIT_CASE_PASS transportfault_preaccepted_drain");
 $display("STAGING_BURST_UNIT_METRICS worst_wait_after_payload_ns=%0f random_stall_events=%0d",worst_drain_ns,stall_events);
 $display("STAGING_BURST_UNIT_PASS cases7 actual_native_staging CRC acceptedwordscoreboard responsebackpressure overflow stale reset fence");$finish;
end
initial begin #1000000;$fatal(1,"unit watchdog");end
endmodule
