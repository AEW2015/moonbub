"""Derive explicit entropy/dequant bindings; no qualification or hardware implied."""
from pathlib import Path
import argparse, hashlib, json, re

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--entropy', required=True)
parser.add_argument('--dequant', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()
out = (root / args.output).resolve()
out.mkdir(parents=True, exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
relative = lambda p: str(p.relative_to(root)).replace('\\', '/')
entropy = (root / args.entropy).resolve()
dequant = (root / args.dequant).resolve()
def module(path):
    names = re.findall(r'^module\s+(\w+)', path.read_text(), re.M)
    assert len(names) == 1, path
    return names[0]

base = root / 'fpga/experiments/cu66-v71/codec/cu71_base_pipeline_bram.sv'
receiver = root / 'fpga/experiments/cu66-v71/codec/cu71_receiver_bram.sv'
system = root / 'fpga/experiments/cu66-v71/system/cu71_system_burst.sv'
jobs = [
    (base, 'cu71_base_pipeline_timing.sv', {
        'cu71_base_pipeline_bram': 'cu71_base_pipeline_timing',
        'cu66_ab38_decoder': module(entropy),
        'cu66_dequant': module(dequant),
    }),
    (receiver, 'cu71_receiver_timing.sv', {
        'cu71_receiver_bram': 'cu71_receiver_timing',
        'cu71_base_pipeline_bram': 'cu71_base_pipeline_timing',
    }),
    (system, 'cu71_system_timing.sv', {
        'cu71_system_burst': 'cu71_system_timing',
        'cu71_receiver_bram': 'cu71_receiver_timing',
    }),
]
bindings = []
replacement = {}
for parent, target, names in jobs:
    text = parent.read_text()
    for old, new in names.items():
        assert len(re.findall(r'\b'+re.escape(old)+r'\b', text)) == 1, (parent, old)
        text = re.sub(r'\b'+re.escape(old)+r'\b', new, text)
    candidate = out / target
    candidate.write_text(text, newline='\n')
    replacement[relative(parent)] = relative(candidate)
    bindings.append(dict(parent=relative(parent), parent_sha256=sha(parent),
                         candidate=relative(candidate), candidate_sha256=sha(candidate),
                         module_replacements=names))
replacement.update({
    'fpga/experiments/cu66-v69/entropy/cu66_ab38_decoder.sv': relative(entropy),
    'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv': relative(dequant),
})
parent_manifest = root / 'fpga/experiments/cu66-v71/system/sources-burst.json'
selection = json.loads(parent_manifest.read_text())
for name, expected in selection['sources_sha256'].items():
    assert sha(root/name) == expected, f'Parent manifest changed: {name}'
sources = [replacement.get(name, name) for name in selection['sources']]
(out/'sources.json').write_text(json.dumps(dict(
    top='cu71_system_timing', sources=sources, include_dirs=selection['include_dirs'],
    sources_sha256={name:sha(root/name) for name in sources}, SIMULATION=False,
    scope='Explicit pipelined entropy/dequant binding, old-map RGB burst; complete integrated regressions/timing pending',
), indent=2)+'\n')
(out/'derivation.json').write_text(json.dumps(dict(
    status='STRUCTURAL_BINDING_ONLY_INTEGRATED_REGRESSION_PENDING', bindings=bindings,
    parent_manifest_sha256=sha(parent_manifest),
    entropy=dict(path=relative(entropy),sha256=sha(entropy)),
    dequant=dict(path=relative(dequant),sha256=sha(dequant)),
    memory_map='Original v70 mapping; no crossbank candidate selected',
    firmware_ABI='Unchanged CU71 local ABI1; no new network wire contract',
    hardware=False, BIT=False,
), indent=2)+'\n')
print(out)
