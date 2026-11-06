`timescale 1ns/1ps
module tb_direct_memory #(parameter integer LAST_LINE=799);
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
 logic rgb_req_valid=0,rgb_req_ready,rgb_rsp_valid,rgb_rsp_ready=1,rgb_rsp_error,rgb_abort_i=0,rgb_busy,rgb_aborted;logic[23:0]rgb_req_addr=0;logic[127:0]rgb_req_data=0;logic[15:0]rgb_req_mask=0;logic[31:0]rgb_completed_writes,rgb_max_wait;
 logic[31:0]cache_hits,cache_misses,completed_reads,completed_writes;
 cu71_memory_system_direct #(.POWERUP_CYCLES(20)) dut(.*);
 sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757),.T_OH_NS(2.223)) model(.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 `include "cu70_memory_map.svh"

 logic pixel_clk=0,pixel_reset_n=0;always #17.03 pixel_clk=~pixel_clk;
 logic prepare_valid=0,prepare_ready;logic[63:0]prepare_generation=1;logic[31:0]prepare_frame_id=100;
 logic[1:0]prepare_canonical_bank=0,prepare_hud_bank=0;logic prepare_cache_slot=0;
 logic prepared_valid,prepared_ready=0;logic[63:0]prepared_generation;logic[31:0]prepared_frame_id;logic prepared_cache_slot,prepared_error;logic[7:0]prepared_reason;
 logic prepare_abort_valid=0,prepare_abort_ready;logic[63:0]prepare_abort_generation=0;logic[31:0]prepare_abort_frame_id=0;logic prepare_abort_cache_slot=0,abort_done,abort_error;
 logic descriptor_valid=0,descriptor_ready;logic[63:0]descriptor_generation=1;logic[31:0]descriptor_frame_id=100;logic descriptor_cache_slot=0;
 logic presented,error,front_valid,front_cache_slot;logic[63:0]front_generation;logic[31:0]front_frame_id;logic pending_valid;logic[31:0]presented_count;
 logic frame_boundary,scanout_drained;logic[31:0]underruns,dma_reads,unowned_dma_responses,accepted_prepares,rejected_prepares,rejected_descriptors,memory_errors,line_cache_misses,generated_lines,prepare_cycles;
 logic[7:0]first_fault;logic[63:0]first_fault_generation;logic[31:0]first_fault_frame_id;
 logic hsync,vsync,data_enable;logic[9:0]physical_x,physical_y;logic[7:0]red,green,blue;
 cu71_direct_scanout scanout(.mem_clk(clk),.*);
 reg[15:0]canonical[0:259199],hud[0:21119],gold[0:345599];integer i,pixels=0,black_lines=0;reg[15:0]want;reg black_line=0,monitor_done=0;integer prep_start,prep_reads;
 always @(posedge pixel_clk)begin
  #0.001;
  if(pixel_reset_n&&front_valid&&data_enable&&!monitor_done)begin
   want=(physical_y>=40&&physical_y<760)?gold[physical_x*720+physical_y-40]:16'd0;
   if(physical_x==0)begin black_line=physical_y>=40&&physical_y<760&&!scanout.lcd.line_good;if(black_line)black_lines=black_lines+1;end
   if(black_line)want=0;
   if(red!=={want[15:11],want[15:13]}||green!=={want[10:5],want[10:9]}||blue!=={want[4:0],want[4:2]})$fatal(1,"direct pin native pixel mismatch x%0d y%0d expected%h got%h %h %h fault%h",physical_x,physical_y,want,red,green,blue,first_fault);
   pixels=pixels+1;if(physical_y==LAST_LINE&&physical_x==479)monitor_done=1;
  end
 end
 reg[23:0]check_address;integer checks=0;reg[15:0]expected_word;
 always @(posedge clk)begin
  if(lcd_req_valid&&lcd_req_ready)check_address<=lcd_req_addr;
  if(lcd_rsp_valid&&lcd_rsp_ready)begin
   for(integer q=0;q<8;q=q+1)begin
    expected_word=check_address>=HUD0_BASE?hud[check_address-HUD0_BASE+q]:canonical[check_address-CANONICAL0_BASE+q];
    if(lcd_rsp_data[q*16+:16]!==expected_word)$fatal(1,"physical BL8 payload mismatch addr%h lane%0d got%h want%h",check_address,q,lcd_rsp_data[q*16+:16],expected_word);
   end
   checks=checks+1;
  end
  if(scanout.cache_rd_valid&&scanout.render_u==0&&scanout.issue_count==40)$display("RAW_V40 ymem%h canonicalY%h CB%h CR%h gold%h",scanout.cache.y_mem[40],canonical[14400],scanout.cache.cb_top_mem[20],scanout.cache.cr_top_mem[20],gold[28800]);
 end
 initial begin
  $readmemh("canonical.hex",canonical);$readmemh("hud.hex",hud);$readmemh("gold.hex",gold);
  for(i=0;i<259200;i=i+1)model.mem[CANONICAL0_BASE+i]=canonical[i];
  for(i=0;i<21120;i=i+1)model.mem[HUD0_BASE+i]=hud[i];
  repeat(8)@(negedge clk);rst=0;wait(idle);@(negedge clk);prep_start=scanout.prepare_cycles;prepare_valid=1;
  do @(posedge clk);while(!prepare_ready);@(negedge clk);prepare_valid=0;wait(prepared_valid);@(negedge clk);
  if(prepared_error||prepared_generation!=1||prepared_frame_id!=100||prepared_cache_slot!=0)$fatal(1,"prepare identity/error reason%h",prepared_reason);
  if(dma_reads!=3600)$fatal(1,"cold prepare reads%0d",dma_reads);
  $display("DIRECT_PREPARE_PASS cycles%0d actual_pin_reads%0d",prepare_cycles,dma_reads);
  prepared_ready=1;@(posedge clk);@(negedge clk);prepared_ready=0;descriptor_valid=1;
  do @(posedge clk);while(!descriptor_ready);@(negedge clk);descriptor_valid=0;pixel_reset_n=1;
  wait(monitor_done);repeat(8)@(negedge clk);
  if(first_fault||memory_errors||unowned_dma_responses)$fatal(1,"direct diagnostics fault%h errors%0d",first_fault,memory_errors);
  $display("CU71_DIRECT_PIN_FUNCTIONAL_PASS pixels%0d black_lines%0d underruns%0d reads%0d maxwait%0d refreshes%0d",pixels,black_lines,underruns,dma_reads,lcd_max_wait,model.refreshes);
  if(black_lines==0&&underruns==0)$display("CU71_DIRECT_PIN_CADENCE_PASS");else $display("CU71_DIRECT_PIN_CADENCE_FAIL");
  $finish;
 end
 initial begin #60000000;$fatal(1,"direct actual pin watchdog gen%0d prep%0d reads%0d fault%h",front_generation,prepared_valid,dma_reads,first_fault);end
endmodule

