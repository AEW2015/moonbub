#!/usr/bin/env python3
"""Verify phase=0 smoke matches the first 10 cycles of the prior ~60 Hz run."""
import json,pathlib
here=pathlib.Path(__file__).resolve().parent
smoke=here/'results/smoke-phase-zero';original=here.parent/'qspi-cadence-jitter/results/60hz-jitter-2ms'
a=json.loads((smoke/'analysis.json').read_text());b=json.loads((original/'analysis.json').read_text())
if a['config']!={'frames':10,'jitter_cycles':200000,'pclk_half_ps':18470,'capture_phase_cycles':0}:raise ValueError('smoke config mismatch')
if b['config']!={'frames':300,'jitter_cycles':200000,'pclk_half_ps':18470}:raise ValueError('reference config mismatch')
if (smoke/'fixture-manifest.sha256').read_text().split()[0]!=(original/'fixture-manifest.sha256').read_text().split()[0]:raise ValueError('fixture manifest mismatch')
if a['exact_pixels']!=10*345600 or b['exact_pixels']!=300*345600:raise ValueError('pixel check missing')
if [(x['id'],x['present']) for x in a['per_frame']]!=[(x['id'],x['present']) for x in b['per_frame'][:10]]:raise ValueError('presentation mismatch')
print('PHASE0_EQUIVALENCE_PASS frames=10 identical_presentation_cycles=10')
