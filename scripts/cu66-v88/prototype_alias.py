#!/usr/bin/env python3
"""Actual alias addresses, descriptor sensitivity and native source parity."""
import datetime,gzip,hashlib,importlib.util,json,statistics,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v88/alias'
CONTROL=ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'


def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
 native=load('v88_alias_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
 layout=load('v88_layout',ROOT/'experiments/python-gamebub-v87/alias/prototype.py')
 trace=load('v88_trace',AREA/'trace.py')
 commitment=load('v88_commitment',ROOT/'scripts/cu66-v82/prototype_commitment.py')
 residency=load('v88_residency',ROOT/'fpga/experiments/cu66-v81/residency/model.py')
 sources=[Path(__file__).resolve(),AREA/'trace.py',ROOT/'experiments/python-gamebub-v87/alias/prototype.py',ROOT/'experiments/python-gamebub-v82/native/data.py',ROOT/'experiments/python-gamebub-v82/native/index.json',ROOT/'scripts/cu66-v82/prototype_commitment.py',ROOT/'fpga/experiments/cu66-v81/residency/model.py',CONTROL]
 pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
 controls={(r['cohort'],r['fid']):r for r in map(json.loads,CONTROL.read_text().splitlines())}
 rows=[];selected=[];cohort=None
 with (out/'frames.jsonl').open('w') as stream:
  for frame in native.iter_frames():
   if frame['cohort']!=cohort:
    cohort=frame['cohort'];slots=layout.TileSlots();tree=commitment.CommitmentTree(granularity=16);banks=residency.Residency(8100);accepted_map=presented_map=None;descriptor_banks=[bytearray(b'\xff'*trace.MAP_STRIDE) for _ in range(3)]
   frame=dict(frame,generation=frame['ordinal']+1);control=controls[cohort,frame['fid']]
   plan=tree.plan(frame,frame['copy_ref_mask']);dirty={t for g in plan['recomputed_groups'] for t in g['tile_indices']}
   assert (plan['root'].hex(),plan['seal'].hex())==(control['root'],control['seal'])
   previous=None if slots.accepted is None else list(slots.accepted);presented=None if slots.presented is None else list(slots.presented)
   slots.begin(frame['tiles'],frame['copy_ref_mask']);candidate=list(slots.candidate)
   assert slots.image(candidate)==frame['tiles']
   before_display=slots.image(presented);before_reference=slots.image(previous)
   if previous is not None:assert before_reference==banks.banks[banks.reference]
   slots.commit(frame['fid'],layout.digest(frame['tiles']));slots.present()
   gathered=[slots.physical[candidate[t]][t] for t in range(8100)]
   assert gathered==frame['tiles'] and slots.image(slots.presented)==frame['tiles']
   # Independently reproduce the actual frozen three-bank residency decision.
   bank=0 if banks.reference is None else (banks.reference+1)%3
   elided=[not frame['key'] and bool(frame['same_mask'][i]) and bool(banks.masks[i]&(1<<bank)) for i in range(8100)]
   assert 8100-sum(elided)==control['physical_store_tiles']
   banks.begin(frame['fid'],frame['packet_sha256'],bank,frame['key'],frame['tiles'],frame['same_mask']);banks.step();banks.commit(authenticated=True);banks.present();tree.commit(plan)
   assert banks.banks[banks.reference]==gathered
   candidate_map=next(i for i in range(3) if i not in (accepted_map,presented_map))
   roles=(accepted_map,presented_map,candidate_map)
   events=trace.commands(frame,previous,candidate,presented,dirty,map_roles=roles)
   trace.validate_descriptors(events,descriptor_banks)
   accounts={p:trace.account(events,p) for p in ('onchip','cached','uncached')}
   a=accounts['onchip'];expected_ref=sum(not frame['key'] and not frame['hidden_mask'][t] and (not frame['copy_ref_mask'][t] or t in dirty) for t in range(8100))*4
   assert a['reference_read_BL8']==expected_ref and a['canonical_write_BL8']==(8100-sum(frame['copy_ref_mask']))*4
   assert a['scanout_read_BL8']==32400 and a['HUD_read_BL8']==a['HUD_write_BL8']==2640
   # The fair baseline gets the same whole-base scanout read traffic and HUD IO.
   baseline_reads=control['logical_BL8']['reference_reads']+2640+32400;baseline_writes=control['logical_BL8']['canonical_writes']+2640
   row=dict(cohort=cohort,fid=frame['fid'],ordinal=frame['ordinal'],key=frame['key'],canonical_sha256=frame['canonical_sha256'],root=control['root'],seal=control['seal'],
            alias_tile_order_sha256=layout.digest(gathered),trace_sha256=trace.digest(events),events=len(events),profiles=accounts,
            frozen_control_data=dict(read_BL8=baseline_reads,write_BL8=baseline_writes,memory_busy_cycles=baseline_reads*18+baseline_writes*16,
                                     decoder_read_BL8=baseline_reads-32400,decoder_memory_busy_cycles=(baseline_reads-32400)*18+baseline_writes*16),
            alias_COPY_tiles=sum(frame['copy_ref_mask']),nonCOPY_new_writes_old_elided=sum(not frame['copy_ref_mask'][t] and elided[t] for t in range(8100)))
   rows.append(row);stream.write(json.dumps(row,separators=(',',':'))+'\n');stream.flush()
   if (cohort,frame['fid']) in ((0,0),(0,1),(3,50)):
    path=out/f'c{cohort}-f{frame["fid"]}-trace.json.gz'
    with gzip.open(path,'wt') as f:json.dump(dict(frame={k:frame[k] for k in ('cohort','fid','key','canonical_sha256')},previous=previous,presented=presented,candidate=candidate,map_roles=roles,hidden=list(frame['hidden_mask']),copy=list(frame['copy_ref_mask']),dirty=sorted(dirty),old_elided=elided,events=events,accounts=accounts),f,separators=(',',':'))
    selected.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),cohort=cohort,fid=frame['fid']))
   accepted_map=presented_map=candidate_map
   if len(rows)%50==0:print('V88_ALIAS_PROGRESS',len(rows),flush=True)
 summaries=[]
 for policy in ('onchip','cached','uncached'):
  differences=[r['frozen_control_data']['memory_busy_cycles']-r['profiles'][policy]['memory_busy_cycles'] for r in rows]
  summaries.append(dict(policy=policy,sources=len(rows),memory_busy_ms=stats([r['profiles'][policy]['memory_busy_cycles']/100000 for r in rows]),decoder_memory_busy_ms=stats([r['profiles'][policy]['decoder_memory_busy_cycles']/100000 for r in rows]),saved_busy_cycles_vs_frozen=stats(differences),improved=sum(d>0 for d in differences),equal=sum(d==0 for d in differences),regressed=sum(d<0 for d in differences)))
 assert len(rows)==457 and pins=={n:sha(ROOT/n) for n in pins}
 report=dict(schema='cu66-v88-addressed-alias-trace-v1',status='PASS_ADDRESSED_ALIAS_AND_NATIVE_PARITY',native_sources=457,profiles=['onchip','cached','uncached'],summaries=summaries,selected_traces=selected,source_sha256=pins,frames_sha256=sha(out/'frames.jsonl'),
             fixed_geometry=[720,480,5400,1350,1350],logical_pixel_bytes=1555200,logical_descriptor_bytes=6075,map_stride_bytes=2048,
             scope=['All nonCOPY tiles physically written, including prior residency-elided nonCOPY; COPYonly aliases accepted tile.',
                    'Actual aligned16B data/HUD/gather addresses and packed2bit descriptor addresses. Data reads include residual prediction anddirtyCOPYleafhash inputs.',
                    'onchipdescriptor entries use nominal1cycle logicalports; cachedexternal uses one16Bword permap plus fullwordcandidate accumulation; uncachedexternal doesentryRMW.',
                    'Complete YUVbase gather read exactlyonce afterpublication. This is data-volume/address proof, not continuousrasterLCD/RGB565/HUDcompositing.',
                    'Frozen baseline gets same32400BL8basegather; original tree/certificate map cost keptseparate in selectedDAGs.',
                    'memorybusy is necessary serialservice accounting18read/16write cycles atassumed100MHz, not measured hardwarecompletion.'],physical_30fps_proven=False,validated_under10ms_proven=False)
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('V88_ALIAS_REPORT',out/'results.json',report['status'],flush=True)

if __name__=='__main__':main()
