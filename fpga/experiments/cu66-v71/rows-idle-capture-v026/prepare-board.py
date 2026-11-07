from pathlib import Path
import hashlib,json,shutil
root=Path('C:/mb70');p=Path(__file__).resolve().parent;old=root/'dy71-v025-20261107-v003';out=root/'dy71-v026-20261107-v001';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert json.loads((p/'pair01/result.json').read_text())['status']=='PASS_OBSERVED_OLD_NEW_ROWS_AND_AUTHORITATIVE_PAYLOAD'
proof=json.loads((p/'proof02/result.json').read_text());assert proof['status']=='PASS_EXACT_CONTROL_PROJECTION_AND_OWNED_PAYLOAD_INDUCTION' and proof['source_sha256']['cu71_tile_rows.sv']==sha(p/'cu71_tile_rows.sv')
out.mkdir();shutil.copytree(old/'inputs',out/'inputs');freeze=json.loads((old/'source-freeze.json').read_text());oldrow='fpga/experiments/cu66-v71/rows/cu71_tile_rows.sv';row=p.relative_to(root).as_posix()+'/cu71_tile_rows.sv';(out/'inputs'/row).parent.mkdir(parents=True);shutil.copyfile(p/'cu71_tile_rows.sv',out/'inputs'/row);freeze[row]=sha(out/'inputs'/row)
platform='fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v004/constraints/platform.xdc';q=out/'inputs'/platform;s=q.read_text();assert '4459373d'in s;q.write_text(s.replace('4459373d','4459373e'));freeze[platform]=sha(q)
(out/'source-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n');sel=json.loads((old/'selection.json').read_text());sel['sources']=[row if n==oldrow else n for n in sel['sources']];sel['source_sha256'].pop(oldrow);sel['source_sha256'][row]=freeze[row];sel['frozen_inputs_sha256']=freeze;sel['USERID_USR_ACCESS']='4459373e';sel['board_revision']='V026';sel['parent_same_bulk_rtl']=str(old);sel['row_capture_proof']=dict(pair=sha(p/'pair01/result.json'),control_projection=sha(p/'proof02/result.json'),derivation=sha(p/'derivation.json'));(out/'selection.json').write_text(json.dumps(sel,indent=2)+'\n')
for n in ['synth.tcl','implementation.tcl','run-phase.py']:
 s=(old/n).read_text().replace('V025_','V026_').replace('V025 synthesis','V026 synthesis')
 if n=='synth.tcl':
  assert s.count(oldrow)==1;s=s.replace(oldrow,row)
 (out/n).write_text(s)
(out/'parent-and-proof-binding.json').write_text(json.dumps(dict(parent=str(old),parent_source_freeze_sha256=sha(old/'source-freeze.json'),row_source_sha256=sha(p/'cu71_tile_rows.sv'),proof=proof,firmware='Same V43 release-bulk-hud-v002; ABI2/cap1f/HBU1 unchanged',clocks_pins_delays_and_SDRAM_budgets_unchanged=True,hardware=False),indent=2)+'\n')
print('V026_FROZEN_NO_HARDWARE',str(out))
