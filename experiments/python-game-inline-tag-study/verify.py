#!/usr/bin/env python3
"""Read-only reconstruction of stripe-tag evidence, not performance timings."""
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('inline_tag_evidence_builder',HERE/'benchmark.py')
builder=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=builder;_spec.loader.exec_module(builder)

def verify():
    data=json.loads((HERE/'results.json').read_text())
    assert data['source_sha256']==builder.pins()
    actual=builder.build()
    # Host duration isn't regenerated as a performance claim.
    for key in ('evidence','source_sha256','case_count','cases','counterfactual','limits'):
        assert actual[key]==data[key],key
    assert data['case_count']==20
    full=[c for c in data['cases'] if (c['width'],c['height'])==(720,480)]
    assert len(full)==8
    assert all(c['peak_stripe_storage_bytes']==11520 and c['canonical_bytes_hashed']==1036804
               and c['conditional_eliminable_packed8_publication_reread_bytes']==518400 for c in full)
    assert all(c['tag']==c['reference_tag'] for c in data['cases'])
    return dict(exact_cases=20,full720x480_cases=8,max_target_stripe_bytes=11520,
                canonical_full_frame_sha_bytes=1036804,conditional_packed8_tag_reread_bytes=518400,
                producer='simulated from already decoded full planes',decoder_fusion_proven=False,
                target_bandwidth_or_30fps_proven=False)

if __name__=='__main__':print(json.dumps(verify(),indent=2))
