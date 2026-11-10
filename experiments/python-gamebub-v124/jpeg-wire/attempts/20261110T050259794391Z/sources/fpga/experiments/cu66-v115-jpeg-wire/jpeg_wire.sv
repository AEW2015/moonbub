`timescale 1ns/1ps
`default_nettype none
// Verification composition only: all three data-path modules are original RTL.
module jpeg_wire (
 input wire endpoint_clk, core_clk, reset,
 input wire qspi_sck, qspi_cs_n, input wire [3:0] qspi_dq,
 output wire [3:0] qspi_out, qspi_oe,
 input wire frame_boundary, memory_idle, pixel_ready,
 output wire pixel_valid, output wire [23:0] pixel_address,
 output wire [15:0] pixel_rgb565,
 output wire front_buffer, front_valid, pattern_enable,
 output wire cdc_overflow, output reg [31:0] transport_lost,
 output wire accepted_bus_write, output wire [11:0] accepted_address,
 output wire [31:0] accepted_data,
 output wire endpoint_sideband_changed
);
 wire spi_write, spi_read;
 wire irq_request, display_external, color_correct_enable, overlay_write;
 wire [3:0] control;
 wire [11:0] forced_buttons;
 wire [23:0] overlay_x, overlay_y;
 wire [17:0] overlay_address;
 wire [15:0] overlay_data;
 assign endpoint_sideband_changed = irq_request || control!=4'd3 ||
  (|forced_buttons) || display_external || color_correct_enable ||
  (|overlay_x) || (|overlay_y) || overlay_write ||
  (|overlay_address) || (|overlay_data);
 wire [11:0] spi_address;
 wire [31:0] spi_wdata, spi_rdata, core_rdata, gray;
 (* ASYNC_REG="TRUE" *) reg [31:0] gray_meta, gray_sync;
 function automatic [31:0] ungray(input [31:0] value);
 integer bit_index;
 begin
  for (bit_index=0;bit_index<32;bit_index=bit_index+1)
   ungray[bit_index]=^(value>>bit_index);
 end
 endfunction
 always @(posedge core_clk) begin
  if (reset) begin gray_meta<=0; gray_sync<=0; transport_lost<=0; end
  else begin gray_meta<=gray; gray_sync<=gray_meta; transport_lost<=ungray(gray_sync); end
 end
 moonshine_qspi_endpoint endpoint (
  .clk200(endpoint_clk),.rst_n(!reset),.qspi_sck(qspi_sck),
  .qspi_cs_n(qspi_cs_n),.qspi_dq_i(qspi_dq),.dq_o(qspi_out),.dq_oe(qspi_oe),
  .buttons_native(12'd0),.vblank(1'b0),.irq_request(irq_request),.control(control),
  .force_buttons_native(forced_buttons),.display_external(display_external),
  .color_correct_enable(color_correct_enable),.overlay_xctrl(overlay_x),
  .overlay_yctrl(overlay_y),.ov_wr(overlay_write),
  .ov_addr(overlay_address),.ov_data(overlay_data),
  .core_write(spi_write),.core_read(spi_read),.core_address(spi_address),
  .core_wdata(spi_wdata),.core_rdata(spi_rdata));
 moonshine_bus_cdc bridge (
  .spi_clk(endpoint_clk),.spi_reset(reset),.spi_write(spi_write),.spi_read(spi_read),
  .spi_address(spi_address),.spi_wdata(spi_wdata),.spi_rdata(spi_rdata),
  .overflow(cdc_overflow),.overflow_gray(gray),.core_clk(core_clk),.core_reset(reset),
  .core_write(accepted_bus_write),.core_address(accepted_address),
  .core_wdata(accepted_data),.core_rdata(core_rdata));
 moonshine_core #(.WATCHDOG_CYCLES(5000000)) core (
  .clk(core_clk),.reset(reset),.bus_write(accepted_bus_write),
  .bus_address(accepted_address),.bus_wdata(accepted_data),.bus_rdata(core_rdata),
  .frame_boundary(frame_boundary),.memory_idle(memory_idle),
  .front_buffer(front_buffer),.front_valid(front_valid),.pattern_enable(pattern_enable),
  .pixel_valid(pixel_valid),.pixel_ready(pixel_ready),.pixel_address(pixel_address),
  .pixel_rgb565(pixel_rgb565),.scanout_underruns(32'd0),.transport_overflows(transport_lost));
endmodule
`default_nettype wire
