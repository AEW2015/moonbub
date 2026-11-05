"""Three paired exact HUD32/HUD33 stage timings on24 qualified HU25 inputs."""
import json,platform,statistics,time
import numpy as np
import helpers as h
model=h.module('hudfast42_benchmark_model',h.HERE/'model.py')

def pipeline(kind,baseline,reference,rid):
    if kind=='slow':
        packet32,work32=h.hud32.encode_hud(baseline,reference,expected_reference_id=rid)
        packet33,work33=h.hud33.encode_hud(baseline,packet32,reference,expected_reference_id=rid)
    else:
        packet32,work32=model.encode_hud32(baseline,reference,expected_reference_id=rid)
        packet33,work33=model.encode_hud33(baseline,packet32,reference,expected_reference_id=rid)
    return packet32,packet33,work32,work33
def clock(fn):
    start=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-start)/1e6

def main():
    before=h.pins();qualification=h.load(h.QUAL/'results.json');cases=[]
    for case in qualification['cases']:
        reference=None;rows=[]
        for old in case['rows'][:6]:
            fid=old['id'];rid=None if old['reference_id']==h.p.NO_REF else old['reference_id']
            baseline=h.raw(old['hud_packets']['HU25'],h.QUAL);expected32=h.raw(old['hud_packets']['HX32'],h.QUAL);expected33=h.raw(old['hud_packets']['HX33_selected'],h.QUAL)
            ref_tag=h.p.ZERO if reference is None else h.p.hud_tag(reference,720,480)
            timings={'slow':[],'fast':[]};orders=[];outputs={}
            for rep in range(3):
                order=('slow','fast')if(fid+rep)%2==0 else('fast','slow');orders.append(list(order))
                for kind in order:
                    outputs[kind],wall=clock(lambda:pipeline(kind,baseline,reference,rid));timings[kind].append(wall)
                for kind in('slow','fast'):
                    assert outputs[kind][0]==expected32 and outputs[kind][1]==expected33,'archived HX32/HX33 byte identity'
                assert outputs['slow'][2]['patches']==outputs['fast'][2]['patches'],'all HUD32 size/rejection/choice decisions'
                assert outputs['slow'][3]['patches']==outputs['fast'][3]['patches'],'all HUD33 size/rejection/choice decisions'
            packet32,packet33,work32,work33=outputs['fast']
            decoded,meta=h.hud33.decode_hud(packet33,reference,expected_epoch=25,expected_reference_id=rid)
            original,prior_meta=h.p.decode_hud(baseline,reference,expected_epoch=25,expected_reference_id=rid)
            for a,b in zip(decoded,original,strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            rows.append(dict(id=fid,reference_id=old['reference_id'],previous_accepted_id=old['previous_accepted_id'],reference_tag=ref_tag.hex(),
                source_rgb_sha256=old['source_rgb_sha256'],HU25=h.blob(baseline),HX32=h.blob(packet32),HX33_selected=h.blob(packet33),
                output_hud_tag=h.p.hud_tag(decoded,720,480).hex(),exact_hud_words=sum(p['words'].size for p in decoded),
                paired_timing_ms=timings,paired_order=orders,paired_median_ms={k:statistics.median(v)for k,v in timings.items()},
                slow32=outputs['slow'][2],slow33=outputs['slow'][3],fast32=work32,fast33=work33))
            reference=decoded
            print(json.dumps(dict(scene=case['scene'],id=fid,bytes=len(packet33))),flush=True)
        means={k:statistics.mean(r['paired_median_ms'][k]for r in rows)for k in('slow','fast')}
        summary=dict(frames=len(rows),HX32_bytes=sum(r['HX32']['raw_bytes']for r in rows),HX33_selected_bytes=sum(r['HX33_selected']['raw_bytes']for r in rows),
            mean_paired_medians_ms=means,paired_stage_ratio=means['slow']/means['fast'],
            fast_huffman_plans=sum(r[v]['work']['huffman_plans']for r in rows for v in('fast32','fast33')),
            fast_huffman_materializations=sum(r[v]['work']['huffman_materializations']for r in rows for v in('fast32','fast33')),
            fast_rice_k_trials=sum(r[v]['work']['rice_k_trials']for r in rows for v in('fast32','fast33')),
            fast_rice_materializations=sum(r[v]['work']['rice_materializations']for r in rows for v in('fast32','fast33')))
        cases.append(dict(scene=case['scene'],rows=rows,summary=summary));print(json.dumps(summary),flush=True)
    assert h.pins()==before
    result=dict(schema='gamebub-hud-fast-v42',source_sha256=before,cases=cases,
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['24HU25inputs=first6each4qualifiedadditionalclips; incominglastacceptedHUDrefs arefrozenpreviousacceptedHX33words.',
               'ThreealternatingpairedrepetitionsEVERYframe. BothstagesincludeHX32thenHX33allbaselineHU25/providedHX32decodevalidation,allrecipes/HuffmanandRiceplanning,chosenpayloads/sealing.',
               'HU25generation/motionsearch/patchselectionisexternallypaidandEXCLUDED. Inputread/decompression,archives,byte/decisionassertions,outside-semanticdecode,transport/displayexcluded.',
               'ExactHUFFtrees/canonicaltables andallRicek0..14costs retained; packonlywinningpatch/channelstreams usingNumPybitLUT/packbits. Nopersistentpreparedcacheorfrozenglobalpatch.',
               'Allslow/fastperpatch/recipe/channelbytes/depthrejections/scheme/mode/tie choicesmatchandarearchived; actualHX32/HX33allbyteidenticaltoqualifiedpackets.',
               'Hostcomponentoptimizationwithprivatearrays,notwholepipelinespeedup,nocompressiongain,native/FPGA/ESPmemoryorphysical30fpsclaim. SharedexactHUDoptimizationbenefitsbothcustomandnativehybridanchors.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
