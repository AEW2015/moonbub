"""Fixed identity/strong filter on later temporal custom/native decoded planes."""
import json,time
import numpy as np
import helpers as h
adapter=h.bound('filter62_owned_adapter',h.HERE/'adapter.py',h)

def main():
    presets=h.fixed_presets();mask=h.excluded();before=h.pins();cases,anchors,missing=adapter.cases();assert not missing
    results=[];cache={}
    for descriptor in cases:
        scene=descriptor['scene']
        if scene not in cache:cache[scene]=adapter.originals(scene)
        words,originals=cache[scene];states={p['name']:h.metric.Diagnostics(h.h.f.f.n.RECTS)for p in presets};rows={p['name']:[]for p in presets}
        for i,presentation in enumerate(adapter.presentations(descriptor,words)):
            fid=presentation['id'];assert fid==24+i;planes=presentation['planes'];patches=presentation['patches'];original=originals[i]
            input_hash=h.planes_digest(planes);canonical_hash=None if presentation['canonical']is None else h.canonical_digest(presentation['canonical'])
            assert canonical_hash==presentation['canonical_sha256']
            for preset in presets:
                begin=time.perf_counter_ns();Y,work=h.filt.filtered_luma(planes[0],mask,preset);filter_ms=(time.perf_counter_ns()-begin)/1e6
                assert h.planes_digest(planes)==input_hash
                if presentation['canonical']is not None:assert h.canonical_digest(presentation['canonical'])==canonical_hash
                display=h.h.f.f.n.overlay(h.h.m.C.corpus.rgb565(h.h.m.ft.planes_to_rgb((Y,planes[1],planes[2]))),tuple(p['words']for p in patches))
                diagnostic=states[preset['name']].add(original,h.h.m.C.corpus.expand565(display))
                for patch,(x,y,w,hh)in zip(patches,h.h.f.f.n.RECTS,strict=True):np.testing.assert_array_equal(display[y:y+hh,x:x+w],patch['words'])
                display_hash=h.digest(display.astype('<u2').tobytes())
                if preset['name']=='identity':
                    assert display_hash==presentation['expected_display_sha256'];assert diagnostic['active_SSE']==presentation['expected_quality']['active_squared_error']
                rows[preset['name']].append(dict(id=fid,native_pts=presentation['native_pts'],reference_input_sha256=input_hash,canonical_reference_sha256=canonical_hash,
                    filtered_luma_sha256=h.digest(Y.tobytes()),display_sha256=display_hash,complete_bytes=presentation['complete_bytes'],
                    source_packet=presentation['source_packet'],diagnostic=diagnostic,work=work,filter_ms=filter_ms))
        assert all(len(v)==24 for v in rows.values());assert all(sum(r['complete_bytes']for r in v)==descriptor['complete_bytes']for v in rows.values())
        result=dict(descriptor,presets=[dict(preset=p,rows=rows[p['name']],summary=states[p['name']].summary())for p in presets]);results.append(result)
        print(json.dumps(dict(scene=scene,kind=descriptor['kind'],policy=descriptor['policy'],source=descriptor['source'],parameter=descriptor.get('parameter'),MSE={k:v.summary()['active_MSE']for k,v in states.items()})),flush=True)
    assert h.pins()==before
    output=dict(schema='gamebub-filter-temporal-v62',source_sha256=before,cases=results,anchor_selection=anchors,missing_declared_inputs=missing,
        calibration_source=(h.FILTER/'calibration.json').relative_to(h.ROOT).as_posix(),source_window=[24,48],
        excluded_luma_samples=int(mask.sum()),excluded_luma_sha256=h.digest(mask.tobytes()),
        summary=dict(source_cases=len(results),unique_source_canvases=96,decoded_presentations=24*len(results),display_variants=48*len(results),
            selected_native_anchors=sum(c['kind']=='native'for c in results),unsupported_native_anchors=sum(a['selected']is None for a in anchors)),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        scope=['Unchanged60strong alpha24/beta12/strength3 frozen ONLY fromzero47 IDs0..23; unchangedidentity andstrong applieduniformly toallselectedcustom/native cases onsourceIDs24..47.',
            'Nativeanchorsminsampledactualbytes subjectcap0+meanoriginalRGB565SSE<=separatezero; selectionexploratory andretainsunsupported ifnone; noencoderheldout/optimalfrontierclaim.',
            'Fresh61nativePTS0..23 mappedexplicitlytosourceIDs24..47; sameactualsourceHX33 words overlayLAST andremainexact. DecodedYUV/customcanonicalrefs notmutated.',
            'Displayonly luma filter, fullplane Pythonproof; encodedbytes/referenceupdate/codecdecisions unchanged. No streaminglinebuffer/DSP/BRAM/timing/FPS orbitrategainclaim.',
            'Error57 large-error/gridjump/coordinate-temporal-change diagnostics rederived, notSSIM/VMAF/subjectiveflickerproof. Additionaltemporalwindow, notproject-wideunseenmedia.'])
    (h.HERE/'results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output['summary']),flush=True)
if __name__=='__main__':main()
