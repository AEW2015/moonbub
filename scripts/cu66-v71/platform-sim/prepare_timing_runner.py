"""Derive a manifest-selectable runner without changing sealed integration01 producer."""
from pathlib import Path
import hashlib

directory = Path(__file__).resolve().parent
parent = directory/'run.py'
target = directory/'run_timing.py'
assert not target.exists()
assert hashlib.sha256(parent.read_bytes()).hexdigest() == '229128076e5cff0af8c03a280bf7e8f84298c6e85bac62559fc2bad6a879192c'
text = parent.read_text()
changes = {
    "a.add_argument('--build-only',action='store_true');args=a.parse_args()":
    "a.add_argument('--build-only',action='store_true');a.add_argument('--manifest',type=Path,required=True);args=a.parse_args()",
    "manifest=json.loads((root/'fpga/experiments/cu66-v71/system/sources-burst.json').read_text());assert manifest['SIMULATION']is False":
    "manifest=json.loads(args.manifest.read_text());assert manifest['SIMULATION']is False",
    "sources=[root/n for n in manifest['sources']]":
    """wrapper=o/'cu71_platform_sim.sv'
wrapper_text=(platform/'cu71_platform_sim.sv').read_text()
assert wrapper_text.count('cu71_system_burst #(')==1
wrapper.write_text(wrapper_text.replace('cu71_system_burst #(',manifest['top']+' #('),newline='\\n')
sources=[root/n for n in manifest['sources']]""",
    "sources += [platform/'cu71_platform_sim.sv',platform/'model-verilator.sv'":
    "sources += [wrapper,platform/'model-verilator.sv'",
    "(o/'source-freeze.json').write_text(json.dumps(origins,indent=2)+'\\n')":
    """origins['selected_system_manifest']=sha(args.manifest)
origins['executed_runner']=sha(Path(__file__))
shutil.copyfile(Path(__file__),o/'executed-runner.py')
(o/'source-freeze.json').write_text(json.dumps(origins,indent=2)+'\\n')""",
}
for old, new in changes.items():
    assert text.count(old) == 1, old
    text = text.replace(old, new)
target.write_text(text, newline='\n')
print(target)
