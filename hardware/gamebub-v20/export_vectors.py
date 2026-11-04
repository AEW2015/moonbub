#!/usr/bin/env python3
"""Deterministic little-endian int32 vectors for scalar-C and future RTL tests."""
import json
from pathlib import Path
import numpy as np
import reference as ref
HERE=Path(__file__).resolve().parent

def build(write=False):
    rows=[]
    for name,values,labels in ref.datasets():
        expected,stats=ref.stripe.inverse(values);np.testing.assert_array_equal(expected,ref.stripe.ft.inverse(values))
        blobs={}
        for kind,a in [('dequantized',values),('residual',expected)]:
            filename,raw,stored=ref.encoded_array(a)
            if write:(HERE/'vectors'/filename).write_bytes(stored)
            blobs[kind]=dict(path='vectors/'+filename,shape=list(a.shape),dtype='<i4',raw_bytes=len(raw),raw_sha256=__import__('hashlib').sha256(raw).hexdigest(),stored_sha256=__import__('hashlib').sha256(stored).hexdigest())
        rows.append(dict(name=name,blocks=len(values),planes=labels,arrays=blobs,
            work=dict(nonzero_coefficients=sum(stats['nonzero_coeff']),nonzero_intermediates=sum(stats['intermediate_nnz']),
                first_products=sum(stats['first_mac']),second_products=sum(stats['second_mac']),constant_products=stats['dc_constant_multiplies'],
                zero=stats['zero'],dc=stats['dc'],general=stats['general'])))
    return dict(schema='gamebub-v20-inverse-golden-v1',source_sha256=ref.source_pins(),datasets=rows,
        total_blocks=sum(r['blocks'] for r in rows),basis_q14=ref.stripe.ft.Q14.tolist(),legal_width_bounds=ref.stripe.legal_width_bounds(),
        scope='Exact dequantized8x8 inverse residuals and work counts. Portable scalarC oracle, not a whole codec, target timing or FPGA mapping. Fixture/oracle arrays are outside target local-memory claims.')
def main():
    d=build(True);(HERE/'golden-index.json').write_text(json.dumps(d,indent=2)+'\n');print('exported',d['total_blocks'],'inverse blocks')
if __name__=='__main__':main()
