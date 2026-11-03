#!/usr/bin/env python3
"""Make a locally scoped synchronous-RAM inference candidate from pinned RTL."""
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text()
changes = [
    ('output reg read_ready,output reg read_valid,output reg read_error,output reg[7:0] read_data,',
     'output reg read_ready,output reg read_valid,output reg read_error,output wire[7:0] read_data,'),
    ('reg owner_bank;reg[15:0] owner_length;', '''reg owner_bank;reg[15:0] owner_length;
 reg [7:0] bank0_data,bank1_data;
 reg last_read_bank,have_read;
 assign read_data=have_read ? (last_read_bank ? bank1_data : bank0_data) : 8'd0;
 // The inferred RAM read ports have no reset; only the output validity and
 // selection state reset. Exactly one bank is read on an accepted request.
 wire ram_read=read_req && read_ready && read_addr<owner_length &&
               {16'd0,read_addr}<CAP_BYTES && !reset && !decode_done &&
               !decode_fail && !decode_grant;
 always @(posedge clk) begin
  if(ram_read && !owner_bank) bank0_data<=compressed0[read_addr];
  if(ram_read && owner_bank) bank1_data<=compressed1[read_addr];
 end'''),
    ('read_error<=0;read_data<=0;owner_bank<=0;owner_length<=0;',
     'read_error<=0;last_read_bank<=0;have_read<=0;owner_bank<=0;owner_length<=0;'),
    ('if(owner_bank)read_data<=compressed1[read_addr];else read_data<=compressed0[read_addr];',
     'last_read_bank<=owner_bank;have_read<=1;'),
]
for before, after in changes:
    if source.count(before) != 1:
        raise SystemExit('source anchor mismatch: '+before)
    source=source.replace(before, after)
Path(sys.argv[2]).write_text(source)
