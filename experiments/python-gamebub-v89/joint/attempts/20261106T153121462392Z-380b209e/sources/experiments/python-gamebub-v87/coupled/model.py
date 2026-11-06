"""Consumer-backpressured CS86 context/backend scheduling; conditional clocks only."""
from __future__ import annotations
import copy

FETCH_FIELDS={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}


def couple(credited,shared,contexts,weights,*,wire_bytes=0,metadata_bytes=0,window=8,dequant_cycles=0):
    """Replace V84 sequential producer with actual per-context observations.

    Existing reference/inverse/output group ownership is preserved. Coefficient
    capacity starts at shared setup and is released by inverse/map consumer,
    never by entropy emission. CRC and metadata scans are parameterized resource
    work; they do not execute a hardware parser or a HUD semantic decoder.
    """
    if type(window)is not int or window<1 or len(shared)!=len(contexts):raise ValueError('window/coverage')
    if any(type(n)is not int or n<0 for n in (wire_bytes,metadata_bytes,dequant_cycles)):raise ValueError('cost inputs')
    work=copy.deepcopy(credited);jobs=work['jobs'];by_id={j['id']:j for j in jobs}
    arrivals=sorted((j for j in jobs if j['kind']=='entropy_tile'),key=lambda j:j['tile'])
    if len(arrivals)!=len(shared):raise ValueError('coverage')
    modes={}
    for j in jobs:
        if j['kind'] in ('map_lookup','inverse'):modes.setdefault(j['tile'],{})[j['kind']]=j
    constraints=work['credits']['constraints']['coefficients']
    if len(constraints)!=len(shared):raise ValueError('coefficient coverage')
    if work['credits']['capacities']['coefficients']!=window:raise ValueError('window/credit mismatch')
    next_id=max(by_id)+1
    def add(kind,resource,duration,deps=(),**fields):
        nonlocal next_id
        ident=next_id;next_id+=1
        j=dict(id=ident,kind=kind,resource=resource,duration=duration,
               deps=sorted(set(x for x in deps if x is not None)),**fields)
        jobs.append(j);by_id[ident]=j;return ident
    prefix=add('outer_crc_scan','fetch',wire_bytes*weights.get('crc_bytes',0))
    metadata=add('metadata_scan','fetch',metadata_bytes*weights.get('header_bytes',0),[prefix])
    # Inputs fully buffered at release. Every provisional producer and HUD store
    # starts after the packet/metadata admission scan; this is conservative
    # scan-before-compute, not authenticated streaming or packet arrival timing.
    for j in jobs[:-2]:
        if j['kind'] in ('group_start','HUD_write'):
            j['deps']=sorted(set(j['deps']+[metadata]))
    setups=[];emits=[];context_last=[None]*4;setup_last=None
    fetch_work=jobs[-2]['duration']+jobs[-1]['duration'];compute_work=[0]*4;emit_work=0
    for tile,(setup,streams) in enumerate(zip(shared,contexts,strict=True)):
        if len(streams)!=4:raise ValueError('context coverage')
        if any(v and n not in FETCH_FIELDS|{'emits'} for n,v in setup.items()):raise ValueError('shared arithmetic')
        group=arrivals[tile]['group']
        deps=[metadata,setup_last,work['groups'][group]['start']]
        prior=None if tile<window else constraints[tile-window]['consumer']
        if prior is not None:deps.append(prior)
        opened=add('shared_setup','fetch',sum(v*weights[k] for k,v in setup.items() if k!='emits'),deps,tile=tile,group=group)
        setups.append(opened);setup_last=opened;fetch_work+=by_id[opened]['duration']
        frontier=[]
        for context,observed in enumerate(streams):
            fc=sum(v*weights[k] for k,v in observed.items() if k in FETCH_FIELDS)
            cc=sum(v*weights[k] for k,v in observed.items() if k not in FETCH_FIELDS)
            fetched=add('context_fetch','fetch',fc,[opened,context_last[context]],tile=tile,context=context)
            done=add('context_compute','arithmetic',cc,[fetched],tile=tile,context=context)
            frontier.append(done);context_last[context]=done;fetch_work+=fc;compute_work[context]+=cc
        emitted=add('tile_emit','emit',setup.get('emits',0)*weights.get('emits',0),[*frontier,emits[-1] if emits else None],tile=tile)
        emits.append(emitted);emit_work+=by_id[emitted]['duration']
        arrival=arrivals[tile];arrival.update(kind='coefficient_arrival',resource=None,duration=0,deps=[emitted])
        constraints[tile]['producer']=opened;constraints[tile]['release_before_production']=prior
        inverse=modes[tile].get('inverse')
        if inverse is not None and dequant_cycles:
            # The same coefficient slot must remain live through dequant AND
            # inverse, so its release stays inverse completion.
            quant=add('dequant','dequant',dequant_cycles,[arrival['id']],tile=tile,group=group)
            inverse['deps']=sorted(set(inverse['deps']+[quant]))
    by_id[work['complete']]['deps']=sorted(set(by_id[work['complete']]['deps']+[metadata,*emits]))
    work['frontend']=dict(setups=setups,emits=emits,consumers=[r['consumer'] for r in constraints],
                          window=window,context_last=context_last,outer_crc=prefix,metadata=metadata,
                          wire_bytes=wire_bytes,metadata_bytes=metadata_bytes,
                          work_cycles=dict(fetch=fetch_work,arithmetic=sum(compute_work),emit=emit_work),
                          context_compute_cycles=compute_work,dequant_cycles_per_residual=dequant_cycles)
    work['counts']['task_count']=len(jobs)
    work['assumptions']['producer']='Actual V86 chunk work on shared fetch/four ordered contexts; admission releases on downstream inverse/map consumer.'
    work['assumptions']['outer_validation']='Full buffered packet CRC pass, then header/mode/qmap/chunk-directory byte scan, on shared fetch; weights hypothetical. No transport/authentication claim.'
    work['assumptions']['unpriced']='HUD entropy/semantic hashing, physical COPY/CONST ports, inverse arithmetic implementation, pixel RAM row timing, LCD/refresh, abort/drain and ESP32/transport remain unqualified.'
    return work


def audit(work,result,lanes):
    """Check actual consumer credit lifetime and per-context resource ordering."""
    by_id={j['id']:j for j in work['jobs']};rows={r['id']:r for r in result['timeline']}
    front=work['frontend'];window=front['window'];events=[];stalls=[]
    for tile,opened in enumerate(front['setups']):
        start=rows[opened]['start'];finish=rows[front['consumers'][tile]]['finish']
        assert finish>=start
        if finish>start:events.extend(((start,1),(finish,-1)))
        if tile>=window:
            assert rows[front['consumers'][tile-window]]['finish']<=start
            assert front['consumers'][tile-window] in by_id[opened]['deps']
            stalls.append(max(0,start-rows[front['emits'][tile-window]]['finish']))
    live=peak=0
    for _,delta in sorted(events):
        live+=delta;assert 0<=live<=window;peak=max(peak,live)
    assert live==0
    last=[None]*4
    for j in work['jobs']:
        if j['kind']=='context_compute':
            context=j['context'];fetch=by_id[j['deps'][0]]
            if last[context] is not None:
                assert last[context] in fetch['deps']
                assert rows[last[context]]['finish']<=rows[fetch['id']]['start']
            last[context]=j['id']
    for resource,total in front['work_cycles'].items():
        assert result['resources'][resource]['work_cycles']==total
    assert result['finish_cycles']>=max(front['work_cycles']['fetch'],(front['work_cycles']['arithmetic']+lanes-1)//lanes)
    ancestors=set();pending=[work['complete']]
    while pending:
        i=pending.pop()
        if i not in ancestors:ancestors.add(i);pending.extend(by_id[i]['deps'])
    assert ancestors==by_id.keys(),'complete fence omits work'
    return dict(coefficient_peak_slots=peak,consumer_release_wait_max_cycles=max(stalls,default=0),
                frontend_work_cycles=front['work_cycles'],all_tasks_in_completion_fence=True)
