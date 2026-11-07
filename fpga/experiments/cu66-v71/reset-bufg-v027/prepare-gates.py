from pathlib import Path
p=Path(__file__).resolve().parent;rows=p.parent/'rows-idle-capture-v026';bulk=p.parent/'hud-bulk-v025'
for name in ['run-xsim-full-synth.py','finish-offline-flow.py','await-native-image-gates.py']:
 s=(rows/name).read_text().replace('dy71-v026-20261107-v001','dy71-v027-20261107-v001').replace('rows-idle-capture-v026/xsim-full-synth01','reset-bufg-v027/xsim-full-synth01').replace('v026-lab.bit','v027-lab.bit')
 if name=='await-native-image-gates.py':s=s.replace("(p/('integration-'+c+'01/comparison.json'))","(Path('C:/mb70/fpga/experiments/cu66-v71/rows-idle-capture-v026')/('integration-'+c+'01/comparison.json'))")
 (p/name).write_text(s)
s=(rows/'image-gates.py').read_text().replace('dy71-v026-20261107-v001','dy71-v027-20261107-v001').replace('4459373e','4459373f').replace('V026_NATIVE_LAB_IMAGE_V1','V027_NATIVE_LAB_IMAGE_V1').replace('V026_LAB_BIT','V027_LAB_BIT').replace('V026_NATIVE_AUDIT','V027_NATIVE_AUDIT').replace('v026-lab.bit','v027-lab.bit')
s=s.replace("expected_added={'fpga/experiments", "expected_added={'fpga/experiments",1)
needle="|{'fpga/experiments/cu66-v71/rows-idle-capture-v026/cu71_tile_rows.sv'}";assert needle in s;s=s.replace(needle,needle+"|{'fpga/experiments/cu66-v71/reset-bufg-v027/moonshine_top_dy71.sv'}")
s=s.replace("str(r/'check-proof-bindings.py')", "str(root/'fpga/experiments/cu66-v71/rows-idle-capture-v026/check-proof-bindings.py')")
s=s.replace("(r/'proof02/result.json')", "(root/'fpga/experiments/cu66-v71/rows-idle-capture-v026/proof02/result.json')").replace("(r/'pair01/result.json')", "(root/'fpga/experiments/cu66-v71/rows-idle-capture-v026/pair01/result.json')")
s=s.replace("d=r/('integration-'+corner+'01')", "d=root/'fpga/experiments/cu66-v71/rows-idle-capture-v026'/('integration-'+corner+'01')")
# The core/data graph is exactly V026; only the top reset distribution changes.
needle="timing=m.timing_metrics((build/'timing-summary.rpt').read_text());";assert needle in s
checks="""
reset_test=json.loads((r/'reset01/result.json').read_text());assert reset_test['status']=='PASS_ORIGINAL_RESET_STAGES_THROUGH_ACTUAL_BUFG_MODEL'
assert all(sha(Path(n))==h for n,h in reset_test['sources_sha256'].items())
assert sha(parent/'inputs/fpga/experiments/cu66-v71/reset-bufg-v027/moonshine_top_dy71.sv')==sha(r/'moonshine_top_dy71.sv')
"""
s=s.replace(needle,checks+'\n'+needle)
s=s.replace("extra += 'set reset", "extra += 'set reset",1)
needle="out.mkdir(exist_ok=False);";assert needle in s
s=s.replace(needle,"extra += '\\nset c [get_cells -quiet core_reset_distribution]\\nif {[llength $c]!=1 || [get_property REF_NAME $c] ni {BUFG BUFGCTRL}} {error \"Missing reset global buffer\"}\\nreport_property $c -file [file join $out reset-buffer.rpt]\\n'\n"+needle)
s=s.replace("Exact V026/V43", "Exact V027/V43")
s=s.replace("Scalar CSR simulation platform and new ABI2 bulk/pins are separate scopes.","Scalar CSR simulation platform and new ABI2 bulk/pins are separate scopes. V027 additionally has the actual UNISIM reset-buffer test; no added reset stage or changed clock period/phase.")
(p/'image-gates.py').write_text(s)
print('V027_GATES_PREPARED_NO_HARDWARE')
