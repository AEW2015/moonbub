`timescale 1ns/1ps
`default_nettype none
module tb_reference_unit;
 logic  clk=0;
 logic  power_on_reset=0;
 logic  reset=0;
 logic  cancel=0;
 logic  accepted_valid=0;
 logic [1:0] accepted_bank=0;
 logic [31:0] accepted_fid=0;
 logic [63:0] accepted_generation=0;
 logic  ref_req_valid=0;
 logic  ref_req_ready;
 logic [31:0] ref_req_epoch=0;
 logic [31:0] ref_req_fid=0;
 logic [63:0] ref_req_generation=0;
 logic [1:0] ref_req_plane=0;
 logic [12:0] ref_req_tile=0;
 logic  ref_rsp_valid;
 logic  ref_rsp_ready=0;
 logic [31:0] ref_rsp_epoch;
 logic [31:0] ref_rsp_fid;
 logic [63:0] ref_rsp_generation;
 logic [1:0] ref_rsp_plane;
 logic [12:0] ref_rsp_tile;
 logic [511:0] ref_rsp_pixels;
 logic  ref_rsp_error;
 logic  mem_req_valid;
 logic  mem_req_ready=0;
 logic [31:0] mem_req_epoch;
 logic [31:0] mem_req_generation;
 logic [1:0] mem_req_bank;
 logic [18:0] mem_req_addr;
 logic  mem_rsp_valid=0;
 logic  mem_rsp_ready;
 logic [31:0] mem_rsp_epoch=0;
 logic [31:0] mem_rsp_generation=0;
 logic [1:0] mem_rsp_bank=0;
 logic [18:0] mem_rsp_addr=0;
 logic [127:0] mem_rsp_data=0;
 logic  mem_rsp_error=0;
 logic  busy;
 logic  physical_pending;
 logic [2:0] state;
 logic [1:0] line_index;
 logic [1:0] source_bank;
 reference_tile_reader dut(.*);
 initial forever #5 clk=~clk;
 integer checks=0;
 task automatic step(input integer n=1);repeat(n)@(negedge clk);endtask
 task automatic check(input bit ok,input string label_text);
  assert(ok)else $fatal(1,"unit FAILED %s",label_text);
  checks++;$display("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%s\"}",label_text);
 endtask
 task automatic request(input logic[1:0] p,input logic[12:0] t);
  ref_req_plane=p;ref_req_tile=t;ref_req_epoch++;ref_req_valid=1;
  do @(posedge clk);while(!ref_req_ready);
  @(negedge clk);ref_req_valid=0;
 endtask
 function automatic logic[7:0] pattern(input integer address);return 8'((address*13+(address>>8)+71)%256);endfunction
 task automatic line(input integer expected_address,input integer wrong_field=-1);
  while(!mem_req_valid)step();
  check(mem_req_addr==19'(expected_address)&&mem_req_bank==1&&mem_req_epoch==ref_req_epoch&&mem_req_generation!=0,"line_physical_identity");
  mem_req_ready=1;step();mem_req_ready=0;
  check(physical_pending&&!ref_req_ready&&busy&&state==2&&source_bank==1&&mem_req_addr==19'(expected_address)&&line_index==2'((expected_address%64)/16),"line_owned");
  mem_rsp_epoch=ref_req_epoch;mem_rsp_generation=mem_req_generation;mem_rsp_bank=1;mem_rsp_addr=19'(expected_address);
  for(integer b=0;b<16;b++)mem_rsp_data[b*8+:8]=pattern(expected_address+b);
  mem_rsp_valid=1;
  if(wrong_field>=0)begin
   case(wrong_field)
    0:mem_rsp_epoch++;1:mem_rsp_generation++;2:mem_rsp_bank=2;3:mem_rsp_addr+=16;default:begin end
   endcase
   step(3);check(physical_pending&&!mem_rsp_ready&&!ref_req_ready,"wrong_reply_keeps_ownership");
   mem_rsp_epoch=ref_req_epoch;mem_rsp_generation=mem_req_generation;mem_rsp_bank=1;mem_rsp_addr=19'(expected_address);
  end
  #1;check(mem_rsp_ready,"matching_line_ack");step();mem_rsp_valid=0;
 endtask
 task automatic finish(input bit error_expected,input integer base);
  logic[511:0] saved;
  while(!ref_rsp_valid)step();
  check(ref_rsp_error==error_expected&&ref_rsp_epoch==ref_req_epoch&&ref_rsp_fid==ref_req_fid&&ref_rsp_generation==ref_req_generation&&ref_rsp_plane==ref_req_plane&&ref_rsp_tile==ref_req_tile,"outer_full_identity_error");
  if(!error_expected)for(integer b=0;b<64;b++)check(ref_rsp_pixels[b*8+:8]==pattern(base+b),"exact_tile_byte");
  saved=ref_rsp_pixels;accepted_valid=0;accepted_bank=2;accepted_fid++;accepted_generation++;
  reset=1;cancel=1;step(3);
  check(ref_rsp_valid&&ref_rsp_pixels==saved&&ref_rsp_error==error_expected&&!ref_req_ready,"held_reply_immutable_across_kill_lease_change");
  reset=0;cancel=0;ref_rsp_ready=1;step();ref_rsp_ready=0;
  check(ref_req_ready&&!physical_pending,"owner_reusable_after_outer_ack");
  accepted_valid=1;accepted_bank=1;accepted_fid=9;accepted_generation=64'h1234567800000001;
 endtask
 integer base;
 initial begin
  power_on_reset=1;step(3);power_on_reset=0;
  accepted_valid=1;accepted_bank=1;accepted_fid=9;accepted_generation=64'h1234567800000001;
  ref_req_epoch=100;ref_req_fid=9;ref_req_generation=64'h1234567800000001;
  for(integer p=0;p<3;p++)for(integer edge_case=0;edge_case<2;edge_case++)begin
   base=(p==0?0:p==1?345600:432000)+(edge_case==0?0:p==0?5399*64:1349*64);
   request(2'(p),13'(edge_case==0?0:p==0?5399:1349));
   for(integer k=0;k<4;k++)line(base+k*16,k);
   finish(0,base);
  end
  accepted_fid=0;ref_req_fid=0;request(0,0);for(integer k=0;k<4;k++)line(k*16);finish(0,0);ref_req_fid=9;
  // Same low32 generation must not pass an unequal high32 publication lease.
  ref_req_generation=64'h8765432100000001;request(0,0);check(!mem_req_valid,"high_generation_rejected");finish(1,0);ref_req_generation=accepted_generation;
  for(integer n=0;n<9;n++)begin
   case(n)
    0:accepted_valid=0;1:accepted_bank=3;2:ref_req_fid=10;3:ref_req_generation=0;4:accepted_fid=10;5:accepted_generation=0;default:begin end
   endcase
   request(n==6?2'd3:n==7?2'd0:2'd2,n==7?13'd5400:n==8?13'd1350:13'd0);
   check(!mem_req_valid,"invalid_no_physical_read");finish(1,0);
   ref_req_fid=9;ref_req_generation=accepted_generation;
  end
  ref_req_epoch=32'hffffffff;request(0,0);finish(1,0);
  // Reset and cancel before acceptance suppress all work.
  for(integer kind=0;kind<2;kind++)begin
   reset=kind==0;cancel=kind==1;ref_req_valid=1;step(3);check(!ref_req_ready&&!mem_req_valid,"kill_before_accept");ref_req_valid=0;reset=0;cancel=0;
   // OFFER has accepted outer lease but no physical request yet.
   request(0,0);reset=kind==0;cancel=kind==1;step();reset=0;cancel=0;check(!mem_req_valid,"kill_before_line_accept");finish(1,0);
   for(integer k=0;k<4;k++)begin
    request(0,0);
    for(integer j=0;j<k;j++)line(j*16);
    while(!mem_req_valid)step();mem_req_ready=1;step();mem_req_ready=0;
    reset=kind==0;cancel=kind==1;step();reset=0;cancel=0;
    check(physical_pending&&!ref_req_ready&&!mem_req_valid,"kill_drain_pending_line");
    mem_rsp_epoch=ref_req_epoch;mem_rsp_generation=mem_req_generation;mem_rsp_bank=1;mem_rsp_addr=19'(k*16);mem_rsp_valid=1;
    step();mem_rsp_valid=0;finish(1,0);
   end
  end
  $display("{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"checks\":%0d}",checks);$finish;
 end
 initial begin #2000000;$fatal(1,"unit watchdog");end
endmodule
`default_nettype wire
