`timescale 1ns/1ps
`default_nettype none
// All registers, compressed RAM, decoder and framebuffer ownership live in clk.
// The platform bridge serializes the existing QSPI transactions into this bus.
module moonshine_core #(
 parameter integer WIDTH=720, HEIGHT=480, MAX_BYTES=262144,
 parameter integer WATCHDOG_CYCLES=50000000
)(
 input wire clk,reset,
 input wire bus_write,input wire [11:0] bus_address,input wire [31:0] bus_wdata,
 output reg [31:0] bus_rdata,
 input wire frame_boundary,input wire memory_idle,
 output reg front_buffer,front_valid,output reg pattern_enable,
 output wire pixel_valid,input wire pixel_ready,
 output wire [23:0] pixel_address,output wire [15:0] pixel_rgb565,
 input wire [31:0] scanout_underruns,input wire [31:0]transport_overflows
);
 localparam integer WORDS=(MAX_BYTES+3)/4;
 (* ram_style="block" *) reg [31:0] compressed[0:WORDS-1];
 reg [31:0] frame_id,length,dimensions,expected_crc,active_id;
 reg [31:0] received,complete_frames,decoded_frames,presented_frames,faults,drops,overflows,last_presented;
 reg [31:0] crc,watchdog,pixel_count,transport_seen;
 reg [15:0] first_bytes,last_bytes;
 reg receiving,decoding,fault,pending,draining;
 reg [3:0] decoder_reset_count;
 reg [31:0] read_offset;
 reg [31:0] decoder_data,decoder_ram_data;
 reg decoder_valid,read_wait;
 wire decoder_accept,decoder_out_valid,decoder_idle;
 wire [15:0] dec_width,dec_height,dec_x,dec_y;
 wire [7:0] dec_r,dec_g,dec_b;
 wire decoder_reset=reset || !decoding || decoder_reset_count!=0;
 wire valid_coord=(dec_width==WIDTH && dec_height==HEIGHT && dec_x<WIDTH && dec_y<HEIGHT);
 wire [31:0] remaining=length-read_offset;
 wire [3:0] decoder_strobe=remaining>=4 ? 4'b1111:remaining==3 ? 4'b0111:remaining==2 ? 4'b0011:4'b0001;
 wire ready_state=!receiving && !decoding && !pending && !draining;
 reg a_valid,b_valid,c_valid;
 reg [9:0] ax;reg [8:0] ay,by;reg [18:0] brow,cindex;
 reg aback,bback,cback;reg [15:0] argb,brgb,crgb;
 wire can_c=!c_valid || pixel_ready;
 wire can_b=!b_valid || can_c;
 wire can_a=!a_valid || can_b;
 wire decoder_output_accept=can_a && valid_coord && decoding && !decoder_reset && !draining;
 assign pixel_valid=decoding && !decoder_reset && c_valid && !draining;
 // Three elastic slots isolate decoder coordinates, row multiplication and
 // final addition from the SDRAM arbiter. Every slot holds during a stall.
 assign pixel_address={4'b0,cback,cindex};
 assign pixel_rgb565=crgb;
 always @(posedge clk)begin
  if(decoder_reset || !decoding)begin a_valid<=0;b_valid<=0;c_valid<=0;end
  else begin
   if(can_c)begin
    c_valid<=b_valid;
    if(b_valid)begin cindex<=brow+by;cback<=bback;crgb<=brgb;end
   end
   if(can_b)begin
    b_valid<=a_valid;
    if(a_valid)begin
     //480=512-32, full portrait index fits19 bits for800x480.
     brow<=({9'd0,ax}<<9)-({9'd0,ax}<<5);by<=ay;bback<=aback;brgb<=argb;
    end
   end
   if(can_a)begin
    a_valid<=decoder_out_valid && valid_coord && !draining;
    if(decoder_output_accept)begin ax<=dec_x[9:0]+10'd40;ay<=dec_y[8:0];aback<=!front_buffer;argb<={dec_r[7:3],dec_g[7:2],dec_b[7:3]};end
   end
  end
 end
 function automatic [31:0] crc_byte(input [31:0] previous,input [7:0] datum);
 reg [31:0] v; integer b;
 begin v=previous^{24'd0,datum};for(b=0;b<8;b=b+1)v=v[0] ? ((v>>1)^32'hedb88320):(v>>1);crc_byte=v;end
 endfunction
 always @* begin
  bus_rdata=0;
  case(bus_address)
   'h000:bus_rdata=32'h4d425631;
   'h004:bus_rdata=32'h00010000;
   'h008:bus_rdata=3;
   'h00c:bus_rdata=receiving ? length-received:0;
   'h010:bus_rdata={27'd0,pending,receiving,fault,decoding,ready_state};
   'h014:bus_rdata=frame_id;'h018:bus_rdata=length;'h01c:bus_rdata=dimensions;
   'h020:bus_rdata=expected_crc;'h028:bus_rdata=received;
   'h02c:bus_rdata=complete_frames;'h030:bus_rdata=decoded_frames;
   'h034:bus_rdata=presented_frames;'h038:bus_rdata=faults;'h03c:bus_rdata=drops;
   'h040:bus_rdata=overflows;'h044:bus_rdata=scanout_underruns;
   'h048:bus_rdata=last_presented;'h04c:bus_rdata=MAX_BYTES;
   'h050:bus_rdata=transport_overflows;
   default:bus_rdata=0;
  endcase
 end
 jpeg_core #(.SUPPORT_WRITABLE_DHT(0)) decoder(
  .clk_i(clk),.rst_i(decoder_reset),.inport_valid_i(decoder_valid && !decoder_reset && !draining),
  // This decoder's last_i terminates its byte iterator immediately, rather
  // than marking an AXI final WORD. EOI is the normal JPEG termination; pad
  // unused final-word lanes with zero via strb instead of dropping EOI bytes.
  .inport_data_i(decoder_data),.inport_strb_i(decoder_strobe),.inport_last_i(1'b0),
  .inport_accept_o(decoder_accept),.outport_accept_i(decoder_output_accept),
  .outport_valid_o(decoder_out_valid),.outport_width_o(dec_width),.outport_height_o(dec_height),
  .outport_pixel_x_o(dec_x),.outport_pixel_y_o(dec_y),
  .outport_pixel_r_o(dec_r),.outport_pixel_g_o(dec_g),.outport_pixel_b_o(dec_b),.idle_o(decoder_idle));
 // Inferred true dual-port BRAM: narrow byte write, synchronous32-bit read.
 always @(posedge clk) begin
  if(bus_write && bus_address=='h100 && receiving && received<length && received<MAX_BYTES)
   compressed[received[17:2]][received[1:0]*8+:8]<=bus_wdata[7:0];
  if(decoding && !decoder_reset && !decoder_valid && !read_wait && read_offset<length)
   decoder_ram_data<=compressed[read_offset[17:2]];
 end
 always @(posedge clk) begin
  if(reset) begin
   frame_id<=0;length<=0;dimensions<={16'(WIDTH),16'(HEIGHT)};expected_crc<=0;active_id<=0;
   received<=0;complete_frames<=0;decoded_frames<=0;presented_frames<=0;
   faults<=0;drops<=0;overflows<=0;last_presented<=0;
   crc<=32'hffffffff;watchdog<=0;pixel_count<=0;transport_seen<=0;first_bytes<=0;last_bytes<=0;
   receiving<=0;decoding<=0;fault<=0;pending<=0;draining<=0;
   decoder_reset_count<=0;read_offset<=0;decoder_valid<=0;read_wait<=0;decoder_data<=0;
   front_buffer<=0;front_valid<=0;pattern_enable<=1;
  end else begin
   if(decoding) begin
    if(decoder_reset_count!=0)decoder_reset_count<=decoder_reset_count-1'b1;
    else if(!draining)begin
     watchdog<=watchdog+1;
     if(!decoder_valid && !read_wait && read_offset<length)read_wait<=1;
     if(read_wait)begin decoder_data<=decoder_ram_data;decoder_valid<=1;read_wait<=0;end
     if(decoder_valid && decoder_accept)begin decoder_valid<=0;read_offset<=read_offset+4;end
     if(decoder_out_valid && !valid_coord)begin
      decoding<=0;fault<=1;faults<=faults+1;drops<=drops+1;decoder_valid<=0;
     end
     if(pixel_valid && pixel_ready)begin
      pixel_count<=pixel_count+1;
      if(pixel_count==WIDTH*HEIGHT-1)begin draining<=1;decoder_valid<=0;end
     end
     if(watchdog>=WATCHDOG_CYCLES)begin
      decoding<=0;fault<=1;faults<=faults+1;drops<=drops+1;decoder_valid<=0;
     end
    end
   end
   if(draining && memory_idle)begin
    draining<=0;decoding<=0;pending<=1;decoded_frames<=decoded_frames+1;
   end
   // Candidate abort priority: explicit abort wins over same-cycle publication.
   if(frame_boundary && pending && transport_overflows==transport_seen &&
      !(bus_write && bus_address==12'h024 && bus_wdata[1]))begin
    front_buffer<=!front_buffer;front_valid<=1;pending<=0;pattern_enable<=0;
    presented_frames<=presented_frames+1;last_presented<=active_id;
   end
   if(bus_write)case(bus_address)
    'h014:if(ready_state)frame_id<=bus_wdata;
    'h018:if(ready_state)length<=bus_wdata;
    'h01c:if(ready_state)dimensions<=bus_wdata;
    'h020:if(ready_state)expected_crc<=bus_wdata;
    'h024:begin
     if(bus_wdata[1])begin
      if(receiving || decoding || pending)drops<=drops+1;
      receiving<=0;decoding<=0;draining<=0;pending<=0;fault<=0;decoder_valid<=0;read_wait<=0;
     end else if(bus_wdata[0])begin
      if(ready_state && length!=0 && length<=MAX_BYTES && dimensions=={16'(WIDTH),16'(HEIGHT)})begin
       receiving<=1;fault<=0;received<=0;crc<=32'hffffffff;
       active_id<=frame_id;first_bytes<=0;last_bytes<=0;
      end else begin fault<=1;faults<=faults+1;drops<=drops+1;end
     end else if(bus_wdata[2])begin
      receiving<=0;
      if(receiving && !fault && received==length && (~crc)==expected_crc && first_bytes==16'hffd8 && last_bytes==16'hffd9)begin
       decoding<=1;draining<=0;read_offset<=0;decoder_valid<=0;read_wait<=0;decoder_reset_count<=8;
       complete_frames<=complete_frames+1;watchdog<=0;pixel_count<=0;
      end else begin fault<=1;faults<=faults+1;drops<=drops+1;end
     end else if(bus_wdata[3])pattern_enable<=1;
    end
    'h100:begin
     if(receiving && received<length && received<MAX_BYTES)begin
      received<=received+1;crc<=crc_byte(crc,bus_wdata[7:0]);
      if(received<2)first_bytes<={first_bytes[7:0],bus_wdata[7:0]};
      last_bytes<={last_bytes[7:0],bus_wdata[7:0]};
     end else begin overflows<=overflows+1;fault<=1;end
    end
    default:begin end
   endcase
   // Any lost queued bus word invalidates the transaction, including control
   // traffic whose loss cannot be inferred from the compressed byte count.
   if(transport_overflows!=transport_seen)begin
    transport_seen<=transport_overflows;fault<=1;faults<=faults+1;
    if(receiving || decoding || pending)drops<=drops+1;
    receiving<=0;decoding<=0;draining<=0;pending<=0;decoder_valid<=0;read_wait<=0;
   end
  end
 end
endmodule
`default_nettype wire
