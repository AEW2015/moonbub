#!/usr/bin/env python3
"""Compose unchanged physical/reference paths and a cycle-equality control top."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
s=(ROOT/'fpga/experiments/cu66-v91l-scratch-service/scratch_shared_timed.sv').read_text()
s=s.replace('module scratch_shared_timed #(parameter real T_AC_NS=2.0,parameter integer POWERUP_CYCLES=30,REFRESH_CYCLES=750)', 'module tile_grant_shared_timed #(parameter real T_AC_NS=2.0,parameter integer POWERUP_CYCLES=30,REFRESH_CYCLES=750,REF_LINES=4,GAP_CYCLES=8)')
s=s.replace('output logic [31:0] scratch_write_requests,scratch_read_requests,scratch_write_words,scratch_read_words);', '''output logic [31:0] scratch_write_requests,scratch_read_requests,scratch_write_words,scratch_read_words,
 output logic [2:0] grant_lines,output logic [3:0] grant_gap,output logic grant_reserved,
 output logic [31:0] grant_groups,grant_continuations,grant_timeouts,grant_mismatches,
 output logic [31:0] grant_yields,grant_cancel_yields,grant_error_yields);''')
s=s.replace(' reader_client_mux mux(', ' tile_reader_mux #(.REF_LINES(REF_LINES),.GAP_CYCLES(GAP_CYCLES)) mux(')
s=s.replace('.mem_busy(rd_busy),', '''.mem_busy(rd_busy),
.grant_lines(grant_lines),.grant_gap(grant_gap),.grant_reserved(grant_reserved),
.grant_groups(grant_groups),.grant_continuations(grant_continuations),.grant_timeouts(grant_timeouts),
.grant_mismatches(grant_mismatches),.grant_yields(grant_yields),.grant_cancel_yields(grant_cancel_yields),.grant_error_yields(grant_error_yields),''')
(AREA/'tile_grant_shared_timed.sv').write_text(s)
src=(AREA/'tile_reader_mux.sv').read_text();start=src.index('module tile_reader_mux');header=src[start:src.index(');',start)+2].replace('module tile_reader_mux','module tile_mux_unit',1)
parts=header[header.index(')(')+2:header.rindex(');')].split(',');ports=[];direction=width=''
for part in parts:
 m=re.match(r'\s*(input|output)\s+logic\s*(.*)',part,re.S)
 if m:direction,part=m.groups();width=''
 m=re.match(r'\s*(\[[^]]+\])\s*(.*)',part,re.S)
 if m:width,part=m.groups()
 name=part.strip();assert re.fullmatch(r'\w+',name),name;ports.append((direction,width,name))
old=(ROOT/'fpga/experiments/cu66-v91l-reference-reader/reader_client_mux.sv').read_text();oldnames=set(re.findall(r'\b\w+\b',old[old.index('module reader_client_mux('):old.index(');')]))
original=[p for p in ports if p[2] in oldnames]
out='`timescale 1ns/1ps\n`default_nettype none\n'+header+'\n tile_reader_mux #(.REF_LINES(REF_LINES),.GAP_CYCLES(GAP_CYCLES)) dut(\n'+',\n'.join('.'+n+'('+n+')' for d,w,n in ports)+'\n);\n generate if(REF_LINES==1)begin: exact_control\n'
for d,w,n in original:
 if d=='output':out+='wire '+w+' old_'+n+';\n'
out+='reader_client_mux frozen(\n'+',\n'.join('.'+n+'('+('old_' if d=='output' else '')+n+')' for d,w,n in original)+'\n);\nalways_ff @(posedge clk)if(!power_on_reset)begin\n'
for d,w,n in original:
 if d=='output':out+='assert('+n+'==old_'+n+')else $fatal(1,"REF_LINES1 differs: '+n+'");\n'
out+='end\nend endgenerate\nendmodule\n`default_nettype wire\n'
(AREA/'tile_mux_unit.sv').write_text(out)
print('TILE_GRANT_WRAPPERS_GENERATED')
