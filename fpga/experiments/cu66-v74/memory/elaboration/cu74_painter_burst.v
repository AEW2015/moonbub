module cu74_painter_burst (
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
	aux_req_read_burst,
	aux_req_burst_data,
	aux_req_byte_enable,
	aux_rsp_valid,
	aux_rsp_ready,
	aux_rsp_data,
	aux_rsp_burst_data,
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
	memory_read_words,
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
	output reg aux_req_read_burst;
	output reg [127:0] aux_req_burst_data;
	output reg [15:0] aux_req_byte_enable;
	input wire aux_rsp_valid;
	output reg aux_rsp_ready;
	input wire [15:0] aux_rsp_data;
	input wire [127:0] aux_rsp_burst_data;
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
	output reg [31:0] memory_read_words;
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
	reg [5:0] load_quad;
	reg [6:0] load_tx;
	reg [1:0] load_chunk;
	reg [2:0] unpack_index;
	reg [127:0] read_data;
	reg [5:0] quad_tag [0:1];
	reg [1:0] quad_valid;
	reg [5:0] stripe_quad;
	reg [2:0] cache_bank;
	reg [8:0] cache_column;
	reg [15:0] cache_word;
	reg [9:0] x;
	reg [9:0] y;
	reg [14:0] bar_index;
	reg [2:0] row_stage;
	reg [15:0] yw0 [0:359];
	reg [15:0] yw1 [0:359];
	reg [15:0] yw2 [0:359];
	reg [15:0] yw3 [0:359];
	reg [15:0] yw4 [0:359];
	reg [15:0] yw5 [0:359];
	reg [15:0] yw6 [0:359];
	reg [15:0] yw7 [0:359];
	reg [15:0] cb0 [0:179];
	reg [15:0] cb1 [0:179];
	reg [15:0] cb2 [0:179];
	reg [15:0] cb3 [0:179];
	reg [15:0] cb4 [0:179];
	reg [15:0] cb5 [0:179];
	reg [15:0] cb6 [0:179];
	reg [15:0] cb7 [0:179];
	reg [15:0] cr0 [0:179];
	reg [15:0] cr1 [0:179];
	reg [15:0] cr2 [0:179];
	reg [15:0] cr3 [0:179];
	reg [15:0] cr4 [0:179];
	reg [15:0] cr5 [0:179];
	reg [15:0] cr6 [0:179];
	reg [15:0] cr7 [0:179];
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
	reg [2:0] top_bank;
	reg [2:0] bottom_bank;
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
	function automatic [5:0] sv2v_cast_6;
		input reg [5:0] inp;
		sv2v_cast_6 = inp;
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
	function automatic signed [23:0] sv2v_cast_24_signed;
		input reg signed [23:0] inp;
		sv2v_cast_24_signed = inp;
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
		top_bank = cy[2:0];
		bottom_bank = (cy == 239 ? cy[2:0] : cy[2:0] + 3'd1);
		stripe_quad = sv2v_cast_6(y >> 3);
		cache_bank = (load_kind == 0 ? {load_chunk, 1'b0} + (unpack_index >> 32'sd2) : ({load_quad[0], 2'b00} + {1'b0, load_chunk[0], 1'b0}) + (unpack_index >> 32'sd2));
		cache_column = (sv2v_cast_9(load_tx) * 9'd4) + sv2v_cast_9(unpack_index[1:0]);
		cache_word = read_data[16 * sv2v_cast_32_signed(unpack_index)+:16];
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
		aux_req_addr = write_addr;
		if (!aux_req_write) begin
			if (load_kind == 3)
				aux_req_addr = load_base;
			else if (load_kind == 0)
				aux_req_addr = load_base + sv2v_cast_24_signed(((((sv2v_cast_32_signed(y) >> 3) * 90) + sv2v_cast_32_signed(load_tx)) * 32) + (sv2v_cast_32_signed(load_chunk) * 8));
			else
				aux_req_addr = load_base + sv2v_cast_24_signed((((((sv2v_cast_32_signed(load_quad) >> 1) * 45) + sv2v_cast_32_signed(load_tx)) * 32) + (sv2v_cast_32_signed(load_quad[0]) * 16)) + (sv2v_cast_32_signed(load_chunk) * 8));
		end
		aux_req_data = write_data[15:0];
		aux_req_burst = aux_req_write;
		aux_req_read_burst = state == 5'd3;
		aux_req_burst_data = write_data;
		aux_req_byte_enable = (aux_req_write ? 16'hffff : 16'd0);
		aux_rsp_ready = pending && !rst;
	end
	task automatic load;
		input reg [1:0] kind;
		input reg [5:0] quad;
		input reg [23:0] address;
		input reg [4:0] return_state;
		begin
			load_kind <= kind;
			load_quad <= quad;
			load_base <= address;
			load_tx <= 0;
			load_chunk <= 0;
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
			load_quad <= 0;
			load_tx <= 0;
			load_chunk <= 0;
			unpack_index <= 0;
			read_data <= 0;
			quad_valid <= 0;
			quad_tag[0] <= 0;
			quad_tag[1] <= 0;
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
			memory_read_words <= 0;
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
				else begin
					memory_reads <= memory_reads + 1;
					memory_read_words <= memory_read_words + 8;
				end
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
							memory_read_words <= 0;
							memory_writes <= 0;
							memory_write_words <= 0;
							painted_pixels <= 0;
							cycle_count <= 0;
							error <= 0;
							error_code <= 0;
							hud_cache_valid <= 0;
							quad_valid <= 0;
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
								if (y[2:0] == 0)
									load(0, 0, yb, 5'd2);
							end
							1: begin
								row_stage <= 2;
								if ((y[2:0] == 0) && (!quad_valid[stripe_quad[0]] || (quad_tag[stripe_quad[0]] != stripe_quad)))
									load(1, stripe_quad, ub, 5'd2);
							end
							2: begin
								row_stage <= 3;
								if ((y[2:0] == 0) && (!quad_valid[stripe_quad[0]] || (quad_tag[stripe_quad[0]] != stripe_quad)))
									load(2, stripe_quad, vb, 5'd2);
							end
							3: begin
								row_stage <= 4;
								if (((y[2:0] == 0) && (stripe_quad < 59)) && (!quad_valid[!stripe_quad[0]] || (quad_tag[!stripe_quad[0]] != (stripe_quad + 1))))
									load(1, stripe_quad + 1, ub, 5'd2);
							end
							4: begin
								row_stage <= 5;
								if (((y[2:0] == 0) && (stripe_quad < 59)) && (!quad_valid[!stripe_quad[0]] || (quad_tag[!stripe_quad[0]] != (stripe_quad + 1))))
									load(2, stripe_quad + 1, vb, 5'd2);
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
							read_data <= aux_rsp_burst_data;
							unpack_index <= 0;
							state <= 5'd14;
						end
					5'd14: begin
						case (load_kind)
							0:
								case (cache_bank)
									3'd0: yw0[cache_column] <= cache_word;
									3'd1: yw1[cache_column] <= cache_word;
									3'd2: yw2[cache_column] <= cache_word;
									3'd3: yw3[cache_column] <= cache_word;
									3'd4: yw4[cache_column] <= cache_word;
									3'd5: yw5[cache_column] <= cache_word;
									3'd6: yw6[cache_column] <= cache_word;
									3'd7: yw7[cache_column] <= cache_word;
								endcase
							1:
								case (cache_bank)
									3'd0: cb0[cache_column[7:0]] <= cache_word;
									3'd1: cb1[cache_column[7:0]] <= cache_word;
									3'd2: cb2[cache_column[7:0]] <= cache_word;
									3'd3: cb3[cache_column[7:0]] <= cache_word;
									3'd4: cb4[cache_column[7:0]] <= cache_word;
									3'd5: cb5[cache_column[7:0]] <= cache_word;
									3'd6: cb6[cache_column[7:0]] <= cache_word;
									3'd7: cb7[cache_column[7:0]] <= cache_word;
								endcase
							2:
								case (cache_bank)
									3'd0: cr0[cache_column[7:0]] <= cache_word;
									3'd1: cr1[cache_column[7:0]] <= cache_word;
									3'd2: cr2[cache_column[7:0]] <= cache_word;
									3'd3: cr3[cache_column[7:0]] <= cache_word;
									3'd4: cr4[cache_column[7:0]] <= cache_word;
									3'd5: cr5[cache_column[7:0]] <= cache_word;
									3'd6: cr6[cache_column[7:0]] <= cache_word;
									3'd7: cr7[cache_column[7:0]] <= cache_word;
								endcase
							3: hud_words[unpack_index] <= cache_word;
						endcase
						if (unpack_index != 7)
							unpack_index <= unpack_index + 1;
						else if (load_kind == 3) begin
							hud_cache_tag <= load_base;
							hud_cache_valid <= 1;
							state <= after_load;
						end
						else if (((load_kind == 0) && (load_chunk == 3)) || ((load_kind != 0) && (load_chunk == 1))) begin
							load_chunk <= 0;
							if (((load_kind == 0) && (load_tx == 89)) || ((load_kind != 0) && (load_tx == 44))) begin
								if (load_kind == 2) begin
									quad_tag[load_quad[0]] <= load_quad;
									quad_valid[load_quad[0]] <= 1;
								end
								state <= after_load;
							end
							else begin
								load_tx <= load_tx + 1;
								state <= 5'd3;
							end
						end
						else begin
							load_chunk <= load_chunk + 1;
							state <= 5'd3;
						end
					end
					5'd5: begin
						case (y[2:0])
							3'd0: ys <= yw0[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
							3'd1: ys <= yw1[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
							3'd2: ys <= yw2[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
							3'd3: ys <= yw3[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
							3'd4: ys <= yw4[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
							3'd5: ys <= yw5[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
							3'd6: ys <= yw6[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
							3'd7: ys <= yw7[x[9:1]][8 * sv2v_cast_32_signed(x[0])+:8];
						endcase
						case (top_bank)
							3'd0: begin
								ct0 <= cb0[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								ct1 <= cb0[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rt0 <= cr0[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rt1 <= cr0[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd1: begin
								ct0 <= cb1[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								ct1 <= cb1[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rt0 <= cr1[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rt1 <= cr1[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd2: begin
								ct0 <= cb2[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								ct1 <= cb2[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rt0 <= cr2[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rt1 <= cr2[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd3: begin
								ct0 <= cb3[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								ct1 <= cb3[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rt0 <= cr3[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rt1 <= cr3[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd4: begin
								ct0 <= cb4[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								ct1 <= cb4[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rt0 <= cr4[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rt1 <= cr4[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd5: begin
								ct0 <= cb5[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								ct1 <= cb5[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rt0 <= cr5[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rt1 <= cr5[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd6: begin
								ct0 <= cb6[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								ct1 <= cb6[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rt0 <= cr6[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rt1 <= cr6[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd7: begin
								ct0 <= cb7[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								ct1 <= cb7[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rt0 <= cr7[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rt1 <= cr7[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
						endcase
						case (bottom_bank)
							3'd0: begin
								cb0s <= cb0[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								cb1s <= cb0[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rb0s <= cr0[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rb1s <= cr0[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd1: begin
								cb0s <= cb1[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								cb1s <= cb1[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rb0s <= cr1[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rb1s <= cr1[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd2: begin
								cb0s <= cb2[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								cb1s <= cb2[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rb0s <= cr2[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rb1s <= cr2[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd3: begin
								cb0s <= cb3[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								cb1s <= cb3[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rb0s <= cr3[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rb1s <= cr3[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd4: begin
								cb0s <= cb4[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								cb1s <= cb4[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rb0s <= cr4[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rb1s <= cr4[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd5: begin
								cb0s <= cb5[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								cb1s <= cb5[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rb0s <= cr5[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rb1s <= cr5[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd6: begin
								cb0s <= cb6[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								cb1s <= cb6[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rb0s <= cr6[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rb1s <= cr6[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
							3'd7: begin
								cb0s <= cb7[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								cb1s <= cb7[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
								rb0s <= cr7[cx[8:1]][8 * sv2v_cast_32_signed(cx[0])+:8];
								rb1s <= cr7[cx1[8:1]][8 * sv2v_cast_32_signed(cx1[0])+:8];
							end
						endcase
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
							load(3, 0, {hud_address[23:3], 3'b000}, 5'd7);
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