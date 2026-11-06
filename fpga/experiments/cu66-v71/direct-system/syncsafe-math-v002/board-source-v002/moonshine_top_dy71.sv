`timescale 1ns/1ps
`default_nettype none
module moonshine_top_dy71(
 input wire clk_50mhz,
 input wire mcu_spi_clk,mcu_spi_cs_n,inout wire[3:0]mcu_spi_d,output wire mcu_irq_n,
 input wire btn_a,btn_b,btn_x,btn_y,btn_up,btn_down,btn_left,btn_right,btn_l,btn_r,btn_start,btn_select,
 output wire lcd_dotclk,lcd_hsync,lcd_vsync,lcd_data_en,
 output wire[7:0]lcd_data_r,lcd_data_g,lcd_data_b,
 output wire[12:0]sdram_a,output wire[1:0]sdram_bs,inout wire[15:0]sdram_dq,
 output wire sdram_clk,sdram_we_n,sdram_ldqm,sdram_udqm,sdram_cas_n,sdram_ras_n,
 output wire[1:0]sdram_cke,sdram_cs_n,
 output wire vibrate_in1,vibrate_in2,dac_mclk,dac_bclk,dac_wclk,dac_din
);
 wire clk50,inclk;IBUF input_buffer(.I(clk_50mhz),.O(inclk));BUFG base_clock(.I(inclk),.O(clk50));
 wire fb,fbb,raw200,raw100,raw_read100,clk200,clk100,read_clk100,locked;
 PLLE2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT(20),.DIVCLK_DIVIDE(1),.CLKOUT0_DIVIDE(5),.CLKOUT1_DIVIDE(10),.CLKOUT2_DIVIDE(10),.CLKOUT2_PHASE(274.5))
 service_pll(.CLKIN1(clk50),.CLKFBIN(fbb),.CLKFBOUT(fb),.CLKOUT0(raw200),.CLKOUT1(raw100),.CLKOUT2(raw_read100),.LOCKED(locked),.PWRDWN(1'b0),.RST(1'b0));
 BUFG feedback(.I(fb),.O(fbb));BUFG spi_clock(.I(raw200),.O(clk200));BUFG memory_clock(.I(raw100),.O(clk100));
 BUFG read_clock(.I(raw_read100),.O(read_clk100));
 wire pfb,pfbb,praw,pclk,plocked;
 MMCME2_BASE #(.CLKIN1_PERIOD(20.0),.CLKFBOUT_MULT_F(56.375),.DIVCLK_DIVIDE(3),.CLKOUT0_DIVIDE_F(32.0))
 panel_mmcm(.CLKIN1(clk50),.CLKFBIN(pfbb),.CLKFBOUT(pfb),.CLKOUT0(praw),.LOCKED(plocked),.PWRDWN(1'b0),.RST(1'b0));
 BUFG panel_feedback(.I(pfb),.O(pfbb));BUFG panel_clock(.I(praw),.O(pclk));

 // Both domains and transport are jointly flushed; later clock loss quarantines
 // this diagnostic configuration until full reconfiguration, never a soft reset.
 (* ASYNC_REG="TRUE" *)reg[1:0]platform_service_lock_sync=0,platform_panel_lock_sync=0;
 reg platform_reset_ref=1;
 always @(posedge clk50)begin
  platform_service_lock_sync<={platform_service_lock_sync[0],locked};
  platform_panel_lock_sync<={platform_panel_lock_sync[0],plocked};
  platform_reset_ref<=!(platform_service_lock_sync[1]&&platform_panel_lock_sync[1]);
 end
 (* ASYNC_REG="TRUE" *)reg[3:0]joint_core_reset=15,joint_spi_reset=15,joint_pixel_reset=15;
 always @(posedge clk100 or posedge platform_reset_ref)if(platform_reset_ref)joint_core_reset<=15;else joint_core_reset<={joint_core_reset[2:0],1'b0};
 always @(posedge clk200 or posedge platform_reset_ref)if(platform_reset_ref)joint_spi_reset<=15;else joint_spi_reset<={joint_spi_reset[2:0],1'b0};
 always @(posedge pclk or posedge platform_reset_ref)if(platform_reset_ref)joint_pixel_reset<=15;else joint_pixel_reset<={joint_pixel_reset[2:0],1'b0};
 reg configuration_started=0,reconfigure_required=0;
 always @(posedge clk50)begin
  if(!platform_reset_ref)configuration_started<=1;
  if(configuration_started&&platform_reset_ref)reconfigure_required<=1;
 end
 (* ASYNC_REG="TRUE" *)reg[1:0]quarantine_sync=0;
 always @(posedge clk100)quarantine_sync<={quarantine_sync[0],reconfigure_required};
 wire clk=clk100,rst=joint_core_reset[3],read_clk=read_clk100,pixel_clk=pclk,pixel_reset_n=!joint_pixel_reset[3];
 wire[3:0]dq_i,dq_o,dq_oe,endpoint_control;wire irq;
 genvar k;generate for(k=0;k<4;k=k+1)begin:mcu_io
 IOBUF lane(.IO(mcu_spi_d[k]),.I(dq_o[k]),.O(dq_i[k]),.T(!dq_oe[k]));end endgenerate
 OBUFT irq_driver(.O(mcu_irq_n),.I(1'b0),.T(!irq));
 wire[11:0]buttons=~{btn_select,btn_start,btn_r,btn_l,btn_right,btn_left,btn_down,btn_up,btn_y,btn_x,btn_b,btn_a};
 wire spi_write,spi_read;wire[11:0]spi_addr;wire[31:0]spi_wdata,spi_rdata;
 moonshine_qspi_endpoint endpoint(.clk200(clk200),.rst_n(!joint_spi_reset[3]),
 .qspi_sck(mcu_spi_clk),.qspi_cs_n(mcu_spi_cs_n),.qspi_dq_i(dq_i),.dq_o(dq_o),.dq_oe(dq_oe),
 .buttons_native(buttons),.vblank(vsync),.irq_request(irq),.control(endpoint_control),.force_buttons_native(),
 .display_external(),.color_correct_enable(),.overlay_xctrl(),.overlay_yctrl(),.ov_wr(),.ov_addr(),.ov_data(),
 .core_write(spi_write),.core_read(spi_read),.core_address(spi_addr),.core_wdata(spi_wdata),.core_rdata(spi_rdata));
 wire bus_write;wire[11:0]bus_address;wire[11:0]bus_read_address;wire[31:0]bus_wdata,bus_rdata;
 wire transport_overflow;wire[31:0]transport_gray;
 (* ASYNC_REG="TRUE" *)reg[31:0]transport_gray_meta=0,transport_gray_sync=0;
 reg[31:0]transport_lost_words=0;
 function automatic[31:0]ungray_transport(input[31:0]value);
 integer i;begin for(i=0;i<32;i=i+1)ungray_transport[i]=^(value>>i);end endfunction
 always @(posedge clk100)begin
  if(rst)begin transport_gray_meta<=0;transport_gray_sync<=0;transport_lost_words<=0;end
  else begin transport_gray_meta<=transport_gray;transport_gray_sync<=transport_gray_meta;transport_lost_words<=ungray_transport(transport_gray_sync);end
 end
 wire transport_fault=quarantine_sync[1]||transport_lost_words!=0;
 cu71_bus_cdc_split bridge(.spi_clk(clk200),.spi_reset(joint_spi_reset[3]),.spi_write(spi_write),.spi_read(spi_read),
 .spi_address(spi_addr),.spi_wdata(spi_wdata),.spi_rdata(spi_rdata),.overflow(transport_overflow),.overflow_gray(transport_gray),
 .core_clk(clk100),.core_reset(rst),.core_write(bus_write),.core_address(bus_address),.core_read_address(bus_read_address),.core_wdata(bus_wdata),.core_rdata(bus_rdata));
 wire  abort_i;
 wire  aborted;
 wire [31:0] accepted_count;
 wire [31:0] active_frame_id;
 wire [63:0] active_generation;
 wire  active_key;
 wire [31:0] active_reference_id;
 wire [7:0] blue;
 wire  busy;
 wire [31:0] cache_accepted_prepares;
 wire [31:0] cache_dma_reads;
 wire [31:0] cache_generated_lines;
 wire [31:0] cache_line_misses;
 wire  cache_prepare_busy;
 wire [31:0] cache_prepare_cycles;
 wire  cache_prepare_fault;
 wire [31:0] cache_rejected_descriptors;
 wire [31:0] cache_rejected_prepares;
 wire [31:0] cache_unowned_responses;
 wire [1:0] candidate_bank;
 wire  clear_fault;
 wire  data_enable;
 wire [9:0] diag_address;
 wire [31:0] diag_data;
 wire  done;
 wire  error;
 wire [7:0] error_code;
 wire [127:0] expected_hud_tag;
 wire [1:0] front_bank;
 wire  front_cache_slot;
 wire [31:0] front_frame_id;
 wire [63:0] front_generation;
 wire  front_valid;
 wire [7:0] green;
 wire  hsync;
 wire [15:0] hud_address;
 wire [31:0] hud_aux_frame_id;
 wire [63:0] hud_aux_generation;
 wire [23:0] hud_aux_req_addr;
 wire [15:0] hud_aux_req_data;
 wire  hud_aux_req_ready;
 wire  hud_aux_req_valid;
 wire  hud_aux_req_write;
 wire [15:0] hud_aux_rsp_data;
 wire  hud_aux_rsp_error;
 wire  hud_aux_rsp_ready;
 wire  hud_aux_rsp_valid;
 wire [15:0] hud_bytes;
 wire [1:0] hud_drain_bank;
 wire [31:0] hud_drain_frame_id;
 wire [63:0] hud_drain_generation;
 wire  hud_drain_ready;
 wire  hud_drain_success;
 wire [127:0] hud_drain_tag;
 wire  hud_drain_valid;
 wire [15:0] hud_drain_words;
 wire  hud_prepare_ready;
 wire  hud_prepare_valid;
 wire [31:0] hud_result_frame_id;
 wire [63:0] hud_result_generation;
 wire  hud_result_ready;
 wire [31:0] hud_result_reference_id;
 wire  hud_result_success;
 wire [127:0] hud_result_tag;
 wire  hud_result_valid;
 wire [15:0] hud_result_words;
 wire  lcd_error;
 wire  lcd_frame_boundary;
 wire [31:0] lcd_front_frame_id;
 wire [63:0] lcd_front_generation;
 wire  lcd_front_slot;
 wire  lcd_front_valid;
 wire [31:0] lcd_memory_errors;
 wire  lcd_pending;
 wire  lcd_presented;
 wire [31:0] lcd_presented_count;
 wire  lcd_scanout_drained;
 wire [31:0] lcd_underruns;
 wire  memory_aux_busy;
 wire [31:0] memory_cache_hits;
 wire [31:0] memory_cache_misses;
 wire  memory_idle;
 wire [31:0] memory_reads;
 wire  memory_tile_busy;
 wire [31:0] memory_writes;
 wire [15:0] packet_req_address;
 wire [63:0] packet_req_generation;
 wire  packet_req_ready;
 wire [31:0] packet_req_sequence;
 wire  packet_req_valid;
 wire [15:0] packet_rsp_address;
 wire [7:0] packet_rsp_data;
 wire [63:0] packet_rsp_generation;
 wire  packet_rsp_ready;
 wire [31:0] packet_rsp_sequence;
 wire  packet_rsp_valid;
 wire [9:0] physical_x;
 wire [9:0] physical_y;
 wire [31:0] presented_count;
 wire [31:0] profile_abi;
 wire [31:0] profile_capabilities;
 wire [31:0] profile_magic;
 wire  quarantine;
 wire [7:0] red;
 wire [1:0] reference_bank;
 wire [31:0] reference_frame_id;
 wire [127:0] reference_tag;
 wire  reference_valid;
 wire [31:0] rejected_count;
 wire [31:0] software_ack_frame_id;
 wire [63:0] software_ack_generation;
 wire [2:0] software_ack_opcode;
 wire  software_ack_ready;
 wire  software_ack_success;
 wire  software_ack_valid;
 wire [2:0] software_command_opcode;
 wire  software_command_ready;
 wire  software_command_valid;
 wire [7:0] stage;
 wire [31:0] stale_completions;
 wire [63:0] start_generation;
 wire [31:0] start_packet_bytes;
 wire  start_ready;
 wire  start_valid;
 wire  vsync;
 dy71_local_control_split control_plane(.clk(clk),.rst(rst),.bus_write(bus_write),.bus_address(bus_address),.bus_read_address(bus_read_address),.bus_wdata(bus_wdata),.bus_rdata(bus_rdata),.transport_fault(transport_fault),.start_valid(start_valid),.start_ready(start_ready),.start_generation(start_generation),.start_packet_bytes(start_packet_bytes),.abort_i(abort_i),.clear_fault(clear_fault),.busy(busy),.done(done),.error(error),.stage(stage),.error_code(error_code),.memory_tile_busy(memory_tile_busy),.memory_aux_busy(memory_aux_busy),.accepted_count(accepted_count),.presented_count(presented_count),.rejected_count(rejected_count),.lcd_underruns(lcd_underruns),.packet_req_valid(packet_req_valid),.packet_req_ready(packet_req_ready),.packet_req_address(packet_req_address),.packet_req_generation(packet_req_generation),.packet_req_sequence(packet_req_sequence),.packet_rsp_valid(packet_rsp_valid),.packet_rsp_ready(packet_rsp_ready),.packet_rsp_address(packet_rsp_address),.packet_rsp_generation(packet_rsp_generation),.packet_rsp_sequence(packet_rsp_sequence),.packet_rsp_data(packet_rsp_data),.hud_prepare_valid(hud_prepare_valid),.hud_prepare_ready(hud_prepare_ready),.active_generation(active_generation),.active_frame_id(active_frame_id),.active_reference_id(active_reference_id),.active_key(active_key),.hud_address(hud_address),.hud_bytes(hud_bytes),.expected_hud_tag(expected_hud_tag),.candidate_bank(candidate_bank),.hud_result_valid(hud_result_valid),.hud_result_ready(hud_result_ready),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_ready(hud_drain_ready),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.software_command_valid(software_command_valid),.software_command_ready(software_command_ready),.software_command_opcode(software_command_opcode),.software_ack_valid(software_ack_valid),.software_ack_ready(software_ack_ready),.software_ack_opcode(software_ack_opcode),.software_ack_generation(software_ack_generation),.software_ack_frame_id(software_ack_frame_id),.software_ack_success(software_ack_success),.hud_aux_req_valid(hud_aux_req_valid),.hud_aux_req_ready(hud_aux_req_ready),.hud_aux_generation(hud_aux_generation),.hud_aux_frame_id(hud_aux_frame_id),.hud_aux_req_write(hud_aux_req_write),.hud_aux_req_addr(hud_aux_req_addr),.hud_aux_req_data(hud_aux_req_data),.hud_aux_rsp_valid(hud_aux_rsp_valid),.hud_aux_rsp_ready(hud_aux_rsp_ready),.hud_aux_rsp_data(hud_aux_rsp_data),.hud_aux_rsp_error(hud_aux_rsp_error),.diag_address(diag_address),.diag_data(diag_data),.quarantine(quarantine));
cu71_system_direct_syncsafe #(.WATCHDOG_CYCLES(32'd3000000000)) system_core(.clk(clk),.read_clk(read_clk),.pixel_clk(pixel_clk),.pixel_reset_n(pixel_reset_n),.rst(rst),.abort_i(abort_i),.clear_fault(clear_fault),.start_valid(start_valid),.start_ready(start_ready),.start_generation(start_generation),.start_packet_bytes(start_packet_bytes),.packet_req_valid(packet_req_valid),.packet_req_ready(packet_req_ready),.packet_req_address(packet_req_address),.packet_req_generation(packet_req_generation),.packet_req_sequence(packet_req_sequence),.packet_rsp_valid(packet_rsp_valid),.packet_rsp_ready(packet_rsp_ready),.packet_rsp_generation(packet_rsp_generation),.packet_rsp_sequence(packet_rsp_sequence),.packet_rsp_address(packet_rsp_address),.packet_rsp_data(packet_rsp_data),.hud_prepare_valid(hud_prepare_valid),.hud_prepare_ready(hud_prepare_ready),.active_generation(active_generation),.active_frame_id(active_frame_id),.active_reference_id(active_reference_id),.active_key(active_key),.hud_address(hud_address),.hud_bytes(hud_bytes),.expected_hud_tag(expected_hud_tag),.candidate_bank(candidate_bank),.hud_result_valid(hud_result_valid),.hud_result_ready(hud_result_ready),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_ready(hud_drain_ready),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.software_command_valid(software_command_valid),.software_command_ready(software_command_ready),.software_command_opcode(software_command_opcode),.software_ack_valid(software_ack_valid),.software_ack_ready(software_ack_ready),.software_ack_opcode(software_ack_opcode),.software_ack_generation(software_ack_generation),.software_ack_frame_id(software_ack_frame_id),.software_ack_success(software_ack_success),.front_valid(front_valid),.front_cache_slot(front_cache_slot),.front_bank(front_bank),.front_generation(front_generation),.front_frame_id(front_frame_id),.reference_valid(reference_valid),.reference_bank(reference_bank),.reference_frame_id(reference_frame_id),.reference_tag(reference_tag),.busy(busy),.done(done),.aborted(aborted),.error(error),.error_code(error_code),.stage(stage),.accepted_count(accepted_count),.presented_count(presented_count),.rejected_count(rejected_count),.stale_completions(stale_completions),.diag_address(diag_address),.diag_data(diag_data),.hud_aux_req_valid(hud_aux_req_valid),.hud_aux_req_ready(hud_aux_req_ready),.hud_aux_generation(hud_aux_generation),.hud_aux_frame_id(hud_aux_frame_id),.hud_aux_req_write(hud_aux_req_write),.hud_aux_req_addr(hud_aux_req_addr),.hud_aux_req_data(hud_aux_req_data),.hud_aux_rsp_valid(hud_aux_rsp_valid),.hud_aux_rsp_ready(hud_aux_rsp_ready),.hud_aux_rsp_data(hud_aux_rsp_data),.hud_aux_rsp_error(hud_aux_rsp_error),.lcd_front_valid(lcd_front_valid),.lcd_front_slot(lcd_front_slot),.lcd_presented(lcd_presented),.lcd_pending(lcd_pending),.lcd_frame_boundary(lcd_frame_boundary),.lcd_scanout_drained(lcd_scanout_drained),.lcd_error(lcd_error),.lcd_front_generation(lcd_front_generation),.lcd_front_frame_id(lcd_front_frame_id),.lcd_presented_count(lcd_presented_count),.lcd_underruns(lcd_underruns),.lcd_memory_errors(lcd_memory_errors),.hsync(hsync),.vsync(vsync),.data_enable(data_enable),.physical_x(physical_x),.physical_y(physical_y),.red(red),.green(green),.blue(blue),.profile_magic(profile_magic),.profile_abi(profile_abi),.profile_capabilities(profile_capabilities),.cache_prepare_busy(cache_prepare_busy),.cache_prepare_fault(cache_prepare_fault),.cache_dma_reads(cache_dma_reads),.cache_line_misses(cache_line_misses),.cache_generated_lines(cache_generated_lines),.cache_prepare_cycles(cache_prepare_cycles),.cache_accepted_prepares(cache_accepted_prepares),.cache_rejected_prepares(cache_rejected_prepares),.cache_rejected_descriptors(cache_rejected_descriptors),.cache_unowned_responses(cache_unowned_responses),.memory_tile_busy(memory_tile_busy),.memory_aux_busy(memory_aux_busy),.memory_idle(memory_idle),.memory_cache_hits(memory_cache_hits),.memory_cache_misses(memory_cache_misses),.memory_reads(memory_reads),.memory_writes(memory_writes),.sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),.sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),.sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));

 assign lcd_hsync=hsync;assign lcd_vsync=vsync;assign lcd_data_en=data_enable;
 assign lcd_data_r=red;assign lcd_data_g=green;assign lcd_data_b=blue;
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) dotclock(.C(pclk),.CE(1'b1),.D1(1'b1),.D2(1'b0),.R(1'b0),.S(1'b0),.Q(lcd_dotclk));
 assign vibrate_in1=0;assign vibrate_in2=0;assign dac_mclk=0;assign dac_bclk=0;assign dac_wclk=0;assign dac_din=0;
endmodule
`default_nettype wire
