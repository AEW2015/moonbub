`timescale 1ns/1ps
`default_nettype none
module tb_controller #(parameter real T_AC_NS=2.0,parameter integer TILED=0);
 logic clk=0;initial forever #5 clk=!clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 logic power_on_reset=1,reset=0,cancel=0;
 logic req_valid=0,rsp_ready=0;wire req_ready,rsp_valid,rsp_error;
 logic [31:0] req_epoch=1,req_token=1;logic [1:0]req_bank=0;logic[19:0]req_addr=0;logic[63:0]req_data=0;
 wire[31:0]rsp_epoch,rsp_token;wire[1:0]rsp_bank;wire[19:0]rsp_addr;
 wire b_valid,b_ready,b_idle,b_write,busy,word_pending,drained;wire[23:0]b_addr;wire[15:0]b_data;wire[2:0]state,word_index;
 wire[31:0]count_rows,count_words_accepted,count_words_retired,count_responses,count_cancels,count_invalid;
 logic raw_mode=0,raw_valid=0,raw_write=0,hold_word=0;logic[23:0]raw_addr=0;logic[15:0]raw_data=0;
 wire c_ready,c_idle,c_read_valid;wire[15:0]c_read_data;
 wire c_valid=raw_mode?raw_valid:(b_valid&&!hold_word);wire c_write=raw_mode?raw_write:b_write;
 wire[23:0]c_addr=raw_mode?raw_addr:b_addr;wire[15:0]c_data=raw_mode?raw_data:b_data;
 assign b_ready=!raw_mode&&!hold_word&&c_ready;assign b_idle=c_idle;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,ldqm,udqm;
 logic[23:0]peek_addr=0;wire[15:0]peek_data;
 integer writes,readwords,refreshes,mrs,activates,precharges;
 integer cycle=0,checks=0,logical_acks=0,controller_accepts=0,controller_retires=0,read_responses=0;
 logic controller_pending=0,controller_saw_busy=0;
 integer owners=0;
 logic owner_write[0:3];logic[23:0]owner_addr[0:3];logic[15:0]owner_data[0:3];
 integer seed=0;logic[31:0]prng=1;
 string native_file;integer native_count=0,native_fd,native_scan;logic[159:0]native_row;
 row_to_sdram bridge(.*,.ctrl_valid(b_valid),.ctrl_ready(b_ready),.ctrl_idle(b_idle),.ctrl_write(b_write),.ctrl_addr(b_addr),.ctrl_data(b_data));
 moonshine_sdram #(.POWERUP_CYCLES(30),.REFRESH_CYCLES(750)) controller(.clk(clk),.read_clk(read_clk),.reset(power_on_reset),
 .request_valid(c_valid),.request_ready(c_ready),.request_write(c_write),.request_address(c_addr),.request_data(c_data),
 .response_valid(c_read_valid),.response_data(c_read_data),.idle(c_idle),.sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(ldqm),.sdram_udqm(udqm));
 sdram_pin_model #(.T_AC_NS(T_AC_NS)) memory(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(ldqm),.udqm(udqm),.dq(dq),.peek_addr(peek_addr),.peek_data(peek_data),.*);
 function automatic logic[19:0]mapped(input logic[19:0]logical_byte);
  integer unsigned base,width,offset,y,x;
  if(TILED==0||logical_byte>=20'd518400)return logical_byte;
  if(logical_byte<20'd345600)begin base=0;width=720;end
  else if(logical_byte<20'd432000)begin base=345600;width=360;end
  else begin base=432000;width=360;end
  offset=32'(logical_byte)-base;y=offset/width;x=offset%width;
  return 20'(base+((y/8)*(width/8)+x/8)*64+(y%8)*8+x%8);
 endfunction
 function automatic logic[23:0]physical(input logic[1:0]bank,input logic[19:0]addr);
  logic[19:0]location;
  assert(addr[0]==0)else $fatal(1,"odd physical word address");
  location=mapped(addr);assert(location[0]==0)else $fatal(1,"mapped odd word address");return {bank,3'b000,location[19:1]};
 endfunction
 function automatic logic[31:0]random32();prng=prng*32'd1664525+32'd1013904223;return prng;endfunction
 task automatic pass(input string name);checks=checks+1;$display("{\"type\":\"check\",\"name\":\"%s\",\"status\":\"PASS\"}",name);endtask
 initial forever begin
  @(posedge clk);
  cycle=cycle+1;
  if(cycle>20000000)$fatal(1,"clock watchdog");
  if(!power_on_reset)begin
   if(controller_pending&&!c_idle)controller_saw_busy=1;
   if(controller_pending&&controller_saw_busy&&c_idle)begin
    for(integer k=0;k<owners;k=k+1)begin
     $display("{\"type\":\"controller_done\",\"cycle\":%0d,\"time_ps\":%0d,\"write\":%0d,\"address\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),owner_write[k],owner_addr[k],owner_data[k]);
     controller_retires=controller_retires+1;
    end
    controller_pending=0;owners=0;
   end
   if(c_valid&&c_ready)begin
    assert(owners<4)else $fatal(1,"controller bounded owner credit overflow");
    owner_write[owners]=c_write;owner_addr[owners]=c_addr;owner_data[owners]=c_data;owners=owners+1;
    if(!controller_pending)controller_saw_busy=0;controller_pending=1;controller_accepts=controller_accepts+1;
    $display("{\"type\":\"controller_req\",\"cycle\":%0d,\"time_ps\":%0d,\"write\":%0d,\"address\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),c_write,c_addr,c_data);
   end
   if(c_read_valid)begin read_responses=read_responses+1;$display("{\"type\":\"controller_read\",\"cycle\":%0d,\"time_ps\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),c_read_data);end
   if(req_valid&&req_ready)$display("{\"type\":\"bridge_req\",\"cycle\":%0d,\"time_ps\":%0d,\"epoch\":%0d,\"token\":%0d,\"bank\":%0d,\"address\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),req_epoch,req_token,req_bank,req_addr,req_data);
   if(rsp_valid)$display("{\"type\":\"bridge_offer\",\"cycle\":%0d,\"time_ps\":%0d,\"epoch\":%0d,\"token\":%0d,\"bank\":%0d,\"address\":%0d,\"error\":%0d,\"ready\":%0d}",cycle,longint'($realtime*1000.0),rsp_epoch,rsp_token,rsp_bank,rsp_addr,rsp_error,rsp_ready);
   if(rsp_valid&&rsp_ready)begin logical_acks=logical_acks+1;$display("{\"type\":\"bridge_rsp\",\"cycle\":%0d,\"time_ps\":%0d,\"epoch\":%0d,\"token\":%0d,\"bank\":%0d,\"address\":%0d,\"error\":%0d}",cycle,longint'($realtime*1000.0),rsp_epoch,rsp_token,rsp_bank,rsp_addr,rsp_error);end
   if(reset||cancel)$display("{\"type\":\"kill\",\"cycle\":%0d,\"time_ps\":%0d,\"reset\":%0d,\"cancel\":%0d,\"word_pending\":%0d,\"state\":%0d,\"word_index\":%0d}",cycle,longint'($realtime*1000.0),reset,cancel,word_pending,state,word_index);
  end
 end
 task automatic request_row(input logic[1:0]bank,input logic[19:0]addr,input logic[63:0]data);
  begin
   @(negedge clk);req_bank=bank;req_addr=addr;req_data=data;req_token=req_token+1;req_epoch=req_epoch+1;req_valid=1;
   while(!req_ready)@(negedge clk);
   @(negedge clk);req_valid=0;
  end
 endtask
 task automatic consume_response(input bit error_expected);
  begin
   while(!rsp_valid)@(negedge clk);
   assert(rsp_epoch==req_epoch&&rsp_token==req_token&&rsp_bank==req_bank&&rsp_addr==req_addr&&rsp_error==error_expected&&!word_pending)else $fatal(1,"row response identity/error/drain");
   rsp_ready=1;@(negedge clk);rsp_ready=0;assert(drained)else $fatal(1,"logical owner not released");
  end
 endtask
 task automatic verify_row(input logic[1:0]bank,input logic[19:0]addr,input logic[63:0]data);
  begin for(integer j=0;j<4;j=j+1)begin peek_addr=physical(bank,addr)+24'(j);#1;assert(peek_data==data[j*16+:16])else $fatal(1,"physical row data %x %x",peek_data,data[j*16+:16]);end end
 endtask
 task automatic write_row(input logic[1:0]bank,input logic[19:0]addr,input logic[63:0]data);
  integer before_words;
  begin before_words=writes;request_row(bank,addr,data);consume_response(0);assert(writes-before_words==4)else $fatal(1,"not four physical writes");verify_row(bank,addr,data);end
 endtask
 task automatic raw_request(input bit write,input logic[23:0]addr,input logic[15:0]data);
  begin
   assert(drained)else $fatal(1,"raw probe overlaps row owner");raw_mode=1;@(negedge clk);raw_valid=1;raw_write=write;raw_addr=addr;raw_data=data;
   while(!c_ready)@(negedge clk);
   @(negedge clk);raw_valid=0;
  end
 endtask
 task automatic raw_write_word(input logic[23:0]addr,input logic[15:0]data);
  begin raw_request(1,addr,data);while(!c_idle)@(negedge clk);@(negedge clk);raw_mode=0;end
 endtask
 task automatic raw_read8(input logic[23:0]addr,input logic[15:0]base);
  integer n;
  begin raw_request(0,addr,0);n=0;
   while(n<8)begin @(negedge clk);if(c_read_valid)begin assert(c_read_data==16'(base+16'(n)))else $fatal(1,"read mismatch %x beat%0d got%x expected%x",addr,n,c_read_data,16'(base+16'(n)));n=n+1;end end
   @(negedge clk);raw_mode=0;
  end
 endtask
 task automatic canceled_row(input bit warm_reset,input integer target);
  integer before_words,before_accepts;logic[63:0]olddata;logic[63:0]data;logic[1:0]bank;logic[19:0]addr;logic[31:0]old_epoch,old_token;
  begin
   bank=target<0?2'd0:2'(target%3);addr=target<0?20'd16384:20'(8192+target*1024);data=64'h76543210fedcba98^64'(target);before_words=writes;before_accepts=int'(count_words_accepted);
   for(integer j=0;j<4;j=j+1)begin peek_addr=physical(bank,addr)+24'(j);#1;olddata[j*16+:16]=peek_data;end
   request_row(bank,addr,data);
   if(target<0)begin hold_word=1;end
   else while(int'(count_words_accepted)-before_accepts!=target+1)@(negedge clk);
   reset=warm_reset;cancel=!warm_reset;@(negedge clk);reset=0;cancel=0;hold_word=0;
   assert(!req_ready)else $fatal(1,"canceled row released before reply");
   old_epoch=req_epoch;old_token=req_token;req_epoch=req_epoch^32'h80000000;req_token=req_token^32'h80000000;req_data=~data;req_valid=1;
   repeat(3)begin @(negedge clk);assert(!req_ready&&rsp_epoch==old_epoch&&rsp_token==old_token)else $fatal(1,"replacement changed owned row");end
   req_valid=0;req_epoch=old_epoch;req_token=old_token;req_data=data;consume_response(1);
   assert(writes-before_words==(target<0?0:target+1))else $fatal(1,"cancellation word count");
   for(integer j=0;j<4;j=j+1)begin peek_addr=physical(bank,addr)+24'(j);#1;assert(peek_data==(j<=target?data[j*16+:16]:olddata[j*16+:16]))else $fatal(1,"cancel partial side effects");end
   pass($sformatf("%s_after_word_%0d",warm_reset?"reset":"cancel",target));
  end
 endtask
 task automatic stalled_prefix_cancel();
  integer accepted_before,written_before;
  begin
   accepted_before=int'(count_words_accepted);written_before=writes;
   request_row(0,20'd49152,64'hbadc0ffee0ddf00d);
   while(int'(count_words_accepted)==accepted_before)@(negedge clk);
   hold_word=1;
   while(!c_idle)@(negedge clk);
   repeat(4)@(negedge clk);
   cancel=1;@(negedge clk);cancel=0;hold_word=0;
   consume_response(1);
   assert(writes-written_before==1)else $fatal(1,"stalled cancel prefix not retained exactly");
   pass("cancel_after_prefix_already_physically_drained");
  end
 endtask
 task automatic ready_qualifiers();
  begin
   raw_request(1,24'h1800,16'h8a51);
   while(controller.state!=8)@(negedge clk);
   assert(!c_idle)else $fatal(1,"accepted raw word did not start");
   raw_write=0;#1;assert(!c_ready)else $fatal(1,"read accepted behind write");
   raw_write=1;raw_addr=24'h400000;#1;assert(!c_ready)else $fatal(1,"bank change accepted behind write");
   raw_addr=24'h1a00;#1;assert(!c_ready)else $fatal(1,"row change accepted behind write");
   while(!c_idle)@(negedge clk);@(negedge clk);raw_mode=0;
   pass("write_follow_refuses_read_bank_and_row_changes");
  end
 endtask
 task automatic refresh_boundary();
  integer accepted,n,blocked;logic[23:0]addr;
  begin
   raw_write_word(24'h2800,16'h1100);raw_mode=1;raw_write=1;raw_addr=24'h2801;raw_data=16'h1101;
   while(controller.refresh_count<748)@(negedge clk);
   raw_valid=1;accepted=0;blocked=0;
   while(accepted<4)begin
    if(c_ready)begin
     addr=raw_addr;@(negedge clk);accepted=accepted+1;raw_addr=addr+1'b1;raw_data=raw_data+1'b1;
    end else begin
     if(controller.refresh_count>=750)begin assert(!c_ready)else $fatal(1,"accepted at refresh budget");blocked=blocked+1;end
     @(negedge clk);
    end
   end
   raw_valid=0;while(!c_idle)@(negedge clk);@(negedge clk);raw_mode=0;
   for(n=0;n<5;n=n+1)begin peek_addr=24'h2800+24'(n);#1;assert(peek_data==16'h1100+16'(n))else $fatal(1,"refresh boundary payload lost");end
   assert(blocked>0)else $fatal(1,"refresh boundary never backpressured");
   pass("refresh_budget_blocks_follow_writes_and_recovers");
  end
 endtask
 task automatic held_response(input bit warm_reset,input bit expected_error);
  logic[95:0]identity;
  begin
   request_row(1,20'd32768,64'h0123456789abcdef);hold_word=expected_error;
   if(expected_error)begin cancel=1;@(negedge clk);cancel=0;hold_word=0;end
   while(!rsp_valid)@(negedge clk);
   identity={rsp_epoch,rsp_token,rsp_bank,rsp_addr,10'd0};
   reset=warm_reset;cancel=!warm_reset;
   repeat(5)begin @(negedge clk);assert(rsp_valid&&rsp_error==expected_error&&!word_pending&&identity=={rsp_epoch,rsp_token,rsp_bank,rsp_addr,10'd0})else $fatal(1,"held response changed on warm kill");end
   reset=0;cancel=0;consume_response(expected_error);
   if(warm_reset)begin
    if(expected_error)pass("reset_held_error_response_stable");else pass("reset_held_success_response_stable");
   end else begin
    if(expected_error)pass("cancel_held_error_response_stable");else pass("cancel_held_success_response_stable");
   end
  end
 endtask
 initial begin
  if(!$value$plusargs("SEED=%d",seed))seed=912301;prng=32'(seed);
  $display("{\"type\":\"config\",\"seed\":%0d,\"t_ac_ns\":%0.3f,\"clock_flight_ns\":4.000,\"read_phase_ns\":7.750,\"initial_memory\":\"(word_address & 65535) ^ 23100\",\"row_bytes\":8,\"bank_mapping\":\"(bank<<22)|(physical_byte>>1)\",\"layout\":\"%s\"}",seed,T_AC_NS,TILED!=0?"tile8x8":"raster");
  repeat(4)@(negedge clk);power_on_reset=0;while(!c_ready)@(negedge clk);
  for(integer b=0;b<4;b=b+1)begin
   for(integer j=0;j<8;j=j+1)raw_write_word(24'(b)*24'h400000+24'h100+24'(j),16'ha000+16'(b*16+j));
   raw_read8(24'(b)*24'h400000+24'h100,16'ha000+16'(b*16));
  end
  pass("four_bank_single_writes_and_exact_bl8_reads");
  begin
   logic[19:0]addresses[0:11];
   addresses[0]=0;addresses[1]=8;addresses[2]=712;addresses[3]=720;
   addresses[4]=345592;addresses[5]=345600;addresses[6]=345952;addresses[7]=345960;
   addresses[8]=431992;addresses[9]=432000;addresses[10]=518392;addresses[11]=518400;
   for(integer k=0;k<12;k=k+1)begin
    write_row(2'(k%3),addresses[k],64'h5a3c000102030405^64'(k));
    for(integer j=0;j<8;j=j+1)assert(mapped(addresses[k]+20'(j))==mapped(addresses[k])+20'(j))else $fatal(1,"mapped row not contiguous");
   end
   pass("plane_tile_chroma_and_hud_mapping_edges");
  end
  if(TILED!=0)begin
   write_row(0,0,64'ha103a102a101a100);
   write_row(0,720,64'ha107a106a105a104);
  end else begin
   write_row(0,0,64'ha103a102a101a100);
   write_row(0,8,64'ha107a106a105a104);
  end
  raw_read8(physical(0,0),16'ha100);pass("mapped_adjacent_physical_tile_rows_exact_bl8");
  write_row(0,0,64'h1020304050607080);write_row(0,8,64'h1122334455667788);pass("row_hit_exact_four_word_writes");
  write_row(0,1024,64'habcdef0198765432);write_row(0,0,64'hfaceb00cdeadbeef);pass("row_miss_precharge_activate");
  for(integer b=0;b<3;b=b+1)write_row(2'(b),560632,64'h0011223344556677+64'(b));pass("three_candidate_bank_aperture_edges");
  for(integer r=0;r<64;r=r+1)begin
   logic[1:0]bank;logic[19:0]addr;logic[63:0]data;bank=2'(random32()%3);addr=20'((random32()%70080)*8);data={random32(),random32()};write_row(bank,addr,data);
  end
  pass("seeded_distinct_row_payloads");
  repeat(1600)@(negedge clk);assert(refreshes>=4&&mrs==1)else $fatal(1,"missing refresh/init");write_row(2,2048,64'hfedcba9876543210);pass("periodic_refresh_and_post_refresh_row");
  for(integer r=0;r<2;r=r+1)for(integer target=-1;target<4;target=target+1)canceled_row(1'(r),target);
  held_response(0,0);held_response(1,0);held_response(0,1);held_response(1,1);
  stalled_prefix_cancel();ready_qualifiers();refresh_boundary();
  begin
   integer before_words;before_words=writes;
   @(negedge clk);req_bank=0;req_addr=0;req_epoch=0;req_token=req_token+1;req_valid=1;
   while(!req_ready)@(negedge clk);@(negedge clk);req_valid=0;consume_response(1);req_epoch=1;
   assert(writes==before_words)else $fatal(1,"zero epoch wrote");
  end
  for(integer bad=1;bad<4;bad=bad+1)begin
   integer before_words;before_words=writes;request_row(bad==1?2'd3:2'd0,bad==2?20'd1:bad==3?20'd560640:20'd0,64'h9999);
   consume_response(1);assert(writes==before_words)else $fatal(1,"invalid row wrote");
  end
  pass("invalid_bank_alignment_and_aperture_reject");
  write_row(0,4096,64'h99aabbccddeeff00);pass("clean_retry_after_cancel_and_reject");
  if($value$plusargs("NATIVE_ROWS=%s",native_file))begin
   $display("{\"type\":\"native_begin\",\"cycle\":%0d,\"time_ps\":%0d}",cycle,longint'($realtime*1000.0));
   assert($value$plusargs("NATIVE_COUNT=%d",native_count)&&native_count>0)else $fatal(1,"native count");
   native_fd=$fopen(native_file,"r");assert(native_fd!=0)else $fatal(1,"native file");
   for(integer n=0;n<native_count;n=n+1)begin
    native_scan=$fscanf(native_fd,"%h\n",native_row);assert(native_row[159:150]==0&&native_scan==1)else $fatal(1,"native fixture short");
    @(negedge clk);req_data=native_row[63:0];req_addr=native_row[83:64];req_bank=native_row[85:84];req_token=native_row[117:86];req_epoch=native_row[149:118];req_valid=1;
    while(!req_ready)@(negedge clk);@(negedge clk);req_valid=0;consume_response(0);
   end
   $fclose(native_fd);$display("{\"type\":\"native_end\",\"cycle\":%0d,\"time_ps\":%0d,\"rows\":%0d}",cycle,longint'($realtime*1000.0),native_count);pass("actual_native_candidate_traffic_replayed");
  end
  repeat(3)@(negedge clk);assert(!controller_pending&&drained&&!busy&&count_words_accepted==count_words_retired&&controller_accepts==controller_retires&&count_responses==32'(logical_acks)&&count_invalid==4&&count_cancels>=10&&readwords==read_responses)else $fatal(1,"final ownership drain");
  $display("{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":%0d,\"t_ac_ns\":%0.3f,\"checks\":%0d,\"rows\":%0d,\"logical_responses\":%0d,\"word_writes\":%0d,\"read_words\":%0d,\"controller_accepts\":%0d,\"controller_retires\":%0d,\"refreshes\":%0d,\"activates\":%0d,\"precharges\":%0d,\"cycles\":%0d,\"native_rows\":%0d}",seed,T_AC_NS,checks,count_rows,logical_acks,writes,read_responses,controller_accepts,controller_retires,refreshes,activates,precharges,cycle,native_count);
  $finish;
 end
 initial begin #200000000;$fatal(1,"time watchdog");end
endmodule
`default_nettype wire
