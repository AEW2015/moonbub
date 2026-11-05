"""Replay compiled output against frozen scalar-safe masking for all96 inputs."""
import hashlib,json
import numpy as np
import helpers as h

def main():
    result=h.old.load(h.HERE/'results.json')
    for p,tag in result['source_sha256'].items():assert h.sha(h.ROOT/p)==tag,p
    plan=h.model.compile_plan((480,720),h.old.n.RECTS)
    sources={(c['scene'],r['id']):r for c in h.old.load(h.old.n.V24/'results.json')['inputs'] for r in c['rows']}
    assert len(result['rows'])==96 and len(sources)==96
    observed=set()
    for row in result['rows']:
        key=(row['scene'],row['id']);assert key not in observed;observed.add(key)
        src=sources[key];assert row['source_sha256']==src['common_yuv420_u8_sha256']
        planes=h.old.n.source(src)
        frozen=h.old.mask.mask_source(planes,h.old.n.RECTS)
        actual=h.model.apply_plan(planes,plan)
        for a,b in zip(actual,frozen,strict=True):np.testing.assert_array_equal(a,b)
        tag=hashlib.sha256(b''.join(p.astype('u1').tobytes() for p in actual)).hexdigest()
        assert tag==row['output_sha256']
    assert observed==set(sources)
    print(json.dumps(dict(exact_frames=len(observed),safe_blocks=plan.blocks,whole_sender_timing=False)))

if __name__=='__main__':main()
