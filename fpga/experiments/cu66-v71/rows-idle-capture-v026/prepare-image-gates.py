"""Derive V026 image gates; preserve V023 checks and explicit inherited scope."""
from pathlib import Path
p=Path(__file__).resolve().parent
old=p.parent/'result-admission-system-v023'
s=(old/'image-gates.py').read_text()
s=s.replace("parent=root/'dy71-v023-20261106-v001'", "parent=root/'dy71-v026-20261107-v001'; inherited=root/'fpga/experiments/cu66-v71/result-admission-system-v023'")
s=s.replace("assert build==parent.resolve(),'Only the exact frozen candidate build may be qualified'", "assert build in (parent.resolve(),(parent/'incremental01').resolve(),(parent/'postroute01').resolve(),(parent/'postroute02').resolve()),'Only frozen v003 named physical candidates may be qualified'")
s=s.replace("runpy.run_path(str(r/'check-source-binding.py'),run_name='__main__')", "runpy.run_path(str(inherited/'check-source-binding.py'),run_name='__main__')\n"+'''
# Inherit only unchanged decoder/system sources, never new control/pin behavior.
oldfreeze=json.loads((root/'dy71-v023-20261106-v001/source-freeze.json').read_text())
newfreeze=json.loads((parent/'source-freeze.json').read_text())
subprocess.run([sys.executable,str(root/'fpga/experiments/cu66-v71/hud-bulk-v025/check-component-bindings.py'),'--build',str(build)],check=True)
assert json.loads((build/'source-freeze.json').read_text())==newfreeze
assert all(sha(build/'inputs'/n)==h for n,h in newfreeze.items())
if build!=parent.resolve():
 assert sha(build/'constrained.dcp')==sha(parent/'constrained.dcp'),'Different synthesis checkpoint'
 assert sha(build/'bulk-funcsim.v')==sha(parent/'bulk-funcsim.v'),'Different simulated cell'
added=set(newfreeze)-set(oldfreeze)
expected_added={'fpga/experiments/cu66-v71/hud-bulk-v025/'+n for n in ['dy71_hud_bulk_v025.sv','dy71_local_control_bulk_v025.sv','cu71_bus_cdc_bulk_v025.sv','moonshine_top_dy71.sv']}|{'fpga/experiments/cu66-v71/rows-idle-capture-v026/cu71_tile_rows.sv'}
assert added==expected_added,(added,expected_added)
platform='fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v004/constraints/platform.xdc'
assert all(oldfreeze[n]==h for n,h in newfreeze.items() if n in oldfreeze and n!=platform),'Existing source/constraint changed'
assert (parent/'inputs'/platform).read_text()==(root/'dy71-v023-20261106-v001/inputs'/platform).read_text().replace('4459373b','4459373e'),'Platform differs beyond image identity'
bulk=root/'fpga/experiments/cu66-v71/hud-bulk-v025'
for name in ['functional04','pins05','legacy05','xsim-vendor04']:
 report=json.loads((bulk/name/'result.json').read_text());assert report['status'].startswith('PASS_')
if a.mode=='emit':
 post=json.loads((r/'xsim-full-synth01/result.json').read_text());assert post['status']=='PASS_XSIM_POST_SYNTH_BULK_NATIVE_WORDS'
 assert post['netlist_sha256']==sha(parent/'bulk-funcsim.v')
''')

# Redirect only the inherited V023 raster loop before adding V026's new loop.
s=s.replace("d=r/('integration-'", "d=inherited/('integration-'")
s=s.replace("cache='fpga/experiments", """
subprocess.run([sys.executable,str(r/'check-proof-bindings.py')],check=True)
proof=json.loads((r/'proof02/result.json').read_text());assert proof['status']=='PASS_EXACT_CONTROL_PROJECTION_AND_OWNED_PAYLOAD_INDUCTION'
row='fpga/experiments/cu66-v71/rows-idle-capture-v026/cu71_tile_rows.sv'
assert proof['source_sha256']['cu71_tile_rows.sv']==sha(parent/'inputs'/row)
assert json.loads((r/'pair01/result.json').read_text())['status']=='PASS_OBSERVED_OLD_NEW_ROWS_AND_AUTHORITATIVE_PAYLOAD'
for corner in ('fast','slow'):
 d=r/('integration-'+corner+'01');v=json.loads((d/'source-binding.json').read_text())
 assert v['row_source']==row and v['row_sha256']==sha(parent/'inputs'/row)
 assert all(sha(Path(n))==h for n,h in v['files_sha256'].items())
 assert '/mnt/c/'+(d/'inputs'/row).as_posix()[3:] in v['compile_command'][-1]
 assert json.loads((d/'comparison.json').read_text())['status']=='PASS_EXACT_NATIVE_RASTER'
 assert all(x['returncode']==0 for x in json.loads((d/'execution.json').read_text()))
 assert 'SDK_RTL_COSIM_PASS' in (d/'native-integration.log').read_text()
cache='fpga/experiments""")

s=s.replace("oracle_helper['verify'](r,", "oracle_helper['verify'](inherited,")
s=s.replace("str(r/'check-components.py')", "str(inherited/'check-components.py')")
s=s.replace('V023_NATIVE_LAB_IMAGE_V1','V026_NATIVE_LAB_IMAGE_V1').replace("USERID_USR_ACCESS='4459373b'", "USERID_USR_ACCESS='4459373e'")
s=s.replace("=='4459373b'", "=='4459373e'").replace("'0x4459373b'", "'0x4459373e'")
s=s.replace('moonbub-v023-lab.bit','moonbub-v026-lab.bit').replace('V023_LAB_BIT_EMITTED_NO_HARDWARE','V026_LAB_BIT_EMITTED_NO_HARDWARE').replace('V023_NATIVE_AUDIT_COMPLETE_NO_BIT','V026_NATIVE_AUDIT_COMPLETE_NO_BIT').replace("'v023-'+a.mode", "'v025-'+a.mode").replace('expected_identity=0x4459373b','expected_identity=0x4459373e')
s=s.replace("sha(r/'check-lcd-reports.py')", "sha(inherited/'check-lcd-reports.py')").replace("str(r/'check-lcd-reports.py')", "str(inherited/'check-lcd-reports.py')")
s=s.replace("'Physical color repair is pending a fresh local fixture on this exact BIT.'", "'Exact V026/V43 original KEY/P physical fixture and all-word readback remain untested.'")
s=s.replace("hardware=False,full_release=False,open_gates=", "hardware=False,full_release=False,inherited_scope='Unchanged V023 decoder/core native raster only; changed V026 bulk/control and pin behavior have separate component tests, not whole-system playback qualification',open_gates=")
s=s.replace("inherited_scope='Unchanged V023 decoder/core native raster only; changed V026 bulk/control and pin behavior have separate component tests, not whole-system playback qualification'","inherited_scope='Unchanged V023 components inherited; changed V026 rows have exact control/payload induction, paired RAM-output simulation and new fast/slow native raster runs. Scalar CSR simulation platform and new ABI2 bulk/pins are separate scopes.'")
(p/'image-gates.py').write_text(s)
print('V026_IMAGE_GATES_PREPARED_NO_BUILD_OR_HARDWARE')
