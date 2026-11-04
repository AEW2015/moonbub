#!/usr/bin/env python3
"""Replay every retained packet and golden, using exact reconstructed references."""
from pathlib import Path
import json,sys,importlib.util
import numpy as np
import benchmark as b
h=b.HERE

def check_pins(pins,archives=None):
    for name,digest in pins.items():
        path=b.ROOT/(archives or {}).get(name,name)
        assert b.n.sha(path)==digest,str(path)

def verify(result,model):
    old=b.n.load(b.n.V24/'results.json');prior=b.n.load(b.CAPPED/'results.json');banks={};total=0
    for inp in old['inputs']:
        frozen=next(c for c in prior['cases'] if c['scene']==inp['scene'] and c['profile']=='capped_key_zero_rdo1')
        ref=None; refs={model.NO_REF:None}
        for row in frozen['rows'][:12]:
            ref,_=model.v25.decode(b.n.raw(row['base_packet'],b.CAPPED),ref,expected_epoch=25,
                                  expected_reference_id=None if row['key'] else row['reference_id'])
            refs[row['id']]=ref
        banks[inp['scene']]=refs
    for case in result['cases']:
        inp=next(x for x in old['inputs'] if x['scene']==case['scene']);ref=None
        for row,source in zip(case['rows'],inp['rows']):
            if case['kind']=='matched':ref=banks[case['scene']][row['reference_id']]
            packet=b.n.raw(row['base_packet'],h)
            got,meta=model.decode(packet,ref,expected_epoch=26,expected_reference_id=None if row['key'] else row['reference_id'])
            assert len(packet)==row['base_bytes']
            assert meta['reconstructed_tag'].hex()==row['reconstructed_tag']
            original=b.n.original(source)
            bare=model.C.corpus.rgb565(model.ft.planes_to_rgb(got))
            hybrid=b.n.overlay(bare,tuple(original[y:y+hh,x:x+ww] for x,y,ww,hh in b.n.RECTS))
            assert b.n.digest(bare)==row['bare_rgb565_sha256']
            assert b.n.digest(hybrid)==row['hybrid_rgb565_sha256']
            assert b.n.metric(original,hybrid)==row['hybrid']
            assert row['hybrid']['hud_word_errors']==0
            if row['id'] in (0,1):
                assert b''.join(p.astype('<i2').tobytes() for p in got)==b.n.raw(row['golden_yuv420_i16'],h)
                assert hybrid.astype('<u2').tobytes()==b.n.raw(row['golden_hybrid_rgb565'],h)
            if case['variant']=='zero':assert row['hybrid']==row['frozen_hybrid']
            if case['kind']=='closed':ref=got
            total+=1
        assert sum(r['base_bytes'] for r in case['rows'])==case['summary']['base_bytes']
    return total

def main():
    result=json.loads((h/'results.json').read_text());check_pins(result['source_sha256'])
    count=verify(result,b.m)
    early=json.loads((h/'early-results.json').read_text())
    archives=json.loads((h/'early-archive.json').read_text())['source_path_archive'];check_pins(early['source_sha256'],archives)
    spec=importlib.util.spec_from_file_location('prediction26_early',h/'model_early_probe.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    earlycount=verify(early,m)
    print(json.dumps(dict(status='PASS',compact_packets=count,early_packets=earlycount,exact_hud_word_errors=0,all_goldens=True)))
if __name__=='__main__':main()
