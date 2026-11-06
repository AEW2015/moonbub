#!/usr/bin/env python3
"""Selected causal DAG replays with actual alias stores and descriptor work."""
import copy,datetime,gzip,hashlib,importlib.util,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
V87=ROOT/'experiments/python-gamebub-v87/coupled'

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def transform(original,snapshot,alias):
 work=copy.deepcopy(original['workload']);jobs=work['jobs'];byid={j['id']:j for j in jobs};nextid=max(byid)+1
 def add(kind,resource,duration,deps=(),**fields):
  nonlocal nextid
  ident=nextid;nextid+=1;j=dict(id=ident,kind=kind,resource=resource,duration=duration,deps=sorted(set(deps)),**fields)
  jobs.append(j);byid[ident]=j;return ident
 oldcomplete=work['complete'];mapreads=mapwrites=0;removed_copy_stores=added_noncopy_stores=removed_copy_reads=0
 if alias:
  clear=add('alias_descriptor_clear','alias_map_w',8100,[work['frontend']['metadata']])
  for group in work['groups']:byid[group['start']]['deps']=sorted(set(byid[group['start']]['deps']+[clear]))
  tiles={}
  for j in list(jobs):
   if 'tile' in j and j['kind'] in ('map_lookup','reference_read','canonical_write','reconstruct','copy_ready','const_generate','map_shadow_entry'):
    tiles.setdefault(j['tile'],{})[j['kind']]=j
  dirty=set(snapshot['dirty'])
  for tile in range(8100):
   entry=tiles[tile];copy_tile=bool(snapshot['copy'][tile]);g=entry['map_lookup']['group']
   n=int(snapshot['previous'] is not None)+int(snapshot['presented'] is not None)
   lookup=add('alias_descriptor_lease_lookup','alias_map_r',n,[entry['map_lookup']['id']],tile=tile,group=g,logical_entries=n)
   mapreads+=n
   reference=entry.get('reference_read')
   if reference:
    reference['deps']=sorted(set(reference['deps']+[lookup]))
    if copy_tile and tile not in dirty:
     reference.update(duration=0,BL8=0,alias_elided=True);removed_copy_reads+=1
    reference['physical_slot']=snapshot['previous'][tile]
    reference['physical_address']=snapshot['previous'][tile]*518400+tile*64
   store=entry.get('canonical_write')
   payload=entry.get('reconstruct',entry.get('copy_ready',entry.get('const_generate')))
   assert payload is not None
   if copy_tile:
    if store:store.update(duration=0,BL8=0,alias_elided=True);removed_copy_stores+=1
    data_done=lookup
   else:
    if store:
     store['deps']=sorted(set(store['deps']+[lookup]));data_done=store['id']
    else:
     invalid=add('alias_added_store_invalidate','map_w',1,[entry['map_lookup']['id']],tile=tile,group=g,entries=1)
     data_done=add('canonical_write','memory',64,[payload['id'],lookup,invalid],tile=tile,group=g,BL8=4,alias_added=True)
     added_noncopy_stores+=1;store=byid[data_done]
    store['physical_slot']=snapshot['candidate'][tile];store['physical_address']=snapshot['candidate'][tile]*518400+tile*64
   described=add('alias_descriptor_valid_write','alias_map_w',1,[data_done],tile=tile,group=g,logical_entries=1)
   mapwrites+=1
   entry['map_shadow_entry']['deps']=sorted(set(entry['map_shadow_entry']['deps']+[described]))
  pub=add('alias_pointer_publication','alias_map_w',2,[oldcomplete])
 else:pub=oldcomplete
 # One64Btile read buffer, sequential canonical tile gather; not rasterLCD.
 previous=pub
 for tile in range(8100):
  deps=[previous]
  if alias:deps=[add('alias_scanout_descriptor','alias_map_r',1,deps,tile=tile,logical_entries=1)]
  previous=add('base_scanout_gather_read','memory',72,deps,tile=tile,BL8=4)
 complete=add('base_gather_complete',None,0,[previous]);work['complete']=complete
 work['alias_trace']=dict(enabled=alias,decode_complete=pub,scanout_complete=complete,map_read_entries=mapreads+8100 if alias else 0,map_write_entries=mapwrites+8100 if alias else 0,publication_cycles=2 if alias else 0,removed_COPY_store_tiles=removed_copy_stores,added_nonCOPY_store_tiles=added_noncopy_stores,removed_clean_COPY_reference_tiles=removed_copy_reads)
 return work

def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'probe-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
 source_report=json.loads((AREA/'results.json').read_text());selected={(r['cohort'],r['fid']):ROOT/r['path'] for r in source_report['selected_traces']}
 extra=json.loads((AREA/'extra-case.json').read_text());assert extra['status']=='PASS_FROZEN_REBUILD_AND_ADDED_STORE_CASE'
 selected[0,3]=ROOT/extra['trace']
 scheduler=load('v88_probe_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py');generic=load('v88_probe_audit',ROOT/'experiments/python-gamebub-v83/audit.py');credits=load('v88_probe_credits',ROOT/'experiments/python-gamebub-v84/credits.py')
 oldaudit=json.loads((V87/'verification.json').read_text());paths=[ROOT/n for n in oldaudit['artifact_sha256'] if n.endswith('.json.gz') and '/attempts/' in n and 'witness-' in n]
 paths=[p for p in paths if p.name in ('witness-c0-f0-low_lanes2.json.gz','witness-c0-f1-low_lanes2.json.gz','witness-c3-f50-low_lanes2.json.gz','witness-c3-f50-high_lanes2.json.gz')]
 assert len(paths)==4
 paths.append(ROOT/extra['original_witness'])
 pins={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'experiments/python-gamebub-v83/scheduler.py',ROOT/'experiments/python-gamebub-v83/audit.py',ROOT/'experiments/python-gamebub-v84/credits.py',AREA/'results.json',AREA/'extra-case.json',*paths,*selected.values()]}
 rows=[]
 for path in paths:
  with gzip.open(path,'rt') as f:original=json.load(f)
  config=original['config'];cohort=0 if 'c0-' in path.name else 3;fid=0 if '-f0-' in path.name else 1 if '-f1-' in path.name else 3 if '-f3-' in path.name else 50
  with gzip.open(selected[cohort,fid],'rt') as f:snapshot=json.load(f)
  for alias in (False,True):
   work=transform(original,snapshot,alias);caps=dict(original['capacities'],alias_map_r=1,alias_map_w=1)
   result=scheduler.schedule(work['jobs'],caps,config['windows'],retain_timeline=True)
   audit=generic.verify(work['jobs'],result['timeline'],caps,config['windows'],work['groups'],4)
   stages=credits.audit_lifetimes(work,result['timeline'])
   timed={r['id']:r for r in result['timeline']};decode=timed[work['alias_trace']['decode_complete']]['finish']
   if alias:
    data_read=sum(j.get('BL8',0) for j in work['jobs'] if j['kind'] in ('reference_read','HUD_read'))
    data_write=sum(j.get('BL8',0) for j in work['jobs'] if j['kind'] in ('canonical_write','HUD_write'))
    assert data_read==snapshot['accounts']['onchip']['decoder_data_read_BL8']
    assert data_write==snapshot['accounts']['onchip']['data_write_BL8']
    assert work['alias_trace']['added_nonCOPY_store_tiles']==sum(not snapshot['copy'][t] and snapshot['old_elided'][t] for t in range(8100))
   filename=f'c{cohort}-f{fid}-{config["name"]}-'+('alias' if alias else 'control')+'.json.gz';witness=out/filename
   with gzip.open(witness,'wt') as f:json.dump(dict(source_witness=str(path.relative_to(ROOT)),source_trace=str(selected[cohort,fid].relative_to(ROOT)),alias=alias,capacities=caps,windows=config['windows'],workload=work,result=result,audit=audit,credits=stages),f,separators=(',',':'))
   rows.append(dict(cohort=cohort,fid=fid,configuration=config['name'],alias=alias,conditional_decode_ms=decode/100000,conditional_base_gather_complete_ms=result['finish_cycles']/100000,memory_work_cycles=audit['resource_work_cycles']['memory'],alias_changes=work['alias_trace'],witness=str(witness.relative_to(ROOT)),witness_sha256=sha(witness),timeline_sha256=hashlib.sha256(json.dumps(result['timeline'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),credit_peaks=stages))
 assert pins=={n:sha(ROOT/n) for n in pins}
 report=dict(schema='cu66-v88-selected-alias-coupled-v1',status='PASS_SELECTED_CAUSAL_ALIAS_REPLAY',unique_sources=4,schedules=10,rows=rows,source_sha256=pins,scope='Selected fixedCS86 modelgraphs withactualaliasnonCOPYstores,descriptorlogicalportsandpostvalidationYUVgather. Assumedcosts, nothardwareorcontinuousdisplay. No entropyformat substitution.')
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'probe.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('V88_ALIAS_COUPLED_PASS',len(rows),out/'results.json')

if __name__=='__main__':main()
