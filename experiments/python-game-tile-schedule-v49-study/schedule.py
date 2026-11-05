"""Finite tile-bank work-demand replay; assumed stage costs, not RTL cycles."""
from pathlib import Path
import hashlib,itertools,json,math,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
PROFILES=(dict(name='shared_conservative',engines=1,decision_cycles=2,renorm_cycles=1,MAC_lanes=8,output_lanes=1),dict(name='parallel_four',engines=4,decision_cycles=2,renorm_cycles=1,MAC_lanes=8,output_lanes=1),dict(name='shared_slow',engines=1,decision_cycles=4,renorm_cycles=1,MAC_lanes=4,output_lanes=1),dict(name='parallel_optimistic',engines=4,decision_cycles=1,renorm_cycles=0,MAC_lanes=8,output_lanes=8))
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(desc):
 p=Path(desc['path']);assert not p.is_absolute() and '..' not in p.parts;stored=(HERE/p).read_bytes();assert digest(stored)==desc['stored_sha256'];d=zlib.decompressobj();b=d.decompress(stored,desc['raw_bytes']+1);assert d.eof and not d.unused_data and not d.unconsumed_tail and len(b)==desc['raw_bytes'] and digest(b)==desc['raw_sha256'];return b

def simulate(entropy,inverse,banks):
 if type(banks)is not int or banks not in(1,2):raise ValueError('one or two coefficient banks')
 if len(entropy)!=len(inverse) or not len(entropy):raise ValueError('nonempty equal work vectors')
 eprev=iprev=0;done=[];wait=0;first=None
 for i,(e,v) in enumerate(zip(entropy,inverse,strict=True)):
  if int(e)!=e or int(v)!=v or e<0 or v<0:raise ValueError('nonnegative integral component work')
  released=done[i-banks] if i>=banks else 0;start=max(eprev,released);wait+=start-eprev;eprev=start+int(e);iprev=max(iprev,eprev)+int(v);done.append(iprev)
  if first is None:first=iprev
 return dict(component_finish_cycles=iprev,first_tile_finish_cycles=first,entropy_stage_cycles=int(sum(entropy)),inverse_stage_cycles=int(sum(inverse)),entropy_backpressure_wait_cycles=wait,coefficient_banks=banks,coefficient_output_bank_bytes=128*banks)

def service(trace,profile,mode):
 offset=0 if mode=='eager' else 8;dec=trace[:,offset:offset+8:2].astype(np.int64);renorm=trace[:,offset+1:offset+8:2].astype(np.int64);band=dec*profile['decision_cycles']+renorm*profile['renorm_cycles']
 e=band.sum(axis=1) if profile['engines']==1 else band.max(axis=1)
 # Assumed 8 cycles to clear a64-word bank and one serial write per nonzero.
 e+=8+trace[:,20].astype(np.int64)
 # Bit-serial interval preload and guard reads. Per-plane start/end charged.
 e[0]+=(64 if profile['engines']==1 else 16);e[-1]+=(8 if profile['engines']==1 else 2)
 lanes=profile['MAC_lanes'];inv=(trace[:,20].astype(np.int64)+lanes-1)//lanes
 inv+=(trace[:,16].astype(np.int64)+lanes-1)//lanes;inv+=(trace[:,17].astype(np.int64)+lanes-1)//lanes
 inv+=16*(trace[:,18]==2);inv+=(64+profile['output_lanes']-1)//profile['output_lanes']
 return e,inv

def build():
 d=json.loads((HERE/'results.json').read_text());rows=[]
 for c in d['cases']:
  for f in c['rows']:
   planes=[np.frombuffer(raw(p['trace']),'<u4').reshape(p['blocks'],21) for p in f['planes']]
   for profile in PROFILES:
    for mode in('eager','deferred'):
     parts=[service(t,profile,mode) for t in planes];e=np.concatenate([a for a,b in parts]);v=np.concatenate([b for a,b in parts])
     for banks in(1,2):
      work=simulate(e,v,banks);rows.append(dict(scene=c['scene'],id=f['id'],profile=profile['name'],mode=mode,banks=banks,work=work,component_ms_at50MHz=work['component_finish_cycles']/50000,component_ms_at100MHz=work['component_finish_cycles']/100000))
 summaries=[]
 for profile in PROFILES:
  for mode in('eager','deferred'):
   for banks in(1,2):
    selected=[r for r in rows if(r['profile'],r['mode'],r['banks'])==(profile['name'],mode,banks)];values=np.array([r['work']['component_finish_cycles'] for r in selected],np.int64)
    summaries.append(dict(profile=profile['name'],mode=mode,banks=banks,frames=len(selected),mean_component_cycles=float(values.mean()),maximum_component_cycles=int(values.max()),component_p95_cycles=float(np.percentile(values,95)),component_p99_cycles=float(np.percentile(values,99)),component_frames_over33_33ms_at50MHz=int(np.count_nonzero(values>50000000/30)),component_frames_over33_33ms_at100MHz=int(np.count_nonzero(values>100000000/30))))
 pins={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in(HERE/'schedule.py',HERE/'results.json')}
 return dict(schema='gamebub-tile-schedule-v49-work-demand',source_sha256=pins,profiles=PROFILES,rows=rows,summary=summaries,scope=['ExactfinitebankreplayoftheASSUMEDper-tilestageservicesfromactualeventcounts;notcycle-accurateRTL.','Sharedor4independentarithmeticengines;4enginecaseassumesindependentcompressedreservoirrefill/portsandstate,unprovedresourcefit.','MACservicecountsnonzerodequantandsymmetricfirst/secondproducts;equalzero/DCshortcuts,assumed16complexround/controlcycles and1or8outputpixels/cycle.','Assumed8cyclebankclearandserialnonzerowrites;16bitserialintervalpreloadperstream+2guardreads.','Frameinputalreadyavailable;reference/outputmemory,CRC/SHA/HUD/color/scanout,network,ESP32/QSPIandportarbitrationexcluded.','Nominal50/100MHzconversionsarecomponentprojections,notroutedclock/end-to-end/physical30fpsproof.','Bankbytescoveronly128Bcoefficientoutputs;inverse/prediction/packet/reservoir/metadata/framebuffersadditional.'])
def main():
 target=HERE/'schedule.json';d=build()
 if '--check' in sys.argv:assert json.loads(target.read_text())==json.loads(json.dumps(d))
 else:target.write_text(json.dumps(d,indent=2)+'\n')
 print(json.dumps(dict(modeled_frames=len(d['rows']),summary=d['summary']),indent=2),flush=True)
if __name__=='__main__':main()
