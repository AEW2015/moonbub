#!/usr/bin/env python3
"""Independent byte/state replay for exact HU32/HU33 host optimization.

No new fast encoder/helper is imported. All actual inputs and outputs are
decoded by the frozen HU25/HX32/HX33 receive implementations against the same
last accepted HUD reference. Preparation and timing evidence is scoped to the
HX32→HX33 component; HU25 generation remains externally paid.
"""
from pathlib import Path
import hashlib,heapq,importlib.util,json,math,statistics,sys
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('hudfast42_frozen_receive_bootstrap',HERE.parent/'python-game-canonical-v36-study/verify.py')
frozen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=frozen;spec.loader.exec_module(frozen)
hud=frozen.hud;protocol=hud.p
OLD=HERE.parent/'python-game-control-qual-v40-study'
SOURCE=HERE.parent/'python-game-source-v40-study'

def load(path):return json.loads(Path(path).read_text())
def raw(desc,folder=HERE):return frozen.frozen.raw(desc,folder)

def exact_wire(candidate,reference):
    if type(candidate)is not bytes or type(reference)is not bytes or candidate!=reference:
        raise ValueError('exact HUD wire identity required')

class HudState:
    def __init__(self):self.reference=None;self.rid=protocol.NO_REF;self.last=-1
    def fork(self):
        result=HudState();result.reference,result.rid,result.last=self.reference,self.rid,self.last;return result
    def receive(self,packet):
        if type(packet)is not bytes:raise ValueError('immutable HUD packet')
        meta=hud._meta(packet);fid,rid=meta['frame_id'],meta['reference_id']
        if meta['epoch']!=25 or fid<=self.last:raise ValueError('epoch and monotonic HUD publication')
        if (meta['width'],meta['height'],tuple(meta['rectangles']))!=(720,480,frozen.n.RECTS):raise ValueError('fixed HUD geometry')
        key=rid==protocol.NO_REF
        if not key and (self.reference is None or self.rid!=rid):raise ValueError('last accepted HUD reference')
        words,decoded=hud.decode_hud(packet,None if key else self.reference,expected_epoch=25,
            expected_reference_id=None if key else self.rid)
        self.reference,self.rid,self.last=words,fid,fid
        return words,decoded

def paired_timings(row):
    values=row['paired_timing_ms']
    if (not isinstance(values,dict) or set(values)!={'slow','fast'} or
            any(not isinstance(v,list) or len(v)!=3 for v in values.values()) or
            any(type(x)not in (int,float) or not math.isfinite(x) or x<=0 for v in values.values() for x in v)):
        raise ValueError('three finite positive slow/fast timing samples')
    medians={k:statistics.median(v) for k,v in values.items()}
    assert medians==row['paired_median_ms']
    expected=[list(('slow','fast') if (row['id']+i)%2==0 else ('fast','slow')) for i in range(3)]
    assert row['paired_order']==expected
    return medians

def check_reference_metadata(reference,candidate):
    """Every old non-clock decision must survive; new counters may be added."""
    if isinstance(reference,dict):
        assert isinstance(candidate,dict)
        for key,value in reference.items():
            if key.endswith('_ms') or key.endswith('_wall_ms'):continue
            assert key in candidate,('missing decision field',key)
            check_reference_metadata(value,candidate[key])
    elif isinstance(reference,list):
        assert isinstance(candidate,list) and len(candidate)==len(reference)
        for a,b in zip(reference,candidate,strict=True):check_reference_metadata(a,b)
    else:assert reference==candidate,('decision metadata',reference,candidate)

def huffman_plan(values):
    """Own histogram/tree cost oracle, without constructing encoded bitstrings."""
    symbols,counts=np.unique(np.asarray(values).reshape(-1),return_counts=True)
    if not len(symbols):return 0,dict(symbols=0,maximum_code_bits=0,coded_bits=0,values=0)
    heap=[(int(n),serial,int(s)) for serial,(s,n) in enumerate(zip(symbols,counts,strict=True))]
    heapq.heapify(heap);serial=len(heap)
    while len(heap)>1:
        a,b=heapq.heappop(heap),heapq.heappop(heap)
        heapq.heappush(heap,(a[0]+b[0],serial,(a[2],b[2])));serial+=1
    depths={};stack=[(heap[0][2],0)]
    while stack:
        node,depth=stack.pop()
        if isinstance(node,int):depths[node]=max(1,depth)
        else:stack.extend(((node[0],depth+1),(node[1],depth+1)))
    maximum=max(depths.values())
    if maximum>16:raise ValueError('code-depth')
    bits=0 if len(symbols)==1 else sum(int(n)*depths[int(s)] for s,n in zip(symbols,counts,strict=True))
    return 6+2*len(symbols)+(bits+7)//8,dict(symbols=len(symbols),maximum_code_bits=maximum,coded_bits=bits,values=int(counts.sum()))

def rice_plan(values):
    a=np.asarray(values,np.int64)
    if not len(a):return 0,0
    sizes=[int((a>>k).sum())+len(a)*(k+1) for k in range(15)]
    k=min(range(15),key=lambda k:sizes[k]);return k,sizes[k]

def channel_plan(values):
    a=np.asarray(values,np.uint16).reshape(-1);trials=[]
    for scheme in range(3):
        if scheme==0:symbols=a;runs=np.empty(0,np.int64)
        elif scheme==1:
            indices=np.flatnonzero(a);symbols=a[indices];runs=np.diff(np.r_[-1,indices,len(a)])-1
        else:
            starts=np.r_[0,np.flatnonzero(a[1:]!=a[:-1])+1];symbols=a[starts];runs=np.diff(np.r_[starts,len(a)])-1
        try:size,stats=huffman_plan(symbols)
        except ValueError:
            trials.append(dict(scheme=scheme,rejected='code-depth'));continue
        k,nb=rice_plan(runs)
        trials.append(dict(scheme=scheme,k=k,events=len(symbols),runs=len(runs),rice_bits=nb,
            bytes=14+size+(nb+7)//8,huffman=stats,rice_k_trials=15 if len(runs) else 0))
    eligible=[t for t in trials if 'bytes'in t]
    if not eligible:raise ValueError('all-channel-Huffman-depth')
    return dict(selected=min(eligible,key=lambda t:t['bytes']),trials=trials)

def components(words):
    return ((words>>11).astype(np.int32),((words>>5)&63).astype(np.int32),(words&31).astype(np.int32))

def mapped_channels(words,prediction,mode):
    values=components(words);pred=None if prediction is None else components(prediction);result=[]
    for axis,a in enumerate(values):
        if mode&7==0:delta=a.copy();delta[:,1:]-=a[:,:-1]
        else:delta=a-pred[axis]
        if mode&8:before=delta.copy();delta[:,1:]-=before[:,:-1]
        result.append(np.where(delta>=0,2*delta,-2*delta-1).reshape(-1))
    return result

def recipes(reference,kind,payload,width,height):
    result=[(0,None,0)]
    if reference is not None:
        result.extend(((1,reference,0),(9,reference,0)))
        if kind==2:
            old_mode=hud.h.HEADER.unpack_from(payload)[2]
            if old_mode in (hud.h.GLOBAL,hud.h.TILED):
                mode=2 if old_mode==hud.h.GLOBAL else 3
                prediction,n=hud.old._motion_reference(reference,mode,payload[hud.h.HEADER.size:-4],width,height)
                result.extend(((mode,prediction,n),(mode|8,prediction,n)))
    return result

def check_recipe_plans(current,reference,baseline_meta,meta32,meta33,work32,work33):
    by_rect={p['rect']:p['words'] for p in reference or ()};recipe_count=channel_schemes=0
    for patch,old_kind,old_payload,p32,p33,k32,k33,s32,s33 in zip(current,baseline_meta['types'],baseline_meta['payloads'],
            meta32['payloads'],meta33['payloads'],meta32['types'],meta33['types'],work32['patches'],work33['patches'],strict=True):
        words=patch['words'];reference_words=by_rect.get(patch['rect'])
        menu=recipes(reference_words,old_kind,old_payload,words.shape[1],words.shape[0])
        assert len(menu)==len(s32['trials'])==len(s33['trials'])
        best32=(len(old_payload),old_kind,None);best33=(len(p32),k32,None,None)
        for (mode,prediction,prefix),trial32,trial33 in zip(menu,s32['trials'],s33['trials'],strict=True):
            assert trial32['mode']==trial33['mode']==mode
            mapped=mapped_channels(words,prediction,mode)
            try:
                planned=[huffman_plan(a) for a in mapped]
            except ValueError:
                assert trial32.get('rejected')=='code-depth'
            else:
                size=hud.h.FIXED_BYTES+prefix+sum(v[0] for v in planned)
                assert trial32['bytes']==size and trial32['bounded_fit']==(size<=hud.h.MAX_PACKET)
                check_reference_metadata([v[1] for v in planned],trial32['channels'])
                if size<=hud.h.MAX_PACKET and size<best32[0]:best32=(size,3,mode)
            try:
                planned33=[channel_plan(a) for a in mapped]
            except ValueError:
                assert trial33.get('rejected')=='all-channel-Huffman-depth' and trial33['bounded_fit']is False
            else:
                check_reference_metadata(planned33,trial33['channels'])
                size=hud.h.FIXED_BYTES+prefix+sum(v['selected']['bytes'] for v in planned33)
                assert trial33['bytes']==size and trial33['bounded_fit']==(size<=hud.h.MAX_PACKET)
                if size<=hud.h.MAX_PACKET and size<best33[0]:best33=(size,4,mode,planned33)
                channel_schemes+=sum(len(p['trials']) for p in planned33)
            recipe_count+=2
        assert (s32['selected_bytes'],s32['selected_kind'],s32['selected_mode'])==best32
        assert (len(p32),k32)==best32[:2]
        assert (s33['selected_bytes'],s33['selected_kind'],s33['selected_mode'])==best33[:3]
        assert (len(p33),k33)==best33[:2]
        check_reference_metadata(best33[3],s33['selected_channels'])
    return recipe_count,channel_schemes

def main():
    data=load(HERE/'results.json');assert data['schema']=='gamebub-hud-fast-v42'
    assert data['physical_30fps_proven']is False and data['new_RTL_implemented']is False and data['HEVC_AV1_superiority_proven']is False
    for name,tag in data['source_sha256'].items():
        path=Path(name);assert not path.is_absolute() and '..'not in path.parts
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==tag,path
    prior=load(OLD/'results.json');source_manifest=load(SOURCE/'manifest.json')
    scenes=['mass-effect-10000','mass-effect-4500','mass-effect-1600','mass-effect-combat']
    assert [c['scene'] for c in data['cases']]==scenes
    frames=word_count=identical32=identical33=recipe_count=scheme_count=0
    for case in data['cases']:
        oldcase=next(c for c in prior['cases'] if c['scene']==case['scene'])
        src_case=next(c for c in source_manifest['cases'] if c['name']==case['scene'])
        assert [r['id'] for r in case['rows']]==list(range(6)) and all(type(r['id'])is int for r in case['rows'])
        accepted=HudState();checks=[]
        for row,old,src in zip(case['rows'],oldcase['rows'][:6],src_case['frames'][:6],strict=True):
            fid=row['id'];rid=protocol.NO_REF if fid==0 else fid-1
            assert old['accepted']is True and row['reference_id']==old['reference_id']==rid
            assert row['previous_accepted_id']==old['previous_accepted_id']==(None if fid==0 else fid-1)
            assert row['source_rgb_sha256']==old['source_rgb_sha256']==src['canvas_rgb_sha256']
            canvas=raw(src['canvas_rgb24'],SOURCE)
            assert hashlib.sha256(canvas).hexdigest()==row['source_rgb_sha256'] and len(canvas)==480*720*3
            words=frozen.m.C.corpus.rgb565(np.frombuffer(canvas,np.uint8).reshape(480,720,3))
            assert hashlib.sha256(words.astype('<u2').tobytes()).hexdigest()==old['source_rgb565_sha256']==src['rgb565_sha256']
            packets={name:raw(row[name]) for name in ('HU25','HX32','HX33_selected')}
            for name,packet in packets.items():exact_wire(packet,raw(old['hud_packets'][name],OLD))
            identical32+=1;identical33+=1
            assert len(packets['HX33_selected'])<=len(packets['HX32'])<=len(packets['HU25'])<=49152
            incoming=bytes(16) if accepted.reference is None else protocol.hud_tag(accepted.reference,720,480)
            assert row['reference_tag']==incoming.hex()
            snapshot=(accepted.reference,accepted.rid,accepted.last);incoming_words=accepted.reference
            decoded={};metas={};branches={}
            for name,packet in packets.items():
                branch=accepted.fork();out,meta=branch.receive(packet)
                assert (meta['epoch'],meta['frame_id'],meta['reference_id'])==(25,fid,rid)
                assert meta['reference_tag']==incoming
                assert tuple(meta['rectangles'])==frozen.n.RECTS
                expected=[words[y:y+h,x:x+w] for x,y,w,h in frozen.n.RECTS]
                for actual,patch in zip(out,expected,strict=True):np.testing.assert_array_equal(actual['words'],patch)
                decoded[name]=out;metas[name]=meta;branches[name]=branch
            assert accepted.reference is snapshot[0] and (accepted.rid,accepted.last)==snapshot[1:]
            if accepted.reference is not None:assert protocol.hud_tag(accepted.reference,720,480)==incoming
            for name in ('HX32','HX33_selected'):
                for a,b in zip(decoded[name],decoded['HU25'],strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            for meta in metas.values():assert meta['reconstructed_tag'].hex()==row['output_hud_tag']==old['hud_tag']
            assert row['exact_hud_words']==sum(p['words'].size for p in decoded['HX33_selected'])==21120
            check_reference_metadata(row['slow32'],row['fast32']);check_reference_metadata(row['slow33'],row['fast33'])
            check_reference_metadata(old['hx32_work']['patches'],row['slow32']['patches'])
            check_reference_metadata(old['hx33_work']['patches'],row['slow33']['patches'])
            recipes_checked,schemes_checked=check_recipe_plans(decoded['HU25'],incoming_words,metas['HU25'],metas['HX32'],metas['HX33_selected'],row['fast32'],row['fast33'])
            recipe_count+=recipes_checked;scheme_count+=schemes_checked
            f32,f33=row['fast32'],row['fast33'];w32,w33=f32['work'],f33['work']
            assert f32['baseline_decode_validation_paid']is True and f33['baseline_HU25_and_HX32_decode_validation_paid']is True
            assert f32['cache_used']is False and f33['cache_used']is False
            assert f32['hu25_generation_externally_paid']is True and f33['hu25_generation_externally_paid']is True
            assert f32['baseline_bytes']==len(packets['HU25']) and f32['packet_bytes']==len(packets['HX32'])
            assert f33['hu25_bytes']==len(packets['HU25']) and f33['v32_bytes']==len(packets['HX32']) and f33['packet_bytes']==len(packets['HX33_selected'])
            assert f32['selected_new']==(packets['HX32'][:4]==b'HX32') and f33['selected_new']==(packets['HX33_selected'][:4]==b'HX33')
            p32=sum(p['selected_kind']==3 for p in f32['patches']);p33=[p for p in f33['patches'] if p['selected_kind']==4]
            assert w32['patch_materializations']==p32 and w32['huffman_materializations']==3*p32
            assert w32['rice_k_trials']==w32['rice_materializations']==0
            assert w33['patch_materializations']==len(p33) and w33['rice_materializations']==3*len(p33)
            assert w33['huffman_materializations']==sum(ch['selected']['huffman']['symbols']>0 for p in p33 for ch in p['selected_channels'])
            # This corpus has no whole-recipe depth rejection. Directed tests
            # separately check the depth bound; every successful plan is counted.
            assert all('channels'in t for p in f32['patches'] for t in p['trials'])
            assert w32['huffman_plans']==sum(len(t['channels']) for p in f32['patches'] for t in p['trials'])
            valid_trials=[t for p in f33['patches'] for t in p['trials']]
            assert all(t.get('channels') for t in valid_trials)
            channel_trials=[scheme for t in valid_trials for channel in t['channels'] for scheme in channel['trials']]
            assert w33['huffman_plans']==sum(t['huffman']['symbols']>0 for t in channel_trials if 'huffman'in t)
            assert w33['rice_k_trials']==sum(t['rice_k_trials'] for t in channel_trials if 'rice_k_trials'in t)
            medians=paired_timings(row)
            assert 0<f32['encode_extra_wall_ms']+f33['encode_extra_wall_ms']<=row['paired_timing_ms']['fast'][-1]
            assert 0<row['slow32']['encode_extra_wall_ms']+row['slow33']['encode_extra_wall_ms']<=row['paired_timing_ms']['slow'][-1]
            accepted=branches['HX33_selected']
            assert accepted.rid==accepted.last==fid
            frames+=1;word_count+=row['exact_hud_words'];checks.append((row,medians))
        summary=case['summary'];assert summary['frames']==6
        assert summary['HX32_bytes']==sum(r['HX32']['raw_bytes'] for r,_ in checks)
        assert summary['HX33_selected_bytes']==sum(r['HX33_selected']['raw_bytes'] for r,_ in checks)
        means={k:statistics.mean(m[k] for _,m in checks) for k in ('slow','fast')}
        for k,value in means.items():assert math.isclose(summary['mean_paired_medians_ms'][k],value,abs_tol=1e-10)
        assert math.isclose(summary['paired_stage_ratio'],means['slow']/means['fast'],abs_tol=1e-12)
        for field in ('huffman_plans','huffman_materializations','rice_k_trials','rice_materializations'):
            assert summary['fast_'+field]==sum(r[v]['work'][field] for r,_ in checks for v in ('fast32','fast33'))
    assert frames==identical32==identical33==24 and word_count==506880
    print(json.dumps(dict(fresh_HUD_inputs=frames,byte_identical_HX32_outputs=identical32,byte_identical_HX33_outputs=identical33,
        exact_unique_HUD_words=word_count,independent_recipe_plans=recipe_count,independent_channel_scheme_plans=scheme_count,
        validated_accepted_reference_chains=4,source_pins=len(data['source_sha256']),cache_used=False,
        new_encoder_imported=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
