#!/usr/bin/env python3
"""Instrument the existing self-checking bench to compare the two wrappers."""
from pathlib import Path
import sys

tb=Path(sys.argv[1]).read_text()
needle=' two_bank_storage dut(.*);'
replacement=''' two_bank_storage dut(.*);
 wire c_begin_accept,c_reject,c_decode_grant,c_decode_bank,c_present,c_front_valid,c_read_ready,c_read_valid,c_read_error;
 wire[3:0] c_reject_reason;wire[31:0] c_decode_id,c_front_id,c_accepted_frames,c_dropped_frames;
 wire[15:0] c_decode_length;wire[7:0] c_read_data;
 two_bank_storage_candidate candidate(
  .clk(clk),.reset(reset),.begin_valid(begin_valid),.begin_id(begin_id),.begin_length(begin_length),.begin_crc(begin_crc),
  .byte_valid(byte_valid),.byte_data(byte_data),.commit_valid(commit_valid),.abort_valid(abort_valid),.ingress_overflow(ingress_overflow),
  .begin_accept(c_begin_accept),.reject(c_reject),.reject_reason(c_reject_reason),
  .decode_request(decode_request),.decode_done(decode_done),.decode_fail(decode_fail),
  .decode_grant(c_decode_grant),.decode_bank(c_decode_bank),.decode_id(c_decode_id),.decode_length(c_decode_length),
  .read_req(read_req),.read_addr(read_addr),.read_ready(c_read_ready),.read_valid(c_read_valid),.read_error(c_read_error),.read_data(c_read_data),
  .vblank(vblank),.present(c_present),.front_valid(c_front_valid),.front_id(c_front_id),
  .accepted_frames(c_accepted_frames),.dropped_frames(c_dropped_frames));
 integer lockstep_cycles=0;
 always @(posedge clk) begin
  #2;
  if ({begin_accept,reject,reject_reason,decode_grant,decode_bank,decode_id,decode_length,
       read_ready,read_valid,read_error,read_data,present,front_valid,front_id,accepted_frames,dropped_frames} !==
      {c_begin_accept,c_reject,c_reject_reason,c_decode_grant,c_decode_bank,c_decode_id,c_decode_length,
       c_read_ready,c_read_valid,c_read_error,c_read_data,c_present,c_front_valid,c_front_id,c_accepted_frames,c_dropped_frames})
    $fatal(1,"lockstep output mismatch at cycle %0d",lockstep_cycles);
  lockstep_cycles=lockstep_cycles+1;
 end'''
if tb.count(needle)!=1:
    raise SystemExit('bench anchor mismatch')
tb=tb.replace(needle,replacement)
needle='  $display("TEST_PASS_BANK_STORAGE'
if tb.count(needle)!=1:
    raise SystemExit('pass marker anchor mismatch')
tb=tb.replace(needle,'  $display("LOCKSTEP_CHECKED_CYCLES=%0d",lockstep_cycles);\n'+needle)
Path(sys.argv[2]).write_text(tb)

candidate=Path(sys.argv[3]).read_text()
needle='module two_bank_storage #('
if candidate.count(needle)!=1:
    raise SystemExit('candidate module anchor mismatch')
Path(sys.argv[4]).write_text(candidate.replace(needle,'module two_bank_storage_candidate #('))
