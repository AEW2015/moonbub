`timescale 1ns/1ps
`default_nettype none
module tb_materialize #(parameter real T_AC_NS=2.0,parameter integer GEN_LANES=4);
 logic clk=0;
 logic power_on_reset /* verilator public_flat_rw */;
 logic wr_reset /* verilator public_flat_rw */;
 logic wr_cancel /* verilator public_flat_rw */;
 logic wr_req_valid /* verilator public_flat_rw */;
 logic wr_rsp_ready /* verilator public_flat_rw */;
 logic wr_req_ready /* verilator public_flat_rw */;
 logic wr_rsp_valid /* verilator public_flat_rw */;
 logic wr_rsp_error /* verilator public_flat_rw */;
 logic [31:0] wr_req_epoch /* verilator public_flat_rw */;
 logic [31:0] wr_req_token /* verilator public_flat_rw */;
 logic [1:0] wr_req_bank /* verilator public_flat_rw */;
 logic [19:0] wr_req_addr /* verilator public_flat_rw */;
 logic [63:0] wr_req_data /* verilator public_flat_rw */;
 logic [31:0] wr_rsp_epoch /* verilator public_flat_rw */;
 logic [31:0] wr_rsp_token /* verilator public_flat_rw */;
 logic [1:0] wr_rsp_bank /* verilator public_flat_rw */;
 logic [19:0] wr_rsp_addr /* verilator public_flat_rw */;
 logic wr_busy /* verilator public_flat_rw */;
 logic wr_pending /* verilator public_flat_rw */;
 logic [2:0] wr_state /* verilator public_flat_rw */;
 logic [2:0] wr_word_index /* verilator public_flat_rw */;
 logic [31:0] wr_rows /* verilator public_flat_rw */;
 logic [31:0] wr_words_accepted /* verilator public_flat_rw */;
 logic [31:0] wr_words_retired /* verilator public_flat_rw */;
 logic [31:0] wr_responses /* verilator public_flat_rw */;
 logic [31:0] wr_cancels /* verilator public_flat_rw */;
 logic [31:0] wr_invalid /* verilator public_flat_rw */;
 logic rd_reset /* verilator public_flat_rw */;
 logic rd_cancel /* verilator public_flat_rw */;
 logic rd_req_valid /* verilator public_flat_rw */;
 logic rd_rsp_ready /* verilator public_flat_rw */;
 logic rd_req_ready /* verilator public_flat_rw */;
 logic rd_rsp_valid /* verilator public_flat_rw */;
 logic rd_rsp_error /* verilator public_flat_rw */;
 logic [31:0] rd_req_epoch /* verilator public_flat_rw */;
 logic [31:0] rd_req_generation /* verilator public_flat_rw */;
 logic [1:0] rd_req_bank /* verilator public_flat_rw */;
 logic [18:0] rd_req_addr /* verilator public_flat_rw */;
 logic [127:0] rd_rsp_data /* verilator public_flat_rw */;
 logic [31:0] rd_rsp_epoch /* verilator public_flat_rw */;
 logic [31:0] rd_rsp_generation /* verilator public_flat_rw */;
 logic [1:0] rd_rsp_bank /* verilator public_flat_rw */;
 logic [18:0] rd_rsp_addr /* verilator public_flat_rw */;
 logic rd_busy /* verilator public_flat_rw */;
 logic rd_pending /* verilator public_flat_rw */;
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
 logic controller_valid /* verilator public_flat_rw */;
 logic controller_write /* verilator public_flat_rw */;
 logic [23:0] controller_addr /* verilator public_flat_rw */;
 logic [15:0] controller_data /* verilator public_flat_rw */;
 logic controller_ready /* verilator public_flat_rw */;
 logic controller_idle /* verilator public_flat_rw */;
 logic controller_read_valid /* verilator public_flat_rw */;
 logic [15:0] controller_read_data /* verilator public_flat_rw */;
 logic [23:0] peek_addr /* verilator public_flat_rw */;
 logic [15:0] peek_data /* verilator public_flat_rw */;
 integer writes /* verilator public_flat_rw */;
 integer readwords /* verilator public_flat_rw */;
 integer refreshes /* verilator public_flat_rw */;
 integer mrs /* verilator public_flat_rw */;
 integer activates /* verilator public_flat_rw */;
 integer precharges /* verilator public_flat_rw */;
 shared_sdram_timed #(.T_AC_NS(T_AC_NS),.REFRESH_CYCLES(80)) physical(.*);
 logic reset=0,cancel=0,accepted_valid=1;
 logic [1:0] accepted_bank=1;
 logic [63:0] accepted_id=64'h1234567800000001;
 logic [2:0] protected_mask=3'b010;
 logic req_valid=0,req_ready,rsp_valid,rsp_ready=0,rsp_error,candidate_valid,busy,physical_pending;
 logic [3:0] state;
 logic [2:0] lease_mask;
 logic [1:0] req_mode=0,req_src_bank=1,req_dst_bank=2;
 logic [31:0] req_epoch=100,rsp_epoch;
 logic [63:0] req_src_id=64'h1234567800000001,req_dst_id=64'habcdef1200000001,rsp_src_id,rsp_dst_id;
 logic [18:0] req_src_addr=0,req_dst_addr=0;
 logic literal_valid=0,literal_ready;logic [7:0] literal_data=0;
 logic e_wr_req_valid,e_wr_req_ready,e_wr_rsp_ready;
 logic [31:0] e_wr_req_epoch,e_wr_req_token;
 logic [1:0] e_wr_req_bank;
 logic [19:0] e_wr_req_addr;
 logic [63:0] e_wr_req_data;
 logic e_rd_req_valid,e_rd_req_ready,e_rd_rsp_ready;
 logic seed_mode=0,seed_valid=0;
 logic [19:0] seed_addr=0;
 logic [63:0] seed_data=0;
 logic read_gate=1,write_gate=1,response_gate=1,wrong_read_tag=0,wrong_write_tag=0;
 logic [31:0] e_rd_rsp_epoch,e_wr_rsp_epoch;
 assign wr_reset=0;assign wr_cancel=0;assign rd_reset=0;assign rd_cancel=0;
 assign wr_req_valid=seed_mode?seed_valid:e_wr_req_valid&&write_gate;
 assign wr_req_epoch=seed_mode?32'd50:e_wr_req_epoch;
 assign wr_req_token=seed_mode?32'd1:e_wr_req_token;
 assign wr_req_bank=seed_mode?2'd1:e_wr_req_bank;
 assign wr_req_addr=seed_mode?seed_addr:e_wr_req_addr;
 assign wr_req_data=seed_mode?seed_data:e_wr_req_data;
 assign wr_rsp_ready=seed_mode?1'b1:e_wr_rsp_ready&&response_gate;
 assign e_wr_req_ready=wr_req_ready&&write_gate&&!seed_mode;
 assign e_rd_req_ready=rd_req_ready&&read_gate;
 assign rd_req_valid=e_rd_req_valid&&read_gate;
 assign rd_rsp_ready=e_rd_rsp_ready&&response_gate;
 assign e_rd_rsp_epoch=rd_rsp_epoch^{31'd0,wrong_read_tag};
 assign e_wr_rsp_epoch=wr_rsp_epoch^{31'd0,wrong_write_tag};
 tile_materializer #(.GEN_LANES(GEN_LANES)) dut(
 .clk(clk),.power_on_reset(power_on_reset),.reset(reset),.cancel(cancel),
 .accepted_valid(accepted_valid),.accepted_bank(accepted_bank),.accepted_id(accepted_id),.protected_mask(protected_mask),
 .req_valid(req_valid),.req_ready(req_ready),.req_mode(req_mode),.req_epoch(req_epoch),
 .req_src_id(req_src_id),.req_dst_id(req_dst_id),.req_src_bank(req_src_bank),.req_dst_bank(req_dst_bank),
 .req_src_addr(req_src_addr),.req_dst_addr(req_dst_addr),
 .literal_valid(literal_valid),.literal_ready(literal_ready),.literal_data(literal_data),
 .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_error(rsp_error),.candidate_valid(candidate_valid),
 .rsp_epoch(rsp_epoch),.rsp_src_id(rsp_src_id),.rsp_dst_id(rsp_dst_id),
 .busy(busy),.physical_pending(physical_pending),.state(state),.lease_mask(lease_mask),
 .rd_req_valid(e_rd_req_valid),.rd_req_ready(e_rd_req_ready),.rd_req_epoch(rd_req_epoch),
 .rd_req_generation(rd_req_generation),.rd_req_bank(rd_req_bank),.rd_req_addr(rd_req_addr),
 .rd_rsp_valid(rd_rsp_valid&&response_gate),.rd_rsp_ready(e_rd_rsp_ready),.rd_rsp_error(rd_rsp_error),
 .rd_rsp_epoch(e_rd_rsp_epoch),.rd_rsp_generation(rd_rsp_generation),.rd_rsp_bank(rd_rsp_bank),.rd_rsp_addr(rd_rsp_addr),.rd_rsp_data(rd_rsp_data),
 .wr_req_valid(e_wr_req_valid),.wr_req_ready(e_wr_req_ready),.wr_req_epoch(e_wr_req_epoch),
 .wr_req_token(e_wr_req_token),.wr_req_bank(e_wr_req_bank),.wr_req_addr(e_wr_req_addr),.wr_req_data(e_wr_req_data),
 .wr_rsp_valid(wr_rsp_valid&&response_gate&&!seed_mode),.wr_rsp_ready(e_wr_rsp_ready),.wr_rsp_error(wr_rsp_error),
 .wr_rsp_epoch(e_wr_rsp_epoch),.wr_rsp_token(wr_rsp_token),.wr_rsp_bank(wr_rsp_bank),.wr_rsp_addr(wr_rsp_addr));
 initial forever #5 clk=~clk;
 integer checks=0,cycle=0,descriptors=0,read_lines=0,write_rows=0,generator_cycles=0;
 always @(posedge clk)begin
  cycle<=cycle+1;
  if(!power_on_reset)begin
   if(req_valid&&req_ready)descriptors<=descriptors+1;
   if(rd_req_valid&&rd_req_ready)read_lines<=read_lines+1;
   if(wr_req_valid&&wr_req_ready&&!seed_mode)write_rows<=write_rows+1;
   if(state==1)generator_cycles<=generator_cycles+1;
  end
 end
 task automatic step(input integer n=1);repeat(n)@(negedge clk);endtask
 task automatic check(input bit ok,input string label_text);
  assert(ok)else $fatal(1,"FAILED %s cycle=%0d state=%0d",label_text,cycle,state);
  checks++;$display("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%s\"}",label_text);
 endtask
 function automatic logic[7:0] pattern(input integer address);return 8'((address*13+(address>>8)+71)%256);endfunction
 function automatic logic [19:0] raster(input integer address,input integer row);
  integer p,w,t;p=address<345600?0:address<432000?345600:432000;w=address<345600?720:360;t=(address-p)/64;
  return 20'(p+((t/(w/8))*8+row)*w+(t%(w/8))*8);
 endfunction
 task automatic seed_tile(input integer address);
  seed_mode=1;
  for(integer row=0;row<8;row++)begin
   seed_addr=raster(address,row);
   for(integer b=0;b<8;b++)seed_data[b*8+:8]=pattern(address+row*8+b);
   seed_valid=1;do @(posedge clk);while(!wr_req_ready);@(negedge clk);seed_valid=0;
   while(!wr_rsp_valid)step();check(!wr_rsp_error,"physical_seed_ack");step();
  end
  while(wr_busy||source_owner!=0)step();seed_mode=0;
 endtask
 task automatic request(input logic[1:0] mode,input integer src,input integer dst);
  assert(src>=0&&src<524288&&dst>=0&&dst<524288)else $fatal(1,"test stimulus address width");
  req_mode=mode;req_src_addr=19'(src);req_dst_addr=19'(dst);req_epoch++;req_valid=1;
  do @(posedge clk);while(!req_ready);@(negedge clk);req_valid=0;
 endtask
 task automatic finish(input bit error_expected);
  logic [31:0] saved_epoch;logic [63:0] saved_src,saved_dst;logic [2:0] saved_lease;
  while(!rsp_valid)step();
  check(rsp_error==error_expected&&candidate_valid==!error_expected&&!physical_pending&&busy,"completion_validity_and_drain");
  check(rsp_epoch==req_epoch&&rsp_src_id==req_src_id&&rsp_dst_id==req_dst_id,"full_64bit_descriptor_identity");
  saved_epoch=rsp_epoch;saved_src=rsp_src_id;saved_dst=rsp_dst_id;saved_lease=lease_mask;
  reset=1;cancel=1;step(4);reset=0;cancel=0;
  check(rsp_valid&&rsp_epoch==saved_epoch&&rsp_src_id==saved_src&&rsp_dst_id==saved_dst&&lease_mask==saved_lease&&candidate_valid==!error_expected,"held_completion_immutable_through_reset");
  rsp_ready=1;step();rsp_ready=0;check(!busy&&lease_mask==0,"lease_release_only_after_completion_ack");
  while(source_owner!=0)step();
 endtask
 task automatic verify_tile(input integer dst,input integer src,input bit constant_pixels);
  for(integer word_index=0;word_index<32;word_index++)begin
   peek_addr=(24'(req_dst_bank)<<22)+24'((dst/2)+word_index);#1;
   check(peek_data==(constant_pixels?16'h8080:{pattern(src+word_index*2+1),pattern(src+word_index*2)}),"actual_pin_word_oracle");
  end
 endtask
 task automatic metric(input string name,input integer start_cycle,input integer start_reads,input integer start_writes,input integer start_gen);
  $display("{\"type\":\"metric\",\"name\":\"%s\",\"cycles\":%0d,\"read_lines\":%0d,\"write_rows\":%0d,\"generator_cycles\":%0d,\"descriptors\":1,\"gen_lanes\":%0d}",name,cycle-start_cycle,read_lines-start_reads,write_rows-start_writes,generator_cycles-start_gen,GEN_LANES);
 endtask
 integer sc,sr,sw,sg,oldwrites,oldreads;
 initial begin
  power_on_reset=1;peek_addr=0;step(4);power_on_reset=0;
  seed_tile(0);seed_tile(345600);seed_tile(432000);seed_tile(518336);
  for(integer mode=0;mode<3;mode++)begin
   sc=cycle;sr=read_lines;sw=write_rows;sg=generator_cycles;
   request(2'(mode),0,64);
   if(mode==2)begin
    for(integer b=0;b<64;b++)begin
     literal_valid=1;literal_data=pattern(b);do @(posedge clk);while(!literal_ready);@(negedge clk);literal_valid=0;
     if(b%7==0)step(2);
    end
   end
   finish(0);metric(mode==0?"copy":mode==1?"const128":"literal",sc,sr,sw,sg);
   check(read_lines-sr==(mode==0?4:0)&&write_rows-sw==8,"exact_real_transaction_counts");
   check(generator_cycles-sg==(mode==1?64/GEN_LANES:0),"explicit_generator_schedule");
   verify_tile(64,0,mode==1);
  end
  for(integer edge_case=0;edge_case<3;edge_case++)begin
   request(0,edge_case==0?345600:edge_case==1?432000:518336,edge_case==0?345664:edge_case==1?432064:518336);
   finish(0);verify_tile(edge_case==0?345664:edge_case==1?432064:518336,edge_case==0?345600:edge_case==1?432000:518336,0);
  end
  // Invalid descriptors must fail before any service/controller/pin traffic.
  for(integer invalid=0;invalid<11;invalid++)begin
   oldwrites=writes;oldreads=readwords;sr=read_lines;sw=write_rows;
   case(invalid)
    0:req_dst_bank=3;
    1:protected_mask=3'b110;
    2:req_src_id=64'hffffffff00000001;
    3:req_dst_id=accepted_id;
    4:req_src_bank=2;
    5:accepted_valid=0;
    6:req_dst_bank=1;
    7:req_src_id=0;
    8:req_mode=3;
    9:req_dst_id=0;
    default:begin end
   endcase
   request(invalid==8?2'd3:2'd0,invalid==10?518400:0,invalid==10?65:64);finish(1);
   check(writes==oldwrites&&readwords==oldreads&&read_lines==sr&&write_rows==sw,"invalid_rejected_before_first_traffic");
   req_dst_bank=2;protected_mask=3'b010;req_src_id=accepted_id;req_dst_id=64'habcdef1200000001;req_src_bank=1;accepted_valid=1;
  end
  // A wrong epoch cannot release the matching line lease or advance the buffer.
  request(0,0,128);while(!rd_rsp_valid)step();wrong_read_tag=1;step(5);
  check(physical_pending&&!rd_rsp_ready&&!rsp_valid&&lease_mask==3'b110,"wrong_read_ack_not_consumed");
  wrong_read_tag=0;finish(0);verify_tile(128,0,0);
  request(1,0,192);while(!wr_rsp_valid)step();wrong_write_tag=1;step(5);
  check(physical_pending&&!wr_rsp_ready&&!rsp_valid,"wrong_write_ack_not_consumed");wrong_write_tag=0;finish(0);verify_tile(192,0,1);
  // Cancel/reset every in-flight source line and destination row. Stop further
  // offers, drain accepted service response, invalidate candidate, then retry.
  for(integer kind=0;kind<2;kind++)begin
   for(integer line=0;line<4;line++)begin
    sr=read_lines;sw=write_rows;request(0,0,256);
    while(!(physical_pending&&state==4&&read_lines-sr==line+1))step();
    response_gate=0;reset=kind==0;cancel=kind==1;step(3);reset=0;cancel=0;
    check(busy&&physical_pending&&lease_mask==3'b110&&!req_ready&&!candidate_valid,"cancel_retains_read_lease_until_ack");
    response_gate=1;finish(1);check(write_rows==sw&&read_lines-sr==line+1,"cancel_no_new_read_or_write");
   end
   for(integer row=0;row<8;row++)begin
    sw=write_rows;request(1,0,320);
    while(!(physical_pending&&state==6&&write_rows-sw==row+1))step();
    response_gate=0;reset=kind==0;cancel=kind==1;step(3);reset=0;cancel=0;
    check(busy&&physical_pending&&!req_ready&&!candidate_valid,"cancel_retains_write_lease_until_ack");
    response_gate=1;finish(1);check(write_rows-sw==row+1,"cancel_no_new_write");
   end
  end
  // Source lease identity changes invalidate before any destination writes.
  sw=write_rows;request(0,0,384);while(!physical_pending)step();accepted_id=64'hffffffff00000001;
  finish(1);check(write_rows==sw,"changed_full_64bit_source_lease_invalidates");accepted_id=64'h1234567800000001;
  // Requests held at the port retain the materialized payload and stay cancelable.
  write_gate=0;request(1,0,448);while(state!=5)step();step(5);cancel=1;step();cancel=0;write_gate=1;finish(1);
  read_gate=0;request(0,0,448);while(state!=3)step();reset=1;step();reset=0;read_gate=1;finish(1);
  request(0,0,448);finish(0);verify_tile(448,0,0);
  check(wr_invalid==0&&rd_invalid==0&&wr_cancels==0&&rd_cancels==0&&refreshes>0&&mrs==1&&writes>0&&readwords>0,"retained_physical_service_and_refresh_clean");
  $display("{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"checks\":%0d,\"descriptors\":%0d,\"read_lines\":%0d,\"write_rows\":%0d,\"pin_writes\":%0d,\"pin_reads\":%0d}",checks,descriptors,read_lines,write_rows,writes,readwords);$finish;
 end
 initial begin #10000000;$fatal(1,"watchdog state=%0d owner=%0d pending=%0d",state,source_owner,physical_pending);end
endmodule
`default_nettype wire
