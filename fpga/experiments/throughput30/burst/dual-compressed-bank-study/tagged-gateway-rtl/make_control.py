#!/usr/bin/env python3
"""Derive experimental controller with the accepted bank exposed."""
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
changes=[('module two_bank_control #(', 'module two_bank_control_gateway #('),
 ('output reg begin_accept,output reg reject,output reg [3:0] reject_reason,',
  'output reg begin_accept,output reg begin_accept_bank,output reg commit_accept,output reg abort_accept,output reg reject,output reg [3:0] reject_reason,'),
 ('begin_accept<=0;reject<=0;reject_reason<=0;mem_we<=0;mem_bank<=0;',
  'begin_accept<=0;begin_accept_bank<=0;commit_accept<=0;abort_accept<=0;reject<=0;reject_reason<=0;mem_we<=0;mem_bank<=0;'),
 ('begin_accept<=0;reject<=0;reject_reason<=0;mem_we<=0;decode_grant<=0;present<=0;',
  'begin_accept<=0;commit_accept<=0;abort_accept<=0;reject<=0;reject_reason<=0;mem_we<=0;decode_grant<=0;present<=0;'),
 ('recv_crc<=32\'hffffffff;begin_accept<=1;',
  'recv_crc<=32\'hffffffff;begin_accept<=1;begin_accept_bank<=free_bank;'),
 ('if(receiving)begin state[recv_bank]<=FREE;receiving<=0;rx_dropped<=rx_dropped+1;end\n    if(ingress_overflow)',
  'if(receiving)begin state[recv_bank]<=FREE;receiving<=0;rx_dropped<=rx_dropped+1;abort_accept<=1;end\n    if(ingress_overflow)'),
 ('receiving<=0;accepted_frames<=accepted_frames+1;end',
  'receiving<=0;accepted_frames<=accepted_frames+1;commit_accept<=1;end')]
for a,b in changes:
 if s.count(a)!=1:raise SystemExit('unexpected controller anchor '+a)
 s=s.replace(a,b)
Path(sys.argv[2]).write_text(s)
