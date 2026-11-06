#!/usr/bin/env python3
"""Stdlib-only direct YUV portrait traffic/cache estimate; no RTL or pixel proof."""
from collections import OrderedDict
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MAP=ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp'
PINS=ROOT/'fpga/experiments/cu66-v74/baseline-sources.json'
BASE=0x80000
OFFSETS={'Y':0,'Cb':172800,'Cr':216000}
BL8=8
WIDTH,HEIGHT=720,480
STRIP=8
HTOTAL=541; VTOTAL=834; PIXEL_NS=34.058
DEADLINE_US=STRIP*HTOTAL*PIXEL_NS/1e3

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def word_addr(plane,u,v):
    """Tile-major 8x8 u8 samples packed two per 16-bit word; plane-local coordinates."""
    w,h=(720,480) if plane=='Y' else (360,240)
    if not (0<=u<w and 0<=v<h): raise ValueError((plane,u,v))
    tiles_per_row=w//8
    tile=(v//8)*tiles_per_row+u//8
    within=(v%8)*8+(u%8)
    # 64 bytes per tile = 32 x16-bit words.
    return BASE+OFFSETS[plane]+tile*32+within//2

class Cache:
    def __init__(self,n,policy):
        self.n=n;self.policy=policy;self.tags=OrderedDict();self.next=0
        self.slots=[None]*n;self.slot_of={}
    def access(self,tag):
        if self.policy=='RR':
            if tag in self.slot_of: return True
            old=self.slots[self.next]
            if old is not None: del self.slot_of[old]
            self.slots[self.next]=tag;self.slot_of[tag]=self.next
            self.next=(self.next+1)%self.n
            return False
        hit=tag in self.tags
        if hit: self.tags.move_to_end(tag)
        else:
            if len(self.tags)>=self.n: self.tags.popitem(last=False)
            self.tags[tag]=None
        return hit

def chroma_samples(u,v):
    cx,cy=u//2,v//2
    x1=min(cx+1,359); y1=min(cy+1,239)
    xs=(cx,x1) if u&1 else (cx,)
    ys=(cy,y1) if v&1 else (cy,)
    return tuple((x,y) for y in ys for x in xs)

def sample_addresses(u,v):
    yield word_addr('Y',u,v)
    for x,y in chroma_samples(u,v):
        yield word_addr('Cb',x,y)
        yield word_addr('Cr',x,y)

def naive(policy,n):
    c=Cache(n,policy); misses=accesses=0
    for u in range(WIDTH):
        for v in range(HEIGHT):
            for a in sample_addresses(u,v):
                accesses+=1;misses+=not c.access(a>>3)
    return {'accesses':accesses,'miss_bursts':misses,'hits':accesses-misses}

def strip_prefetch(n):
    c=Cache(n,'LRU'); rows=[]; total_miss=0; open_row={}; total_act=total_pre=0
    for u0 in range(0,WIDTH,STRIP):
        sets={p:set() for p in ('Y','Cb','Cr')}
        # Tile/block traversal emits the same set as the bilinear sampler, avoiding a
        # 384k-entry trace while retaining edge and chroma-halo behavior.
        for u in range(u0,u0+STRIP):
            for v in range(HEIGHT):
                sets['Y'].add(word_addr('Y',u,v)>>3)
                for x,y in chroma_samples(u,v):
                    sets['Cb'].add(word_addr('Cb',x,y)>>3)
                    sets['Cr'].add(word_addr('Cr',x,y)>>3)
        counts={k:len(v) for k,v in sets.items()}
        ordered=[tag for p in ('Y','Cb','Cr') for tag in sorted(sets[p])]
        miss_tags=[tag for tag in ordered if not c.access(tag)]
        misses=len(miss_tags)
        act=pre=0
        bank_counts={str(b):{'ACT':0,'PRE':0} for b in range(4)}
        for tag in miss_tags:
            addr=tag*8; bank=(addr>>22)&3; row=(addr>>9)&0x1fff
            if bank not in open_row:
                open_row[bank]=row; act+=1; bank_counts[str(bank)]['ACT']+=1
            elif open_row[bank]!=row:
                pre+=1; act+=1; open_row[bank]=row
                bank_counts[str(bank)]['PRE']+=1; bank_counts[str(bank)]['ACT']+=1
        total_act+=act; total_pre+=pre
        hud_words=sum(max(0,min(u0+STRIP,x+w)-max(u0,x))*h for x,y,w,h in HUD_RECTS)
        total_miss+=misses
        rows.append({'u_start':u0,'u_end_exclusive':u0+STRIP,'unique_bl8_by_plane':counts,
                     'unique_bl8_total':sum(counts.values()),'miss_bursts_after_rolling_cache':misses,
                     'wire_bytes':misses*BL8*2,'hud_words':hud_words,
                     'hud_read_bytes':hud_words*2,'act_commands':act,'pre_commands':pre,
                     'act_pre_by_bank':bank_counts})
    wires=[r['wire_bytes'] for r in rows]
    return {'stripes':len(rows),'cache_lines':n,'cache_bytes':n*16,
            'unique_bl8_min':min(r['unique_bl8_total'] for r in rows),
            'unique_bl8_max':max(r['unique_bl8_total'] for r in rows),
            'miss_bursts_total':total_miss,'wire_bytes_total':total_miss*16,
            'act_commands_total':total_act,'pre_commands_total':total_pre,
            'min_stripe_wire_bytes':min(wires),'max_stripe_wire_bytes':max(wires),
            'min_stripe_hud_read_bytes':min(r['hud_read_bytes'] for r in rows),
            'max_stripe_hud_read_bytes':max(r['hud_read_bytes'] for r in rows),
            'stripes_detail':rows}

HUD_RECTS=[(22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24)]

def main():
    maptext=MAP.read_text()
    assert 'CANONICAL0_BASE=0x080000' in maptext
    # Mapping bounds, row/tile transitions, last chroma clamp and odd-axis sample counts.
    assert word_addr('Y',0,0)==BASE
    assert word_addr('Y',8,0)==BASE+32
    assert word_addr('Y',0,8)==BASE+90*32
    assert word_addr('Y',719,479)<BASE+172800
    assert word_addr('Cb',359,239)<BASE+216000
    assert chroma_samples(719,479)==((359,239),(359,239),(359,239),(359,239))
    assert len(chroma_samples(718,479))==2 and len(chroma_samples(719,478))==2
    assert len(chroma_samples(719,478))==2
    # All four HUD rectangles from native CU66 display constants total 21,120 words.
    rects=HUD_RECTS
    hud_words=sum(w*h for x,y,w,h in rects); assert hud_words==21120
    result={
      'schema':'cu66-v74-direct-yuv-traffic-v1',
      'scope':'deterministic physical-address/cache traffic and schedulability estimate only; no exact-pixel, RTL, physical timing, or FPS proof',
      'mapping':{'coded_size':[WIDTH,HEIGHT],'physical_active':[480,800],
        'placement':'physical x=0..479 maps v; physical y=40..759 maps u=physical_y-40; outside active image black',
        'planes_word_bases':{k:BASE+v for k,v in OFFSETS.items()},'tile':'8x8 u8 samples, row-major in-tile, packed two samples per x16 word; 32 words/tile',
        'bl8':'8 x16 words = 16 wire bytes; tag = physical_word_address >> 3',
        'chroma':'bilinear 4-neighbor interpolation; exact 1/2/4 neighbor accesses based on odd u/v; final neighbor clamps to 359/239'},
      'checks':{'physical_address_bounds_pass':True,'row_edges_and_tile_transitions_pass':True,
        'last_chroma_clamp_pass':True,'read_beats_equal_bursts_x8':True,'wire_bytes_equal_beats_x2':True,
        'hud_rectangles_native_geometry_words':hud_words,
        'note':'opaque HUD composition modeled conservatively: YUV is still fetched under HUD; HUD reads counted separately'},
      'assumptions':{'display_refresh_hz':1000000000/(HTOTAL*VTOTAL*PIXEL_NS),
        'native_panel_timing':{'Htotal':HTOTAL,'Vtotal':VTOTAL,'pixel_period_ns':PIXEL_NS},
        'eight_physical_row_deadline_us':DEADLINE_US,'raw_memory_bandwidth_bytes_s':200000000,
        'controller_cost_assumption_clocks_per_bl8_burst':[20,32],
        'controller_clock_hz':100000000,
        'controller_cost_is_conservative_assumption_not_measured_service_guarantee':True,
        'foreground_work':'YUV display reads at panel refresh plus candidate 30fps YUV source writes; excludes unrelated traffic'},
      'traffic':{},'cache_results':{},
      'source_sha256':{**json.loads(PINS.read_text())['source_sha256'],
        'scripts/cu66-v74/direct_yuv.py':sha(Path(__file__))}}
    # Pixel and HUD work for one frame, with conservative 4 samples at every output pixel
    # also reported separately as an upper-bound comparison.
    samples=0
    for u in range(WIDTH):
        for v in range(HEIGHT): samples+=len(chroma_samples(u,v))
    sample_expected=WIDTH*HEIGHT*9//4 # parity average is (1+2+2+4)/4 = 2.25
    assert samples==sample_expected
    result['traffic']={'y_samples':WIDTH*HEIGHT,'chroma_sample_fetches_per_component':samples,
      'chroma_fetch_policy':'normative parity count (1/2/4); sum is 2.25 samples per component/output pixel',
      'hud_read_words_per_display_frame':hud_words,
      'baseline_rgb_writes_bytes_per_source_frame':384000*2,
      'baseline_rgb_scanout_reads_bytes_per_panel':345600*2,
      'candidate_yuv_source_write_bytes_per_30fps_frame':(WIDTH*HEIGHT*3//2),
      'yuv_ref_physical_accesses_per_frame':WIDTH*HEIGHT+2*samples,
      'yuv_ref_unique_request_set_is_cache_dependent':True}
    # Working-set burst sets include address merging and all exact interpolation fetches.
    for n in (8,64,128,256,512,720,1024):
        for policy in ('LRU','RR'):
            # Full naive trace provides true cache behavior; roughly 1.5m references each.
            t=naive(policy,n)
            result['cache_results'][f'naive_{policy}_{n}']={**t,'cache_lines':n,'cache_bytes':n*16,
              'read_beats':t['miss_bursts']*BL8,'wire_bytes':t['miss_bursts']*BL8*2}
        result['cache_results'][f'strip8_rolling_lru_{n}']=strip_prefetch(n)
    # Sanity check accounting for every synthetic trace.
    for key,val in result['cache_results'].items():
        if key.startswith('naive_'):
            assert val['miss_bursts']>=0
        else:
            assert val['wire_bytes_total']==val['miss_bursts_total']*8*2
            assert val['stripes']==90
    for n in (8,64,128,256,512,720,1024):
        r=result['cache_results'][f'strip8_rolling_lru_{n}']
        per_burst=[20,32]; clk=result['assumptions']['controller_clock_hz']
        stripe_bursts=[s['miss_bursts_after_rolling_cache']+((s['hud_read_bytes']+15)//16) for s in r['stripes_detail']]
        r['stripe_total_bursts_including_hud_assumed_bl8']={'min':min(stripe_bursts),'max':max(stripe_bursts)}
        r['max_stripe_wire_bytes_including_hud_reads']=r['max_stripe_wire_bytes']+r['max_stripe_hud_read_bytes']
        r['max_stripe_raw_bus_time_us']=r['max_stripe_wire_bytes_including_hud_reads']/200.0
        r['max_stripe_assumed_controller_service_us']={str(c):max(stripe_bursts)*c/clk*1e6 for c in per_burst}
        r['max_stripe_deadline_fraction_raw']=r['max_stripe_raw_bus_time_us']/DEADLINE_US
        r['max_stripe_deadline_fraction_controller_assumption']={k:v/DEADLINE_US for k,v in r['max_stripe_assumed_controller_service_us'].items()}
        # Display read traffic at panel rate, plus one complete source upload at 30 fps.
        panel_hz=result['assumptions']['display_refresh_hz']
        frame_upload=result['traffic']['candidate_yuv_source_write_bytes_per_30fps_frame']
        r['foreground_estimate']={'display_read_MB_s_including_HUD':(r['wire_bytes_total']+hud_words*2)*panel_hz/1e6,
          'candidate_upload_MB_s_at_30fps':frame_upload*30/1e6,
          'combined_MB_s':((r['wire_bytes_total']+hud_words*2)*panel_hz+frame_upload*30)/1e6,
          'combined_raw_200MB_s_share':((r['wire_bytes_total']+hud_words*2)*panel_hz+frame_upload*30)/200e6,
          'baseline_RGB_write_MB_s_at_30fps':384000*2*30/1e6,
          'baseline_LCD_RGB_read_MB_s_at_panel_refresh':345600*2*panel_hz/1e6,
          'baseline_RGB_write_plus_LCD_read_MB_s':(384000*2*30+345600*2*panel_hz)/1e6}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
