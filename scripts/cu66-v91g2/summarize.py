#!/usr/bin/env python3
"""Write the V91g2 evidence index and bundle hash manifest after independent audit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91g2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    analysis = json.loads((AREA/'analysis.json').read_text())
    audit = json.loads((AREA/'audit.json').read_text())
    model = json.loads((AREA/'tile-bank-results.json').read_text())
    assert analysis['status'] == 'PASS'
    assert str(audit['status']).startswith('PASS')
    summary = dict(schema='cu66-v91g2-bounded-two-bank-tile-overlap-evidence-v1', status='PASS',
        parent_commit='f06293ae9f1099841f5de9faa8c6687cff9fb23a',
        selected=[dict(seed=c['seed'],report=c['report'],report_sha256=c['report_sha256'],
                       populations=c['populations'],highwaters=c['highwaters']) for c in analysis['campaigns']],
        evidence_sha256={str(p.relative_to(ROOT)):sha(p) for p in [AREA/'analysis.json',AREA/'audit.json',
            AREA/'tile-bank-results.json',AREA/'telemetry-contract.json']},
        model_scope=model['scope'],
        next_tile_merge_overlap_implemented=True,
        unchanged='BR88 bytes, quantization, packed scratch layout and dense coefficients',
        current_endpoint=analysis['endpoint'],
        full_frame_validated_decode_under10ms_proven=False, hardware_distinct_30fps_proven=False,
        physical_clock_fit_or_memory_controller_calibration_proven=False,
        firmware_or_hardware_deployed=False)
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    roots = [ROOT/'scripts/cu66-v91g2',ROOT/'fpga/experiments/cu66-v91g2',AREA,ROOT/'docs/cu66-v91g2']
    files = [p for root in roots for p in root.rglob('*') if p.is_file() and
             '__pycache__' not in p.parts and p.name not in ('bundle-manifest.json','vectors.txt')]
    files += [ROOT/p for p in ['docs/gamebub-application-specific-codec-plan.md',
        'docs/gamebub-v91-v110-development-plan.md','docs/literature-review-2026-11-06/README.md']]
    manifest=dict(schema='cu66-v91g2-bundle-manifest-v1',
        scope='All V91g2 source, retained historical/final receipts, independent evidence and three updated shared plans; excludes this self-reference, cache files and transient text vectors.',
        files_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))})
    (AREA/'bundle-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('V91G2_EVIDENCE_INDEX_PASS',len(files),'files')


if __name__ == '__main__':
    main()
