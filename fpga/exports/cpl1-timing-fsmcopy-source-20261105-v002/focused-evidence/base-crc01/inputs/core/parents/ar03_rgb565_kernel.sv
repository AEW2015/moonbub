// SPDX-License-Identifier: GPL-3.0-or-later
// Isolated arithmetic seam, matching Sunshine c9c0bf4 body::render565.
// No memory, framebuffer, scanout, publication, network, or hardware clock claim.
module ar03_rgb565_kernel #(parameter integer TAG_WIDTH = 160) (
    input wire clk, input wire rst, input wire abort,
    input wire in_valid, output wire in_ready,
    input wire [7:0] in_y,
    input wire [7:0] cb00, cb10, cb01, cb11,
    input wire [7:0] cr00, cr10, cr01, cr11,
    input wire [11:0] in_x, in_row, in_width, in_height,
    input wire [TAG_WIDTH-1:0] in_tag,
    output wire out_valid, input wire out_ready,
    output wire [15:0] out_rgb565,
    output wire [11:0] out_x, out_row, out_width, out_height,
    output wire [TAG_WIDTH-1:0] out_tag,
    output wire out_error
);
    reg [3:0] valid;
    wire [3:0] ready;
    reg [TAG_WIDTH+47:0] meta [0:3];
    reg [3:0] error;
    reg [7:0] y0, y1, y2;
    reg [7:0] cb_top, cb_bottom, cr_top, cr_bottom;
    reg signed [8:0] cb_centered, cr_centered;
    reg signed [18:0] red_sum, green_sum, blue_sum;
    reg [15:0] rgb;
    wire live = !rst && !abort;
    assign ready[3] = !valid[3] || out_ready;
    assign ready[2] = !valid[2] || ready[3];
    assign ready[1] = !valid[1] || ready[2];
    assign ready[0] = !valid[0] || ready[1];
    assign in_ready = ready[0] && live;
    assign out_valid = valid[3] && live;
    assign out_rgb565 = rgb;
    assign {out_tag,out_x,out_row,out_width,out_height} = meta[3];
    assign out_error = error[3];
    wire right_edge = (in_x >> 1) == ((in_width >> 1) - 1);
    wire bottom_edge = (in_row >> 1) == ((in_height >> 1) - 1);
    wire bad_geometry = in_width < 2 || in_height < 2 ||
        in_width > 2048 || in_height > 2048 || in_width[0] || in_height[0] ||
        (in_width * in_height > 32'd345600) ||
        in_x >= in_width || in_row >= in_height;

    function automatic [7:0] half_up(input [7:0] a, b);
        reg [8:0] sum;
        begin sum = {1'b0,a} + {1'b0,b} + 9'd1; half_up = sum[8:1]; end
    endfunction
    function automatic [7:0] clamp8(input signed [18:0] value);
        begin
            if (value < 0) clamp8 = 0;
            else if (value > 255) clamp8 = 255;
            else clamp8 = value[7:0];
        end
    endfunction
    // Arithmetic shift is signed floor division, including negative biased sums.
    wire signed [18:0] r_final = $signed({1'b0,y2}) + (red_sum >>> 8);
    wire signed [18:0] g_final = $signed({1'b0,y2}) - (green_sum >>> 8);
    wire signed [18:0] b_final = $signed({1'b0,y2}) + (blue_sum >>> 8);
    wire [7:0] r8 = clamp8(r_final), g8 = clamp8(g_final), b8 = clamp8(b_final);
    always @(posedge clk) begin
        if (rst || abort) begin
            valid <= 0;
            error <= 0;
        end else begin
            if (ready[0]) begin
                valid[0] <= in_valid;
                if (in_valid) begin
                    meta[0] <= {in_tag,in_x,in_row,in_width,in_height};
                    error[0] <= bad_geometry;
                    y0 <= in_y;
                    cb_top <= in_x[0] ? half_up(cb00,right_edge ? cb00 : cb10) : cb00;
                    cb_bottom <= bottom_edge ?
                        (in_x[0] ? half_up(cb00,right_edge ? cb00 : cb10) : cb00) :
                        (in_x[0] ? half_up(cb01,right_edge ? cb01 : cb11) : cb01);
                    cr_top <= in_x[0] ? half_up(cr00,right_edge ? cr00 : cr10) : cr00;
                    cr_bottom <= bottom_edge ?
                        (in_x[0] ? half_up(cr00,right_edge ? cr00 : cr10) : cr00) :
                        (in_x[0] ? half_up(cr01,right_edge ? cr01 : cr11) : cr01);
                end
            end
            if (ready[1]) begin
                valid[1] <= valid[0];
                if (valid[0]) begin
                    meta[1] <= meta[0]; error[1] <= error[0]; y1 <= y0;
                    cb_centered <= $signed({1'b0,(meta[0][24] ? half_up(cb_top,cb_bottom) : cb_top)}) - 9'sd128;
                    cr_centered <= $signed({1'b0,(meta[0][24] ? half_up(cr_top,cr_bottom) : cr_top)}) - 9'sd128;
                end
            end
            if (ready[2]) begin
                valid[2] <= valid[1];
                if (valid[1]) begin
                    meta[2] <= meta[1]; error[2] <= error[1]; y2 <= y1;
                    red_sum <= 19'sd359 * cr_centered + 19'sd128;
                    green_sum <= 19'sd88 * cb_centered + 19'sd183 * cr_centered + 19'sd128;
                    blue_sum <= 19'sd454 * cb_centered + 19'sd128;
                end
            end
            if (ready[3]) begin
                valid[3] <= valid[2];
                if (valid[2]) begin
                    meta[3] <= meta[2]; error[3] <= error[2];
                    rgb <= error[2] ? 16'b0 : {r8[7:3],g8[7:2],b8[7:3]};
                end
            end
        end
    end
endmodule
