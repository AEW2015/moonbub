#!/usr/bin/env python3
"""Derive a mapper-only tiled bridge from the frozen four-credit bridge."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=Path(__file__).resolve().parent
BASE=ROOT/'fpga/experiments/cu66-v91l-writepipe/row_to_sdram.sv'
MAPPER=" // Canonical plane bytes become 8x8 tile-major; semantic HUD stays linear.\n // Constant division/modulo are combinational architecture, not routed timing proof.\n function automatic logic [19:0] physical_byte(input logic [19:0] logical_byte);\n  integer unsigned base,width,offset,y,x;\n  if(logical_byte>=20'd518400)return logical_byte;\n  if(logical_byte<20'd345600)begin base=0;width=720;end\n  else if(logical_byte<20'd432000)begin base=345600;width=360;end\n  else begin base=432000;width=360;end\n  offset=32'(logical_byte)-base;y=offset/width;x=offset%width;\n  return 20'(base+((y/8)*(width/8)+x/8)*64+(y%8)*8+x%8);\n endfunction\n wire [19:0] mapped_addr=physical_byte(req_addr);\n"
def main():
 src=BASE.read_text()
 edits=[dict(old=' logic [23:0] base_word;\n',new=' logic [23:0] base_word;\n'+MAPPER),dict(old="base_word<={req_bank,3'b000,req_addr[19:1]};",new="base_word<={req_bank,3'b000,mapped_addr[19:1]};")]
 for e in edits:
  assert src.count(e['old'])==1
  src=src.replace(e['old'],e['new'])
 extra=dict(old='   if(rsp_valid)assert(!word_pending);',new='   if(req_valid&&req_ready&&req_epoch!=0&&req_bank<3&&req_addr[2:0]==0&&req_addr<=560632)assert(mapped_addr[2:0]==0);\n   if(rsp_valid)assert(!word_pending);')
 assert src.count(extra['old'])==1
 src=src.replace(extra['old'],extra['new']);edits.append(extra)
 target=AREA/'row_to_sdram.sv';target.write_text(src)
 result=dict(schema='cu66-v91l-tiled-bridge-derivation-v1',baseline=str(BASE.relative_to(ROOT)),baseline_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),derived=str(target.relative_to(ROOT)),derived_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),replacements=edits,scope='Only canonical byte address mapping changed; logical identities, 4word credit limit, cancellation, bounds, warm reset and final idle ACK fence retained. Caller grants provisional bank; no role checks or physical fault detection added.')
 (AREA/'bridge-derivation.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
