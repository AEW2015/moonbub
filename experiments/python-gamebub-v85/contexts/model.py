"""Prospective arithmetic-lane/fetch rendezvous DAG; not RTL clock behavior."""
FETCH_FIELDS = {'stream_bytes','raw_bytes','header_bytes','crc_bytes'}


def build(shared, contexts, weights, window):
    if type(window)is not int or window<1 or len(shared)!=len(contexts):
        raise ValueError('window/coverage')
    jobs=[];emit=[];context_last=[None]*4;setup_last=None
    compute_work=[0]*4;fetch_work=emit_work=0
    def add(kind,resource,duration,deps=(),**fields):
        ident=len(jobs)
        jobs.append(dict(id=ident,deps=sorted(set(x for x in deps if x is not None)),
                         kind=kind,resource=resource,duration=duration,**fields))
        return ident
    for tile,(setup,streams) in enumerate(zip(shared,contexts,strict=True)):
        if len(streams)!=4:
            raise ValueError('four contexts required')
        # The observed native shared work is CRC/header and emission only.
        if any(value and name not in FETCH_FIELDS|{'emits'} for name,value in setup.items()):
            raise ValueError('unmodeled shared arithmetic primitive')
        shared_cost=sum(value*weights[name] for name,value in setup.items() if name!='emits')
        admission=[setup_last]
        if tile>=window:admission.append(emit[tile-window])
        opened=add('shared_setup','fetch',shared_cost,admission,tile=tile)
        setup_last=opened;fetch_work+=shared_cost
        frontier=[]
        for context,work in enumerate(streams):
            fetched=sum(value*weights[name] for name,value in work.items() if name in FETCH_FIELDS)
            computed=sum(value*weights[name] for name,value in work.items() if name not in FETCH_FIELDS)
            fetch=add('context_fetch','fetch',fetched,[opened,context_last[context]],tile=tile,context=context)
            done=add('context_compute','arithmetic',computed,[fetch],tile=tile,context=context)
            context_last[context]=done;frontier.append(done)
            compute_work[context]+=computed;fetch_work+=fetched
        emitted=add('tile_emit','emit',setup.get('emits',0)*weights.get('emits',0),
                    [*frontier,emit[-1] if emit else None],tile=tile)
        emit.append(emitted);emit_work+=jobs[emitted]['duration']
    complete=add('complete',None,0,[emit[-1]] if emit else [])
    return dict(jobs=jobs,complete=complete,emissions=emit,window=window,
                work=dict(fetch=fetch_work,emit=emit_work,context_compute=compute_work),
                assumptions=['One shared nonpreemptive fetch/control server; one emitter.',
                             'Per-context order retained; each tile waits all four context frontiers.',
                             'Context byte-fetch batch precedes its arithmetic batch for that tile; this is a scheduling abstraction.',
                             'Setup/header prefetch may overlap prior arithmetic within the admitted window.',
                             'Tile window releases on emission to an immediate external consumer; no inverse/display/ESP32 path.'])


def audit(work, result, lanes):
    rows={r['id']:r for r in result['timeline']};jobs={j['id']:j for j in work['jobs']}
    assert rows.keys()==jobs.keys()
    events={r:[] for r in ('fetch','arithmetic','emit')}
    totals={r:0 for r in events};starts={};finishes={}
    for ident,job in jobs.items():
        row=rows[ident]
        assert 0<=row['start']<=row['finish'] and row['finish']-row['start']==job['duration']
        assert row['resource']==job['resource']
        assert all(rows[d]['finish']<=row['start'] for d in job['deps'])
        if job['resource']is not None:
            totals[job['resource']]+=job['duration']
            if row['finish']>row['start']:
                events[job['resource']].extend(((row['start'],1),(row['finish'],-1)))
        if job['kind']=='shared_setup':starts[job['tile']]=row['start']
        if job['kind']=='tile_emit':finishes[job['tile']]=row['finish']
    peaks={}
    for resource,points in events.items():
        live=peak=0
        for _,delta in sorted(points):
            live+=delta;assert 0<=live<=(lanes if resource=='arithmetic' else 1)
            peak=max(peak,live)
        assert live==0;peaks[resource]=peak
    window_events=[]
    for tile,start in starts.items():
        finish=finishes[tile];assert finish>=start
        if finish>start:window_events.extend(((start,1),(finish,-1)))
        if tile>=work['window']:assert start>=finishes[tile-work['window']]
    live=window_peak=0
    for _,delta in sorted(window_events):
        live+=delta;assert 0<=live<=work['window'];window_peak=max(live,window_peak)
    assert live==0
    assert totals['fetch']==work['work']['fetch']
    assert totals['arithmetic']==sum(work['work']['context_compute'])
    assert totals['emit']==work['work']['emit']
    assert rows[work['complete']]['finish']==result['finish_cycles']
    floor=max(totals['fetch'],totals['emit'],max(work['work']['context_compute'],default=0),
              (totals['arithmetic']+lanes-1)//lanes)
    assert result['finish_cycles']>=floor
    return dict(resource_work_cycles=totals,resource_peaks=peaks,window_peak=window_peak,
                necessary_work_floor_cycles=floor,finish_cycles=result['finish_cycles'])
