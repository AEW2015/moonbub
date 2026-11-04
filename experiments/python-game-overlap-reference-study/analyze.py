#!/usr/bin/env python3
"""Derive matched-delivery and wire evidence without rerunning timed work."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    path=HERE/'results.json';result=json.loads(path.read_text())
    cases={c['profile']:c for c in result['cases'] if c['source']=='mass-effect-2600-heldout180'}
    ca,cb=cases['immutable_initial'],cases['overlap_recent16_initial'];a,b=ca['result'],cb['result']
    ids={}
    for field in ('packets','commits','presented'):
        left=[r['id'] for r in a[field]];right=[r['id'] for r in b[field]]
        assert left==right and len(left)==179
        ids[field]=left
    assert [d['id'] for d in a['drops']]==[d['id'] for d in b['drops']]==[1]
    native_hashes=ca['manifest']['frame_sha256']
    assert native_hashes==cb['manifest']['frame_sha256']
    mean_body=lambda r:sum(p['bytes'] for p in r['packets'])/len(r['packets'])
    forward=lambda r:r['forward_ipv4_udp_bytes']
    all_wire=lambda r:r['forward_ipv4_udp_bytes']+r['reverse_ipv4_udp_bytes']
    steady={}
    for name,r in (('immutable_initial',a),('overlap_recent16_initial',b)):
        displayed=[p for p in r['presented'] if 500<=p['at_ms']<5500]
        seq=[p['id'] for p in displayed]
        assert seq==list(range(13,163))
        assert len(set(native_hashes[i] for i in seq))==150
        steady[name]=dict(window_ms=[500,5500],presented_ids=seq,
            distinct_native_source_hashes=150,diagnostic_ids_per_second=30.,interior_missing_ids=[])
    assert a['reverse_ipv4_udp_bytes']==b['reverse_ipv4_udp_bytes']==12709
    out=dict(results_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        matched_admitted_ids=ids['packets'],matched_decoded_ids=ids['commits'],matched_presented_ids=ids['presented'],
        matched_distinct_native_hashes=len(set(native_hashes[i] for i in ids['presented'])),
        only_dropped_source_id=1,drop_scope='Initial key-ACK startup latest-replacement,notaninteriordrop.',
        mean_body_bytes=[mean_body(a),mean_body(b)],mean_body_saving_percent=100*(1-mean_body(b)/mean_body(a)),
        forward_wire_bytes=[forward(a),forward(b)],forward_wire_saving_percent=100*(1-forward(b)/forward(a)),
        reverse_wire_bytes=[a['reverse_ipv4_udp_bytes'],b['reverse_ipv4_udp_bytes']],
        total_wire_bytes=[all_wire(a),all_wire(b)],total_wire_saving_percent=100*(1-all_wire(b)/all_wire(a)),
        modeled_max_presented_age_ms=[max(p['age_ms'] for p in a['presented']),max(p['age_ms'] for p in b['presented'])],
        mean_active_mse=[sum(c['active_rgb565_mse'] for c in a['commits'])/179,
                         sum(c['active_rgb565_mse'] for c in b['commits'])/179],
        steady=steady,
        scope='Same179sourceIDsand150distinctsourcehashesin5sdiagnosticwindow,actualcodec/wirebytes;differentreferencesanddistortion,remeasuredhostcosts,assumedlinks/vblank.NoHEVC/AV1qualityequivalence,nativehardwareorlongduration30fpsproof.')
    target=HERE/'matched-delivery.json'
    if args.check:
        assert json.loads(target.read_text())==out
        print('PASS:matched179admitted/decoded/presentedIDs,150distinctsteadyimageseach,body/wire/age/qualityaccounting')
    else:target.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
