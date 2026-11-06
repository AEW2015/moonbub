"""Derive the new system wrapper; frozen v70 sources are never edited."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2]
p=r/'fpga/experiments/cu66-v70/system/cu70_system.sv'
o=r/'fpga/experiments/cu66-v71/system';o.mkdir(parents=True,exist_ok=True)
f=o/'cu71_system.sv';assert not f.exists()
s=p.read_text();s=s.replace('module cu70_system #(','module cu71_system #(',1)
needle='    logic l_req_valid,l_req_ready,l_req_write,l_rsp_valid,l_rsp_ready,l_rsp_error;'
assert s.count(needle)==1
s=s.replace(needle,needle+'''
    // LCD traffic bypasses the scalar HUD/painter arbiter.
    logic lcd_req_valid,lcd_req_ready,lcd_rsp_valid,lcd_rsp_ready,lcd_rsp_error;
    logic [23:0] lcd_req_addr;logic [127:0] lcd_rsp_data;
    logic lcd_abort_i,lcd_busy,lcd_aborted;
    assign l_req_valid=1'b0;assign l_req_write=1'b0;
    assign l_req_addr=24'd0;assign l_req_data=16'd0;assign l_rsp_ready=1'b1;
''')
s=s.replace('    cu70_memory_system #(','    cu71_memory_system #(',1)
needle='        .cache_hits(memory_cache_hits),.cache_misses(memory_cache_misses),.completed_reads(memory_reads),.completed_writes(memory_writes),'
assert s.count(needle)==1
s=s.replace(needle,needle+'''
        .lcd_req_valid,.lcd_req_ready,.lcd_req_addr,.lcd_rsp_valid,.lcd_rsp_ready,
        .lcd_rsp_data,.lcd_rsp_error,.lcd_abort_i,.lcd_busy,.lcd_aborted,''')
s=s.replace('    cu70_scanout #(','    cu71_scanout #(',1)
needle='''        .aux_req_valid(l_req_valid),.aux_req_ready(l_req_ready),.aux_req_write(l_req_write),.aux_req_addr(l_req_addr),.aux_req_data(l_req_data),
        .aux_rsp_valid(l_rsp_valid),.aux_rsp_ready(l_rsp_ready),.aux_rsp_data(l_rsp_data),.aux_rsp_error(l_rsp_error),'''
assert s.count(needle)==1
s=s.replace(needle,'''        .lcd_req_valid,.lcd_req_ready,.lcd_req_addr,.lcd_rsp_valid,.lcd_rsp_ready,
        .lcd_rsp_data,.lcd_rsp_error,.lcd_abort_i,.lcd_busy,.lcd_aborted,''')
f.write_text('// CU71 successor: qualified memory backend and dedicated BL8 scanout.\n'+s,newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(o/'derivation.json').write_text(json.dumps(dict(parent=str(p),parent_sha256=sha(p),candidate_sha256=sha(f),scope='Structural memory/scanout port integration; owner, HUD permissions, painter and publication semantics unchanged; verification pending'),indent=2)+'\n')
print(f)
