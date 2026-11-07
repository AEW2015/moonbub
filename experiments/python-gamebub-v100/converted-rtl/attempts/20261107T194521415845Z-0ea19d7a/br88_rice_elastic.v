module br88_rice_elastic (
	clk,
	reset,
	stream_start,
	stream_bits,
	word16,
	serial_mode,
	in_valid,
	in_ready,
	in_data,
	in_bits,
	in_last,
	req_valid,
	req_ready,
	req_k,
	req_escape,
	out_valid,
	out_ready,
	out_value,
	out_consumed,
	out_error,
	count_cycles,
	count_inputs,
	count_symbols,
	count_bits,
	count_input_wait,
	count_output_stall,
	reservoir_bits
);
	input wire clk;
	input wire reset;
	input wire stream_start;
	input wire [31:0] stream_bits;
	input wire word16;
	input wire serial_mode;
	input wire in_valid;
	output reg in_ready;
	input wire [31:0] in_data;
	input wire [5:0] in_bits;
	input wire in_last;
	input wire req_valid;
	output reg req_ready;
	input wire [4:0] req_k;
	input wire [4:0] req_escape;
	output reg out_valid;
	input wire out_ready;
	output reg [23:0] out_value;
	output reg [31:0] out_consumed;
	output reg [3:0] out_error;
	output reg [63:0] count_cycles;
	output reg [63:0] count_inputs;
	output reg [63:0] count_symbols;
	output reg [63:0] count_bits;
	output reg [63:0] count_input_wait;
	output reg [63:0] count_output_stall;
	output reg [6:0] reservoir_bits;
	localparam [1:0] IDLE = 0;
	localparam [1:0] PREFIX = 1;
	localparam [1:0] SUFFIX = 2;
	localparam [1:0] RESPONSE = 3;
	localparam [3:0] OK = 0;
	localparam [3:0] BAD_PARAM = 1;
	localparam [3:0] TRUNCATED = 2;
	localparam [3:0] BAD_WORD = 3;
	reg [1:0] state;
	reg active;
	reg use16;
	reg serial;
	reg [3:0] failed;
	reg [31:0] size_bits;
	reg [31:0] loaded;
	reg [31:0] consumed;
	reg [63:0] reservoir;
	reg [6:0] available;
	reg [4:0] k;
	reg [4:0] escape_width;
	reg [4:0] quotient;
	reg [4:0] suffix_left;
	reg [23:0] suffix_acc;
	reg [31:0] remaining;
	reg [31:0] load_remaining;
	reg [5:0] expected_word;
	reg [5:0] window;
	reg [5:0] needed;
	reg [5:0] take_bits;
	reg [4:0] zeros;
	reg found_one;
	reg prefix_empty;
	reg word_bad;
	reg can_step;
	reg [63:0] extracted;
	reg [63:0] keep_mask;
	reg [23:0] suffix_value;
	reg [23:0] decoded_value;
	integer i;
	function automatic [5:0] sv2v_cast_6;
		input reg [5:0] inp;
		sv2v_cast_6 = inp;
	endfunction
	function automatic signed [6:0] sv2v_cast_7_signed;
		input reg signed [6:0] inp;
		sv2v_cast_7_signed = inp;
	endfunction
	function automatic [6:0] sv2v_cast_7;
		input reg [6:0] inp;
		sv2v_cast_7 = inp;
	endfunction
	function automatic [23:0] sv2v_cast_24;
		input reg [23:0] inp;
		sv2v_cast_24 = inp;
	endfunction
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	always_comb begin
		remaining = size_bits - consumed;
		load_remaining = size_bits - loaded;
		expected_word = (load_remaining < (use16 ? 32'd16 : 32'd32) ? sv2v_cast_6(load_remaining) : (use16 ? 6'd16 : 6'd32));
		window = (remaining < 15 ? sv2v_cast_6(remaining) : 6'd15);
		zeros = 0;
		found_one = 0;
		for (i = 0; i < 15; i = i + 1)
			if ((i < sv2v_cast_32_signed(window)) && !found_one) begin
				if ((available > sv2v_cast_7_signed(i)) && reservoir[(available - 1) - sv2v_cast_7_signed(i)])
					found_one = 1;
				else
					zeros = zeros + 1'b1;
			end
		prefix_empty = window == 0;
		needed = 0;
		take_bits = 0;
		if (state == PREFIX) begin
			needed = (serial ? 6'd1 : window);
			take_bits = (serial ? 6'd1 : (zeros == 15 ? 6'd15 : (found_one ? sv2v_cast_6(zeros) + 1'b1 : window)));
		end
		else if (state == SUFFIX) begin
			needed = (serial && (suffix_left != 0) ? 6'd1 : sv2v_cast_6(suffix_left));
			take_bits = needed;
		end
		can_step = available >= sv2v_cast_7(needed);
		extracted = (take_bits == 0 ? 64'd0 : reservoir >> (available - sv2v_cast_7(take_bits)));
		keep_mask = (sv2v_cast_7(take_bits) == available ? 64'd0 : 64'hffffffffffffffff >> (64 - (available - sv2v_cast_7(take_bits))));
		suffix_value = (serial ? (suffix_acc << 1) | sv2v_cast_24(extracted) : sv2v_cast_24(extracted));
		decoded_value = (quotient == 15 ? suffix_value : (sv2v_cast_24(quotient) << k) | suffix_value);
		word_bad = (((in_bits != expected_word) || (in_bits == 0)) || (in_last != ((loaded + sv2v_cast_32(in_bits)) == size_bits))) || ((in_bits < 32) && ((in_data & (32'hffffffff >> in_bits)) != 0));
		req_ready = (((active && (state == IDLE)) && !out_valid) && !stream_start) && !reset;
		in_ready = ((((((active && (failed == 0)) && !out_valid) && (available <= 32)) && (loaded < size_bits)) && !((state == IDLE) && req_valid)) && !stream_start) && !reset;
		reservoir_bits = available;
	end
	task automatic respond_error;
		input reg [3:0] code;
		begin
			failed <= code;
			out_valid <= 1;
			out_error <= code;
			out_value <= 0;
			out_consumed <= consumed;
			state <= RESPONSE;
		end
	endtask
	function automatic [63:0] sv2v_cast_64;
		input reg [63:0] inp;
		sv2v_cast_64 = inp;
	endfunction
	always_ff @(posedge clk)
		if (reset || stream_start) begin
			active <= !reset;
			use16 <= word16;
			serial <= serial_mode;
			size_bits <= stream_bits;
			loaded <= 0;
			consumed <= 0;
			reservoir <= 0;
			available <= 0;
			failed <= 0;
			state <= IDLE;
			k <= 0;
			escape_width <= 0;
			quotient <= 0;
			suffix_left <= 0;
			suffix_acc <= 0;
			out_valid <= 0;
			out_value <= 0;
			out_consumed <= 0;
			out_error <= 0;
			count_cycles <= 0;
			count_inputs <= 0;
			count_symbols <= 0;
			count_bits <= 0;
			count_input_wait <= 0;
			count_output_stall <= 0;
		end
		else if (active) begin
			count_cycles <= count_cycles + 1'b1;
			if (out_valid && !out_ready)
				count_output_stall <= count_output_stall + 1'b1;
			if ((((((state == PREFIX) || (state == SUFFIX)) && (needed != 0)) && !can_step) && !(in_valid && in_ready)) && (remaining >= sv2v_cast_32(needed)))
				count_input_wait <= count_input_wait + 1'b1;
			if (out_valid && out_ready) begin
				out_valid <= 0;
				state <= IDLE;
				if (out_error == 0)
					count_symbols <= count_symbols + 1'b1;
			end
			if (req_valid && req_ready) begin
				if (failed != 0)
					respond_error(failed);
				else if ((req_k > 19) || (req_escape > 24))
					respond_error(BAD_PARAM);
				else begin
					k <= req_k;
					escape_width <= req_escape;
					quotient <= 0;
					suffix_acc <= 0;
					suffix_left <= 0;
					state <= PREFIX;
				end
			end
			else if (in_valid && in_ready) begin
				count_inputs <= count_inputs + 1'b1;
				if (word_bad) begin
					failed <= BAD_WORD;
					if (state != IDLE)
						respond_error(BAD_WORD);
				end
				else begin
					reservoir <= (reservoir << in_bits) | (sv2v_cast_64(in_data) >> (32 - in_bits));
					available <= available + sv2v_cast_7(in_bits);
					loaded <= loaded + sv2v_cast_32(in_bits);
				end
			end
			else if ((state == PREFIX) && !out_valid) begin
				if (failed != 0)
					respond_error(failed);
				else if (prefix_empty)
					respond_error(TRUNCATED);
				else if (can_step) begin
					reservoir <= reservoir & keep_mask;
					available <= available - sv2v_cast_7(take_bits);
					consumed <= consumed + sv2v_cast_32(take_bits);
					count_bits <= count_bits + sv2v_cast_64(take_bits);
					if ((!serial && !found_one) && (window < 15)) begin
						failed <= TRUNCATED;
						out_valid <= 1;
						out_error <= TRUNCATED;
						out_value <= 0;
						out_consumed <= consumed + sv2v_cast_32(take_bits);
						state <= RESPONSE;
					end
					else if ((serial && (extracted == 0)) && (quotient < 14))
						quotient <= quotient + 1'b1;
					else begin
						if (serial) begin
							quotient <= (extracted == 0 ? 5'd15 : quotient);
							suffix_left <= (extracted == 0 ? escape_width : k);
						end
						else begin
							quotient <= zeros;
							suffix_left <= (zeros == 15 ? escape_width : k);
						end
						state <= SUFFIX;
					end
				end
			end
			else if ((state == SUFFIX) && !out_valid) begin
				if (remaining < sv2v_cast_32(suffix_left))
					respond_error(TRUNCATED);
				else if (can_step) begin
					reservoir <= reservoir & keep_mask;
					available <= available - sv2v_cast_7(take_bits);
					consumed <= consumed + sv2v_cast_32(take_bits);
					count_bits <= count_bits + sv2v_cast_64(take_bits);
					if (!serial || (suffix_left <= 1)) begin
						out_valid <= 1;
						out_error <= OK;
						out_value <= decoded_value;
						out_consumed <= consumed + sv2v_cast_32(take_bits);
						state <= RESPONSE;
					end
					else begin
						suffix_left <= suffix_left - 1'b1;
						suffix_acc <= suffix_value;
					end
				end
			end
		end
endmodule
module br88_context (
	clk,
	reset,
	start,
	abort_context,
	blocks,
	band,
	k0,
	k1,
	event_count,
	stream_bits,
	epoch,
	word16,
	serial_mode,
	in_valid,
	in_ready,
	in_data,
	in_bits,
	in_last,
	out_valid,
	out_ready,
	out_block,
	out_index,
	out_coefficient,
	out_epoch,
	done,
	error,
	consumed_bits,
	count_cycles,
	count_inputs,
	count_symbols,
	count_outputs,
	count_output_stall,
	count_input_wait,
	count_parser_cycles,
	count_parser_output_stall,
	debug_state,
	reservoir_bits
);
	input wire clk;
	input wire reset;
	input wire start;
	input wire abort_context;
	input wire [16:0] blocks;
	input wire [7:0] band;
	input wire [7:0] k0;
	input wire [7:0] k1;
	input wire [31:0] event_count;
	input wire [31:0] stream_bits;
	input wire [31:0] epoch;
	input wire word16;
	input wire serial_mode;
	input wire in_valid;
	output wire in_ready;
	input wire [31:0] in_data;
	input wire [5:0] in_bits;
	input wire in_last;
	output reg out_valid;
	input wire out_ready;
	output reg [15:0] out_block;
	output reg [5:0] out_index;
	output reg signed [15:0] out_coefficient;
	output reg [31:0] out_epoch;
	output reg done;
	output reg [3:0] error;
	output reg [31:0] consumed_bits;
	output reg [63:0] count_cycles;
	output wire [63:0] count_inputs;
	output wire [63:0] count_symbols;
	output reg [63:0] count_outputs;
	output reg [63:0] count_output_stall;
	output wire [63:0] count_input_wait;
	output wire [63:0] count_parser_cycles;
	output wire [63:0] count_parser_output_stall;
	output reg [3:0] debug_state;
	output wire [6:0] reservoir_bits;
	localparam [3:0] IDLE = 0;
	localparam [3:0] REQ_DC = 1;
	localparam [3:0] WAIT_DC = 2;
	localparam [3:0] REQ_RUN = 3;
	localparam [3:0] WAIT_RUN = 4;
	localparam [3:0] REQ_LEVEL = 5;
	localparam [3:0] WAIT_LEVEL = 6;
	localparam [3:0] HELD = 7;
	localparam [3:0] FINISHED = 8;
	localparam [3:0] FAILED = 9;
	localparam [383:0] ZIGZAG = 384'h12102420ca45881948b1053136a1a30a626d43461ce55c8eac78e72ae47563d77a5b33ebbd2d99f9eed7cf76bf7fbf;
	reg [3:0] state;
	reg [7:0] context_band;
	reg [4:0] run_k;
	reg [4:0] level_k;
	reg [31:0] size_bits;
	reg [31:0] context_epoch;
	reg [31:0] target;
	reg [31:0] emitted;
	reg [31:0] position;
	reg [31:0] limit;
	reg [15:0] sparse_block;
	reg [5:0] sparse_index;
	reg active;
	reg req_valid;
	wire req_ready;
	wire parser_valid;
	reg parser_ready;
	wire parser_in_ready;
	reg [4:0] req_k;
	reg [4:0] req_escape;
	wire [23:0] parser_value;
	wire [31:0] parser_consumed;
	wire [3:0] parser_error;
	wire [63:0] parser_bits;
	reg [32:0] next_position;
	reg [24:0] unsigned_coefficient;
	reg signed [25:0] signed_coefficient;
	reg [5:0] start_width;
	reg [31:0] start_limit;
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [15:0] sv2v_cast_16;
		input reg [15:0] inp;
		sv2v_cast_16 = inp;
	endfunction
	function automatic [5:0] sv2v_cast_6;
		input reg [5:0] inp;
		sv2v_cast_6 = inp;
	endfunction
	function automatic [32:0] sv2v_cast_33;
		input reg [32:0] inp;
		sv2v_cast_33 = inp;
	endfunction
	function automatic [25:0] sv2v_cast_26;
		input reg [25:0] inp;
		sv2v_cast_26 = inp;
	endfunction
	always_comb begin
		case (band)
			1: start_width = 5;
			2: start_width = 15;
			3: start_width = 43;
			default: start_width = 1;
		endcase
		start_limit = sv2v_cast_32(blocks) * sv2v_cast_32(start_width);
		case (context_band)
			1: begin
				sparse_block = sv2v_cast_16(position / 32'd5);
				sparse_index = ZIGZAG[(63 - sv2v_cast_6(32'd1 + (position % 32'd5))) * 6+:6];
			end
			2: begin
				sparse_block = sv2v_cast_16(position / 32'd15);
				sparse_index = ZIGZAG[(63 - sv2v_cast_6(32'd6 + (position % 32'd15))) * 6+:6];
			end
			3: begin
				sparse_block = sv2v_cast_16(position / 32'd43);
				sparse_index = ZIGZAG[(63 - sv2v_cast_6(32'd21 + (position % 32'd43))) * 6+:6];
			end
			default: begin
				sparse_block = sv2v_cast_16(emitted);
				sparse_index = 0;
			end
		endcase
		active = ((state != IDLE) && (state != FINISHED)) && (state != FAILED);
		req_valid = (((active && (((state == REQ_DC) || (state == REQ_RUN)) || (state == REQ_LEVEL))) && !start) && !abort_context) && !reset;
		req_k = (state == REQ_LEVEL ? level_k : run_k);
		req_escape = (state == REQ_DC ? 5'd14 : (state == REQ_RUN ? 5'd24 : 5'd12));
		parser_ready = (((((state == WAIT_DC) || (state == WAIT_RUN)) || (state == WAIT_LEVEL)) && !start) && !abort_context) && !reset;
		next_position = ({1'b0, position} + sv2v_cast_33(parser_value)) + 1'b1;
		unsigned_coefficient = {1'b0, parser_value} + (state == WAIT_LEVEL ? 25'd1 : 25'd0);
		signed_coefficient = (unsigned_coefficient[0] ? -((sv2v_cast_26(unsigned_coefficient) >> 1) + 26'sd1) : sv2v_cast_26(unsigned_coefficient) >> 1);
		consumed_bits = sv2v_cast_32(parser_bits);
		debug_state = state;
	end
	assign in_ready = (((parser_in_ready && active) && !start) && !abort_context) && !reset;
	br88_rice_elastic parser(
		.clk(clk),
		.reset(reset || abort_context),
		.stream_start(start && !abort_context),
		.stream_bits(stream_bits),
		.word16(word16),
		.serial_mode(serial_mode),
		.in_valid(((in_valid && active) && !start) && !abort_context),
		.in_ready(parser_in_ready),
		.in_data(in_data),
		.in_bits(in_bits),
		.in_last(in_last),
		.req_valid(req_valid),
		.req_ready(req_ready),
		.req_k(req_k),
		.req_escape(req_escape),
		.out_valid(parser_valid),
		.out_ready(parser_ready),
		.out_value(parser_value),
		.out_consumed(parser_consumed),
		.out_error(parser_error),
		.count_cycles(count_parser_cycles),
		.count_inputs(count_inputs),
		.count_symbols(count_symbols),
		.count_bits(parser_bits),
		.count_input_wait(count_input_wait),
		.count_output_stall(count_parser_output_stall),
		.reservoir_bits(reservoir_bits)
	);
	task automatic fail_context;
		input reg [3:0] code;
		begin
			error <= code;
			state <= FAILED;
			out_valid <= 0;
			done <= 0;
		end
	endtask
	function automatic signed [15:0] sv2v_cast_16_signed;
		input reg signed [15:0] inp;
		sv2v_cast_16_signed = inp;
	endfunction
	always_ff @(posedge clk)
		if (reset || abort_context) begin
			state <= IDLE;
			context_band <= 0;
			run_k <= 0;
			level_k <= 0;
			size_bits <= 0;
			context_epoch <= 0;
			target <= 0;
			emitted <= 0;
			position <= 0;
			limit <= 0;
			out_valid <= 0;
			out_block <= 0;
			out_index <= 0;
			out_coefficient <= 0;
			out_epoch <= 0;
			done <= 0;
			error <= 0;
			count_cycles <= 0;
			count_outputs <= 0;
			count_output_stall <= 0;
		end
		else if (start) begin
			context_band <= band;
			run_k <= k0[4:0];
			level_k <= k1[4:0];
			size_bits <= stream_bits;
			context_epoch <= epoch;
			target <= (band == 0 ? sv2v_cast_32(blocks) : event_count);
			emitted <= 0;
			position <= 32'hffffffff;
			limit <= start_limit;
			out_valid <= 0;
			out_block <= 0;
			out_index <= 0;
			out_coefficient <= 0;
			out_epoch <= epoch;
			done <= 0;
			error <= 0;
			count_cycles <= 0;
			count_outputs <= 0;
			count_output_stall <= 0;
			if (((((blocks == 0) || (blocks > 65536)) || (band > 3)) || ((band == 0) && (((k0 > 13) || (k1 != 255)) || (event_count != sv2v_cast_32(blocks))))) || ((band != 0) && (((k0 > 19) || (k1 > 11)) || (event_count > start_limit)))) begin
				state <= FAILED;
				error <= 4;
			end
			else if ((band != 0) && (event_count == 0)) begin
				if (stream_bits != 0) begin
					state <= FAILED;
					error <= 7;
				end
				else begin
					state <= FINISHED;
					done <= 1;
				end
			end
			else
				state <= (band == 0 ? REQ_DC : REQ_RUN);
		end
		else if (active) begin
			count_cycles <= count_cycles + 1'b1;
			if (out_valid && !out_ready)
				count_output_stall <= count_output_stall + 1'b1;
			if (req_valid && req_ready)
				case (state)
					REQ_DC: state <= WAIT_DC;
					REQ_RUN: state <= WAIT_RUN;
					default: state <= WAIT_LEVEL;
				endcase
			if (parser_valid && parser_ready) begin
				if (parser_error != 0)
					fail_context(parser_error);
				else if (state == WAIT_RUN) begin
					if ((emitted == 0 ? sv2v_cast_33(parser_value) : next_position) >= sv2v_cast_33(limit))
						fail_context(6);
					else begin
						position <= (emitted == 0 ? sv2v_cast_32(parser_value) : sv2v_cast_32(next_position));
						state <= REQ_LEVEL;
					end
				end
				else if (((signed_coefficient < -2048) || (signed_coefficient > 2048)) || ((state == WAIT_LEVEL) && (signed_coefficient == 0)))
					fail_context(5);
				else if (((emitted + 1) == target) && (parser_consumed != size_bits))
					fail_context(7);
				else begin
					out_valid <= 1;
					out_epoch <= context_epoch;
					out_coefficient <= sv2v_cast_16_signed(signed_coefficient);
					out_block <= sparse_block;
					out_index <= sparse_index;
					state <= HELD;
				end
			end
			if (out_valid && out_ready) begin
				out_valid <= 0;
				count_outputs <= count_outputs + 1'b1;
				emitted <= emitted + 1'b1;
				if ((emitted + 1) == target) begin
					done <= 1;
					state <= FINISHED;
				end
				else
					state <= (context_band == 0 ? REQ_DC : REQ_RUN);
			end
		end
endmodule
module br88_packet_ingress (
	clk,
	reset,
	start,
	abort_packet,
	packet_bytes,
	blocks,
	epoch,
	word16,
	serial_mode,
	in_valid,
	in_ready,
	in_data,
	in_last,
	out_valid,
	out_ready,
	out_block,
	out_index,
	out_coefficient,
	out_epoch,
	meta_valid,
	meta_ready,
	meta_blocks,
	meta_count1,
	meta_count2,
	meta_count3,
	meta_epoch,
	meta_raw,
	out_band,
	band_end_valid,
	band_end_ready,
	band_end_band,
	band_end_epoch,
	done,
	error,
	count_cycles,
	count_inputs,
	count_outputs,
	count_output_stall,
	debug_state
);
	parameter integer MAX_PACKET_BYTES = 49152;
	input wire clk;
	input wire reset;
	input wire start;
	input wire abort_packet;
	input wire [31:0] packet_bytes;
	input wire [16:0] blocks;
	input wire [31:0] epoch;
	input wire word16;
	input wire serial_mode;
	input wire in_valid;
	output reg in_ready;
	input wire [7:0] in_data;
	input wire in_last;
	output reg out_valid;
	input wire out_ready;
	output reg [15:0] out_block;
	output reg [5:0] out_index;
	output reg signed [15:0] out_coefficient;
	output reg [31:0] out_epoch;
	output reg meta_valid;
	input wire meta_ready;
	output reg [16:0] meta_blocks;
	output reg [31:0] meta_count1;
	output reg [31:0] meta_count2;
	output reg [31:0] meta_count3;
	output reg [31:0] meta_epoch;
	output reg meta_raw;
	output reg [1:0] out_band;
	output reg band_end_valid;
	input wire band_end_ready;
	output reg [1:0] band_end_band;
	output reg [31:0] band_end_epoch;
	output reg done;
	output reg [3:0] error;
	output reg [63:0] count_cycles;
	output reg [63:0] count_inputs;
	output reg [63:0] count_outputs;
	output reg [63:0] count_output_stall;
	output reg [3:0] debug_state;
	localparam [3:0] IDLE = 0;
	localparam [3:0] RECEIVE = 1;
	localparam [3:0] HEADER = 2;
	localparam [3:0] DESCRIPTOR = 3;
	localparam [3:0] CONTEXT_START = 4;
	localparam [3:0] CONTEXT_RUN = 5;
	localparam [3:0] RAW = 6;
	localparam [3:0] FINISHED = 7;
	localparam [3:0] FAILED = 8;
	localparam [3:0] METADATA = 9;
	localparam [3:0] CONTEXT_END = 10;
	localparam [3:0] RAW_END = 11;
	reg [3:0] state;
	reg [7:0] memory [0:MAX_PACKET_BYTES - 1];
	reg [31:0] size_bytes;
	reg [31:0] context_epoch;
	reg [31:0] received;
	reg [31:0] crc;
	reg [31:0] cursor;
	reg [16:0] context_blocks;
	reg mode16;
	reg mode_serial;
	reg raw_mode;
	reg [1:0] band;
	reg [31:0] lengths [0:3];
	reg [31:0] counts [0:3];
	reg [31:0] offsets [0:3];
	reg [31:0] sizes [0:3];
	reg [7:0] k0s [0:3];
	reg [7:0] k1s [0:3];
	reg [31:0] descriptor_bits;
	reg [31:0] descriptor_bytes;
	reg [31:0] descriptor_limit;
	reg [31:0] replay_bits;
	reg [31:0] raw_position;
	reg [31:0] ctx_data;
	reg [5:0] ctx_bits;
	reg ctx_last;
	reg ctx_valid;
	wire ctx_ready;
	wire ctx_out_valid;
	wire ctx_done;
	wire [15:0] ctx_block;
	wire [5:0] ctx_index;
	wire signed [15:0] ctx_coefficient;
	reg signed [15:0] raw_coefficient;
	wire [31:0] ctx_epoch;
	wire [3:0] ctx_error;
	wire [31:0] unused_consumed;
	wire [63:0] unused_cycles;
	wire [63:0] unused_inputs;
	wire [63:0] unused_symbols;
	wire [63:0] unused_outputs;
	wire [63:0] unused_stall;
	wire [63:0] unused_wait;
	wire [63:0] unused_parser_cycles;
	wire [63:0] unused_parser_stall;
	wire [3:0] unused_debug;
	wire [6:0] unused_reservoir;
	reg cancelled;
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	function automatic [31:0] le32;
		input reg [31:0] at;
		if (at <= sv2v_cast_32_signed(MAX_PACKET_BYTES - 4))
			le32 = {memory[at + 3], memory[at + 2], memory[at + 1], memory[at]};
		else
			le32 = 0;
	endfunction
	function automatic [31:0] crc_byte;
		input reg [31:0] previous_crc;
		input reg [7:0] value;
		reg [31:0] c;
		begin
			c = previous_crc ^ {24'd0, value};
			begin : sv2v_autoblock_1
				integer j;
				for (j = 0; j < 8; j = j + 1)
					c = (c[0] ? (c >> 1) ^ 32'hedb88320 : c >> 1);
			end
			crc_byte = c;
		end
	endfunction
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [5:0] sv2v_cast_6;
		input reg [5:0] inp;
		sv2v_cast_6 = inp;
	endfunction
	function automatic [15:0] sv2v_cast_16;
		input reg [15:0] inp;
		sv2v_cast_16 = inp;
	endfunction
	always_comb begin
		cancelled = (reset || abort_packet) || start;
		in_ready = (state == RECEIVE) && !cancelled;
		descriptor_bits = le32(cursor + 2);
		descriptor_bytes = (descriptor_bits >> 3) + sv2v_cast_32(descriptor_bits[2:0] != 0);
		case (band)
			1: descriptor_limit = sv2v_cast_32(context_blocks) * 5;
			2: descriptor_limit = sv2v_cast_32(context_blocks) * 15;
			3: descriptor_limit = sv2v_cast_32(context_blocks) * 43;
			default: descriptor_limit = sv2v_cast_32(context_blocks);
		endcase
		ctx_data = 0;
		ctx_bits = sv2v_cast_6(((sizes[band] - replay_bits) < (mode16 ? 16 : 32) ? sizes[band] - replay_bits : (mode16 ? 16 : 32)));
		begin : sv2v_autoblock_2
			integer j;
			for (j = 0; j < 32; j = j + 1)
				if ((j < sv2v_cast_32(ctx_bits)) && (state == CONTEXT_RUN))
					ctx_data[31 - j] = memory[offsets[band] + ((replay_bits + j) >> 3)][7 - ((replay_bits + j) & 7)];
		end
		ctx_last = (replay_bits + sv2v_cast_32(ctx_bits)) == sizes[band];
		ctx_valid = ((state == CONTEXT_RUN) && (replay_bits < sizes[band])) && !cancelled;
		raw_coefficient = 0;
		if ((state == RAW) && (raw_position < (sv2v_cast_32(context_blocks) * 64)))
			raw_coefficient = $signed({memory[(42 + (2 * raw_position)) + 1], memory[42 + (2 * raw_position)]});
		out_valid = !cancelled && (((state == CONTEXT_RUN) && ctx_out_valid) || (((state == RAW) && (raw_coefficient >= -2048)) && (raw_coefficient <= 2048)));
		out_block = (state == RAW ? sv2v_cast_16(raw_position >> 6) : ctx_block);
		out_index = (state == RAW ? raw_position[5:0] : ctx_index);
		out_coefficient = (state == RAW ? raw_coefficient : ctx_coefficient);
		out_epoch = (state == RAW ? context_epoch : ctx_epoch);
		meta_valid = (state == METADATA) && !cancelled;
		meta_blocks = context_blocks;
		meta_count1 = counts[1];
		meta_count2 = counts[2];
		meta_count3 = counts[3];
		meta_epoch = context_epoch;
		meta_raw = raw_mode;
		out_band = (state == RAW ? 2'd0 : band);
		band_end_valid = ((state == CONTEXT_END) || (state == RAW_END)) && !cancelled;
		band_end_band = (state == RAW_END ? 2'd0 : band);
		band_end_epoch = context_epoch;
		debug_state = state;
	end
	br88_context context_decoder(
		.clk(clk),
		.reset(reset),
		.start((state == CONTEXT_START) && !cancelled),
		.abort_context(abort_packet || start),
		.blocks(context_blocks),
		.band({6'd0, band}),
		.k0(k0s[band]),
		.k1(k1s[band]),
		.event_count(counts[band]),
		.stream_bits(sizes[band]),
		.epoch(context_epoch),
		.word16(mode16),
		.serial_mode(mode_serial),
		.in_valid(ctx_valid),
		.in_ready(ctx_ready),
		.in_data(ctx_data),
		.in_bits(ctx_bits),
		.in_last(ctx_last),
		.out_valid(ctx_out_valid),
		.out_ready((out_ready && (state == CONTEXT_RUN)) && !cancelled),
		.out_block(ctx_block),
		.out_index(ctx_index),
		.out_coefficient(ctx_coefficient),
		.out_epoch(ctx_epoch),
		.done(ctx_done),
		.error(ctx_error),
		.consumed_bits(unused_consumed),
		.count_cycles(unused_cycles),
		.count_inputs(unused_inputs),
		.count_symbols(unused_symbols),
		.count_outputs(unused_outputs),
		.count_output_stall(unused_stall),
		.count_input_wait(unused_wait),
		.count_parser_cycles(unused_parser_cycles),
		.count_parser_output_stall(unused_parser_stall),
		.debug_state(unused_debug),
		.reservoir_bits(unused_reservoir)
	);
	task automatic fail_packet;
		input reg [3:0] code;
		begin
			state <= FAILED;
			error <= code;
			done <= 0;
		end
	endtask
	always_ff @(posedge clk)
		if (reset || abort_packet) begin
			state <= IDLE;
			size_bytes <= 0;
			context_epoch <= 0;
			context_blocks <= 0;
			received <= 0;
			crc <= 32'hffffffff;
			cursor <= 0;
			band <= 0;
			mode16 <= 0;
			mode_serial <= 0;
			raw_mode <= 0;
			replay_bits <= 0;
			raw_position <= 0;
			done <= 0;
			error <= 0;
			count_cycles <= 0;
			count_inputs <= 0;
			count_outputs <= 0;
			count_output_stall <= 0;
			begin : sv2v_autoblock_3
				integer j;
				for (j = 0; j < 4; j = j + 1)
					begin
						lengths[j] <= 0;
						counts[j] <= 0;
						offsets[j] <= 0;
						sizes[j] <= 0;
						k0s[j] <= 0;
						k1s[j] <= 0;
					end
			end
		end
		else if (start) begin
			size_bytes <= packet_bytes;
			context_epoch <= epoch;
			context_blocks <= blocks;
			mode16 <= word16;
			mode_serial <= serial_mode;
			raw_mode <= 0;
			received <= 0;
			crc <= 32'hffffffff;
			cursor <= 42;
			band <= 0;
			replay_bits <= 0;
			raw_position <= 0;
			done <= 0;
			error <= 0;
			count_cycles <= 0;
			count_inputs <= 0;
			count_outputs <= 0;
			count_output_stall <= 0;
			if (((((blocks == 0) || (blocks > 65536)) || (packet_bytes < 46)) || (packet_bytes > MAX_PACKET_BYTES)) || (packet_bytes > (46 + (128 * sv2v_cast_32(blocks))))) begin
				state <= FAILED;
				error <= 1;
			end
			else
				state <= RECEIVE;
		end
		else if (((state != IDLE) && (state != FINISHED)) && (state != FAILED)) begin
			count_cycles <= count_cycles + 1'b1;
			if (out_valid && !out_ready)
				count_output_stall <= count_output_stall + 1'b1;
			if (out_valid && out_ready)
				count_outputs <= count_outputs + 1'b1;
			case (state)
				RECEIVE:
					if (in_valid && in_ready) begin
						memory[received] <= in_data;
						received <= received + 1'b1;
						count_inputs <= count_inputs + 1'b1;
						if (received < (size_bytes - 4))
							crc <= crc_byte(crc, in_data);
						if (in_last != ((received + 1) == size_bytes))
							fail_packet(2);
						else if ((received + 1) == size_bytes)
							state <= HEADER;
					end
				HEADER:
					if ((crc ^ 32'hffffffff) != le32(size_bytes - 4))
						fail_packet(3);
					else if ((((((le32(0) != 32'h38385242) || (memory[4] != 1)) || (memory[5] > 1)) || (le32(6) != sv2v_cast_32(context_blocks))) || ({memory[11], memory[10]} != 1)) || ({memory[13], memory[12]} != 0))
						fail_packet(4);
					else if (((({2'd0, le32(14)} + {2'd0, le32(18)}) + {2'd0, le32(22)}) + {2'd0, le32(26)}) != ({2'd0, size_bytes} - 34'd46))
						fail_packet(4);
					else begin
						begin : sv2v_autoblock_4
							integer j;
							for (j = 0; j < 4; j = j + 1)
								lengths[j] <= le32(14 + (j * 4));
						end
						counts[0] <= sv2v_cast_32(context_blocks);
						raw_mode <= memory[5] == 1;
						begin : sv2v_autoblock_5
							integer j;
							for (j = 1; j < 4; j = j + 1)
								counts[j] <= le32(26 + (j * 4));
						end
						if (memory[5] == 1) begin
							if (((((((le32(14) != (128 * sv2v_cast_32(context_blocks))) || (le32(18) != 0)) || (le32(22) != 0)) || (le32(26) != 0)) || (le32(30) != 0)) || (le32(34) != 0)) || (le32(38) != 0))
								fail_packet(4);
							else
								state <= METADATA;
						end
						else
							state <= DESCRIPTOR;
					end
				DESCRIPTOR:
					if (((lengths[band] < 6) || (cursor > (size_bytes - 4))) || (lengths[band] > ((size_bytes - 4) - cursor)))
						fail_packet(4);
					else if ((descriptor_bytes != (lengths[band] - 6)) || (descriptor_bits > (8 * (size_bytes - 46))))
						fail_packet(4);
					else if (((band == 0) && ((memory[cursor] > 13) || (memory[cursor + 1] != 255))) || ((band != 0) && (((memory[cursor] > 19) || (memory[cursor + 1] > 11)) || (counts[band] > descriptor_limit))))
						fail_packet(4);
					else if (((band != 0) && (counts[band] == 0)) && (descriptor_bits != 0))
						fail_packet(7);
					else if ((descriptor_bits[2:0] != 0) && ((memory[(cursor + lengths[band]) - 1] & (8'hff >> descriptor_bits[2:0])) != 0))
						fail_packet(7);
					else begin
						k0s[band] <= memory[cursor];
						k1s[band] <= memory[cursor + 1];
						sizes[band] <= descriptor_bits;
						offsets[band] <= cursor + 6;
						cursor <= cursor + lengths[band];
						if (band == 3) begin
							band <= 0;
							state <= METADATA;
						end
						else
							band <= band + 1'b1;
					end
				METADATA:
					if (meta_valid && meta_ready)
						state <= (raw_mode ? RAW : CONTEXT_START);
				CONTEXT_START: begin
					replay_bits <= 0;
					state <= CONTEXT_RUN;
				end
				CONTEXT_RUN: begin
					if (ctx_valid && ctx_ready)
						replay_bits <= replay_bits + sv2v_cast_32(ctx_bits);
					if (ctx_error != 0)
						fail_packet(ctx_error);
					else if (ctx_done)
						state <= CONTEXT_END;
				end
				RAW:
					if ((raw_coefficient < -2048) || (raw_coefficient > 2048))
						fail_packet(5);
					else if (out_valid && out_ready) begin
						raw_position <= raw_position + 1'b1;
						if ((raw_position + 1) == (sv2v_cast_32(context_blocks) * 64))
							state <= RAW_END;
					end
				CONTEXT_END:
					if (band_end_valid && band_end_ready) begin
						if (band == 3) begin
							done <= 1;
							state <= FINISHED;
						end
						else begin
							band <= band + 1'b1;
							state <= CONTEXT_START;
						end
					end
				RAW_END:
					if (band_end_valid && band_end_ready) begin
						done <= 1;
						state <= FINISHED;
					end
				default:
					fail_packet(4);
			endcase
		end
endmodule
module packed_scratch_v91g2 (
	clk,
	reset,
	begin_valid,
	begin_ready,
	begin_blocks,
	begin_raw,
	begin_serial_clear,
	begin_overlap,
	begin_prefetch,
	begin_tile_overlap,
	begin_count1,
	begin_count2,
	begin_count3,
	begin_epoch,
	coef_valid,
	coef_ready,
	coef_band,
	coef_block,
	coef_index,
	coef_value,
	coef_epoch,
	band_end_valid,
	band_end_ready,
	band_end_band,
	band_end_epoch,
	seal_valid,
	seal_ready,
	seal_epoch,
	abort_valid,
	abort_epoch,
	busy,
	sealed,
	done,
	error,
	active_epoch,
	used_bytes,
	dense_valid,
	dense_ready,
	dense_block,
	dense_index,
	dense_value,
	dense_epoch,
	mem_req_valid,
	mem_req_ready,
	mem_req_write,
	mem_req_addr,
	mem_req_data,
	mem_req_epoch,
	mem_rsp_valid,
	mem_rsp_ready,
	mem_rsp_data,
	mem_rsp_epoch,
	mem_rsp_error,
	debug_state,
	debug_return_state,
	debug_outstanding,
	debug_phase,
	debug_assembly_bytes,
	debug_cache_valid,
	debug_prefetch_offer,
	debug_prefetch_launch,
	debug_prefetch_use,
	debug_tile_mode,
	debug_tile_preparing,
	debug_prepare_bank,
	debug_emit_bank,
	debug_bank_ready,
	debug_bank_owned,
	debug_emitter_state,
	debug_prepare_block,
	debug_bank_block,
	debug_bank_epoch,
	debug_tile_prepare_start,
	debug_tile_publish,
	debug_tile_release,
	debug_write_slot_valid,
	debug_assembler_full,
	debug_write_enqueue,
	debug_head_valid
);
	input wire clk;
	input wire reset;
	input wire begin_valid;
	output reg begin_ready;
	input wire [16:0] begin_blocks;
	input wire begin_raw;
	input wire begin_serial_clear;
	input wire begin_overlap;
	input wire begin_prefetch;
	input wire begin_tile_overlap;
	input wire [31:0] begin_count1;
	input wire [31:0] begin_count2;
	input wire [31:0] begin_count3;
	input wire [31:0] begin_epoch;
	input wire coef_valid;
	output reg coef_ready;
	input wire [1:0] coef_band;
	input wire [15:0] coef_block;
	input wire [5:0] coef_index;
	input wire signed [15:0] coef_value;
	input wire [31:0] coef_epoch;
	input wire band_end_valid;
	output reg band_end_ready;
	input wire [1:0] band_end_band;
	input wire [31:0] band_end_epoch;
	input wire seal_valid;
	output reg seal_ready;
	input wire [31:0] seal_epoch;
	input wire abort_valid;
	input wire [31:0] abort_epoch;
	output reg busy;
	output reg sealed;
	output reg done;
	output reg [3:0] error;
	output reg [31:0] active_epoch = 0;
	output reg [18:0] used_bytes;
	output reg dense_valid;
	input wire dense_ready;
	output reg [15:0] dense_block;
	output reg [5:0] dense_index;
	output reg signed [15:0] dense_value;
	output reg [31:0] dense_epoch;
	output reg mem_req_valid;
	input wire mem_req_ready;
	output reg mem_req_write;
	output reg [17:0] mem_req_addr;
	output reg [127:0] mem_req_data;
	output reg [31:0] mem_req_epoch;
	input wire mem_rsp_valid;
	output reg mem_rsp_ready;
	input wire [127:0] mem_rsp_data;
	input wire [31:0] mem_rsp_epoch;
	input wire mem_rsp_error;
	output wire [4:0] debug_state;
	output wire [4:0] debug_return_state;
	output wire debug_outstanding;
	output wire [2:0] debug_phase;
	output wire [4:0] debug_assembly_bytes;
	output wire [3:0] debug_cache_valid;
	output wire debug_prefetch_offer;
	output wire debug_prefetch_launch;
	output reg debug_prefetch_use;
	output wire debug_tile_mode;
	output wire debug_tile_preparing;
	output wire debug_prepare_bank;
	output wire debug_emit_bank;
	output wire [1:0] debug_bank_ready;
	output wire [1:0] debug_bank_owned;
	output wire [1:0] debug_emitter_state;
	output wire [15:0] debug_prepare_block;
	output wire [31:0] debug_bank_block;
	output wire [63:0] debug_bank_epoch;
	output wire debug_tile_prepare_start;
	output wire debug_tile_publish;
	output wire debug_tile_release;
	output wire debug_write_slot_valid;
	output wire debug_assembler_full;
	output reg debug_write_enqueue;
	output wire [2:0] debug_head_valid;
	reg [4:0] state = 5'd0;
	reg [4:0] return_state;
	reg outstanding = 0;
	reg epoch_seen = 0;
	reg [31:0] last_epoch = 0;
	reg [16:0] blocks;
	reg raw_mode;
	reg serial_clear;
	reg overlap_mode;
	reg prefetch_mode;
	reg tile_overlap_mode = 0;
	wire tile_mode;
	reg prep_bank;
	reg emit_bank;
	reg tile_preparing;
	reg [15:0] prepare_block;
	reg [5:0] tile_emit_index;
	reg [1:0] bank_ready;
	reg [15:0] bank_block [0:1];
	reg [31:0] bank_epoch [0:1];
	reg prefetch_offer = 0;
	reg [3:0] prefetched_valid;
	reg [1:0] prefetch_segment;
	reg [1:0] candidate_segment;
	reg [17:0] candidate_address;
	reg candidate_valid;
	reg prefetch_launch;
	reg prefetch_complete;
	reg response_failure;
	reg [31:0] candidate_word_address;
	reg write_slot_valid = 0;
	reg slot_available;
	reg [63:0] tile_valid [0:1];
	reg [31:0] counts [0:3];
	reg [31:0] starts [0:3];
	reg [31:0] written;
	reg [31:0] previous_position;
	reg previous_valid;
	reg [2:0] phase;
	reg [127:0] assembler;
	reg [4:0] assembly_bytes;
	reg [31:0] write_address;
	reg [31:0] pending_record;
	reg [2:0] pending_bytes;
	reg [31:0] pending_position;
	reg [127:0] transfer_data;
	reg [17:0] transfer_address;
	reg [31:0] request_epoch;
	reg [127:0] descriptor_low;
	reg [127:0] cache_data [0:3];
	reg [17:0] cache_address [0:3];
	reg [3:0] cache_valid;
	reg [1:0] read_segment;
	reg [31:0] read_address;
	reg [31:0] heads [1:3];
	reg [31:0] cursors [1:3];
	reg [3:1] head_valid;
	reg [1:0] read_band;
	reg signed [15:0] tile [0:1][0:63];
	reg [15:0] output_block;
	reg [5:0] output_index;
	reg [5:0] clear_index;
	reg signed [15:0] raw_value;
	reg [31:0] plan_start1;
	reg [31:0] plan_start2;
	reg [31:0] plan_start3;
	reg [31:0] plan_used;
	reg [31:0] input_position;
	reg [5:0] input_zigzag;
	reg input_bad;
	reg [31:0] read_word;
	reg signed [15:0] read_half;
	reg [31:0] read_position;
	reg cancel;
	function automatic [31:0] aligned;
		input reg [31:0] n;
		aligned = (n + 15) & 32'hfffffff0;
	endfunction
	function automatic signed [5:0] sv2v_cast_6_signed;
		input reg signed [5:0] inp;
		sv2v_cast_6_signed = inp;
	endfunction
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	function automatic [5:0] zigzag;
		input reg [5:0] raster;
		integer rank;
		integer sum;
		integer row;
		begin
			rank = 0;
			zigzag = 0;
			begin : sv2v_autoblock_1
				integer diagonal;
				for (diagonal = 0; diagonal < 15; diagonal = diagonal + 1)
					begin : sv2v_autoblock_2
						integer step;
						for (step = 0; step < 8; step = step + 1)
							begin
								row = ((diagonal % 2) == 1 ? step : 7 - step);
								sum = diagonal - row;
								if ((sum >= 0) && (sum < 8)) begin
									if (((row * 8) + sum) == sv2v_cast_32_signed(raster))
										zigzag = sv2v_cast_6_signed(rank);
									rank = rank + 1;
								end
							end
					end
			end
		end
	endfunction
	function automatic band_matches;
		input reg [1:0] band;
		input reg [5:0] index;
		reg [5:0] z;
		begin
			z = zigzag(index);
			case (band)
				1: band_matches = (z >= 1) && (z < 6);
				2: band_matches = (z >= 6) && (z < 21);
				3: band_matches = z >= 21;
				default: band_matches = index == 0;
			endcase
		end
	endfunction
	assign tile_mode = tile_overlap_mode && !raw_mode;
	assign debug_tile_mode = tile_mode;
	assign debug_tile_preparing = tile_mode && tile_preparing;
	assign debug_prepare_bank = prep_bank;
	assign debug_emit_bank = emit_bank;
	assign debug_prepare_block = prepare_block;
	genvar _gv_b_1;
	generate
		for (_gv_b_1 = 0; _gv_b_1 < 2; _gv_b_1 = _gv_b_1 + 1) begin : bank_views
			localparam b = _gv_b_1;
			assign debug_bank_block[(1 - b) * 16+:16] = bank_block[b];
			assign debug_bank_epoch[(1 - b) * 32+:32] = bank_epoch[b];
			genvar _gv_k_1;
			for (_gv_k_1 = 0; _gv_k_1 < 64; _gv_k_1 = _gv_k_1 + 1) begin : immutable_payload
				localparam k = _gv_k_1;
			end
		end
	endgenerate
	assign debug_bank_ready = (tile_mode ? bank_ready : 2'b00);
	assign debug_bank_owned = (tile_mode ? bank_ready | (tile_preparing ? 2'b01 << prep_bank : 2'b00) : 2'b00);
	assign debug_emitter_state = (!tile_mode ? 2'd3 : (!dense_valid ? 2'd0 : (dense_ready ? 2'd1 : 2'd2)));
	function automatic [16:0] sv2v_cast_17;
		input reg [16:0] inp;
		sv2v_cast_17 = inp;
	endfunction
	assign debug_tile_prepare_start = ((tile_mode && !cancel) && !response_failure) && ((((state == 5'd13) && (descriptor_low == {counts[1], 31'd0, raw_mode, 15'd0, blocks, 32'h43393150})) && (transfer_data == {45'h000000000000, used_bytes, counts[3], counts[2]})) || (((state == 5'd28) && ((sv2v_cast_17(prepare_block) + 1) < blocks)) && !bank_ready[!prep_bank]));
	assign debug_tile_publish = (((((tile_mode && !cancel) && !response_failure) && (state == 5'd17)) && (head_valid[read_band] || (cursors[read_band] >= counts[read_band]))) && !(head_valid[read_band] && (heads[read_band][31:19] == prepare_block[12:0]))) && (read_band == 3);
	assign debug_tile_release = ((tile_mode && dense_valid) && dense_ready) && (tile_emit_index == 63);
	assign debug_prefetch_offer = prefetch_offer;
	assign debug_prefetch_launch = prefetch_launch;
	assign debug_write_slot_valid = write_slot_valid;
	assign debug_assembler_full = assembly_bytes == 16;
	assign debug_state = state;
	assign debug_return_state = return_state;
	assign debug_outstanding = outstanding;
	assign debug_phase = phase;
	assign debug_assembly_bytes = assembly_bytes;
	assign debug_cache_valid = cache_valid;
	assign debug_head_valid = head_valid;
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [15:0] sv2v_cast_16;
		input reg [15:0] inp;
		sv2v_cast_16 = inp;
	endfunction
	function automatic [4:0] sv2v_cast_5;
		input reg [4:0] inp;
		sv2v_cast_5 = inp;
	endfunction
	function automatic [17:0] sv2v_cast_18;
		input reg [17:0] inp;
		sv2v_cast_18 = inp;
	endfunction
	function automatic signed [1:0] sv2v_cast_2_signed;
		input reg signed [1:0] inp;
		sv2v_cast_2_signed = inp;
	endfunction
	always_comb begin
		response_failure = mem_rsp_valid && ((!outstanding || (mem_rsp_epoch != request_epoch)) || mem_rsp_error);
		plan_start1 = 32 + aligned(sv2v_cast_32(begin_blocks) * 2);
		plan_start2 = plan_start1 + aligned(begin_count1 * 4);
		plan_start3 = plan_start2 + aligned(begin_count2 * 4);
		plan_used = (begin_raw ? 32 + (sv2v_cast_32(begin_blocks) * 128) : plan_start3 + aligned(begin_count3 * 4));
		read_word = sv2v_cast_32(cache_data[read_segment] >> (8 * read_address[3:0]));
		read_half = sv2v_cast_16(cache_data[0] >> (8 * read_address[3:0]));
		read_position = (sv2v_cast_32(read_word[31:19]) * 64) + sv2v_cast_32(zigzag(read_word[18:13]));
		cancel = reset || (abort_valid && (abort_epoch == active_epoch));
		begin_ready = ((state == 5'd0) && !outstanding) && !cancel;
		coef_ready = (state == 5'd1) && !cancel;
		band_end_ready = ((state == 5'd1) && !coef_valid) && !cancel;
		seal_ready = ((state == 5'd4) && !cancel) && (!overlap_mode || ((!write_slot_valid && !outstanding) && (assembly_bytes == 0)));
		slot_available = !write_slot_valid || (((outstanding && mem_rsp_valid) && (mem_rsp_epoch == request_epoch)) && !mem_rsp_error);
		busy = ((state != 5'd0) && (state != 5'd23)) && (state != 5'd24);
		dense_valid = (tile_mode ? (((((bank_ready[emit_bank] && sealed) && (error == 0)) && (state != 5'd24)) && (state != 5'd25)) && !cancel) && !response_failure : (((state == 5'd20) || (state == 5'd22)) && !cancel) && !(prefetch_offer && response_failure));
		dense_block = (tile_mode ? bank_block[emit_bank] : output_block);
		dense_index = (tile_mode ? tile_emit_index : output_index);
		dense_value = (tile_mode ? (tile_valid[emit_bank][tile_emit_index] ? tile[emit_bank][tile_emit_index] : 16'sd0) : (raw_mode ? raw_value : (tile_valid[0][output_index] ? tile[0][output_index] : 16'sd0)));
		dense_epoch = (tile_mode ? bank_epoch[emit_bank] : active_epoch);
		mem_req_valid = ((((state == 5'd8) || (state == 5'd10)) || (((write_slot_valid && !outstanding) && (state != 5'd25)) && (state != 5'd24))) || (((prefetch_offer && !outstanding) && (state != 5'd25)) && (state != 5'd24))) && !cancel;
		mem_req_write = (state == 5'd8) || write_slot_valid;
		mem_req_addr = transfer_address;
		mem_req_data = transfer_data;
		mem_req_epoch = request_epoch;
		mem_rsp_ready = 1;
		input_zigzag = zigzag(coef_index);
		input_position = (raw_mode ? (sv2v_cast_32(coef_block) * 64) + sv2v_cast_32(coef_index) : (phase == 0 ? sv2v_cast_32(coef_block) : (sv2v_cast_32(coef_block) * 64) + sv2v_cast_32(input_zigzag)));
		input_bad = (((((coef_epoch != active_epoch) || (coef_band != phase[1:0])) || (coef_block >= sv2v_cast_16(blocks))) || (coef_value < -2048)) || (coef_value > 2048)) || (written >= counts[phase[1:0]]);
		debug_write_enqueue = (((overlap_mode && !cancel) && slot_available) && !(mem_rsp_valid && ((!outstanding || (mem_rsp_epoch != request_epoch)) || mem_rsp_error))) && ((((state == 5'd2) && ((assembly_bytes + sv2v_cast_5(pending_bytes)) == 16)) || (state == 5'd26)) || (((((((state == 5'd1) && !coef_valid) && band_end_valid) && (assembly_bytes != 0)) && (band_end_epoch == active_epoch)) && (band_end_band == phase[1:0])) && (written == counts[phase[1:0]])));
		candidate_valid = 0;
		candidate_segment = 0;
		candidate_address = 0;
		candidate_word_address = 0;
		if ((((((prefetch_mode && !tile_mode) && sealed) && !prefetch_offer) && !outstanding) && !cancel) && (error == 0)) begin
			if (((state == 5'd20) && !raw_mode) && ((sv2v_cast_17(output_block) + 1) < blocks)) begin
				candidate_word_address = 32 + ((sv2v_cast_32(output_block) + 1) * 2);
				if (!cache_valid[0] || (cache_address[0] != sv2v_cast_18(candidate_word_address & 32'hfffffff0))) begin
					candidate_valid = 1;
					candidate_segment = 0;
					candidate_address = sv2v_cast_18(candidate_word_address & 32'hfffffff0);
				end
				begin : sv2v_autoblock_3
					integer b;
					for (b = 1; b <= 3; b = b + 1)
						begin
							candidate_word_address = starts[b] + (cursors[b] * 4);
							if ((!candidate_valid && (cursors[b] < counts[b])) && (!cache_valid[b] || (cache_address[b] != sv2v_cast_18(candidate_word_address & 32'hfffffff0)))) begin
								candidate_valid = 1;
								candidate_segment = sv2v_cast_2_signed(b);
								candidate_address = sv2v_cast_18(candidate_word_address & 32'hfffffff0);
							end
						end
				end
			end
			else if (((state == 5'd22) && raw_mode) && ((((sv2v_cast_32(output_block) * 64) + sv2v_cast_32(output_index)) + 1) < (sv2v_cast_32(blocks) * 64))) begin
				candidate_word_address = 32 + ((((sv2v_cast_32(output_block) * 64) + sv2v_cast_32(output_index)) + 1) * 2);
				if (!cache_valid[0] || (cache_address[0] != sv2v_cast_18(candidate_word_address & 32'hfffffff0))) begin
					candidate_valid = 1;
					candidate_segment = 0;
					candidate_address = sv2v_cast_18(candidate_word_address & 32'hfffffff0);
				end
			end
		end
		debug_prefetch_use = (!cancel && !response_failure) && (((((state == 5'd16) && cache_valid[0]) && prefetched_valid[0]) && (cache_address[0] == sv2v_cast_18(read_address & 32'hfffffff0))) || ((((state == 5'd19) && cache_valid[read_segment]) && prefetched_valid[read_segment]) && (cache_address[read_segment] == sv2v_cast_18(read_address & 32'hfffffff0))));
		prefetch_launch = candidate_valid;
		prefetch_complete = (((prefetch_offer && outstanding) && mem_rsp_valid) && (mem_rsp_epoch == request_epoch)) && !mem_rsp_error;
		if (raw_mode)
			input_bad = input_bad || (input_position != written);
		else if (phase == 0)
			input_bad = (input_bad || (coef_index != 0)) || (sv2v_cast_32(coef_block) != written);
		else
			input_bad = ((input_bad || !band_matches(coef_band, coef_index)) || (coef_value == 0)) || (previous_valid && (input_position <= previous_position));
	end
	function automatic [18:0] sv2v_cast_19;
		input reg [18:0] inp;
		sv2v_cast_19 = inp;
	endfunction
	function automatic [127:0] sv2v_cast_128;
		input reg [127:0] inp;
		sv2v_cast_128 = inp;
	endfunction
	always_ff @(posedge clk)
		if (reset || (abort_valid && (abort_epoch == active_epoch))) begin
			sealed <= 0;
			done <= 0;
			error <= 0;
			cache_valid <= 0;
			head_valid <= 0;
			assembly_bytes <= 0;
			write_slot_valid <= 0;
			prefetch_offer <= 0;
			prefetched_valid <= 0;
			bank_ready <= 0;
			tile_preparing <= 0;
			tile_valid[0] <= 0;
			tile_valid[1] <= 0;
			tile_overlap_mode <= 0;
			if (outstanding && (!mem_rsp_valid || (mem_rsp_epoch != request_epoch))) begin
				state <= 5'd25;
				if (mem_rsp_valid)
					error <= 6;
			end
			else begin
				state <= 5'd0;
				outstanding <= 0;
			end
		end
		else if (mem_rsp_valid && (!outstanding || (mem_rsp_epoch != request_epoch))) begin
			error <= 6;
			sealed <= 0;
			done <= 0;
			write_slot_valid <= 0;
			assembly_bytes <= 0;
			prefetch_offer <= 0;
			cache_valid <= 0;
			prefetched_valid <= 0;
			bank_ready <= 0;
			tile_preparing <= 0;
			state <= (outstanding ? 5'd25 : 5'd24);
		end
		else if (state == 5'd25) begin
			if (mem_rsp_valid && outstanding) begin
				outstanding <= 0;
				state <= 5'd0;
			end
			else if (!outstanding)
				state <= 5'd0;
		end
		else if (((prefetch_offer && outstanding) && mem_rsp_valid) && mem_rsp_error) begin
			outstanding <= 0;
			prefetch_offer <= 0;
			cache_valid <= 0;
			prefetched_valid <= 0;
			error <= 5;
			sealed <= 0;
			done <= 0;
			state <= 5'd24;
		end
		else if ((((overlap_mode && write_slot_valid) && outstanding) && mem_rsp_valid) && mem_rsp_error) begin
			outstanding <= 0;
			write_slot_valid <= 0;
			assembly_bytes <= 0;
			error <= 5;
			sealed <= 0;
			done <= 0;
			state <= 5'd24;
		end
		else begin
			if ((tile_mode && dense_valid) && dense_ready) begin
				if (tile_emit_index == 63) begin
					bank_ready[emit_bank] <= 0;
					tile_emit_index <= 0;
					emit_bank <= !emit_bank;
				end
				else
					tile_emit_index <= tile_emit_index + 1;
			end
			if (overlap_mode && write_slot_valid) begin
				if ((!outstanding && mem_req_valid) && mem_req_ready)
					outstanding <= 1;
				if (outstanding && mem_rsp_valid) begin
					outstanding <= 0;
					write_slot_valid <= 0;
				end
			end
			if (debug_prefetch_use) begin
				if (state == 5'd16)
					prefetched_valid[0] <= 0;
				else
					prefetched_valid[read_segment] <= 0;
			end
			if (prefetch_launch) begin
				transfer_address <= candidate_address;
				request_epoch <= active_epoch;
				prefetch_segment <= candidate_segment;
				prefetch_offer <= 1;
			end
			if (prefetch_offer) begin
				if ((!outstanding && mem_req_valid) && mem_req_ready)
					outstanding <= 1;
				if (prefetch_complete) begin
					outstanding <= 0;
					prefetch_offer <= 0;
					cache_data[prefetch_segment] <= mem_rsp_data;
					cache_address[prefetch_segment] <= transfer_address;
					cache_valid[prefetch_segment] <= 1;
					prefetched_valid[prefetch_segment] <= 1;
				end
			end
			case (state)
				5'd0:
					if (begin_valid) begin
						sealed <= 0;
						done <= 0;
						error <= 0;
						if (epoch_seen && (begin_epoch <= last_epoch)) begin
							error <= 2;
							state <= 5'd24;
						end
						else if (((((((begin_blocks == 0) || (begin_blocks > 8192)) || (begin_count1 > (sv2v_cast_32(begin_blocks) * 5))) || (begin_count2 > (sv2v_cast_32(begin_blocks) * 15))) || (begin_count3 > (sv2v_cast_32(begin_blocks) * 43))) || (begin_raw && (((begin_count1 != 0) || (begin_count2 != 0)) || (begin_count3 != 0)))) || (plan_used > 262144)) begin
							error <= 1;
							state <= 5'd24;
						end
						else begin
							epoch_seen <= 1;
							last_epoch <= begin_epoch;
							active_epoch <= begin_epoch;
							blocks <= begin_blocks;
							raw_mode <= begin_raw;
							tile_overlap_mode <= begin_tile_overlap;
							bank_ready <= 0;
							tile_preparing <= 0;
							prep_bank <= 0;
							emit_bank <= 0;
							prepare_block <= 0;
							tile_emit_index <= 0;
							tile_valid[0] <= 0;
							tile_valid[1] <= 0;
							serial_clear <= begin_serial_clear;
							overlap_mode <= begin_overlap;
							prefetch_mode <= begin_prefetch;
							prefetch_offer <= 0;
							prefetched_valid <= 0;
							write_slot_valid <= 0;
							used_bytes <= sv2v_cast_19(plan_used);
							counts[0] <= (begin_raw ? sv2v_cast_32(begin_blocks) * 64 : sv2v_cast_32(begin_blocks));
							counts[1] <= begin_count1;
							counts[2] <= begin_count2;
							counts[3] <= begin_count3;
							starts[0] <= 32;
							starts[1] <= plan_start1;
							starts[2] <= plan_start2;
							starts[3] <= plan_start3;
							phase <= 0;
							written <= 0;
							previous_valid <= 0;
							assembler <= 0;
							assembly_bytes <= 0;
							write_address <= 32;
							cache_valid <= 0;
							head_valid <= 0;
							begin : sv2v_autoblock_4
								integer b;
								for (b = 1; b <= 3; b = b + 1)
									cursors[b] <= 0;
							end
							state <= 5'd1;
						end
					end
				5'd1:
					if (coef_valid) begin
						if (input_bad) begin
							error <= (coef_epoch != active_epoch ? 2 : 3);
							if (overlap_mode) begin
								write_slot_valid <= 0;
								assembly_bytes <= 0;
								state <= ((outstanding && !mem_rsp_valid) || ((!outstanding && mem_req_valid) && mem_req_ready) ? 5'd25 : 5'd24);
							end
							else
								state <= 5'd24;
						end
						else begin
							pending_record <= (raw_mode || (phase == 0) ? {16'd0, coef_value} : {coef_block[12:0], coef_index, coef_value[12:0]});
							pending_bytes <= (raw_mode || (phase == 0) ? 2 : 4);
							pending_position <= input_position;
							state <= 5'd2;
						end
					end
					else if (band_end_valid) begin
						if (((band_end_epoch != active_epoch) || (band_end_band != phase[1:0])) || (written != counts[phase[1:0]])) begin
							error <= (band_end_epoch != active_epoch ? 2 : 4);
							if (overlap_mode) begin
								write_slot_valid <= 0;
								assembly_bytes <= 0;
								state <= ((outstanding && !mem_rsp_valid) || ((!outstanding && mem_req_valid) && mem_req_ready) ? 5'd25 : 5'd24);
							end
							else
								state <= 5'd24;
						end
						else if (assembly_bytes != 0) begin
							if (overlap_mode) begin
								return_state <= 5'd3;
								if (slot_available) begin
									transfer_data <= assembler;
									transfer_address <= sv2v_cast_18(write_address);
									request_epoch <= active_epoch;
									write_slot_valid <= 1;
									write_address <= write_address + 16;
									state <= 5'd3;
								end
								else
									state <= 5'd26;
							end
							else begin
								transfer_data <= assembler;
								transfer_address <= sv2v_cast_18(write_address);
								request_epoch <= active_epoch;
								return_state <= 5'd3;
								state <= 5'd8;
							end
						end
						else
							state <= 5'd3;
					end
				5'd2: begin
					if (pending_bytes == 2)
						assembler[8 * assembly_bytes+:16] <= pending_record[15:0];
					else
						assembler[8 * assembly_bytes+:32] <= pending_record;
					written <= written + 1;
					previous_position <= pending_position;
					previous_valid <= 1;
					if ((assembly_bytes + sv2v_cast_5(pending_bytes)) == 16) begin
						return_state <= 5'd1;
						if (overlap_mode) begin
							if (slot_available) begin
								transfer_data <= assembler | (sv2v_cast_128(pending_record) << (8 * assembly_bytes));
								transfer_address <= sv2v_cast_18(write_address);
								request_epoch <= active_epoch;
								write_slot_valid <= 1;
								write_address <= write_address + 16;
								state <= 5'd1;
								assembler <= 0;
								assembly_bytes <= 0;
							end
							else begin
								assembly_bytes <= 16;
								state <= 5'd26;
							end
						end
						else begin
							transfer_data <= assembler | (sv2v_cast_128(pending_record) << (8 * assembly_bytes));
							transfer_address <= sv2v_cast_18(write_address);
							request_epoch <= active_epoch;
							state <= 5'd8;
							assembler <= 0;
							assembly_bytes <= 0;
						end
					end
					else begin
						assembly_bytes <= assembly_bytes + sv2v_cast_5(pending_bytes);
						state <= 5'd1;
					end
				end
				5'd26:
					if (slot_available) begin
						transfer_data <= assembler;
						transfer_address <= sv2v_cast_18(write_address);
						request_epoch <= active_epoch;
						write_slot_valid <= 1;
						write_address <= write_address + 16;
						assembler <= 0;
						assembly_bytes <= 0;
						state <= return_state;
					end
				5'd3: begin
					assembler <= 0;
					assembly_bytes <= 0;
					written <= 0;
					previous_valid <= 0;
					if (raw_mode || (phase == 3)) begin
						phase <= 4;
						state <= 5'd4;
					end
					else begin
						phase <= phase + 1;
						write_address <= starts[phase[1:0] + 2'd1];
						state <= 5'd1;
					end
				end
				5'd4:
					if (seal_valid && seal_ready) begin
						if (seal_epoch != active_epoch) begin
							error <= 2;
							state <= 5'd24;
						end
						else
							state <= 5'd5;
					end
				5'd5: begin
					transfer_data <= {counts[1], 31'd0, raw_mode, 15'd0, blocks, 32'h43393150};
					transfer_address <= 0;
					request_epoch <= active_epoch;
					return_state <= 5'd6;
					state <= 5'd8;
				end
				5'd6: begin
					transfer_data <= {45'h000000000000, used_bytes, counts[3], counts[2]};
					transfer_address <= 16;
					request_epoch <= active_epoch;
					return_state <= 5'd7;
					state <= 5'd8;
				end
				5'd7: begin
					sealed <= 1;
					transfer_address <= 0;
					return_state <= 5'd12;
					state <= 5'd10;
				end
				5'd8:
					if (mem_req_ready) begin
						outstanding <= 1;
						state <= 5'd9;
					end
				5'd9:
					if (mem_rsp_valid) begin
						outstanding <= 0;
						if (mem_rsp_error) begin
							error <= 5;
							sealed <= 0;
							state <= 5'd24;
							bank_ready <= 0;
							tile_preparing <= 0;
						end
						else begin
							write_address <= write_address + 16;
							state <= return_state;
						end
					end
				5'd10:
					if (mem_req_ready) begin
						outstanding <= 1;
						state <= 5'd11;
					end
				5'd11:
					if (mem_rsp_valid) begin
						outstanding <= 0;
						if (mem_rsp_error) begin
							error <= 5;
							sealed <= 0;
							state <= 5'd24;
							bank_ready <= 0;
							tile_preparing <= 0;
						end
						else begin
							transfer_data <= mem_rsp_data;
							if ((return_state != 5'd12) && (return_state != 5'd13)) begin
								cache_data[read_segment] <= mem_rsp_data;
								cache_address[read_segment] <= transfer_address;
								cache_valid[read_segment] <= 1;
								prefetched_valid[read_segment] <= 0;
							end
							state <= return_state;
						end
					end
				5'd12: begin
					descriptor_low <= transfer_data;
					transfer_address <= 16;
					return_state <= 5'd13;
					state <= 5'd10;
				end
				5'd13:
					if ((descriptor_low != {counts[1], 31'd0, raw_mode, 15'd0, blocks, 32'h43393150}) || (transfer_data != {45'h000000000000, used_bytes, counts[3], counts[2]})) begin
						error <= 7;
						sealed <= 0;
						state <= 5'd24;
					end
					else begin
						output_block <= 0;
						output_index <= 0;
						clear_index <= 0;
						if (tile_mode) begin
							prep_bank <= 0;
							emit_bank <= 0;
							prepare_block <= 0;
							tile_emit_index <= 0;
							bank_ready <= 0;
							tile_preparing <= 1;
							bank_block[0] <= 0;
							bank_epoch[0] <= active_epoch;
						end
						state <= (raw_mode ? 5'd21 : 5'd14);
					end
				5'd14: begin
					tile_valid[prep_bank] <= 0;
					if (serial_clear)
						tile[prep_bank][clear_index] <= 0;
					if (!serial_clear || (clear_index == 63)) begin
						clear_index <= 0;
						state <= 5'd15;
					end
					else
						clear_index <= clear_index + 1;
				end
				5'd15, 5'd21: begin
					read_address <= 32 + (raw_mode ? ((sv2v_cast_32(output_block) * 64) + sv2v_cast_32(output_index)) * 2 : (tile_mode ? sv2v_cast_32(prepare_block) : sv2v_cast_32(output_block)) * 2);
					read_segment <= 0;
					state <= 5'd16;
				end
				5'd16:
					if (!cache_valid[0] || (cache_address[0] != sv2v_cast_18(read_address & 32'hfffffff0))) begin
						transfer_address <= sv2v_cast_18(read_address & 32'hfffffff0);
						return_state <= 5'd16;
						state <= 5'd10;
					end
					else if ((read_half < -2048) || (read_half > 2048)) begin
						error <= 3;
						sealed <= 0;
						state <= 5'd24;
					end
					else if (raw_mode) begin
						raw_value <= sv2v_cast_16(cache_data[0] >> (8 * read_address[3:0]));
						state <= 5'd22;
					end
					else begin
						tile[prep_bank][0] <= sv2v_cast_16(cache_data[0] >> (8 * read_address[3:0]));
						tile_valid[prep_bank][0] <= 1;
						read_band <= 1;
						state <= 5'd17;
					end
				5'd17:
					if (!head_valid[read_band] && (cursors[read_band] < counts[read_band]))
						state <= 5'd18;
					else if (head_valid[read_band] && (heads[read_band][31:19] == (tile_mode ? prepare_block[12:0] : output_block[12:0]))) begin
						tile[prep_bank][heads[read_band][18:13]] <= {{3 {heads[read_band][12]}}, heads[read_band][12:0]};
						tile_valid[prep_bank][heads[read_band][18:13]] <= 1;
						head_valid[read_band] <= 0;
					end
					else if (read_band == 3) begin
						if (tile_mode) begin
							bank_ready[prep_bank] <= 1;
							tile_preparing <= 0;
							state <= 5'd28;
						end
						else begin
							output_index <= 0;
							state <= 5'd20;
						end
					end
					else
						read_band <= read_band + 1;
				5'd18: begin
					read_segment <= read_band;
					read_address <= starts[read_band] + (cursors[read_band] * 4);
					state <= 5'd19;
				end
				5'd19:
					if (!cache_valid[read_segment] || (cache_address[read_segment] != sv2v_cast_18(read_address & 32'hfffffff0))) begin
						transfer_address <= sv2v_cast_18(read_address & 32'hfffffff0);
						return_state <= 5'd19;
						state <= 5'd10;
					end
					else if ((((((sv2v_cast_17(read_word[31:19]) >= blocks) || !band_matches(read_band, read_word[18:13])) || ($signed(read_word[12:0]) == 0)) || ($signed(read_word[12:0]) < -2048)) || ($signed(read_word[12:0]) > 2048)) || ((cursors[read_band] != 0) && (read_position <= ((sv2v_cast_32(heads[read_band][31:19]) * 64) + sv2v_cast_32(zigzag(heads[read_band][18:13])))))) begin
						error <= 3;
						sealed <= 0;
						state <= 5'd24;
					end
					else begin
						heads[read_band] <= read_word;
						cursors[read_band] <= cursors[read_band] + 1;
						head_valid[read_band] <= 1;
						state <= 5'd17;
					end
				5'd20, 5'd22:
					if (dense_ready) begin
						if (output_index == 63) begin
							if ((sv2v_cast_17(output_block) + 1) == blocks) begin
								done <= 1;
								state <= 5'd23;
							end
							else begin
								output_block <= output_block + 1;
								output_index <= 0;
								if (prefetch_mode && (prefetch_launch || (prefetch_offer && !prefetch_complete))) begin
									return_state <= (raw_mode ? 5'd21 : 5'd14);
									state <= 5'd27;
								end
								else
									state <= (raw_mode ? 5'd21 : 5'd14);
							end
						end
						else begin
							output_index <= output_index + 1;
							if (raw_mode) begin
								if (prefetch_mode && (prefetch_launch || (prefetch_offer && !prefetch_complete))) begin
									return_state <= 5'd21;
									state <= 5'd27;
								end
								else
									state <= 5'd21;
							end
						end
					end
				5'd27:
					if (prefetch_complete || (!prefetch_offer && !outstanding))
						state <= return_state;
				5'd28:
					if ((sv2v_cast_17(prepare_block) + 1) == blocks)
						state <= 5'd29;
					else if (!bank_ready[!prep_bank]) begin
						prep_bank <= !prep_bank;
						prepare_block <= prepare_block + 1;
						bank_block[!prep_bank] <= prepare_block + 1;
						bank_epoch[!prep_bank] <= active_epoch;
						tile_preparing <= 1;
						clear_index <= 0;
						state <= 5'd14;
					end
				5'd29:
					;
				5'd23, 5'd24:
					;
				default: state <= 5'd24;
			endcase
			if ((((tile_mode && dense_valid) && dense_ready) && (tile_emit_index == 63)) && ((sv2v_cast_17(bank_block[emit_bank]) + 1) == blocks)) begin
				done <= 1;
				state <= 5'd23;
			end
		end
endmodule
module br88_packet_ingress_v91h (
	clk,
	reset,
	start,
	abort_packet,
	packet_bytes,
	blocks,
	epoch,
	word16,
	serial_mode,
	in_valid,
	in_ready,
	in_data,
	in_last,
	out_valid,
	out_ready,
	out_block,
	out_index,
	out_coefficient,
	out_epoch,
	meta_valid,
	meta_ready,
	meta_blocks,
	meta_count1,
	meta_count2,
	meta_count3,
	meta_epoch,
	meta_raw,
	out_band,
	band_end_valid,
	band_end_ready,
	band_end_band,
	band_end_epoch,
	done,
	error,
	count_cycles,
	count_inputs,
	count_outputs,
	count_output_stall,
	debug_state,
	stage_read_req,
	stage_read_rsp,
	stage_write,
	stage_pending,
	stage_context_active,
	stage_cancel,
	stage_word_valid,
	stage_word_ready,
	stage_read_addr,
	stage_rsp_addr,
	stage_write_addr,
	stage_req_epoch,
	stage_rsp_epoch,
	stage_read_data,
	stage_write_data,
	stage_buffer_bytes,
	stage_buffer_highwater,
	stage_purpose,
	count_stage_reads,
	count_stage_responses,
	count_stage_writes,
	count_stage_fetch_wait,
	count_stage_word_hold
);
	parameter integer MAX_PACKET_BYTES = 49152;
	parameter integer SYNC_STAGING = 1;
	input wire clk;
	input wire reset;
	input wire start;
	input wire abort_packet;
	input wire [31:0] packet_bytes;
	input wire [16:0] blocks;
	input wire [31:0] epoch;
	input wire word16;
	input wire serial_mode;
	input wire in_valid;
	output wire in_ready;
	input wire [7:0] in_data;
	input wire in_last;
	output wire out_valid;
	input wire out_ready;
	output wire [15:0] out_block;
	output wire [5:0] out_index;
	output wire signed [15:0] out_coefficient;
	output wire [31:0] out_epoch;
	output wire meta_valid;
	input wire meta_ready;
	output wire [16:0] meta_blocks;
	output wire [31:0] meta_count1;
	output wire [31:0] meta_count2;
	output wire [31:0] meta_count3;
	output wire [31:0] meta_epoch;
	output wire meta_raw;
	output wire [1:0] out_band;
	output wire band_end_valid;
	input wire band_end_ready;
	output wire [1:0] band_end_band;
	output wire [31:0] band_end_epoch;
	output wire done;
	output wire [3:0] error;
	output wire [63:0] count_cycles;
	output wire [63:0] count_inputs;
	output wire [63:0] count_outputs;
	output wire [63:0] count_output_stall;
	output wire [3:0] debug_state;
	output wire stage_read_req;
	output wire stage_read_rsp;
	output wire stage_write;
	output wire stage_pending;
	output wire stage_context_active;
	output wire stage_cancel;
	output wire stage_word_valid;
	output wire stage_word_ready;
	output wire [31:0] stage_read_addr;
	output wire [31:0] stage_rsp_addr;
	output wire [31:0] stage_write_addr;
	output wire [31:0] stage_req_epoch;
	output wire [31:0] stage_rsp_epoch;
	output wire [7:0] stage_read_data;
	output wire [7:0] stage_write_data;
	output wire [5:0] stage_buffer_bytes;
	output wire [5:0] stage_buffer_highwater;
	output wire [2:0] stage_purpose;
	output wire [63:0] count_stage_reads;
	output wire [63:0] count_stage_responses;
	output wire [63:0] count_stage_writes;
	output wire [63:0] count_stage_fetch_wait;
	output wire [63:0] count_stage_word_hold;
	generate
		if (SYNC_STAGING == 0) begin : legacy
			br88_packet_ingress #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) ingress(
				.clk(clk),
				.reset(reset),
				.start(start),
				.abort_packet(abort_packet),
				.packet_bytes(packet_bytes),
				.blocks(blocks),
				.epoch(epoch),
				.word16(word16),
				.serial_mode(serial_mode),
				.in_valid(in_valid),
				.in_ready(in_ready),
				.in_data(in_data),
				.in_last(in_last),
				.out_valid(out_valid),
				.out_ready(out_ready),
				.out_block(out_block),
				.out_index(out_index),
				.out_coefficient(out_coefficient),
				.out_epoch(out_epoch),
				.meta_valid(meta_valid),
				.meta_ready(meta_ready),
				.meta_blocks(meta_blocks),
				.meta_count1(meta_count1),
				.meta_count2(meta_count2),
				.meta_count3(meta_count3),
				.meta_epoch(meta_epoch),
				.meta_raw(meta_raw),
				.out_band(out_band),
				.band_end_valid(band_end_valid),
				.band_end_ready(band_end_ready),
				.band_end_band(band_end_band),
				.band_end_epoch(band_end_epoch),
				.done(done),
				.error(error),
				.count_cycles(count_cycles),
				.count_inputs(count_inputs),
				.count_outputs(count_outputs),
				.count_output_stall(count_output_stall),
				.debug_state(debug_state)
			);
			assign stage_read_req = 1'sb0;
			assign stage_read_rsp = 1'sb0;
			assign stage_write = 1'sb0;
			assign stage_pending = 1'sb0;
			assign stage_context_active = 1'sb0;
			assign stage_cancel = (reset || start) || abort_packet;
			assign stage_word_valid = 1'sb0;
			assign stage_word_ready = 1'sb0;
			assign stage_read_addr = 1'sb0;
			assign stage_rsp_addr = 1'sb0;
			assign stage_write_addr = 1'sb0;
			assign stage_req_epoch = 1'sb0;
			assign stage_rsp_epoch = 1'sb0;
			assign stage_read_data = 1'sb0;
			assign stage_write_data = 1'sb0;
			assign stage_buffer_bytes = 1'sb0;
			assign stage_buffer_highwater = 1'sb0;
			assign stage_purpose = 1'sb0;
			assign count_stage_reads = 1'sb0;
			assign count_stage_responses = 1'sb0;
			assign count_stage_writes = 1'sb0;
			assign count_stage_fetch_wait = 1'sb0;
			assign count_stage_word_hold = 1'sb0;
		end
		else begin : synchronous
			br88_packet_ingress_sync_v91h #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) ingress(
				.clk(clk),
				.reset(reset),
				.start(start),
				.abort_packet(abort_packet),
				.packet_bytes(packet_bytes),
				.blocks(blocks),
				.epoch(epoch),
				.word16(word16),
				.serial_mode(serial_mode),
				.in_valid(in_valid),
				.in_ready(in_ready),
				.in_data(in_data),
				.in_last(in_last),
				.out_valid(out_valid),
				.out_ready(out_ready),
				.out_block(out_block),
				.out_index(out_index),
				.out_coefficient(out_coefficient),
				.out_epoch(out_epoch),
				.meta_valid(meta_valid),
				.meta_ready(meta_ready),
				.meta_blocks(meta_blocks),
				.meta_count1(meta_count1),
				.meta_count2(meta_count2),
				.meta_count3(meta_count3),
				.meta_epoch(meta_epoch),
				.meta_raw(meta_raw),
				.out_band(out_band),
				.band_end_valid(band_end_valid),
				.band_end_ready(band_end_ready),
				.band_end_band(band_end_band),
				.band_end_epoch(band_end_epoch),
				.done(done),
				.error(error),
				.count_cycles(count_cycles),
				.count_inputs(count_inputs),
				.count_outputs(count_outputs),
				.count_output_stall(count_output_stall),
				.debug_state(debug_state),
				.stage_read_req(stage_read_req),
				.stage_read_rsp(stage_read_rsp),
				.stage_write(stage_write),
				.stage_pending(stage_pending),
				.stage_context_active(stage_context_active),
				.stage_cancel(stage_cancel),
				.stage_word_valid(stage_word_valid),
				.stage_word_ready(stage_word_ready),
				.stage_read_addr(stage_read_addr),
				.stage_rsp_addr(stage_rsp_addr),
				.stage_write_addr(stage_write_addr),
				.stage_req_epoch(stage_req_epoch),
				.stage_rsp_epoch(stage_rsp_epoch),
				.stage_read_data(stage_read_data),
				.stage_write_data(stage_write_data),
				.stage_buffer_bytes(stage_buffer_bytes),
				.stage_buffer_highwater(stage_buffer_highwater),
				.stage_purpose(stage_purpose),
				.count_stage_reads(count_stage_reads),
				.count_stage_responses(count_stage_responses),
				.count_stage_writes(count_stage_writes),
				.count_stage_fetch_wait(count_stage_fetch_wait),
				.count_stage_word_hold(count_stage_word_hold)
			);
		end
	endgenerate
endmodule
module br88_packet_ingress_sync_v91h (
	clk,
	reset,
	start,
	abort_packet,
	packet_bytes,
	blocks,
	epoch,
	word16,
	serial_mode,
	in_valid,
	in_ready,
	in_data,
	in_last,
	out_valid,
	out_ready,
	out_block,
	out_index,
	out_coefficient,
	out_epoch,
	meta_valid,
	meta_ready,
	meta_blocks,
	meta_count1,
	meta_count2,
	meta_count3,
	meta_epoch,
	meta_raw,
	out_band,
	band_end_valid,
	band_end_ready,
	band_end_band,
	band_end_epoch,
	done,
	error,
	count_cycles,
	count_inputs,
	count_outputs,
	count_output_stall,
	debug_state,
	stage_read_req,
	stage_read_rsp,
	stage_write,
	stage_pending,
	stage_context_active,
	stage_cancel,
	stage_word_valid,
	stage_word_ready,
	stage_read_addr,
	stage_rsp_addr,
	stage_write_addr,
	stage_req_epoch,
	stage_rsp_epoch,
	stage_read_data,
	stage_write_data,
	stage_buffer_bytes,
	stage_buffer_highwater,
	stage_purpose,
	count_stage_reads,
	count_stage_responses,
	count_stage_writes,
	count_stage_fetch_wait,
	count_stage_word_hold
);
	parameter integer MAX_PACKET_BYTES = 49152;
	input wire clk;
	input wire reset;
	input wire start;
	input wire abort_packet;
	input wire [31:0] packet_bytes;
	input wire [16:0] blocks;
	input wire [31:0] epoch;
	input wire word16;
	input wire serial_mode;
	input wire in_valid;
	output reg in_ready;
	input wire [7:0] in_data;
	input wire in_last;
	output reg out_valid;
	input wire out_ready;
	output reg [15:0] out_block;
	output reg [5:0] out_index;
	output reg signed [15:0] out_coefficient;
	output reg [31:0] out_epoch;
	output reg meta_valid;
	input wire meta_ready;
	output reg [16:0] meta_blocks;
	output reg [31:0] meta_count1;
	output reg [31:0] meta_count2;
	output reg [31:0] meta_count3;
	output reg [31:0] meta_epoch;
	output reg meta_raw;
	output reg [1:0] out_band;
	output reg band_end_valid;
	input wire band_end_ready;
	output reg [1:0] band_end_band;
	output reg [31:0] band_end_epoch;
	output reg done;
	output reg [3:0] error;
	output reg [63:0] count_cycles;
	output reg [63:0] count_inputs;
	output reg [63:0] count_outputs;
	output reg [63:0] count_output_stall;
	output reg [3:0] debug_state;
	output reg stage_read_req;
	output reg stage_read_rsp;
	output reg stage_write;
	output reg stage_pending;
	output reg stage_context_active;
	output reg stage_cancel;
	output reg stage_word_valid;
	output reg stage_word_ready;
	output reg [31:0] stage_read_addr;
	output reg [31:0] stage_rsp_addr;
	output reg [31:0] stage_write_addr;
	output reg [31:0] stage_req_epoch;
	output reg [31:0] stage_rsp_epoch;
	output reg [7:0] stage_read_data;
	output reg [7:0] stage_write_data;
	output reg [5:0] stage_buffer_bytes;
	output reg [5:0] stage_buffer_highwater;
	output reg [2:0] stage_purpose;
	output reg [63:0] count_stage_reads;
	output reg [63:0] count_stage_responses;
	output reg [63:0] count_stage_writes;
	output reg [63:0] count_stage_fetch_wait;
	output reg [63:0] count_stage_word_hold;
	localparam [3:0] IDLE = 0;
	localparam [3:0] RECEIVE = 1;
	localparam [3:0] HEADER = 2;
	localparam [3:0] DESCRIPTOR = 3;
	localparam [3:0] CONTEXT_START = 4;
	localparam [3:0] CONTEXT_RUN = 5;
	localparam [3:0] RAW = 6;
	localparam [3:0] FINISHED = 7;
	localparam [3:0] FAILED = 8;
	localparam [3:0] METADATA = 9;
	localparam [3:0] CONTEXT_END = 10;
	localparam [3:0] RAW_END = 11;
	localparam [3:0] FETCH_REQ = 12;
	localparam [3:0] FETCH_WAIT = 13;
	localparam [2:0] F_HEADER = 0;
	localparam [2:0] F_DESCRIPTOR = 1;
	localparam [2:0] F_REPLAY = 2;
	localparam [2:0] F_RAW = 3;
	localparam integer AW = $clog2(MAX_PACKET_BYTES);
	reg [3:0] state;
	reg [3:0] fetch_return;
	reg [7:0] memory [0:MAX_PACKET_BYTES - 1];
	reg ram_valid;
	reg [7:0] ram_data;
	reg [31:0] ram_addr;
	reg [31:0] ram_epoch;
	reg [7:0] fetch_bytes [0:45];
	reg [5:0] fetch_index;
	reg [5:0] fetch_count;
	reg [5:0] buffer_bytes;
	reg [2:0] fetch_kind;
	reg [31:0] fetch_base;
	reg [31:0] fetch_address;
	reg [31:0] fetched_word;
	reg [31:0] size_bytes;
	reg [31:0] context_epoch;
	reg [31:0] received;
	reg [31:0] crc;
	reg [31:0] cursor;
	reg [16:0] context_blocks;
	reg mode16;
	reg mode_serial;
	reg raw_mode;
	reg descriptor_ready;
	reg word_valid;
	reg raw_valid;
	reg context_active;
	reg [1:0] band;
	reg [31:0] lengths [0:3];
	reg [31:0] counts [0:3];
	reg [31:0] offsets [0:3];
	reg [31:0] sizes [0:3];
	reg [7:0] k0s [0:3];
	reg [7:0] k1s [0:3];
	reg [31:0] descriptor_bits;
	reg [31:0] descriptor_bytes;
	reg [31:0] descriptor_limit;
	reg [31:0] replay_bits;
	reg [31:0] raw_position;
	reg [31:0] replay_word;
	reg [31:0] ctx_data;
	reg [5:0] ctx_bits;
	reg ctx_last;
	reg ctx_valid;
	wire ctx_ready;
	wire ctx_out_valid;
	wire ctx_done;
	wire [15:0] ctx_block;
	wire [5:0] ctx_index;
	wire signed [15:0] ctx_coefficient;
	reg signed [15:0] raw_coefficient;
	wire [31:0] ctx_epoch;
	wire [3:0] ctx_error;
	wire [31:0] unused_consumed;
	wire [63:0] unused_cycles;
	wire [63:0] unused_inputs;
	wire [63:0] unused_symbols;
	wire [63:0] unused_outputs;
	wire [63:0] unused_stall;
	wire [63:0] unused_wait;
	wire [63:0] unused_parser_cycles;
	wire [63:0] unused_parser_stall;
	wire [3:0] unused_debug;
	wire [6:0] unused_reservoir;
	reg cancelled;
	reg context_failure;
	function automatic [31:0] cached32;
		input integer at;
		cached32 = {fetch_bytes[at + 3], fetch_bytes[at + 2], fetch_bytes[at + 1], fetch_bytes[at]};
	endfunction
	function automatic [31:0] crc_byte;
		input reg [31:0] previous_crc;
		input reg [7:0] value;
		reg [31:0] c;
		begin
			c = previous_crc ^ {24'd0, value};
			begin : sv2v_autoblock_1
				integer j;
				for (j = 0; j < 8; j = j + 1)
					c = (c[0] ? (c >> 1) ^ 32'hedb88320 : c >> 1);
			end
			crc_byte = c;
		end
	endfunction
	task automatic fail_packet;
		input reg [3:0] code;
		begin
			state <= FAILED;
			error <= code;
			done <= 0;
			context_active <= 0;
			word_valid <= 0;
			raw_valid <= 0;
		end
	endtask
	task automatic begin_fetch;
		input reg [2:0] kind;
		input reg [5:0] bytes_to_fetch;
		input reg [31:0] base;
		input reg [3:0] continuation;
		begin
			fetch_kind <= kind;
			fetch_count <= bytes_to_fetch;
			fetch_index <= 0;
			fetch_base <= base;
			fetch_return <= continuation;
			buffer_bytes <= 0;
			state <= FETCH_REQ;
		end
	endtask
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [5:0] sv2v_cast_6;
		input reg [5:0] inp;
		sv2v_cast_6 = inp;
	endfunction
	function automatic [15:0] sv2v_cast_16;
		input reg [15:0] inp;
		sv2v_cast_16 = inp;
	endfunction
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	always_comb begin
		cancelled = (reset || abort_packet) || start;
		context_failure = context_active && (ctx_error != 0);
		in_ready = (state == RECEIVE) && !cancelled;
		fetch_address = fetch_base + sv2v_cast_32(fetch_index);
		if ((fetch_kind == F_HEADER) && (fetch_index >= 42))
			fetch_address = ((size_bytes - 4) + sv2v_cast_32(fetch_index)) - 42;
		if ((fetch_kind == F_DESCRIPTOR) && (fetch_index == 6))
			fetch_address = (fetch_base + lengths[band]) - 1;
		stage_read_req = ((((state == FETCH_REQ) && !cancelled) && (fetch_address < size_bytes)) && (fetch_address < MAX_PACKET_BYTES)) && !(context_active && ((ctx_error != 0) || ctx_done));
		stage_read_rsp = (ram_valid && !cancelled) && !context_failure;
		stage_write = in_valid && in_ready;
		stage_pending = state == FETCH_WAIT;
		stage_context_active = context_active;
		stage_cancel = cancelled || context_failure;
		stage_read_addr = fetch_address;
		stage_rsp_addr = ram_addr;
		stage_write_addr = received;
		stage_req_epoch = context_epoch;
		stage_rsp_epoch = ram_epoch;
		stage_read_data = ram_data;
		stage_write_data = in_data;
		stage_buffer_bytes = buffer_bytes;
		stage_purpose = fetch_kind;
		descriptor_bits = cached32(2);
		descriptor_bytes = (descriptor_bits >> 3) + sv2v_cast_32(descriptor_bits[2:0] != 0);
		case (band)
			1: descriptor_limit = sv2v_cast_32(context_blocks) * 5;
			2: descriptor_limit = sv2v_cast_32(context_blocks) * 15;
			3: descriptor_limit = sv2v_cast_32(context_blocks) * 43;
			default: descriptor_limit = sv2v_cast_32(context_blocks);
		endcase
		fetched_word = 0;
		begin : sv2v_autoblock_2
			integer j;
			for (j = 0; j < 4; j = j + 1)
				if (j < sv2v_cast_32_signed(fetch_count))
					fetched_word[31 - (8 * j)-:8] = (j == sv2v_cast_32_signed(fetch_index) ? ram_data : fetch_bytes[j]);
		end
		ctx_data = replay_word;
		ctx_bits = sv2v_cast_6(((sizes[band] - replay_bits) < (mode16 ? 16 : 32) ? sizes[band] - replay_bits : (mode16 ? 16 : 32)));
		ctx_last = (replay_bits + sv2v_cast_32(ctx_bits)) == sizes[band];
		ctx_valid = ((((state == CONTEXT_RUN) && word_valid) && (replay_bits < sizes[band])) && !cancelled) && !context_failure;
		stage_word_valid = ctx_valid;
		stage_word_ready = ctx_ready;
		out_valid = !cancelled && ((context_active && ctx_out_valid) || ((((state == RAW) && raw_valid) && (raw_coefficient >= -2048)) && (raw_coefficient <= 2048)));
		out_block = (raw_mode ? sv2v_cast_16(raw_position >> 6) : ctx_block);
		out_index = (raw_mode ? raw_position[5:0] : ctx_index);
		out_coefficient = (raw_mode ? raw_coefficient : ctx_coefficient);
		out_epoch = (raw_mode ? context_epoch : ctx_epoch);
		meta_valid = (state == METADATA) && !cancelled;
		meta_blocks = context_blocks;
		meta_count1 = counts[1];
		meta_count2 = counts[2];
		meta_count3 = counts[3];
		meta_epoch = context_epoch;
		meta_raw = raw_mode;
		out_band = (raw_mode ? 2'd0 : band);
		band_end_valid = ((state == CONTEXT_END) || (state == RAW_END)) && !cancelled;
		band_end_band = (state == RAW_END ? 2'd0 : band);
		band_end_epoch = context_epoch;
		debug_state = state;
	end
	function automatic [AW - 1:0] sv2v_cast_DE851;
		input reg [AW - 1:0] inp;
		sv2v_cast_DE851 = inp;
	endfunction
	always_ff @(posedge clk) begin
		if (stage_write)
			memory[sv2v_cast_DE851(received)] <= in_data;
		if (cancelled || context_failure)
			ram_valid <= 0;
		else begin
			ram_valid <= stage_read_req;
			if (stage_read_req) begin
				ram_data <= memory[sv2v_cast_DE851(fetch_address)];
				ram_addr <= fetch_address;
				ram_epoch <= context_epoch;
			end
		end
	end
	br88_context context_decoder(
		.clk(clk),
		.reset(reset),
		.start((state == CONTEXT_START) && !cancelled),
		.abort_context(abort_packet || start),
		.blocks(context_blocks),
		.band({6'd0, band}),
		.k0(k0s[band]),
		.k1(k1s[band]),
		.event_count(counts[band]),
		.stream_bits(sizes[band]),
		.epoch(context_epoch),
		.word16(mode16),
		.serial_mode(mode_serial),
		.in_valid(ctx_valid),
		.in_ready(ctx_ready),
		.in_data(ctx_data),
		.in_bits(ctx_bits),
		.in_last(ctx_last),
		.out_valid(ctx_out_valid),
		.out_ready((out_ready && context_active) && !cancelled),
		.out_block(ctx_block),
		.out_index(ctx_index),
		.out_coefficient(ctx_coefficient),
		.out_epoch(ctx_epoch),
		.done(ctx_done),
		.error(ctx_error),
		.consumed_bits(unused_consumed),
		.count_cycles(unused_cycles),
		.count_inputs(unused_inputs),
		.count_symbols(unused_symbols),
		.count_outputs(unused_outputs),
		.count_output_stall(unused_stall),
		.count_input_wait(unused_wait),
		.count_parser_cycles(unused_parser_cycles),
		.count_parser_output_stall(unused_parser_stall),
		.debug_state(unused_debug),
		.reservoir_bits(unused_reservoir)
	);
	always_ff @(posedge clk)
		if (reset || abort_packet) begin
			state <= IDLE;
			size_bytes <= 0;
			context_epoch <= 0;
			context_blocks <= 0;
			received <= 0;
			crc <= 32'hffffffff;
			cursor <= 0;
			band <= 0;
			mode16 <= 0;
			mode_serial <= 0;
			raw_mode <= 0;
			replay_bits <= 0;
			raw_position <= 0;
			descriptor_ready <= 0;
			word_valid <= 0;
			raw_valid <= 0;
			context_active <= 0;
			fetch_kind <= F_HEADER;
			fetch_count <= 0;
			fetch_index <= 0;
			fetch_base <= 0;
			fetch_return <= IDLE;
			replay_word <= 0;
			raw_coefficient <= 0;
			buffer_bytes <= 0;
			stage_buffer_highwater <= 0;
			done <= 0;
			error <= 0;
			count_cycles <= 0;
			count_inputs <= 0;
			count_outputs <= 0;
			count_output_stall <= 0;
			count_stage_reads <= 0;
			count_stage_responses <= 0;
			count_stage_writes <= 0;
			count_stage_fetch_wait <= 0;
			count_stage_word_hold <= 0;
			begin : sv2v_autoblock_3
				integer j;
				for (j = 0; j < 46; j = j + 1)
					fetch_bytes[j] <= 0;
			end
			begin : sv2v_autoblock_4
				integer j;
				for (j = 0; j < 4; j = j + 1)
					begin
						lengths[j] <= 0;
						counts[j] <= 0;
						offsets[j] <= 0;
						sizes[j] <= 0;
						k0s[j] <= 0;
						k1s[j] <= 0;
					end
			end
		end
		else if (start) begin
			size_bytes <= packet_bytes;
			context_epoch <= epoch;
			context_blocks <= blocks;
			mode16 <= word16;
			mode_serial <= serial_mode;
			raw_mode <= 0;
			received <= 0;
			crc <= 32'hffffffff;
			cursor <= 42;
			band <= 0;
			replay_bits <= 0;
			raw_position <= 0;
			descriptor_ready <= 0;
			word_valid <= 0;
			raw_valid <= 0;
			context_active <= 0;
			fetch_kind <= F_HEADER;
			fetch_count <= 0;
			fetch_index <= 0;
			fetch_base <= 0;
			fetch_return <= IDLE;
			replay_word <= 0;
			raw_coefficient <= 0;
			buffer_bytes <= 0;
			stage_buffer_highwater <= 0;
			done <= 0;
			error <= 0;
			count_cycles <= 0;
			count_inputs <= 0;
			count_outputs <= 0;
			count_output_stall <= 0;
			count_stage_reads <= 0;
			count_stage_responses <= 0;
			count_stage_writes <= 0;
			count_stage_fetch_wait <= 0;
			count_stage_word_hold <= 0;
			if (((((blocks == 0) || (blocks > 65536)) || (packet_bytes < 46)) || (packet_bytes > MAX_PACKET_BYTES)) || (packet_bytes > (46 + (128 * sv2v_cast_32(blocks))))) begin
				state <= FAILED;
				error <= 1;
			end
			else
				state <= RECEIVE;
		end
		else if (((state != IDLE) && (state != FINISHED)) && (state != FAILED)) begin
			count_cycles <= count_cycles + 1'b1;
			if (stage_read_req)
				count_stage_reads <= count_stage_reads + 1'b1;
			if (stage_read_rsp)
				count_stage_responses <= count_stage_responses + 1'b1;
			if (stage_write)
				count_stage_writes <= count_stage_writes + 1'b1;
			if (state == FETCH_WAIT)
				count_stage_fetch_wait <= count_stage_fetch_wait + 1'b1;
			if (ctx_valid && !ctx_ready)
				count_stage_word_hold <= count_stage_word_hold + 1'b1;
			if (out_valid && !out_ready)
				count_output_stall <= count_output_stall + 1'b1;
			if (out_valid && out_ready)
				count_outputs <= count_outputs + 1'b1;
			if (context_active && (ctx_error != 0))
				fail_packet(ctx_error);
			else if (context_active && ctx_done) begin
				context_active <= 0;
				word_valid <= 0;
				state <= CONTEXT_END;
			end
			else
				case (state)
					RECEIVE:
						if (in_valid && in_ready) begin
							received <= received + 1'b1;
							count_inputs <= count_inputs + 1'b1;
							if (received < (size_bytes - 4))
								crc <= crc_byte(crc, in_data);
							if (in_last != ((received + 1) == size_bytes))
								fail_packet(2);
							else if ((received + 1) == size_bytes)
								begin_fetch(F_HEADER, 46, 0, HEADER);
						end
					HEADER:
						if ((crc ^ 32'hffffffff) != cached32(42))
							fail_packet(3);
						else if ((((((cached32(0) != 32'h38385242) || (fetch_bytes[4] != 1)) || (fetch_bytes[5] > 1)) || (cached32(6) != sv2v_cast_32(context_blocks))) || ({fetch_bytes[11], fetch_bytes[10]} != 1)) || ({fetch_bytes[13], fetch_bytes[12]} != 0))
							fail_packet(4);
						else if (((({2'd0, cached32(14)} + {2'd0, cached32(18)}) + {2'd0, cached32(22)}) + {2'd0, cached32(26)}) != ({2'd0, size_bytes} - 34'd46))
							fail_packet(4);
						else begin
							begin : sv2v_autoblock_5
								integer j;
								for (j = 0; j < 4; j = j + 1)
									lengths[j] <= cached32(14 + (j * 4));
							end
							counts[0] <= sv2v_cast_32(context_blocks);
							raw_mode <= fetch_bytes[5] == 1;
							begin : sv2v_autoblock_6
								integer j;
								for (j = 1; j < 4; j = j + 1)
									counts[j] <= cached32(26 + (j * 4));
							end
							if (fetch_bytes[5] == 1) begin
								if (((((((cached32(14) != (128 * sv2v_cast_32(context_blocks))) || (cached32(18) != 0)) || (cached32(22) != 0)) || (cached32(26) != 0)) || (cached32(30) != 0)) || (cached32(34) != 0)) || (cached32(38) != 0))
									fail_packet(4);
								else
									state <= METADATA;
							end
							else
								state <= DESCRIPTOR;
						end
					DESCRIPTOR:
						if (!descriptor_ready) begin
							if (((lengths[band] < 6) || (cursor > (size_bytes - 4))) || (lengths[band] > ((size_bytes - 4) - cursor)))
								fail_packet(4);
							else
								begin_fetch(F_DESCRIPTOR, 7, cursor, DESCRIPTOR);
						end
						else begin
							descriptor_ready <= 0;
							if ((descriptor_bytes != (lengths[band] - 6)) || (descriptor_bits > (8 * (size_bytes - 46))))
								fail_packet(4);
							else if (((band == 0) && ((fetch_bytes[0] > 13) || (fetch_bytes[1] != 255))) || ((band != 0) && (((fetch_bytes[0] > 19) || (fetch_bytes[1] > 11)) || (counts[band] > descriptor_limit))))
								fail_packet(4);
							else if (((band != 0) && (counts[band] == 0)) && (descriptor_bits != 0))
								fail_packet(7);
							else if ((descriptor_bits[2:0] != 0) && ((fetch_bytes[6] & (8'hff >> descriptor_bits[2:0])) != 0))
								fail_packet(7);
							else begin
								k0s[band] <= fetch_bytes[0];
								k1s[band] <= fetch_bytes[1];
								sizes[band] <= descriptor_bits;
								offsets[band] <= cursor + 6;
								cursor <= cursor + lengths[band];
								if (band == 3) begin
									band <= 0;
									state <= METADATA;
								end
								else
									band <= band + 1'b1;
							end
						end
					METADATA:
						if (meta_valid && meta_ready)
							state <= (raw_mode ? RAW : CONTEXT_START);
					CONTEXT_START: begin
						replay_bits <= 0;
						word_valid <= 0;
						context_active <= 1;
						state <= CONTEXT_RUN;
					end
					CONTEXT_RUN:
						if (ctx_valid && ctx_ready) begin
							replay_bits <= replay_bits + sv2v_cast_32(ctx_bits);
							word_valid <= 0;
						end
						else if (!word_valid && (replay_bits < sizes[band]))
							begin_fetch(F_REPLAY, sv2v_cast_6((sv2v_cast_32(ctx_bits) + 7) >> 3), offsets[band] + (replay_bits >> 3), CONTEXT_RUN);
					RAW:
						if (!raw_valid)
							begin_fetch(F_RAW, 2, 42 + (2 * raw_position), RAW);
						else if ((raw_coefficient < -2048) || (raw_coefficient > 2048))
							fail_packet(5);
						else if (out_valid && out_ready) begin
							raw_valid <= 0;
							raw_position <= raw_position + 1'b1;
							if ((raw_position + 1) == (sv2v_cast_32(context_blocks) * 64))
								state <= RAW_END;
						end
					FETCH_REQ:
						if (stage_read_req)
							state <= FETCH_WAIT;
						else if ((fetch_address >= size_bytes) || (fetch_address >= MAX_PACKET_BYTES))
							fail_packet(4);
					FETCH_WAIT:
						if (stage_read_rsp) begin
							if ((ram_epoch != context_epoch) || (ram_addr != fetch_address))
								fail_packet(4);
							else begin
								fetch_bytes[fetch_index] <= ram_data;
								buffer_bytes <= fetch_index + 1'b1;
								if ((fetch_index + 1'b1) > stage_buffer_highwater)
									stage_buffer_highwater <= fetch_index + 1'b1;
								if ((fetch_index + 6'd1) == fetch_count) begin
									if (fetch_kind == F_DESCRIPTOR)
										descriptor_ready <= 1;
									if (fetch_kind == F_REPLAY) begin
										replay_word <= fetched_word;
										word_valid <= 1;
									end
									if (fetch_kind == F_RAW) begin
										raw_coefficient <= $signed({ram_data, fetch_bytes[0]});
										raw_valid <= 1;
									end
									state <= fetch_return;
								end
								else begin
									fetch_index <= fetch_index + 1'b1;
									state <= FETCH_REQ;
								end
							end
						end
					CONTEXT_END:
						if (band_end_valid && band_end_ready) begin
							if (band == 3) begin
								done <= 1;
								state <= FINISHED;
							end
							else begin
								band <= band + 1'b1;
								state <= CONTEXT_START;
							end
						end
					RAW_END:
						if (band_end_valid && band_end_ready) begin
							done <= 1;
							state <= FINISHED;
						end
					default:
						fail_packet(4);
				endcase
		end
endmodule
module br88_pipeline_v91h (
	clk,
	reset,
	start,
	abort_packet,
	packet_bytes,
	epoch,
	blocks,
	serial_clear,
	write_overlap,
	read_prefetch,
	tile_overlap,
	in_valid,
	in_ready,
	in_data,
	in_last,
	out_valid,
	out_ready,
	out_block,
	out_index,
	out_value,
	out_epoch,
	done,
	error,
	busy,
	draining,
	scratch_sealed,
	used_bytes,
	count_cycles,
	count_input_bytes,
	count_dense,
	count_reads,
	count_writes,
	count_dense_stall,
	mem_req_valid,
	mem_req_ready,
	mem_req_write,
	mem_req_addr,
	mem_req_data,
	mem_req_epoch,
	mem_rsp_valid,
	mem_rsp_ready,
	mem_rsp_data,
	mem_rsp_epoch,
	mem_rsp_error,
	packet_state,
	metadata_wait,
	dbg_running,
	dbg_allocation,
	dbg_seal_sent,
	dbg_packet_done,
	dbg_coef_valid,
	dbg_coef_ready,
	dbg_coef_band,
	dbg_coef_block,
	dbg_coef_index,
	dbg_coef_value,
	dbg_coef_epoch,
	dbg_meta_valid,
	dbg_meta_ready,
	dbg_meta_raw,
	dbg_band_end_valid,
	dbg_band_end_ready,
	dbg_band_end_band,
	dbg_seal_valid,
	dbg_seal_ready,
	dbg_scratch_state,
	dbg_scratch_return_state,
	dbg_scratch_outstanding,
	dbg_prefetch_offer,
	dbg_prefetch_launch,
	dbg_prefetch_use,
	dbg_tile_mode,
	dbg_tile_preparing,
	dbg_prepare_bank,
	dbg_emit_bank,
	dbg_bank_ready,
	dbg_bank_owned,
	dbg_emitter_state,
	dbg_prepare_block,
	dbg_bank_block,
	dbg_bank_epoch,
	dbg_tile_prepare_start,
	dbg_tile_publish,
	dbg_tile_release,
	count_emitter_state,
	count_tile_starts,
	count_tile_publishes,
	count_tile_releases,
	count_prepare_output_overlap,
	count_prepare_output_hold,
	count_tile_read_output_overlap,
	count_tile_bank_wait,
	count_both_ready_wait,
	count_tile_prep_done_wait,
	count_output_valid,
	count_publish_release_same_edge,
	max_tile_owned,
	max_tile_ready,
	count_prefetch_offers,
	count_prefetch_accepts,
	count_prefetch_acks,
	count_prefetch_uses,
	count_dense_during_read_pending,
	count_prefetch_drain_wait,
	max_prefetch_offer,
	dbg_write_slot_valid,
	dbg_assembler_full,
	dbg_write_enqueue,
	count_write_enqueues,
	count_write_accepts,
	count_write_acks,
	count_full_wait,
	count_packing_during_write_pending,
	max_write_slot,
	max_owned_lines,
	dbg_scratch_phase,
	dbg_scratch_assembly_bytes,
	dbg_scratch_cache_valid,
	dbg_scratch_head_valid,
	count_packet_state,
	count_scratch_state,
	count_coef_stall,
	count_metadata_wait,
	count_band_end_stall,
	count_mem_req_stall,
	count_mem_pending,
	count_input_starved,
	ts_first_input,
	ts_last_input,
	ts_metadata_accept,
	ts_last_sparse_coef,
	ts_packet_done_observed,
	ts_seal_accepted,
	ts_scratch_sealed_observed,
	ts_first_dense,
	ts_last_dense,
	ts_integrated_done,
	ts_first_coef_band,
	ts_last_coef_band,
	ts_band_end,
	max_assembly_bytes,
	max_cache_valid,
	max_head_valid,
	max_outstanding,
	stage_read_req,
	stage_read_rsp,
	stage_write,
	stage_pending,
	stage_context_active,
	stage_cancel,
	stage_word_valid,
	stage_word_ready,
	stage_read_addr,
	stage_rsp_addr,
	stage_write_addr,
	stage_req_epoch,
	stage_rsp_epoch,
	stage_read_data,
	stage_write_data,
	stage_buffer_bytes,
	stage_buffer_highwater,
	stage_purpose,
	count_stage_reads,
	count_stage_responses,
	count_stage_writes,
	count_stage_fetch_wait,
	count_stage_word_hold
);
	parameter integer SYNC_STAGING = 1;
	input wire clk;
	input wire reset;
	input wire start;
	input wire abort_packet;
	input wire [31:0] packet_bytes;
	input wire [31:0] epoch;
	input wire [16:0] blocks;
	input wire serial_clear;
	input wire write_overlap;
	input wire read_prefetch;
	input wire tile_overlap;
	input wire in_valid;
	output wire in_ready;
	input wire [7:0] in_data;
	input wire in_last;
	output wire out_valid;
	input wire out_ready;
	output wire [15:0] out_block;
	output wire [5:0] out_index;
	output wire signed [15:0] out_value;
	output wire [31:0] out_epoch;
	output reg done;
	output reg [7:0] error;
	output wire busy;
	output wire draining;
	output wire scratch_sealed;
	output wire [18:0] used_bytes;
	output reg [63:0] count_cycles;
	output reg [63:0] count_input_bytes;
	output reg [63:0] count_dense;
	output reg [63:0] count_reads;
	output reg [63:0] count_writes;
	output reg [63:0] count_dense_stall;
	output wire mem_req_valid;
	input wire mem_req_ready;
	output wire mem_req_write;
	output wire [17:0] mem_req_addr;
	output wire [127:0] mem_req_data;
	output wire [31:0] mem_req_epoch;
	input wire mem_rsp_valid;
	output wire mem_rsp_ready;
	input wire [127:0] mem_rsp_data;
	input wire [31:0] mem_rsp_epoch;
	input wire mem_rsp_error;
	output wire [3:0] packet_state;
	output wire metadata_wait;
	output wire dbg_running;
	output wire dbg_allocation;
	output wire dbg_seal_sent;
	output wire dbg_packet_done;
	output wire dbg_coef_valid;
	output wire dbg_coef_ready;
	output wire [1:0] dbg_coef_band;
	output wire [15:0] dbg_coef_block;
	output wire [5:0] dbg_coef_index;
	output wire signed [15:0] dbg_coef_value;
	output wire [31:0] dbg_coef_epoch;
	output wire dbg_meta_valid;
	output wire dbg_meta_ready;
	output wire dbg_meta_raw;
	output wire dbg_band_end_valid;
	output wire dbg_band_end_ready;
	output wire [1:0] dbg_band_end_band;
	output wire dbg_seal_valid;
	output wire dbg_seal_ready;
	output wire [4:0] dbg_scratch_state;
	output wire [4:0] dbg_scratch_return_state;
	output wire dbg_scratch_outstanding;
	output wire dbg_prefetch_offer;
	output wire dbg_prefetch_launch;
	output wire dbg_prefetch_use;
	output wire dbg_tile_mode;
	output wire dbg_tile_preparing;
	output wire dbg_prepare_bank;
	output wire dbg_emit_bank;
	output wire [1:0] dbg_bank_ready;
	output wire [1:0] dbg_bank_owned;
	output wire [1:0] dbg_emitter_state;
	output wire [15:0] dbg_prepare_block;
	output wire [31:0] dbg_bank_block;
	output wire [63:0] dbg_bank_epoch;
	output wire dbg_tile_prepare_start;
	output wire dbg_tile_publish;
	output wire dbg_tile_release;
	output reg [255:0] count_emitter_state;
	output reg [63:0] count_tile_starts;
	output reg [63:0] count_tile_publishes;
	output reg [63:0] count_tile_releases;
	output reg [63:0] count_prepare_output_overlap;
	output reg [63:0] count_prepare_output_hold;
	output reg [63:0] count_tile_read_output_overlap;
	output reg [63:0] count_tile_bank_wait;
	output reg [63:0] count_both_ready_wait;
	output reg [63:0] count_tile_prep_done_wait;
	output reg [63:0] count_output_valid;
	output reg [63:0] count_publish_release_same_edge;
	output reg [1:0] max_tile_owned;
	output reg [1:0] max_tile_ready;
	output reg [63:0] count_prefetch_offers;
	output reg [63:0] count_prefetch_accepts;
	output reg [63:0] count_prefetch_acks;
	output reg [63:0] count_prefetch_uses;
	output reg [63:0] count_dense_during_read_pending;
	output reg [63:0] count_prefetch_drain_wait;
	output reg max_prefetch_offer;
	output wire dbg_write_slot_valid;
	output wire dbg_assembler_full;
	output wire dbg_write_enqueue;
	output reg [63:0] count_write_enqueues;
	output reg [63:0] count_write_accepts;
	output reg [63:0] count_write_acks;
	output reg [63:0] count_full_wait;
	output reg [63:0] count_packing_during_write_pending;
	output reg max_write_slot;
	output reg [1:0] max_owned_lines;
	output wire [2:0] dbg_scratch_phase;
	output wire [4:0] dbg_scratch_assembly_bytes;
	output wire [3:0] dbg_scratch_cache_valid;
	output wire [2:0] dbg_scratch_head_valid;
	output reg [1023:0] count_packet_state;
	output reg [2047:0] count_scratch_state;
	output reg [63:0] count_coef_stall;
	output reg [63:0] count_metadata_wait;
	output reg [63:0] count_band_end_stall;
	output reg [63:0] count_mem_req_stall;
	output reg [63:0] count_mem_pending;
	output reg [63:0] count_input_starved;
	output reg [63:0] ts_first_input;
	output reg [63:0] ts_last_input;
	output reg [63:0] ts_metadata_accept;
	output reg [63:0] ts_last_sparse_coef;
	output reg [63:0] ts_packet_done_observed;
	output reg [63:0] ts_seal_accepted;
	output reg [63:0] ts_scratch_sealed_observed;
	output reg [63:0] ts_first_dense;
	output reg [63:0] ts_last_dense;
	output reg [63:0] ts_integrated_done;
	output reg [255:0] ts_first_coef_band;
	output reg [255:0] ts_last_coef_band;
	output reg [255:0] ts_band_end;
	output reg [4:0] max_assembly_bytes;
	output reg [2:0] max_cache_valid;
	output reg [2:0] max_head_valid;
	output reg max_outstanding;
	output wire stage_read_req;
	output wire stage_read_rsp;
	output wire stage_write;
	output wire stage_pending;
	output wire stage_context_active;
	output wire stage_cancel;
	output wire stage_word_valid;
	output wire stage_word_ready;
	output wire [31:0] stage_read_addr;
	output wire [31:0] stage_rsp_addr;
	output wire [31:0] stage_write_addr;
	output wire [31:0] stage_req_epoch;
	output wire [31:0] stage_rsp_epoch;
	output wire [7:0] stage_read_data;
	output wire [7:0] stage_write_data;
	output wire [5:0] stage_buffer_bytes;
	output reg [5:0] stage_buffer_highwater;
	output wire [2:0] stage_purpose;
	output reg [63:0] count_stage_reads;
	output reg [63:0] count_stage_responses;
	output reg [63:0] count_stage_writes;
	output reg [63:0] count_stage_fetch_wait;
	output reg [63:0] count_stage_word_hold;
	reg running;
	reg allocation;
	reg seal_sent;
	reg use_serial_clear;
	reg use_write_overlap;
	reg use_read_prefetch;
	reg use_tile_overlap;
	wire [63:0] unused_stage_reads;
	wire [63:0] unused_stage_responses;
	wire [63:0] unused_stage_writes;
	wire [63:0] unused_stage_fetch_wait;
	wire [63:0] unused_stage_word_hold;
	wire [5:0] unused_stage_buffer_highwater;
	wire cancelled;
	wire packet_abort;
	wire store_abort;
	wire packet_ready;
	wire packet_done;
	wire [3:0] packet_error;
	wire [3:0] store_error;
	wire meta_valid;
	wire meta_ready;
	wire meta_raw;
	wire [16:0] meta_blocks;
	wire [31:0] meta_count1;
	wire [31:0] meta_count2;
	wire [31:0] meta_count3;
	wire [31:0] meta_epoch;
	wire coef_valid;
	wire coef_ready;
	wire [1:0] coef_band;
	wire [15:0] coef_block;
	wire [5:0] coef_index;
	wire signed [15:0] coef_value;
	wire [31:0] coef_epoch;
	wire end_valid;
	wire end_ready;
	wire [1:0] end_band;
	wire [31:0] end_epoch;
	wire store_busy;
	wire store_done;
	wire seal_ready;
	wire dense_valid;
	wire [31:0] store_epoch;
	wire [63:0] packet_cycles;
	wire [63:0] packet_inputs;
	wire [63:0] packet_outputs;
	wire [63:0] packet_stall;
	assign cancelled = (reset || start) || abort_packet;
	assign packet_abort = abort_packet || ((!start && running) && (store_error != 0));
	assign store_abort = (start || abort_packet) || (running && (packet_error != 0));
	assign in_ready = ((packet_ready && running) && (error == 0)) && !cancelled;
	assign out_valid = ((dense_valid && running) && (error == 0)) && !cancelled;
	assign busy = running || store_busy;
	assign draining = store_busy && !running;
	assign metadata_wait = meta_valid && !meta_ready;
	assign dbg_running = running;
	assign dbg_allocation = allocation;
	assign dbg_seal_sent = seal_sent;
	assign dbg_packet_done = packet_done;
	assign dbg_coef_valid = coef_valid;
	assign dbg_coef_ready = coef_ready;
	assign dbg_coef_band = coef_band;
	assign dbg_coef_block = coef_block;
	assign dbg_coef_index = coef_index;
	assign dbg_coef_value = coef_value;
	assign dbg_coef_epoch = coef_epoch;
	assign dbg_meta_valid = meta_valid;
	assign dbg_meta_ready = meta_ready;
	assign dbg_meta_raw = meta_raw;
	assign dbg_band_end_valid = end_valid;
	assign dbg_band_end_ready = end_ready;
	assign dbg_band_end_band = end_band;
	assign dbg_seal_valid = (((packet_done && allocation) && !seal_sent) && running) && (error == 0);
	assign dbg_seal_ready = seal_ready;
	br88_packet_ingress_v91h #(.SYNC_STAGING(SYNC_STAGING)) packet_decoder(
		.clk(clk),
		.reset(reset),
		.start(start),
		.abort_packet(packet_abort),
		.packet_bytes(packet_bytes),
		.blocks(blocks),
		.epoch(epoch),
		.word16(1'b0),
		.serial_mode(1'b0),
		.in_valid((in_valid && running) && (error == 0)),
		.in_ready(packet_ready),
		.in_data(in_data),
		.in_last(in_last),
		.out_valid(coef_valid),
		.out_ready(coef_ready),
		.out_block(coef_block),
		.out_index(coef_index),
		.out_coefficient(coef_value),
		.out_epoch(coef_epoch),
		.out_band(coef_band),
		.meta_valid(meta_valid),
		.meta_ready(meta_ready),
		.meta_blocks(meta_blocks),
		.meta_count1(meta_count1),
		.meta_count2(meta_count2),
		.meta_count3(meta_count3),
		.meta_epoch(meta_epoch),
		.meta_raw(meta_raw),
		.band_end_valid(end_valid),
		.band_end_ready(end_ready),
		.band_end_band(end_band),
		.band_end_epoch(end_epoch),
		.done(packet_done),
		.error(packet_error),
		.count_cycles(packet_cycles),
		.count_inputs(packet_inputs),
		.count_outputs(packet_outputs),
		.count_output_stall(packet_stall),
		.debug_state(packet_state),
		.stage_read_req(stage_read_req),
		.stage_read_rsp(stage_read_rsp),
		.stage_write(stage_write),
		.stage_pending(stage_pending),
		.stage_context_active(stage_context_active),
		.stage_cancel(stage_cancel),
		.stage_word_valid(stage_word_valid),
		.stage_word_ready(stage_word_ready),
		.stage_read_addr(stage_read_addr),
		.stage_rsp_addr(stage_rsp_addr),
		.stage_write_addr(stage_write_addr),
		.stage_req_epoch(stage_req_epoch),
		.stage_rsp_epoch(stage_rsp_epoch),
		.stage_read_data(stage_read_data),
		.stage_write_data(stage_write_data),
		.stage_buffer_bytes(stage_buffer_bytes),
		.stage_buffer_highwater(unused_stage_buffer_highwater),
		.stage_purpose(stage_purpose),
		.count_stage_reads(unused_stage_reads),
		.count_stage_responses(unused_stage_responses),
		.count_stage_writes(unused_stage_writes),
		.count_stage_fetch_wait(unused_stage_fetch_wait),
		.count_stage_word_hold(unused_stage_word_hold)
	);
	packed_scratch_v91g2 scratch(
		.clk(clk),
		.reset(reset),
		.begin_valid((meta_valid && running) && (error == 0)),
		.begin_ready(meta_ready),
		.begin_blocks(meta_blocks),
		.begin_raw(meta_raw),
		.begin_count1(meta_count1),
		.begin_count2(meta_count2),
		.begin_count3(meta_count3),
		.begin_epoch(meta_epoch),
		.begin_serial_clear(use_serial_clear),
		.begin_overlap(use_write_overlap),
		.begin_prefetch(use_read_prefetch),
		.begin_tile_overlap(use_tile_overlap),
		.coef_valid((coef_valid && running) && (error == 0)),
		.coef_ready(coef_ready),
		.coef_band(coef_band),
		.coef_block(coef_block),
		.coef_index(coef_index),
		.coef_value(coef_value),
		.coef_epoch(coef_epoch),
		.band_end_valid((end_valid && running) && (error == 0)),
		.band_end_ready(end_ready),
		.band_end_band(end_band),
		.band_end_epoch(end_epoch),
		.seal_valid((((packet_done && allocation) && !seal_sent) && running) && (error == 0)),
		.seal_ready(seal_ready),
		.seal_epoch(meta_epoch),
		.abort_valid(store_abort),
		.abort_epoch(store_epoch),
		.busy(store_busy),
		.sealed(scratch_sealed),
		.done(store_done),
		.error(store_error),
		.active_epoch(store_epoch),
		.used_bytes(used_bytes),
		.dense_valid(dense_valid),
		.dense_ready(((out_ready && running) && (error == 0)) && !cancelled),
		.dense_block(out_block),
		.dense_index(out_index),
		.dense_value(out_value),
		.dense_epoch(out_epoch),
		.mem_req_valid(mem_req_valid),
		.mem_req_ready(mem_req_ready),
		.mem_req_write(mem_req_write),
		.mem_req_addr(mem_req_addr),
		.mem_req_data(mem_req_data),
		.mem_req_epoch(mem_req_epoch),
		.mem_rsp_valid(mem_rsp_valid),
		.mem_rsp_ready(mem_rsp_ready),
		.mem_rsp_data(mem_rsp_data),
		.mem_rsp_epoch(mem_rsp_epoch),
		.mem_rsp_error(mem_rsp_error),
		.debug_state(dbg_scratch_state),
		.debug_return_state(dbg_scratch_return_state),
		.debug_outstanding(dbg_scratch_outstanding),
		.debug_phase(dbg_scratch_phase),
		.debug_assembly_bytes(dbg_scratch_assembly_bytes),
		.debug_tile_mode(dbg_tile_mode),
		.debug_tile_preparing(dbg_tile_preparing),
		.debug_prepare_bank(dbg_prepare_bank),
		.debug_emit_bank(dbg_emit_bank),
		.debug_bank_ready(dbg_bank_ready),
		.debug_bank_owned(dbg_bank_owned),
		.debug_emitter_state(dbg_emitter_state),
		.debug_prepare_block(dbg_prepare_block),
		.debug_bank_block(dbg_bank_block),
		.debug_bank_epoch(dbg_bank_epoch),
		.debug_tile_prepare_start(dbg_tile_prepare_start),
		.debug_tile_publish(dbg_tile_publish),
		.debug_tile_release(dbg_tile_release),
		.debug_prefetch_offer(dbg_prefetch_offer),
		.debug_prefetch_launch(dbg_prefetch_launch),
		.debug_prefetch_use(dbg_prefetch_use),
		.debug_write_slot_valid(dbg_write_slot_valid),
		.debug_assembler_full(dbg_assembler_full),
		.debug_write_enqueue(dbg_write_enqueue),
		.debug_cache_valid(dbg_scratch_cache_valid),
		.debug_head_valid(dbg_scratch_head_valid)
	);
	function automatic [1:0] sv2v_cast_2;
		input reg [1:0] inp;
		sv2v_cast_2 = inp;
	endfunction
	always_ff @(posedge clk)
		if ((reset || abort_packet) || start) begin
			count_stage_reads <= 0;
			count_stage_responses <= 0;
			count_stage_writes <= 0;
			count_stage_fetch_wait <= 0;
			count_stage_word_hold <= 0;
			stage_buffer_highwater <= 0;
			begin : sv2v_autoblock_1
				integer i;
				for (i = 0; i < 16; i = i + 1)
					count_packet_state[(15 - i) * 64+:64] <= 0;
			end
			begin : sv2v_autoblock_2
				integer i;
				for (i = 0; i < 32; i = i + 1)
					count_scratch_state[(31 - i) * 64+:64] <= 0;
			end
			count_coef_stall <= 0;
			count_metadata_wait <= 0;
			count_band_end_stall <= 0;
			count_mem_req_stall <= 0;
			count_mem_pending <= 0;
			count_input_starved <= 0;
			ts_first_input <= 0;
			ts_last_input <= 0;
			ts_metadata_accept <= 0;
			ts_last_sparse_coef <= 0;
			ts_packet_done_observed <= 0;
			ts_seal_accepted <= 0;
			ts_scratch_sealed_observed <= 0;
			ts_first_dense <= 0;
			ts_last_dense <= 0;
			ts_integrated_done <= 0;
			begin : sv2v_autoblock_3
				integer i;
				for (i = 0; i < 4; i = i + 1)
					begin
						ts_first_coef_band[(3 - i) * 64+:64] <= 0;
						ts_last_coef_band[(3 - i) * 64+:64] <= 0;
						ts_band_end[(3 - i) * 64+:64] <= 0;
					end
			end
			max_assembly_bytes <= 0;
			max_cache_valid <= 0;
			max_head_valid <= 0;
			max_outstanding <= 0;
			count_write_enqueues <= 0;
			count_write_accepts <= 0;
			count_packing_during_write_pending <= 0;
			count_write_acks <= 0;
			count_full_wait <= 0;
			max_write_slot <= 0;
			max_owned_lines <= 0;
			count_prefetch_offers <= 0;
			count_prefetch_accepts <= 0;
			count_prefetch_acks <= 0;
			count_prefetch_uses <= 0;
			count_dense_during_read_pending <= 0;
			count_prefetch_drain_wait <= 0;
			max_prefetch_offer <= 0;
			begin : sv2v_autoblock_4
				integer i;
				for (i = 0; i < 4; i = i + 1)
					count_emitter_state[(3 - i) * 64+:64] <= 0;
			end
			count_tile_starts <= 0;
			count_tile_publishes <= 0;
			count_tile_releases <= 0;
			count_prepare_output_overlap <= 0;
			count_prepare_output_hold <= 0;
			count_tile_read_output_overlap <= 0;
			count_tile_bank_wait <= 0;
			count_both_ready_wait <= 0;
			count_tile_prep_done_wait <= 0;
			count_output_valid <= 0;
			count_publish_release_same_edge <= 0;
			max_tile_owned <= 0;
			max_tile_ready <= 0;
		end
		else if (running) begin
			if (!stage_cancel) begin
				if (stage_read_req)
					count_stage_reads <= count_stage_reads + 1'b1;
				if (stage_read_rsp)
					count_stage_responses <= count_stage_responses + 1'b1;
				if (stage_write)
					count_stage_writes <= count_stage_writes + 1'b1;
				if (packet_state == 13)
					count_stage_fetch_wait <= count_stage_fetch_wait + 1'b1;
				if (stage_word_valid && !stage_word_ready)
					count_stage_word_hold <= count_stage_word_hold + 1'b1;
				if (stage_buffer_bytes > stage_buffer_highwater)
					stage_buffer_highwater <= stage_buffer_bytes;
			end
			count_emitter_state[(3 - dbg_emitter_state) * 64+:64] <= count_emitter_state[(3 - dbg_emitter_state) * 64+:64] + 1'b1;
			if (dbg_tile_prepare_start)
				count_tile_starts <= count_tile_starts + 1'b1;
			if (dbg_tile_publish)
				count_tile_publishes <= count_tile_publishes + 1'b1;
			if (dbg_tile_release)
				count_tile_releases <= count_tile_releases + 1'b1;
			if ((dbg_tile_preparing && out_valid) && out_ready)
				count_prepare_output_overlap <= count_prepare_output_overlap + 1'b1;
			if ((dbg_tile_preparing && out_valid) && !out_ready)
				count_prepare_output_hold <= count_prepare_output_hold + 1'b1;
			if ((((dbg_tile_mode && dbg_scratch_outstanding) && !mem_req_write) && out_valid) && out_ready)
				count_tile_read_output_overlap <= count_tile_read_output_overlap + 1'b1;
			if (out_valid)
				count_output_valid <= count_output_valid + 1'b1;
			if (dbg_tile_mode && (dbg_scratch_state == 29))
				count_tile_prep_done_wait <= count_tile_prep_done_wait + 1'b1;
			if (dbg_tile_mode && (dbg_scratch_state == 28))
				count_tile_bank_wait <= count_tile_bank_wait + 1'b1;
			if ((dbg_tile_mode && (dbg_scratch_state == 28)) && (dbg_bank_ready == 2'b11))
				count_both_ready_wait <= count_both_ready_wait + 1'b1;
			if (dbg_tile_publish && dbg_tile_release)
				count_publish_release_same_edge <= count_publish_release_same_edge + 1'b1;
			if (2'($countones(dbg_bank_owned)) > max_tile_owned)
				max_tile_owned <= 2'($countones(dbg_bank_owned));
			if (2'($countones(dbg_bank_ready)) > max_tile_ready)
				max_tile_ready <= 2'($countones(dbg_bank_ready));
			count_packet_state[(15 - packet_state) * 64+:64] <= count_packet_state[(15 - packet_state) * 64+:64] + 1'b1;
			count_scratch_state[(31 - dbg_scratch_state) * 64+:64] <= count_scratch_state[(31 - dbg_scratch_state) * 64+:64] + 1'b1;
			if (coef_valid && !coef_ready)
				count_coef_stall <= count_coef_stall + 1'b1;
			if (meta_valid && !meta_ready)
				count_metadata_wait <= count_metadata_wait + 1'b1;
			if (end_valid && !end_ready)
				count_band_end_stall <= count_band_end_stall + 1'b1;
			if (mem_req_valid && !mem_req_ready)
				count_mem_req_stall <= count_mem_req_stall + 1'b1;
			if (dbg_scratch_outstanding)
				count_mem_pending <= count_mem_pending + 1'b1;
			if (in_ready && !in_valid)
				count_input_starved <= count_input_starved + 1'b1;
			if (in_valid && in_ready) begin
				if (ts_first_input == 0)
					ts_first_input <= count_cycles + 1'b1;
				ts_last_input <= count_cycles + 1'b1;
			end
			if (meta_valid && meta_ready)
				ts_metadata_accept <= count_cycles + 1'b1;
			if (coef_valid && coef_ready) begin
				ts_last_sparse_coef <= count_cycles + 1'b1;
				if (ts_first_coef_band[(3 - coef_band) * 64+:64] == 0)
					ts_first_coef_band[(3 - coef_band) * 64+:64] <= count_cycles + 1'b1;
				ts_last_coef_band[(3 - coef_band) * 64+:64] <= count_cycles + 1'b1;
			end
			if (end_valid && end_ready)
				ts_band_end[(3 - end_band) * 64+:64] <= count_cycles + 1'b1;
			if (dbg_scratch_assembly_bytes > max_assembly_bytes)
				max_assembly_bytes <= dbg_scratch_assembly_bytes;
			if (3'($countones(dbg_scratch_cache_valid)) > max_cache_valid)
				max_cache_valid <= 3'($countones(dbg_scratch_cache_valid));
			if (3'($countones(dbg_scratch_head_valid)) > max_head_valid)
				max_head_valid <= 3'($countones(dbg_scratch_head_valid));
			if (dbg_scratch_outstanding)
				max_outstanding <= 1;
			if (dbg_write_slot_valid)
				max_write_slot <= 1;
			if ((sv2v_cast_2(dbg_write_slot_valid) + sv2v_cast_2(dbg_scratch_assembly_bytes != 0)) > max_owned_lines)
				max_owned_lines <= sv2v_cast_2(dbg_write_slot_valid) + sv2v_cast_2(dbg_scratch_assembly_bytes != 0);
			if (dbg_prefetch_offer)
				max_prefetch_offer <= 1;
			if (dbg_prefetch_launch)
				count_prefetch_offers <= count_prefetch_offers + 1'b1;
			if ((dbg_prefetch_offer && mem_req_valid) && mem_req_ready)
				count_prefetch_accepts <= count_prefetch_accepts + 1'b1;
			if ((((dbg_prefetch_offer && dbg_scratch_outstanding) && mem_rsp_valid) && (mem_rsp_epoch == store_epoch)) && !mem_rsp_error)
				count_prefetch_acks <= count_prefetch_acks + 1'b1;
			if (dbg_prefetch_use)
				count_prefetch_uses <= count_prefetch_uses + 1'b1;
			if (((dbg_prefetch_offer && dbg_scratch_outstanding) && out_valid) && out_ready)
				count_dense_during_read_pending <= count_dense_during_read_pending + 1'b1;
			if (dbg_scratch_state == 27)
				count_prefetch_drain_wait <= count_prefetch_drain_wait + 1'b1;
			if (dbg_write_enqueue)
				count_write_enqueues <= count_write_enqueues + 1'b1;
			if ((dbg_write_slot_valid && mem_req_valid) && mem_req_ready)
				count_write_accepts <= count_write_accepts + 1'b1;
			if ((dbg_scratch_outstanding && mem_req_write) && ((dbg_scratch_state == 1) || (dbg_scratch_state == 2)))
				count_packing_during_write_pending <= count_packing_during_write_pending + 1'b1;
			if (((dbg_write_slot_valid && dbg_scratch_outstanding) && mem_rsp_valid) && (mem_rsp_epoch == store_epoch))
				count_write_acks <= count_write_acks + 1'b1;
			if (dbg_scratch_state == 26)
				count_full_wait <= count_full_wait + 1'b1;
			if (packet_done && (ts_packet_done_observed == 0))
				ts_packet_done_observed <= count_cycles + 1'b1;
			if (dbg_seal_valid && seal_ready)
				ts_seal_accepted <= count_cycles + 1'b1;
			if (scratch_sealed && (ts_scratch_sealed_observed == 0))
				ts_scratch_sealed_observed <= count_cycles + 1'b1;
			if (out_valid && out_ready) begin
				if (ts_first_dense == 0)
					ts_first_dense <= count_cycles + 1'b1;
				ts_last_dense <= count_cycles + 1'b1;
			end
			if (store_done)
				ts_integrated_done <= count_cycles + 1'b1;
		end
	always_ff @(posedge clk)
		if (reset || abort_packet) begin
			running <= 0;
			allocation <= 0;
			seal_sent <= 0;
			use_serial_clear <= 0;
			use_write_overlap <= 0;
			use_read_prefetch <= 0;
			use_tile_overlap <= 0;
			done <= 0;
			error <= 0;
			count_cycles <= 0;
			count_input_bytes <= 0;
			count_dense <= 0;
			count_reads <= 0;
			count_writes <= 0;
			count_dense_stall <= 0;
		end
		else if (start) begin
			running <= 1;
			allocation <= 0;
			seal_sent <= 0;
			use_serial_clear <= serial_clear;
			use_write_overlap <= write_overlap;
			use_read_prefetch <= read_prefetch;
			use_tile_overlap <= tile_overlap;
			done <= 0;
			error <= 0;
			count_cycles <= 0;
			count_input_bytes <= 0;
			count_dense <= 0;
			count_reads <= 0;
			count_writes <= 0;
			count_dense_stall <= 0;
		end
		else if (running) begin
			count_cycles <= count_cycles + 1'b1;
			if (in_valid && in_ready)
				count_input_bytes <= count_input_bytes + 1'b1;
			if (out_valid && out_ready)
				count_dense <= count_dense + 1'b1;
			if (out_valid && !out_ready)
				count_dense_stall <= count_dense_stall + 1'b1;
			if (mem_req_valid && mem_req_ready) begin
				if (mem_req_write)
					count_writes <= count_writes + 1'b1;
				else
					count_reads <= count_reads + 1'b1;
			end
			if (meta_valid && meta_ready)
				allocation <= 1;
			if (((packet_done && allocation) && !seal_sent) && seal_ready)
				seal_sent <= 1;
			if (packet_error != 0) begin
				error <= {4'h1, packet_error};
				running <= 0;
			end
			else if (store_error != 0) begin
				error <= {4'h2, store_error};
				running <= 0;
			end
			else if (store_done) begin
				done <= 1;
				running <= 0;
			end
		end
endmodule
module cs88_admission_v91i2a (
	clk,
	reset,
	start,
	abort_packet,
	cache_write,
	cache_index,
	cache_data,
	replay_req,
	replay_addr,
	replay_ready,
	replay_rsp_valid,
	replay_data,
	replay_rsp_addr,
	replay_rsp_epoch,
	lookup_req,
	lookup_tile,
	lookup_cell,
	lookup_rsp_valid,
	lookup_mode,
	lookup_scale,
	packet_bytes,
	epoch,
	accepted_ref_valid,
	accepted_qcache_valid,
	accepted_ref_fid,
	accepted_ref_generation,
	in_valid,
	in_last,
	in_data,
	in_ready,
	busy,
	receipt_valid,
	receipt_ready,
	error,
	receipt_epoch,
	fid,
	refid,
	generation,
	key_frame,
	mode_bytes,
	qmap_bytes,
	hud_bytes,
	data_bytes,
	plane_blocks,
	plane_offset,
	plane_length,
	plane_entropy,
	stage_read_req,
	stage_read_rsp,
	stage_write,
	stage_pending,
	stage_cancel,
	stage_read_addr,
	stage_rsp_addr,
	stage_req_epoch,
	stage_rsp_epoch,
	stage_read_data,
	debug_state,
	count_cycles,
	count_inputs,
	count_stage_reads,
	count_stage_responses,
	count_receipt_wait,
	required_cells
);
	input wire clk;
	input wire reset;
	input wire start;
	input wire abort_packet;
	input wire cache_write;
	input wire [10:0] cache_index;
	input wire [1:0] cache_data;
	input wire replay_req;
	input wire [31:0] replay_addr;
	output wire replay_ready;
	output reg replay_rsp_valid;
	output wire [7:0] replay_data;
	output wire [31:0] replay_rsp_addr;
	output wire [31:0] replay_rsp_epoch;
	input wire lookup_req;
	input wire [12:0] lookup_tile;
	input wire [10:0] lookup_cell;
	output reg lookup_rsp_valid;
	output reg [1:0] lookup_mode;
	output reg [1:0] lookup_scale;
	input wire [31:0] packet_bytes;
	input wire [31:0] epoch;
	input wire accepted_ref_valid;
	input wire accepted_qcache_valid;
	input wire [31:0] accepted_ref_fid;
	input wire [63:0] accepted_ref_generation;
	input wire in_valid;
	input wire in_last;
	input wire [7:0] in_data;
	output wire in_ready;
	output wire busy;
	output wire receipt_valid;
	input wire receipt_ready;
	output reg [7:0] error;
	output reg [31:0] receipt_epoch;
	output reg [31:0] fid;
	output reg [31:0] refid;
	output reg [63:0] generation;
	output reg key_frame;
	output reg [31:0] mode_bytes;
	output reg [31:0] qmap_bytes;
	output reg [31:0] hud_bytes;
	output reg [31:0] data_bytes;
	output reg [95:0] plane_blocks;
	output reg [95:0] plane_offset;
	output reg [95:0] plane_length;
	output reg [5:0] plane_entropy;
	output wire stage_read_req;
	output wire stage_read_rsp;
	output wire stage_write;
	output wire stage_pending;
	output wire stage_cancel;
	output wire [31:0] stage_read_addr;
	output wire [31:0] stage_rsp_addr;
	output wire [31:0] stage_req_epoch;
	output wire [31:0] stage_rsp_epoch;
	output wire [7:0] stage_read_data;
	output wire [7:0] debug_state;
	output reg [63:0] count_cycles;
	output reg [63:0] count_inputs;
	output reg [63:0] count_stage_reads;
	output reg [63:0] count_stage_responses;
	output reg [63:0] count_receipt_wait;
	output reg [31:0] required_cells;
	localparam [7:0] IDLE = 0;
	localparam [7:0] RX = 1;
	localparam [7:0] CRC_CHECK = 2;
	localparam [7:0] HEADER_LOAD = 3;
	localparam [7:0] HEADER_BYTE = 4;
	localparam [7:0] HEADER_CHECK = 5;
	localparam [7:0] KEY_TILE = 6;
	localparam [7:0] GROUP_BEGIN = 7;
	localparam [7:0] MODE_BIT = 8;
	localparam [7:0] MODE_LOADED = 9;
	localparam [7:0] GROUP_TILE = 10;
	localparam [7:0] GROUP_NEXT = 11;
	localparam [7:0] MODE_END = 12;
	localparam [7:0] ACTIVE_SCAN = 13;
	localparam [7:0] Q_LOAD = 14;
	localparam [7:0] Q_BYTE = 15;
	localparam [7:0] Q_CHECK = 16;
	localparam [7:0] Q_RUN = 17;
	localparam [7:0] PLANE_BEGIN = 18;
	localparam [7:0] CHUNK_NUMBER = 19;
	localparam [7:0] CHUNK_BLOCKS = 20;
	localparam [7:0] CHUNK_LENGTH = 21;
	localparam [7:0] CHUNK_MAGIC = 22;
	localparam [7:0] PLANE_NEXT = 23;
	localparam [7:0] COMPLETE = 24;
	localparam [7:0] RECEIPT = 25;
	localparam [7:0] FINISHED = 26;
	localparam [7:0] FAILED = 27;
	localparam [7:0] FETCH_REQ = 28;
	localparam [7:0] FETCH_WAIT = 29;
	localparam [7:0] WORD_BYTE = 30;
	localparam [7:0] ACTIVE_CLEAR = 31;
	localparam [7:0] Q_FILL = 32;
	localparam integer MAX_BYTES = 49152;
	reg [7:0] state;
	reg [7:0] fetch_return;
	reg [7:0] word_return;
	reg [7:0] memory [0:MAX_BYTES - 1];
	reg [7:0] header [0:127];
	reg [7:0] qbuffer [0:353];
	reg active_cell [0:1349];
	reg [1:0] modes [0:8099];
	reg [1:0] scales [0:1349];
	reg [6:0] q_remaining;
	reg [1:0] q_value;
	reg [7:0] ram_data;
	reg [7:0] byte_value;
	reg [31:0] ram_addr;
	reg [31:0] ram_epoch;
	reg [31:0] fetch_addr;
	reg [31:0] size_bytes;
	reg [31:0] received;
	reg [31:0] outer_crc;
	reg [31:0] outer_trailer;
	reg snapshot_valid;
	reg snapshot_cache;
	reg [31:0] snapshot_fid;
	reg [63:0] snapshot_generation;
	reg [31:0] cursor;
	reg [31:0] q_start;
	reg [31:0] residual_start;
	reg [31:0] residual_end;
	reg [31:0] header_index;
	reg [31:0] q_index;
	reg [31:0] q_crc;
	reg [31:0] q_trailer;
	reg [31:0] q_runs;
	reg [31:0] tile;
	reg [31:0] group_end;
	reg [31:0] group_visible;
	reg [31:0] mixed_ones;
	reg [1:0] plane;
	reg [1:0] group_tag;
	reg [7:0] bit_cache;
	reg [3:0] bits_left;
	reg tag_second;
	reg first_tag_bit;
	reg mixed_bit;
	reg [31:0] mode_cursor;
	reg [31:0] active_index;
	reg [31:0] word_cursor;
	reg [31:0] word_index;
	reg [23:0] word_acc;
	reg [31:0] word_value;
	reg [31:0] chunk_length;
	integer i;
	function automatic [31:0] crc_byte;
		input reg [31:0] old_crc;
		input reg [7:0] b;
		reg [31:0] c;
		begin
			c = old_crc ^ {24'd0, b};
			begin : sv2v_autoblock_1
				integer k;
				for (k = 0; k < 8; k = k + 1)
					c = (c[0] ? (c >> 1) ^ 32'hedb88320 : c >> 1);
			end
			crc_byte = c;
		end
	endfunction
	function automatic [31:0] h32;
		input integer n;
		h32 = {header[n], header[n + 1], header[n + 2], header[n + 3]};
	endfunction
	function automatic [15:0] h16;
		input integer n;
		h16 = {header[n], header[n + 1]};
	endfunction
	function automatic hidden;
		input reg [1:0] p;
		input reg [31:0] t;
		reg [0:1] _sv2v_jump;
		begin
			_sv2v_jump = 2'b00;
			if (p != 0) begin
				hidden = (t >= 1046) && (t <= 1064);
				_sv2v_jump = 2'b11;
			end
			if (_sv2v_jump == 2'b00) begin
				hidden = (((((((((t >= 633) && (t <= 651)) || ((t >= 723) && (t <= 741))) || ((t >= 993) && (t <= 1011))) || ((t >= 1083) && (t <= 1101))) || ((t >= 4071) && (t <= 4110))) || ((t >= 4161) && (t <= 4200))) || ((t >= 4251) && (t <= 4290))) || ((t >= 4431) && (t <= 4460))) || ((t >= 4521) && (t <= 4550));
				_sv2v_jump = 2'b11;
			end
		end
	endfunction
	function automatic [31:0] tile_count;
		input reg [1:0] p;
		tile_count = (p == 0 ? 32'd5400 : 32'd1350);
	endfunction
	function automatic [31:0] cell_index;
		input reg [1:0] p;
		input reg [31:0] t;
		cell_index = (p == 0 ? (((t / 90) / 2) * 45) + ((t % 90) / 2) : t);
	endfunction
	function automatic [31:0] visible_group;
		input reg [1:0] p;
		input reg [31:0] t;
		reg [31:0] n;
		begin
			n = 0;
			begin : sv2v_autoblock_2
				integer k;
				for (k = 0; k < 16; k = k + 1)
					if (((t + k) < tile_count(p)) && !hidden(p, t + k))
						n = n + 1;
			end
			visible_group = n;
		end
	endfunction
	task automatic reject;
		input reg [7:0] code;
		begin
			error <= code;
			state <= FAILED;
		end
	endtask
	task automatic request_byte;
		input reg [31:0] address;
		input reg [7:0] continuation;
		begin
			fetch_addr <= address;
			fetch_return <= continuation;
			state <= FETCH_REQ;
		end
	endtask
	task automatic request_word;
		input reg [31:0] address;
		input reg [7:0] continuation;
		begin
			word_cursor <= address;
			word_index <= 0;
			word_acc <= 0;
			word_return <= continuation;
			request_byte(address, WORD_BYTE);
		end
	endtask
	function automatic [10:0] sv2v_cast_11;
		input reg [10:0] inp;
		sv2v_cast_11 = inp;
	endfunction
	task automatic residual_tile;
		begin
			active_cell[sv2v_cast_11(cell_index(plane, tile))] <= 1'b1;
			plane_blocks[(2 - plane) * 32+:32] <= plane_blocks[(2 - plane) * 32+:32] + 1;
		end
	endtask
	assign replay_ready = ((((state == FINISHED) && !reset) && !start) && !abort_packet) && (replay_addr < size_bytes);
	assign replay_data = ram_data;
	assign replay_rsp_addr = ram_addr;
	assign replay_rsp_epoch = ram_epoch;
	assign in_ready = (((state == RX) && !reset) && !start) && !abort_packet;
	assign receipt_valid = (((state == RECEIPT) && !reset) && !start) && !abort_packet;
	assign busy = ((state != IDLE) && (state != FINISHED)) && (state != FAILED);
	assign stage_read_req = (((state == FETCH_REQ) && !reset) && !start) && !abort_packet;
	assign stage_read_rsp = (((state == FETCH_WAIT) && !reset) && !start) && !abort_packet;
	assign stage_write = in_valid && in_ready;
	assign stage_pending = state == FETCH_WAIT;
	assign stage_cancel = (reset || start) || abort_packet;
	assign stage_read_addr = fetch_addr;
	assign stage_rsp_addr = ram_addr;
	assign stage_req_epoch = receipt_epoch;
	assign stage_rsp_epoch = ram_epoch;
	assign stage_read_data = ram_data;
	assign debug_state = state;
	function automatic [12:0] sv2v_cast_13;
		input reg [12:0] inp;
		sv2v_cast_13 = inp;
	endfunction
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	always_ff @(posedge clk) begin
		if (stage_write)
			memory[received[15:0]] <= in_data;
		replay_rsp_valid <= replay_req && replay_ready;
		lookup_rsp_valid <= (((lookup_req && (state == FINISHED)) && !reset) && !start) && !abort_packet;
		if (((cache_write && !reset) && !start) && !abort_packet)
			scales[cache_index] <= cache_data;
		if ((((lookup_req && (state == FINISHED)) && !reset) && !start) && !abort_packet) begin
			lookup_mode <= modes[lookup_tile];
			lookup_scale <= scales[lookup_cell];
		end
		if (stage_read_req) begin
			ram_data <= memory[fetch_addr[15:0]];
			ram_addr <= fetch_addr;
			ram_epoch <= receipt_epoch;
		end
		else if (replay_req && replay_ready) begin
			ram_data <= memory[replay_addr[15:0]];
			ram_addr <= replay_addr;
			ram_epoch <= receipt_epoch;
		end
		if ((reset || start) || abort_packet) begin
			state <= IDLE;
			error <= 0;
			receipt_epoch <= epoch;
			replay_rsp_valid <= 0;
			lookup_rsp_valid <= 0;
			size_bytes <= packet_bytes;
			received <= 0;
			outer_crc <= 32'hffffffff;
			outer_trailer <= 0;
			snapshot_valid <= accepted_ref_valid;
			snapshot_cache <= accepted_qcache_valid;
			snapshot_fid <= accepted_ref_fid;
			snapshot_generation <= accepted_ref_generation;
			fid <= 0;
			refid <= 0;
			generation <= 0;
			key_frame <= 0;
			mode_bytes <= 0;
			qmap_bytes <= 0;
			hud_bytes <= 0;
			data_bytes <= 0;
			required_cells <= 0;
			count_cycles <= 0;
			count_inputs <= 0;
			count_stage_reads <= 0;
			count_stage_responses <= 0;
			count_receipt_wait <= 0;
			for (i = 0; i < 3; i = i + 1)
				begin
					plane_blocks[(2 - i) * 32+:32] <= 0;
					plane_offset[(2 - i) * 32+:32] <= 0;
					plane_length[(2 - i) * 32+:32] <= 0;
					plane_entropy[(2 - i) * 2+:2] <= 0;
				end
			if ((start && !reset) && !abort_packet) begin
				if ((packet_bytes < 132) || (packet_bytes > MAX_BYTES)) begin
					state <= FAILED;
					error <= 1;
				end
				else begin
					active_index <= 0;
					state <= ACTIVE_CLEAR;
				end
			end
		end
		else begin
			if (busy)
				count_cycles <= count_cycles + 1;
			if (stage_read_req)
				count_stage_reads <= count_stage_reads + 1;
			if (stage_read_rsp)
				count_stage_responses <= count_stage_responses + 1;
			case (state)
				ACTIVE_CLEAR:
					if (active_index == 8100)
						state <= RX;
					else begin
						if (active_index < 1350)
							active_cell[active_index[10:0]] <= 0;
						modes[active_index[12:0]] <= 1;
						active_index <= active_index + 1;
					end
				RX:
					if (in_valid && in_ready) begin
						count_inputs <= count_inputs + 1;
						received <= received + 1;
						if (received < (size_bytes - 4))
							outer_crc <= crc_byte(outer_crc, in_data);
						else
							outer_trailer <= {outer_trailer[23:0], in_data};
						if (in_last != (received == (size_bytes - 1)))
							reject(2);
						else if (received == (size_bytes - 1))
							state <= CRC_CHECK;
					end
				CRC_CHECK:
					if (~outer_crc != outer_trailer)
						reject(3);
					else begin
						header_index <= 0;
						state <= HEADER_LOAD;
					end
				HEADER_LOAD:
					request_byte(header_index, HEADER_BYTE);
				HEADER_BYTE: begin
					header[header_index[6:0]] <= byte_value;
					if (header_index == 127)
						state <= HEADER_CHECK;
					else begin
						header_index <= header_index + 1;
						state <= HEADER_LOAD;
					end
				end
				HEADER_CHECK: begin : header_validation
					reg padding_ok;
					padding_ok = 1;
					begin : sv2v_autoblock_3
						integer k;
						for (k = 116; k < 128; k = k + 1)
							if (header[k] != 0)
								padding_ok = 0;
					end
					if ((((((h32(0) != 32'h43533838) || (header[4] != 1)) || (header[6] != 16)) || (h16(28) != 32)) || (h32(32) != 65536)) || (header[5] == 1 ? header[7] != 0 : header[7] != 3))
						reject(4);
					else if (((((((((((header[5] > 1) || (h16(24) != 720)) || (h16(26) != 480)) || (h16(30) != 0)) || !padding_ok) || (h32(36) > 976)) || (h32(40) < 16)) || (h32(40) > 354)) || (h32(44) < 110)) || (h32(44) > 49152)) || (((((64'd132 + {32'd0, h32(36)}) + {32'd0, h32(40)}) + {32'd0, h32(44)}) + {32'd0, h32(48)}) != {32'd0, size_bytes}))
						reject(5);
					else if (((h32(8) == 32'hffffffff) || ({h32(16), h32(20)} == 0)) || (snapshot_valid && ((h32(8) <= snapshot_fid) || ({h32(16), h32(20)} <= snapshot_generation))))
						reject(6);
					else if ((header[5] == 1 ? h32(12) != 32'hffffffff : !snapshot_valid || (h32(12) != snapshot_fid)))
						reject(7);
					else if ((header[5] == 1) && (h32(36) != 0))
						reject(8);
					else begin
						fid <= h32(8);
						refid <= h32(12);
						generation <= {h32(16), h32(20)};
						key_frame <= header[5] == 1;
						mode_bytes <= h32(36);
						qmap_bytes <= h32(40);
						hud_bytes <= h32(44);
						data_bytes <= h32(48);
						q_start <= 128 + h32(36);
						residual_start <= (128 + h32(36)) + h32(40);
						residual_end <= ((128 + h32(36)) + h32(40)) + h32(48);
						plane <= 0;
						tile <= 0;
						mode_cursor <= 128;
						bits_left <= 0;
						bit_cache <= 0;
						state <= (header[5] == 1 ? KEY_TILE : GROUP_BEGIN);
					end
				end
				KEY_TILE:
					if (tile == tile_count(plane)) begin
						tile <= 0;
						if (plane == 2)
							state <= MODE_END;
						else
							plane <= plane + 1;
					end
					else begin
						modes[sv2v_cast_13((plane == 0 ? 0 : (plane == 1 ? 5400 : 6750)) + tile)] <= (hidden(plane, tile) ? 2'd1 : 2'd2);
						if (!hidden(plane, tile))
							residual_tile;
						tile <= tile + 1;
					end
				GROUP_BEGIN: begin
					group_end <= ((tile + 16) < tile_count(plane) ? tile + 16 : tile_count(plane));
					group_visible <= visible_group(plane, tile);
					mixed_ones <= 0;
					tag_second <= 0;
					mixed_bit <= 0;
					state <= MODE_BIT;
				end
				MODE_BIT:
					if (bits_left == 0) begin
						if (mode_cursor >= (128 + mode_bytes))
							reject(8);
						else begin
							mode_cursor <= mode_cursor + 1;
							request_byte(mode_cursor, MODE_LOADED);
						end
					end
					else begin
						bit_cache <= {bit_cache[6:0], 1'b0};
						bits_left <= bits_left - 1;
						if (mixed_bit) begin
							modes[sv2v_cast_13((plane == 0 ? 0 : (plane == 1 ? 5400 : 6750)) + tile)] <= (bit_cache[7] ? 2'd2 : 2'd0);
							if (bit_cache[7]) begin
								residual_tile;
								mixed_ones <= mixed_ones + 1;
							end
							tile <= tile + 1;
							state <= GROUP_TILE;
						end
						else if (!tag_second) begin
							first_tag_bit <= bit_cache[7];
							tag_second <= 1;
						end
						else begin
							group_tag <= {first_tag_bit, bit_cache[7]};
							if (group_visible == 0) begin
								if ({first_tag_bit, bit_cache[7]} != 3)
									reject(8);
								else begin
									tile <= group_end;
									state <= GROUP_NEXT;
								end
							end
							else if ({first_tag_bit, bit_cache[7]} == 3)
								reject(8);
							else
								state <= GROUP_TILE;
						end
					end
				MODE_LOADED: begin
					bit_cache <= byte_value;
					bits_left <= 8;
					state <= MODE_BIT;
				end
				GROUP_TILE:
					if (tile == group_end) begin
						if ((group_tag == 2) && ((mixed_ones == 0) || (mixed_ones == group_visible)))
							reject(8);
						else
							state <= GROUP_NEXT;
					end
					else if (hidden(plane, tile) || (group_tag == 0)) begin
						modes[sv2v_cast_13((plane == 0 ? 0 : (plane == 1 ? 5400 : 6750)) + tile)] <= (hidden(plane, tile) ? 2'd1 : 2'd0);
						tile <= tile + 1;
					end
					else if (group_tag == 1) begin
						modes[sv2v_cast_13((plane == 0 ? 0 : (plane == 1 ? 5400 : 6750)) + tile)] <= 2'd2;
						residual_tile;
						tile <= tile + 1;
					end
					else begin
						mixed_bit <= 1;
						state <= MODE_BIT;
					end
				GROUP_NEXT:
					if (tile == tile_count(plane)) begin
						if (plane == 2)
							state <= MODE_END;
						else begin
							plane <= plane + 1;
							tile <= 0;
							state <= GROUP_BEGIN;
						end
					end
					else
						state <= GROUP_BEGIN;
				MODE_END:
					if (!key_frame && ((mode_cursor != (128 + mode_bytes)) || (bit_cache != 0)))
						reject(8);
					else begin
						active_index <= 0;
						required_cells <= 0;
						state <= ACTIVE_SCAN;
					end
				ACTIVE_SCAN:
					if (active_index == 1350) begin
						q_index <= 0;
						q_crc <= 32'hffffffff;
						q_trailer <= 0;
						state <= Q_LOAD;
					end
					else begin
						if (active_cell[active_index[10:0]])
							required_cells <= required_cells + 1;
						active_index <= active_index + 1;
					end
				Q_LOAD:
					request_byte(q_start + q_index, Q_BYTE);
				Q_BYTE: begin
					qbuffer[q_index[8:0]] <= byte_value;
					if (q_index < (qmap_bytes - 4))
						q_crc <= crc_byte(q_crc, byte_value);
					else
						q_trailer <= {q_trailer[23:0], byte_value};
					if (q_index == (qmap_bytes - 1))
						state <= Q_CHECK;
					else begin
						q_index <= q_index + 1;
						state <= Q_LOAD;
					end
				end
				Q_CHECK:
					if (~q_crc != q_trailer)
						reject(9);
					else if (((({qbuffer[0], qbuffer[1], qbuffer[2], qbuffer[3]} != 32'h514d3837) || (qbuffer[4] != 1)) || ({qbuffer[6], qbuffer[7]} != 1350)) || ((sv2v_cast_32({qbuffer[8], qbuffer[9]}) + 16) != qmap_bytes))
						reject(10);
					else if ((qbuffer[5] != 2) && (qbuffer[5] != 6))
						reject(4);
					else if (sv2v_cast_32({qbuffer[10], qbuffer[11]}) != required_cells)
						reject(11);
					else if (qbuffer[5] == 6) begin
						if ((key_frame || !snapshot_valid) || !snapshot_cache)
							reject(7);
						else if (qmap_bytes != 16)
							reject(10);
						else begin
							plane <= 0;
							cursor <= residual_start;
							state <= PLANE_BEGIN;
						end
					end
					else begin
						q_index <= 12;
						q_runs <= 0;
						state <= Q_RUN;
					end
				Q_RUN:
					if (q_index == (qmap_bytes - 4)) begin
						if (q_runs != 1350)
							reject(10);
						else begin
							plane <= 0;
							cursor <= residual_start;
							state <= PLANE_BEGIN;
						end
					end
					else if ((qbuffer[q_index[8:0]][7:6] > 2) || (((q_runs + sv2v_cast_32(qbuffer[q_index[8:0]][5:0])) + 1) > 1350))
						reject(10);
					else begin
						q_remaining <= {1'b0, qbuffer[q_index[8:0]][5:0]} + 1;
						q_value <= qbuffer[q_index[8:0]][7:6];
						q_index <= q_index + 1;
						state <= Q_FILL;
					end
				Q_FILL: begin
					scales[q_runs[10:0]] <= q_value;
					q_runs <= q_runs + 1;
					q_remaining <= q_remaining - 1;
					if (q_remaining == 1)
						state <= Q_RUN;
				end
				PLANE_BEGIN:
					if ((cursor + 4) > residual_end)
						reject(13);
					else
						request_word(cursor, CHUNK_NUMBER);
				CHUNK_NUMBER: begin
					cursor <= cursor + 4;
					if (word_value != (plane_blocks[(2 - plane) * 32+:32] == 0 ? 32'd0 : 32'd1))
						reject(12);
					else if (word_value == 0)
						state <= PLANE_NEXT;
					else if ((cursor + 12) > residual_end)
						reject(13);
					else
						request_word(cursor + 4, CHUNK_BLOCKS);
				end
				CHUNK_BLOCKS: begin
					cursor <= cursor + 4;
					if ((word_value != plane_blocks[(2 - plane) * 32+:32]) || (word_value == 0))
						reject(13);
					else
						request_word(cursor + 4, CHUNK_LENGTH);
				end
				CHUNK_LENGTH: begin
					cursor <= cursor + 4;
					chunk_length <= word_value;
					if (((word_value < 46) || (word_value > (46 + (128 * plane_blocks[(2 - plane) * 32+:32])))) || ((({32'd0, cursor} + 4) + {32'd0, word_value}) > {32'd0, residual_end}))
						reject(13);
					else begin
						plane_offset[(2 - plane) * 32+:32] <= cursor + 4;
						plane_length[(2 - plane) * 32+:32] <= word_value;
						request_word(cursor + 4, CHUNK_MAGIC);
					end
				end
				CHUNK_MAGIC: begin
					if (word_value == 32'h41423338)
						plane_entropy[(2 - plane) * 2+:2] <= 1;
					else if (word_value == 32'h42523838)
						plane_entropy[(2 - plane) * 2+:2] <= 2;
					else
						reject(14);
					if ((word_value == 32'h41423338) || (word_value == 32'h42523838)) begin
						cursor <= cursor + chunk_length;
						state <= PLANE_NEXT;
					end
				end
				PLANE_NEXT:
					if (plane == 2)
						state <= COMPLETE;
					else begin
						plane <= plane + 1;
						state <= PLANE_BEGIN;
					end
				COMPLETE:
					if (cursor != residual_end)
						reject(13);
					else
						state <= RECEIPT;
				RECEIPT:
					if (receipt_ready)
						state <= FINISHED;
					else
						count_receipt_wait <= count_receipt_wait + 1;
				FETCH_REQ: state <= FETCH_WAIT;
				FETCH_WAIT: begin
					byte_value <= ram_data;
					state <= fetch_return;
				end
				WORD_BYTE:
					if (word_index == 3) begin
						word_value <= {word_acc, byte_value};
						state <= word_return;
					end
					else begin
						word_acc <= {word_acc[15:0], byte_value};
						word_index <= word_index + 1;
						word_cursor <= word_cursor + 1;
						request_byte(word_cursor + 1, WORD_BYTE);
					end
				default:
					;
			endcase
		end
	end
endmodule
module byte_refill_queue_v91i2b (
	clk,
	reset,
	cancel,
	start,
	clear_stats,
	start_offset,
	start_length,
	start_epoch,
	req_valid,
	req_ready,
	req_addr,
	req_epoch,
	rsp_valid,
	rsp_addr,
	rsp_epoch,
	rsp_data,
	out_valid,
	out_ready,
	out_data,
	out_last,
	done,
	error,
	active,
	fifo_count,
	pending,
	push_event,
	pop_event,
	count_requests,
	count_responses,
	count_pops,
	count_stalls,
	count_cancel_queued,
	count_cancel_pending,
	max_count,
	max_owned
);
	input wire clk;
	input wire reset;
	input wire cancel;
	input wire start;
	input wire clear_stats;
	input wire [31:0] start_offset;
	input wire [31:0] start_length;
	input wire [31:0] start_epoch;
	output wire req_valid;
	input wire req_ready;
	output wire [31:0] req_addr;
	output wire [31:0] req_epoch;
	input wire rsp_valid;
	input wire [31:0] rsp_addr;
	input wire [31:0] rsp_epoch;
	input wire [7:0] rsp_data;
	output wire out_valid;
	input wire out_ready;
	output wire [7:0] out_data;
	output wire out_last;
	output reg done;
	output reg [7:0] error;
	output reg active;
	output reg [1:0] fifo_count;
	output reg pending;
	output wire push_event;
	output wire pop_event;
	output reg [31:0] count_requests;
	output reg [31:0] count_responses;
	output reg [31:0] count_pops;
	output reg [31:0] count_stalls;
	output reg [31:0] count_cancel_queued;
	output reg [31:0] count_cancel_pending;
	output reg [1:0] max_count;
	output reg [1:0] max_owned;
	reg [7:0] data [0:1];
	reg last [0:1];
	reg head;
	reg tail;
	reg pending_last;
	reg [31:0] offset;
	reg [31:0] length;
	reg [31:0] owner_epoch;
	reg [31:0] issued;
	reg [31:0] consumed;
	reg [31:0] pending_addr;
	wire blocked;
	wire response_fault;
	wire issue;
	wire [2:0] owned_after_pop;
	wire [2:0] next_count;
	wire [2:0] next_owned;
	assign blocked = ((reset || cancel) || start) || clear_stats;
	assign response_fault = active && ((pending && ((!rsp_valid || (rsp_addr != pending_addr)) || (rsp_epoch != owner_epoch))) || (!pending && rsp_valid));
	assign out_valid = ((active && (fifo_count != 0)) && !blocked) && !response_fault;
	assign out_data = data[head];
	assign out_last = last[head];
	assign pop_event = out_valid && out_ready;
	assign push_event = (((active && pending) && rsp_valid) && !blocked) && !response_fault;
	assign owned_after_pop = ({1'b0, fifo_count} + {2'b00, pending}) - {2'b00, pop_event};
	assign req_valid = (((active && (issued < length)) && (owned_after_pop < 3'd2)) && !blocked) && !response_fault;
	assign req_addr = offset + issued;
	assign req_epoch = owner_epoch;
	assign issue = req_valid && req_ready;
	assign next_count = ({1'b0, fifo_count} + {2'b00, push_event}) - {2'b00, pop_event};
	assign next_owned = next_count + {2'b00, issue};
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [2:0] sv2v_cast_3;
		input reg [2:0] inp;
		sv2v_cast_3 = inp;
	endfunction
	always_ff @(posedge clk) begin
		if (reset || clear_stats) begin
			count_requests <= 0;
			count_responses <= 0;
			count_pops <= 0;
			count_stalls <= 0;
			count_cancel_queued <= 0;
			count_cancel_pending <= 0;
			max_count <= 0;
			max_owned <= 0;
		end
		else begin
			if (issue)
				count_requests <= count_requests + 1;
			if (push_event)
				count_responses <= count_responses + 1;
			if (pop_event)
				count_pops <= count_pops + 1;
			if (out_valid && !out_ready)
				count_stalls <= count_stalls + 1;
			if ((cancel || start) || response_fault) begin
				count_cancel_queued <= count_cancel_queued + sv2v_cast_32(fifo_count);
				count_cancel_pending <= count_cancel_pending + sv2v_cast_32(pending);
			end
			if (!blocked && !response_fault) begin
				if (next_count > sv2v_cast_3(max_count))
					max_count <= next_count[1:0];
				if (next_owned > sv2v_cast_3(max_owned))
					max_owned <= next_owned[1:0];
			end
		end
		if ((reset || cancel) || clear_stats) begin
			active <= 0;
			done <= 0;
			error <= 0;
			fifo_count <= 0;
			pending <= 0;
			head <= 0;
			tail <= 0;
			offset <= 0;
			length <= 0;
			owner_epoch <= 0;
			issued <= 0;
			consumed <= 0;
			pending_addr <= 0;
			pending_last <= 0;
		end
		else if (start) begin
			active <= start_length != 0;
			done <= start_length == 0;
			error <= 0;
			fifo_count <= 0;
			pending <= 0;
			head <= 0;
			tail <= 0;
			offset <= start_offset;
			length <= start_length;
			owner_epoch <= start_epoch;
			issued <= 0;
			consumed <= 0;
			pending_addr <= 0;
			pending_last <= 0;
		end
		else if (response_fault) begin
			error <= 1;
			active <= 0;
			done <= 0;
			fifo_count <= 0;
			pending <= 0;
			head <= 0;
			tail <= 0;
		end
		else if (active) begin
			pending <= issue;
			fifo_count <= next_count[1:0];
			if (issue) begin
				issued <= issued + 1;
				pending_addr <= req_addr;
				pending_last <= (issued + 1) == length;
			end
			if (push_event) begin
				data[tail] <= rsp_data;
				last[tail] <= pending_last;
				tail <= !tail;
			end
			if (pop_event) begin
				head <= !head;
				consumed <= consumed + 1;
				if (out_last) begin
					active <= 0;
					done <= 1;
				end
			end
		end
	end
endmodule
module cu66_inverse_stream_v91j (
	clk,
	reset,
	start,
	cancel,
	input_done,
	in_valid,
	in_ready,
	in_epoch,
	in_child_epoch,
	in_plane,
	in_qscale,
	in_block,
	in_tile,
	in_qcell,
	in_index,
	in_value,
	out_valid,
	out_ready,
	out_epoch,
	out_child_epoch,
	out_token,
	out_plane,
	out_qscale,
	out_block,
	out_tile,
	out_qcell,
	out_index,
	out_value,
	busy,
	done,
	error,
	bank_state,
	fill_bank,
	math_bank,
	math_state,
	owned_banks,
	max_owned_banks,
	dbg_launch,
	dbg_dequant,
	dbg_token,
	dbg_coefficients,
	dbg_dequantized,
	dbg_epoch,
	dbg_child_epoch,
	dbg_plane,
	dbg_qscale,
	dbg_block,
	dbg_tile,
	dbg_qcell,
	count_inputs,
	count_tiles,
	count_launches,
	count_dequant,
	count_outputs,
	count_completed_tiles,
	count_input_stalls,
	count_output_stalls,
	count_cancelled_banks
);
	input wire clk;
	input wire reset;
	input wire start;
	input wire cancel;
	input wire input_done;
	input wire in_valid;
	output wire in_ready;
	input wire [31:0] in_epoch;
	input wire [31:0] in_child_epoch;
	input wire [1:0] in_plane;
	input wire [1:0] in_qscale;
	input wire [15:0] in_block;
	input wire [12:0] in_tile;
	input wire [10:0] in_qcell;
	input wire [5:0] in_index;
	input wire signed [15:0] in_value;
	output wire out_valid;
	input wire out_ready;
	output wire [31:0] out_epoch;
	output wire [31:0] out_child_epoch;
	output wire [31:0] out_token;
	output wire [1:0] out_plane;
	output wire [1:0] out_qscale;
	output wire [15:0] out_block;
	output wire [12:0] out_tile;
	output wire [10:0] out_qcell;
	output wire [5:0] out_index;
	output wire signed [23:0] out_value;
	output wire busy;
	output reg done;
	output reg [7:0] error;
	output reg [3:0] bank_state;
	output reg fill_bank;
	output reg math_bank;
	output reg [2:0] math_state;
	output wire [1:0] owned_banks;
	output reg [1:0] max_owned_banks;
	output wire dbg_launch;
	output wire dbg_dequant;
	output wire [31:0] dbg_token;
	output wire [1023:0] dbg_coefficients;
	output wire [1279:0] dbg_dequantized;
	output wire [31:0] dbg_epoch;
	output wire [31:0] dbg_child_epoch;
	output wire [1:0] dbg_plane;
	output wire [1:0] dbg_qscale;
	output wire [15:0] dbg_block;
	output wire [12:0] dbg_tile;
	output wire [10:0] dbg_qcell;
	output reg [63:0] count_inputs;
	output reg [63:0] count_tiles;
	output reg [63:0] count_launches;
	output reg [63:0] count_dequant;
	output reg [63:0] count_outputs;
	output reg [63:0] count_completed_tiles;
	output reg [63:0] count_input_stalls;
	output reg [63:0] count_output_stalls;
	output reg [63:0] count_cancelled_banks;
	localparam [1:0] FREE = 0;
	localparam [1:0] FILL = 1;
	localparam [1:0] READY = 2;
	localparam [1:0] ACTIVE = 3;
	localparam [2:0] M_IDLE = 0;
	localparam [2:0] M_DQ_SEND = 1;
	localparam [2:0] M_DQ_WAIT = 2;
	localparam [2:0] M_IDCT_WAIT = 3;
	localparam [2:0] M_EMIT = 4;
	reg running;
	reg finished_input;
	wire kill;
	reg [1023:0] coefficients [0:1];
	reg [31:0] epochs [0:1];
	reg [31:0] child_epochs [0:1];
	reg [31:0] tokens [0:1];
	reg [1:0] planes [0:1];
	reg [1:0] scales [0:1];
	reg [15:0] blocks [0:1];
	reg [12:0] tiles [0:1];
	reg [10:0] cells [0:1];
	reg [5:0] fill_index;
	reg [5:0] emit_index;
	reg [31:0] next_token;
	wire dq_ready;
	wire dq_valid;
	wire dq_out_ready;
	wire dq_error;
	wire [31:0] dq_id;
	wire [1279:0] dq_data;
	wire idct_ready;
	wire idct_valid;
	wire idct_out_ready;
	wire idct_error;
	wire [31:0] idct_id;
	wire [1535:0] idct_data;
	wire [31:0] unused_idct_cycles;
	wire input_metadata_bad;
	reg [7:0] input_fault;
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [10:0] sv2v_cast_11;
		input reg [10:0] inp;
		sv2v_cast_11 = inp;
	endfunction
	function automatic [10:0] quant_cell;
		input reg [1:0] p;
		input reg [12:0] t;
		quant_cell = (p == 0 ? sv2v_cast_11((((sv2v_cast_32(t) / 90) / 2) * 45) + ((sv2v_cast_32(t) % 90) / 2)) : sv2v_cast_11(t));
	endfunction
	task automatic fail;
		input reg [7:0] reason;
		begin
			error <= reason;
			running <= 0;
			done <= 0;
			bank_state[2+:2] <= FREE;
			bank_state[0+:2] <= FREE;
			fill_index <= 0;
			math_state <= M_IDLE;
		end
	endtask
	assign kill = ((reset || start) || cancel) || (error != 0);
	assign busy = (running || (owned_banks != 0)) || (math_state != M_IDLE);
	function automatic [1:0] sv2v_cast_2;
		input reg [1:0] inp;
		sv2v_cast_2 = inp;
	endfunction
	assign owned_banks = sv2v_cast_2(bank_state[2+:2] != FREE) + sv2v_cast_2(bank_state[0+:2] != FREE);
	assign in_ready = (((running && !finished_input) && !input_done) && !kill) && ((bank_state[(1 - fill_bank) * 2+:2] == FREE) || (bank_state[(1 - fill_bank) * 2+:2] == FILL));
	assign input_metadata_bad = (((in_plane > 2) || (in_tile >= (in_plane == 0 ? 13'd5400 : 13'd1350))) || (in_qcell != quant_cell(in_plane, in_tile))) || ((bank_state[(1 - fill_bank) * 2+:2] == FILL) && (((((((epochs[fill_bank] != in_epoch) || (child_epochs[fill_bank] != in_child_epoch)) || (planes[fill_bank] != in_plane)) || (scales[fill_bank] != in_qscale)) || (blocks[fill_bank] != in_block)) || (tiles[fill_bank] != in_tile)) || (cells[fill_bank] != in_qcell)));
	always_comb begin
		input_fault = 0;
		if (input_done && (fill_index != 0))
			input_fault = 4;
		else if (in_valid && in_ready) begin
			if (in_index != fill_index)
				input_fault = 1;
			else if (input_metadata_bad)
				input_fault = 2;
			else if (((in_qscale == 3) || (in_value < -16'sd2048)) || (in_value > 16'sd2048))
				input_fault = 3;
			else if ((fill_index == 0) && (next_token == 32'hffffffff))
				input_fault = 7;
		end
	end
	assign out_valid = ((((running && (math_state == M_EMIT)) && idct_valid) && !kill) && !idct_error) && (idct_id == tokens[math_bank]);
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	assign out_value = $signed(idct_data[sv2v_cast_32_signed(emit_index) * 24+:24]);
	assign out_index = emit_index;
	assign out_epoch = epochs[math_bank];
	assign out_child_epoch = child_epochs[math_bank];
	assign out_token = tokens[math_bank];
	assign out_plane = planes[math_bank];
	assign out_qscale = scales[math_bank];
	assign out_block = blocks[math_bank];
	assign out_tile = tiles[math_bank];
	assign out_qcell = cells[math_bank];
	assign dq_out_ready = ((((math_state == M_DQ_WAIT) && idct_ready) && !kill) && !dq_error) && (dq_id == tokens[math_bank]);
	assign idct_out_ready = (((((math_state == M_EMIT) && out_ready) && (emit_index == 63)) && !kill) && !idct_error) && (idct_id == tokens[math_bank]);
	assign dbg_launch = ((math_state == M_DQ_SEND) && dq_ready) && !kill;
	assign dbg_dequant = dq_valid && dq_out_ready;
	assign dbg_coefficients = coefficients[math_bank];
	assign dbg_dequantized = dq_data;
	assign dbg_token = tokens[math_bank];
	assign dbg_epoch = epochs[math_bank];
	assign dbg_child_epoch = child_epochs[math_bank];
	assign dbg_plane = planes[math_bank];
	assign dbg_qscale = scales[math_bank];
	assign dbg_block = blocks[math_bank];
	assign dbg_tile = tiles[math_bank];
	assign dbg_qcell = cells[math_bank];
	cu66_dequant dequant(
		.clk(clk),
		.rst(reset),
		.abort_i((start || cancel) || (error != 0)),
		.in_valid((math_state == M_DQ_SEND) && !kill),
		.in_ready(dq_ready),
		.in_id(tokens[math_bank]),
		.in_coefficients(coefficients[math_bank]),
		.in_chroma(planes[math_bank] != 0),
		.in_scale_code(scales[math_bank]),
		.out_valid(dq_valid),
		.out_ready(dq_out_ready),
		.out_id(dq_id),
		.out_dequantized(dq_data),
		.out_error(dq_error)
	);
	cu66_idct8x8 inverse(
		.clk(clk),
		.rst(reset),
		.abort_frame((start || cancel) || (error != 0)),
		.in_valid((((dq_valid && (math_state == M_DQ_WAIT)) && !kill) && !dq_error) && (dq_id == tokens[math_bank])),
		.in_ready(idct_ready),
		.in_id(dq_id),
		.in_tile(dq_data),
		.out_valid(idct_valid),
		.out_ready(idct_out_ready),
		.out_id(idct_id),
		.out_tile(idct_data),
		.out_error(idct_error),
		.active_cycles(unused_idct_cycles)
	);
	function automatic [63:0] sv2v_cast_64;
		input reg [63:0] inp;
		sv2v_cast_64 = inp;
	endfunction
	always_ff @(posedge clk)
		if ((reset || start) || cancel) begin
			running <= (start && !reset) && !cancel;
			finished_input <= 0;
			done <= 0;
			error <= 0;
			bank_state[2+:2] <= FREE;
			bank_state[0+:2] <= FREE;
			fill_bank <= 0;
			math_bank <= 0;
			fill_index <= 0;
			emit_index <= 0;
			math_state <= M_IDLE;
			next_token <= 0;
			if (reset || start) begin
				count_inputs <= 0;
				count_tiles <= 0;
				count_launches <= 0;
				count_dequant <= 0;
				count_outputs <= 0;
				count_completed_tiles <= 0;
				count_input_stalls <= 0;
				count_output_stalls <= 0;
				count_cancelled_banks <= 0;
				max_owned_banks <= 0;
			end
			else
				count_cancelled_banks <= count_cancelled_banks + sv2v_cast_64(owned_banks);
		end
		else if ((error == 0) && running) begin
			if (owned_banks > max_owned_banks)
				max_owned_banks <= owned_banks;
			if (in_valid && !in_ready)
				count_input_stalls <= count_input_stalls + 1;
			if (out_valid && !out_ready)
				count_output_stalls <= count_output_stalls + 1;
			if (in_valid && in_ready)
				count_inputs <= count_inputs + 1;
			if (dbg_launch)
				count_launches <= count_launches + 1;
			if (dbg_dequant)
				count_dequant <= count_dequant + 1;
			if (out_valid && out_ready) begin
				count_outputs <= count_outputs + 1;
				if (emit_index == 63)
					count_completed_tiles <= count_completed_tiles + 1;
			end
			if (input_fault != 0)
				fail(input_fault);
			else begin
				if (input_done)
					finished_input <= 1;
				if (in_valid && in_ready) begin
					coefficients[fill_bank][sv2v_cast_32_signed(fill_index) * 16+:16] <= in_value;
					if (fill_index == 0) begin
						epochs[fill_bank] <= in_epoch;
						child_epochs[fill_bank] <= in_child_epoch;
						planes[fill_bank] <= in_plane;
						scales[fill_bank] <= in_qscale;
						blocks[fill_bank] <= in_block;
						tiles[fill_bank] <= in_tile;
						cells[fill_bank] <= in_qcell;
						tokens[fill_bank] <= next_token + 1;
						next_token <= next_token + 1;
						bank_state[(1 - fill_bank) * 2+:2] <= FILL;
					end
					if (fill_index == 63) begin
						bank_state[(1 - fill_bank) * 2+:2] <= READY;
						fill_bank <= !fill_bank;
						fill_index <= 0;
						count_tiles <= count_tiles + 1;
					end
					else
						fill_index <= fill_index + 1;
				end
				case (math_state)
					M_IDLE:
						if (bank_state[(1 - math_bank) * 2+:2] == READY) begin
							bank_state[(1 - math_bank) * 2+:2] <= ACTIVE;
							math_state <= M_DQ_SEND;
						end
					M_DQ_SEND:
						if (dbg_launch)
							math_state <= M_DQ_WAIT;
					M_DQ_WAIT:
						if (dq_valid) begin
							if (dq_error || (dq_id != tokens[math_bank]))
								fail(5);
							else if (dq_out_ready)
								math_state <= M_IDCT_WAIT;
						end
					M_IDCT_WAIT:
						if (idct_valid) begin
							if (idct_error || (idct_id != tokens[math_bank]))
								fail(6);
							else begin
								emit_index <= 0;
								math_state <= M_EMIT;
							end
						end
					M_EMIT:
						if (idct_valid && (idct_error || (idct_id != tokens[math_bank])))
							fail(6);
						else if (out_valid && out_ready) begin
							if (emit_index == 63) begin
								bank_state[(1 - math_bank) * 2+:2] <= FREE;
								math_bank <= !math_bank;
								math_state <= M_IDLE;
								emit_index <= 0;
							end
							else
								emit_index <= emit_index + 1;
						end
					default:
						;
				endcase
				if ((finished_input && (owned_banks == 0)) && (math_state == M_IDLE)) begin
					running <= 0;
					done <= 1;
				end
			end
		end
endmodule
module cu66_dequant (
	clk,
	rst,
	abort_i,
	in_valid,
	in_ready,
	in_id,
	in_coefficients,
	in_chroma,
	in_scale_code,
	out_valid,
	out_ready,
	out_id,
	out_dequantized,
	out_error
);
	input wire clk;
	input wire rst;
	input wire abort_i;
	input wire in_valid;
	output wire in_ready;
	input wire [31:0] in_id;
	input wire [1023:0] in_coefficients;
	input wire in_chroma;
	input wire [1:0] in_scale_code;
	output wire out_valid;
	input wire out_ready;
	output reg [31:0] out_id;
	output reg [1279:0] out_dequantized;
	output reg out_error;
	function automatic [7:0] base_quant;
		input reg chroma;
		input reg [5:0] position;
		case ({chroma, position})
			7'd0: base_quant = 8'd16;
			7'd1: base_quant = 8'd11;
			7'd2: base_quant = 8'd10;
			7'd3: base_quant = 8'd16;
			7'd4: base_quant = 8'd24;
			7'd5: base_quant = 8'd40;
			7'd6: base_quant = 8'd51;
			7'd7: base_quant = 8'd61;
			7'd8: base_quant = 8'd12;
			7'd9: base_quant = 8'd12;
			7'd10: base_quant = 8'd14;
			7'd11: base_quant = 8'd19;
			7'd12: base_quant = 8'd26;
			7'd13: base_quant = 8'd58;
			7'd14: base_quant = 8'd60;
			7'd15: base_quant = 8'd55;
			7'd16: base_quant = 8'd14;
			7'd17: base_quant = 8'd13;
			7'd18: base_quant = 8'd16;
			7'd19: base_quant = 8'd24;
			7'd20: base_quant = 8'd40;
			7'd21: base_quant = 8'd57;
			7'd22: base_quant = 8'd69;
			7'd23: base_quant = 8'd56;
			7'd24: base_quant = 8'd14;
			7'd25: base_quant = 8'd17;
			7'd26: base_quant = 8'd22;
			7'd27: base_quant = 8'd29;
			7'd28: base_quant = 8'd51;
			7'd29: base_quant = 8'd87;
			7'd30: base_quant = 8'd80;
			7'd31: base_quant = 8'd62;
			7'd32: base_quant = 8'd18;
			7'd33: base_quant = 8'd22;
			7'd34: base_quant = 8'd37;
			7'd35: base_quant = 8'd56;
			7'd36: base_quant = 8'd68;
			7'd37: base_quant = 8'd109;
			7'd38: base_quant = 8'd103;
			7'd39: base_quant = 8'd77;
			7'd40: base_quant = 8'd24;
			7'd41: base_quant = 8'd35;
			7'd42: base_quant = 8'd55;
			7'd43: base_quant = 8'd64;
			7'd44: base_quant = 8'd81;
			7'd45: base_quant = 8'd104;
			7'd46: base_quant = 8'd113;
			7'd47: base_quant = 8'd92;
			7'd48: base_quant = 8'd49;
			7'd49: base_quant = 8'd64;
			7'd50: base_quant = 8'd78;
			7'd51: base_quant = 8'd87;
			7'd52: base_quant = 8'd103;
			7'd53: base_quant = 8'd121;
			7'd54: base_quant = 8'd120;
			7'd55: base_quant = 8'd101;
			7'd56: base_quant = 8'd72;
			7'd57: base_quant = 8'd92;
			7'd58: base_quant = 8'd95;
			7'd59: base_quant = 8'd98;
			7'd60: base_quant = 8'd112;
			7'd61: base_quant = 8'd100;
			7'd62: base_quant = 8'd103;
			7'd63: base_quant = 8'd99;
			7'd64: base_quant = 8'd17;
			7'd65: base_quant = 8'd18;
			7'd66: base_quant = 8'd24;
			7'd67: base_quant = 8'd47;
			7'd68: base_quant = 8'd99;
			7'd69: base_quant = 8'd99;
			7'd70: base_quant = 8'd99;
			7'd71: base_quant = 8'd99;
			7'd72: base_quant = 8'd18;
			7'd73: base_quant = 8'd21;
			7'd74: base_quant = 8'd26;
			7'd75: base_quant = 8'd66;
			7'd76: base_quant = 8'd99;
			7'd77: base_quant = 8'd99;
			7'd78: base_quant = 8'd99;
			7'd79: base_quant = 8'd99;
			7'd80: base_quant = 8'd24;
			7'd81: base_quant = 8'd26;
			7'd82: base_quant = 8'd56;
			7'd83: base_quant = 8'd99;
			7'd84: base_quant = 8'd99;
			7'd85: base_quant = 8'd99;
			7'd86: base_quant = 8'd99;
			7'd87: base_quant = 8'd99;
			7'd88: base_quant = 8'd47;
			7'd89: base_quant = 8'd66;
			7'd90: base_quant = 8'd99;
			7'd91: base_quant = 8'd99;
			7'd92: base_quant = 8'd99;
			7'd93: base_quant = 8'd99;
			7'd94: base_quant = 8'd99;
			7'd95: base_quant = 8'd99;
			7'd96: base_quant = 8'd99;
			7'd97: base_quant = 8'd99;
			7'd98: base_quant = 8'd99;
			7'd99: base_quant = 8'd99;
			7'd100: base_quant = 8'd99;
			7'd101: base_quant = 8'd99;
			7'd102: base_quant = 8'd99;
			7'd103: base_quant = 8'd99;
			7'd104: base_quant = 8'd99;
			7'd105: base_quant = 8'd99;
			7'd106: base_quant = 8'd99;
			7'd107: base_quant = 8'd99;
			7'd108: base_quant = 8'd99;
			7'd109: base_quant = 8'd99;
			7'd110: base_quant = 8'd99;
			7'd111: base_quant = 8'd99;
			7'd112: base_quant = 8'd99;
			7'd113: base_quant = 8'd99;
			7'd114: base_quant = 8'd99;
			7'd115: base_quant = 8'd99;
			7'd116: base_quant = 8'd99;
			7'd117: base_quant = 8'd99;
			7'd118: base_quant = 8'd99;
			7'd119: base_quant = 8'd99;
			7'd120: base_quant = 8'd99;
			7'd121: base_quant = 8'd99;
			7'd122: base_quant = 8'd99;
			7'd123: base_quant = 8'd99;
			7'd124: base_quant = 8'd99;
			7'd125: base_quant = 8'd99;
			7'd126: base_quant = 8'd99;
			7'd127: base_quant = 8'd99;
			default: base_quant = 0;
		endcase
	endfunction
	reg [1:0] state;
	reg [1023:0] coefficients;
	reg chroma;
	reg [1:0] scale_code;
	reg [2:0] group_index;
	reg input_bad;
	reg [7:0] q [0:7];
	reg [8:0] scaled [0:7];
	reg signed [24:0] products [0:7];
	function automatic signed [2:0] sv2v_cast_3_signed;
		input reg signed [2:0] inp;
		sv2v_cast_3_signed = inp;
	endfunction
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	always_comb begin
		input_bad = in_scale_code == 3;
		begin : sv2v_autoblock_1
			integer i;
			for (i = 0; i < 64; i = i + 1)
				if (($signed(in_coefficients[i * 16+:16]) < -16'sd2048) || ($signed(in_coefficients[i * 16+:16]) > 16'sd2048))
					input_bad = 1;
		end
		begin : sv2v_autoblock_2
			integer lane;
			for (lane = 0; lane < 8; lane = lane + 1)
				begin
					case (scale_code)
						0: scaled[lane] = ({1'b0, base_quant(chroma, {group_index, sv2v_cast_3_signed(lane)})} + 9'd1) >> 1;
						1: scaled[lane] = {1'b0, base_quant(chroma, {group_index, sv2v_cast_3_signed(lane)})};
						2: scaled[lane] = {base_quant(chroma, {group_index, sv2v_cast_3_signed(lane)}), 1'b0};
						default: scaled[lane] = 0;
					endcase
					q[lane] = (scaled[lane] > 255 ? 8'hff : scaled[lane][7:0]);
					products[lane] = $signed(coefficients[((sv2v_cast_32_signed(group_index) * 8) + lane) * 16+:16]) * $signed({1'b0, q[lane]});
				end
		end
	end
	assign in_ready = ((state == 2'd0) && !rst) && !abort_i;
	assign out_valid = ((state == 2'd2) && !rst) && !abort_i;
	function automatic [19:0] sv2v_cast_20;
		input reg [19:0] inp;
		sv2v_cast_20 = inp;
	endfunction
	always_ff @(posedge clk)
		if (rst || abort_i) begin
			state <= 2'd0;
			coefficients <= 0;
			chroma <= 0;
			scale_code <= 0;
			group_index <= 0;
			out_id <= 0;
			out_error <= 0;
			out_dequantized <= 0;
		end
		else
			case (state)
				2'd0:
					if (in_valid && in_ready) begin
						coefficients <= in_coefficients;
						chroma <= in_chroma;
						scale_code <= in_scale_code;
						out_id <= in_id;
						out_error <= input_bad;
						group_index <= 0;
						if (input_bad || (in_coefficients == 0)) begin
							out_dequantized <= 0;
							state <= 2'd2;
						end
						else
							state <= 2'd1;
					end
				2'd1: begin
					begin : sv2v_autoblock_3
						integer lane;
						for (lane = 0; lane < 8; lane = lane + 1)
							out_dequantized[((sv2v_cast_32_signed(group_index) * 8) + lane) * 20+:20] <= sv2v_cast_20(products[lane]);
					end
					if (group_index == 7)
						state <= 2'd2;
					else
						group_index <= group_index + 1;
				end
				2'd2:
					if (out_ready && out_valid)
						state <= 2'd0;
				default: state <= 2'd0;
			endcase
endmodule
module cu66_idct8x8 (
	clk,
	rst,
	abort_frame,
	in_valid,
	in_ready,
	in_id,
	in_tile,
	out_valid,
	out_ready,
	out_id,
	out_tile,
	out_error,
	active_cycles
);
	input wire clk;
	input wire rst;
	input wire abort_frame;
	input wire in_valid;
	output wire in_ready;
	input wire [31:0] in_id;
	input wire [1279:0] in_tile;
	output wire out_valid;
	input wire out_ready;
	output reg [31:0] out_id;
	output reg [1535:0] out_tile;
	output reg out_error;
	output reg [31:0] active_cycles;
	reg [3:0] state;
	reg [1279:0] source_tile;
	reg [1:0] group_index;
	reg [2:0] k;
	reg signed [23:0] intermediate [0:63];
	reg signed [23:0] dc_middle;
	reg signed [23:0] samples [0:7];
	reg signed [37:0] products [0:7];
	reg signed [39:0] even_sum [0:7];
	reg signed [39:0] odd_sum [0:7];
	reg signed [39:0] next_even [0:7];
	reg signed [39:0] next_odd [0:7];
	reg input_bad;
	integer lane;
	integer index;
	function automatic signed [13:0] basis;
		input reg [2:0] fk;
		input reg [1:0] fp;
		case ({fk, fp})
			5'd0, 5'd1, 5'd2, 5'd3: basis = 14'sd5793;
			5'd4: basis = 14'sd8035;
			5'd5: basis = 14'sd6811;
			5'd6: basis = 14'sd4551;
			5'd7: basis = 14'sd1598;
			5'd8: basis = 14'sd7568;
			5'd9: basis = 14'sd3135;
			5'd10: basis = -14'sd3135;
			5'd11: basis = -14'sd7568;
			5'd12: basis = 14'sd6811;
			5'd13: basis = -14'sd1598;
			5'd14: basis = -14'sd8035;
			5'd15: basis = -14'sd4551;
			5'd16: basis = 14'sd5793;
			5'd17: basis = -14'sd5793;
			5'd18: basis = -14'sd5793;
			5'd19: basis = 14'sd5793;
			5'd20: basis = 14'sd4551;
			5'd21: basis = -14'sd8035;
			5'd22: basis = 14'sd1598;
			5'd23: basis = 14'sd6811;
			5'd24: basis = 14'sd3135;
			5'd25: basis = -14'sd7568;
			5'd26: basis = 14'sd7568;
			5'd27: basis = -14'sd3135;
			5'd28: basis = 14'sd1598;
			5'd29: basis = -14'sd4551;
			5'd30: basis = 14'sd6811;
			5'd31: basis = -14'sd8035;
			default: basis = 1'sb0;
		endcase
	endfunction
	function automatic signed [23:0] sv2v_cast_24_signed;
		input reg signed [23:0] inp;
		sv2v_cast_24_signed = inp;
	endfunction
	function automatic signed [23:0] rounded;
		input reg signed [39:0] a;
		rounded = sv2v_cast_24_signed((a + 40'sd8192) >>> 14);
	endfunction
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	always_comb begin
		input_bad = 1'b0;
		begin : sv2v_autoblock_1
			integer n;
			for (n = 0; n < 64; n = n + 1)
				if (($signed(in_tile[n * 20+:20]) > 20'sd522240) || ($signed(in_tile[n * 20+:20]) < -20'sd522240))
					input_bad = 1'b1;
		end
		begin : sv2v_autoblock_2
			integer l;
			for (l = 0; l < 8; l = l + 1)
				begin
					samples[l] = 1'sb0;
					if (state == 4'd1)
						samples[l] = {{4 {source_tile[(((((sv2v_cast_32_signed(group_index) * 2) + (l / 4)) * 8) + sv2v_cast_32_signed(k)) * 20) + 19]}}, source_tile[((((sv2v_cast_32_signed(group_index) * 2) + (l / 4)) * 8) + sv2v_cast_32_signed(k)) * 20+:20]};
					else if (state == 4'd3)
						samples[l] = intermediate[((sv2v_cast_32_signed(k) * 8) + (sv2v_cast_32_signed(group_index) * 2)) + (l / 4)];
					else if ((state == 4'd5) && (l == 0))
						samples[l] = {{4 {source_tile[19]}}, source_tile[19:0]};
					else if ((state == 4'd7) && (l == 0))
						samples[l] = dc_middle;
					next_even[l] = even_sum[l];
					next_odd[l] = odd_sum[l];
					if (k[0])
						next_odd[l] = odd_sum[l] + {{2 {products[l][37]}}, products[l]};
					else
						next_even[l] = even_sum[l] + {{2 {products[l][37]}}, products[l]};
				end
		end
	end
	assign in_ready = ((state == 4'd0) && !abort_frame) && !rst;
	assign out_valid = ((state == 4'd9) && !abort_frame) && !rst;
	function automatic signed [1:0] sv2v_cast_2_signed;
		input reg signed [1:0] inp;
		sv2v_cast_2_signed = inp;
	endfunction
	always_ff @(posedge clk)
		if (rst || abort_frame) begin
			state <= 4'd0;
			source_tile <= 1'sb0;
			out_tile <= 1'sb0;
			out_error <= 1'b0;
			out_id <= 1'sb0;
			group_index <= 1'sb0;
			k <= 1'sb0;
			dc_middle <= 1'sb0;
			active_cycles <= 1'sb0;
			for (lane = 0; lane < 8; lane = lane + 1)
				begin
					products[lane] <= 1'sb0;
					even_sum[lane] <= 1'sb0;
					odd_sum[lane] <= 1'sb0;
				end
		end
		else begin
			if ((state != 4'd0) && (state != 4'd9))
				active_cycles <= active_cycles + 1;
			case (state)
				4'd0:
					if (in_valid && in_ready) begin
						source_tile <= in_tile;
						out_id <= in_id;
						out_error <= input_bad;
						active_cycles <= 0;
						group_index <= 0;
						k <= 0;
						for (lane = 0; lane < 8; lane = lane + 1)
							begin
								even_sum[lane] <= 0;
								odd_sum[lane] <= 0;
							end
						if (input_bad || (in_tile == 0)) begin
							out_tile <= 0;
							state <= 4'd9;
						end
						else if (in_tile[1279:20] == 0)
							state <= 4'd5;
						else
							state <= 4'd1;
					end
				4'd1, 4'd3, 4'd5, 4'd7: begin
					for (lane = 0; lane < 8; lane = lane + 1)
						products[lane] <= $signed(samples[lane]) * $signed(basis(k, sv2v_cast_2_signed(lane % 4)));
					case (state)
						4'd1: state <= 4'd2;
						4'd3: state <= 4'd4;
						4'd5: state <= 4'd6;
						default: state <= 4'd8;
					endcase
				end
				4'd6: begin
					dc_middle <= rounded({{2 {products[0][37]}}, products[0]});
					state <= 4'd7;
				end
				4'd8: begin
					for (index = 0; index < 64; index = index + 1)
						out_tile[index * 24+:24] <= rounded({{2 {products[0][37]}}, products[0]});
					state <= 4'd9;
				end
				4'd2, 4'd4:
					if (k == 7) begin
						for (lane = 0; lane < 8; lane = lane + 1)
							begin
								if (state == 4'd2) begin
									intermediate[(((sv2v_cast_32_signed(group_index) * 2) + (lane / 4)) * 8) + (lane % 4)] <= rounded(next_even[lane] + next_odd[lane]);
									intermediate[((((sv2v_cast_32_signed(group_index) * 2) + (lane / 4)) * 8) + 7) - (lane % 4)] <= rounded(next_even[lane] - next_odd[lane]);
								end
								else begin
									out_tile[((((lane % 4) * 8) + (sv2v_cast_32_signed(group_index) * 2)) + (lane / 4)) * 24+:24] <= rounded(next_even[lane] + next_odd[lane]);
									out_tile[((((7 - (lane % 4)) * 8) + (sv2v_cast_32_signed(group_index) * 2)) + (lane / 4)) * 24+:24] <= rounded(next_even[lane] - next_odd[lane]);
								end
								even_sum[lane] <= 0;
								odd_sum[lane] <= 0;
							end
						k <= 0;
						if (group_index == 3) begin
							group_index <= 0;
							state <= (state == 4'd2 ? 4'd3 : 4'd9);
						end
						else begin
							group_index <= group_index + 1;
							state <= (state == 4'd2 ? 4'd1 : 4'd3);
						end
					end
					else begin
						for (lane = 0; lane < 8; lane = lane + 1)
							begin
								even_sum[lane] <= next_even[lane];
								odd_sum[lane] <= next_odd[lane];
							end
						k <= k + 1;
						state <= (state == 4'd2 ? 4'd1 : 4'd3);
					end
				4'd9:
					if (out_ready && out_valid)
						state <= 4'd0;
				default: state <= 4'd0;
			endcase
		end
endmodule
module cu66_reconstruct_tile (
	clk,
	rst,
	abort_i,
	in_valid,
	in_ready,
	in_id,
	in_key,
	in_hidden,
	in_residual,
	ref_valid,
	ref_ready,
	ref_tile_id,
	ref_pixels,
	out_valid,
	out_ready,
	out_id,
	out_pixels,
	out_error
);
	input wire clk;
	input wire rst;
	input wire abort_i;
	input wire in_valid;
	output reg in_ready;
	input wire [31:0] in_id;
	input wire in_key;
	input wire in_hidden;
	input wire [1535:0] in_residual;
	input wire ref_valid;
	output reg ref_ready;
	input wire [31:0] ref_tile_id;
	input wire [511:0] ref_pixels;
	output reg out_valid;
	input wire out_ready;
	output reg [31:0] out_id;
	output reg [511:0] out_pixels;
	output reg out_error;
	reg slot_ready;
	reg signed [24:0] combined [0:63];
	always_comb begin
		slot_ready = !out_valid || out_ready;
		in_ready = ((!rst && !abort_i) && slot_ready) && ((in_key || in_hidden) || ref_valid);
		ref_ready = ((((!rst && !abort_i) && slot_ready) && in_valid) && !in_key) && !in_hidden;
		begin : sv2v_autoblock_1
			integer i;
			for (i = 0; i < 64; i = i + 1)
				combined[i] = $signed({in_residual[(i * 24) + 23], in_residual[i * 24+:24]}) + (in_key ? 25'sd128 : $signed({17'd0, ref_pixels[i * 8+:8]}));
		end
	end
	always_ff @(posedge clk)
		if (rst || abort_i) begin
			out_valid <= 0;
			out_id <= 0;
			out_pixels <= 0;
			out_error <= 0;
		end
		else if (slot_ready) begin
			out_valid <= in_valid && ((in_key || in_hidden) || ref_valid);
			if (in_valid && ((in_key || in_hidden) || ref_valid)) begin
				out_id <= in_id;
				out_error <= (!in_key && !in_hidden) && (ref_tile_id != in_id);
				begin : sv2v_autoblock_2
					integer i;
					for (i = 0; i < 64; i = i + 1)
						if (in_hidden)
							out_pixels[i * 8+:8] <= 8'd128;
						else if (combined[i] < 0)
							out_pixels[i * 8+:8] <= 0;
						else if (combined[i] > 255)
							out_pixels[i * 8+:8] <= 8'd255;
						else
							out_pixels[i * 8+:8] <= combined[i][7:0];
				end
			end
		end
endmodule
module cs88_coefficients_v91k (
	clk,
	reset,
	start,
	abort_packet,
	reconstruct_lookup_req,
	reconstruct_lookup_tile,
	reconstruct_lookup_cell,
	reconstruct_lookup_ready,
	reconstruct_lookup_rsp,
	reconstruct_lookup_mode,
	reconstruct_lookup_scale,
	admitted_ready,
	admitted_key,
	admitted_fid,
	admitted_generation,
	start_ready,
	cache_valid,
	cache_last,
	cache_ready,
	cache_complete,
	cache_data,
	cache_ref_fid,
	cache_ref_generation,
	cache_error,
	accepted_ref_valid,
	accepted_qcache_valid,
	accepted_ref_fid,
	accepted_ref_generation,
	out_plane,
	out_tile,
	out_qcell,
	out_qscale,
	frame_state,
	frame_fid,
	core_starts,
	refill_bytes,
	blocked_starts,
	current_child_epoch,
	admission_reads,
	replay_reads,
	admission_error,
	frame_read_req,
	frame_read_rsp,
	frame_read_addr,
	frame_rsp_addr,
	frame_rsp_epoch,
	frame_read_data,
	queue_count,
	queue_max_count,
	queue_max_owned,
	queue_pending,
	queue_active,
	queue_push,
	queue_pop,
	queue_stall,
	queue_requests,
	queue_responses,
	queue_pops,
	queue_stalls,
	queue_cancel_queued,
	queue_cancel_pending,
	packet_bytes,
	epoch,
	serial_clear,
	write_overlap,
	read_prefetch,
	tile_overlap,
	in_valid,
	in_ready,
	in_data,
	in_last,
	out_valid,
	out_ready,
	out_block,
	out_index,
	out_value,
	out_epoch,
	done,
	error,
	busy,
	draining,
	scratch_sealed,
	used_bytes,
	count_cycles,
	count_input_bytes,
	count_dense,
	count_reads,
	count_writes,
	count_dense_stall,
	mem_req_valid,
	mem_req_ready,
	mem_req_write,
	mem_req_addr,
	mem_req_data,
	mem_req_epoch,
	mem_rsp_valid,
	mem_rsp_ready,
	mem_rsp_data,
	mem_rsp_epoch,
	mem_rsp_error,
	packet_state,
	metadata_wait,
	dbg_running,
	dbg_allocation,
	dbg_seal_sent,
	dbg_packet_done,
	dbg_coef_valid,
	dbg_coef_ready,
	dbg_coef_band,
	dbg_coef_block,
	dbg_coef_index,
	dbg_coef_value,
	dbg_coef_epoch,
	dbg_meta_valid,
	dbg_meta_ready,
	dbg_meta_raw,
	dbg_band_end_valid,
	dbg_band_end_ready,
	dbg_band_end_band,
	dbg_seal_valid,
	dbg_seal_ready,
	dbg_scratch_state,
	dbg_scratch_return_state,
	dbg_scratch_outstanding,
	dbg_prefetch_offer,
	dbg_prefetch_launch,
	dbg_prefetch_use,
	dbg_tile_mode,
	dbg_tile_preparing,
	dbg_prepare_bank,
	dbg_emit_bank,
	dbg_bank_ready,
	dbg_bank_owned,
	dbg_emitter_state,
	dbg_prepare_block,
	dbg_bank_block,
	dbg_bank_epoch,
	dbg_tile_prepare_start,
	dbg_tile_publish,
	dbg_tile_release,
	count_emitter_state,
	count_tile_starts,
	count_tile_publishes,
	count_tile_releases,
	count_prepare_output_overlap,
	count_prepare_output_hold,
	count_tile_read_output_overlap,
	count_tile_bank_wait,
	count_both_ready_wait,
	count_tile_prep_done_wait,
	count_output_valid,
	count_publish_release_same_edge,
	max_tile_owned,
	max_tile_ready,
	count_prefetch_offers,
	count_prefetch_accepts,
	count_prefetch_acks,
	count_prefetch_uses,
	count_dense_during_read_pending,
	count_prefetch_drain_wait,
	max_prefetch_offer,
	dbg_write_slot_valid,
	dbg_assembler_full,
	dbg_write_enqueue,
	count_write_enqueues,
	count_write_accepts,
	count_write_acks,
	count_full_wait,
	count_packing_during_write_pending,
	max_write_slot,
	max_owned_lines,
	dbg_scratch_phase,
	dbg_scratch_assembly_bytes,
	dbg_scratch_cache_valid,
	dbg_scratch_head_valid,
	count_packet_state,
	count_scratch_state,
	count_coef_stall,
	count_metadata_wait,
	count_band_end_stall,
	count_mem_req_stall,
	count_mem_pending,
	count_input_starved,
	ts_first_input,
	ts_last_input,
	ts_metadata_accept,
	ts_last_sparse_coef,
	ts_packet_done_observed,
	ts_seal_accepted,
	ts_scratch_sealed_observed,
	ts_first_dense,
	ts_last_dense,
	ts_integrated_done,
	ts_first_coef_band,
	ts_last_coef_band,
	ts_band_end,
	max_assembly_bytes,
	max_cache_valid,
	max_head_valid,
	max_outstanding,
	stage_read_req,
	stage_read_rsp,
	stage_write,
	stage_pending,
	stage_context_active,
	stage_cancel,
	stage_word_valid,
	stage_word_ready,
	stage_read_addr,
	stage_rsp_addr,
	stage_write_addr,
	stage_req_epoch,
	stage_rsp_epoch,
	stage_read_data,
	stage_write_data,
	stage_buffer_bytes,
	stage_buffer_highwater,
	stage_purpose,
	count_stage_reads,
	count_stage_responses,
	count_stage_writes,
	count_stage_fetch_wait,
	count_stage_word_hold
);
	parameter integer REFILL_OVERLAP = 1;
	input wire clk;
	input wire reset;
	input wire start;
	input wire abort_packet;
	input wire reconstruct_lookup_req;
	input wire [12:0] reconstruct_lookup_tile;
	input wire [10:0] reconstruct_lookup_cell;
	output wire reconstruct_lookup_ready;
	output wire reconstruct_lookup_rsp;
	output wire [1:0] reconstruct_lookup_mode;
	output wire [1:0] reconstruct_lookup_scale;
	output wire admitted_ready;
	output wire admitted_key;
	output wire [31:0] admitted_fid;
	output wire [63:0] admitted_generation;
	output wire start_ready;
	input wire cache_valid;
	input wire cache_last;
	output wire cache_ready;
	output reg cache_complete;
	input wire [1:0] cache_data;
	input wire [31:0] cache_ref_fid;
	input wire [63:0] cache_ref_generation;
	output reg [7:0] cache_error;
	input wire accepted_ref_valid;
	input wire accepted_qcache_valid;
	input wire [31:0] accepted_ref_fid;
	input wire [63:0] accepted_ref_generation;
	output wire [1:0] out_plane;
	output wire [12:0] out_tile;
	output wire [10:0] out_qcell;
	output wire [1:0] out_qscale;
	output wire [7:0] frame_state;
	output wire [31:0] frame_fid;
	output reg [31:0] core_starts;
	output reg [31:0] refill_bytes;
	output reg [31:0] blocked_starts;
	output reg [31:0] current_child_epoch;
	output wire [63:0] admission_reads;
	output reg [31:0] replay_reads;
	output wire [7:0] admission_error;
	output wire frame_read_req;
	output wire frame_read_rsp;
	output wire [31:0] frame_read_addr;
	output wire [31:0] frame_rsp_addr;
	output wire [31:0] frame_rsp_epoch;
	output wire [7:0] frame_read_data;
	output wire [1:0] queue_count;
	output wire [1:0] queue_max_count;
	output wire [1:0] queue_max_owned;
	output wire queue_pending;
	output wire queue_active;
	output wire queue_push;
	output wire queue_pop;
	output wire queue_stall;
	output wire [31:0] queue_requests;
	output wire [31:0] queue_responses;
	output wire [31:0] queue_pops;
	output wire [31:0] queue_stalls;
	output wire [31:0] queue_cancel_queued;
	output wire [31:0] queue_cancel_pending;
	input wire [31:0] packet_bytes;
	input wire [31:0] epoch;
	input wire serial_clear;
	input wire write_overlap;
	input wire read_prefetch;
	input wire tile_overlap;
	input wire in_valid;
	output wire in_ready;
	input wire [7:0] in_data;
	input wire in_last;
	output wire out_valid;
	input wire out_ready;
	output wire [15:0] out_block;
	output wire [5:0] out_index;
	output wire signed [15:0] out_value;
	output wire [31:0] out_epoch;
	output reg done;
	output reg [7:0] error;
	output wire busy;
	output wire draining;
	output wire scratch_sealed;
	output wire [18:0] used_bytes;
	output wire [63:0] count_cycles;
	output wire [63:0] count_input_bytes;
	output wire [63:0] count_dense;
	output wire [63:0] count_reads;
	output wire [63:0] count_writes;
	output wire [63:0] count_dense_stall;
	output wire mem_req_valid;
	input wire mem_req_ready;
	output wire mem_req_write;
	output wire [17:0] mem_req_addr;
	output wire [127:0] mem_req_data;
	output wire [31:0] mem_req_epoch;
	input wire mem_rsp_valid;
	output wire mem_rsp_ready;
	input wire [127:0] mem_rsp_data;
	input wire [31:0] mem_rsp_epoch;
	input wire mem_rsp_error;
	output wire [3:0] packet_state;
	output wire metadata_wait;
	output wire dbg_running;
	output wire dbg_allocation;
	output wire dbg_seal_sent;
	output wire dbg_packet_done;
	output wire dbg_coef_valid;
	output wire dbg_coef_ready;
	output wire [1:0] dbg_coef_band;
	output wire [15:0] dbg_coef_block;
	output wire [5:0] dbg_coef_index;
	output wire signed [15:0] dbg_coef_value;
	output wire [31:0] dbg_coef_epoch;
	output wire dbg_meta_valid;
	output wire dbg_meta_ready;
	output wire dbg_meta_raw;
	output wire dbg_band_end_valid;
	output wire dbg_band_end_ready;
	output wire [1:0] dbg_band_end_band;
	output wire dbg_seal_valid;
	output wire dbg_seal_ready;
	output wire [4:0] dbg_scratch_state;
	output wire [4:0] dbg_scratch_return_state;
	output wire dbg_scratch_outstanding;
	output wire dbg_prefetch_offer;
	output wire dbg_prefetch_launch;
	output wire dbg_prefetch_use;
	output wire dbg_tile_mode;
	output wire dbg_tile_preparing;
	output wire dbg_prepare_bank;
	output wire dbg_emit_bank;
	output wire [1:0] dbg_bank_ready;
	output wire [1:0] dbg_bank_owned;
	output wire [1:0] dbg_emitter_state;
	output wire [15:0] dbg_prepare_block;
	output wire [31:0] dbg_bank_block;
	output wire [63:0] dbg_bank_epoch;
	output wire dbg_tile_prepare_start;
	output wire dbg_tile_publish;
	output wire dbg_tile_release;
	output wire [255:0] count_emitter_state;
	output wire [63:0] count_tile_starts;
	output wire [63:0] count_tile_publishes;
	output wire [63:0] count_tile_releases;
	output wire [63:0] count_prepare_output_overlap;
	output wire [63:0] count_prepare_output_hold;
	output wire [63:0] count_tile_read_output_overlap;
	output wire [63:0] count_tile_bank_wait;
	output wire [63:0] count_both_ready_wait;
	output wire [63:0] count_tile_prep_done_wait;
	output wire [63:0] count_output_valid;
	output wire [63:0] count_publish_release_same_edge;
	output wire [1:0] max_tile_owned;
	output wire [1:0] max_tile_ready;
	output wire [63:0] count_prefetch_offers;
	output wire [63:0] count_prefetch_accepts;
	output wire [63:0] count_prefetch_acks;
	output wire [63:0] count_prefetch_uses;
	output wire [63:0] count_dense_during_read_pending;
	output wire [63:0] count_prefetch_drain_wait;
	output wire max_prefetch_offer;
	output wire dbg_write_slot_valid;
	output wire dbg_assembler_full;
	output wire dbg_write_enqueue;
	output wire [63:0] count_write_enqueues;
	output wire [63:0] count_write_accepts;
	output wire [63:0] count_write_acks;
	output wire [63:0] count_full_wait;
	output wire [63:0] count_packing_during_write_pending;
	output wire max_write_slot;
	output wire [1:0] max_owned_lines;
	output wire [2:0] dbg_scratch_phase;
	output wire [4:0] dbg_scratch_assembly_bytes;
	output wire [3:0] dbg_scratch_cache_valid;
	output wire [2:0] dbg_scratch_head_valid;
	output wire [1023:0] count_packet_state;
	output wire [2047:0] count_scratch_state;
	output wire [63:0] count_coef_stall;
	output wire [63:0] count_metadata_wait;
	output wire [63:0] count_band_end_stall;
	output wire [63:0] count_mem_req_stall;
	output wire [63:0] count_mem_pending;
	output wire [63:0] count_input_starved;
	output wire [63:0] ts_first_input;
	output wire [63:0] ts_last_input;
	output wire [63:0] ts_metadata_accept;
	output wire [63:0] ts_last_sparse_coef;
	output wire [63:0] ts_packet_done_observed;
	output wire [63:0] ts_seal_accepted;
	output wire [63:0] ts_scratch_sealed_observed;
	output wire [63:0] ts_first_dense;
	output wire [63:0] ts_last_dense;
	output wire [63:0] ts_integrated_done;
	output wire [255:0] ts_first_coef_band;
	output wire [255:0] ts_last_coef_band;
	output wire [255:0] ts_band_end;
	output wire [4:0] max_assembly_bytes;
	output wire [2:0] max_cache_valid;
	output wire [2:0] max_head_valid;
	output wire max_outstanding;
	output wire stage_read_req;
	output wire stage_read_rsp;
	output wire stage_write;
	output wire stage_pending;
	output wire stage_context_active;
	output wire stage_cancel;
	output wire stage_word_valid;
	output wire stage_word_ready;
	output wire [31:0] stage_read_addr;
	output wire [31:0] stage_rsp_addr;
	output wire [31:0] stage_write_addr;
	output wire [31:0] stage_req_epoch;
	output wire [31:0] stage_rsp_epoch;
	output wire [7:0] stage_read_data;
	output wire [7:0] stage_write_data;
	output wire [5:0] stage_buffer_bytes;
	output wire [5:0] stage_buffer_highwater;
	output wire [2:0] stage_purpose;
	output wire [63:0] count_stage_reads;
	output wire [63:0] count_stage_responses;
	output wire [63:0] count_stage_writes;
	output wire [63:0] count_stage_fetch_wait;
	output wire [63:0] count_stage_word_hold;
	localparam [7:0] IDLE = 0;
	localparam [7:0] ADMIT = 1;
	localparam [7:0] CHECK_ENTROPY = 2;
	localparam [7:0] PREP_PLANE = 3;
	localparam [7:0] ALLOCATE = 4;
	localparam [7:0] CORE_START = 5;
	localparam [7:0] REFILL_REQ = 6;
	localparam [7:0] REFILL_WAIT = 7;
	localparam [7:0] REFILL_SEND = 8;
	localparam [7:0] MAP_REQ = 9;
	localparam [7:0] MAP_WAIT = 10;
	localparam [7:0] DISPATCH = 11;
	localparam [7:0] WAIT_DONE = 12;
	localparam [7:0] NEXT_PLANE = 13;
	localparam [7:0] FINISHED = 14;
	localparam [7:0] FAILED = 15;
	localparam [7:0] REFILL_STREAM = 16;
	reg [7:0] state;
	wire frame_running;
	wire accepted_start;
	reg [31:0] frame_epoch;
	reg [31:0] latched_size;
	reg [31:0] last_frame_epoch = 0;
	reg [31:0] child_nonce = 0;
	reg [1:0] plane;
	reg [12:0] tile_cursor;
	reg [12:0] mapped_tile;
	reg [10:0] mapped_cell;
	reg [1:0] mapped_scale;
	reg [15:0] expected_block;
	reg [31:0] refill_cursor;
	reg [31:0] selected_offset;
	reg [31:0] selected_length;
	reg [16:0] selected_blocks;
	reg [7:0] refill_data;
	wire refill_valid;
	wire refill_last;
	wire child_in_ready;
	wire [7:0] child_input_data;
	wire queue_req_valid;
	wire queue_done;
	wire [7:0] queue_error;
	wire [7:0] queue_data;
	wire queue_valid;
	wire queue_last;
	wire [31:0] queue_req_addr;
	wire [31:0] queue_req_epoch;
	wire child_start;
	wire child_abort;
	wire child_out_valid;
	wire child_out_ready;
	wire child_done;
	wire [7:0] child_error;
	wire child_busy;
	wire child_draining;
	reg child_owned;
	wire [31:0] child_out_epoch;
	wire local_abort;
	reg [10:0] cache_count;
	reg [31:0] cached_fid;
	reg [63:0] cached_generation;
	wire snapshot_cache_eligible;
	wire [31:0] unused_fork_epoch;
	wire [31:0] fork_fid;
	wire [31:0] unused_fork_refid;
	wire [63:0] unused_fork_generation;
	wire unused_fork_key;
	wire coefficient_lookup_req;
	reg lookup_owner_reconstruct;
	wire physical_lookup_rsp;
	wire [1:0] physical_lookup_mode;
	wire [1:0] physical_lookup_scale;
	wire [31:0] unused_fork_mode_bytes;
	wire [31:0] unused_fork_qmap_bytes;
	wire [31:0] unused_fork_hud_bytes;
	wire [31:0] unused_fork_data_bytes;
	wire [95:0] fork_blocks;
	wire [95:0] fork_offsets;
	wire [95:0] fork_lengths;
	wire [5:0] fork_entropy;
	wire fork_in_ready;
	wire unused_fork_busy;
	wire fork_receipt;
	wire replay_ready;
	wire replay_rsp;
	wire [7:0] replay_data;
	wire [31:0] replay_rsp_addr;
	wire [31:0] replay_rsp_epoch;
	wire lookup_rsp;
	wire [1:0] lookup_mode;
	wire [1:0] lookup_scale;
	wire [12:0] lookup_tile;
	wire [10:0] lookup_cell;
	wire [63:0] fork_count_reads;
	wire unused_fork_read_req;
	wire unused_fork_read_rsp;
	wire unused_fork_write;
	wire unused_fork_pending;
	wire unused_fork_cancel;
	wire [31:0] unused_fork_read_addr;
	wire [31:0] unused_fork_rsp_addr;
	wire [31:0] unused_fork_req_epoch;
	wire [31:0] unused_fork_rsp_epoch;
	wire [31:0] unused_fork_required;
	wire [7:0] unused_fork_data;
	wire [7:0] unused_fork_state;
	wire [63:0] unused_fork_cycles;
	wire [63:0] unused_fork_inputs;
	wire [63:0] unused_fork_responses;
	wire [63:0] unused_fork_wait;
	function automatic [12:0] tiles;
		input reg [1:0] p;
		tiles = (p == 0 ? 13'd5400 : 13'd1350);
	endfunction
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [10:0] sv2v_cast_11;
		input reg [10:0] inp;
		sv2v_cast_11 = inp;
	endfunction
	function automatic [10:0] quant_cell;
		input reg [1:0] p;
		input reg [12:0] t;
		quant_cell = (p == 0 ? sv2v_cast_11((((sv2v_cast_32(t) / 90) / 2) * 45) + ((sv2v_cast_32(t) % 90) / 2)) : sv2v_cast_11(t));
	endfunction
	assign frame_running = ((state != IDLE) && (state != FINISHED)) && (state != FAILED);
	assign busy = (frame_running || child_busy) || (cache_count != 0);
	assign draining = child_draining;
	assign start_ready = ((((!frame_running && !child_busy) && !child_draining) && (cache_count == 0)) && !reset) && !abort_packet;
	assign accepted_start = start && start_ready;
	assign cache_ready = ((((!frame_running && !child_busy) && !child_draining) && !reset) && !abort_packet) && !start;
	assign snapshot_cache_eligible = ((accepted_qcache_valid && cache_complete) && (cached_fid == accepted_ref_fid)) && (cached_generation == accepted_ref_generation);
	assign in_ready = (((state == ADMIT) && fork_in_ready) && !reset) && !abort_packet;
	assign local_abort = abort_packet || (state == FAILED);
	assign child_start = ((state == CORE_START) && !reset) && !abort_packet;
	assign child_abort = local_abort;
	assign refill_valid = (REFILL_OVERLAP != 0 ? queue_valid : ((state == REFILL_SEND) && !reset) && !abort_packet);
	assign refill_last = (REFILL_OVERLAP != 0 ? queue_last : (refill_cursor + 1) == selected_length);
	assign child_input_data = (REFILL_OVERLAP != 0 ? queue_data : refill_data);
	assign child_out_ready = (((((state == DISPATCH) && out_ready) && (child_out_epoch == current_child_epoch)) && (out_block == expected_block)) && !reset) && !abort_packet;
	assign out_valid = (((((state == DISPATCH) && child_out_valid) && (child_out_epoch == current_child_epoch)) && (out_block == expected_block)) && !reset) && !abort_packet;
	assign out_epoch = frame_epoch;
	assign out_plane = plane;
	assign out_tile = mapped_tile;
	assign out_qcell = mapped_cell;
	assign out_qscale = mapped_scale;
	assign frame_state = state;
	assign frame_fid = fork_fid;
	function automatic [12:0] sv2v_cast_13;
		input reg [12:0] inp;
		sv2v_cast_13 = inp;
	endfunction
	assign lookup_tile = sv2v_cast_13((plane == 0 ? 0 : (plane == 1 ? 5400 : 6750)) + sv2v_cast_32(tile_cursor));
	assign lookup_cell = quant_cell(plane, tile_cursor);
	assign frame_read_req = (REFILL_OVERLAP != 0 ? queue_req_valid && replay_ready : (((state == REFILL_REQ) && replay_ready) && !reset) && !abort_packet);
	assign frame_read_rsp = replay_rsp;
	assign frame_read_addr = (REFILL_OVERLAP != 0 ? queue_req_addr : selected_offset + refill_cursor);
	assign frame_rsp_addr = replay_rsp_addr;
	assign frame_rsp_epoch = replay_rsp_epoch;
	assign frame_read_data = replay_data;
	assign admission_reads = fork_count_reads;
	assign coefficient_lookup_req = (((state == MAP_REQ) && (tile_cursor < tiles(plane))) && !reset) && !abort_packet;
	assign reconstruct_lookup_ready = ((admitted_ready && !coefficient_lookup_req) && !reset) && !abort_packet;
	assign admitted_ready = (state >= PREP_PLANE) && (state != FAILED);
	assign admitted_key = unused_fork_key;
	assign admitted_fid = fork_fid;
	assign admitted_generation = unused_fork_generation;
	assign lookup_rsp = physical_lookup_rsp && !lookup_owner_reconstruct;
	assign lookup_mode = physical_lookup_mode;
	assign lookup_scale = physical_lookup_scale;
	assign reconstruct_lookup_rsp = ((physical_lookup_rsp && lookup_owner_reconstruct) && !reset) && !abort_packet;
	assign reconstruct_lookup_mode = physical_lookup_mode;
	assign reconstruct_lookup_scale = physical_lookup_scale;
	always_ff @(posedge clk)
		if ((reset || abort_packet) || accepted_start)
			lookup_owner_reconstruct <= 0;
		else if (coefficient_lookup_req || (reconstruct_lookup_req && reconstruct_lookup_ready))
			lookup_owner_reconstruct <= !coefficient_lookup_req;
	cs88_admission_v91i2a admission(
		.clk(clk),
		.reset(reset),
		.start(accepted_start),
		.abort_packet(abort_packet),
		.cache_write((cache_valid && cache_ready) && (cache_data < 3)),
		.cache_index(cache_count),
		.cache_data(cache_data),
		.packet_bytes(packet_bytes),
		.epoch(epoch),
		.accepted_ref_valid(accepted_ref_valid),
		.accepted_qcache_valid(snapshot_cache_eligible),
		.accepted_ref_fid(accepted_ref_fid),
		.accepted_ref_generation(accepted_ref_generation),
		.in_valid(in_valid && (state == ADMIT)),
		.in_last(in_last),
		.in_data(in_data),
		.in_ready(fork_in_ready),
		.busy(unused_fork_busy),
		.receipt_valid(fork_receipt),
		.receipt_ready(state == ADMIT),
		.error(admission_error),
		.receipt_epoch(unused_fork_epoch),
		.fid(fork_fid),
		.refid(unused_fork_refid),
		.generation(unused_fork_generation),
		.key_frame(unused_fork_key),
		.mode_bytes(unused_fork_mode_bytes),
		.qmap_bytes(unused_fork_qmap_bytes),
		.hud_bytes(unused_fork_hud_bytes),
		.data_bytes(unused_fork_data_bytes),
		.plane_blocks(fork_blocks),
		.plane_offset(fork_offsets),
		.plane_length(fork_lengths),
		.plane_entropy(fork_entropy),
		.stage_read_req(unused_fork_read_req),
		.stage_read_rsp(unused_fork_read_rsp),
		.stage_write(unused_fork_write),
		.stage_pending(unused_fork_pending),
		.stage_cancel(unused_fork_cancel),
		.stage_read_addr(unused_fork_read_addr),
		.stage_rsp_addr(unused_fork_rsp_addr),
		.stage_req_epoch(unused_fork_req_epoch),
		.stage_rsp_epoch(unused_fork_rsp_epoch),
		.stage_read_data(unused_fork_data),
		.debug_state(unused_fork_state),
		.count_cycles(unused_fork_cycles),
		.count_inputs(unused_fork_inputs),
		.count_stage_reads(fork_count_reads),
		.count_stage_responses(unused_fork_responses),
		.count_receipt_wait(unused_fork_wait),
		.required_cells(unused_fork_required),
		.replay_req((REFILL_OVERLAP != 0 ? queue_req_valid : ((state == REFILL_REQ) && !reset) && !abort_packet)),
		.replay_addr(frame_read_addr),
		.replay_ready(replay_ready),
		.replay_rsp_valid(replay_rsp),
		.replay_data(replay_data),
		.replay_rsp_addr(replay_rsp_addr),
		.replay_rsp_epoch(replay_rsp_epoch),
		.lookup_req(coefficient_lookup_req || (reconstruct_lookup_req && reconstruct_lookup_ready)),
		.lookup_tile((coefficient_lookup_req ? lookup_tile : reconstruct_lookup_tile)),
		.lookup_cell((coefficient_lookup_req ? lookup_cell : reconstruct_lookup_cell)),
		.lookup_rsp_valid(physical_lookup_rsp),
		.lookup_mode(physical_lookup_mode),
		.lookup_scale(physical_lookup_scale)
	);
	assign queue_stall = ((REFILL_OVERLAP != 0) && queue_valid) && !child_in_ready;
	generate
		if (REFILL_OVERLAP != 0) begin : refill_overlap_enabled
			byte_refill_queue_v91i2b refill_queue(
				.clk(clk),
				.reset(reset),
				.cancel(abort_packet || local_abort),
				.start(child_start),
				.clear_stats(accepted_start),
				.start_offset(selected_offset),
				.start_length(selected_length),
				.start_epoch(frame_epoch),
				.req_valid(queue_req_valid),
				.req_ready(replay_ready),
				.req_addr(queue_req_addr),
				.req_epoch(queue_req_epoch),
				.rsp_valid(replay_rsp),
				.rsp_addr(replay_rsp_addr),
				.rsp_epoch(replay_rsp_epoch),
				.rsp_data(replay_data),
				.out_valid(queue_valid),
				.out_ready(child_in_ready),
				.out_data(queue_data),
				.out_last(queue_last),
				.done(queue_done),
				.error(queue_error),
				.active(queue_active),
				.fifo_count(queue_count),
				.pending(queue_pending),
				.push_event(queue_push),
				.pop_event(queue_pop),
				.count_requests(queue_requests),
				.count_responses(queue_responses),
				.count_pops(queue_pops),
				.count_stalls(queue_stalls),
				.count_cancel_queued(queue_cancel_queued),
				.count_cancel_pending(queue_cancel_pending),
				.max_count(queue_max_count),
				.max_owned(queue_max_owned)
			);
		end
		else begin : refill_overlap_disabled
			assign queue_req_valid = 0;
			assign queue_req_addr = 0;
			assign queue_req_epoch = 0;
			assign queue_done = 0;
			assign queue_error = 0;
			assign queue_data = 0;
			assign queue_valid = 0;
			assign queue_last = 0;
			assign queue_active = 0;
			assign queue_count = 0;
			assign queue_pending = 0;
			assign queue_push = 0;
			assign queue_pop = 0;
			assign queue_requests = 0;
			assign queue_responses = 0;
			assign queue_pops = 0;
			assign queue_stalls = 0;
			assign queue_cancel_queued = 0;
			assign queue_cancel_pending = 0;
			assign queue_max_count = 0;
			assign queue_max_owned = 0;
		end
	endgenerate
	always_ff @(posedge clk)
		if (reset || abort_packet) begin
			cache_count <= 0;
			cached_fid <= 0;
			cached_generation <= 0;
			cache_complete <= 0;
			cache_error <= 0;
		end
		else if (accepted_start)
			cache_complete <= 0;
		else if (cache_valid && cache_ready) begin
			if (cache_count == 0) begin
				cached_fid <= cache_ref_fid;
				cached_generation <= cache_ref_generation;
				cache_complete <= 0;
				cache_error <= 0;
			end
			if (cache_data == 3)
				cache_error <= 3;
			else if (cache_last != (cache_count == 1349))
				cache_error <= 1;
			if (cache_last || (cache_count == 1349)) begin
				cache_count <= 0;
				if (((cache_last && (cache_count == 1349)) && (cache_data < 3)) && ((cache_count == 0) || (cache_error == 0)))
					cache_complete <= 1;
			end
			else
				cache_count <= cache_count + 1;
		end
	function automatic [63:0] sv2v_cast_64;
		input reg [63:0] inp;
		sv2v_cast_64 = inp;
	endfunction
	function automatic [16:0] sv2v_cast_17;
		input reg [16:0] inp;
		sv2v_cast_17 = inp;
	endfunction
	always_ff @(posedge clk)
		if (reset || abort_packet) begin
			state <= IDLE;
			error <= 0;
			done <= 0;
			plane <= 0;
			tile_cursor <= 0;
			mapped_tile <= 0;
			mapped_cell <= 0;
			mapped_scale <= 0;
			expected_block <= 0;
			refill_cursor <= 0;
			selected_offset <= 0;
			selected_length <= 0;
			selected_blocks <= 0;
			frame_epoch <= 0;
			latched_size <= 0;
			current_child_epoch <= 0;
			refill_data <= 0;
			child_owned <= 0;
			core_starts <= 0;
			refill_bytes <= 0;
			blocked_starts <= 0;
			replay_reads <= 0;
		end
		else begin
			if (start && !start_ready)
				blocked_starts <= blocked_starts + 1;
			if (accepted_start) begin
				state <= ADMIT;
				error <= 0;
				done <= 0;
				frame_epoch <= epoch;
				latched_size <= packet_bytes;
				plane <= 0;
				tile_cursor <= 0;
				expected_block <= 0;
				child_owned <= 0;
				core_starts <= 0;
				refill_bytes <= 0;
				replay_reads <= 0;
				if ((epoch == 0) || (epoch <= last_frame_epoch)) begin
					state <= FAILED;
					error <= 65;
				end
				else
					last_frame_epoch <= epoch;
			end
			else begin
				if (frame_read_req)
					replay_reads <= replay_reads + 1;
				if (child_start) begin
					core_starts <= core_starts + 1;
					child_owned <= 1;
				end
				else if (child_done)
					child_owned <= 0;
				if (refill_valid && child_in_ready)
					refill_bytes <= refill_bytes + 1;
				if (((REFILL_OVERLAP != 0) && frame_running) && (queue_error != 0)) begin
					state <= FAILED;
					error <= 67;
					child_owned <= 0;
				end
				else if ((frame_running && child_owned) && (child_error != 0)) begin
					state <= FAILED;
					error <= 8'h80 | child_error;
					child_owned <= 0;
				end
				else
					case (state)
						ADMIT:
							if (admission_error != 0) begin
								state <= FAILED;
								error <= admission_error;
							end
							else if (fork_receipt)
								state <= CHECK_ENTROPY;
						CHECK_ENTROPY:
							if ((((fork_blocks[64+:32] != 0) && (fork_entropy[4+:2] != 2)) || ((fork_blocks[32+:32] != 0) && (fork_entropy[2+:2] != 2))) || ((fork_blocks[0+:32] != 0) && (fork_entropy[0+:2] != 2))) begin
								state <= FAILED;
								error <= 64;
							end
							else if (((({32'd0, child_nonce} + sv2v_cast_64(fork_blocks[64+:32] != 0)) + sv2v_cast_64(fork_blocks[32+:32] != 0)) + sv2v_cast_64(fork_blocks[0+:32] != 0)) > 64'h00000000ffffffff) begin
								state <= FAILED;
								error <= 66;
							end
							else begin
								plane <= 0;
								state <= PREP_PLANE;
							end
						PREP_PLANE:
							if (fork_blocks[(2 - plane) * 32+:32] == 0)
								state <= NEXT_PLANE;
							else begin
								selected_offset <= fork_offsets[(2 - plane) * 32+:32];
								selected_length <= fork_lengths[(2 - plane) * 32+:32];
								selected_blocks <= sv2v_cast_17(fork_blocks[(2 - plane) * 32+:32]);
								tile_cursor <= 0;
								expected_block <= 0;
								refill_cursor <= 0;
								state <= ALLOCATE;
							end
						ALLOCATE:
							if (child_busy || child_draining)
								;
							else if (child_nonce == 32'hffffffff) begin
								state <= FAILED;
								error <= 66;
							end
							else begin
								current_child_epoch <= child_nonce + 1;
								child_nonce <= child_nonce + 1;
								state <= CORE_START;
							end
						CORE_START: state <= (REFILL_OVERLAP != 0 ? REFILL_STREAM : REFILL_REQ);
						REFILL_REQ:
							if (replay_ready)
								state <= REFILL_WAIT;
						REFILL_WAIT:
							if (replay_rsp) begin
								if ((replay_rsp_addr != (selected_offset + refill_cursor)) || (replay_rsp_epoch != frame_epoch)) begin
									state <= FAILED;
									error <= 67;
								end
								else begin
									refill_data <= replay_data;
									state <= REFILL_SEND;
								end
							end
						REFILL_SEND:
							if (child_in_ready) begin
								if (refill_last)
									state <= MAP_REQ;
								else begin
									refill_cursor <= refill_cursor + 1;
									state <= REFILL_REQ;
								end
							end
						REFILL_STREAM:
							if (queue_done)
								state <= MAP_REQ;
						MAP_REQ:
							if (tile_cursor >= tiles(plane)) begin
								state <= FAILED;
								error <= 67;
							end
							else
								state <= MAP_WAIT;
						MAP_WAIT:
							if (lookup_rsp) begin
								if (lookup_mode == 2) begin
									mapped_tile <= tile_cursor;
									mapped_cell <= quant_cell(plane, tile_cursor);
									mapped_scale <= lookup_scale;
									state <= DISPATCH;
								end
								else begin
									tile_cursor <= tile_cursor + 1;
									state <= MAP_REQ;
								end
							end
						DISPATCH:
							if (child_out_valid && ((child_out_epoch != current_child_epoch) || (out_block != expected_block))) begin
								state <= FAILED;
								error <= 67;
							end
							else if ((out_valid && out_ready) && (out_index == 63)) begin
								expected_block <= expected_block + 1;
								if ((sv2v_cast_32(expected_block) + 1) == sv2v_cast_32(selected_blocks))
									state <= WAIT_DONE;
								else begin
									tile_cursor <= tile_cursor + 1;
									state <= MAP_REQ;
								end
							end
						WAIT_DONE:
							if ((child_done && !child_busy) && !child_draining)
								state <= NEXT_PLANE;
						NEXT_PLANE:
							if (plane == 2) begin
								done <= 1;
								state <= FINISHED;
							end
							else begin
								plane <= plane + 1;
								state <= PREP_PLANE;
							end
						default:
							;
					endcase
			end
		end
	br88_pipeline_v91h #(.SYNC_STAGING(1)) child(
		.clk(clk),
		.reset(reset),
		.start(child_start),
		.abort_packet(child_abort),
		.packet_bytes(selected_length),
		.epoch(current_child_epoch),
		.blocks(selected_blocks),
		.serial_clear(serial_clear),
		.write_overlap(write_overlap),
		.read_prefetch(read_prefetch),
		.tile_overlap(tile_overlap),
		.in_valid(refill_valid),
		.in_ready(child_in_ready),
		.in_data(child_input_data),
		.in_last(refill_last),
		.out_valid(child_out_valid),
		.out_ready(child_out_ready),
		.out_block(out_block),
		.out_index(out_index),
		.out_value(out_value),
		.out_epoch(child_out_epoch),
		.done(child_done),
		.error(child_error),
		.busy(child_busy),
		.draining(child_draining),
		.scratch_sealed(scratch_sealed),
		.used_bytes(used_bytes),
		.count_cycles(count_cycles),
		.count_input_bytes(count_input_bytes),
		.count_dense(count_dense),
		.count_reads(count_reads),
		.count_writes(count_writes),
		.count_dense_stall(count_dense_stall),
		.mem_req_valid(mem_req_valid),
		.mem_req_ready(mem_req_ready),
		.mem_req_write(mem_req_write),
		.mem_req_addr(mem_req_addr),
		.mem_req_data(mem_req_data),
		.mem_req_epoch(mem_req_epoch),
		.mem_rsp_valid(mem_rsp_valid),
		.mem_rsp_ready(mem_rsp_ready),
		.mem_rsp_data(mem_rsp_data),
		.mem_rsp_epoch(mem_rsp_epoch),
		.mem_rsp_error(mem_rsp_error),
		.packet_state(packet_state),
		.metadata_wait(metadata_wait),
		.dbg_running(dbg_running),
		.dbg_allocation(dbg_allocation),
		.dbg_seal_sent(dbg_seal_sent),
		.dbg_packet_done(dbg_packet_done),
		.dbg_coef_valid(dbg_coef_valid),
		.dbg_coef_ready(dbg_coef_ready),
		.dbg_coef_band(dbg_coef_band),
		.dbg_coef_block(dbg_coef_block),
		.dbg_coef_index(dbg_coef_index),
		.dbg_coef_value(dbg_coef_value),
		.dbg_coef_epoch(dbg_coef_epoch),
		.dbg_meta_valid(dbg_meta_valid),
		.dbg_meta_ready(dbg_meta_ready),
		.dbg_meta_raw(dbg_meta_raw),
		.dbg_band_end_valid(dbg_band_end_valid),
		.dbg_band_end_ready(dbg_band_end_ready),
		.dbg_band_end_band(dbg_band_end_band),
		.dbg_seal_valid(dbg_seal_valid),
		.dbg_seal_ready(dbg_seal_ready),
		.dbg_scratch_state(dbg_scratch_state),
		.dbg_scratch_return_state(dbg_scratch_return_state),
		.dbg_scratch_outstanding(dbg_scratch_outstanding),
		.dbg_prefetch_offer(dbg_prefetch_offer),
		.dbg_prefetch_launch(dbg_prefetch_launch),
		.dbg_prefetch_use(dbg_prefetch_use),
		.dbg_tile_mode(dbg_tile_mode),
		.dbg_tile_preparing(dbg_tile_preparing),
		.dbg_prepare_bank(dbg_prepare_bank),
		.dbg_emit_bank(dbg_emit_bank),
		.dbg_bank_ready(dbg_bank_ready),
		.dbg_bank_owned(dbg_bank_owned),
		.dbg_emitter_state(dbg_emitter_state),
		.dbg_prepare_block(dbg_prepare_block),
		.dbg_bank_block(dbg_bank_block),
		.dbg_bank_epoch(dbg_bank_epoch),
		.dbg_tile_prepare_start(dbg_tile_prepare_start),
		.dbg_tile_publish(dbg_tile_publish),
		.dbg_tile_release(dbg_tile_release),
		.count_emitter_state(count_emitter_state),
		.count_tile_starts(count_tile_starts),
		.count_tile_publishes(count_tile_publishes),
		.count_tile_releases(count_tile_releases),
		.count_prepare_output_overlap(count_prepare_output_overlap),
		.count_prepare_output_hold(count_prepare_output_hold),
		.count_tile_read_output_overlap(count_tile_read_output_overlap),
		.count_tile_bank_wait(count_tile_bank_wait),
		.count_both_ready_wait(count_both_ready_wait),
		.count_tile_prep_done_wait(count_tile_prep_done_wait),
		.count_output_valid(count_output_valid),
		.count_publish_release_same_edge(count_publish_release_same_edge),
		.max_tile_owned(max_tile_owned),
		.max_tile_ready(max_tile_ready),
		.count_prefetch_offers(count_prefetch_offers),
		.count_prefetch_accepts(count_prefetch_accepts),
		.count_prefetch_acks(count_prefetch_acks),
		.count_prefetch_uses(count_prefetch_uses),
		.count_dense_during_read_pending(count_dense_during_read_pending),
		.count_prefetch_drain_wait(count_prefetch_drain_wait),
		.max_prefetch_offer(max_prefetch_offer),
		.dbg_write_slot_valid(dbg_write_slot_valid),
		.dbg_assembler_full(dbg_assembler_full),
		.dbg_write_enqueue(dbg_write_enqueue),
		.count_write_enqueues(count_write_enqueues),
		.count_write_accepts(count_write_accepts),
		.count_write_acks(count_write_acks),
		.count_full_wait(count_full_wait),
		.count_packing_during_write_pending(count_packing_during_write_pending),
		.max_write_slot(max_write_slot),
		.max_owned_lines(max_owned_lines),
		.dbg_scratch_phase(dbg_scratch_phase),
		.dbg_scratch_assembly_bytes(dbg_scratch_assembly_bytes),
		.dbg_scratch_cache_valid(dbg_scratch_cache_valid),
		.dbg_scratch_head_valid(dbg_scratch_head_valid),
		.count_packet_state(count_packet_state),
		.count_scratch_state(count_scratch_state),
		.count_coef_stall(count_coef_stall),
		.count_metadata_wait(count_metadata_wait),
		.count_band_end_stall(count_band_end_stall),
		.count_mem_req_stall(count_mem_req_stall),
		.count_mem_pending(count_mem_pending),
		.count_input_starved(count_input_starved),
		.ts_first_input(ts_first_input),
		.ts_last_input(ts_last_input),
		.ts_metadata_accept(ts_metadata_accept),
		.ts_last_sparse_coef(ts_last_sparse_coef),
		.ts_packet_done_observed(ts_packet_done_observed),
		.ts_seal_accepted(ts_seal_accepted),
		.ts_scratch_sealed_observed(ts_scratch_sealed_observed),
		.ts_first_dense(ts_first_dense),
		.ts_last_dense(ts_last_dense),
		.ts_integrated_done(ts_integrated_done),
		.ts_first_coef_band(ts_first_coef_band),
		.ts_last_coef_band(ts_last_coef_band),
		.ts_band_end(ts_band_end),
		.max_assembly_bytes(max_assembly_bytes),
		.max_cache_valid(max_cache_valid),
		.max_head_valid(max_head_valid),
		.max_outstanding(max_outstanding),
		.stage_read_req(stage_read_req),
		.stage_read_rsp(stage_read_rsp),
		.stage_write(stage_write),
		.stage_pending(stage_pending),
		.stage_context_active(stage_context_active),
		.stage_cancel(stage_cancel),
		.stage_word_valid(stage_word_valid),
		.stage_word_ready(stage_word_ready),
		.stage_read_addr(stage_read_addr),
		.stage_rsp_addr(stage_rsp_addr),
		.stage_write_addr(stage_write_addr),
		.stage_req_epoch(stage_req_epoch),
		.stage_rsp_epoch(stage_rsp_epoch),
		.stage_read_data(stage_read_data),
		.stage_write_data(stage_write_data),
		.stage_buffer_bytes(stage_buffer_bytes),
		.stage_buffer_highwater(stage_buffer_highwater),
		.stage_purpose(stage_purpose),
		.count_stage_reads(count_stage_reads),
		.count_stage_responses(count_stage_responses),
		.count_stage_writes(count_stage_writes),
		.count_stage_fetch_wait(count_stage_fetch_wait),
		.count_stage_word_hold(count_stage_word_hold)
	);
endmodule
module cu66_reconstruct_stream_v91k (
	clk,
	reset,
	start,
	cancel,
	admitted_ready,
	key_frame,
	input_done,
	epoch,
	frame_fid,
	accepted_ref_valid,
	accepted_ref_fid,
	accepted_ref_generation,
	lookup_req,
	lookup_ready,
	lookup_tile,
	lookup_cell,
	lookup_rsp,
	lookup_mode,
	lookup_scale,
	in_valid,
	in_ready,
	in_epoch,
	in_child_epoch,
	in_token,
	in_plane,
	in_qscale,
	in_block,
	in_tile,
	in_qcell,
	in_index,
	in_value,
	out_valid,
	out_ready,
	out_epoch,
	out_fid,
	out_plane,
	out_mode,
	out_tile,
	out_index,
	out_value,
	ref_req_valid,
	ref_req_ready,
	ref_req_epoch,
	ref_req_fid,
	ref_req_generation,
	ref_req_plane,
	ref_req_tile,
	ref_rsp_valid,
	ref_rsp_ready,
	ref_rsp_epoch,
	ref_rsp_fid,
	ref_rsp_generation,
	ref_rsp_plane,
	ref_rsp_tile,
	ref_rsp_pixels,
	ref_rsp_error,
	busy,
	done,
	ref_pending,
	error,
	state,
	count_modes,
	count_residuals,
	count_outputs,
	count_ref_requests,
	count_ref_acks,
	count_copy_tiles,
	count_const_tiles,
	count_residual_tiles,
	count_ref_discarded,
	count_output_stalls,
	count_ref_wait
);
	input wire clk;
	input wire reset;
	input wire start;
	input wire cancel;
	input wire admitted_ready;
	input wire key_frame;
	input wire input_done;
	input wire [31:0] epoch;
	input wire [31:0] frame_fid;
	input wire accepted_ref_valid;
	input wire [31:0] accepted_ref_fid;
	input wire [63:0] accepted_ref_generation;
	output wire lookup_req;
	input wire lookup_ready;
	output wire [12:0] lookup_tile;
	output wire [10:0] lookup_cell;
	input wire lookup_rsp;
	input wire [1:0] lookup_mode;
	input wire [1:0] lookup_scale;
	input wire in_valid;
	output wire in_ready;
	input wire [31:0] in_epoch;
	input wire [31:0] in_child_epoch;
	input wire [31:0] in_token;
	input wire [1:0] in_plane;
	input wire [1:0] in_qscale;
	input wire [15:0] in_block;
	input wire [12:0] in_tile;
	input wire [10:0] in_qcell;
	input wire [5:0] in_index;
	input wire signed [23:0] in_value;
	output wire out_valid;
	input wire out_ready;
	output wire [31:0] out_epoch;
	output wire [31:0] out_fid;
	output wire [1:0] out_plane;
	output wire [1:0] out_mode;
	output wire [12:0] out_tile;
	output wire [5:0] out_index;
	output wire [7:0] out_value;
	output wire ref_req_valid;
	input wire ref_req_ready;
	output wire [31:0] ref_req_epoch;
	output wire [31:0] ref_req_fid;
	output wire [63:0] ref_req_generation;
	output wire [1:0] ref_req_plane;
	output wire [12:0] ref_req_tile;
	input wire ref_rsp_valid;
	output wire ref_rsp_ready;
	input wire [31:0] ref_rsp_epoch;
	input wire [31:0] ref_rsp_fid;
	input wire [63:0] ref_rsp_generation;
	input wire [1:0] ref_rsp_plane;
	input wire [12:0] ref_rsp_tile;
	input wire [511:0] ref_rsp_pixels;
	input wire ref_rsp_error;
	output wire busy;
	output reg done;
	output reg ref_pending;
	output reg [7:0] error;
	output reg [3:0] state;
	output reg [63:0] count_modes;
	output reg [63:0] count_residuals;
	output reg [63:0] count_outputs;
	output reg [63:0] count_ref_requests;
	output reg [63:0] count_ref_acks;
	output reg [63:0] count_copy_tiles;
	output reg [63:0] count_const_tiles;
	output reg [63:0] count_residual_tiles;
	output reg [63:0] count_ref_discarded;
	output reg [63:0] count_output_stalls;
	output reg [63:0] count_ref_wait;
	localparam [3:0] IDLE = 0;
	localparam [3:0] WAIT_ADMISSION = 1;
	localparam [3:0] MODE_REQ = 2;
	localparam [3:0] MODE_WAIT = 3;
	localparam [3:0] RESIDUAL = 4;
	localparam [3:0] REF_REQ = 5;
	localparam [3:0] REF_WAIT = 6;
	localparam [3:0] MATH_SEND = 7;
	localparam [3:0] MATH_WAIT = 8;
	localparam [3:0] EMIT = 9;
	localparam [3:0] WAIT_DONE = 10;
	reg running;
	reg snapshot_ref_valid;
	reg snapshot_key;
	reg discard_ref;
	reg [31:0] frame_epoch;
	reg [31:0] frame_id;
	reg [31:0] snapshot_ref_fid;
	reg [63:0] snapshot_ref_generation;
	reg [1:0] plane;
	reg [1:0] mode;
	reg [1:0] scale;
	reg [12:0] tile;
	reg [5:0] fill_index;
	reg [5:0] emit_index;
	reg [15:0] residual_block [0:2];
	reg [31:0] residual_child;
	reg [31:0] residual_token;
	reg [1535:0] residual;
	reg [511:0] reference_pixels;
	reg [31:0] pending_epoch = 0;
	reg [31:0] pending_fid = 0;
	reg [63:0] pending_generation = 0;
	reg [1:0] pending_plane = 0;
	reg [12:0] pending_tile = 0;
	reg owner_initialized = 0;
	wire ref_match;
	wire kill;
	wire hidden;
	wire math_in_ready;
	wire math_out_valid;
	wire math_out_error;
	wire math_ref_ready;
	wire [31:0] math_out_id;
	wire [511:0] math_out_pixels;
	wire [31:0] tile_id;
	function automatic [31:0] sv2v_cast_32;
		input reg [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function automatic [10:0] sv2v_cast_11;
		input reg [10:0] inp;
		sv2v_cast_11 = inp;
	endfunction
	function automatic [10:0] quant_cell;
		input reg [1:0] p;
		input reg [12:0] t;
		quant_cell = (p == 0 ? sv2v_cast_11((((sv2v_cast_32(t) / 90) / 2) * 45) + ((sv2v_cast_32(t) % 90) / 2)) : sv2v_cast_11(t));
	endfunction
	function automatic safe_hidden;
		input reg [1:0] p;
		input reg [12:0] t;
		integer x;
		integer y;
		begin
			x = sv2v_cast_32(t) % (p == 0 ? 90 : 45);
			y = sv2v_cast_32(t) / (p == 0 ? 90 : 45);
			safe_hidden = (p == 0 ? ((((x >= 3) && (x < 22)) && (((y >= 7) && (y < 9)) || ((y >= 11) && (y < 13)))) || ((((x >= 21) && (x < 61)) && (y >= 45)) && (y < 48))) || ((((x >= 21) && (x < 51)) && (y >= 49)) && (y < 51)) : ((x >= 11) && (x < 30)) && (y == 23));
		end
	endfunction
	task automatic fail;
		input reg [7:0] reason;
		begin
			error <= reason;
			running <= 0;
			done <= 0;
			state <= IDLE;
			discard_ref <= 1;
		end
	endtask
	assign kill = ((reset || start) || cancel) || (error != 0);
	assign busy = running || ref_pending;
	assign hidden = safe_hidden(plane, tile);
	assign tile_id = (plane == 0 ? 0 : (plane == 1 ? 5400 : 6750)) + sv2v_cast_32(tile);
	function automatic [12:0] sv2v_cast_13;
		input reg [12:0] inp;
		sv2v_cast_13 = inp;
	endfunction
	assign lookup_tile = sv2v_cast_13(tile_id);
	assign lookup_cell = quant_cell(plane, tile);
	assign lookup_req = (running && (state == MODE_REQ)) && !kill;
	assign in_ready = (running && (state == RESIDUAL)) && !kill;
	assign out_valid = (((running && (state == EMIT)) && math_out_valid) && !math_out_error) && !kill;
	assign out_epoch = frame_epoch;
	assign out_fid = frame_id;
	assign out_plane = plane;
	assign out_tile = tile;
	assign out_mode = mode;
	assign out_index = emit_index;
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	assign out_value = math_out_pixels[sv2v_cast_32_signed(emit_index) * 8+:8];
	assign ref_req_valid = ((running && (state == REF_REQ)) && !ref_pending) && !kill;
	assign ref_req_epoch = frame_epoch;
	assign ref_req_fid = snapshot_ref_fid;
	assign ref_req_generation = snapshot_ref_generation;
	assign ref_req_plane = plane;
	assign ref_req_tile = tile;
	assign ref_rsp_ready = ref_pending;
	assign ref_match = ((((ref_rsp_epoch == pending_epoch) && (ref_rsp_fid == pending_fid)) && (ref_rsp_generation == pending_generation)) && (ref_rsp_plane == pending_plane)) && (ref_rsp_tile == pending_tile);
	cu66_reconstruct_tile reconstruct(
		.clk(clk),
		.rst(reset),
		.abort_i((start || cancel) || (error != 0)),
		.in_valid((running && (state == MATH_SEND)) && !kill),
		.in_ready(math_in_ready),
		.in_id(tile_id),
		.in_key(snapshot_key),
		.in_hidden(mode == 1),
		.in_residual(residual),
		.ref_valid((snapshot_key || (mode == 1)) || (state == MATH_SEND)),
		.ref_ready(math_ref_ready),
		.ref_tile_id(tile_id),
		.ref_pixels(reference_pixels),
		.out_valid(math_out_valid),
		.out_ready((((running && (state == EMIT)) && out_ready) && (emit_index == 63)) && !kill),
		.out_id(math_out_id),
		.out_pixels(math_out_pixels),
		.out_error(math_out_error)
	);
	initial ref_pending = 0;
	always_ff @(posedge clk) begin
		owner_initialized <= 1;
		if (ref_req_valid && ref_req_ready) begin
			ref_pending <= 1;
			pending_epoch <= ref_req_epoch;
			pending_fid <= ref_req_fid;
			pending_generation <= ref_req_generation;
			pending_plane <= ref_req_plane;
			pending_tile <= ref_req_tile;
		end
		if ((ref_rsp_valid && ref_rsp_ready) && ref_match)
			ref_pending <= 0;
	end
	always_ff @(posedge clk)
		if ((reset || cancel) || start) begin
			running <= (start && !reset) && !cancel;
			done <= 0;
			error <= 0;
			state <= (start ? WAIT_ADMISSION : IDLE);
			plane <= 0;
			tile <= 0;
			mode <= 0;
			scale <= 0;
			fill_index <= 0;
			emit_index <= 0;
			residual <= 0;
			reference_pixels <= 0;
			residual_child <= 0;
			residual_token <= 0;
			residual_block[0] <= 0;
			residual_block[1] <= 0;
			residual_block[2] <= 0;
			discard_ref <= 1;
			if (start) begin
				frame_epoch <= epoch;
				frame_id <= frame_fid;
				snapshot_ref_valid <= accepted_ref_valid;
				snapshot_ref_fid <= accepted_ref_fid;
				snapshot_ref_generation <= accepted_ref_generation;
			end
			if (reset || start) begin
				count_modes <= 0;
				count_residuals <= 0;
				count_outputs <= 0;
				count_ref_requests <= 0;
				count_ref_acks <= 0;
				count_copy_tiles <= 0;
				count_const_tiles <= 0;
				count_residual_tiles <= 0;
				count_ref_discarded <= 0;
				count_output_stalls <= 0;
				count_ref_wait <= 0;
			end
		end
		else begin
			if (ref_rsp_valid && ref_rsp_ready) begin
				if (ref_match) begin
					count_ref_acks <= count_ref_acks + 1;
					if (discard_ref || !running)
						count_ref_discarded <= count_ref_discarded + 1;
					else if (ref_rsp_error)
						fail(3);
					else begin
						reference_pixels <= ref_rsp_pixels;
						state <= MATH_SEND;
					end
				end
				else if (running && !discard_ref)
					fail(3);
			end
			if (running && (error == 0)) begin
				if (out_valid && !out_ready)
					count_output_stalls <= count_output_stalls + 1;
				if (ref_pending)
					count_ref_wait <= count_ref_wait + 1;
				case (state)
					WAIT_ADMISSION:
						if (admitted_ready) begin
							frame_id <= frame_fid;
							snapshot_key <= key_frame;
							state <= MODE_REQ;
							discard_ref <= 0;
						end
					MODE_REQ:
						if (lookup_ready)
							state <= MODE_WAIT;
					MODE_WAIT:
						if (lookup_rsp) begin
							count_modes <= count_modes + 1;
							mode <= lookup_mode;
							scale <= lookup_scale;
							fill_index <= 0;
							residual <= 0;
							reference_pixels <= 0;
							if (((lookup_mode > 2) || (hidden != (lookup_mode == 1))) || (snapshot_key && (lookup_mode == 0)))
								fail(1);
							else if (lookup_mode == 2) begin
								state <= RESIDUAL;
								count_residual_tiles <= count_residual_tiles + 1;
							end
							else if (lookup_mode == 1) begin
								state <= MATH_SEND;
								count_const_tiles <= count_const_tiles + 1;
							end
							else if (!snapshot_ref_valid)
								fail(2);
							else begin
								state <= REF_REQ;
								count_copy_tiles <= count_copy_tiles + 1;
							end
						end
					RESIDUAL:
						if (in_valid && in_ready) begin
							if ((((((((((in_epoch != frame_epoch) || (in_plane != plane)) || (in_tile != tile)) || (in_index != fill_index)) || (in_qcell != quant_cell(plane, tile))) || (in_qscale != scale)) || (in_block != residual_block[plane])) || (in_child_epoch == 0)) || (in_token == 0)) || ((fill_index != 0) && ((in_child_epoch != residual_child) || (in_token != residual_token))))
								fail(4);
							else begin
								residual[sv2v_cast_32_signed(fill_index) * 24+:24] <= in_value;
								count_residuals <= count_residuals + 1;
								if (fill_index == 0) begin
									residual_child <= in_child_epoch;
									residual_token <= in_token;
								end
								if (fill_index == 63) begin
									residual_block[plane] <= residual_block[plane] + 1;
									if (snapshot_key)
										state <= MATH_SEND;
									else if (!snapshot_ref_valid)
										fail(2);
									else
										state <= REF_REQ;
								end
								else
									fill_index <= fill_index + 1;
							end
						end
					REF_REQ:
						if (ref_req_valid && ref_req_ready) begin
							state <= REF_WAIT;
							count_ref_requests <= count_ref_requests + 1;
						end
					REF_WAIT:
						;
					MATH_SEND:
						if (math_in_ready)
							state <= MATH_WAIT;
					MATH_WAIT:
						if (math_out_valid) begin
							if (math_out_error || (math_out_id != tile_id))
								fail(5);
							else begin
								emit_index <= 0;
								state <= EMIT;
							end
						end
					EMIT:
						if (out_valid && out_ready) begin
							count_outputs <= count_outputs + 1;
							if (emit_index == 63) begin
								emit_index <= 0;
								if ((tile + 1) == (plane == 0 ? 13'd5400 : 13'd1350)) begin
									tile <= 0;
									if (plane == 2)
										state <= WAIT_DONE;
									else begin
										plane <= plane + 1;
										state <= MODE_REQ;
									end
								end
								else begin
									tile <= tile + 1;
									state <= MODE_REQ;
								end
							end
							else
								emit_index <= emit_index + 1;
						end
					WAIT_DONE:
						if (input_done && !ref_pending) begin
							running <= 0;
							done <= 1;
							state <= IDLE;
						end
					default:
						;
				endcase
			end
		end
endmodule
module cs88_pipeline_v91k_sv2v (
	clk,
	reset,
	start,
	abort_packet,
	out_valid,
	out_ready,
	out_value,
	out_epoch,
	out_fid,
	out_plane,
	out_mode,
	out_tile,
	out_index,
	ref_req_valid,
	ref_req_ready,
	ref_req_epoch,
	ref_req_fid,
	ref_req_generation,
	ref_req_plane,
	ref_req_tile,
	ref_rsp_valid,
	ref_rsp_ready,
	ref_rsp_epoch,
	ref_rsp_fid,
	ref_rsp_generation,
	ref_rsp_plane,
	ref_rsp_tile,
	ref_rsp_pixels,
	ref_rsp_error,
	reconstruct_busy,
	reconstruct_done,
	ref_pending,
	reconstruct_error,
	reconstruct_state,
	count_reconstruct_modes,
	count_reconstruct_residuals,
	count_reconstruct_outputs,
	count_ref_requests,
	count_ref_acks,
	count_copy_tiles,
	count_const_tiles,
	count_residual_tiles,
	count_ref_discarded,
	count_reconstruct_output_stalls,
	count_reconstruct_ref_wait,
	reconstruct_lookup_req,
	reconstruct_lookup_ready,
	reconstruct_lookup_rsp,
	reconstruct_lookup_tile,
	reconstruct_lookup_cell,
	reconstruct_lookup_mode,
	reconstruct_lookup_scale,
	admitted_ready,
	admitted_key,
	admitted_fid,
	admitted_generation,
	start_ready,
	cache_valid,
	cache_last,
	cache_ready,
	cache_complete,
	cache_data,
	cache_ref_fid,
	cache_ref_generation,
	cache_error,
	accepted_ref_valid,
	accepted_qcache_valid,
	accepted_ref_fid,
	accepted_ref_generation,
	residual_plane,
	residual_tile,
	residual_qcell,
	residual_qscale,
	frame_state,
	frame_fid,
	core_starts,
	refill_bytes,
	blocked_starts,
	current_child_epoch,
	admission_reads,
	replay_reads,
	admission_error,
	frame_read_req,
	frame_read_rsp,
	frame_read_addr,
	frame_rsp_addr,
	frame_rsp_epoch,
	frame_read_data,
	queue_count,
	queue_max_count,
	queue_max_owned,
	queue_pending,
	queue_active,
	queue_push,
	queue_pop,
	queue_stall,
	queue_requests,
	queue_responses,
	queue_pops,
	queue_stalls,
	queue_cancel_queued,
	queue_cancel_pending,
	residual_child_epoch,
	residual_token,
	coefficient_valid,
	coefficient_ready,
	coefficient_done,
	coefficient_epoch,
	coefficient_plane,
	coefficient_qscale,
	coefficient_block,
	coefficient_tile,
	coefficient_qcell,
	coefficient_index,
	coefficient_value,
	coefficient_error,
	inverse_error,
	inverse_busy,
	inverse_done,
	inverse_bank_state,
	inverse_fill_bank,
	inverse_math_bank,
	inverse_math_state,
	inverse_owned_banks,
	inverse_max_owned_banks,
	inverse_launch,
	inverse_dequant,
	inverse_token,
	inverse_epoch,
	inverse_child_epoch,
	inverse_plane,
	inverse_qscale,
	inverse_block,
	inverse_tile,
	inverse_qcell,
	inverse_coefficients,
	inverse_dequantized,
	inverse_count_inputs,
	inverse_count_tiles,
	inverse_count_launches,
	inverse_count_dequant,
	inverse_count_outputs,
	inverse_count_completed_tiles,
	inverse_count_input_stalls,
	inverse_count_output_stalls,
	inverse_count_cancelled_banks,
	packet_bytes,
	epoch,
	serial_clear,
	write_overlap,
	read_prefetch,
	tile_overlap,
	in_valid,
	in_ready,
	in_data,
	in_last,
	residual_valid,
	residual_ready,
	residual_block,
	residual_index,
	residual_value,
	residual_epoch,
	done,
	error,
	busy,
	draining,
	scratch_sealed,
	used_bytes,
	count_cycles,
	count_input_bytes,
	count_dense,
	count_reads,
	count_writes,
	count_dense_stall,
	mem_req_valid,
	mem_req_ready,
	mem_req_write,
	mem_req_addr,
	mem_req_data,
	mem_req_epoch,
	mem_rsp_valid,
	mem_rsp_ready,
	mem_rsp_data,
	mem_rsp_epoch,
	mem_rsp_error,
	packet_state,
	metadata_wait,
	dbg_running,
	dbg_allocation,
	dbg_seal_sent,
	dbg_packet_done,
	dbg_coef_valid,
	dbg_coef_ready,
	dbg_coef_band,
	dbg_coef_block,
	dbg_coef_index,
	dbg_coef_value,
	dbg_coef_epoch,
	dbg_meta_valid,
	dbg_meta_ready,
	dbg_meta_raw,
	dbg_band_end_valid,
	dbg_band_end_ready,
	dbg_band_end_band,
	dbg_seal_valid,
	dbg_seal_ready,
	dbg_scratch_state,
	dbg_scratch_return_state,
	dbg_scratch_outstanding,
	dbg_prefetch_offer,
	dbg_prefetch_launch,
	dbg_prefetch_use,
	dbg_tile_mode,
	dbg_tile_preparing,
	dbg_prepare_bank,
	dbg_emit_bank,
	dbg_bank_ready,
	dbg_bank_owned,
	dbg_emitter_state,
	dbg_prepare_block,
	dbg_bank_block,
	dbg_bank_epoch,
	dbg_tile_prepare_start,
	dbg_tile_publish,
	dbg_tile_release,
	count_emitter_state,
	count_tile_starts,
	count_tile_publishes,
	count_tile_releases,
	count_prepare_output_overlap,
	count_prepare_output_hold,
	count_tile_read_output_overlap,
	count_tile_bank_wait,
	count_both_ready_wait,
	count_tile_prep_done_wait,
	count_output_valid,
	count_publish_release_same_edge,
	max_tile_owned,
	max_tile_ready,
	count_prefetch_offers,
	count_prefetch_accepts,
	count_prefetch_acks,
	count_prefetch_uses,
	count_dense_during_read_pending,
	count_prefetch_drain_wait,
	max_prefetch_offer,
	dbg_write_slot_valid,
	dbg_assembler_full,
	dbg_write_enqueue,
	count_write_enqueues,
	count_write_accepts,
	count_write_acks,
	count_full_wait,
	count_packing_during_write_pending,
	max_write_slot,
	max_owned_lines,
	dbg_scratch_phase,
	dbg_scratch_assembly_bytes,
	dbg_scratch_cache_valid,
	dbg_scratch_head_valid,
	count_packet_state,
	count_scratch_state,
	count_coef_stall,
	count_metadata_wait,
	count_band_end_stall,
	count_mem_req_stall,
	count_mem_pending,
	count_input_starved,
	ts_first_input,
	ts_last_input,
	ts_metadata_accept,
	ts_last_sparse_coef,
	ts_packet_done_observed,
	ts_seal_accepted,
	ts_scratch_sealed_observed,
	ts_first_dense,
	ts_last_dense,
	ts_integrated_done,
	ts_first_coef_band,
	ts_last_coef_band,
	ts_band_end,
	max_assembly_bytes,
	max_cache_valid,
	max_head_valid,
	max_outstanding,
	stage_read_req,
	stage_read_rsp,
	stage_write,
	stage_pending,
	stage_context_active,
	stage_cancel,
	stage_word_valid,
	stage_word_ready,
	stage_read_addr,
	stage_rsp_addr,
	stage_write_addr,
	stage_req_epoch,
	stage_rsp_epoch,
	stage_read_data,
	stage_write_data,
	stage_buffer_bytes,
	stage_buffer_highwater,
	stage_purpose,
	count_stage_reads,
	count_stage_responses,
	count_stage_writes,
	count_stage_fetch_wait,
	count_stage_word_hold
);
	input wire clk;
	input wire reset;
	input wire start;
	input wire abort_packet;
	output wire out_valid;
	input wire out_ready;
	output wire [7:0] out_value;
	output wire [31:0] out_epoch;
	output wire [31:0] out_fid;
	output wire [1:0] out_plane;
	output wire [1:0] out_mode;
	output wire [12:0] out_tile;
	output wire [5:0] out_index;
	output wire ref_req_valid;
	input wire ref_req_ready;
	output wire [31:0] ref_req_epoch;
	output wire [31:0] ref_req_fid;
	output wire [63:0] ref_req_generation;
	output wire [1:0] ref_req_plane;
	output wire [12:0] ref_req_tile;
	input wire ref_rsp_valid;
	output wire ref_rsp_ready;
	input wire [31:0] ref_rsp_epoch;
	input wire [31:0] ref_rsp_fid;
	input wire [63:0] ref_rsp_generation;
	input wire [1:0] ref_rsp_plane;
	input wire [12:0] ref_rsp_tile;
	input wire [511:0] ref_rsp_pixels;
	input wire ref_rsp_error;
	output wire reconstruct_busy;
	output wire reconstruct_done;
	output wire ref_pending;
	output wire [7:0] reconstruct_error;
	output wire [3:0] reconstruct_state;
	output wire [63:0] count_reconstruct_modes;
	output wire [63:0] count_reconstruct_residuals;
	output wire [63:0] count_reconstruct_outputs;
	output wire [63:0] count_ref_requests;
	output wire [63:0] count_ref_acks;
	output wire [63:0] count_copy_tiles;
	output wire [63:0] count_const_tiles;
	output wire [63:0] count_residual_tiles;
	output wire [63:0] count_ref_discarded;
	output wire [63:0] count_reconstruct_output_stalls;
	output wire [63:0] count_reconstruct_ref_wait;
	output wire reconstruct_lookup_req;
	output wire reconstruct_lookup_ready;
	output wire reconstruct_lookup_rsp;
	output wire [12:0] reconstruct_lookup_tile;
	output wire [10:0] reconstruct_lookup_cell;
	output wire [1:0] reconstruct_lookup_mode;
	output wire [1:0] reconstruct_lookup_scale;
	output wire admitted_ready;
	output wire admitted_key;
	output wire [31:0] admitted_fid;
	output wire [63:0] admitted_generation;
	output wire start_ready;
	input wire cache_valid;
	input wire cache_last;
	output wire cache_ready;
	output wire cache_complete;
	input wire [1:0] cache_data;
	input wire [31:0] cache_ref_fid;
	input wire [63:0] cache_ref_generation;
	output wire [7:0] cache_error;
	input wire accepted_ref_valid;
	input wire accepted_qcache_valid;
	input wire [31:0] accepted_ref_fid;
	input wire [63:0] accepted_ref_generation;
	output wire [1:0] residual_plane;
	output wire [12:0] residual_tile;
	output wire [10:0] residual_qcell;
	output wire [1:0] residual_qscale;
	output wire [7:0] frame_state;
	output wire [31:0] frame_fid;
	output wire [31:0] core_starts;
	output wire [31:0] refill_bytes;
	output wire [31:0] blocked_starts;
	output wire [31:0] current_child_epoch;
	output wire [63:0] admission_reads;
	output wire [31:0] replay_reads;
	output wire [7:0] admission_error;
	output wire frame_read_req;
	output wire frame_read_rsp;
	output wire [31:0] frame_read_addr;
	output wire [31:0] frame_rsp_addr;
	output wire [31:0] frame_rsp_epoch;
	output wire [7:0] frame_read_data;
	output wire [1:0] queue_count;
	output wire [1:0] queue_max_count;
	output wire [1:0] queue_max_owned;
	output wire queue_pending;
	output wire queue_active;
	output wire queue_push;
	output wire queue_pop;
	output wire queue_stall;
	output wire [31:0] queue_requests;
	output wire [31:0] queue_responses;
	output wire [31:0] queue_pops;
	output wire [31:0] queue_stalls;
	output wire [31:0] queue_cancel_queued;
	output wire [31:0] queue_cancel_pending;
	output wire [31:0] residual_child_epoch;
	output wire [31:0] residual_token;
	output wire coefficient_valid;
	output wire coefficient_ready;
	output wire coefficient_done;
	output wire [31:0] coefficient_epoch;
	output wire [1:0] coefficient_plane;
	output wire [1:0] coefficient_qscale;
	output wire [15:0] coefficient_block;
	output wire [12:0] coefficient_tile;
	output wire [10:0] coefficient_qcell;
	output wire [5:0] coefficient_index;
	output wire signed [15:0] coefficient_value;
	output wire [7:0] coefficient_error;
	output wire [7:0] inverse_error;
	output wire inverse_busy;
	output wire inverse_done;
	output wire [3:0] inverse_bank_state;
	output wire inverse_fill_bank;
	output wire inverse_math_bank;
	output wire [2:0] inverse_math_state;
	output wire [1:0] inverse_owned_banks;
	output wire [1:0] inverse_max_owned_banks;
	output wire inverse_launch;
	output wire inverse_dequant;
	output wire [31:0] inverse_token;
	output wire [31:0] inverse_epoch;
	output wire [31:0] inverse_child_epoch;
	output wire [1:0] inverse_plane;
	output wire [1:0] inverse_qscale;
	output wire [15:0] inverse_block;
	output wire [12:0] inverse_tile;
	output wire [10:0] inverse_qcell;
	output wire [1023:0] inverse_coefficients;
	output wire [1279:0] inverse_dequantized;
	output wire [63:0] inverse_count_inputs;
	output wire [63:0] inverse_count_tiles;
	output wire [63:0] inverse_count_launches;
	output wire [63:0] inverse_count_dequant;
	output wire [63:0] inverse_count_outputs;
	output wire [63:0] inverse_count_completed_tiles;
	output wire [63:0] inverse_count_input_stalls;
	output wire [63:0] inverse_count_output_stalls;
	output wire [63:0] inverse_count_cancelled_banks;
	input wire [31:0] packet_bytes;
	input wire [31:0] epoch;
	input wire serial_clear;
	input wire write_overlap;
	input wire read_prefetch;
	input wire tile_overlap;
	input wire in_valid;
	output wire in_ready;
	input wire [7:0] in_data;
	input wire in_last;
	output wire residual_valid;
	output wire residual_ready;
	output wire [15:0] residual_block;
	output wire [5:0] residual_index;
	output wire signed [23:0] residual_value;
	output wire [31:0] residual_epoch;
	output wire done;
	output wire [7:0] error;
	output wire busy;
	output wire draining;
	output wire scratch_sealed;
	output wire [18:0] used_bytes;
	output wire [63:0] count_cycles;
	output wire [63:0] count_input_bytes;
	output wire [63:0] count_dense;
	output wire [63:0] count_reads;
	output wire [63:0] count_writes;
	output wire [63:0] count_dense_stall;
	output wire mem_req_valid;
	input wire mem_req_ready;
	output wire mem_req_write;
	output wire [17:0] mem_req_addr;
	output wire [127:0] mem_req_data;
	output wire [31:0] mem_req_epoch;
	input wire mem_rsp_valid;
	output wire mem_rsp_ready;
	input wire [127:0] mem_rsp_data;
	input wire [31:0] mem_rsp_epoch;
	input wire mem_rsp_error;
	output wire [3:0] packet_state;
	output wire metadata_wait;
	output wire dbg_running;
	output wire dbg_allocation;
	output wire dbg_seal_sent;
	output wire dbg_packet_done;
	output wire dbg_coef_valid;
	output wire dbg_coef_ready;
	output wire [1:0] dbg_coef_band;
	output wire [15:0] dbg_coef_block;
	output wire [5:0] dbg_coef_index;
	output wire signed [15:0] dbg_coef_value;
	output wire [31:0] dbg_coef_epoch;
	output wire dbg_meta_valid;
	output wire dbg_meta_ready;
	output wire dbg_meta_raw;
	output wire dbg_band_end_valid;
	output wire dbg_band_end_ready;
	output wire [1:0] dbg_band_end_band;
	output wire dbg_seal_valid;
	output wire dbg_seal_ready;
	output wire [4:0] dbg_scratch_state;
	output wire [4:0] dbg_scratch_return_state;
	output wire dbg_scratch_outstanding;
	output wire dbg_prefetch_offer;
	output wire dbg_prefetch_launch;
	output wire dbg_prefetch_use;
	output wire dbg_tile_mode;
	output wire dbg_tile_preparing;
	output wire dbg_prepare_bank;
	output wire dbg_emit_bank;
	output wire [1:0] dbg_bank_ready;
	output wire [1:0] dbg_bank_owned;
	output wire [1:0] dbg_emitter_state;
	output wire [15:0] dbg_prepare_block;
	output wire [31:0] dbg_bank_block;
	output wire [63:0] dbg_bank_epoch;
	output wire dbg_tile_prepare_start;
	output wire dbg_tile_publish;
	output wire dbg_tile_release;
	output wire [255:0] count_emitter_state;
	output wire [63:0] count_tile_starts;
	output wire [63:0] count_tile_publishes;
	output wire [63:0] count_tile_releases;
	output wire [63:0] count_prepare_output_overlap;
	output wire [63:0] count_prepare_output_hold;
	output wire [63:0] count_tile_read_output_overlap;
	output wire [63:0] count_tile_bank_wait;
	output wire [63:0] count_both_ready_wait;
	output wire [63:0] count_tile_prep_done_wait;
	output wire [63:0] count_output_valid;
	output wire [63:0] count_publish_release_same_edge;
	output wire [1:0] max_tile_owned;
	output wire [1:0] max_tile_ready;
	output wire [63:0] count_prefetch_offers;
	output wire [63:0] count_prefetch_accepts;
	output wire [63:0] count_prefetch_acks;
	output wire [63:0] count_prefetch_uses;
	output wire [63:0] count_dense_during_read_pending;
	output wire [63:0] count_prefetch_drain_wait;
	output wire max_prefetch_offer;
	output wire dbg_write_slot_valid;
	output wire dbg_assembler_full;
	output wire dbg_write_enqueue;
	output wire [63:0] count_write_enqueues;
	output wire [63:0] count_write_accepts;
	output wire [63:0] count_write_acks;
	output wire [63:0] count_full_wait;
	output wire [63:0] count_packing_during_write_pending;
	output wire max_write_slot;
	output wire [1:0] max_owned_lines;
	output wire [2:0] dbg_scratch_phase;
	output wire [4:0] dbg_scratch_assembly_bytes;
	output wire [3:0] dbg_scratch_cache_valid;
	output wire [2:0] dbg_scratch_head_valid;
	output wire [1023:0] count_packet_state;
	output wire [2047:0] count_scratch_state;
	output wire [63:0] count_coef_stall;
	output wire [63:0] count_metadata_wait;
	output wire [63:0] count_band_end_stall;
	output wire [63:0] count_mem_req_stall;
	output wire [63:0] count_mem_pending;
	output wire [63:0] count_input_starved;
	output wire [63:0] ts_first_input;
	output wire [63:0] ts_last_input;
	output wire [63:0] ts_metadata_accept;
	output wire [63:0] ts_last_sparse_coef;
	output wire [63:0] ts_packet_done_observed;
	output wire [63:0] ts_seal_accepted;
	output wire [63:0] ts_scratch_sealed_observed;
	output wire [63:0] ts_first_dense;
	output wire [63:0] ts_last_dense;
	output wire [63:0] ts_integrated_done;
	output wire [255:0] ts_first_coef_band;
	output wire [255:0] ts_last_coef_band;
	output wire [255:0] ts_band_end;
	output wire [4:0] max_assembly_bytes;
	output wire [2:0] max_cache_valid;
	output wire [2:0] max_head_valid;
	output wire max_outstanding;
	output wire stage_read_req;
	output wire stage_read_rsp;
	output wire stage_write;
	output wire stage_pending;
	output wire stage_context_active;
	output wire stage_cancel;
	output wire stage_word_valid;
	output wire stage_word_ready;
	output wire [31:0] stage_read_addr;
	output wire [31:0] stage_rsp_addr;
	output wire [31:0] stage_write_addr;
	output wire [31:0] stage_req_epoch;
	output wire [31:0] stage_rsp_epoch;
	output wire [7:0] stage_read_data;
	output wire [7:0] stage_write_data;
	output wire [5:0] stage_buffer_bytes;
	output wire [5:0] stage_buffer_highwater;
	output wire [2:0] stage_purpose;
	output wire [63:0] count_stage_reads;
	output wire [63:0] count_stage_responses;
	output wire [63:0] count_stage_writes;
	output wire [63:0] count_stage_fetch_wait;
	output wire [63:0] count_stage_word_hold;
	wire accepted_start;
	wire base_start_ready;
	wire base_cache_ready;
	wire base_busy;
	wire inverse_cancel;
	wire base_abort;
	reg inverse_fault_ack;
	reg reconstruction_fault_ack;
	wire reconstruction_cancel;
	assign start_ready = (((base_start_ready && !inverse_busy) && !reconstruct_busy) && !reset) && !abort_packet;
	assign accepted_start = start && start_ready;
	assign cache_ready = (base_cache_ready && !inverse_busy) && !reconstruct_busy;
	assign base_abort = (abort_packet || ((inverse_error != 0) && !inverse_fault_ack)) || ((reconstruct_error != 0) && !reconstruction_fault_ack);
	assign inverse_cancel = abort_packet || (!accepted_start && ((coefficient_error != 0) || (reconstruct_error != 0)));
	assign reconstruction_cancel = abort_packet || (!accepted_start && ((coefficient_error != 0) || (inverse_error != 0)));
	assign error = (reconstruct_error != 0 ? 8'he0 | reconstruct_error : (inverse_error != 0 ? 8'hc0 | inverse_error : coefficient_error));
	assign busy = (base_busy || inverse_busy) || reconstruct_busy;
	assign done = ((coefficient_done && inverse_done) && reconstruct_done) && (error == 0);
	always_ff @(posedge clk)
		if ((reset || abort_packet) || accepted_start) begin
			inverse_fault_ack <= 0;
			reconstruction_fault_ack <= 0;
		end
		else begin
			if (inverse_error != 0)
				inverse_fault_ack <= 1;
			if (reconstruct_error != 0)
				reconstruction_fault_ack <= 1;
		end
	cu66_inverse_stream_v91j transform(
		.clk(clk),
		.reset(reset),
		.start(accepted_start),
		.cancel(inverse_cancel),
		.input_done(coefficient_done),
		.in_valid(coefficient_valid),
		.in_ready(coefficient_ready),
		.in_epoch(coefficient_epoch),
		.in_child_epoch(current_child_epoch),
		.in_plane(coefficient_plane),
		.in_qscale(coefficient_qscale),
		.in_block(coefficient_block),
		.in_tile(coefficient_tile),
		.in_qcell(coefficient_qcell),
		.in_index(coefficient_index),
		.in_value(coefficient_value),
		.out_valid(residual_valid),
		.out_ready(residual_ready),
		.out_epoch(residual_epoch),
		.out_child_epoch(residual_child_epoch),
		.out_token(residual_token),
		.out_plane(residual_plane),
		.out_qscale(residual_qscale),
		.out_block(residual_block),
		.out_tile(residual_tile),
		.out_qcell(residual_qcell),
		.out_index(residual_index),
		.out_value(residual_value),
		.busy(inverse_busy),
		.done(inverse_done),
		.error(inverse_error),
		.bank_state(inverse_bank_state),
		.fill_bank(inverse_fill_bank),
		.math_bank(inverse_math_bank),
		.math_state(inverse_math_state),
		.owned_banks(inverse_owned_banks),
		.max_owned_banks(inverse_max_owned_banks),
		.dbg_launch(inverse_launch),
		.dbg_dequant(inverse_dequant),
		.dbg_token(inverse_token),
		.dbg_coefficients(inverse_coefficients),
		.dbg_dequantized(inverse_dequantized),
		.dbg_epoch(inverse_epoch),
		.dbg_child_epoch(inverse_child_epoch),
		.dbg_plane(inverse_plane),
		.dbg_qscale(inverse_qscale),
		.dbg_block(inverse_block),
		.dbg_tile(inverse_tile),
		.dbg_qcell(inverse_qcell),
		.count_inputs(inverse_count_inputs),
		.count_tiles(inverse_count_tiles),
		.count_launches(inverse_count_launches),
		.count_dequant(inverse_count_dequant),
		.count_outputs(inverse_count_outputs),
		.count_completed_tiles(inverse_count_completed_tiles),
		.count_input_stalls(inverse_count_input_stalls),
		.count_output_stalls(inverse_count_output_stalls),
		.count_cancelled_banks(inverse_count_cancelled_banks)
	);
	cu66_reconstruct_stream_v91k reconstruction(
		.clk(clk),
		.reset(reset),
		.start(accepted_start),
		.cancel(reconstruction_cancel),
		.admitted_ready(admitted_ready),
		.key_frame(admitted_key),
		.input_done(inverse_done),
		.epoch(epoch),
		.frame_fid(admitted_fid),
		.accepted_ref_valid(accepted_ref_valid),
		.accepted_ref_fid(accepted_ref_fid),
		.accepted_ref_generation(accepted_ref_generation),
		.lookup_req(reconstruct_lookup_req),
		.lookup_ready(reconstruct_lookup_ready),
		.lookup_tile(reconstruct_lookup_tile),
		.lookup_cell(reconstruct_lookup_cell),
		.lookup_rsp(reconstruct_lookup_rsp),
		.lookup_mode(reconstruct_lookup_mode),
		.lookup_scale(reconstruct_lookup_scale),
		.in_valid(residual_valid),
		.in_ready(residual_ready),
		.in_epoch(residual_epoch),
		.in_child_epoch(residual_child_epoch),
		.in_token(residual_token),
		.in_plane(residual_plane),
		.in_qscale(residual_qscale),
		.in_block(residual_block),
		.in_tile(residual_tile),
		.in_qcell(residual_qcell),
		.in_index(residual_index),
		.in_value(residual_value),
		.out_valid(out_valid),
		.out_ready(out_ready),
		.out_epoch(out_epoch),
		.out_fid(out_fid),
		.out_plane(out_plane),
		.out_mode(out_mode),
		.out_tile(out_tile),
		.out_index(out_index),
		.out_value(out_value),
		.ref_req_valid(ref_req_valid),
		.ref_req_ready(ref_req_ready),
		.ref_req_epoch(ref_req_epoch),
		.ref_req_fid(ref_req_fid),
		.ref_req_generation(ref_req_generation),
		.ref_req_plane(ref_req_plane),
		.ref_req_tile(ref_req_tile),
		.ref_rsp_valid(ref_rsp_valid),
		.ref_rsp_ready(ref_rsp_ready),
		.ref_rsp_epoch(ref_rsp_epoch),
		.ref_rsp_fid(ref_rsp_fid),
		.ref_rsp_generation(ref_rsp_generation),
		.ref_rsp_plane(ref_rsp_plane),
		.ref_rsp_tile(ref_rsp_tile),
		.ref_rsp_pixels(ref_rsp_pixels),
		.ref_rsp_error(ref_rsp_error),
		.busy(reconstruct_busy),
		.done(reconstruct_done),
		.ref_pending(ref_pending),
		.error(reconstruct_error),
		.state(reconstruct_state),
		.count_modes(count_reconstruct_modes),
		.count_residuals(count_reconstruct_residuals),
		.count_outputs(count_reconstruct_outputs),
		.count_ref_requests(count_ref_requests),
		.count_ref_acks(count_ref_acks),
		.count_copy_tiles(count_copy_tiles),
		.count_const_tiles(count_const_tiles),
		.count_residual_tiles(count_residual_tiles),
		.count_ref_discarded(count_ref_discarded),
		.count_output_stalls(count_reconstruct_output_stalls),
		.count_ref_wait(count_reconstruct_ref_wait)
	);
	cs88_coefficients_v91k #(.REFILL_OVERLAP(1)) coefficients(
		.reconstruct_lookup_req(reconstruct_lookup_req),
		.reconstruct_lookup_tile(reconstruct_lookup_tile),
		.reconstruct_lookup_cell(reconstruct_lookup_cell),
		.reconstruct_lookup_ready(reconstruct_lookup_ready),
		.reconstruct_lookup_rsp(reconstruct_lookup_rsp),
		.reconstruct_lookup_mode(reconstruct_lookup_mode),
		.reconstruct_lookup_scale(reconstruct_lookup_scale),
		.admitted_ready(admitted_ready),
		.admitted_key(admitted_key),
		.admitted_fid(admitted_fid),
		.admitted_generation(admitted_generation),
		.clk(clk),
		.reset(reset),
		.start(accepted_start),
		.abort_packet(base_abort),
		.start_ready(base_start_ready),
		.cache_valid((cache_valid && !inverse_busy) && !reconstruct_busy),
		.cache_last(cache_last),
		.cache_ready(base_cache_ready),
		.cache_complete(cache_complete),
		.cache_data(cache_data),
		.cache_ref_fid(cache_ref_fid),
		.cache_ref_generation(cache_ref_generation),
		.cache_error(cache_error),
		.accepted_ref_valid(accepted_ref_valid),
		.accepted_qcache_valid(accepted_qcache_valid),
		.accepted_ref_fid(accepted_ref_fid),
		.accepted_ref_generation(accepted_ref_generation),
		.out_plane(coefficient_plane),
		.out_tile(coefficient_tile),
		.out_qcell(coefficient_qcell),
		.out_qscale(coefficient_qscale),
		.frame_state(frame_state),
		.frame_fid(frame_fid),
		.core_starts(core_starts),
		.refill_bytes(refill_bytes),
		.blocked_starts(blocked_starts),
		.current_child_epoch(current_child_epoch),
		.admission_reads(admission_reads),
		.replay_reads(replay_reads),
		.admission_error(admission_error),
		.frame_read_req(frame_read_req),
		.frame_read_rsp(frame_read_rsp),
		.frame_read_addr(frame_read_addr),
		.frame_rsp_addr(frame_rsp_addr),
		.frame_rsp_epoch(frame_rsp_epoch),
		.frame_read_data(frame_read_data),
		.queue_count(queue_count),
		.queue_max_count(queue_max_count),
		.queue_max_owned(queue_max_owned),
		.queue_pending(queue_pending),
		.queue_active(queue_active),
		.queue_push(queue_push),
		.queue_pop(queue_pop),
		.queue_stall(queue_stall),
		.queue_requests(queue_requests),
		.queue_responses(queue_responses),
		.queue_pops(queue_pops),
		.queue_stalls(queue_stalls),
		.queue_cancel_queued(queue_cancel_queued),
		.queue_cancel_pending(queue_cancel_pending),
		.packet_bytes(packet_bytes),
		.epoch(epoch),
		.serial_clear(serial_clear),
		.write_overlap(write_overlap),
		.read_prefetch(read_prefetch),
		.tile_overlap(tile_overlap),
		.in_valid(in_valid),
		.in_ready(in_ready),
		.in_data(in_data),
		.in_last(in_last),
		.out_valid(coefficient_valid),
		.out_ready(coefficient_ready),
		.out_block(coefficient_block),
		.out_index(coefficient_index),
		.out_value(coefficient_value),
		.out_epoch(coefficient_epoch),
		.done(coefficient_done),
		.error(coefficient_error),
		.busy(base_busy),
		.draining(draining),
		.scratch_sealed(scratch_sealed),
		.used_bytes(used_bytes),
		.count_cycles(count_cycles),
		.count_input_bytes(count_input_bytes),
		.count_dense(count_dense),
		.count_reads(count_reads),
		.count_writes(count_writes),
		.count_dense_stall(count_dense_stall),
		.mem_req_valid(mem_req_valid),
		.mem_req_ready(mem_req_ready),
		.mem_req_write(mem_req_write),
		.mem_req_addr(mem_req_addr),
		.mem_req_data(mem_req_data),
		.mem_req_epoch(mem_req_epoch),
		.mem_rsp_valid(mem_rsp_valid),
		.mem_rsp_ready(mem_rsp_ready),
		.mem_rsp_data(mem_rsp_data),
		.mem_rsp_epoch(mem_rsp_epoch),
		.mem_rsp_error(mem_rsp_error),
		.packet_state(packet_state),
		.metadata_wait(metadata_wait),
		.dbg_running(dbg_running),
		.dbg_allocation(dbg_allocation),
		.dbg_seal_sent(dbg_seal_sent),
		.dbg_packet_done(dbg_packet_done),
		.dbg_coef_valid(dbg_coef_valid),
		.dbg_coef_ready(dbg_coef_ready),
		.dbg_coef_band(dbg_coef_band),
		.dbg_coef_block(dbg_coef_block),
		.dbg_coef_index(dbg_coef_index),
		.dbg_coef_value(dbg_coef_value),
		.dbg_coef_epoch(dbg_coef_epoch),
		.dbg_meta_valid(dbg_meta_valid),
		.dbg_meta_ready(dbg_meta_ready),
		.dbg_meta_raw(dbg_meta_raw),
		.dbg_band_end_valid(dbg_band_end_valid),
		.dbg_band_end_ready(dbg_band_end_ready),
		.dbg_band_end_band(dbg_band_end_band),
		.dbg_seal_valid(dbg_seal_valid),
		.dbg_seal_ready(dbg_seal_ready),
		.dbg_scratch_state(dbg_scratch_state),
		.dbg_scratch_return_state(dbg_scratch_return_state),
		.dbg_scratch_outstanding(dbg_scratch_outstanding),
		.dbg_prefetch_offer(dbg_prefetch_offer),
		.dbg_prefetch_launch(dbg_prefetch_launch),
		.dbg_prefetch_use(dbg_prefetch_use),
		.dbg_tile_mode(dbg_tile_mode),
		.dbg_tile_preparing(dbg_tile_preparing),
		.dbg_prepare_bank(dbg_prepare_bank),
		.dbg_emit_bank(dbg_emit_bank),
		.dbg_bank_ready(dbg_bank_ready),
		.dbg_bank_owned(dbg_bank_owned),
		.dbg_emitter_state(dbg_emitter_state),
		.dbg_prepare_block(dbg_prepare_block),
		.dbg_bank_block(dbg_bank_block),
		.dbg_bank_epoch(dbg_bank_epoch),
		.dbg_tile_prepare_start(dbg_tile_prepare_start),
		.dbg_tile_publish(dbg_tile_publish),
		.dbg_tile_release(dbg_tile_release),
		.count_emitter_state(count_emitter_state),
		.count_tile_starts(count_tile_starts),
		.count_tile_publishes(count_tile_publishes),
		.count_tile_releases(count_tile_releases),
		.count_prepare_output_overlap(count_prepare_output_overlap),
		.count_prepare_output_hold(count_prepare_output_hold),
		.count_tile_read_output_overlap(count_tile_read_output_overlap),
		.count_tile_bank_wait(count_tile_bank_wait),
		.count_both_ready_wait(count_both_ready_wait),
		.count_tile_prep_done_wait(count_tile_prep_done_wait),
		.count_output_valid(count_output_valid),
		.count_publish_release_same_edge(count_publish_release_same_edge),
		.max_tile_owned(max_tile_owned),
		.max_tile_ready(max_tile_ready),
		.count_prefetch_offers(count_prefetch_offers),
		.count_prefetch_accepts(count_prefetch_accepts),
		.count_prefetch_acks(count_prefetch_acks),
		.count_prefetch_uses(count_prefetch_uses),
		.count_dense_during_read_pending(count_dense_during_read_pending),
		.count_prefetch_drain_wait(count_prefetch_drain_wait),
		.max_prefetch_offer(max_prefetch_offer),
		.dbg_write_slot_valid(dbg_write_slot_valid),
		.dbg_assembler_full(dbg_assembler_full),
		.dbg_write_enqueue(dbg_write_enqueue),
		.count_write_enqueues(count_write_enqueues),
		.count_write_accepts(count_write_accepts),
		.count_write_acks(count_write_acks),
		.count_full_wait(count_full_wait),
		.count_packing_during_write_pending(count_packing_during_write_pending),
		.max_write_slot(max_write_slot),
		.max_owned_lines(max_owned_lines),
		.dbg_scratch_phase(dbg_scratch_phase),
		.dbg_scratch_assembly_bytes(dbg_scratch_assembly_bytes),
		.dbg_scratch_cache_valid(dbg_scratch_cache_valid),
		.dbg_scratch_head_valid(dbg_scratch_head_valid),
		.count_packet_state(count_packet_state),
		.count_scratch_state(count_scratch_state),
		.count_coef_stall(count_coef_stall),
		.count_metadata_wait(count_metadata_wait),
		.count_band_end_stall(count_band_end_stall),
		.count_mem_req_stall(count_mem_req_stall),
		.count_mem_pending(count_mem_pending),
		.count_input_starved(count_input_starved),
		.ts_first_input(ts_first_input),
		.ts_last_input(ts_last_input),
		.ts_metadata_accept(ts_metadata_accept),
		.ts_last_sparse_coef(ts_last_sparse_coef),
		.ts_packet_done_observed(ts_packet_done_observed),
		.ts_seal_accepted(ts_seal_accepted),
		.ts_scratch_sealed_observed(ts_scratch_sealed_observed),
		.ts_first_dense(ts_first_dense),
		.ts_last_dense(ts_last_dense),
		.ts_integrated_done(ts_integrated_done),
		.ts_first_coef_band(ts_first_coef_band),
		.ts_last_coef_band(ts_last_coef_band),
		.ts_band_end(ts_band_end),
		.max_assembly_bytes(max_assembly_bytes),
		.max_cache_valid(max_cache_valid),
		.max_head_valid(max_head_valid),
		.max_outstanding(max_outstanding),
		.stage_read_req(stage_read_req),
		.stage_read_rsp(stage_read_rsp),
		.stage_write(stage_write),
		.stage_pending(stage_pending),
		.stage_context_active(stage_context_active),
		.stage_cancel(stage_cancel),
		.stage_word_valid(stage_word_valid),
		.stage_word_ready(stage_word_ready),
		.stage_read_addr(stage_read_addr),
		.stage_rsp_addr(stage_rsp_addr),
		.stage_write_addr(stage_write_addr),
		.stage_req_epoch(stage_req_epoch),
		.stage_rsp_epoch(stage_rsp_epoch),
		.stage_read_data(stage_read_data),
		.stage_write_data(stage_write_data),
		.stage_buffer_bytes(stage_buffer_bytes),
		.stage_buffer_highwater(stage_buffer_highwater),
		.stage_purpose(stage_purpose),
		.count_stage_reads(count_stage_reads),
		.count_stage_responses(count_stage_responses),
		.count_stage_writes(count_stage_writes),
		.count_stage_fetch_wait(count_stage_fetch_wait),
		.count_stage_word_hold(count_stage_word_hold)
	);
endmodule