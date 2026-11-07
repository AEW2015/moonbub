"""Wire the frozen live producer and RGB reader to one physical SDRAM service."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
FABRIC=ROOT/'fpga/experiments/cu66-v91l-scratch-service'
def ports(path):
 s=path.read_text();s=s[re.search(r'\)\s*\(',s).end():];s=s[:s.index(');')]
 result=[];direction=typ=width=''
 for part in s.split(','):
  part=part.strip()
  m=re.match(r'(input|output|inout)\s+(logic(?: signed)?|wire|integer)\s*(.*)',part,re.S)
  if m:direction,typ,part=m.groups();width=''
  m=re.match(r'(\[[^]]+\])\s*(.*)',part,re.S)
  if m:width,part=m.groups()
  m=re.fullmatch(r'(\w+)(\s*\[[^]]+\])?',part)
  assert m,(path,part)
  result.append((direction,typ,width,m[1],m[2] or ''))
 return result

def decl(p,name=None,direction=None):
 d,t,w,n,a=p;return f'{direction or d} {t} {w} {name or n}{a}'.replace('  ',' ')
rows=ports(ROOT/'fpga/experiments/cu66-v91l-rows/cs88_rows_v91l.sv')
rgb=ports(ROOT/'fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_tiled.sv')
fabric=ports(FABRIC/'scratch_shared_timed.sv')
connections={}
for p in fabric:
 n=p[3]
 if n in ('clk','power_on_reset'):connections[n]=n
 elif n=='scratch_reset':connections[n]='reset'
 elif n=='scratch_cancel':connections[n]='abort_packet||transaction_faulted||stage_cancel'
 elif n.startswith(('scratch_req_','scratch_rsp_')):connections[n]='mem_'+n[8:]
 elif n=='ref_reset':connections[n]='reset'
 elif n=='ref_cancel':connections[n]='abort_packet||transaction_faulted'
 elif n.startswith(('ref_req_','ref_rsp_')):connections[n]=n
 elif n=='accepted_valid':connections[n]='v_reference_bank_valid'
 elif n=='accepted_bank':connections[n]='v_reference_bank'
 elif n=='accepted_fid':connections[n]='v_accepted_fid'
 elif n=='accepted_generation':connections[n]='v_accepted_generation'
 elif n=='wr_reset':connections[n]='reset'
 elif n=='wr_cancel':connections[n]='abort_packet||transaction_faulted'
 elif n=='wr_req_valid':connections[n]='candidate_req_valid&&display_candidate_allowed'
 elif n=='wr_req_ready':connections[n]='guard_candidate_ready'
 elif n.startswith(('wr_req_','wr_rsp_')):connections[n]='candidate_'+n[3:]
 elif n in ('rd_reset','rd_cancel'):connections[n]='rgb_'+n[3:]
 elif n.startswith(('rd_req_','rd_rsp_')):connections[n]='rgb_mem_'+n[3:]
 else:connections[n]='fabric_'+n
out=[decl(p,direction='output' if p[3].startswith(('candidate_','mem_')) or p[3]=='ref_req_ready' or p[3].startswith('ref_rsp_') and p[3]!='ref_rsp_ready' else None) for p in rows]
for p in rgb:
 n=p[3]
 if n in ('clk','power_on_reset'):continue
 # Physical return fields are outputs of the joined top, never actor inputs.
 out.append(decl(p,'rgb_'+n,'output' if n.startswith('mem_') else None))
for p in fabric:
 if connections[p[3]].startswith('fabric_'):out.append(decl(p,connections[p[3]]))
out.extend(['output logic display_active','output logic display_draining','output logic display_effective_drained','output logic display_candidate_allowed','output logic display_alias_fault','output logic display_start_rejected','output logic [1:0] display_bank','output logic [31:0] display_epoch','output logic [31:0] display_fid','output logic [63:0] display_generation','output logic [7:0] display_terminal_error','output logic [1:0] display_idle_samples','output logic display_terminal_seen','output logic display_engine_start'])
s='`timescale 1ns/1ps\n`default_nettype none\nmodule overlap_live #(parameter real T_AC_NS=2.0)(\n '+',\n '.join(out)+'\n);\n'
s+=' wire guard_engine_ready,guard_candidate_ready;\n assign candidate_req_ready=guard_candidate_ready&&display_candidate_allowed;\n'
s+=' cs88_rows_v91l #(.ROW_WRITES(1\'b1)) live(\n '+',\n '.join('.'+p[3]+'('+('display_effective_drained' if p[3]=='present_drained' else p[3])+')' for p in rows)+'\n );\n'
s+=' canonical_rgb565_tiled #(.RETAIN_ROWS(1\'b1)) rgb(\n '+',\n '.join('.'+p[3]+'('+('display_engine_start' if p[3]=='start' else 'guard_engine_ready' if p[3]=='start_ready' else '(rgb_reset||reset)' if p[3]=='reset' else ('' if p[3] in ('clk','power_on_reset') else 'rgb_')+p[3])+')' for p in rgb)+'\n );\n'
s+=' scratch_shared_timed #(.T_AC_NS(T_AC_NS)) memory(\n '+',\n '.join('.'+p[3]+'('+connections[p[3]]+')' for p in fabric)+'\n );\n'
s+=' display_overlap_lease display_lease(\n .clk(clk),.power_on_reset(power_on_reset),.reset(reset||rgb_reset),.cancel(rgb_cancel),\n .start_valid(rgb_start),.start_ready(rgb_start_ready),.start_epoch(rgb_start_epoch),.start_generation(rgb_start_generation),.start_bank(rgb_start_bank),\n .accepted_valid(v_reference_bank_valid),.accepted_bank(v_reference_bank),.accepted_fid(v_accepted_fid),.accepted_generation(v_accepted_generation),\n .engine_start_ready(guard_engine_ready),.engine_start(display_engine_start),.engine_busy(rgb_busy),.engine_draining(rgb_draining),.engine_done(rgb_done),.engine_error(rgb_error),\n .reader_busy(rgb_reader_busy||fabric_rd_busy),.reader_pending(rgb_reader_pending||fabric_rd_pending),.mux_owner(fabric_mux_owner),.external_drained(present_drained),\n .candidate_valid(candidate_req_valid),.candidate_bank(candidate_req_bank),.candidate_allowed(display_candidate_allowed),.alias_fault(display_alias_fault),\n .start_rejected(display_start_rejected),.active(display_active),.draining(display_draining),.lease_bank(display_bank),.lease_epoch(display_epoch),.lease_fid(display_fid),.lease_generation(display_generation),\n .terminal_error(display_terminal_error),.effective_drained(display_effective_drained),.idle_samples(display_idle_samples),.terminal_seen(display_terminal_seen));\n'
s+='endmodule\n`default_nettype wire\n'
(AREA/'overlap_live.sv').write_text(s)
print('OVERLAP_LIVE_WRAPPER_GENERATED')
