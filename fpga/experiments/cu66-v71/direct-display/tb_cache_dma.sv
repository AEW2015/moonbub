`timescale 1ns/1ps
module tb_cache_dma;
 reg clk=0,rst=1;always #5 clk=~clk;
 reg cmd_valid=0;wire cmd_ready;
 reg[63:0]cmd_generation=0;reg[31:0]cmd_frame_id=0,cmd_cookie=0;
 reg cmd_context=0,cmd_bank=0;reg[1:0]cmd_kind=0;
 reg[23:0]cmd_source=0;reg[8:0]cmd_row=0;reg[14:0]cmd_hud_index=0;
 wire result_valid;reg result_ready=0;wire[63:0]result_generation;wire[31:0]result_frame_id,result_cookie;
 wire result_context,result_error,result_aborted;wire[7:0]result_reason;
 reg abort_valid=0;wire abort_ready;reg[63:0]abort_generation=0;reg[31:0]abort_frame_id=0;reg abort_context=0;wire abort_rejected;
 wire lcd_req_valid,lcd_req_ready;wire[23:0]lcd_req_addr;wire lcd_rsp_valid,lcd_rsp_ready;
 wire[127:0]lcd_rsp_data;wire lcd_rsp_error,lcd_abort_i;reg lcd_busy=0,lcd_aborted=0;
 wire cache_wr_valid,cache_wr_context,cache_wr_bank;wire[1:0]cache_wr_kind;wire[8:0]cache_wr_row;
 wire[63:0]cache_wr_data;wire[14:0]cache_wr_hud_index;wire[15:0]cache_wr_hud_word;wire cache_wr_error;
 wire[31:0]accepted_commands,accepted_reads,completed_commands,aborted_commands,unowned_responses;
 wire[7:0]first_fault;wire[63:0]fault_generation;wire[31:0]fault_frame_id,fault_cookie;wire[23:0]fault_source;wire busy;
 cu71_cache_dma dma(.*);
 `include "cu70_memory_map.svh"
 reg allow_requests=1,response_error=0,inject_response=0,model_valid=0,model_aborting=0;
 reg[23:0]model_address=0;reg[127:0]model_data=0;integer delay_left=0,configured_delay=6;
 assign lcd_req_ready=allow_requests&&!lcd_busy&&!model_valid;
 assign lcd_rsp_valid=model_valid||inject_response;assign lcd_rsp_data=model_data;assign lcd_rsp_error=response_error;
 function automatic[15:0]word_value(input[23:0]address);
  word_value=16'((address*24'd13)^(address>>7)^24'h005a3c);
 endfunction
 always @(posedge clk)begin
  if(rst)begin lcd_busy<=0;lcd_aborted<=0;model_valid<=0;model_aborting<=0;delay_left<=0;end
  else begin
   lcd_aborted<=0;
   if(lcd_req_valid&&lcd_req_ready)begin
    lcd_busy<=1;model_address<=lcd_req_addr;delay_left<=configured_delay;model_aborting<=0;
    for(integer j=0;j<8;j=j+1)model_data[16*j+:16]<=word_value(lcd_req_addr+24'(j));
   end
   if(lcd_busy&&lcd_abort_i)model_aborting<=1;
   if(lcd_busy&&delay_left!=0)delay_left<=delay_left-1;
   if(lcd_busy&&delay_left==0)begin
    if(model_aborting||lcd_abort_i)begin lcd_busy<=0;model_valid<=0;model_aborting<=0;lcd_aborted<=1;end
    else model_valid<=1;
   end
   if(model_valid&&lcd_rsp_ready)begin model_valid<=0;lcd_busy<=0;end
  end
 end
 reg wr_allow=1;
 reg rd_valid=0,rd_context=0;reg[9:0]rd_u=0;reg[8:0]rd_v=0;reg rd_hud_hit=0;reg[14:0]rd_hud_index=0;reg[31:0]rd_tag=0;
 wire cache_valid,cache_error;wire[31:0]cache_tag;wire[7:0]Y,cb_t0,cb_t1,cb_b0,cb_b1,cr_t0,cr_t1,cr_b0,cr_b1;
 wire xo,yo,hh;wire[15:0]hw;
 cu71_direct_cache cache(.clk,.rst,.wr_valid(cache_wr_valid),.wr_allow,.wr_context(cache_wr_context),.wr_bank(cache_wr_bank),.wr_kind(cache_wr_kind),.wr_row(cache_wr_row),.wr_data(cache_wr_data),.wr_hud_index(cache_wr_hud_index),.wr_hud_word(cache_wr_hud_word),.wr_error(cache_wr_error),
 .front_valid(1'b0),.front_context(1'b0),.render_live(1'b0),.render_context(1'b0),.render_u(10'd0),
 .rd_valid,.rd_context,.rd_u,.rd_v,.rd_hud_hit,.rd_hud_index,.rd_tag,.out_valid(cache_valid),.out_error(cache_error),.out_tag(cache_tag),.out_y(Y),
 .out_cb_t0(cb_t0),.out_cb_t1(cb_t1),.out_cb_b0(cb_b0),.out_cb_b1(cb_b1),.out_cr_t0(cr_t0),.out_cr_t1(cr_t1),.out_cr_b0(cr_b0),.out_cr_b1(cr_b1),.out_x_odd(xo),.out_y_odd(yo),.out_hud_word(hw),.out_hud_hit(hh));
 integer checks=0,commands=0,writes_seen=0,initial_reads,initial_writes;
 always @(posedge clk)if(cache_wr_valid)writes_seen=writes_seen+1;
 task automatic start(input[1:0]kind,input ctx,bank,input[8:0]row,input[14:0]hud,input[23:0]source);
  begin
   @(negedge clk);cmd_valid=1;cmd_cookie=cmd_cookie+1;cmd_generation=100+64'(cmd_cookie);cmd_frame_id=cmd_cookie;cmd_context=ctx;cmd_bank=bank;cmd_kind=kind;cmd_row=row;cmd_hud_index=hud;cmd_source=source;
   do @(posedge clk);while(!cmd_ready);
   @(negedge clk);cmd_valid=0;commands=commands+1;
  end
 endtask
 task automatic finish(input bad,aborted,input[7:0]reason);
  integer bound;reg[63:0]g;reg[31:0]f,c;
  begin
   bound=0;while(!result_valid)begin @(negedge clk);bound=bound+1;if(bound>300)$fatal(1,"DMA result watchdog");end
   if(lcd_busy||cache_wr_valid||result_generation!=cmd_generation||result_frame_id!=cmd_frame_id||result_cookie!=cmd_cookie||result_context!=cmd_context||result_error!==bad||result_aborted!==aborted||result_reason!==reason)
    $fatal(1,"DMA result identity/drain goterr%b abort%b reason%0d expected%b/%b/%0d",result_error,result_aborted,result_reason,bad,aborted,reason);
   g=result_generation;f=result_frame_id;c=result_cookie;
   repeat(3)begin @(negedge clk);if(!result_valid||result_generation!=g||result_frame_id!=f||result_cookie!=c)$fatal(1,"held result changed");end
   result_ready=1;@(posedge clk);@(negedge clk);result_ready=0;checks=checks+1;
  end
 endtask
 task automatic abort_command(input wrong);
  begin
   @(negedge clk);abort_valid=1;abort_generation=cmd_generation+(wrong?1:0);abort_frame_id=cmd_frame_id;abort_context=cmd_context;
   #1;if(abort_ready===wrong)$fatal(1,"abort identity gate");
   @(posedge clk);@(negedge clk);if(wrong&&!abort_rejected)$fatal(1,"stale abort not retained");abort_valid=0;
  end
 endtask
 task automatic readback(input[1:0]kind,input ctx,bank,input[8:0]row,input[14:0]hud,input[23:0]source);
  integer i,k;reg[7:0]a,b;
  begin
   for(i=0;i<8;i=i+1)begin
    @(negedge clk);rd_valid=1;rd_context=ctx;rd_u=kind==0?(bank?8:0)+10'(i):(bank?16:0)+10'(i*2);rd_v=kind==0?row:9'(row*2);rd_hud_hit=kind==3;rd_hud_index=hud+15'(i);
    @(posedge clk);@(negedge clk);
    if(!cache_valid||cache_error)$fatal(1,"functional cache read rejected");
    if(kind==3)begin if(hw!==word_value(source+24'(i)))$fatal(1,"HUD cache word");end
    else begin
     k=i/2;a=8'(word_value(source+24'(k))>>(8*(i%2)));b=8'(word_value(source+24'(k+4))>>(8*(i%2)));
     if(kind==0)begin if(Y!==a)$fatal(1,"Y cache first row");rd_v=row+1;@(posedge clk);@(negedge clk);if(Y!==b)$fatal(1,"Y cache second row");end
     else if(kind==1)begin if(cb_t0!==a||cb_b0!==b)$fatal(1,"Cb cache pair");end
     else if(cr_t0!==a||cr_b0!==b)$fatal(1,"Cr cache pair");
    end
    rd_valid=0;checks=checks+1;
   end
  end
 endtask
 integer kind,ctx,bank;
 initial begin
  repeat(4)@(negedge clk);rst=0;
  for(ctx=0;ctx<2;ctx=ctx+1)for(bank=0;bank<2;bank=bank+1)for(kind=0;kind<4;kind=kind+1)begin
   start(2'(kind),1'(ctx),1'(bank),kind==0?9'd478:9'd238,15'd21112,kind==3?HUD0_BASE+24'd21112:CANONICAL0_BASE+24'd128);
   finish(0,0,0);readback(2'(kind),1'(ctx),1'(bank),kind==0?9'd478:9'd238,15'd21112,kind==3?HUD0_BASE+24'd21112:CANONICAL0_BASE+24'd128);
  end
  initial_reads=accepted_reads;start(0,0,0,0,0,RGB0_BASE);finish(1,0,1);if(accepted_reads!=initial_reads)$fatal(1,"bad source issued read");
  start(0,0,0,479,0,CANONICAL0_BASE);finish(1,0,1);
  start(1,0,0,239,0,CANONICAL0_BASE);finish(1,0,1);
  start(3,0,0,0,21120,HUD0_BASE);finish(1,0,1);
  start(0,0,0,0,0,CANONICAL0_BASE+1);finish(1,0,1);
  response_error=1;initial_writes=writes_seen;start(0,0,0,0,0,CANONICAL0_BASE);finish(1,0,2);response_error=0;if(writes_seen!=initial_writes)$fatal(1,"failed read wrote cache");
  wr_allow=0;start(3,0,0,0,0,HUD0_BASE);finish(1,0,6);wr_allow=1;
  allow_requests=0;start(0,0,0,0,0,CANONICAL0_BASE);wait(lcd_req_valid);abort_command(0);finish(0,1,0);allow_requests=1;
  configured_delay=20;start(0,0,0,0,0,CANONICAL0_BASE);wait(lcd_busy);abort_command(0);finish(0,1,0);
  start(3,0,0,0,0,HUD0_BASE);wait(cache_wr_valid);repeat(2)@(posedge clk);abort_command(0);finish(0,1,0);
  start(0,0,0,0,0,CANONICAL0_BASE);wait(result_valid);abort_command(0);finish(0,1,0);
  start(0,0,0,0,0,CANONICAL0_BASE);wait(lcd_busy);abort_command(1);finish(0,0,0);
  @(negedge clk);inject_response=1;@(posedge clk);@(negedge clk);inject_response=0;
  while(!result_valid)@(negedge clk);if(!result_error||result_reason!=3||unowned_responses!=1||cache_wr_valid)$fatal(1,"unowned response not quarantined");
  result_ready=1;@(posedge clk);@(negedge clk);result_ready=0;checks=checks+1;
  start(0,1,1,0,0,CANONICAL1_BASE);wait(lcd_busy);@(negedge clk);rst=1;repeat(3)@(negedge clk);rst=0;
  if(busy||lcd_busy||result_valid||cache_wr_valid)$fatal(1,"coordinated reset not flushed");
  start(0,1,1,0,0,CANONICAL1_BASE);finish(0,0,0);readback(0,1,1,0,0,CANONICAL1_BASE);
  $display("CU71_CACHE_DMA_PASS checks=%0d commands=%0d contexts=2 cache_kinds=4 abort_phases=4 stale_abort=1 response_error=1 cache_error=1 unowned_reply=1 coordinated_reset=1",checks,commands);$finish;
 end
 initial begin #1000000;$fatal(1,"cache DMA watchdog");end
endmodule
