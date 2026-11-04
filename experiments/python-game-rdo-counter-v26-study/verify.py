#!/usr/bin/env python3
"""Recheck source pins, native counts and every fast native candidate byte."""
import json
import numpy as np
import benchmark as p

def main():
    data=json.loads((p.HERE/'results.json').read_text())
    for path,digest in data['source_sha256'].items():assert p.sha(p.ROOT/path)==digest,path
    cases,inputs=p.fixtures();a,manifest,general=p.native_samples(cases)
    assert manifest==data['counter']['manifest'] and general==data['counter']['general_packets']
    assert p.digest(a)==data['counter']['coefficient_sha256']
    sizes=p.c.isolated_packet_bytes(a)
    want=np.array([len(p.c.oracle.encode_coefficients(x[None],1)) for x in a],np.int64)
    np.testing.assert_array_equal(sizes,want)
    assert p.digest(sizes)==data['counter']['sizes_sha256']
    rows=p.native_campaign(cases,inputs,verify_rows=data['rows'])
    assert len(rows)==96
    for row,old in zip(rows,data['rows']):
        for key in ('scene','id','key','reference_id','selected_background'):assert row[key]==old[key]
        assert len(row['attempts'])==len(old['attempts'])
        for attempt,before in zip(row['attempts'],old['attempts']):
            for key in ('background','packet','packet_sha256','packet_bytes','coefficient_sha256','reconstructed_sha256','rdo'):assert attempt[key]==before[key],key
    assert p.summarize(data['rows'])==data['summary']
    print(json.dumps(dict(native_sources=len(rows),native_attempts=sum(len(r['attempts']) for r in rows),isolated_blocks=len(a),general_packets=len(general),all_fast_bytes_equal_retained_GM25=True,source_pins_checked=len(data['source_sha256']),hardware_fps_proven=False),indent=2))

if __name__=='__main__':main()
