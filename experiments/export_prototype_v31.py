#!/usr/bin/env python3
"""Bind the isolated RTL experiment, firmware notes and inherited goldens."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent.parent
P='experiments/rtl-game-inverse-v31-study/'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    parent=json.loads((ROOT/'docs/prototype-v30-provenance.json').read_text())
    frozen={p:h for p,h in parent['file_sha256'].items() if p not in ('README.md','docs/gamebub-application-specific-codec-plan.md')}
    for p,h in frozen.items():assert sha(ROOT/p)==h,('frozen v30',p)
    paths={ROOT/p for p in parent['file_sha256']}
    paths|={ROOT/p for p in ('docs/prototype-v30-provenance.json','docs/esp32-compact-transport-plan.md','docs/v31-rtl-acceleration-2026-11-04.md',
                            'experiments/export_prototype_v31.py','experiments/verify_prototype_v31.py','host/moonshine/protocol.py',
                            'firmware/handheld/src/streaming/protocol.rs','firmware/handheld/src/streaming/mod.rs')}
    paths|={p for p in (ROOT/P).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    for name in ('vectors.json','results/results.json'):
        for p,h in json.loads((ROOT/P/name).read_text())['source_sha256'].items():
            q=Path(p);assert not q.is_absolute() and '..' not in q.parts
            assert sha(ROOT/q)==h,('executed source',p);paths.add(ROOT/q)
    m=dict(schema='gamebub-v31-provenance',parent_commit='8c9836f58dad0baf2a1ab93ea32f3539b86944aa',
           file_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},frozen_v30_sha256=frozen,
           rtl_helper=P+'verify.py',rtl_run_artifact=P+'results/results.json',simulation_cases=5,
           limitations=['Isolated dequantized Q14 inverse/predict-add/clip kernel, not a full decoder.',
                        'Verilator behavioral full corpus; Icarus RTL and generic Series7 mapped functional directed subset.',
                        'No XSim/HLS run, Vivado timing closure, whole-design fit, CDC/electrical proof or physical30fps.',
                        'Compact ESP32 transport is documented only; no firmware implementation or flash.'])
    (ROOT/'docs/prototype-v31-provenance.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(paths),frozen_v30_files=len(frozen),simulation_cases=5)))
if __name__=='__main__':main()
