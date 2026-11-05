"""Declared memory-traffic scenarios; no fitted board or controller measurement."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=HERE.parent/'python-game-binary-qual-v40-study/results.json'
YUV=720*480*3//2;RGB=720*480*2;HUD=21120*2

def traffic(frame_rate,scanout_rate,reference_taps,average_packet,key_fraction,mode):
 if frame_rate<=0 or scanout_rate<=0 or reference_taps not in(1,2,4) or not 0<=key_fraction<=1 or average_packet<0 or mode not in('materialize_RGB565','scan_YUV420'):raise ValueError('declared positive memory scenario')
 out=dict(reference_YUV_reads=(1-key_fraction)*YUV*frame_rate*reference_taps,normalized_YUV_writes=YUV*frame_rate,compressed_staging_write_read=2*average_packet*frame_rate,HUD_words_update_writes=HUD*frame_rate)
 if mode=='materialize_RGB565':out.update(YUV_composition_reads=YUV*frame_rate,RGB565_frame_writes=RGB*frame_rate,RGB565_scanout_reads=RGB*scanout_rate,HUD_composition_reads=HUD*frame_rate)
 else:out.update(YUV_scanout_reads=YUV*scanout_rate,HUD_scanout_reads=HUD*scanout_rate)
 return dict(mode=mode,frame_rate=frame_rate,scanout_rate=scanout_rate,reference_taps=reference_taps,key_fraction=key_fraction,bytes_per_second_by_operation=out,total_bytes_per_second=sum(out.values()))

def build():
 source=json.loads(SOURCE.read_text());cases=[]
 for c in source['cases']:
  rows=c['rows'][:24];avg=sum(r['complete_bytes'] for r in rows)/len(rows);keys=sum(r['key'] for r in rows)/len(rows)
  for taps in(1,2,4):
   pair=[traffic(30,60,taps,avg,keys,mode) for mode in('materialize_RGB565','scan_YUV420')]
   for d in pair:
    bus=[]
    for MHz in(50,100):
     for efficiency in(.25,.5,.75):
      peak=2*MHz*1000000;effective=peak*efficiency;reserved=.8*effective;bus.append(dict(bus_width_bits=16,memory_clock_MHz=MHz,assumed_effective_fraction=efficiency,assumed_reserved_margin_fraction=.2,effective_bytes_per_second=effective,reserved_budget_bytes_per_second=reserved,under_effective_budget=d['total_bytes_per_second']<=effective,under_reserved_budget=d['total_bytes_per_second']<=reserved))
    d.update(scene=c['scene'],average_complete_packet_bytes=avg,bus_scenarios=bus);cases.append(d)
 stats=dict(logical_YUV_frame_bytes=YUV,logical_RGB565_frame_bytes=RGB,triple_YUV_banks_bytes=3*YUV,triple_RGB565_banks_bytes=3*RGB,double_exact_HUD_banks_bytes=2*HUD,logical_input_plus_output_line_bytes=3600)
 pins={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in(SOURCE,HERE/'memory_budget.py',HERE/'results.json')}
 return dict(schema='gamebub-yuv-scanout-v52-memory-budget',source_sha256=pins,cases=cases,logical_storage=stats,scope=['720x480CODEDcanvas,nominal30decode/60scanoutarescenarioparameters,notverifiedboardpanelgeometry/orientation/timing.','YUVstored8bits/sample,RGB56516bits;1/2/4referencefetchesweightedwithactualfirst24keyfraction;noextraburst/rowoverfetchmodeled.','BothpathswriteYUVreference;RGBpathadditionallyrereadsYUVforcompositionandwrites/scansfullRGB565bank;YUVpathcolors/HUDatline-scanout.','Actualselectedcompletepacketmeansfrom96prefixframes,compressedstagingchargedwrite+readonce;CRC/SHA/retries/metadata/DMAcopies/cachetrafficunmodeled.','AlluncompressedHUDtrafficchargedtosharedbus;separateSRAM/BRAMwouldchangearbitration,notprovenimplemented.','16bit50/100MHzbus,25/50/75%efficiencyand20%marginareexplicitassumptions;nosustainedmeasurementortimingguarantee.','Triplebankstorageisbudgetarithmetic,notprovedbankownership/porting/fences/physicalpartfit.','NoHEVC/AV1compressionwinorphysical30fpsproof.'])
def main():
 d=build();target=HERE/'memory-budget.json'
 if '--check' in sys.argv:assert json.loads(target.read_text())==d
 else:target.write_text(json.dumps(d,indent=2)+'\n')
 print(json.dumps(dict(logical_storage=d['logical_storage'],first_clip_one_tap=[dict(mode=c['mode'],MB_per_s=c['total_bytes_per_second']/1e6) for c in d['cases'][:2]])),flush=True)
if __name__=='__main__':main()
