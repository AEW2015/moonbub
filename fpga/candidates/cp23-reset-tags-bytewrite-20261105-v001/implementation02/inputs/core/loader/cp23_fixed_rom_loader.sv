// SPDX-License-Identifier: CERN-OHL-S-2.0
`timescale 1ns/1ps
`default_nettype none
// Restricted immutable fixture loader. No CSR/network/profile/publication path.
// Reset and cancellation are requests to stop, never proof of consumer drain.
module cp23_fixed_rom_loader (
    input wire clk,
    input wire reset,
    input wire local_start,
    input wire local_cancel,
    // Fresh low->high indication in WAIT_RELEASE only. The integrator must
    // prove current-owner consumer AND physical writers idle, including boot.
    input wire consumer_released,
    output wire start_valid,
    input wire start_ready,
    output wire payload_valid,
    input wire payload_ready,
    output wire [7:0] payload_byte,
    output wire payload_last,
    output wire abort_job,
    output wire busy,
    output wire waiting_release,
    output reg start_accepted,
    output reg start_rejected,
    output reg released_pulse,
    output reg consumer_started,
    output reg load_complete,
    output reg cancelled,
    output reg [31:0] bytes_sent,
    output reg [31:0] rejected_starts
);
    localparam integer FIXTURE_BYTES = 17412;
    localparam [2:0] IDLE=0, START=1, FETCH=2, HOLD=3, WAIT_RELEASE=4;
    reg [2:0] state;
    reg start_seen, release_seen, cancel_pending;
    reg [14:0] rom_index;
    (* rom_style="block" *) reg [7:0] rom [0:FIXTURE_BYTES-1];
    initial $readmemh("key.cp23.hex", rom);
    reg [7:0] rom_data;

    wire start_edge = local_start && !start_seen;
    wire release_edge = consumer_released && !release_seen;
    assign busy = state != IDLE;
    assign waiting_release = state == WAIT_RELEASE;
    assign abort_job = reset || local_cancel || cancel_pending;
    assign start_valid = state == START && !reset && !local_cancel && !cancel_pending;
    assign payload_valid = state == HOLD && !reset && !local_cancel && !cancel_pending;
    // Never expose stale/uninitialized ROM data or a stale last marker.
    assign payload_byte = payload_valid ? rom_data : 8'd0;
    assign payload_last = payload_valid && rom_index == FIXTURE_BYTES-1;

    // Preserve the guarded AKD1 ROM pattern: a separate unreset data register,
    // fetch disabled throughout reset/cancel and while any byte is held.
    wire fixture_fetch_enable = !reset && !local_cancel && !cancel_pending &&
                                state == FETCH && rom_index < FIXTURE_BYTES;
    always @(posedge clk)
        if (fixture_fetch_enable) rom_data <= rom[rom_index];

    always @(posedge clk) begin
        if (reset) begin
            state <= WAIT_RELEASE;
            start_seen <= local_start;
            release_seen <= consumer_released;
            cancel_pending <= 1'b1;
            rom_index <= 0;
            start_accepted <= 0;
            start_rejected <= 0;
            released_pulse <= 0;
            consumer_started <= 0;
            load_complete <= 0;
            cancelled <= 1;
            bytes_sent <= 0;
            rejected_starts <= 0;
        end else begin
            start_seen <= local_start;
            release_seen <= consumer_released;
            start_accepted <= 0;
            start_rejected <= 0;
            released_pulse <= 0;
            // A positive simultaneous release may retire ownership, but must
            // not erase the fact that CANCEL was requested for this job.
            if (local_cancel && state != IDLE) cancelled <= 1;
            // Edges while busy/cancelling are rejected, never queued. A held
            // START cannot retrigger after release or after a local reset.
            if (start_edge && (state != IDLE || local_cancel)) begin
                start_rejected <= 1;
                if (rejected_starts != 32'hffffffff)
                    rejected_starts <= rejected_starts + 1'b1;
            end
            if (state == WAIT_RELEASE && release_edge) begin
                state <= IDLE;
                cancel_pending <= 0;
                consumer_started <= 0;
                released_pulse <= 1;
            end else if (local_cancel && state != IDLE) begin
                state <= WAIT_RELEASE;
                cancel_pending <= 1;
                cancelled <= 1;
            end else begin
                case (state)
                    IDLE: if (start_edge && !local_cancel) begin
                        state <= START;
                        rom_index <= 0;
                        bytes_sent <= 0;
                        start_accepted <= 1;
                        consumer_started <= 0;
                        load_complete <= 0;
                        cancelled <= 0;
                        cancel_pending <= 0;
                    end
                    START: if (start_valid && start_ready) begin
                        consumer_started <= 1;
                        state <= FETCH;
                    end
                    FETCH: if (fixture_fetch_enable) state <= HOLD;
                    HOLD: if (payload_valid && payload_ready) begin
                        bytes_sent <= bytes_sent + 1'b1;
                        if (rom_index == FIXTURE_BYTES-1) begin
                            load_complete <= 1;
                            state <= WAIT_RELEASE;
                        end else begin
                            rom_index <= rom_index + 1'b1;
                            state <= FETCH;
                        end
                    end
                    WAIT_RELEASE: begin end
                    default: begin
                        state <= WAIT_RELEASE;
                        cancel_pending <= 1;
                        cancelled <= 1;
                    end
                endcase
            end
        end
    end
endmodule
`default_nettype wire
