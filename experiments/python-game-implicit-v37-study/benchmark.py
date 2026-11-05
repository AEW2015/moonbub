"""Actual CS37 packets and equality; times only paid-input transcoding."""
import json,statistics
import numpy as np
import helpers as h
model=h.module('implicit37_encoder',h.HERE/'model.py')
decoder=h.module('implicit37_independent_decode',h.HERE/'verify.py')

def main():
    pins=h.pins();folder=h.HERE.parent/'python-game-canonical-v36-study';old=h.load(folder/'results.json');cases=[]
    items=[(c,'main') for c in old['cases']]+[(old['motion_probe'],'fractional_motion')]
    for case,kind in items:
        rx=decoder.Receiver();baseline=decoder.f.Receiver();rows=[]
        for prior in case['rows']:
            packet=h.raw(prior['skip']['packet'],folder);rep=[];results=[]
            for _ in range(3):
                result,work=model.transcode(packet);rep.append(work['transcode_ms']);results.append(result)
            assert results[0]==results[1]==results[2]
            actual,parts,meta=rx.receive(result);expected,hud,oldmeta=baseline.receive(packet)
            for a,b in zip(actual,expected,strict=True):np.testing.assert_array_equal(a,b)
            for a,b in zip(parts,hud,strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            normalized=h.m.C.reference_tag(actual).hex();assert normalized==prior['skip']['normalized_tag']
            display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(actual)),tuple(v['words'] for v in parts))
            tag=h.n.digest(display);assert tag==prior['skip']['display_sha256']
            rows.append(dict(id=prior['id'],packet=h.blob(result),complete_bytes=len(result),old_complete_bytes=len(packet),
                             normalized_tag=normalized,display_sha256=tag,hybrid=prior['skip']['hybrid'],
                             work=work,transcode_ms_samples=rep,median_transcode_ms=statistics.median(rep)))
        new=sum(r['complete_bytes'] for r in rows);previous=sum(r['old_complete_bytes'] for r in rows)
        summary=dict(frames=len(rows),complete_bytes=new,old_complete_bytes=previous,saved_bytes=previous-new,
                     percent_saved=100*(previous-new)/previous,maximum_complete_bytes=max(r['complete_bytes'] for r in rows),
                     implicit_planes=sum(sum(p['implicit_selected'] for p in r['work']['planes']) for r in rows),
                     mean_median_transcode_ms=statistics.mean(r['median_transcode_ms'] for r in rows),
                     active_mse=sum(r['hybrid']['active_squared_error'] for r in rows)/sum(r['hybrid']['active_channel_samples'] for r in rows),
                     nominal_Mbps_at30=new*240/len(rows)/1e6)
        cases.append(dict(scene=case['scene'],kind=kind,rows=rows,summary=summary));print(json.dumps(dict(scene=case['scene'],kind=kind,summary=summary)),flush=True)
    assert h.pins()==pins
    output=dict(schema='gamebub-implicit-v37',parent_commit='f433677b66c1b9b6a2a74bf21f95dc6ff042524c',source_sha256=pins,cases=cases,
                profile=dict(magic='CS37',inner_magic='GS37',dispatch=4,wrapper_bytes=80,bitmap_bytes=0,profile_tag=model.PROFILE.hex()),
                physical_30fps_proven=False,new_RTL_implemented=False,
                scope=['Actual serialized bounded packets; no bitmap: fixed profile implicitly determines safe omitted blocks and visible raster order.',
                       'Compact plane entropy bw1; full-grid frozen plane fallback wins ties and costs no extra prefixbyte. Every actual packet <=old CN36 skip.',
                       'Already encoded CN36skip input is paid externally; all three transcoding repetitions include originalpacketparse, compact entropy trial, fallbackchoice and sealing.',
                       'Equality, fixtures, blobI/O and receiver decode excluded from transcoder timing. This is not integrated directsender or inverse bypass.',
                       'Independent decoder does not import new encoder, expands implicit coefficients and verifies original/normalized tags, exactHUD, fullcausalreferences and display.',
                       'Two short retained windows plus directed6frame motion probe; no fresh nativeencode or hardware qualification.'])
    (h.HERE/'results.json').write_text(json.dumps(output,indent=2)+'\n')

if __name__=='__main__':main()
