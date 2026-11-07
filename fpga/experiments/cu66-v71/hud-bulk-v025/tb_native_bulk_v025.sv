`timescale 1ns/1ps
module tb_native_bulk_v025 #(parameter integer CORRUPT=0);
 reg clk=0;always #5 clk=~clk;
 reg rst=1,bus_write=0;reg[11:0]bus_address=0,bus_read_address=0;reg[31:0]bus_wdata=0;wire selected;wire[31:0]bus_rdata;
 reg setup_valid=0,identity_valid=1,run_valid=0,hud_live=1;
 wire setup_ready,setup_error,run_ready,done,error,active;
 reg[63:0]command_generation=5,live_generation=5;reg[31:0]command_frame=7,command_reference=6,command_ticket=1,word_offset=0,word_count=0,read_mode=0;
 reg[1:0]command_bank=1,live_bank=1;reg[31:0]live_frame=7,live_reference=6,live_ticket=1;
 wire req_valid,req_ready,req_write,rsp_ready;wire[63:0]req_generation;wire[31:0]req_frame;wire[23:0]req_address;wire[15:0]req_data;wire[8:0]completed_words;
 reg rsp_valid=0,rsp_error=0;reg[15:0]rsp_data=0;
 dy71_hud_bulk_v025 dut(.*,.bus_selected(selected));
 reg allow_req=1,allow_rsp=1,pending=0;integer delay_count=0,cycles=0,requests=0,responses=0,run_requests=0,fail_index=-1;
 reg[23:0]saved_address;reg[15:0]saved_data;reg saved_write;reg[15:0]memory[0:63359];
 integer expect_offset=0,expect_bank=1;
 wire[23:0]expect_base=expect_bank==0?24'h100000:expect_bank==1?24'h500000:24'h900000;
 function automatic integer mem_index(input[23:0]a);
 begin if(a>=24'h100000&&a<24'h105280)mem_index=a-24'h100000;
 else if(a>=24'h500000&&a<24'h505280)mem_index=21120+a-24'h500000;
 else if(a>=24'h900000&&a<24'h905280)mem_index=42240+a-24'h900000;
 else begin $fatal(1,"AUX escaped HUD banks %h",a);mem_index=0;end end endfunction
 assign req_ready=!rst&&allow_req&&!pending&&!rsp_valid&&(cycles%7!=0);
 reg was_stalled=0;reg[136:0]held;
 always @(posedge clk)begin
  if(rst)begin cycles<=0;pending<=0;rsp_valid<=0;delay_count<=0;was_stalled<=0;end
  else begin
   cycles<=cycles+1;
   if(was_stalled&&(!req_valid||{req_generation,req_frame,req_write,req_address,req_data}!==held))$fatal(1,"ready/valid request changed under backpressure");
   was_stalled<=req_valid&&!req_ready;held<={req_generation,req_frame,req_write,req_address,req_data};
   if(req_valid&&req_ready)begin
    if(req_generation!==command_generation||req_frame!==command_frame||req_address!==expect_base+expect_offset+run_requests)$fatal(1,"AUX identity/address sequence");
    saved_address<=req_address;saved_data<=req_data;saved_write<=req_write;pending<=1;delay_count<=(requests*7)%11+1;requests<=requests+1;run_requests<=run_requests+1;
   end
   if(pending)begin
    if(delay_count>0)delay_count<=delay_count-1;
    else if(allow_rsp)begin pending<=0;rsp_valid<=1;rsp_data<=memory[mem_index(saved_address)]^((CORRUPT&&!saved_write&&saved_address[15:0]==1234)?16'd1:16'd0);rsp_error<=(run_requests-1==fail_index);if(saved_write)memory[mem_index(saved_address)]<=saved_data;end
   end
   if(rsp_valid&&rsp_ready)begin rsp_valid<=0;responses<=responses+1;end
  end
 end
 reg[15:0]gold0[0:21119],gold1[0:21119];integer gold_frame=0;
 function automatic[15:0]pattern(input integer x);begin pattern=gold_frame==0?gold0[x]:gold1[x];end endfunction
 task tick;begin @(posedge clk);#1;end endtask
 task setup(input integer off,input integer n,input integer rd,input integer legal);
 begin @(negedge clk);word_offset=off;word_count=n;read_mode=rd;setup_valid=1;#1;if(!setup_ready||setup_error!==!legal)$fatal(1,"setup legality off%0d n%0d",off,n);tick();@(negedge clk);setup_valid=0;expect_offset=off;expect_bank=command_bank;run_requests=0;end endtask
 task load(input integer slot,input[31:0]value);
 begin @(negedge clk);bus_write=1;bus_address=12'h400+slot*4;bus_wdata=value;tick();@(negedge clk);bus_write=0;end endtask
 task fill(input integer off,input integer n);
 integer k;reg[31:0]v;begin for(k=0;k<(n+1)/2;k=k+1)begin v={pattern(off+k*2+1),pattern(off+k*2)};if(k*2+1==n)v[31:16]=0;load(k,v);end end endtask
 task kick;
 begin @(negedge clk);run_valid=1;#1;if(!run_ready)$fatal(1,"run not ready");tick();@(negedge clk);run_valid=0;end endtask
 task wait_done(input integer expected_error);
 integer watchdog;begin watchdog=0;while(!done)begin tick();watchdog=watchdog+1;if(watchdog>20000)$fatal(1,"block watchdog");end if(error!==expected_error[0])$fatal(1,"block result error%0d expected%0d",error,expected_error);end endtask
 task read_csr(input[11:0]a,output[31:0]v);
 begin @(negedge clk);bus_read_address=a;repeat(3)tick();v=bus_rdata;end endtask

 integer i,off,n,k;reg[31:0]v,expected;
 initial begin
  $readmemh("C:/mb70/fpga/experiments/cu66-v71/hud-bulk-v025/native-gold/words0.hex",gold0);
  $readmemh("C:/mb70/fpga/experiments/cu66-v71/hud-bulk-v025/native-gold/words1.hex",gold1);
  for(i=0;i<63360;i=i+1)memory[i]=16'hdead;
  repeat(24)tick();@(negedge clk);rst=0;
  for(gold_frame=0;gold_frame<2;gold_frame=gold_frame+1)begin
   command_generation=gold_frame+1;live_generation=command_generation;command_frame=gold_frame;live_frame=command_frame;command_reference=gold_frame==0?32'hffffffff:0;live_reference=command_reference;command_ticket=gold_frame+1;live_ticket=command_ticket;command_bank=gold_frame;live_bank=command_bank;
   for(off=0;off<21120;off=off+256)begin n=(21120-off)>256?256:(21120-off);setup(off,n,0,1);fill(off,n);kick();wait_done(0);if(completed_words!=n)$fatal(1,"native write count");end
   for(off=0;off<21120;off=off+256)begin n=(21120-off)>256?256:(21120-off);setup(off,n,1,1);kick();wait_done(0);
    for(k=0;k<(n+1)/2;k=k+1)begin read_csr('h400+k*4,v);expected={pattern(off+k*2+1),pattern(off+k*2)};if(v!==expected)$fatal(1,"native readback mismatch frame%0d word%0d got%h expected%h",gold_frame,off+k*2,v,expected);end
   end
  end
  if(requests!=84480||responses!=84480)$fatal(1,"actual native full coverage counts");
  $display("NATIVE_BULK_PASS frames2 HUD_words_written42240 actual_readback_words42240 requests84480 responses84480 original_HU_golden_CRC358486a6_9b082f5c");$finish;
 end
 initial begin #50000000;$fatal(1,"native watchdog");end
endmodule
