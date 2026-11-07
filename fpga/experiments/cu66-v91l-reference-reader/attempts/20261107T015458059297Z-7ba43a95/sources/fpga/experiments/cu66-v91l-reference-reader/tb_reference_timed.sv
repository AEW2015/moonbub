`timescale 1ns/1ps
`default_nettype none
module tb_reference_timed #(parameter real T_AC_NS=2.0);
 logic  clk=0;
 logic  power_on_reset=0;
 logic  wr_reset=0;
 logic  wr_cancel=0;
 logic  wr_req_valid=0;
 logic  wr_rsp_ready=0;
 logic  wr_req_ready /* verilator public_flat_rw */;
 logic  wr_rsp_valid /* verilator public_flat_rw */;
 logic  wr_rsp_error /* verilator public_flat_rw */;
 logic [31:0] wr_req_epoch=0;
 logic [31:0] wr_req_token=0;
 logic [1:0] wr_req_bank=0;
 logic [19:0] wr_req_addr=0;
 logic [63:0] wr_req_data=0;
 logic [31:0] wr_rsp_epoch /* verilator public_flat_rw */;
 logic [31:0] wr_rsp_token /* verilator public_flat_rw */;
 logic [1:0] wr_rsp_bank /* verilator public_flat_rw */;
 logic [19:0] wr_rsp_addr /* verilator public_flat_rw */;
 logic  wr_busy /* verilator public_flat_rw */;
 logic  wr_pending /* verilator public_flat_rw */;
 logic [2:0] wr_state /* verilator public_flat_rw */;
 logic [2:0] wr_word_index /* verilator public_flat_rw */;
 logic [31:0] wr_rows /* verilator public_flat_rw */;
 logic [31:0] wr_words_accepted /* verilator public_flat_rw */;
 logic [31:0] wr_words_retired /* verilator public_flat_rw */;
 logic [31:0] wr_responses /* verilator public_flat_rw */;
 logic [31:0] wr_cancels /* verilator public_flat_rw */;
 logic [31:0] wr_invalid /* verilator public_flat_rw */;
 logic  rd_reset=0;
 logic  rd_cancel=0;
 logic  rd_req_valid=0;
 logic  rd_rsp_ready=0;
 logic  rd_req_ready /* verilator public_flat_rw */;
 logic  rd_rsp_valid /* verilator public_flat_rw */;
 logic  rd_rsp_error /* verilator public_flat_rw */;
 logic [31:0] rd_req_epoch=0;
 logic [31:0] rd_req_generation=0;
 logic [1:0] rd_req_bank=0;
 logic [18:0] rd_req_addr=0;
 logic [127:0] rd_rsp_data /* verilator public_flat_rw */;
 logic [31:0] rd_rsp_epoch /* verilator public_flat_rw */;
 logic [31:0] rd_rsp_generation /* verilator public_flat_rw */;
 logic [1:0] rd_rsp_bank /* verilator public_flat_rw */;
 logic [18:0] rd_rsp_addr /* verilator public_flat_rw */;
 logic  rd_busy /* verilator public_flat_rw */;
 logic  rd_pending /* verilator public_flat_rw */;
 logic [2:0] rd_state /* verilator public_flat_rw */;
 logic [3:0] rd_beats /* verilator public_flat_rw */;
 logic [31:0] rd_requests /* verilator public_flat_rw */;
 logic [31:0] rd_commands /* verilator public_flat_rw */;
 logic [31:0] rd_count_beats /* verilator public_flat_rw */;
 logic [31:0] rd_responses /* verilator public_flat_rw */;
 logic [31:0] rd_cancels /* verilator public_flat_rw */;
 logic [31:0] rd_invalid /* verilator public_flat_rw */;
 logic [1:0] source_owner /* verilator public_flat_rw */;
 logic [31:0] writer_grants /* verilator public_flat_rw */;
 logic [31:0] reader_grants /* verilator public_flat_rw */;
 logic [31:0] writer_commands /* verilator public_flat_rw */;
 logic [31:0] reader_commands /* verilator public_flat_rw */;
 logic [31:0] owner_releases /* verilator public_flat_rw */;
 logic  controller_valid /* verilator public_flat_rw */;
 logic  controller_write /* verilator public_flat_rw */;
 logic [23:0] controller_addr /* verilator public_flat_rw */;
 logic [15:0] controller_data /* verilator public_flat_rw */;
 logic  controller_ready /* verilator public_flat_rw */;
 logic  controller_idle /* verilator public_flat_rw */;
 logic  controller_read_valid /* verilator public_flat_rw */;
 logic [15:0] controller_read_data /* verilator public_flat_rw */;
 logic [23:0] peek_addr=0;
 logic [15:0] peek_data /* verilator public_flat_rw */;
 integer writes /* verilator public_flat_rw */;
 integer readwords /* verilator public_flat_rw */;
 integer refreshes /* verilator public_flat_rw */;
 integer mrs /* verilator public_flat_rw */;
 integer activates /* verilator public_flat_rw */;
 integer precharges /* verilator public_flat_rw */;
 logic  ref_reset=0;
 logic  ref_cancel=0;
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
 logic  ref_busy;
 logic  ref_pending;
 logic [2:0] ref_state;
 logic [1:0] ref_line_index;
 logic [1:0] ref_source_bank;
 logic [1:0] mux_owner;
 logic  ref_line_req_valid;
 logic  ref_line_req_ready;
 logic  ref_line_rsp_valid;
 logic  ref_line_rsp_ready;
 logic  ref_line_rsp_error;
 logic [31:0] ref_line_req_epoch;
 logic [31:0] ref_line_req_generation;
 logic [31:0] ref_line_rsp_epoch;
 logic [31:0] ref_line_rsp_generation;
 logic [1:0] ref_line_req_bank;
 logic [1:0] ref_line_rsp_bank;
 logic [18:0] ref_line_req_addr;
 logic [18:0] ref_line_rsp_addr;
 logic [127:0] ref_line_rsp_data;
 reference_shared_timed #(.T_AC_NS(T_AC_NS),.REFRESH_CYCLES(80)) dut(.*);
 initial forever #5 clk=~clk;
 integer checks=0;
 task automatic check(input bit ok,input string label_text);
  assert(ok)else $fatal(1,"timed FAILED %s",label_text);
  checks++;$display("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%s\"}",label_text);
 endtask
 task automatic step(input integer n=1);repeat(n)@(negedge clk);endtask
 function automatic logic[7:0] pattern(input integer address);return 8'((address*13+(address>>8)+71)%256);endfunction
 task automatic seed_tile(input integer address);
  integer plane_base,width,tile_number;
  plane_base=address<345600?0:address<432000?345600:432000;
  width=address<345600?720:360;tile_number=(address-plane_base)/64;
  for(integer row=0;row<8;row++)begin
   wr_req_addr=20'(plane_base+((tile_number/(width/8))*8+row)*width+(tile_number%(width/8))*8);wr_req_bank=1;wr_req_epoch=50;wr_req_token++;
   for(integer b=0;b<8;b++)wr_req_data[b*8+:8]=pattern(address+row*8+b);
   wr_req_valid=1;do @(posedge clk);while(!wr_req_ready);@(negedge clk);wr_req_valid=0;
   while(!wr_rsp_valid)step();check(!wr_rsp_error,"seed_write_ack");wr_rsp_ready=1;step();wr_rsp_ready=0;
  end
 endtask
 task automatic request(input logic[1:0] p,input logic[12:0] t);
  ref_req_plane=p;ref_req_tile=t;ref_req_epoch++;ref_req_valid=1;
  do @(posedge clk);while(!ref_req_ready);@(negedge clk);ref_req_valid=0;
 endtask
 task automatic finish(input bit expected_error,input integer address);
  logic[511:0] saved;
  while(!ref_rsp_valid)step();
  check(ref_rsp_error==expected_error&&ref_rsp_epoch==ref_req_epoch&&ref_rsp_fid==9&&ref_rsp_generation==64'h1234567800000001&&ref_source_bank==1&&ref_busy&&ref_rsp_plane==ref_req_plane&&ref_rsp_tile==ref_req_tile,"outer_physical_full_identity");
  if(!expected_error)for(integer b=0;b<64;b++)check(ref_rsp_pixels[b*8+:8]==pattern(address+b),"pin_tile_byte");
  saved=ref_rsp_pixels;accepted_valid=0;accepted_bank=2;accepted_generation=64'hffffffff00000001;ref_reset=1;step(3);ref_reset=0;
  check(ref_rsp_pixels==saved&&ref_rsp_valid&&ref_rsp_error==expected_error,"physical_outer_held_immutable");
  ref_rsp_ready=1;step();ref_rsp_ready=0;accepted_valid=1;accepted_bank=1;accepted_generation=64'h1234567800000001;
 endtask
 integer base;
 integer physical_count=0,display_count=0;
 logic [31:0] owned_epoch,owned_ticket;
 logic [1:0] owned_bank;logic [18:0] owned_addr;
 always_ff @(posedge clk)if(!power_on_reset)begin
  if(ref_line_req_valid&&ref_line_req_ready)begin
   physical_count<=physical_count+1;
   owned_epoch<=ref_line_req_epoch;owned_ticket<=ref_line_req_generation;owned_bank<=ref_line_req_bank;owned_addr<=ref_line_req_addr;
   assert(ref_line_req_epoch==ref_req_epoch&&ref_line_req_generation!=0&&ref_line_req_bank==1&&ref_line_req_addr[3:0]==0)else $fatal(1,"pin line request identity");
  end
  if(ref_line_rsp_valid&&ref_line_rsp_ready)begin
   assert(ref_line_rsp_epoch==owned_epoch&&ref_line_rsp_generation==owned_ticket&&ref_line_rsp_bank==owned_bank&&ref_line_rsp_addr==owned_addr)else $fatal(1,"pin line response identity");
   if(!ref_line_rsp_error)for(integer b=0;b<16;b++)assert(ref_line_rsp_data[b*8+:8]==pattern(int'(owned_addr)+b))else $fatal(1,"pin line byte oracle");
  end
  if(rd_req_valid&&rd_req_ready)display_count<=display_count+1;
 end

 initial begin
  power_on_reset=1;step(4);power_on_reset=0;
  accepted_valid=1;accepted_bank=1;accepted_fid=9;accepted_generation=64'h1234567800000001;
  ref_req_epoch=100;ref_req_fid=9;ref_req_generation=64'h1234567800000001;
  for(integer p=0;p<3;p++)for(integer edge_case=0;edge_case<2;edge_case++)begin
   base=(p==0?0:p==1?345600:432000)+(edge_case==0?0:p==0?5399*64:1349*64);
   seed_tile(base);request(2'(p),13'(edge_case==0?0:p==0?5399:1349));finish(0,base);
  end
  check(physical_count==24,"four_reads_per_tile");
  // Simultaneous display and reference demand, held display reply excludes reuse.
  request(0,0);rd_req_epoch=800;rd_req_generation=900;rd_req_bank=1;rd_req_addr=0;rd_req_valid=1;
  do @(posedge clk);while(!rd_req_ready);@(negedge clk);rd_req_valid=0;
  while(!rd_rsp_valid)step();
  begin
   integer old_count;logic[127:0] saved;
   old_count=physical_count;saved=rd_rsp_data;ref_cancel=1;step(5);ref_cancel=0;
   check(rd_rsp_valid&&!rd_rsp_error&&rd_rsp_data==saved&&physical_count==old_count&&mux_owner==1,"ungranted_reference_cancel_preserves_held_display");
  end
  rd_rsp_ready=1;step();rd_rsp_ready=0;finish(1,0);
  // Contention all four chunks: display offers again as soon as its last line ACK.
  request(0,0);
  for(integer k=0;k<4;k++)begin
   rd_req_epoch++;rd_req_generation++;rd_req_valid=1;
   do @(posedge clk);while(!rd_req_ready);@(negedge clk);rd_req_valid=0;
   while(!rd_rsp_valid)step();check(!rd_rsp_error,"contending_display_success");rd_rsp_ready=1;step();rd_rsp_ready=0;
  end
  finish(0,0);check(display_count==5,"all_display_lines_retired");
  for(integer kind=0;kind<2;kind++)for(integer k=0;k<4;k++)begin
   request(0,0);
   while(!(ref_pending&&ref_line_index==2'(k)))step();ref_reset=kind==0;ref_cancel=kind==1;step();ref_reset=0;ref_cancel=0;
   finish(1,0);while(rd_busy||mux_owner!=0)step();
   check(!ref_pending,"physical_cancel_drain_complete");
  end
  check(writes==48*4&&readwords>0,"unit_seed_writes_and_pin_reads");
  $display("{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"checks\":%0d}",checks);$finish;
 end
 initial begin #5000000;$fatal(1,"timed watchdog state=%d line=%d mux=%d",ref_state,ref_line_index,mux_owner);end
endmodule
`default_nettype wire
