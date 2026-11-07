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
				candidate_word_address = starts[1] + (cursors[1] * 4);
				if ((!candidate_valid && (cursors[1] < counts[1])) && (!cache_valid[1] || (cache_address[1] != sv2v_cast_18(candidate_word_address & 32'hfffffff0)))) begin
					candidate_valid = 1;
					candidate_segment = 2'd1;
					candidate_address = sv2v_cast_18(candidate_word_address & 32'hfffffff0);
				end
				candidate_word_address = starts[2] + (cursors[2] * 4);
				if ((!candidate_valid && (cursors[2] < counts[2])) && (!cache_valid[2] || (cache_address[2] != sv2v_cast_18(candidate_word_address & 32'hfffffff0)))) begin
					candidate_valid = 1;
					candidate_segment = 2'd2;
					candidate_address = sv2v_cast_18(candidate_word_address & 32'hfffffff0);
				end
				candidate_word_address = starts[3] + (cursors[3] * 4);
				if ((!candidate_valid && (cursors[3] < counts[3])) && (!cache_valid[3] || (cache_address[3] != sv2v_cast_18(candidate_word_address & 32'hfffffff0)))) begin
					candidate_valid = 1;
					candidate_segment = 2'd3;
					candidate_address = sv2v_cast_18(candidate_word_address & 32'hfffffff0);
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
							begin : sv2v_autoblock_3
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
