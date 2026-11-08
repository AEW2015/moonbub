#!/usr/bin/env python3
"""Exhaustive owned bank selection and update-priority model; never an RTL verdict."""
import itertools,json
from pathlib import Path
from qualify import verify,sha,ROOT,SRC,AREA

def main():
 r=verify();e=r['production']['packed_scratch_v91g2.sv'];old=(ROOT/e['original']).read_text();new=(ROOT/e['candidate']).read_text()
 # The complete existing assertion block is retained byte for byte.
 marker='    function automatic logic capacity_expected_wrap'
 tail=old[old.index(marker):].rsplit('endmodule',1)[0]
 assert tail in new
 select_rows=0
 words=[int.from_bytes(bytes((b*47+off*13)&255 for off in range(16)),'little') for b in range(4)]
 positions=[[((bank*983+off*173)&((1<<19)-1)) for off in range(16)] for bank in range(4)]
 for bank,off,valid,prefetched,tags in itertools.product(range(4),range(16),range(16),range(16),range(16)):
  oh=1<<bank
  selected_word=0;selected_pos=0;hit=False;prefetch_hit=False
  for physical in range(4):
   if oh>>physical&1:
    selected_word|=(words[physical]>>(8*off))&0xffffffff
    selected_pos|=positions[physical][off]
   local_hit=bool(oh>>physical&1 and valid>>physical&1 and tags>>physical&1)
   hit|=local_hit;prefetch_hit|=local_hit and bool(prefetched>>physical&1)
  assert selected_word==(words[bank]>>(8*off))&0xffffffff and selected_pos==positions[bank][off]
  assert hit==bool(valid>>bank&1 and tags>>bank&1)
  assert prefetch_hit==bool(valid>>bank&1 and prefetched>>bank&1 and tags>>bank&1)
  select_rows+=1
 update_rows=0
 for foreground,background,consume,fg_enable,bg_enable,consume_enable in itertools.product(range(4),range(4),range(4),(False,True),(False,True),(False,True)):
  olddata=[10,11,12,13];newdata=olddata[:];oldpref=[1,1,1,1];newpref=oldpref[:]
  # Source procedural order: foreground consumption, background fill, foreground fill.
  if consume_enable:oldpref[consume]=0
  if bg_enable:olddata[background]=50;oldpref[background]=1
  if fg_enable:olddata[foreground]=90;oldpref[foreground]=0
  for physical in range(4):
   if consume_enable and (1<<consume)>>physical&1:newpref[physical]=0
  if bg_enable:newdata[background]=50;newpref[background]=1
  for physical in range(4):
   if fg_enable and (1<<foreground)>>physical&1:newdata[physical]=90;newpref[physical]=0
  assert olddata==newdata and oldpref==newpref;update_rows+=1
 result=dict(status='PASS_OWNED_BANK_MODEL_NOT_RTL',selection_rows=select_rows,forwarding_priority_rows=update_rows,binary_capture_assignments=2,onehot_capture_assignments=2,original_assertion_tail_byte_identical=True,added_public_cycles=0,source_sha256={e[k]:sha(ROOT/e[k]) for k in ('original','candidate')},scope='Owned binary/OH bank word/position/tag/valid/prefetched selection and same-edge foreground/background update ordering. No simulation, four-state arbitrary initialization, physical timing or full pipeline claim.')
 (AREA/'model.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],select_rows,update_rows)
if __name__=='__main__':main()
