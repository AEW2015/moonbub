"""Alternating paired component timings; fixture and equality excluded."""
import json, platform, statistics, time
import numpy as np
import helpers as h

def clock(fn):
    start=time.perf_counter_ns();result=fn()
    return result,(time.perf_counter_ns()-start)/1e6

def main():
    pins=h.pins()
    plan,compile_ms=clock(lambda:h.model.compile_plan((480,720),h.old.n.RECTS))
    rows=[]
    for case in h.old.load(h.old.n.V24/'results.json')['inputs']:
        for src in case['rows']:
            planes=h.old.n.source(src)
            times={'frozen':[],'compiled':[]};outputs={}
            for rep in range(3):
                order=('frozen','compiled') if (src['id']+rep)%2==0 else ('compiled','frozen')
                for name in order:
                    fn=(lambda:h.old.mask.mask_source(planes,h.old.n.RECTS)) if name=='frozen' else (lambda:h.model.apply_plan(planes,plan))
                    outputs[name],wall=clock(fn);times[name].append(wall)
                for a,b in zip(outputs['frozen'],outputs['compiled'],strict=True):np.testing.assert_array_equal(a,b)
            tag=hashlib_tag(outputs['compiled'])
            rows.append(dict(scene=case['scene'],id=src['id'],source_sha256=src['common_yuv420_u8_sha256'],output_sha256=tag,
                             timing_ms=times,paired_median_ms={k:statistics.median(v) for k,v in times.items()}))
    assert h.pins()==pins
    old=statistics.mean(r['paired_median_ms']['frozen'] for r in rows)
    new=statistics.mean(r['paired_median_ms']['compiled'] for r in rows)
    results=dict(schema='gamebub-maskplan-v36',source_sha256=pins,rows=rows,
                 summary=dict(frames=len(rows),repetitions=3,compile_ms_once=compile_ms,
                              mean_paired_medians_ms=dict(frozen=old,compiled=new),component_ratio=old/new,
                              safe_blocks=list(plan.blocks),constant_stores=sum(plan.blocks)*64,
                              row_spans=sum(map(len,plan.runs)),
                              packed_plan_bytes_if_u16_triplets=sum(map(len,plan.runs))*6,
                              packed_plan_is_estimate_not_python_memory=True,
                              actual_owned_int16_plane_bytes=1036800,logical_u8_plane_bytes=518400),
                 environment=dict(python=platform.python_version(),numpy=np.__version__),
                 scope=['Both paths validate all planes, copy planes and set identical hidden samples to128.',
                        'Compile happens once for fixed geometry. Per-frame compiled clocks exclude compilation, fixture decode, equality proof, hashing and archive I/O.',
                        'Three paired repetitions alternate order. No whole-sender, native endpoint or FPGA timing claim.',
                        'Plan has Python tuple storage; 16-bit packed run estimate is not measured Python object memory.'])
    (h.HERE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results['summary']))

def hashlib_tag(planes):
    import hashlib
    return hashlib.sha256(b''.join(p.astype('u1').tobytes() for p in planes)).hexdigest()

if __name__=='__main__':main()
