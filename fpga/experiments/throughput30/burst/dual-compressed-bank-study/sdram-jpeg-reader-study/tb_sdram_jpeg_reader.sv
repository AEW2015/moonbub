`timescale 1ns/1ps
module tb_sdram_jpeg_reader;
 localparam integer BASE='h060000;
 reg clk=0,reset=1,start=0,owned=1,inject=0;always #5 clk=~clk;
 reg[31:0]granted_length=0;wire start_accept,active,error,frame_done,mem_req_valid,read_inflight,faulted,out_valid;
 wire[23:0]mem_req_addr;wire[31:0]out_data;wire[3:0]out_strb;
 integer cycle=0,left=0,delay=0,base_byte=0,beat=0,req_count=0,expected_addr=BASE;
 reg mem_data_valid=0;reg[15:0]mem_data=0;
 wire mem_req_ready=(cycle%5)!=0;
 wire out_ready=(cycle%7)<4;
 sdram_jpeg_reader dut(.clk(clk),.reset(reset),.start(start),.owned(owned),.granted_length(granted_length),
  .start_accept(start_accept),.active(active),.error(error),.frame_done(frame_done),
  .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_addr(mem_req_addr),
  .mem_data_valid(mem_data_valid||inject),.mem_data(mem_data),.out_valid(out_valid),.out_data(out_data),.out_strb(out_strb),.out_ready(out_ready),.read_inflight(read_inflight),.faulted(faulted));
 function automatic [7:0] value(input integer idx);value=8'(idx*13+49);endfunction
 integer got=0,words=0,frames=0;reg saw_error=0,held=0;reg[35:0]held_value;
 integer k;reg[31:0]expected;reg[3:0]strb;integer take;
 always @(posedge clk)begin
  cycle<=cycle+1;
  if(reset)begin left<=0;delay<=0;mem_data_valid<=0;mem_data<=0;beat<=0;end
  else begin
   if(mem_req_valid&&mem_req_ready)begin
    if(left!=0||{8'd0,mem_req_addr}!=expected_addr)$fatal(1,"request address/order got=%h expected=%h",mem_req_addr,expected_addr);
    base_byte<=({8'd0,mem_req_addr}-BASE)*2;left<=8;delay<=2;beat<=0;expected_addr=expected_addr+8;req_count=req_count+1;
   end
   mem_data_valid<=0;
   if(delay>0)delay<=delay-1;
   else if(left>0)begin
    mem_data<={value(base_byte+2*beat+1),value(base_byte+2*beat)};
    mem_data_valid<=1;beat<=beat+1;left<=left-1;
   end
   if(error)saw_error<=1;
   if(held && (!out_valid || {out_data,out_strb}!==held_value))$fatal(1,"output changed under backpressure");
   held<=out_valid&&!out_ready;if(out_valid&&!out_ready)held_value<={out_data,out_strb};
   if(out_valid&&out_ready)begin
    take=granted_length-got;if(take>4)take=4;expected=0;strb=0;
    for(k=0;k<take;k=k+1)begin expected[k*8+:8]=value(got+k);strb[k]=1;end
    if(out_data!==expected||out_strb!==strb)$fatal(1,"word/strobe mismatch byte=%0d",got);
    got=got+take;words=words+1;
   end
   if(frame_done)frames=frames+1;
  end
 end
 task automatic run_length(input integer n);
 integer timeout_count;
 begin
  @(negedge clk);granted_length=n;got=0;words=0;req_count=0;expected_addr=BASE;start=1;
  @(negedge clk);start=0;if(!start_accept)$fatal(1,"start rejected n=%0d",n);
  timeout_count=0;while(!frame_done)begin @(negedge clk);timeout_count=timeout_count+1;if(timeout_count>1000000)$fatal(1,"length timeout");end
  if(got!=n||words!=(n+3)/4||req_count!=(n+15)/16||read_inflight||faulted)$fatal(1,"length accounting n=%0d got=%0d words=%0d req=%0d",n,got,words,req_count);
 end endtask
 integer lens[0:12];integer i;
 initial begin
  lens[0]=1;lens[1]=2;lens[2]=3;lens[3]=4;lens[4]=15;lens[5]=16;lens[6]=17;
  lens[7]=31;lens[8]=32;lens[9]=33;lens[10]=257;lens[11]=26991;lens[12]=262144;
  repeat(3)@(negedge clk);reset=0;
  for(i=0;i<13;i=i+1)run_length(lens[i]);
  // Revocation during an outstanding read discards the buffer and drains the
  // eight already-issued beats before a new owner can start.
  @(negedge clk);granted_length=100;got=0;expected_addr=BASE;req_count=0;start=1;
  @(negedge clk);start=0;while(!read_inflight)@(negedge clk);owned=0;
  @(negedge clk);if(out_valid)$fatal(1,"revoked output still valid");
  while(read_inflight)begin @(negedge clk);if(out_valid)$fatal(1,"output during drain");end
  if(!saw_error||active)$fatal(1,"revocation not reported");owned=1;run_length(17);
  // An unsolicited beat faults closed until reset.
  @(negedge clk);inject=1;@(negedge clk);inject=0;if(!faulted)$fatal(1,"unexpected response not faulted");
  granted_length=1;start=1;@(negedge clk);start=0;if(start_accept||!error)$fatal(1,"faulted reader restarted");
  $display("SDRAM_READER_PASS lengths=14 max_bytes=262144 tail_strobes=1,2,3,4 revoke_drain=1 unsolicited_fault=1");$finish;
 end
 initial begin #30000000;$fatal(1,"watchdog");end
endmodule
