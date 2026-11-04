#!/usr/bin/env python3
"""Twelve-frame/two-scene fixed accepted-GM27-reference search probe.

No candidate output becomes a later reference. A new causal controller belongs
to the parent experiment. Every candidate here is actually GM27 encoded and
decoded, and its CP27 envelope is serialized before its size is reported.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import sys
import time
import zlib
import numpy as np
import model as s

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V27 = HERE.parent/'python-game-unified-v27-study'


def load_module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    out = importlib.util.module_from_spec(spec); sys.modules[name]=out; spec.loader.exec_module(out)
    return out


n = load_module('search28_native',HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
p = load_module('search28_protocol',V27/'protocol.py')


def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blob(value):
    stored = zlib.compress(value,9)
    path = HERE/'objects'/f'{hashlib.sha256(stored).hexdigest()}.zlib'
    path.parent.mkdir(exist_ok=True); path.write_bytes(stored)
    return dict(path=path.relative_to(HERE).as_posix(),raw_bytes=len(value),raw_sha256=hashlib.sha256(value).hexdigest(),stored_sha256=sha(path))


def source_pins(prior,inputs):
    paths = {ROOT/q for q in prior['source_sha256']}
    paths |= {V27/'results.json',n.V24/'results.json'}
    paths |= set(HERE.glob('*.py'))|set(HERE.glob('*.md'))
    for inp in inputs:
        case = next(c for c in prior['cases'] if c['scene']==inp['scene'] and c['policy']=='unified_causal')
        for sr,row in zip(inp['rows'][:12],case['rows'][:12]):
            paths |= {n.V24/sr[k]['path'] for k in ('common_yuv420_u8','original_rgb565')}
            paths.add(V27/row['packet']['path'])
    return {q.relative_to(ROOT).as_posix():sha(q) for q in sorted(paths)}


def main():
    prior = load(V27/'results.json'); inputs = load(n.V24/'results.json')['inputs']
    before = source_pins(prior,inputs); rows = []
    for inp in inputs:
        case = next(c for c in prior['cases'] if c['scene']==inp['scene'] and c['policy']=='unified_causal')
        receiver = p.Receiver(epoch=25)
        ref = None; refid = s.m.NO_REF
        for sr,oldrow in zip(inp['rows'][:12],case['rows'][:12]):
            fid = sr['id']; src = n.source(sr); original = n.original(sr)
            accepted_pair = n.raw(oldrow['packet'],V27)
            accepted_meta = p.parse_pair(accepted_pair); accepted_hud = accepted_meta['hud']
            qmap = s.m.roi.declared_map(720,480,n.ROIS,8,oldrow['selected_background'])
            result = dict(scene=inp['scene'],id=fid,reference_id=refid,
                          reference_tag=None if ref is None else s.m.C.reference_tag(ref).hex(),
                          accepted_packet=oldrow['packet'],background=oldrow['selected_background'],variants={})
            for policy in ('exhaustive',*s.POLICIES):
                kwargs = dict(epoch=25,frame_id=fid,reference_id=refid,block_size=32,
                              motion_mode='zero' if ref is None else 'block',penalty=0,motion_precision='half')
                prepared = s.m.analyze_planes(src,ref,**kwargs) if policy=='exhaustive' else s.analyze_planes(src,ref,search_policy=policy,**kwargs)
                began = time.perf_counter_ns()
                packet,expected,work = s.m.encode_prepared(prepared,qmap,rdo_lambda=1)
                encode_ms = (time.perf_counter_ns()-began)/1e6
                decoded,meta = s.m.decode(packet,ref,expected_reference_id=None if ref is None else refid)
                for a,b in zip(decoded,expected): np.testing.assert_array_equal(a,b)
                bare = s.m.C.corpus.rgb565(s.m.ft.planes_to_rgb(decoded))
                hybrid = n.overlay(bare,tuple(original[y:y+h,x:x+w] for x,y,w,h in n.RECTS))
                quality = n.metric(original,hybrid)
                flags = p.PUBLISH|(p.KEY if ref is None else 0)
                pair = p.seal(p.PAIR.pack(b'CP27',1,flags,25,fid,oldrow['source_slot'],oldrow['destination_slot'],len(packet),len(accepted_hud),p.digest(packet),p.digest(accepted_hud))+packet+accepted_hud)
                fit = len(pair)<=p.CAP
                if fit: p.parse_pair(pair)
                result['variants'][policy] = dict(base_packet=blob(packet),packet=blob(pair),base_bytes=len(packet),complete_bytes=len(pair),cap_fit=fit,
                      analysis=prepared.work,encode_ms=encode_ms,whole_base_encode_ms=prepared.work['analysis_wall_ms']+encode_ms,
                      work=work,hybrid=quality,reconstructed_tag=meta['reconstructed_tag'].hex(),
                      hybrid_rgb565_sha256=n.digest(hybrid),vector_bytes=prepared.vector_bytes.hex())
            decoded,patches,ack = receiver.receive(accepted_pair)
            p.validate_ack(ack,accepted_pair)
            for patch,(x,y,w,h) in zip(patches,n.RECTS): np.testing.assert_array_equal(patch['words'],original[y:y+h,x:x+w])
            assert s.m.C.reference_tag(decoded).hex()==oldrow['reconstructed_tag']
            ref,refid = decoded,fid
            rows.append(result)
            print(json.dumps(dict(scene=inp['scene'],id=fid,variants={k:dict(bytes=v['complete_bytes'],mse=v['hybrid']['active_mse'],analysis_ms=v['analysis']['analysis_wall_ms']) for k,v in result['variants'].items()})),flush=True)
    summaries = {}
    for policy in ('exhaustive',*s.POLICIES):
        variants = [r['variants'][policy] for r in rows]
        pframes = [v for r,v in zip(rows,variants) if r['reference_id']!=s.m.NO_REF]
        summaries[policy] = dict(frames=len(variants),p_frames=len(pframes),complete_bytes=sum(v['complete_bytes'] for v in variants),
                  active_mse=sum(v['hybrid']['active_squared_error'] for v in variants)/sum(v['hybrid']['active_channel_samples'] for v in variants),
                  cap_fit_frames=sum(v['cap_fit'] for v in variants),hud_word_errors=sum(v['hybrid']['hud_word_errors'] for v in variants),
                  mean_p_analysis_ms=float(np.mean([v['analysis']['analysis_wall_ms'] for v in pframes])),
                  mean_p_search_ms=float(np.mean([v['analysis']['search_ms'] for v in pframes])),
                  mean_whole_base_encode_ms=float(np.mean([v['whole_base_encode_ms'] for v in variants])),
                  p_sad_sample_operations=sum(v['analysis']['search']['sad_sample_operations'] for v in pframes),
                  p_reference_sample_fetches=sum(v['analysis']['search']['reference_sample_fetches'] for v in pframes))
    assert before==source_pins(prior,inputs),'source changed during run'
    out = dict(schema='gamebub-search-v28-probe1',source_sha256=before,versions=dict(python=platform.python_version(),numpy=np.__version__),
               scope='Fixed accepted unified_causal GM27 reference history, first12 frames per scene; actual new GM27/CP27 packets; no new causal acceptance or physical30fps claim.',
               summaries=summaries,rows=rows)
    (HERE/'results.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps(summaries),flush=True)


if __name__=='__main__': main()
