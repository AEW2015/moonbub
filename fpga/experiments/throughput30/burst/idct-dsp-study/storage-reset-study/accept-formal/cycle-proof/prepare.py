from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
old='    ,output          inport_accept_o\n'
new='    ,output [15:0] audit_control_o\n    ,output          inport_accept_o\n'
if s.count(old)!=1: raise SystemExit('port anchor mismatch')
s=s.replace(old,new)
old='assign inport_accept_o = ~block_ready_q[block_wr_q];'
new='assign audit_control_o = {block_ready_q,block_wr_q,block_rd_q,rd_idx_q,rd_addr_q,state_q};\n'+old
if s.count(old)!=1: raise SystemExit('assignment anchor mismatch')
s=s.replace(old,new)
Path(sys.argv[2]).write_text(s)
