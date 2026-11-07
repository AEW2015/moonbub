// Standalone behavioral research kernel. One physical symbol update engine;
// interleaved states do not imply two/four symbols per clock.
module rans_symbol (
    input  logic clk,
    input  logic rst,
    input  logic abort_job,
    input  logic [3:0] cfg_scale,
    input  logic cfg_valid,
    output logic cfg_ready,
    input  logic [4:0] cfg_addr,
    input  logic [10:0] cfg_frequency,
    input  logic [10:0] cfg_cumulative,
    input  logic init_valid,
    output logic init_ready,
    input  logic [1:0] init_lane,
    input  logic [31:0] init_state,
    input  logic start,
    input  logic [2:0] start_lanes,
    input  logic [1:0] start_models,
    input  logic [31:0] start_symbols,
    input  logic [31:0] start_bytes,
    input  logic byte_valid,
    output logic byte_ready,
    input  logic [7:0] byte_data,
    output logic out_valid,
    input  logic out_ready,
    output logic [3:0] out_symbol,
    output logic [1:0] out_lane,
    output logic [31:0] out_state,
    output logic [31:0] bytes_consumed,
    output logic [31:0] symbols_emitted,
    output logic done,
    output logic error,
    output logic [7:0] error_code
);
  localparam logic [31:0] LOWER = 32'h00800000;
  typedef enum logic [2:0] {IDLE, LOOKUP, UPDATE, RENORMALIZE, EMIT, FINISHED, FAILED} phase_t;
  phase_t phase;
  logic [10:0] frequency [0:31];
  logic [10:0] cumulative [0:31];
  logic [31:0] lane_state [0:3];
  logic [3:0] initial_mask;
  logic [5:0] configured;
  logic [11:0] expected_cumulative;
  logic [3:0] scale;
  logic [2:0] lanes;
  logic [1:0] models;
  logic [31:0] total_symbols, total_bytes;
  logic [31:0] working;
  logic [1:0] refills;
  logic [10:0] multiply_frequency;
  logic [23:0] multiply_quotient;
  logic [10:0] remainder;
  logic [34:0] product;
  logic [31:0] current, slot;
  logic [1:0] selected_lane;
  logic selected_model, found;
  logic [3:0] found_symbol;
  logic [10:0] found_frequency, found_cumulative;
  logic [11:0] config_sum, config_limit;
  logic terminal_ok;

  always_comb begin
    cfg_ready = phase == IDLE && !error && configured < 32;
    init_ready = phase == IDLE && !error;
    byte_ready = phase == RENORMALIZE && working < LOWER &&
                 bytes_consumed < total_bytes && refills < 2;
    out_valid = phase == EMIT;
    done = phase == FINISHED;
    config_sum = {1'b0, cfg_cumulative} + {1'b0, cfg_frequency};
    config_limit = 12'd1 << cfg_scale;
    selected_lane = lanes == 4 ? symbols_emitted[1:0] : {1'b0, symbols_emitted[0]};
    selected_model = models == 2 && symbols_emitted[0];
    current = lane_state[selected_lane];
    slot = current & ((32'd1 << scale) - 1);
    found = 0;
    found_symbol = 0;
    found_frequency = 0;
    found_cumulative = 0;
    for (int i = 0; i < 16; i++) begin
      if (frequency[{selected_model, 4'(i)}] != 0 &&
          slot >= {21'd0, cumulative[{selected_model, 4'(i)}]} &&
          slot < 32'(frequency[{selected_model, 4'(i)}]) +
                 32'(cumulative[{selected_model, 4'(i)}])) begin
        found = 1;
        found_symbol = 4'(i);
        found_frequency = frequency[{selected_model, 4'(i)}];
        found_cumulative = cumulative[{selected_model, 4'(i)}];
      end
    end
    // 24 x 11 is within a DSP48E1's operand widths. Mapping and routed fit
    // are deliberately unclaimed; no vendor primitive is instantiated here.
    product = multiply_quotient * multiply_frequency;
    terminal_ok = working == LOWER && bytes_consumed == total_bytes;
    for (int i = 0; i < 4; i++) begin
      if (i < int'(lanes) && 2'(i) != out_lane && lane_state[i] != LOWER)
        terminal_ok = 0;
    end
    out_state = working;
  end

  always_ff @(posedge clk) begin
    if (rst || abort_job) begin
      phase <= IDLE;
      initial_mask <= 0;
      configured <= 0;
      expected_cumulative <= 0;
      scale <= 0;
      lanes <= 0;
      models <= 0;
      total_symbols <= 0;
      total_bytes <= 0;
      working <= 0;
      refills <= 0;
      multiply_frequency <= 0;
      multiply_quotient <= 0;
      remainder <= 0;
      out_symbol <= 0;
      out_lane <= 0;
      bytes_consumed <= 0;
      symbols_emitted <= 0;
      error <= 0;
      error_code <= 0;
      for (int i = 0; i < 4; i++) lane_state[i] <= 0;
    end else begin
      case (phase)
        IDLE: begin
          if (cfg_valid || init_valid || start) begin
            if ((cfg_valid && init_valid) || (start && (cfg_valid || init_valid))) begin
              phase <= FAILED; error <= 1; error_code <= 1;
            end else if (cfg_valid) begin
              if (!cfg_ready || {1'b0, cfg_addr} != configured ||
                  !(cfg_scale == 8 || cfg_scale == 9 || cfg_scale == 10) ||
                  (configured != 0 && cfg_scale != scale) ||
                  {1'b0, cfg_cumulative} != expected_cumulative ||
                  config_sum > config_limit ||
                  (cfg_addr[3:0] == 15 && config_sum != config_limit)) begin
                phase <= FAILED; error <= 1; error_code <= 2;
              end else begin
                scale <= cfg_scale;
                frequency[cfg_addr] <= cfg_frequency;
                cumulative[cfg_addr] <= cfg_cumulative;
                configured <= configured + 1;
                expected_cumulative <= cfg_addr[3:0] == 15 ? 12'd0 : config_sum;
              end
            end else if (init_valid) begin
              if (initial_mask[init_lane] || init_state < LOWER || init_state[31]) begin
                phase <= FAILED; error <= 1; error_code <= 3;
              end else begin
                lane_state[init_lane] <= init_state;
                initial_mask[init_lane] <= 1;
              end
            end else if (start) begin
              if (!(start_lanes == 2 || start_lanes == 4) ||
                  !(start_models == 1 || start_models == 2) ||
                  configured != (start_models == 1 ? 16 : 32) ||
                  initial_mask != (start_lanes == 2 ? 4'b0011 : 4'b1111) ||
                  start_symbols > 5636096 || {1'b0, start_bytes} > ({1'b0, start_symbols} << 1)) begin
                phase <= FAILED; error <= 1; error_code <= 4;
              end else begin
                lanes <= start_lanes;
                models <= start_models;
                total_symbols <= start_symbols;
                total_bytes <= start_bytes;
                if (start_symbols == 0) begin
                  if (start_bytes != 0 || lane_state[0] != LOWER || lane_state[1] != LOWER ||
                      (start_lanes == 4 && (lane_state[2] != LOWER || lane_state[3] != LOWER))) begin
                    phase <= FAILED; error <= 1; error_code <= 5;
                  end else phase <= FINISHED;
                end else phase <= LOOKUP;
              end
            end
          end
        end
        LOOKUP: begin
          if (!found) begin
            phase <= FAILED; error <= 1; error_code <= 6;
          end else begin
            out_symbol <= found_symbol;
            out_lane <= selected_lane;
            multiply_frequency <= found_frequency;
            multiply_quotient <= 24'(current >> scale);
            remainder <= 11'(slot - {21'd0, found_cumulative});
            refills <= 0;
            phase <= UPDATE;
          end
        end
        UPDATE: begin
          if (product[34:32] != 0) begin
            phase <= FAILED; error <= 1; error_code <= 7;
          end else begin
            working <= product[31:0] + {21'd0, remainder};
            phase <= RENORMALIZE;
          end
        end
        RENORMALIZE: begin
          if (working >= LOWER) phase <= EMIT;
          else if (bytes_consumed == total_bytes || refills == 2) begin
            phase <= FAILED; error <= 1; error_code <= 8;
          end else if (byte_valid) begin
            working <= {working[23:0], byte_data};
            bytes_consumed <= bytes_consumed + 1;
            refills <= refills + 1;
          end
        end
        EMIT: if (out_ready) begin
          lane_state[out_lane] <= working;
          symbols_emitted <= symbols_emitted + 1;
          if (symbols_emitted + 1 == total_symbols) begin
            if (!terminal_ok) begin
              phase <= FAILED; error <= 1; error_code <= 9;
            end else phase <= FINISHED;
          end else phase <= LOOKUP;
        end
        default: begin end
      endcase
    end
  end
endmodule
