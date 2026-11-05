"""Full retained 457-frame strong-filter qualification; no encoder changes."""
import json
import numpy as np
import helpers as h
model=h.module('qual67_owned_summary',h.HERE/'model.py')

def main():
    before=h.pins();preset=h.preset();mask=h.excluded();sources=h.load(h.SOURCE/'manifest.json');packets=h.load(h.PACKETS/'results.json');cases=[]
    for src,encoded in zip(sources['cases'],packets['cases'],strict=True):
        assert src['name']==encoded['scene'];rx=h.direct.Receiver();rows=[]
        for source,f in zip(src['frames'],encoded['rows'],strict=True):
            fid=f['id'];assert source['id']==fid
            packet=h.raw(f['packet'],h.PACKETS);canonical,patches,meta,_=rx.receive(packet)
            assert h.h.m.C.reference_tag(canonical).hex()==f['normalized_tag']
            planes=tuple(p.astype(np.uint8) for p in canonical)
            for p in planes:p.setflags(write=False)
            input_sha=h.digest(b''.join(p.tobytes() for p in planes))
            rgb=np.frombuffer(h.raw(source['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3)
            original=h.h.m.C.corpus.rgb565(rgb)
            identity=h.h.f.f.n.overlay(h.h.m.C.corpus.rgb565(h.h.m.ft.planes_to_rgb(planes)),tuple(p['words'] for p in patches))
            identity_quality=h.h.f.f.n.metric(original,identity)
            assert identity_quality==f['quality'];assert h.h.f.f.n.digest(identity)==f['display_sha256']
            Y,work=h.filt.filtered_luma(planes[0],mask,preset)
            strong=h.h.f.f.n.overlay(h.h.m.C.corpus.rgb565(h.h.m.ft.planes_to_rgb((Y,planes[1],planes[2]))),tuple(p['words'] for p in patches))
            strong_quality=h.h.f.f.n.metric(original,strong)
            for patch,(x,y,w,hh) in zip(patches,h.h.f.f.n.RECTS,strict=True):
                np.testing.assert_array_equal(strong[y:y+hh,x:x+w],patch['words'])
            assert identity_quality['hud_word_errors']==strong_quality['hud_word_errors']==0
            assert input_sha==h.digest(b''.join(p.tobytes() for p in planes))
            assert h.h.m.C.reference_tag(canonical).hex()==f['normalized_tag']
            rows.append(dict(id=fid,key=meta['key'],complete_bytes=len(packet),source_packet=f['packet'],source_canvas=source['canvas_rgb24'],
                canonical_tag=f['normalized_tag'],reference_input_sha256=input_sha,identity=identity_quality,strong=strong_quality,
                identity_display_sha256=f['display_sha256'],strong_display_sha256=h.h.f.f.n.digest(strong),
                filtered_luma_sha256=h.digest(Y.tobytes()),work=work))
        case=dict(scene=encoded['scene'],rows=rows,summary=model.summarize(rows),partitions=model.partitions(rows));cases.append(case)
        print(json.dumps(dict(scene=case['scene'],summary=case['summary'],remaining=case['partitions']['remaining_48_plus'])),flush=True)
    assert h.pins()==before
    summary=dict(frames=sum(len(c['rows']) for c in cases),display_variants=2*sum(len(c['rows']) for c in cases),
        additional_temporal_canvases_beyond_first48=sum(len(c['rows'])-48 for c in cases),
        improved_frames=sum(c['summary']['improved_frames'] for c in cases),regressed_frames=sum(c['summary']['regressed_frames'] for c in cases),
        tied_frames=sum(c['summary']['tied_frames'] for c in cases),complete_bytes=sum(c['summary']['complete_bytes'] for c in cases),
        identity_SSE=sum(c['summary']['identity_SSE'] for c in cases),strong_SSE=sum(c['summary']['strong_SSE'] for c in cases))
    result=dict(schema='gamebub-filter-qual-v67',source_sha256=before,preset=preset,cases=cases,summary=summary,
        physical_30fps_proven=False,new_RTL_implemented=False,
        scope=['Unchanged strong filter calibrated only on first24 zero-motion trajectories; full457 existingCS38 causal histories, including keys every24.',
               'Known four related precompressed Mass Effect clips, not unseen games/new captures;265 additional canvases beyond previously tested first48/clip.',
               'All canonical refs/HUD/encoded bytes unchanged. Per-frame regressions retained; fixed filter is not guaranteed to improve every frame.',
               'No new native encodes or HEVC/AV1 comparison in this extended custom-only qualification.',
               'Full-plane proof filter, no additional line-buffer/physical memory/FPS evidence.'])
    (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
