#!/usr/bin/env python3
"""Read-only actual AR03 arithmetic and conditional stripe-service reconciliation."""
import hashlib,json
from pathlib import Path
import model,importlib.util
_spec=importlib.util.spec_from_file_location('v19_actual_stripe_benchmark',Path(__file__).with_name('benchmark.py'))
benchmark=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(benchmark)
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def main():
    d=json.loads((HERE/'results.json').read_text())
    for raw,h in d['source_sha256'].items():assert hashlib.sha256((ROOT/raw).read_bytes()).hexdigest()==h,raw
    assert d['schema']=='gamebub-actual-stripe-service-v1'
    assert d['counts']==dict(packets=16,native_decisions=12,unique_native_acquisitions=6,flat_controls=4,blocks=97308,
        exact_residual_samples=6227712,exact_reconstructed_samples=6224472,exact_selected_ui_words=253440,profiles=10),d['counts']
    current=benchmark.make_frames();assert current==d['frames'],'fresh exact arithmetic/fixture reconciliation'
    assert len(d['cases'])==10
    for c in d['cases']:
        b=model.Budget(**c['budget'])
        assert len(c['rows'])==len(current)
        for f,r in zip(current,c['rows']):
            assert (f['cohort'],f['id'])==(r['cohort'],r['id'])
            got=model.schedule(f,b);assert got==r['schedule']
            uniform=model.schedule(f,b,True);assert uniform['frame_done_ms']==r['uniform_frame_done_ms']
            assert abs(sum(s['refill_bytes'] for s in uniform['stripes'])-got['entropy_refill_bytes'])<1e-6
            assert got['local_buffer_total_bytes']==49152+got['local_coefficient_stripe_bytes']+got['local_reconstruction_stripe_bytes']+16+960+512+got['local_color_line_bytes']+got['local_ui_palette_bytes']
            last={}
            for s in got['stripes']:
                assert s['entropy_done_ms']<=s['consumer_start_ms']<=s['prediction_done_ms']<=s['inverse_done_ms']<=s['done_ms']
                if s['coefficient_slot'] in last:assert s['entropy_start_ms']>=last[s['coefficient_slot']]
                last[s['coefficient_slot']]=s['done_ms']
    assert d['legal_width_bounds']==model.legal_width_bounds()
    assert d['legal_width_bounds']['accumulator_signed_bits']<=40
    print(json.dumps(dict(packets=16,exact_blocks=97308,exact_residual_samples=d['counts']['exact_residual_samples'],
        exact_yuv_samples=d['counts']['exact_reconstructed_samples'],exact_selected_ui_words=253440,conditional_profiles=10,
        native_or_physical_30fps_proven=False),indent=2))
if __name__=='__main__':main()
