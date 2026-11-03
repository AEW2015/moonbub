`timescale 1ns/1ps
// Rev4 stock ESP32 overlay, independent of the tester's SDRAM/SRAM and CPU.
// Native panel coordinates are 480x800; landscape = (in_y,in_x).
// HandheldTop Rev4 places its 360x240 image at landscape (12,0), scale 2.
// Its DPI path ignores overlay X/Y control registers; preserve that behavior.
// ov_data is already byte-swapped by the protocol endpoint: ARGB1555.
// Three registered pixel stages, including synchronous BRAM read. All syncs,
// DE and base RGB follow the same delay. Place after the app color conversion.
// Dual-clock same-address read/write is intentionally not atomic (stock also
// updates its single buffer live); a pixel can show old/new data during update.
module esp32_overlay #(
    parameter integer TESTER_THEME = 0
)(
    input wire sys_clk, sys_rst_n,
    input wire ov_wr,
    input wire [17:0] ov_addr,
    input wire [15:0] ov_data,
    input wire pixel_clk, pixel_rst_n,
    input wire [9:0] in_x, in_y,
    input wire in_hs, in_vs, in_de,
    input wire [23:0] in_rgb,
    output reg out_hs=0, out_vs=0, out_de=0,
    output reg [23:0] out_rgb=0,
    // Pixel-clock-domain conservative ownership hint, not a menu-type decode.
    // Assert as soon as an opaque pixel is scanned; release only after an
    // entire transparent frame. The consumer must synchronize this one bit.
    output wire overlay_visible
);
    localparam integer PIXELS = 360*240;
    (* ram_style="block" *) reg [15:0] pixels[0:PIXELS-1];
    integer i;
    // Keep the loop below Vivado's default 65536-iteration elaboration limit.
    initial for(i=0;i<PIXELS/2;i=i+1) begin
        pixels[i]=16'h0000;
        pixels[i+PIXELS/2]=16'h0000;
    end
    // No RAM reset loop: configuration initializes transparent, CPU/pixel reset
    // preserves the ESP32-owned framebuffer. Invalid offsets cannot alias it.
    always @(posedge sys_clk)
        if(sys_rst_n && ov_wr && !ov_addr[0] && ov_addr[17:1]<PIXELS)
            pixels[ov_addr[17:1]]<=ov_data;

    wire coordinate_valid = in_x<480 && in_y>=12 && in_y<732;
    wire [8:0] row = in_x[9:1];
    wire [9:0] landscape_relative = in_y-10'd12;
    wire [8:0] column = landscape_relative[9:1];
    // Explicit 17-bit shift/add constant multiplication avoids a DSP dependency.
    wire [16:0] row_extended = {8'b0,row};
    wire [16:0] address = (row_extended<<8)+(row_extended<<6)+
                         (row_extended<<5)+(row_extended<<3)+{8'b0,column};
    reg [16:0] read_address=0;
    reg [15:0] read_pixel;
    reg valid_1=0,valid_2=0;
    reg [26:0] base_1=0,base_2=0;
    // A plain synchronous read is important for block RAM inference.
    always @(posedge pixel_clk) read_pixel<=pixels[read_address];

    function automatic [23:0] expand_color(input [14:0] c);
        begin
            expand_color={c[14:10],c[14:12],c[9:5],c[9:7],c[4:0],c[4:2]};
            // Monotonic neutral-ramp inversion: stock white chrome becomes
            // tester dark blue (0c1b27), black text becomes pale (e9f2fa).
            // Interpolated intermediate grays preserve antialiased text edges.
            // Colored status/error/gamma assets and alpha remain unchanged.
            if(TESTER_THEME && c[14:10]==c[9:5] && c[9:5]==c[4:0]) begin
                case(c[14:10])
                    5'd0:expand_color=24'he9f2fa;
                    5'd1:expand_color=24'he2ebf3;
                    5'd2:expand_color=24'hdbe4ec;
                    5'd3:expand_color=24'hd4dde6;
                    5'd4:expand_color=24'hccd6df;
                    5'd5:expand_color=24'hc5cfd8;
                    5'd6:expand_color=24'hbec8d1;
                    5'd7:expand_color=24'hb7c1ca;
                    5'd8:expand_color=24'hb0bbc4;
                    5'd9:expand_color=24'ha9b4bd;
                    5'd10:expand_color=24'ha2adb6;
                    5'd11:expand_color=24'h9ba6af;
                    5'd12:expand_color=24'h939fa8;
                    5'd13:expand_color=24'h8c98a2;
                    5'd14:expand_color=24'h85919b;
                    5'd15:expand_color=24'h7e8a94;
                    5'd16:expand_color=24'h77838d;
                    5'd17:expand_color=24'h707c86;
                    5'd18:expand_color=24'h69757f;
                    5'd19:expand_color=24'h626e79;
                    5'd20:expand_color=24'h5a6772;
                    5'd21:expand_color=24'h53606b;
                    5'd22:expand_color=24'h4c5964;
                    5'd23:expand_color=24'h45525d;
                    5'd24:expand_color=24'h3e4c57;
                    5'd25:expand_color=24'h374550;
                    5'd26:expand_color=24'h303e49;
                    5'd27:expand_color=24'h293742;
                    5'd28:expand_color=24'h21303b;
                    5'd29:expand_color=24'h1a2935;
                    5'd30:expand_color=24'h13222e;
                    5'd31:expand_color=24'h0c1b27;
                endcase
            end
        end
    endfunction

    reg frame_opaque=0,previous_frame_opaque=0,previous_vs=0;
    wire chosen = valid_2 && base_2[24] && read_pixel[15];
    assign overlay_visible=frame_opaque|previous_frame_opaque;
    always @(posedge pixel_clk) begin
        if(!pixel_rst_n) begin
            read_address<=0;valid_1<=0;valid_2<=0;base_1<=0;base_2<=0;
            out_hs<=0;out_vs<=0;out_de<=0;out_rgb<=0;
            frame_opaque<=0;previous_frame_opaque<=0;previous_vs<=0;
        end else begin
            read_address<=coordinate_valid ? address : 17'd0;
            valid_1<=coordinate_valid;valid_2<=valid_1;
            base_1<={in_hs,in_vs,in_de,in_rgb};base_2<=base_1;
            {out_hs,out_vs,out_de}<=base_2[26:24];
            out_rgb<=base_2[24] ? (chosen ? expand_color(read_pixel[14:0]) : base_2[23:0]) : 24'd0;
            previous_vs<=base_2[25];
            if(base_2[25] && !previous_vs) begin
                previous_frame_opaque<=frame_opaque;
                frame_opaque<=chosen;
            end else if(chosen) frame_opaque<=1;
        end
    end
endmodule
