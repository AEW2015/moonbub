#!/usr/bin/env python3
"""Actual HD21/HD22/full-patch work on retained exact HC21 source sequences."""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import sys
import time
import zlib
import numpy as np
import model as m

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=HERE.parent/'python-game-hud-cache-study'
spec=importlib.util.spec_from_file_location('gap22_cache',OLD/'model.py')
cache=importlib.util.module_from_spec(spec);sys.modules[spec.name]=cache;spec.loader.exec_module(cache)
previous=cache.hd


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pins():
    old=json.loads((OLD/'results.json').read_text())
    paths={ROOT/p for p in old['source_sha256']}
    paths|={OLD/'results.json'}|set((OLD/'objects').glob('*'))
    paths|={HERE/n for n in ('model.py','benchmark.py','verify.py','test_model.py','README.md','SCHEMA.md')}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}


def raw(desc,folder=OLD):
    p=Path(desc['path']);assert not p.is_absolute() and '..' not in p.parts
    data=(folder/p).read_bytes();assert hashlib.sha256(data).hexdigest()==desc['stored_sha256']
    dec=zlib.decompressobj();out=dec.decompress(data,desc['raw_bytes']+1)
    assert dec.eof and not dec.unconsumed_tail and not dec.unused_data and len(out)==desc['raw_bytes']
    assert hashlib.sha256(out).hexdigest()==desc['raw_sha256'];return out


def blob(raw):
    stored=zlib.compress(raw,9);name='objects/'+hashlib.sha256(stored).hexdigest()+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(stored)
    return dict(path=name,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),stored_sha256=hashlib.sha256(stored).hexdigest())


def measured(fn):
    start=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-start)/1e6


def arrays(row):
    return tuple(np.frombuffer(raw(d),dtype='<u2').reshape(rect[3],rect[2]) for rect,d in zip(cache.RECTANGLES,row['original_patches']))


def rgb_canvas(patches):
    canvas=np.zeros((480,720,3),np.uint8)
    for rect,p in zip(cache.RECTANGLES,patches):
        x,y,w,h=rect;canvas[y:y+h,x:x+w]=cache.legacy.codec.corpus.expand565(p)
    return canvas


def process_case(oldcase,export=False):
    selector=cache.legacy.ui.PatchSelector(rectangles=cache.RECTANGLES)
    confirmed=None;rows=[];goldens=[]
    for row in oldcase['rows']:
        current=arrays(row)
        # This canvas is an offline RGB565-exact reconstruction of fixture UI.
        # It is not a source capture/BOX or measured color-conversion stage.
        canvas=rgb_canvas(current)
        full,legacy_ms=measured(lambda:selector.select(canvas,98304))
        assert len(full.patches)==4
        assert full.used_bytes==row['legacy_patch_bytes']
        details=[];decoded=[]
        for i,(cur,legacy) in enumerate(zip(current,full.patches)):
            ref=None if confirmed is None else confirmed[i]
            oldpacket,old_ms=measured(lambda:previous.encode(cur,ref))
            packet,new_ms=measured(lambda:m.encode(cur,ref))
            oldmeta,newmeta=previous.inspect(oldpacket),m.inspect(packet)
            assert len(packet)<=len(oldpacket)
            old_kind='legacy' if len(legacy)<=len(oldpacket) else ('raw','copy','span_xor')[oldmeta['mode']]
            kind='legacy' if len(legacy)<=len(packet) else ('raw','copy','span_xor')[newmeta['mode']]
            selected=legacy if kind=='legacy' else packet
            old_selected=legacy if old_kind=='legacy' else oldpacket
            def decode_selected():
                return cache.legacy.ui.validate_patches((selected,),720,480)[0]['words'] if kind=='legacy' else m.decode(selected,ref)
            out,decode_ms=measured(decode_selected)
            np.testing.assert_array_equal(out,cur)
            decoded.append(out)
            detail=dict(index=i,legacy_bytes=len(legacy),hd21_bytes=len(oldpacket),hd22_bytes=len(packet),
                        hd21_mode=oldmeta['mode'],hd22_mode=newmeta['mode'],old_selected_kind=old_kind,selected_kind=kind,
                        old_selected_bytes=len(old_selected),selected_bytes=len(selected),
                        hd21_spans=oldmeta['span_count'],hd22_spans=newmeta['span_count'],
                        merged_zero_words=newmeta['merged_zero_words'],
                        actual_changed_words=cur.size if ref is None else int(np.count_nonzero(cur!=ref)),
                        hd21_ms=old_ms,hd22_ms=new_ms,selected_decode_ms=decode_ms,
                        hd22_sha256=hashlib.sha256(packet).hexdigest())
            details.append(detail)
            # One interesting sample per sequence plus the initial full sample.
            choose=(row['frame']==0 and i==0 and len(goldens)<1) or (newmeta['merged_zero_words']>0 and len(goldens)<2)
            if export and choose:
                goldens.append(dict(case=oldcase['name'],frame=row['frame'],patch=i,shape=list(cur.shape),
                                    current=blob(cur.astype('<u2').tobytes()),reference=None if ref is None else blob(ref.astype('<u2').tobytes()),
                                    packet=blob(packet),meta=newmeta))
        before=cache.HEADER.size+4+sum(p['old_selected_bytes'] for p in details)
        after=cache.HEADER.size+4+sum(p['selected_bytes'] for p in details)
        assert before==row['sidecar_bytes']
        assert after<=before
        rows.append(dict(frame=row['frame'],legacy_ms=legacy_ms,patches=details,
                         hc21_bytes=before,proposed_same_overhead_bytes=after,
                         exact_words=sum(a.size for a in decoded),
                         old_paid_encode_ms=legacy_ms+sum(p['hd21_ms'] for p in details),
                         new_paid_encode_ms=legacy_ms+sum(p['hd22_ms'] for p in details)))
        # Actual selected decodes, not original-source aliases, become the next
        # confirmed reference. ACK delivery is immediate and assumed here.
        confirmed=tuple(a.copy() for a in decoded)
    summary=dict(name=oldcase['name'],frames=len(rows),patch_decisions=4*len(rows),
                 hc21_bytes=sum(r['hc21_bytes'] for r in rows),
                 proposed_same_overhead_bytes=sum(r['proposed_same_overhead_bytes'] for r in rows),
                 total_hd21_candidate_bytes=sum(p['hd21_bytes'] for r in rows for p in r['patches']),
                 total_hd22_candidate_bytes=sum(p['hd22_bytes'] for r in rows for p in r['patches']),
                 total_hd21_candidate_spans=sum(p['hd21_spans'] for r in rows for p in r['patches']),
                 total_hd22_candidate_spans=sum(p['hd22_spans'] for r in rows for p in r['patches']),
                 total_hd22_merged_zero_words=sum(p['merged_zero_words'] for r in rows for p in r['patches']),
                 selected_hd21_span_records=sum(p['hd21_spans'] for r in rows for p in r['patches'] if p['old_selected_kind']=='span_xor'),
                 selected_hd22_span_records=sum(p['hd22_spans'] for r in rows for p in r['patches'] if p['selected_kind']=='span_xor'),
                 selected_hd22_merged_zero_words=sum(p['merged_zero_words'] for r in rows for p in r['patches'] if p['selected_kind']=='span_xor'),
                 matched_span_patches=sum(p['old_selected_kind']==p['selected_kind']=='span_xor' for r in rows for p in r['patches']),
                 matched_span_removed_headers=sum(p['hd21_spans']-p['hd22_spans'] for r in rows for p in r['patches'] if p['old_selected_kind']==p['selected_kind']=='span_xor'),
                 matched_span_extra_zero_words=sum(p['merged_zero_words'] for r in rows for p in r['patches'] if p['old_selected_kind']==p['selected_kind']=='span_xor'),
                 exact_words=sum(r['exact_words'] for r in rows),
                 maximum_hd22_packet_bytes=max(p['hd22_bytes'] for r in rows for p in r['patches']),
                 old_modes={k:sum(p['old_selected_kind']==k for r in rows for p in r['patches']) for k in ('legacy','raw','copy','span_xor')},
                 new_modes={k:sum(p['selected_kind']==k for r in rows for p in r['patches']) for k in ('legacy','raw','copy','span_xor')},
                 mean_old_paid_encode_ms=sum(r['old_paid_encode_ms'] for r in rows)/len(rows),
                 mean_new_paid_encode_ms=sum(r['new_paid_encode_ms'] for r in rows)/len(rows),
                 mean_new_selected_decode_ms=sum(sum(p['selected_decode_ms'] for p in r['patches']) for r in rows)/len(rows))
    summary['hud_forward_saving_percent']=100*(summary['hc21_bytes']-summary['proposed_same_overhead_bytes'])/summary['hc21_bytes']
    return dict(name=oldcase['name'],rows=rows,summary=summary),goldens


def main():
    before=pins();old=json.loads((OLD/'results.json').read_text());cases=[];goldens=[]
    for c in old['cases']:
        result,vectors=process_case(c,export=True);cases.append(result);goldens.extend(vectors)
        print(json.dumps(result['summary']),flush=True)
    assert before==pins()
    result=dict(schema='gamebub-gap-span-v22',source_sha256=before,cases=cases,goldens=goldens,
                counts=dict(native_updates=96,synthetic_updates=36,updates=132,patch_decisions=528,exact_words=2787840),
                versions=dict(python=platform.python_version(),numpy=np.__version__),
                scope=['ActualHD22/HD21andlegacyencoding/selecteddecodeonfixedretainedRGB565sequences;allmodespaid.',
                       'NoYUVbase/quantizer/referencehistorychanges;newHD22magicnotacceptedbyHC21nativeorPythonreceiver.',
                       'Sidecartotalsprojectsame83BHC21overheadwithnewdispatchversion;notserializedjointprofile.',
                       'ImmediateACKassumed;noscheduledtransport/RF/ESP32ISA/DMA/FPGAresources/physical30fpsproof.',
                       'FixtureRGB565-toRGBcanvaspreparationandcorrectness/exportexcludedfrompaidencoderstages.'])
    (HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')


if __name__=='__main__':main()
