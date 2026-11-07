"""Derive V025 image gates; preserve V023 checks and explicit inherited scope."""
from pathlib import Path
p=Path(__file__).resolve().parent
old=p.parent/'result-admission-system-v023'
s=(old/'image-gates.py').read_text()
s=s.replace("parent=root/'dy71-v023-20261106-v001'", "parent=root/'dy71-v025-20261107-v003'; inherited=root/'fpga/experiments/cu66-v71/result-admission-system-v023'")
s=s.replace("runpy.run_path(str(r/'check-source-binding.py'),run_name='__main__')", "runpy.run_path(str(inherited/'check-source-binding.py'),run_name='__main__')\n"+'''
# Inherit only unchanged decoder/system sources, never new control/pin behavior.
oldfreeze=json.loads((root/'dy71-v023-20261106-v001/source-freeze.json').read_text())
newfreeze=json.loads((parent/'source-freeze.json').read_text())
added=set(newfreeze)-set(oldfreeze)
expected_added={'fpga/experiments/cu66-v71/hud-bulk-v025/'+n for n in ['dy71_hud_bulk_v025.sv','dy71_local_control_bulk_v025.sv','cu71_bus_cdc_bulk_v025.sv','moonshine_top_dy71.sv']}
assert added==expected_added,(added,expected_added)
platform='fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v004/constraints/platform.xdc'
assert all(oldfreeze[n]==h for n,h in newfreeze.items() if n in oldfreeze and n!=platform),'Existing source/constraint changed'
assert (parent/'inputs'/platform).read_text()==(root/'dy71-v023-20261106-v001/inputs'/platform).read_text().replace('4459373b','4459373d'),'Platform differs beyond image identity'
for name in ['functional04','pins05','legacy05','xsim-vendor04']:
 report=json.loads((r/name/'result.json').read_text());assert report['status'].startswith('PASS_')
if a.mode=='emit':
 post=json.loads((r/'xsim-full-synth02/result.json').read_text());assert post['status']=='PASS_XSIM_POST_SYNTH_BULK_NATIVE_WORDS'
 assert post['netlist_sha256']==sha(parent/'bulk-funcsim.v')
''')
s=s.replace("oracle_helper['verify'](r,", "oracle_helper['verify'](inherited,")
s=s.replace("str(r/'check-components.py')", "str(inherited/'check-components.py')")
s=s.replace("d=r/('integration-'", "d=inherited/('integration-'")
s=s.replace('V023_NATIVE_LAB_IMAGE_V1','V025_NATIVE_LAB_IMAGE_V1').replace("USERID_USR_ACCESS='4459373b'", "USERID_USR_ACCESS='4459373d'")
s=s.replace("=='4459373b'", "=='4459373d'").replace("'0x4459373b'", "'0x4459373d'")
s=s.replace('moonbub-v023-lab.bit','moonbub-v025-lab.bit').replace('V023_LAB_BIT_EMITTED_NO_HARDWARE','V025_LAB_BIT_EMITTED_NO_HARDWARE').replace('V023_NATIVE_AUDIT_COMPLETE_NO_BIT','V025_NATIVE_AUDIT_COMPLETE_NO_BIT').replace("'v023-'+a.mode", "'v025-'+a.mode").replace('expected_identity=0x4459373b','expected_identity=0x4459373d')
s=s.replace("sha(r/'check-lcd-reports.py')", "sha(inherited/'check-lcd-reports.py')").replace("str(r/'check-lcd-reports.py')", "str(inherited/'check-lcd-reports.py')")
s=s.replace("'Physical color repair is pending a fresh local fixture on this exact BIT.'", "'Exact V025/V43 original KEY/P physical fixture and all-word readback remain untested.'")
s=s.replace("hardware=False,full_release=False,open_gates=", "hardware=False,full_release=False,inherited_scope='Unchanged V023 decoder/core native raster only; changed V025 bulk/control and pin behavior have separate component tests, not whole-system playback qualification',open_gates=")
(p/'image-gates.py').write_text(s)
print('V025_IMAGE_GATES_PREPARED_NO_BUILD_OR_HARDWARE')
