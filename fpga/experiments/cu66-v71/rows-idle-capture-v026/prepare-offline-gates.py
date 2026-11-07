"""Derive V026 gates from executed V025 gates; add exact new-row proof/raster checks."""
from pathlib import Path
p=Path(__file__).resolve().parent;bulk=p.parent/'hud-bulk-v025'
s=(bulk/'run-xsim-vendor-v004.py').read_text(encoding='utf-8-sig')
s=s.replace("e=p/'xsim-vendor04'", "e=Path('C:/mb70/fpga/experiments/cu66-v71/rows-idle-capture-v026/xsim-full-synth01')")
s=s.replace("p/'mapping04/funcsim.v'", "Path('C:/mb70/dy71-v026-20261107-v001/bulk-funcsim.v')").replace("p/'mapping04/dy71_hud_bulk_v025.sv'", "Path('C:/mb70/dy71-v026-20261107-v001/inputs/fpga/experiments/cu66-v71/hud-bulk-v025/dy71_hud_bulk_v025.sv')")
s=s.replace('Actual synthesized standalone bulk engine / AMD unisims_ver;', 'Exact V026 full-synthesis exported bulk engine / AMD unisims_ver;')
(p/'run-xsim-full-synth.py').write_text(s)
s=(bulk/'prepare-image-gates.py').read_text().replace('dy71-v025-20261107-v003','dy71-v026-20261107-v001')
s=s.replace("expected_added={'fpga/experiments/cu66-v71/hud-bulk-v025/'+n for n in ['dy71_hud_bulk_v025.sv','dy71_local_control_bulk_v025.sv','cu71_bus_cdc_bulk_v025.sv','moonshine_top_dy71.sv']}","expected_added={'fpga/experiments/cu66-v71/hud-bulk-v025/'+n for n in ['dy71_hud_bulk_v025.sv','dy71_local_control_bulk_v025.sv','cu71_bus_cdc_bulk_v025.sv','moonshine_top_dy71.sv']}|{'fpga/experiments/cu66-v71/rows-idle-capture-v026/cu71_tile_rows.sv'}")
s=s.replace("for name in ['functional04'", "bulk=root/'fpga/experiments/cu66-v71/hud-bulk-v025'\nfor name in ['functional04'")
s=s.replace("(r/name/'result.json')", "(bulk/name/'result.json')").replace("r/'xsim-full-synth02/result.json'", "r/'xsim-full-synth01/result.json'")
s=s.replace('4459373d','4459373e').replace('V025','V026').replace('v025-lab.bit','v026-lab.bit')
# Inject exact source binding for the changed rows; do not inherit its old raster proof.
needle="s=s.replace(\"oracle_helper['verify'](r,\", \"oracle_helper['verify'](inherited,\")"
assert needle in s
addition='''
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
'''
s=s.replace(needle,addition+'\n'+needle)
s=s.replace("(p/'image-gates.py').write_text(s)","s=s.replace(\"inherited_scope='Unchanged V023 decoder/core native raster only; changed V026 bulk/control and pin behavior have separate component tests, not whole-system playback qualification'\",\"inherited_scope='Unchanged V023 components inherited; changed V026 rows have exact control/payload induction, paired RAM-output simulation and new fast/slow native raster runs. Scalar CSR simulation platform and new ABI2 bulk/pins are separate scopes.'\")\n(p/'image-gates.py').write_text(s)")
(p/'prepare-image-gates.py').write_text(s)
# Same fail-closed phase/report flow, with a qualified exact full-build export.
s=(bulk/'finish-offline-flow.py').read_text().replace('dy71-v025-20261107-v003','dy71-v026-20261107-v001')
s=s.replace("str(p/'verify-bulk-netlist.py')", "str(Path('C:/mb70/fpga/experiments/cu66-v71/hud-bulk-v025/verify-bulk-netlist.py'))")
(p/'finish-offline-flow.py').write_text(s)
s=(bulk/'await-native-image-gates.py').read_text().replace('dy71-v025-20261107-v003','dy71-v026-20261107-v001').replace('xsim-full-synth02','xsim-full-synth01').replace('v025-lab.bit','v026-lab.bit')
# Wait for the additional native raster gate before attempting the audit.
s=s.replace("for mode in ['audit','emit']:","while not all((p/('integration-'+c+'01/comparison.json')).exists() for c in ['fast','slow']):\n assert time.monotonic()<deadline,'Native raster wait expired'\n time.sleep(5)\nfor mode in ['audit','emit']:")
(p/'await-native-image-gates.py').write_text(s)
print('V026_OFFLINE_GATES_PREPARED')
