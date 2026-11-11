#!/usr/bin/env python3
"""Derive speculative packet RAM candidate and real paired-module wrapper."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'fpga/experiments/cu66-v128-padding/cs88_admission_v91i2a.sv'
OUT=ROOT/'fpga/experiments/cu66-v130-spec-read'
S=OLD.read_text()
OLD_BLOCK='''    assign memory_read_enable=stage_read_req || (replay_req && replay_ready);
    assign memory_read_address=stage_read_req ? fetch_addr[15:0] : replay_addr[15:0];'''
NEW_BLOCK='''    // Physical RAM reads are unowned until the unchanged request handshake.
    // Replay speculation clamps every invalid address to the first byte.
    assign memory_read_enable=(state==FETCH_REQ) || (state==FINISHED);
    assign memory_read_address=(state==FETCH_REQ) ? fetch_addr[15:0] :
        ((replay_addr<32'd49152) ? replay_addr[15:0] : 16'd0);
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(memory_read_enable)
        assert(memory_read_address<16'd49152)else $fatal(1,"speculative RAM address out of bounds");
`endif'''
assert S.count(OLD_BLOCK)==1
cand=S.replace(OLD_BLOCK,NEW_BLOCK,1)
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'cs88_admission_v91i2a.sv').write_text(cand)
# Verification-only split: separate both top module names, share byte-exact helpers.
marker='module cu66_scale_tdp_v107'
a,b=S.split(marker,1); c,d=cand.split(marker,1); assert b==d
for name,source in [('admission_original',a),('admission_candidate',c)]:
    assert source.count('module cs88_admission_v91i2a (')==1
    (OUT/(name+'.sv')).write_text(source.replace('module cs88_admission_v91i2a (','module '+name+' (',1))
assert b.count('module cu66_mode_store_v107')==1
m,n=b.split('module cu66_mode_store_v107',1)
(OUT/'cu66_scale_tdp_v107.sv').write_text(marker+m)
(OUT/'cu66_mode_store_v107.sv').write_text('module cu66_mode_store_v107'+n)
header=a[a.index('module cs88_admission_v91i2a (')+len('module cs88_admission_v91i2a ('):a.index('\n);')]
ports=[]
for line in header.strip().splitlines():
    line=line.strip().rstrip(',')
    mo=re.fullmatch(r'(input|output) logic\s*(\[[^]]+\])?\s*(.+)',line)
    assert mo,line
    direction,width,names=mo.groups()
    for part in names.split(','):
        nm=re.fullmatch(r'\s*(\w+)\s*(\[[^]]+\])?\s*',part);assert nm,part
        ports.append((direction,width or '',nm.group(1),nm.group(2) or ''))
inputs=[x[2] for x in ports if x[0]=='input'];outputs=[x for x in ports if x[0]=='output']
lines=['module admission_pair (',header+',\n    output logic mismatch',' );']
for _,w,n,arr in outputs:
    lines.append(f'    logic {w} old_{n} {arr};')
    lines.append(f'    logic {w} new_{n} {arr};')
for inst in ('original','candidate'):
    prefix='old' if inst=='original' else 'new'
    conns=[f'.{name}({name})' for name in inputs]+[f'.{n}({prefix}_{n})' for _,_,n,_ in outputs]
    lines.append(f'    admission_{inst} {inst} ('+', '.join(conns)+');')
for _,w,n,arr in outputs:
    lines.append(f'    assign {n}=old_{n};')
checks=[]
for _,w,n,arr in outputs:
    if n=='replay_data':expr='(old_replay_rsp_valid && old_replay_data != new_replay_data)'
    elif n=='stage_read_data':expr='(old_stage_read_rsp && old_stage_read_data != new_stage_read_data)'
    elif arr:expr=' || '.join(f'(old_{n}[{i}] != new_{n}[{i}])' for i in range(3))
    else:expr=f'(old_{n} != new_{n})'
    checks.append(expr)
lines.append('    assign mismatch = '+' ||\n        '.join(checks)+';')
lines.append('endmodule\n')
(OUT/'admission_pair.sv').write_text('\n'.join(lines))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rec={'parent':str(OLD.relative_to(ROOT)),'parent_sha256':sha(OLD),'candidate_sha256':sha(OUT/'cs88_admission_v91i2a.sv'),
     'old_block':OLD_BLOCK,'new_block':NEW_BLOCK,'verification_output_names':[x[2] for x in outputs],
     'scope':'invalid replay_data and stage_read_data are intentionally valid-qualified; no other output exceptions',
     'not_promoted':True,'RTL_cycle_delta':0}
(OUT/'derivation.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
print('candidate prepared',len(inputs),'inputs',len(outputs),'outputs')
