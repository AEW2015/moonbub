"""Actual RP39 lossless mode-rank transcoding of all54 paid SP38 packets."""
import json,platform
import numpy as np
import helpers as h
model=h.module('rank39_benchmark_model',h.HERE/'model.py')

def array_blob(array):return dict(**h.blob(array.tobytes()),shape=list(array.shape),dtype=array.dtype.str)
def main():
    pins=h.pins();folder=h.HERE.parent/'python-game-spatial-v38-study';old=h.load(folder/'results.json');cases=[]
    for case in old['cases']:
        rx=h.f.Receiver();ref=None;rows=[]
        for prior in case['rows']:
            incoming=h.raw(prior['packet'],folder)
            packet,output,work,trials=model.transcode(incoming,ref)
            expected,parts,meta=rx.receive(incoming)
            for a,b in zip(output,expected,strict=True):np.testing.assert_array_equal(a,b)
            assert h.m.C.reference_tag(output).hex()==prior['normalized_tag']
            display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(output)),tuple(v['words']for v in parts))
            assert h.n.digest(display)==prior['display_sha256']
            trial_records=[dict(rank_packet=h.blob(t['rank_packet']),menus=array_blob(t['menus']),ranks=array_blob(t['ranks']))for t in trials]
            rows.append(dict(id=prior['id'],key=prior['key'],reference_id=prior['reference_id'],source_sha256=prior['source_sha256'],
                packet=h.blob(packet),old_packet=prior['packet'],old_complete_bytes=len(incoming),complete_bytes=len(packet),
                reference_tag=prior['reference_tag'],normalized_tag=prior['normalized_tag'],display_sha256=prior['display_sha256'],
                hybrid=prior['hybrid'],work=work,trials=trial_records))
            ref=expected
            print(json.dumps(dict(scene=case['scene'],policy=case['policy'],frame=prior['id'],bytes=len(packet))),flush=True)
        total=sum(r['complete_bytes']for r in rows);previous=sum(r['old_complete_bytes']for r in rows)
        planes=[w for r in rows for w in r['work']['planes']]
        summary=dict(frames=len(rows),complete_bytes=total,old_complete_bytes=previous,saved_bytes=previous-total,
            percent_saved=100*(previous-total)/previous,maximum_complete_bytes=max(r['complete_bytes']for r in rows),
            old_mode_bytes=sum(w['old_mode_bytes']for w in planes),selected_mode_bytes=sum(w['selected_mode_bytes']for w in planes),
            rank_planes=sum(w['rank_selected']for w in planes),trial_probability_products=sum(w['probability_products']for w in planes),
            selected_probability_products=sum(w['probability_products']for w in planes if w['rank_selected']),
            selected_arithmetic_bits=sum(w['arithmetic_bit_count']for w in planes if w['rank_selected']),
            menu_counts=[sum(w['menu_counts'][i]for w in planes)for i in range(4)],
            mean_paid_transcode_ms=sum(r['work']['transcode_ms']for r in rows)/len(rows),
            active_mse=sum(r['hybrid']['active_squared_error']for r in rows)/sum(r['hybrid']['active_channel_samples']for r in rows))
        cases.append(dict(scene=case['scene'],kind=case['kind'],policy=case['policy'],rows=rows,summary=summary));print(json.dumps(summary),flush=True)
    assert h.pins()==pins
    result=dict(schema='gamebub-mode-rank-v39',source_sha256=pins,cases=cases,
        profile=dict(magic='RP39',inner_magic='TR39',profile_tag=model.PROFILE.hex(),outer_format=model.OUTER.format,inner_format=model.INNER.format,
            rank_dispatch=3,rank_header_bytes=5,rank_order='tilemajor ty,tx then00,01,10,11;hidden=noevent',rank_code='truncatedunarywithN-1maximumdecisions',
            context='position*12+(N-2)*3+decision;max44',probability_states=88,interval_bits=16,probability_bits=8,
            arithmetic_adaptation='frozenAB38shift5',old_full_mode_fallback_wins_ties=True,coefficients_unchanged=True),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['PaidSP38inputtranscoder,oneactualtimedsample/frame;parse,decoder-deriveddistinctmenus,reconstruction,allranktrials,arithmetic,comparisonandrepackpaid. No wholesenderFPSclaim.',
               'Same54actualpilotframes; modeidentity/coefficients/references/displaylossless. SelectedmodeisstablefirstamongidenticalCLIPPEDpredictors;noncanonicalduplicateinputrejected.',
               'N1rank0noarithdecisions. Truncatedunaryuses<=3binarydecisionsforN<=4,one17x8probabilityproduct/decision,frozen16bitAB38intervalandshiftadaptation.',
               'Fulloldmodepayloadwinscompletebyteties. Bothheaders,rankdispatch/bitcount/termination/padding/inner+outerCRCpaid;everyframecannotgrow.',
               'Allcandidate rankpackets/menu/rankarraysretained,includingfallbacklosers. Coeffentropy/qmap/exactHUDunchanged. Fixtures/archive/metrics/independentdecode/network/displayexcludedfromtranscodeclock.',
               'Nochangedmodechoices,heldoutgameplay,freshnativecomparison,FPGAresources/clockorphysical30fpsproof. LogicalcoderstateisnotPythonmemoryorfittedhardware.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
