`timescale 1ns/1ps
module tb_scanout_memory #(parameter integer BACKGROUND=1);
 logic clk=0,read_clk=0,rst=1,abort_i=0,aux_abort_i=0;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.625 ~clk;
 logic read_valid=0,read_ready;logic [63:0] read_generation=0;logic [1:0] read_bank=0,read_plane=0;logic [16:0]read_index=0;
 logic read_rsp_valid,read_rsp_ready=0;logic [63:0]read_rsp_generation;logic[1:0]read_rsp_bank,read_rsp_plane;logic[16:0]read_rsp_index;logic[511:0]read_rsp_pixels;logic read_rsp_error;
 logic write_valid=0,write_ready;logic[63:0]write_generation=0;logic[1:0]write_bank=0,write_plane=0;logic[16:0]write_index=0;logic[511:0]write_pixels=0;
 logic write_done_valid,write_done_ready=0;logic[63:0]write_done_generation;logic[1:0]write_done_bank,write_done_plane;logic[16:0]write_done_index;logic write_done_error;
 logic tile_busy,tile_aborted;
 logic aux_req_valid=0,aux_req_ready,aux_req_write=0;logic[23:0]aux_req_addr=0;logic[15:0]aux_req_data=0;
 logic aux_rsp_valid,aux_rsp_ready=0;logic[15:0]aux_rsp_data;logic aux_rsp_error,aux_busy,aux_aborted;
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;logic idle;
 logic lcd_req_valid,lcd_req_ready,lcd_rsp_valid,lcd_rsp_ready,lcd_rsp_error,lcd_abort_i,lcd_busy,lcd_aborted;
 logic[23:0]lcd_req_addr;logic[127:0]lcd_rsp_data;logic[31:0]lcd_completed_reads,lcd_max_wait;
 logic[31:0]cache_hits,cache_misses,completed_reads,completed_writes;
 cu71_memory_system #(.POWERUP_CYCLES(20)) dut(.*);
 sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768),.T_OH_NS(2.223)) model(.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 `include "cu70_memory_map.svh"
 integer checks=0,tiles=0,aux_ops=0,aborts=0,cycles=0;
 integer seed=7001,seed_input,max_aux_wait=0;
 logic[511:0]pattern;
 logic[15:0]got;
 integer b,p,t,j,k,idx,base,pitch,by,bx,address0,prior_writes,prior_refreshes;
 always @(posedge clk)cycles=cycles+1;
 function automatic logic[511:0]make_pattern(input integer salt);
  for(integer i=0;i<64;i=i+1)make_pattern[8*i+:8]=8'((salt*37+i*19)^(i/8));
 endfunction
 task automatic aux(input bit writing,input logic[23:0]address,input logic[15:0]data,input bit expect_bad,output logic[15:0]result);
  logic[15:0]saved;integer wait_count;
  begin
   @(negedge clk);aux_req_valid=1;aux_req_write=writing;aux_req_addr=address;aux_req_data=data;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;wait_count=0;
   while(!aux_rsp_valid)begin @(negedge clk);wait_count=wait_count+1;if(wait_count>2000)$fatal(1,"aux watchdog address%h",address);end
   if(wait_count>max_aux_wait)max_aux_wait=wait_count;
   if(aux_rsp_error!==expect_bad)$fatal(1,"aux error address%h got%b expected%b",address,aux_rsp_error,expect_bad);
   saved=aux_rsp_data;
   repeat(2)begin @(negedge clk);if(!aux_rsp_valid||aux_rsp_data!==saved||aux_rsp_error!==expect_bad)$fatal(1,"aux held response changed");end
   result=saved;aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;aux_ops=aux_ops+1;checks=checks+1;
  end
 endtask
 task automatic write_tile(input integer bank_id,plane_id,tile_id,input logic[511:0]pixels,input bit expect_bad);
  begin
   if(bank_id<0||bank_id>3||plane_id<0||plane_id>3||tile_id<0||tile_id>131071)$fatal(1,"write taskportdomain");
   @(negedge clk);write_valid=1;write_generation=64'd100+64'(tiles);write_bank=2'(bank_id);write_plane=2'(plane_id);write_index=17'(tile_id);write_pixels=pixels;
   do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;
   while(!write_done_valid)@(negedge clk);
   if(write_done_generation!=write_generation||write_done_bank!=write_bank||write_done_plane!=write_plane||write_done_index!=write_index||write_done_error!==expect_bad)$fatal(1,"write identity/error");
   repeat(3)begin @(negedge clk);if(!write_done_valid||write_done_error!==expect_bad)$fatal(1,"write result changed");end
   write_done_ready=1;@(posedge clk);@(negedge clk);write_done_ready=0;tiles=tiles+1;checks=checks+1;
  end
 endtask
 task automatic read_tile(input integer bank_id,plane_id,tile_id,input logic[511:0]pixels,input bit expect_bad);
  logic[511:0]saved;
  begin
   if(bank_id<0||bank_id>3||plane_id<0||plane_id>3||tile_id<0||tile_id>131071)$fatal(1,"read taskportdomain");
   @(negedge clk);read_valid=1;read_generation=64'd200+64'(tiles);read_bank=2'(bank_id);read_plane=2'(plane_id);read_index=17'(tile_id);
   do @(posedge clk);while(!read_ready);
   @(negedge clk);read_valid=0;
   while(!read_rsp_valid)@(negedge clk);
   if(read_rsp_generation!=read_generation||read_rsp_bank!=read_bank||read_rsp_plane!=read_plane||read_rsp_index!=read_index||read_rsp_error!==expect_bad)$fatal(1,"read identity/error");
   if(!expect_bad&&read_rsp_pixels!==pixels)$fatal(1,"tile mismatch bank%0d plane%0d index%0d got%h expected%h",bank_id,plane_id,tile_id,read_rsp_pixels,pixels);
   saved=read_rsp_pixels;
   repeat(3)begin @(negedge clk);if(!read_rsp_valid||read_rsp_pixels!==saved)$fatal(1,"read response changed");end
   read_rsp_ready=1;@(posedge clk);@(negedge clk);read_rsp_ready=0;tiles=tiles+1;checks=checks+1;
  end
 endtask
 task automatic abort_write(input integer accepted_words);
  integer before_count,initial_writes;
  begin
   initial_writes=model.writes;
   @(negedge clk);write_valid=1;write_generation=700;write_bank=0;write_plane=0;write_index=100;write_pixels=make_pattern(accepted_words+900);
   do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;while(model.writes-initial_writes<accepted_words)@(negedge clk);
   before_count=model.writes;abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(write_done_valid||read_rsp_valid)$fatal(1,"aborted tile exposed success");@(negedge clk);end
   if(!tile_aborted)$fatal(1,"missing tileabort completion");
   if(model.writes-before_count>1)$fatal(1,"abort started new writes");
   // Previously accepted controller write may have reached the array, but all
   // later writes are canceled and the transaction never reports success.
   aborts=aborts+1;checks=checks+1;
  end
 endtask
 task automatic abort_read(input integer accepted_bursts);
  integer initial_reads;
  begin
   initial_reads=model.reads;
   @(negedge clk);read_valid=1;read_generation=800;read_bank=2;read_plane=2;read_index=17'(200+accepted_bursts*7);
   do @(posedge clk);while(!read_ready);
   @(negedge clk);read_valid=0;
   while(model.reads-initial_reads<accepted_bursts)@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(read_rsp_valid||write_done_valid)$fatal(1,"abortedreadexposedsuccess");@(negedge clk);end
   if(!tile_aborted)$fatal(1,"missingreadabortcompletion");
   aborts=aborts+1;checks=checks+1;
  end
 endtask

 logic pixel_clk=0,pixel_reset_n=0;
 always #17.03 pixel_clk=~pixel_clk;
 logic descriptor_valid=0,descriptor_ready,descriptor_slot=0;
 logic[63:0]descriptor_generation=1;logic[31:0]descriptor_frame_id=10;
 logic presented,error,front_valid,front_slot,pending_valid;
 logic[63:0]front_generation;logic[31:0]front_frame_id,presented_count;
 logic frame_boundary,scanout_drained;logic[31:0]underruns,memory_errors;
 logic hsync,vsync,data_enable;logic[9:0]physical_x,physical_y;logic[7:0]red,green,blue;
 cu71_scanout_prefetch #(.RGB_BASE(RGB0_BASE)) scanout(
  .mem_clk(clk),.mem_rst(rst),.pixel_clk,.pixel_reset_n,
  .descriptor_valid,.descriptor_ready,.descriptor_generation,.descriptor_frame_id,.descriptor_slot,
  .presented,.error,.front_valid,.front_slot,.front_generation,.front_frame_id,.pending_valid,.presented_count,
  .frame_boundary,.scanout_drained,.lcd_req_valid,.lcd_req_ready,.lcd_req_addr,.lcd_rsp_valid,.lcd_rsp_ready,
  .lcd_rsp_data,.lcd_rsp_error,.lcd_abort_i,.lcd_busy,.lcd_aborted,.underruns,.memory_errors,
  .hsync,.vsync,.data_enable,.physical_x,.physical_y,.red,.green,.blue);
 function automatic[15:0]expected(input integer x,y);
  integer value;
  begin value=(x*47+y*133)^((x^y)<<7);expected=16'(value|1);end
 endfunction
 integer pixel_checks=0,canvas_checks=0,black_lines=0,background_tiles=0,background_hud=0;
 bit line_black=0,monitor_done=0;integer selected_underruns=0;
 initial begin wait(monitor_done);repeat(8)@(negedge clk);selected_underruns=underruns;end
 logic[15:0]want;
 always @(posedge pixel_clk)begin
  #0.1;
  if(pixel_reset_n&&front_valid&&data_enable&&!monitor_done)begin
   if(physical_x>=480||physical_y>=800)$fatal(1,"raster bounds");
   want=(physical_y>=40&&physical_y<760)?expected(physical_x,physical_y):16'd0;
   if(physical_x==0)begin
    line_black=physical_y>=40&&physical_y<760&&red==0&&green==0&&blue==0;
    if(line_black)black_lines=black_lines+1;
   end
   if(line_black)want=0;
   if(red!=={want[15:11],want[15:13]}||green!=={want[10:5],want[10:9]}||blue!=={want[4:0],want[4:2]})
    $fatal(1,"actual SDRAM/LCD pixel mismatch x%0d y%0d got%h,%h,%h expected%h",physical_x,physical_y,red,green,blue,want);
   pixel_checks=pixel_checks+1;
   if(physical_y>=40&&physical_y<48)canvas_checks=canvas_checks+1;
   if(physical_y==47&&physical_x==479)monitor_done=1;
  end
 end
 integer line_start=0,max_line_fill_cycles=0,line_fills=0;
 bit previous_receiving=0;
 always @(posedge clk)begin
  if(lcd_req_valid&&lcd_req_ready&&((lcd_req_addr-RGB0_BASE)%480)==0)line_start=cycles;
  #0.2;
  if(previous_receiving&&!scanout.lcd.receiving)begin
   if(cycles-line_start>max_line_fill_cycles)max_line_fill_cycles=cycles-line_start;
   line_fills=line_fills+1;
  end
  previous_receiving=scanout.lcd.receiving;
 end
 initial begin
  for(j=0;j<384000;j=j+1)model.mem[RGB0_BASE+j]=expected(j%480,j/480);
  repeat(10)@(negedge clk);rst=0;
  wait(idle);@(negedge clk);descriptor_valid=1;
  do @(posedge clk);while(!descriptor_ready);
  @(negedge clk);descriptor_valid=0;pixel_reset_n=1;
  wait(front_valid);wait(lcd_req_valid);
  if(BACKGROUND!=0)begin
  fork
   begin
    while(!monitor_done)begin write_tile(1,0,230,make_pattern(background_tiles),0);background_tiles=background_tiles+1;end
   end
   begin
    integer n;logic[15:0]value;n=0;
    while(!monitor_done)begin aux(1,HUD2_BASE+24'(n),16'(n*13+3),0,value);n=n+1;background_hud=background_hud+1;end
   end
  join
  end else wait(monitor_done);
  repeat(10)@(negedge clk);
  if(canvas_checks!=3840||front_generation!=1||front_frame_id!=10||presented_count!=1||memory_errors||error)
   $fatal(1,"descriptor/pixel/accounting failure");
  if((BACKGROUND!=0&&(background_tiles<1||background_hud<1))||model.refreshes<1)$fatal(1,"missing concurrent workload");
  if(selected_underruns!=black_lines)$fatal(1,"black line accounting selected%0d global%0d black%0d",selected_underruns,underruns,black_lines);
  $display("CU71_MEMORY_SCANOUT_FUNCTIONAL_PASS canvas_pixels=%0d all_checked_pixels=%0d lines_filled=%0d max_line_fill_cycles=%0d backend_wait=%0d tile_writes=%0d HUD_writes=%0d refreshes=%0d black_lines=%0d selected_underruns=%0d total_underruns_after_background_drain=%0d",canvas_checks,pixel_checks,line_fills,max_line_fill_cycles,lcd_max_wait,background_tiles,background_hud,model.refreshes,black_lines,selected_underruns,underruns);
  if(black_lines==0)$display("CU71_MEMORY_SCANOUT_CADENCE_PASS selected_lines=8");
  else $display("CU71_MEMORY_SCANOUT_CADENCE_FAIL selected_lines=8");
  $finish;
 end
 initial begin #5000000;$fatal(1,"integrated scanout watchdog");end
endmodule
