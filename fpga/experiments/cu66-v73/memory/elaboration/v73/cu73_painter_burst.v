module cu73_painter_burst (
	clk,
	rst,
	abort_i,
	start_valid,
	start_ready,
	generation,
	frame_id,
	y_base,
	u_base,
	v_base,
	hud_base,
	rgb_base,
	aux_req_valid,
	aux_req_ready,
	aux_req_write,
	aux_req_addr,
	aux_req_data,
	aux_req_burst,
	aux_req_burst_data,
	aux_req_byte_enable,
	aux_rsp_valid,
	aux_rsp_ready,
	aux_rsp_data,
	aux_rsp_error,
	result_valid,
	result_ready,
	result_generation,
	result_frame_id,
	busy,
	done,
	aborted,
	error,
	error_code,
	memory_reads,
	memory_writes,
	memory_write_words,
	painted_pixels,
	cycle_count
);
	reg _sv2v_0;
	input wire clk;
	input wire rst;
	input wire abort_i;
	input wire start_valid;
	output reg start_ready;
	input wire [63:0] generation;
	input wire [31:0] frame_id;
	input wire [23:0] y_base;
	input wire [23:0] u_base;
	input wire [23:0] v_base;
	input wire [23:0] hud_base;
	input wire [23:0] rgb_base;
	output reg aux_req_valid;
	input wire aux_req_ready;
	output reg aux_req_write;
	output reg [23:0] aux_req_addr;
	output reg [15:0] aux_req_data;
	output reg aux_req_burst;
	output reg [127:0] aux_req_burst_data;
	output reg [15:0] aux_req_byte_enable;
	input wire aux_rsp_valid;
	output reg aux_rsp_ready;
	input wire [15:0] aux_rsp_data;
	input wire aux_rsp_error;
	output reg result_valid;
	input wire result_ready;
	output reg [63:0] result_generation;
	output reg [31:0] result_frame_id;
	output reg busy;
	output reg done;
	output reg aborted;
	output reg error;
	output reg [7:0] error_code;
	output reg [31:0] memory_reads;
	output reg [31:0] memory_writes;
	output reg [31:0] memory_write_words;
	output reg [31:0] painted_pixels;
	output reg [31:0] cycle_count;
	reg [4:0] state;
	reg [4:0] after_load;
	reg [4:0] after_write;
	reg [23:0] yb;
	reg [23:0] ub;
	reg [23:0] vb;
	reg [23:0] hb;
	reg [23:0] rb;
	reg [23:0] load_base;
	reg [23:0] write_addr;
	reg [127:0] write_data;
	reg [1:0] load_kind;
	reg load_bank;
	reg [8:0] load_index;
	reg [8:0] load_words;
	reg [9:0] x;
	reg [9:0] y;
	reg [14:0] bar_index;
	reg [2:0] row_stage;
	reg [15:0] y_words [0:359];
	reg [15:0] cb0 [0:179];
	reg [15:0] cb1 [0:179];
	reg [15:0] cr0 [0:179];
	reg [15:0] cr1 [0:179];
	reg [15:0] hud_words [0:7];
	reg [15:0] strip0 [0:719];
	reg [15:0] strip1 [0:719];
	reg [15:0] strip2 [0:719];
	reg [15:0] strip3 [0:719];
	reg [15:0] strip4 [0:719];
	reg [15:0] strip5 [0:719];
	reg [15:0] strip6 [0:719];
	reg [15:0] strip7 [0:719];
	reg [9:0] drain_x;
	reg [8:0] strip_y;
	reg [23:0] hud_cache_tag;
	reg hud_cache_valid;
	reg pending;
	reg [7:0] ys;
	reg [7:0] ct0;
	reg [7:0] ct1;
	reg [7:0] cb0s;
	reg [7:0] cb1s;
	reg [7:0] rt0;
	reg [7:0] rt1;
	reg [7:0] rb0s;
	reg [7:0] rb1s;
	reg [8:0] cx;
	reg [8:0] cx1;
	reg [7:0] cy;
	reg top_bank;
	reg bottom_bank;
	reg hud_hit;
	reg [14:0] hud_index;
	reg [23:0] hud_address;
	reg signed [31:0] cb_top;
	reg signed [31:0] cb_bottom;
	reg signed [31:0] cr_top;
	reg signed [31:0] cr_bottom;
	reg signed [31:0] cb;
	reg signed [31:0] cr;
	reg signed [31:0] rr;
	reg signed [31:0] gg;
	reg signed [31:0] bb;
	reg [15:0] converted;
	function automatic ranges_overlap;
		input reg [23:0] a;
		input reg [24:0] an;
		input reg [23:0] b;
		input reg [24:0] bn;
		ranges_overlap = ({1'b0, a} < ({1'b0, b} + bn)) && ({1'b0, b} < ({1'b0, a} + an));
	endfunction
	function automatic [7:0] clip;
		input reg signed [31:0] n;
		if (n < 0)
			clip = 0;
		else if (n > 255)
			clip = 255;
		else
			clip = n[7:0];
	endfunction
	function automatic [8:0] sv2v_cast_9;
		input reg [8:0] inp;
		sv2v_cast_9 = inp;
	endfunction
	function automatic [7:0] sv2v_cast_8;
		input reg [7:0] inp;
		sv2v_cast_8 = inp;
	endfunction
	function automatic signed [14:0] sv2v_cast_15_signed;
		input reg signed [14:0] inp;
		sv2v_cast_15_signed = inp;
	endfunction
	function automatic [23:0] sv2v_cast_24;
		input reg [23:0] inp;
		sv2v_cast_24 = inp;
	endfunction
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [4:0] sv2v_cast_5;
		input reg [4:0] inp;
		sv2v_cast_5 = inp;
	endfunction
	function automatic [5:0] sv2v_cast_6;
		input reg [5:0] inp;
		sv2v_cast_6 = inp;
	endfunction
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	always @(*) begin
		if (_sv2v_0)
			;
		cx = sv2v_cast_9(x >> 1);
		cx1 = (cx == 359 ? cx : cx + 1);
		cy = sv2v_cast_8(y >> 1);
		top_bank = cy[0];
		bottom_bank = (cy == 239 ? cy[0] : !cy[0]);
		hud_hit = 0;
		hud_index = 0;
		if ((((x >= 22) && (x < 182)) && (y >= 54)) && (y < 78)) begin
			hud_hit = 1;
			hud_index = sv2v_cast_15_signed((((sv2v_cast_32_signed(y) - 54) * 160) + sv2v_cast_32_signed(x)) - 22);
		end
		else if ((((x >= 22) && (x < 182)) && (y >= 82)) && (y < 106)) begin
			hud_hit = 1;
			hud_index = sv2v_cast_15_signed(((3840 + ((sv2v_cast_32_signed(y) - 82) * 160)) + sv2v_cast_32_signed(x)) - 22);
		end
		else if ((((x >= 168) && (x < 488)) && (y >= 360)) && (y < 384)) begin
			hud_hit = 1;
			hud_index = sv2v_cast_15_signed(((7680 + ((sv2v_cast_32_signed(y) - 360) * 320)) + sv2v_cast_32_signed(x)) - 168);
		end
		else if ((((x >= 168) && (x < 408)) && (y >= 390)) && (y < 414)) begin
			hud_hit = 1;
			hud_index = sv2v_cast_15_signed(((15360 + ((sv2v_cast_32_signed(y) - 390) * 240)) + sv2v_cast_32_signed(x)) - 168);
		end
		hud_address = hb + sv2v_cast_24(hud_index);
		cb_top = (x[0] ? ((sv2v_cast_32(ct0) + sv2v_cast_32(ct1)) + 1) >> 1 : sv2v_cast_32(ct0));
		cb_bottom = (x[0] ? ((sv2v_cast_32(cb0s) + sv2v_cast_32(cb1s)) + 1) >> 1 : sv2v_cast_32(cb0s));
		cr_top = (x[0] ? ((sv2v_cast_32(rt0) + sv2v_cast_32(rt1)) + 1) >> 1 : sv2v_cast_32(rt0));
		cr_bottom = (x[0] ? ((sv2v_cast_32(rb0s) + sv2v_cast_32(rb1s)) + 1) >> 1 : sv2v_cast_32(rb0s));
		cb = (y[0] ? ((cb_top + cb_bottom) + 1) >>> 1 : cb_top) - 128;
		cr = (y[0] ? ((cr_top + cr_bottom) + 1) >>> 1 : cr_top) - 128;
		rr = $signed({24'd0, ys}) + (((359 * cr) + 128) >>> 8);
		gg = $signed({24'd0, ys}) - ((((88 * cb) + (183 * cr)) + 128) >>> 8);
		bb = $signed({24'd0, ys}) + (((454 * cb) + 128) >>> 8);
		converted = {sv2v_cast_5(clip(rr) >> 3), sv2v_cast_6(clip(gg) >> 2), sv2v_cast_5(clip(bb) >> 3)};
		start_ready = ((state == 5'd0) && !rst) && !abort_i;
		busy = state != 5'd0;
		result_valid = ((state == 5'd11) && !rst) && !abort_i;
		aux_req_valid = (((state == 5'd3) || (state == 5'd8)) && !rst) && !abort_i;
		aux_req_write = state == 5'd8;
		aux_req_addr = (aux_req_write ? write_addr : load_base + sv2v_cast_24(load_index));
		aux_req_data = write_data[15:0];
		aux_req_burst = aux_req_write;
		aux_req_burst_data = write_data;
		aux_req_byte_enable = (aux_req_write ? 16'hffff : 16'd0);
		aux_rsp_ready = pending && !rst;
	end
	task automatic load;
		input reg [1:0] kind;
		input reg bank;
		input reg [23:0] address;
		input reg [8:0] words;
		input reg [4:0] return_state;
		begin
			load_kind <= kind;
			load_bank <= bank;
			load_base <= address;
			load_words <= words;
			load_index <= 0;
			after_load <= return_state;
			state <= 5'd3;
		end
	endtask
	task automatic write_burst;
		input reg [23:0] address;
		input reg [127:0] data;
		input reg [4:0] return_state;
		begin
			write_addr <= address;
			write_data <= data;
			after_write <= return_state;
			state <= 5'd8;
		end
	endtask
	task automatic emit_pixel;
		input reg [15:0] data;
		begin
			case (y[2:0])
				3'd0: strip0[x] <= data;
				3'd1: strip1[x] <= data;
				3'd2: strip2[x] <= data;
				3'd3: strip3[x] <= data;
				3'd4: strip4[x] <= data;
				3'd5: strip5[x] <= data;
				3'd6: strip6[x] <= data;
				3'd7: strip7[x] <= data;
			endcase
			painted_pixels <= painted_pixels + 1;
			if (x == 719) begin
				x <= 0;
				y <= y + 1;
				if (y[2:0] == 7) begin
					strip_y <= y[8:0] - 9'd7;
					drain_x <= 0;
					state <= 5'd13;
				end
				else
					state <= 5'd2;
			end
			else begin
				x <= x + 1;
				state <= 5'd5;
			end
		end
	endtask
	function automatic signed [23:0] sv2v_cast_24_signed;
		input reg signed [23:0] inp;
		sv2v_cast_24_signed = inp;
	endfunction
	always @(posedge clk)
		if (rst) begin
			state <= 5'd0;
			after_load <= 5'd0;
			after_write <= 5'd0;
			pending <= 0;
			drain_x <= 0;
			strip_y <= 0;
			yb <= 0;
			ub <= 0;
			vb <= 0;
			hb <= 0;
			rb <= 0;
			load_base <= 0;
			write_addr <= 0;
			write_data <= 0;
			load_kind <= 0;
			load_bank <= 0;
			load_index <= 0;
			load_words <= 0;
			x <= 0;
			y <= 0;
			bar_index <= 0;
			row_stage <= 0;
			hud_cache_tag <= 0;
			hud_cache_valid <= 0;
			ys <= 0;
			ct0 <= 0;
			ct1 <= 0;
			cb0s <= 0;
			cb1s <= 0;
			rt0 <= 0;
			rt1 <= 0;
			rb0s <= 0;
			rb1s <= 0;
			result_generation <= 0;
			result_frame_id <= 0;
			done <= 0;
			aborted <= 0;
			error <= 0;
			error_code <= 0;
			memory_reads <= 0;
			memory_writes <= 0;
			memory_write_words <= 0;
			painted_pixels <= 0;
			cycle_count <= 0;
		end
		else begin
			done <= 0;
			aborted <= 0;
			if (busy)
				cycle_count <= cycle_count + 1;
			if (aux_req_valid && aux_req_ready) begin
				pending <= 1;
				if (aux_req_write) begin
					memory_writes <= memory_writes + 1;
					memory_write_words <= memory_write_words + 8;
				end
				else
					memory_reads <= memory_reads + 1;
			end
			if (aux_rsp_valid && aux_rsp_ready)
				pending <= 0;
			if ((abort_i && (state != 5'd0)) && (state != 5'd12))
				state <= 5'd12;
			else if (((aux_rsp_valid && aux_rsp_ready) && aux_rsp_error) && (state != 5'd12)) begin
				state <= 5'd12;
				error <= 1;
				error_code <= 8'd2;
			end
			else
				case (state)
					5'd0:
						if (start_valid && start_ready) begin
							result_generation <= generation;
							result_frame_id <= frame_id;
							memory_reads <= 0;
							memory_writes <= 0;
							memory_write_words <= 0;
							painted_pixels <= 0;
							cycle_count <= 0;
							error <= 0;
							error_code <= 0;
							hud_cache_valid <= 0;
							x <= 0;
							y <= 0;
							bar_index <= 0;
							row_stage <= 0;
							yb <= y_base;
							ub <= u_base;
							vb <= v_base;
							hb <= hud_base;
							rb <= rgb_base;
							if ((((((((((((((((((generation == 0) || (frame_id == 32'hffffffff)) || (rgb_base[2:0] != 0)) || (({1'b0, y_base} + 25'd172800) > 25'h1000000)) || (({1'b0, u_base} + 25'd43200) > 25'h1000000)) || (({1'b0, v_base} + 25'd43200) > 25'h1000000)) || (({1'b0, hud_base} + 25'd21120) > 25'h1000000)) || (({1'b0, rgb_base} + 25'd384000) > 25'h1000000)) || ranges_overlap(y_base, 25'd172800, u_base, 25'd43200)) || ranges_overlap(y_base, 25'd172800, v_base, 25'd43200)) || ranges_overlap(y_base, 25'd172800, hud_base, 25'd21120)) || ranges_overlap(y_base, 25'd172800, rgb_base, 25'd384000)) || ranges_overlap(u_base, 25'd43200, v_base, 25'd43200)) || ranges_overlap(u_base, 25'd43200, hud_base, 25'd21120)) || ranges_overlap(u_base, 25'd43200, rgb_base, 25'd384000)) || ranges_overlap(v_base, 25'd43200, hud_base, 25'd21120)) || ranges_overlap(v_base, 25'd43200, rgb_base, 25'd384000)) || ranges_overlap(hud_base, 25'd21120, rgb_base, 25'd384000)) begin
								error <= 1;
								error_code <= 1;
								state <= 5'd12;
							end
							else
								state <= 5'd1;
						end
					5'd1: begin
						write_burst(rb + sv2v_cast_24(bar_index), 128'd0, 5'd1);
						if (bar_index == 19192) begin
							after_write <= 5'd2;
							bar_index <= 0;
						end
						else
							bar_index <= bar_index + 8;
					end
					5'd2:
						case (row_stage)
							0: begin
								row_stage <= 1;
								load(0, 0, yb + sv2v_cast_24_signed(sv2v_cast_32_signed(y) * 360), 9'd360, 5'd2);
							end
							1: begin
								row_stage <= 2;
								if (y == 0)
									load(1, 0, ub, 9'd180, 5'd2);
								else if (!y[0] && (cy < 239))
									load(1, !cy[0], ub + sv2v_cast_24_signed((sv2v_cast_32_signed(cy) + 1) * 180), 9'd180, 5'd2);
							end
							2: begin
								row_stage <= 3;
								if (y == 0)
									load(2, 0, vb, 9'd180, 5'd2);
								else if (!y[0] && (cy < 239))
									load(2, !cy[0], vb + sv2v_cast_24_signed((sv2v_cast_32_signed(cy) + 1) * 180), 9'd180, 5'd2);
							end
							3: begin
								row_stage <= 4;
								if (y == 0)
									load(1, 1, ub + 24'd180, 9'd180, 5'd2);
							end
							4: begin
								row_stage <= 5;
								if (y == 0)
									load(2, 1, vb + 24'd180, 9'd180, 5'd2);
							end
							default: begin
								row_stage <= 0;
								state <= 5'd5;
							end
						endcase
					5'd3:
						if (aux_req_valid && aux_req_ready)
							state <= 5'd4;
					5'd4:
						if (aux_rsp_valid && aux_rsp_ready) begin
							case (load_kind)
								0: y_words[load_index] <= aux_rsp_data;
								1:
									if (load_bank)
										cb1[load_index[7:0]] <= aux_rsp_data;
									else
										cb0[load_index[7:0]] <= aux_rsp_data;
								2:
									if (load_bank)
										cr1[load_index[7:0]] <= aux_rsp_data;
									else
										cr0[load_index[7:0]] <= aux_rsp_data;
								3: hud_words[load_index[2:0]] <= aux_rsp_data;
							endcase
							if ((load_index + 9'd1) == load_words) begin
								state <= after_load;
								if (load_kind == 3) begin
									hud_cache_tag <= load_base;
									hud_cache_valid <= 1;
								end
							end
							else begin
								load_index <= load_index + 1;
								state <= 5'd3;
							end
						end
					5'd5: begin
						ys <= y_words[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
						ct0 <= (top_bank ? cb1[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8] : cb0[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8]);
						ct1 <= (top_bank ? cb1[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8] : cb0[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8]);
						cb0s <= (bottom_bank ? cb1[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8] : cb0[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8]);
						cb1s <= (bottom_bank ? cb1[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8] : cb0[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8]);
						rt0 <= (top_bank ? cr1[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8] : cr0[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8]);
						rt1 <= (top_bank ? cr1[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8] : cr0[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8]);
						rb0s <= (bottom_bank ? cr1[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8] : cr0[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8]);
						rb1s <= (bottom_bank ? cr1[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8] : cr0[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8]);
						state <= 5'd6;
					end
					5'd6:
						if (hud_hit)
							state <= 5'd7;
						else
							emit_pixel(converted);
					5'd7:
						if (hud_cache_valid && (hud_cache_tag == {hud_address[23:3], 3'b000}))
							emit_pixel(hud_words[hud_address[2:0]]);
						else
							load(3, 0, {hud_address[23:3], 3'b000}, 9'd8, 5'd7);
					5'd13: begin
						write_burst(rb + sv2v_cast_24_signed(((sv2v_cast_32_signed(drain_x) + 40) * 480) + sv2v_cast_32_signed(strip_y)), {strip7[drain_x], strip6[drain_x], strip5[drain_x], strip4[drain_x], strip3[drain_x], strip2[drain_x], strip1[drain_x], strip0[drain_x]}, 5'd13);
						if (drain_x == 719) begin
							bar_index <= 0;
							after_write <= (strip_y == 472 ? 5'd10 : 5'd2);
						end
						else
							drain_x <= drain_x + 1;
					end
					5'd8:
						if (aux_req_valid && aux_req_ready)
							state <= 5'd9;
					5'd9:
						if (aux_rsp_valid && aux_rsp_ready)
							state <= after_write;
					5'd10: begin
						write_burst((rb + 24'd364800) + sv2v_cast_24(bar_index), 128'd0, 5'd10);
						if (bar_index == 19192)
							after_write <= 5'd11;
						else
							bar_index <= bar_index + 8;
					end
					5'd11:
						if (result_valid && result_ready) begin
							done <= 1;
							state <= 5'd0;
						end
					5'd12:
						if (!pending) begin
							aborted <= 1;
							state <= 5'd0;
						end
					default: begin
						state <= 5'd12;
						error <= 1;
						error_code <= 3;
					end
				endcase
		end
	initial _sv2v_0 = 0;
endmodule