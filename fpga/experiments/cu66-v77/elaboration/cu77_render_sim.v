module cu77_direct_cache (
	clk,
	rst,
	abort_i,
	desc_valid,
	desc_ready,
	desc_generation,
	desc_frame_id,
	desc_bank,
	finish_valid,
	finish_ready,
	active,
	aborted,
	error,
	error_code,
	active_generation,
	active_frame_id,
	prefetch_valid,
	prefetch_ready,
	prefetch_index,
	prefetch_done_valid,
	prefetch_done_ready,
	prefetch_done_index,
	consume_valid,
	consume_ready,
	consume_index,
	prefetched_count,
	consumed_count,
	mem_req_valid,
	mem_req_ready,
	mem_req_addr,
	mem_rsp_valid,
	mem_rsp_ready,
	mem_rsp_data,
	mem_rsp_last,
	mem_rsp_error,
	pixel_req_valid,
	pixel_req_ready,
	pixel_u,
	pixel_v,
	pixel_rsp_valid,
	pixel_rsp_ready,
	pixel_rsp_u,
	pixel_rsp_v,
	pixel_y,
	cb00,
	cb10,
	cb01,
	cb11,
	cr00,
	cr10,
	cr01,
	cr11,
	pixel_hud_hit,
	pixel_hud,
	pixel_rsp_error,
	read_commands,
	read_words,
	pixel_queries,
	cache_misses
);
	reg _sv2v_0;
	input wire clk;
	input wire rst;
	input wire abort_i;
	input wire desc_valid;
	output reg desc_ready;
	input wire [63:0] desc_generation;
	input wire [31:0] desc_frame_id;
	input wire [1:0] desc_bank;
	input wire finish_valid;
	output reg finish_ready;
	output reg active;
	output reg aborted;
	output reg error;
	output reg [7:0] error_code;
	output reg [63:0] active_generation;
	output reg [31:0] active_frame_id;
	input wire prefetch_valid;
	output reg prefetch_ready;
	input wire [6:0] prefetch_index;
	output reg prefetch_done_valid;
	input wire prefetch_done_ready;
	output reg [6:0] prefetch_done_index;
	input wire consume_valid;
	output reg consume_ready;
	input wire [6:0] consume_index;
	output reg [6:0] prefetched_count;
	output reg [6:0] consumed_count;
	output reg mem_req_valid;
	input wire mem_req_ready;
	output reg [23:0] mem_req_addr;
	input wire mem_rsp_valid;
	output reg mem_rsp_ready;
	input wire [15:0] mem_rsp_data;
	input wire mem_rsp_last;
	input wire mem_rsp_error;
	input wire pixel_req_valid;
	output reg pixel_req_ready;
	input wire [9:0] pixel_u;
	input wire [8:0] pixel_v;
	output reg pixel_rsp_valid;
	input wire pixel_rsp_ready;
	output reg [9:0] pixel_rsp_u;
	output reg [8:0] pixel_rsp_v;
	output reg [7:0] pixel_y;
	output reg [7:0] cb00;
	output reg [7:0] cb10;
	output reg [7:0] cb01;
	output reg [7:0] cb11;
	output reg [7:0] cr00;
	output reg [7:0] cr10;
	output reg [7:0] cr01;
	output reg [7:0] cr11;
	output reg pixel_hud_hit;
	output reg [15:0] pixel_hud;
	output reg pixel_rsp_error;
	output reg [31:0] read_commands;
	output reg [31:0] read_words;
	output reg [31:0] pixel_queries;
	output reg [31:0] cache_misses;
	reg [2:0] state;
	reg [1:0] bank;
	reg aborting;
	reg failed;
	reg [6:0] strip;
	reg [2:0] phase;
	reg [5:0] column;
	reg [5:0] tile_row;
	reg [1:0] block_no;
	reg [2:0] beat;
	reg [2:0] yvalid;
	reg [2:0] cvalid0;
	reg [2:0] cvalid1;
	reg [6:0] ytag [0:2];
	reg [5:0] ctag0 [0:2];
	reg [5:0] ctag1 [0:2];
	reg [15:0] hvalid;
	reg [5:0] htag [0:15];
	reg [15:0] ymemory [0:5759];
	reg [15:0] hmemory [0:3071];
	reg [15:0] cbmem0 [0:719];
	reg [15:0] cbmem1 [0:719];
	reg [15:0] cbmem2 [0:719];
	reg [15:0] cbmem3 [0:719];
	reg [15:0] crmem0 [0:719];
	reg [15:0] crmem1 [0:719];
	reg [15:0] crmem2 [0:719];
	reg [15:0] crmem3 [0:719];
	reg [15:0] yword;
	reg [15:0] hword;
	reg [15:0] cbword [0:3];
	reg [15:0] crword [0:3];
	reg pixel_pending;
	reg ylane;
	reg clane0;
	reg clane1;
	reg [1:0] mb00;
	reg [1:0] mb10;
	reg [1:0] mb01;
	reg [1:0] mb11;
	reg [12:0] yraddr;
	reg [11:0] hraddr;
	reg [9:0] craddr [0:3];
	reg query_ok;
	reg qhud;
	reg [1:0] qb00;
	reg [1:0] qb10;
	reg [1:0] qb01;
	reg [1:0] qb11;
	integer qu;
	integer qv;
	integer qcx;
	integer qcx1;
	integer qcy;
	integer qcy1;
	integer qys;
	integer qcs0;
	integer qcs1;
	integer qcw0;
	integer qcw1;
	integer qs;
	integer hrect;
	integer hx;
	integer hw;
	integer hoff;
	integer hlo;
	integer hhi;
	integer hlast;
	integer target_col;
	integer target_slot;
	integer last_row;
	integer fill_row;
	integer fill_word;
	integer write_bank;
	reg [12:0] write_addr;
	reg scan_hit;
	reg scan_empty;
	reg last_column;
	function automatic integer rect_x;
		input integer n;
		case (n)
			0, 1: rect_x = 22;
			default: rect_x = 168;
		endcase
	endfunction
	function automatic integer rect_y;
		input integer n;
		case (n)
			0: rect_y = 54;
			1: rect_y = 82;
			2: rect_y = 360;
			default: rect_y = 390;
		endcase
	endfunction
	function automatic integer rect_w;
		input integer n;
		case (n)
			0, 1: rect_w = 160;
			2: rect_w = 320;
			default: rect_w = 240;
		endcase
	endfunction
	function automatic integer rect_off;
		input integer n;
		case (n)
			0: rect_off = 0;
			1: rect_off = 3840;
			2: rect_off = 7680;
			default: rect_off = 15360;
		endcase
	endfunction
	function automatic [23:0] canonical;
		input reg [1:0] b;
		case (b)
			0: canonical = 24'h080000;
			1: canonical = 24'h480000;
			default: canonical = 24'h880000;
		endcase
	endfunction
	function automatic [23:0] hudbase;
		input reg [1:0] b;
		case (b)
			0: hudbase = 24'h100000;
			1: hudbase = 24'h500000;
			default: hudbase = 24'h900000;
		endcase
	endfunction
	function automatic integer caddr;
		input integer slot;
		input integer cy;
		input integer cw;
		caddr = ((slot * 240) + ((cy / 2) * 2)) + (cw / 2);
	endfunction
	function automatic signed [23:0] sv2v_cast_24_signed;
		input reg signed [23:0] inp;
		sv2v_cast_24_signed = inp;
	endfunction
	function automatic signed [12:0] sv2v_cast_13_signed;
		input reg signed [12:0] inp;
		sv2v_cast_13_signed = inp;
	endfunction
	function automatic signed [6:0] sv2v_cast_7_signed;
		input reg signed [6:0] inp;
		sv2v_cast_7_signed = inp;
	endfunction
	function automatic signed [5:0] sv2v_cast_6_signed;
		input reg signed [5:0] inp;
		sv2v_cast_6_signed = inp;
	endfunction
	function automatic signed [11:0] sv2v_cast_12_signed;
		input reg signed [11:0] inp;
		sv2v_cast_12_signed = inp;
	endfunction
	function automatic signed [1:0] sv2v_cast_2_signed;
		input reg signed [1:0] inp;
		sv2v_cast_2_signed = inp;
	endfunction
	function automatic signed [9:0] sv2v_cast_10_signed;
		input reg signed [9:0] inp;
		sv2v_cast_10_signed = inp;
	endfunction
	function automatic [7:0] sv2v_cast_8;
		input reg [7:0] inp;
		sv2v_cast_8 = inp;
	endfunction
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	always @(*) begin
		if (_sv2v_0)
			;
		hrect = sv2v_cast_32_signed(phase) - 3;
		hx = rect_x(hrect);
		hw = rect_w(hrect);
		hoff = rect_off(hrect);
		hlo = ((sv2v_cast_32_signed(strip) * 8) > hx ? sv2v_cast_32_signed(strip) * 8 : hx);
		hhi = (((sv2v_cast_32_signed(strip) * 8) + 8) < (hx + hw) ? (sv2v_cast_32_signed(strip) * 8) + 8 : hx + hw);
		hlast = ((hhi - 1) - hx) / 8;
		target_col = (phase == 0 ? sv2v_cast_32_signed(strip) : sv2v_cast_32_signed(column));
		target_slot = target_col % 3;
		scan_hit = 0;
		scan_empty = 0;
		last_column = 1;
		last_row = (phase == 0 ? 59 : (phase < 3 ? 29 : 23));
		if (phase == 0)
			scan_hit = yvalid[target_slot] && (ytag[target_slot] == strip);
		else if (phase == 1) begin
			scan_hit = cvalid0[target_slot] && (ctag0[target_slot] == column);
			last_column = sv2v_cast_32_signed(column) == ((((sv2v_cast_32_signed(strip) * 4) + 4) > 359 ? 359 : (sv2v_cast_32_signed(strip) * 4) + 4) / 8);
		end
		else if (phase == 2) begin
			scan_hit = cvalid1[target_slot] && (ctag1[target_slot] == column);
			last_column = sv2v_cast_32_signed(column) == ((((sv2v_cast_32_signed(strip) * 4) + 4) > 359 ? 359 : (sv2v_cast_32_signed(strip) * 4) + 4) / 8);
		end
		else if (phase <= 6) begin
			target_slot = sv2v_cast_32_signed(column) % 4;
			scan_empty = hlo >= hhi;
			scan_hit = hvalid[(hrect * 4) + target_slot] && (htag[(hrect * 4) + target_slot] == column);
			last_column = sv2v_cast_32_signed(column) == hlast;
		end
		mem_req_addr = canonical(bank);
		if (phase == 0)
			mem_req_addr = canonical(bank) + sv2v_cast_24_signed((((sv2v_cast_32_signed(tile_row) * 90) + sv2v_cast_32_signed(strip)) * 32) + (sv2v_cast_32_signed(block_no) * 8));
		else if ((phase == 1) || (phase == 2))
			mem_req_addr = (canonical(bank) + (phase == 1 ? 24'd172800 : 24'd216000)) + sv2v_cast_24_signed((((sv2v_cast_32_signed(tile_row) * 45) + sv2v_cast_32_signed(column)) * 32) + (sv2v_cast_32_signed(block_no) * 8));
		else if (phase <= 6)
			mem_req_addr = hudbase(bank) + sv2v_cast_24_signed((hoff + (sv2v_cast_32_signed(tile_row) * hw)) + (sv2v_cast_32_signed(column) * 8));
		fill_word = (sv2v_cast_32_signed(block_no) * 8) + sv2v_cast_32_signed(beat);
		fill_row = (sv2v_cast_32_signed(tile_row) * 8) + (fill_word / 4);
		write_addr = sv2v_cast_13_signed((phase == 0 ? (((sv2v_cast_32_signed(strip) % 3) * 1920) + (fill_row * 4)) + (fill_word % 4) : (phase < 3 ? caddr(sv2v_cast_32_signed(column) % 3, fill_row, fill_word % 4) : (((hrect * 768) + ((sv2v_cast_32_signed(column) % 4) * 192)) + (sv2v_cast_32_signed(tile_row) * 8)) + sv2v_cast_32_signed(beat))));
		write_bank = ((fill_row % 2) * 2) + (fill_word % 2);
		desc_ready = ((((!active && (state == 3'd0)) && !pixel_pending) && !mem_rsp_valid) && !rst) && !abort_i;
		finish_ready = (((((((active && !error) && (state == 3'd0)) && (prefetched_count == 90)) && (consumed_count == 90)) && !pixel_pending) && !pixel_req_valid) && !abort_i) && !rst;
		prefetch_ready = ((((((active && !error) && (state == 3'd0)) && !abort_i) && !rst) && (prefetch_index == prefetched_count)) && (prefetched_count < 90)) && (sv2v_cast_32_signed(prefetch_index) < (sv2v_cast_32_signed(consumed_count) + 3));
		prefetch_done_valid = (((((state == 3'd4) && active) && !error) && !aborting) && !abort_i) && !rst;
		prefetch_done_index = strip;
		consume_ready = ((((((active && !error) && !abort_i) && !rst) && !pixel_pending) && !pixel_req_valid) && (consume_index == consumed_count)) && (consumed_count < prefetched_count);
		mem_req_valid = (((((state == 3'd2) && active) && !failed) && !aborting) && !abort_i) && !rst;
		mem_rsp_ready = (state == 3'd3) && !rst;
		qu = sv2v_cast_32_signed(pixel_u);
		qv = sv2v_cast_32_signed(pixel_v);
		qs = qu / 8;
		qcx = qu / 2;
		qcx1 = ((qcx + 1) < 360 ? qcx + 1 : 359);
		qcy = qv / 2;
		qcy1 = ((qcy + 1) < 240 ? qcy + 1 : 239);
		qys = qs % 3;
		qcs0 = (qcx / 8) % 3;
		qcs1 = (qcx1 / 8) % 3;
		qcw0 = (qcx % 8) / 2;
		qcw1 = (qcx1 % 8) / 2;
		query_ok = ((((active && !error) && (qu < 720)) && (qv < 480)) && (qs >= sv2v_cast_32_signed(consumed_count))) && (qs < sv2v_cast_32_signed(prefetched_count));
		if (((((((((!yvalid[qys] || (ytag[qys] != sv2v_cast_7_signed(qs))) || !cvalid0[qcs0]) || !cvalid0[qcs1]) || !cvalid1[qcs0]) || !cvalid1[qcs1]) || (ctag0[qcs0] != sv2v_cast_6_signed(qcx / 8))) || (ctag0[qcs1] != sv2v_cast_6_signed(qcx1 / 8))) || (ctag1[qcs0] != sv2v_cast_6_signed(qcx / 8))) || (ctag1[qcs1] != sv2v_cast_6_signed(qcx1 / 8)))
			query_ok = 0;
		yraddr = sv2v_cast_13_signed(((qys * 1920) + (qv * 4)) + ((qu % 8) / 2));
		hraddr = 0;
		qhud = 0;
		begin : sv2v_autoblock_1
			integer i;
			for (i = 0; i < 4; i = i + 1)
				if ((((qu >= rect_x(i)) && (qu < (rect_x(i) + rect_w(i)))) && (qv >= rect_y(i))) && (qv < (rect_y(i) + 24))) begin
					qhud = 1;
					hraddr = sv2v_cast_12_signed((((i * 768) + ((((qu - rect_x(i)) / 8) % 4) * 192)) + ((qv - rect_y(i)) * 8)) + ((qu - rect_x(i)) % 8));
					if (!hvalid[(i * 4) + (((qu - rect_x(i)) / 8) % 4)] || (htag[(i * 4) + (((qu - rect_x(i)) / 8) % 4)] != sv2v_cast_6_signed((qu - rect_x(i)) / 8)))
						query_ok = 0;
				end
		end
		qb00 = sv2v_cast_2_signed(((qcy % 2) * 2) + (qcw0 % 2));
		qb10 = sv2v_cast_2_signed(((qcy % 2) * 2) + (qcw1 % 2));
		qb01 = sv2v_cast_2_signed(((qcy1 % 2) * 2) + (qcw0 % 2));
		qb11 = sv2v_cast_2_signed(((qcy1 % 2) * 2) + (qcw1 % 2));
		begin : sv2v_autoblock_2
			integer i;
			for (i = 0; i < 4; i = i + 1)
				craddr[i] = 0;
		end
		craddr[qb00] = sv2v_cast_10_signed(caddr(qcs0, qcy, qcw0));
		craddr[qb10] = sv2v_cast_10_signed(caddr(qcs1, qcy, qcw1));
		craddr[qb01] = sv2v_cast_10_signed(caddr(qcs0, qcy1, qcw0));
		craddr[qb11] = sv2v_cast_10_signed(caddr(qcs1, qcy1, qcw1));
		if (!query_ok) begin : sv2v_autoblock_3
			integer i;
			for (i = 0; i < 4; i = i + 1)
				craddr[i] = 0;
		end
		pixel_req_ready = (((active && !error) && !abort_i) && !rst) && (!pixel_pending || pixel_rsp_ready);
		pixel_rsp_valid = (pixel_pending && !abort_i) && !rst;
		pixel_y = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(yword >> (ylane ? 8 : 0)));
		cb00 = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(cbword[mb00] >> (clane0 ? 8 : 0)));
		cb10 = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(cbword[mb10] >> (clane1 ? 8 : 0)));
		cb01 = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(cbword[mb01] >> (clane0 ? 8 : 0)));
		cb11 = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(cbword[mb11] >> (clane1 ? 8 : 0)));
		cr00 = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(crword[mb00] >> (clane0 ? 8 : 0)));
		cr10 = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(crword[mb10] >> (clane1 ? 8 : 0)));
		cr01 = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(crword[mb01] >> (clane0 ? 8 : 0)));
		cr11 = (pixel_rsp_error ? 8'd0 : sv2v_cast_8(crword[mb11] >> (clane1 ? 8 : 0)));
		pixel_hud = (pixel_rsp_error ? 16'd0 : hword);
	end
	always @(posedge clk) begin
		if ((((((mem_rsp_valid && mem_rsp_ready) && !aborting) && !abort_i) && !failed) && !mem_rsp_error) && (mem_rsp_last == (beat == 7))) begin
			if (phase == 0)
				ymemory[write_addr] <= mem_rsp_data;
			else if (phase == 1)
				case (write_bank)
					0: cbmem0[write_addr[9:0]] <= mem_rsp_data;
					1: cbmem1[write_addr[9:0]] <= mem_rsp_data;
					2: cbmem2[write_addr[9:0]] <= mem_rsp_data;
					default: cbmem3[write_addr[9:0]] <= mem_rsp_data;
				endcase
			else if (phase == 2)
				case (write_bank)
					0: crmem0[write_addr[9:0]] <= mem_rsp_data;
					1: crmem1[write_addr[9:0]] <= mem_rsp_data;
					2: crmem2[write_addr[9:0]] <= mem_rsp_data;
					default: crmem3[write_addr[9:0]] <= mem_rsp_data;
				endcase
			else
				hmemory[write_addr[11:0]] <= mem_rsp_data;
		end
		if (pixel_req_valid && pixel_req_ready) begin
			yword <= ymemory[(query_ok ? yraddr : 13'd0)];
			hword <= hmemory[(query_ok ? hraddr : 12'd0)];
			cbword[0] <= cbmem0[craddr[0]];
			cbword[1] <= cbmem1[craddr[1]];
			cbword[2] <= cbmem2[craddr[2]];
			cbword[3] <= cbmem3[craddr[3]];
			crword[0] <= crmem0[craddr[0]];
			crword[1] <= crmem1[craddr[1]];
			crword[2] <= crmem2[craddr[2]];
			crword[3] <= crmem3[craddr[3]];
		end
	end
	task automatic next_phase;
		begin
			tile_row <= 0;
			block_no <= 0;
			if (phase == 0) begin
				phase <= 1;
				column <= sv2v_cast_6_signed((sv2v_cast_32_signed(strip) * 4) / 8);
			end
			else if (phase == 1) begin
				phase <= 2;
				column <= sv2v_cast_6_signed((sv2v_cast_32_signed(strip) * 4) / 8);
			end
			else if (phase == 2) begin
				phase <= 3;
				column <= sv2v_cast_6_signed(((sv2v_cast_32_signed(strip) * 8) > 22 ? (sv2v_cast_32_signed(strip) * 8) - 22 : 0) / 8);
			end
			else if (phase < 6) begin
				phase <= phase + 1'b1;
				column <= sv2v_cast_6_signed(((sv2v_cast_32_signed(strip) * 8) > rect_x(sv2v_cast_32_signed(phase) - 2) ? (sv2v_cast_32_signed(strip) * 8) - rect_x(sv2v_cast_32_signed(phase) - 2) : 0) / 8);
			end
			else begin
				prefetched_count <= strip + 1'b1;
				state <= 3'd4;
			end
		end
	endtask
	function automatic signed [0:0] sv2v_cast_1_signed;
		input reg signed [0:0] inp;
		sv2v_cast_1_signed = inp;
	endfunction
	always @(posedge clk)
		if (rst) begin
			state <= 3'd0;
			active <= 0;
			bank <= 0;
			aborting <= 0;
			failed <= 0;
			aborted <= 0;
			error <= 0;
			error_code <= 0;
			active_generation <= 0;
			active_frame_id <= 0;
			strip <= 0;
			phase <= 0;
			column <= 0;
			tile_row <= 0;
			block_no <= 0;
			beat <= 0;
			prefetched_count <= 0;
			consumed_count <= 0;
			yvalid <= 0;
			cvalid0 <= 0;
			cvalid1 <= 0;
			hvalid <= 0;
			pixel_pending <= 0;
			pixel_rsp_u <= 0;
			pixel_rsp_v <= 0;
			pixel_rsp_error <= 0;
			pixel_hud_hit <= 0;
			ylane <= 0;
			clane0 <= 0;
			clane1 <= 0;
			mb00 <= 0;
			mb10 <= 0;
			mb01 <= 0;
			mb11 <= 0;
			read_commands <= 0;
			read_words <= 0;
			pixel_queries <= 0;
			cache_misses <= 0;
			begin : sv2v_autoblock_4
				integer i;
				for (i = 0; i < 3; i = i + 1)
					begin
						ytag[i] <= 0;
						ctag0[i] <= 0;
						ctag1[i] <= 0;
					end
			end
			begin : sv2v_autoblock_5
				integer i;
				for (i = 0; i < 16; i = i + 1)
					htag[i] <= 0;
			end
		end
		else begin
			aborted <= 0;
			if (pixel_rsp_valid && pixel_rsp_ready)
				pixel_pending <= 0;
			if (pixel_req_valid && pixel_req_ready) begin
				pixel_pending <= 1;
				pixel_rsp_u <= pixel_u;
				pixel_rsp_v <= pixel_v;
				pixel_rsp_error <= !query_ok;
				pixel_hud_hit <= query_ok && qhud;
				ylane <= pixel_u[0];
				clane0 <= sv2v_cast_1_signed(qcx % 2);
				clane1 <= sv2v_cast_1_signed(qcx1 % 2);
				mb00 <= qb00;
				mb10 <= qb10;
				mb01 <= qb01;
				mb11 <= qb11;
				pixel_queries <= pixel_queries + 1;
				if (!query_ok)
					cache_misses <= cache_misses + 1;
			end
			if (desc_valid && desc_ready) begin
				error <= ((desc_generation == 0) || (desc_frame_id == 32'hffffffff)) || (desc_bank > 2);
				error_code <= (((desc_generation == 0) || (desc_frame_id == 32'hffffffff)) || (desc_bank > 2) ? 8'h01 : 8'd0);
				active <= ((desc_generation != 0) && (desc_frame_id != 32'hffffffff)) && (desc_bank < 3);
				active_generation <= desc_generation;
				active_frame_id <= desc_frame_id;
				bank <= desc_bank;
				prefetched_count <= 0;
				consumed_count <= 0;
				yvalid <= 0;
				cvalid0 <= 0;
				cvalid1 <= 0;
				hvalid <= 0;
				aborting <= 0;
				failed <= 0;
				read_commands <= 0;
				read_words <= 0;
				pixel_queries <= 0;
				cache_misses <= 0;
			end
			if (finish_valid && finish_ready) begin
				active <= 0;
				yvalid <= 0;
				cvalid0 <= 0;
				cvalid1 <= 0;
				hvalid <= 0;
			end
			if (consume_valid && consume_ready)
				consumed_count <= consumed_count + 1'b1;
			if (abort_i && active) begin
				pixel_pending <= 0;
				aborting <= 1;
				yvalid <= 0;
				cvalid0 <= 0;
				cvalid1 <= 0;
				hvalid <= 0;
				if (state != 3'd3) begin
					active <= 0;
					state <= 3'd0;
					aborting <= 0;
					aborted <= 1;
				end
			end
			else if (!aborting)
				case (state)
					3'd0:
						if (prefetch_valid && prefetch_ready) begin
							strip <= prefetch_index;
							phase <= 0;
							column <= 0;
							tile_row <= 0;
							block_no <= 0;
							beat <= 0;
							failed <= 0;
							state <= 3'd1;
						end
					3'd1:
						if (scan_empty || scan_hit) begin
							if (last_column || scan_empty)
								next_phase;
							else
								column <= column + 1'b1;
						end
						else begin
							if (phase == 0)
								yvalid[target_slot] <= 0;
							else if (phase == 1)
								cvalid0[target_slot] <= 0;
							else if (phase == 2)
								cvalid1[target_slot] <= 0;
							else
								hvalid[(hrect * 4) + target_slot] <= 0;
							tile_row <= 0;
							block_no <= 0;
							beat <= 0;
							state <= 3'd2;
						end
					3'd2:
						if (mem_req_valid && mem_req_ready) begin
							read_commands <= read_commands + 1;
							beat <= 0;
							state <= 3'd3;
						end
					3'd3:
						;
					3'd4:
						if (prefetch_done_valid && prefetch_done_ready)
							state <= 3'd0;
					default: state <= 3'd0;
				endcase
			if (((state == 3'd3) && mem_rsp_valid) && mem_rsp_ready) begin
				read_words <= read_words + 1;
				if (mem_rsp_error || (mem_rsp_last != (beat == 7))) begin
					failed <= 1;
					error <= 1;
					error_code <= 8'h02;
				end
				if (beat == 7) begin
					beat <= 0;
					if ((((aborting || abort_i) || failed) || mem_rsp_error) || !mem_rsp_last) begin
						active <= 0;
						state <= 3'd0;
						aborting <= 0;
						aborted <= 1;
						pixel_pending <= 0;
						yvalid <= 0;
						cvalid0 <= 0;
						cvalid1 <= 0;
						hvalid <= 0;
					end
					else if ((sv2v_cast_32_signed(tile_row) == last_row) && ((phase >= 3) || (block_no == 3))) begin
						if (phase == 0) begin
							yvalid[target_slot] <= 1;
							ytag[target_slot] <= strip;
						end
						else if (phase == 1) begin
							cvalid0[target_slot] <= 1;
							ctag0[target_slot] <= column;
						end
						else if (phase == 2) begin
							cvalid1[target_slot] <= 1;
							ctag1[target_slot] <= column;
						end
						else begin
							hvalid[(hrect * 4) + target_slot] <= 1;
							htag[(hrect * 4) + target_slot] <= column;
						end
						tile_row <= 0;
						block_no <= 0;
						state <= 3'd1;
						if (last_column)
							next_phase;
						else
							column <= column + 1'b1;
					end
					else begin
						if ((phase >= 3) || (block_no == 3)) begin
							block_no <= 0;
							tile_row <= tile_row + 1'b1;
						end
						else
							block_no <= block_no + 1'b1;
						state <= 3'd2;
					end
				end
				else
					beat <= beat + 1'b1;
			end
		end
	initial _sv2v_0 = 0;
endmodule
module cu77_yuv_rgb (
	clk,
	rst,
	abort_i,
	in_valid,
	in_ready,
	in_u,
	in_v,
	in_y,
	in_cb00,
	in_cb10,
	in_cb01,
	in_cb11,
	in_cr00,
	in_cr10,
	in_cr01,
	in_cr11,
	in_hud_hit,
	in_hud,
	in_error,
	out_valid,
	out_ready,
	out_u,
	out_v,
	out_rgb,
	out_error
);
	reg _sv2v_0;
	input wire clk;
	input wire rst;
	input wire abort_i;
	input wire in_valid;
	output reg in_ready;
	input wire [9:0] in_u;
	input wire [8:0] in_v;
	input wire [7:0] in_y;
	input wire [7:0] in_cb00;
	input wire [7:0] in_cb10;
	input wire [7:0] in_cb01;
	input wire [7:0] in_cb11;
	input wire [7:0] in_cr00;
	input wire [7:0] in_cr10;
	input wire [7:0] in_cr01;
	input wire [7:0] in_cr11;
	input wire in_hud_hit;
	input wire [15:0] in_hud;
	input wire in_error;
	output reg out_valid;
	input wire out_ready;
	output reg [9:0] out_u;
	output reg [8:0] out_v;
	output reg [15:0] out_rgb;
	output reg out_error;
	reg v0;
	reg v1;
	reg v2;
	reg r0;
	reg r1;
	reg r2;
	reg [9:0] u0;
	reg [9:0] u1;
	reg [9:0] u2;
	reg [8:0] vv0;
	reg [8:0] vv1;
	reg [8:0] vv2;
	reg [7:0] y0;
	reg signed [8:0] cb0;
	reg signed [8:0] cr0;
	reg h0;
	reg h1;
	reg e0;
	reg e1;
	reg e2;
	reg [15:0] hud0;
	reg [15:0] hud1;
	reg [15:0] rgb2;
	reg signed [18:0] red1;
	reg signed [18:0] green1;
	reg signed [18:0] blue1;
	reg signed [18:0] red_calc;
	reg signed [18:0] green_calc;
	reg signed [18:0] blue_calc;
	function automatic signed [8:0] sv2v_cast_9_signed;
		input reg signed [8:0] inp;
		sv2v_cast_9_signed = inp;
	endfunction
	function automatic signed [31:0] sv2v_cast_32_signed;
		input reg signed [31:0] inp;
		sv2v_cast_32_signed = inp;
	endfunction
	function automatic signed [8:0] interp;
		input reg [7:0] a;
		input reg [7:0] b;
		input reg [7:0] c;
		input reg [7:0] d;
		input reg oddx;
		input reg oddy;
		integer top;
		integer bottom;
		begin
			top = sv2v_cast_32_signed(a);
			bottom = sv2v_cast_32_signed(c);
			if (oddx) begin
				top = ((top + sv2v_cast_32_signed(b)) + 1) / 2;
				bottom = ((bottom + sv2v_cast_32_signed(d)) + 1) / 2;
			end
			if (oddy)
				top = ((top + bottom) + 1) / 2;
			interp = sv2v_cast_9_signed(top - 128);
		end
	endfunction
	function automatic signed [4:0] sv2v_cast_5_signed;
		input reg signed [4:0] inp;
		sv2v_cast_5_signed = inp;
	endfunction
	function automatic [4:0] clamp5;
		input reg signed [18:0] value;
		if (value < 0)
			clamp5 = 0;
		else if (value > 255)
			clamp5 = 31;
		else
			clamp5 = sv2v_cast_5_signed(value >>> 3);
	endfunction
	function automatic signed [5:0] sv2v_cast_6_signed;
		input reg signed [5:0] inp;
		sv2v_cast_6_signed = inp;
	endfunction
	function automatic [5:0] clamp6;
		input reg signed [18:0] value;
		if (value < 0)
			clamp6 = 0;
		else if (value > 255)
			clamp6 = 63;
		else
			clamp6 = sv2v_cast_6_signed(value >>> 2);
	endfunction
	function automatic signed [18:0] sv2v_cast_19_signed;
		input reg signed [18:0] inp;
		sv2v_cast_19_signed = inp;
	endfunction
	always @(*) begin
		if (_sv2v_0)
			;
		r2 = !v2 || out_ready;
		r1 = !v1 || r2;
		r0 = !v0 || r1;
		in_ready = (r0 && !rst) && !abort_i;
		out_valid = (v2 && !rst) && !abort_i;
		out_u = u2;
		out_v = vv2;
		out_rgb = rgb2;
		out_error = e2;
		red_calc = sv2v_cast_19_signed($signed({1'b0, y0})) + (((sv2v_cast_19_signed($signed(cr0)) * 19'sd359) + 19'sd128) >>> 8);
		green_calc = sv2v_cast_19_signed($signed({1'b0, y0})) - ((((sv2v_cast_19_signed($signed(cb0)) * 19'sd88) + (sv2v_cast_19_signed($signed(cr0)) * 19'sd183)) + 19'sd128) >>> 8);
		blue_calc = sv2v_cast_19_signed($signed({1'b0, y0})) + (((sv2v_cast_19_signed($signed(cb0)) * 19'sd454) + 19'sd128) >>> 8);
	end
	always @(posedge clk)
		if (rst || abort_i) begin
			v0 <= 0;
			v1 <= 0;
			v2 <= 0;
			u0 <= 0;
			u1 <= 0;
			u2 <= 0;
			vv0 <= 0;
			vv1 <= 0;
			vv2 <= 0;
			y0 <= 0;
			cb0 <= 0;
			cr0 <= 0;
			h0 <= 0;
			h1 <= 0;
			e0 <= 0;
			e1 <= 0;
			e2 <= 0;
			hud0 <= 0;
			hud1 <= 0;
			rgb2 <= 0;
			red1 <= 0;
			green1 <= 0;
			blue1 <= 0;
		end
		else begin
			if (r0) begin
				v0 <= in_valid;
				if (in_valid) begin
					u0 <= in_u;
					vv0 <= in_v;
					y0 <= in_y;
					cb0 <= interp(in_cb00, in_cb10, in_cb01, in_cb11, in_u[0], in_v[0]);
					cr0 <= interp(in_cr00, in_cr10, in_cr01, in_cr11, in_u[0], in_v[0]);
					h0 <= in_hud_hit;
					hud0 <= in_hud;
					e0 <= in_error;
				end
			end
			if (r1) begin
				v1 <= v0;
				if (v0) begin
					u1 <= u0;
					vv1 <= vv0;
					h1 <= h0;
					hud1 <= hud0;
					e1 <= e0;
					red1 <= red_calc;
					green1 <= green_calc;
					blue1 <= blue_calc;
				end
			end
			if (r2) begin
				v2 <= v1;
				if (v1) begin
					u2 <= u1;
					vv2 <= vv1;
					e2 <= e1;
					rgb2 <= (h1 ? hud1 : {clamp5(red1), clamp6(green1), clamp5(blue1)});
				end
			end
		end
	initial _sv2v_0 = 0;
endmodule
module cu77_render_sim (
	clk,
	rst,
	abort_i,
	desc_valid,
	desc_ready,
	desc_generation,
	desc_frame_id,
	desc_bank,
	finish_valid,
	finish_ready,
	active,
	aborted,
	error,
	error_code,
	active_generation,
	active_frame_id,
	prefetch_valid,
	prefetch_ready,
	prefetch_index,
	prefetch_done_valid,
	prefetch_done_ready,
	prefetch_done_index,
	consume_valid,
	consume_ready,
	consume_index,
	prefetched_count,
	consumed_count,
	mem_req_valid,
	mem_req_ready,
	mem_req_addr,
	mem_rsp_valid,
	mem_rsp_ready,
	mem_rsp_data,
	mem_rsp_last,
	mem_rsp_error,
	pixel_req_valid,
	pixel_req_ready,
	pixel_u,
	pixel_v,
	rgb_valid,
	rgb_ready,
	rgb_u,
	rgb_v,
	rgb_data,
	rgb_error,
	read_commands,
	read_words,
	pixel_queries,
	cache_misses,
	pixel_inflight
);
	input wire clk;
	input wire rst;
	input wire abort_i;
	input wire desc_valid;
	output wire desc_ready;
	input wire [63:0] desc_generation;
	input wire [31:0] desc_frame_id;
	input wire [1:0] desc_bank;
	input wire finish_valid;
	output wire finish_ready;
	output wire active;
	output wire aborted;
	output wire error;
	output wire [7:0] error_code;
	output wire [63:0] active_generation;
	output wire [31:0] active_frame_id;
	input wire prefetch_valid;
	output wire prefetch_ready;
	input wire [6:0] prefetch_index;
	output wire prefetch_done_valid;
	input wire prefetch_done_ready;
	output wire [6:0] prefetch_done_index;
	input wire consume_valid;
	output wire consume_ready;
	input wire [6:0] consume_index;
	output wire [6:0] prefetched_count;
	output wire [6:0] consumed_count;
	output wire mem_req_valid;
	input wire mem_req_ready;
	output wire [23:0] mem_req_addr;
	input wire mem_rsp_valid;
	output wire mem_rsp_ready;
	input wire [15:0] mem_rsp_data;
	input wire mem_rsp_last;
	input wire mem_rsp_error;
	input wire pixel_req_valid;
	output wire pixel_req_ready;
	input wire [9:0] pixel_u;
	input wire [8:0] pixel_v;
	output wire rgb_valid;
	input wire rgb_ready;
	output wire [9:0] rgb_u;
	output wire [8:0] rgb_v;
	output wire [15:0] rgb_data;
	output wire rgb_error;
	output wire [31:0] read_commands;
	output wire [31:0] read_words;
	output wire [31:0] pixel_queries;
	output wire [31:0] cache_misses;
	output reg [3:0] pixel_inflight;
	wire cache_desc_ready;
	wire cache_finish_ready;
	wire cache_consume_ready;
	wire cache_pixel_ready;
	wire px_valid;
	wire px_ready;
	wire px_error;
	wire px_hud_hit;
	wire [9:0] px_u;
	wire [8:0] px_v;
	wire [7:0] px_y;
	wire [7:0] cb00;
	wire [7:0] cb10;
	wire [7:0] cb01;
	wire [7:0] cb11;
	wire [7:0] cr00;
	wire [7:0] cr10;
	wire [7:0] cr01;
	wire [7:0] cr11;
	wire [15:0] px_hud;
	wire pipe_empty;
	wire request_fire;
	wire response_fire;
	assign pipe_empty = pixel_inflight == 0;
	assign desc_ready = cache_desc_ready && pipe_empty;
	assign finish_ready = cache_finish_ready && pipe_empty;
	assign consume_ready = cache_consume_ready && pipe_empty;
	assign pixel_req_ready = cache_pixel_ready && !finish_valid;
	assign request_fire = pixel_req_valid && pixel_req_ready;
	assign response_fire = rgb_valid && rgb_ready;
	always @(posedge clk)
		if (rst || abort_i)
			pixel_inflight <= 0;
		else
			case ({request_fire, response_fire})
				2'b10: pixel_inflight <= pixel_inflight + 1'b1;
				2'b01: pixel_inflight <= pixel_inflight - 1'b1;
				default:
					;
			endcase
	cu77_direct_cache cache(
		.clk(clk),
		.rst(rst),
		.abort_i(abort_i),
		.desc_valid(desc_valid && pipe_empty),
		.desc_ready(cache_desc_ready),
		.desc_generation(desc_generation),
		.desc_frame_id(desc_frame_id),
		.desc_bank(desc_bank),
		.finish_valid(finish_valid && pipe_empty),
		.finish_ready(cache_finish_ready),
		.active(active),
		.aborted(aborted),
		.error(error),
		.error_code(error_code),
		.active_generation(active_generation),
		.active_frame_id(active_frame_id),
		.prefetch_valid(prefetch_valid),
		.prefetch_ready(prefetch_ready),
		.prefetch_index(prefetch_index),
		.prefetch_done_valid(prefetch_done_valid),
		.prefetch_done_ready(prefetch_done_ready),
		.prefetch_done_index(prefetch_done_index),
		.consume_valid(consume_valid && pipe_empty),
		.consume_ready(cache_consume_ready),
		.consume_index(consume_index),
		.prefetched_count(prefetched_count),
		.consumed_count(consumed_count),
		.mem_req_valid(mem_req_valid),
		.mem_req_ready(mem_req_ready),
		.mem_req_addr(mem_req_addr),
		.mem_rsp_valid(mem_rsp_valid),
		.mem_rsp_ready(mem_rsp_ready),
		.mem_rsp_data(mem_rsp_data),
		.mem_rsp_last(mem_rsp_last),
		.mem_rsp_error(mem_rsp_error),
		.pixel_req_valid(pixel_req_valid && !finish_valid),
		.pixel_req_ready(cache_pixel_ready),
		.pixel_u(pixel_u),
		.pixel_v(pixel_v),
		.pixel_rsp_valid(px_valid),
		.pixel_rsp_ready(px_ready),
		.pixel_rsp_u(px_u),
		.pixel_rsp_v(px_v),
		.pixel_y(px_y),
		.cb00(cb00),
		.cb10(cb10),
		.cb01(cb01),
		.cb11(cb11),
		.cr00(cr00),
		.cr10(cr10),
		.cr01(cr01),
		.cr11(cr11),
		.pixel_hud_hit(px_hud_hit),
		.pixel_hud(px_hud),
		.pixel_rsp_error(px_error),
		.read_commands(read_commands),
		.read_words(read_words),
		.pixel_queries(pixel_queries),
		.cache_misses(cache_misses)
	);
	cu77_yuv_rgb converter(
		.clk(clk),
		.rst(rst),
		.abort_i(abort_i),
		.in_valid(px_valid),
		.in_ready(px_ready),
		.in_u(px_u),
		.in_v(px_v),
		.in_y(px_y),
		.in_cb00(cb00),
		.in_cb10(cb10),
		.in_cb01(cb01),
		.in_cb11(cb11),
		.in_cr00(cr00),
		.in_cr10(cr10),
		.in_cr01(cr01),
		.in_cr11(cr11),
		.in_hud_hit(px_hud_hit),
		.in_hud(px_hud),
		.in_error(px_error),
		.out_valid(rgb_valid),
		.out_ready(rgb_ready),
		.out_u(rgb_u),
		.out_v(rgb_v),
		.out_rgb(rgb_data),
		.out_error(rgb_error)
	);
endmodule