#!/usr/bin/env python3
"""Native source/hash/RGB audit with scratch and video learned from common pins.

The native validation routine is a reviewed continuation of the frozen
reference checker; its added memory endpoint is checked by scratch_trace.py.
"""
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
REFERENCE=ROOT/'experiments/python-gamebub-v91l-reference-reader'
sys.path.insert(0,str(REFERENCE))
spec=importlib.util.spec_from_file_location('frozen_reference_audit',REFERENCE/'verify_results.py')
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)
need,numeric,sha,native,physical_byte=control.need,control.numeric,control.sha,control.native,control.physical_byte
merge,rows,LINE_ORDER,fnv=control.merge,control.rows,control.LINE_ORDER,control.fnv
events,read_cases_modes,ReferenceTraffic=control.events,control.read_cases_modes,control.ReferenceTraffic
from scratch_trace import ScratchReplay,ordered_scratch

def audit_native_mode(attempt,mode,frames,goldens):
    directory=attempt/mode['directory'];bus=iter(native.iter_bus(directory/'bus.bin.gz'))
    memory=ScratchReplay(True);refs=ReferenceTraffic(read_cases_modes(attempt/'inputs/cases.tsv'),frames);current=None;done=[];line=None;delivered=[];pixel_rows=[];holds=[];presented=[]
    pipeline_cases=[]
    def observed_stdout():
        for event in events(attempt/f'pins-seed{mode["seed"]}-tac{mode["t_ac_ns"]}.jsonl.gz'):
            if event['type']=='case':pipeline_cases.append(event)
            yield event
    stream=ordered_scratch(merge(observed_stdout(),events(directory/'physical-events.jsonl.gz')))
    for e in stream:
        k=e['type'];refs.feed(e,current,done)
        if k=='native_start':
            need(current is None and e['fid']==len(done),'native key/delta order differs')
            f=frames[f'c0_f{e["fid"]}'];h=f['header']
            need(e['epoch']!=0 and e['generation']==h['generation'] and e['bank_active']==1,'native allocation lease differs')
            protected=[e[p+'_bank'] for p in ('accepted_ref','front','pending') if e[p+'_valid']]
            need(e['bank'] not in protected,'candidate aliases protected bank at allocation')
            if e['fid']:
                need(e['accepted_ref_valid'] and e['accepted_ref_bank']==done[-1]['bank'],'delta reference is not accepted key bank')
                need(e['accepted_fid']==0 and e['accepted_generation']==frames['c0_f0']['header']['generation'],'delta accepted reference identity differs')
            current=dict(e,fixture=f,rows=iter(rows(f)),writes=0,acks=0,hashbytes=0,commit=None,rgb=None,lineindex=0,physical_reads=0)
        elif k=='wr_req':
            need(current is not None and current['commit'] is None,'candidate write outside provisional live frame')
            need(e['bank']==current['bank'] and e['epoch']==current['epoch'],'candidate write lease differs')
            expected=next(current['rows'],None);need(expected==(e['address'],numeric(e['data'])),'live row payload/order differs from native source')
            record=next(bus);need(record[:9]==(0,0,e['bank'],8,current['fid'],e['epoch'],e['token'],e['address'],numeric(e['data'])),'binary candidate request differs from actual SV handshake')
            need(record[9]*10000-5000==e['time_ps'],'binary request clock differs from actual edge');current['writes']+=1
        elif k=='scratch_live_req':
            need(current is not None and current['commit'] is None and e['id']==current['id'],
                 'native scratch handshake escapes its provisional source frame')
        elif k=='wr_rsp':
            need(current is not None and not e['error'],'native candidate write unexpectedly failed')
            a=memory.active;need(a is not None,'candidate ACK has no active physical row')
            value=numeric(a['data']);record=next(bus)
            need(record[:9]==(1,0,e['bank'],8,current['fid'],e['epoch'],e['token'],e['address'],value),'binary ACK differs from actual SV handshake')
            need(record[9]*10000-5000==e['time_ps'],'binary ACK clock differs from actual edge')
            for i in range(8):
                d=next(bus);need(d[:9]==(2,0,e['bank'],1,current['fid'],e['epoch'],0,e['address']+i,(value>>(8*i))&255),'ACK-backed hash byte/order differs')
                need(d[9]>=record[9],'hash byte delivered before actual physical ACK')
                word=memory.pin.value((e['bank']<<22)|(physical_byte(e['address']+i)>>1))
                need((word>>(8*((e['address']+i)&1)))&255==d[8],'hash byte not backed by real pin WRITE')
                current['hashbytes']+=1
            current['acks']+=1
        elif k=='native_commit':
            need(current is not None and current['commit'] is None and memory.active is None,'commit before physical write lease closes')
            need(e['v_commit']==1 and e['bank']==e['accepted_ref_bank']==current['bank'],'commit allocation/accepted bank differs')
            need(e['fid']==e['accepted_fid']==current['fid'] and e['accepted_generation']==current['generation'],'atomic commit identity differs')
            need(current['writes']==current['acks']==70080 and current['hashbytes']==560640,'commit before all rows/hash bytes')
            need(next(current['rows'],None) is None,'native source row suffix unwritten')
            for prior in [*done,dict(bank=current['bank'],fid=current['fid'])]:
                target=frames[f'c0_f{prior["fid"]}'];wanted=target['tiles']+target['hud']
                actual=b''.join(memory.pin.value((prior['bank']<<22)+i).to_bytes(2,'little') for i in range(280320))
                need(actual==wanted,'physical accepted/protected bank differs from source-backed native bytes')
            current['commit']=e
        elif k=='rgb_start':
            need(current is not None and current['commit'] is not None and current['rgb'] is None,'RGB begins without validated native commit')
            need(all(e[x]==current[x] for x in ('bank','epoch','generation','fid')),'RGB lease differs from validated candidate')
            current['rgb']=e;pixel_rows=[];delivered=[]
        elif k=='rd_req':
            need(current is not None,'physical read without a live frame')
            if current['rgb'] is not None:
                need(all(e[x]==current[x] for x in ('bank','epoch','generation')),'physical RGB read lease differs');current['physical_reads']+=1
            else:need(refs.is_reference_read(e),'unowned/misrouted physical reference read')
        elif k=='line_req':
            need(current is not None and line is None,'overlapping canonical line owner')
            need(e['address']==LINE_ORDER[current['lineindex']] and e['epoch']==current['epoch'],'canonical line order/epoch differs');line=e
        elif k=='line_rsp':
            need(line is not None and all(e[x]==line[x] for x in ('address','epoch','token')),'canonical response identity differs')
            need(bytes.fromhex(e['data'])==current['fixture']['raster'][e['address']:e['address']+16],'canonical line bytes differ from original native source')
            current['lineindex']+=1;line=None
        elif k=='pixel_row':
            need(current is not None and current['rgb'] is not None and e['row']==len(pixel_rows),'pixel row order differs')
            data=goldens[current['id']][e['row']*1440:(e['row']+1)*1440]
            need(e['pixels']==720 and e['epoch']==current['epoch'] and e['hash_fnv64']==fnv(data),'native RGB row bytes differ')
            need(e['first_cycle']<=e['last_cycle'],'pixel row timing invalid');pixel_rows.append(e)
        elif k=='rgb_frame':
            need(current is not None and current['rgb'] is not None and memory.active is None,'RGB closes with pending physical owner')
            need(e['pixels']==345600 and e['bytes']==691200 and len(pixel_rows)==480,'incomplete native RGB')
            need(current['lineindex']==current['physical_reads']==e['logical_reads']==e['physical_reads']==32400 and line is None,'RGB line/read count differs')
            need(e['first_pixel_cycle']==pixel_rows[0]['first_cycle'] and e['last_pixel_cycle']==pixel_rows[-1]['last_cycle'],'RGB row/fence timing differs')
            raw=(directory/e['output']).read_bytes();need(raw==goldens[e['id']],'complete native RGB output differs')
            need(e['commit_cycle']==current['commit']['cycle'] and e['start_cycle']==current['rgb']['cycle'],'RGB commit/start fence differs')
            need(e['native_start_cycle']==current['cycle'],'RGB closure names a different native start')
            done.append(dict(e,output_sha256=sha(directory/e['output']),live_cycles=e['commit_cycle']-e['native_start_cycle'],rgb_cycles=e['closed_cycle']-e['start_cycle'],joint_serial_cycles=e['closed_cycle']-e['native_start_cycle']))
            current=None
        elif k.startswith('publication_wait_'):
            need(len(done)==2 and e['front_valid']==1 and e['front_fid']==0 and e['front_bank']==done[0]['bank'] and
                 e['pending_valid']==1 and e['pending_fid']==1 and e['pending_bank']==done[1]['bank'] and e['v_presented']==0,
                 'presentation escaped held publication fence')
            if k.endswith('vblank'):need(e['vblank']==0,'missing vblank hold')
            else:need(e['scanout_drained']==0,'missing scanout hold')
            holds.append(k)
        elif k=='native_presented':
            need(e['v_presented']==1 and e['front_valid']==1 and e['front_fid']==e['fid'],'presented identity differs')
            need(e['vblank'] and e['scanout_drained'],'presentation before both fences');presented.append(e['fid'])
        memory.feed(e)
    result=memory.finish();need(current is None and len(done)==2 and next(bus,None) is None,'native source/bus suffix remains')
    need(set(holds)=={'publication_wait_vblank','publication_wait_scanout'} and presented==[0,1],'publication fence evidence incomplete')
    need(result['video_write_words']==560640 and result['video_captured_words']==768192,'physical video full-frame work differs')
    hashes=native.parse_hash_trace(directory/'hashes.jsonl.gz');need(len(hashes)==2,'native RTL SHA group count differs')
    need([(row['id'],row['epoch']) for row in mode['live_cases']]==[(f'c0_f{f["fid"]}',f['epoch']) for f in done],
         'native RTL SHA summary omits/reorders a completed source frame')
    for row in mode['live_cases']:
        f=frames[row['id']];key=(row['id'],0,row['epoch'])
        need(hashes.pop(key)==native.expected_hash_jobs(f),'actual RTL C2/HUD/seal digest differs from independent hashlib')
        need(row['root']==f['root'].hex() and row['hud_sha256']==f['hud_sha'].hex() and row['seal']==f['seal'].hex(),'accepted content commitments differ')
        need(row['hash_jobs']==1025 and row['hash_message_bytes']==628815 and row['hash_blocks']==10298,'hash work accounting differs')
    need(not hashes,'unverified native RTL SHA group remains')
    archived={}
    for raw in gzip.open(directory/'actual.tsv.gz','rt'):
        tag,profile,data=raw.rstrip().split('\t');need(profile=='0','unqualified service profile');archived[tag]=bytes.fromhex(data)
    cases=native.read_cases(attempt/'inputs/cases.tsv')
    need(len(pipeline_cases)==2,'packet ingress/final decoder summaries incomplete')
    for resultrow in done:
        f=frames[f'c0_f{resultrow["fid"]}'];key=resultrow['id']
        need(archived[key]==f['raster'],'actual live canonical output differs')
        need(archived['accepted_'+key]==f['raster']+f['hud'],'ACK-backed canonical/HUD mirror differs')
        need(archived['qcache_'+key]==cases[key]['scales'],'captured RTL qcache differs')
        ingress=next(e for e in pipeline_cases if e['id']==key)
        need(ingress['status']=='PASS' and ingress['frame_epoch']==resultrow['epoch'] and
             ingress['first_input']<=ingress['last_input']<resultrow['commit_cycle'],'packet-complete/commit fence invalid')
        resultrow['packet_complete_cycle']=ingress['last_input']
        resultrow['packet_complete_to_commit_cycles']=resultrow['commit_cycle']-ingress['last_input']
    need(cases['actual_006']['prior']==archived['qcache_actual_001'],'delta qcache is not actual accepted history')
    reference=refs.finish()
    counters=check_scratch_counters(directory,reference,done,result)
    return dict(reference=reference,reference_counters=counters,seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],physical=result,frames=done,rtl_sha_jobs=2050,
                source_canonical_HUD_bytes=1121280,publication_hold_checks=len(holds),presented_fids=presented)

def check_scratch_counters(directory, reference, actual_frames, physical):
    records=list(events(directory/'physical-events.jsonl.gz'))
    counters={k:[e for e in records if e['type']==k] for k in ('scratch_frame','reference_frame','service_counts')}
    need(all(len(v)==2 for v in counters.values()),'scratch/reference/service frame summaries incomplete')
    need(set(physical['scratch_by_native_id'])=={f['id'] for f in actual_frames},'scratch source-frame set differs')
    totals=collections.Counter()
    for i,(scratch,ref,service,frame) in enumerate(zip(counters['scratch_frame'],counters['reference_frame'],counters['service_counts'],actual_frames)):
        stats=physical['scratch_by_native_id'][frame['id']]
        for key in ('requests','responses','write_requests','read_requests','max_address'):
            need(scratch[key]==stats[key],'scratch independent summary differs: '+key)
        need(scratch['write_responses']==scratch['write_requests'] and scratch['read_responses']==scratch['read_requests'], 'scratch frame responses incomplete')
        need(scratch['write_words']==stats['write_requests']*8 and scratch['read_words']==stats['read_requests']*8,'scratch frame physical word costs differ')
        need(stats['errors']==0 and stats['commands']==stats['write_requests']*8+stats['read_requests'],'scratch command accounting differs')
        need(scratch['first_cycle']*10000-5000==stats['first_request_ps'] and scratch['last_cycle']*10000-5000==stats['last_ack_ps'],'scratch frame request/ACK fences differ')
        need(frame['native_start_cycle']<=scratch['first_cycle']<=scratch['last_cycle']<=frame['commit_cycle'],'scratch work escapes live decode/commit fence')
        for key in ('requests','responses','commands','write_requests','read_requests'):totals[key]+=stats[key]
        need(scratch['physical_requests']==totals['requests'] and scratch['physical_responses']==totals['responses'] and scratch['physical_commands']==totals['commands'],'cumulative scratch RTL counters differ')
        expected=0 if i==0 else 7806
        need(ref['tile_requests']==ref['tile_responses']==expected and ref['line_requests']==ref['line_responses']==expected*4,'reference source-derived counts differ')
        need(ref['x16_read_words']==expected*32 and ref['last_canonical_pixel_cycle']<=ref['commit_cycle']<=ref['rgb_closed_cycle'],'reference counts/fences differ')
        need(ref['start_cycle']==frame['native_start_cycle'] and ref['input_complete_cycle']==frame['packet_complete_cycle'] and ref['commit_cycle']==frame['commit_cycle'] and ref['rgb_closed_cycle']==frame['closed_cycle'],'reference summary timing differs')
        video_reads=(32400,96024)[i]
        need(service['writes']==(i+1)*280320+totals['write_requests']*8,'combined pin WRITE word accounting differs')
        need(service['readwords']==video_reads*8+totals['read_requests']*8,'combined pin READ word accounting differs')
        need(service['writer_commands']==service['wr_words_accepted']==service['wr_words_retired']==(i+1)*280320,'video writer counters differ')
        need(service['reader_commands']==service['rd_requests']==service['rd_responses']==video_reads and service['rd_count_beats']==video_reads*8,'video reader counters differ')
    need(physical['native_scratch_observers']==dict(requests=totals['requests'],responses=totals['responses']),'native scratch handshakes incomplete')
    return counters

def checker_negatives(trace):
    def scratch_command(e):return e['type']=='ctrl_req' and e['owner']==3 and e['write']==1
    tests=[
        ('scratch address intent',lambda e:e['type']=='scratch_req' and e['write']==1,lambda e:dict(e,address=e['address']^16),'scratch physical command address'),
        ('scratch epoch identity',lambda e:e['type']=='scratch_req',lambda e:dict(e,epoch=e['epoch']^1),'scratch response epoch'),
        ('scratch controller address',scratch_command,lambda e:dict(e,address=e['address']^1),'scratch physical command address'),
        ('scratch controller payload',scratch_command,lambda e:dict(e,data=e['data']^1),'scratch controller write word'),
        ('scratch pin DQ',lambda e:e['type']=='pin' and e['bank']==3 and e['command']==4,lambda e:dict(e,dq=e['dq']^1),'scratch pin DQ'),
        ('scratch pin column',lambda e:e['type']=='pin' and e['bank']==3 and e['command']==5,lambda e:dict(e,address=e['address']^16),'scratch pin address'),
        ('scratch capture payload',lambda e:e['type']=='controller_read' and e['owner']==3,lambda e:dict(e,data=e['data']^1),'capture/retime/consume data'),
        ('scratch capture phase',lambda e:e['type']=='controller_read' and e['owner']==3,lambda e:dict(e,time_ps=e['time_ps']+1),'capture/retime/consume timing'),
        ('scratch capture owner',lambda e:e['type']=='controller_read' and e['owner']==3,lambda e:dict(e,owner=2),'read capture routed'),
        ('scratch response assembly',lambda e:e['type']=='scratch_rsp_offer' and numeric(e['data'])!=0,lambda e:dict(e,data=f'{numeric(e["data"])^1:032x}'),'scratch held reply'),
        ('scratch held response epoch',lambda e:e['type']=='scratch_rsp',lambda e:dict(e,epoch=e['epoch']^1),'scratch response epoch'),
        ('scratch held response mutation',lambda e:e['type']=='scratch_rsp',lambda e:dict(e,data=f'{numeric(e["data"])^1:032x}'),'scratch held reply mutated'),
        ('scratch response error',lambda e:e['type']=='scratch_rsp_offer',lambda e:dict(e,error=e['error']^1),'scratch error'),
        ('physical arbiter grant',lambda e:e['type']=='scratch_owner' and e['old_owner']==0,lambda e:dict(e,owner=3-e['owner']),'physical arbiter round-robin grant'),
        ('video controller address',lambda e:e['type']=='ctrl_req' and e['owner']==1,lambda e:dict(e,address=e['address']^1),'physical command address'),
        ('video pin DQ',lambda e:e['type']=='pin' and e['bank']<3 and e['command']==4,lambda e:dict(e,dq=e['dq']^1),'pin DQ'),
        ('video held response',lambda e:e['type']=='wr_rsp',lambda e:dict(e,bank=e['bank']^1),'bridge response identity'),
        ('video read capture',lambda e:e['type']=='controller_read' and e['owner']==2,lambda e:dict(e,data=e['data']^1),'capture/retime/consume data'),
        ('video read reply',lambda e:e['type']=='rd_rsp',lambda e:dict(e,data=f'{numeric(e["data"])^1:032x}'),'held response mutated')]
    results=[]
    for label,predicate,mutate,cause in tests:
        index=next(i for i,e in enumerate(trace) if predicate(e))
        original=trace[index];corrupted=mutate(original);oracle=ScratchReplay()
        try:
            for i,e in enumerate(trace):oracle.feed(corrupted if i==index else e)
            oracle.finish()
        except AssertionError as error:
            need(cause in str(error),'negative rejected for unrelated cause: '+label+': '+str(error))
            results.append(dict(label=label,index=index,original=original,corrupted=corrupted,rejected=True,reason=str(error)))
        else:raise AssertionError('checker accepted corruption: '+label)
    return results

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--unit-only',action='store_true');args=ap.parse_args()
    pins=json.loads((HERE/'reviewed-source-hashes.json').read_text())
    for name,digest in pins.items():need(sha(ROOT/name)==digest,'reviewed scratch source differs: '+name)
    control.prior.BASELINE='8226113182edbbd79b0fce3d92cf1f87ecee1627'
    control.prior.REVIEWED=pins
    up,unit=control.prior.provenance('fpga/experiments/cu66-v91l-scratch-service/results.json','PASS_PHYSICAL_SCRATCH_DIRECTED')
    need(len(unit['modes'])==2 and {m['t_ac_ns'] for m in unit['modes']}=={2,7},'scratch unit corner grid incomplete')
    modes=[];negatives=[]
    for mode in unit['modes']:
        raw=list(events(up.parent/mode['event_log']));checks=[e for e in raw if e['type']=='check']
        need(mode['verdict']['status']=='TEST_PASS' and mode['verdict']['checks']==len(checks)>=811 and all(e['status']=='PASS' for e in checks),'scratch directed checks incomplete')
        trace=list(ordered_scratch(raw));memory=ScratchReplay();tile=control.TileTrace();mux=control.MuxTrace()
        for event in trace:memory.feed(event);tile.feed(event);mux.feed(event)
        modes.append(dict(mode=mode['mode'],t_ac_ns=mode['t_ac_ns'],checks=len(checks),physical=memory.finish(),reference=tile.finish(),mux=mux.finish()))
        negatives.extend(dict(mode=mode['mode'],**n) for n in checker_negatives(trace))
        negatives.extend(dict(mode=mode['mode'],**n) for n in control.reference_negatives(trace,trace))
    inherited={str((REFERENCE/n).relative_to(ROOT)):sha(REFERENCE/n) for n in ('verify_results.py','reference_trace.py','unit_trace.py')}
    expected=json.loads((REFERENCE/'audit.json').read_text())
    need(inherited[str((REFERENCE/'verify_results.py').relative_to(ROOT))]==expected['verifier_sha256'] and
         inherited[str((REFERENCE/'reference_trace.py').relative_to(ROOT))]==expected['reference_verifier_sha256'] and
         inherited[str((REFERENCE/'unit_trace.py').relative_to(ROOT))]==expected['unit_verifier_sha256'],'frozen reference checker changed')
    result=dict(schema='cu66-v91l-scratch-independent-audit-v1',status='PASS_INDEPENDENT_PHYSICAL_SCRATCH_UNIT',
        unit_report=str(up.relative_to(ROOT)),unit_report_sha256=sha(up),unit_modes=modes,
        checker_negative_controls=negatives,reviewed_source_sha256=pins,inherited_checker_sha256=inherited,
        original_helper_sha256=control.prior.HELPERS,verifier_sha256=sha(Path(__file__)),scratch_trace_sha256=sha(HERE/'scratch_trace.py'))
    reports=[(up,unit)]
    if not args.unit_only:
        lp,live=control.prior.provenance('fpga/experiments/cu66-v91l-scratch-live/results.json','PASS_EXACT_PHYSICAL_SCRATCH_LIVE_TO_SAME_TIMED_MEMORY_RGB')
        need(live['scratch_service_rtl'] and live['physical_scratch_service'] and live['all_external_memory_endpoints_rtl'] and not live['scratch_memory_actors'],'scratch endpoint remains a software actor')
        need(live['physical_reference_service'] and live['actual_physical_candidate_writes'] and live['actual_rgb_from_same_pin_memory'] and not live['physical_preload'],'partial physical memory join')
        need(not live['full_live_physical_service_complete'] and not live['full_rtl_hud_decoder'] and not live['full_rtl_hud_overlay'] and not live['hardware_30fps_proven'] and not live['physical_hardware_tested'],'unsupported whole-system/hardware scope')
        need(len(live['modes'])==4 and {(m['seed'],m['t_ac_ns']) for m in live['modes']}=={(s,t) for s in (912901,912902) for t in (2,7)},'native seed/corner grid incomplete')
        frames=native.expected_frames(lp.parent);goldens={}
        for line in gzip.open(lp.parent/'inputs/rgb_goldens.tsv.gz','rt'):
            ident,data=line.rstrip().split('\t')
            if ident in ('actual_001','actual_006'):goldens[ident]=bytes.fromhex(data)
        qualified=[]
        for mode in live['modes']:
            qualified.append(audit_native_mode(lp.parent,mode,frames,goldens));print('AUDITED_PHYSICAL_SCRATCH',mode['seed'],mode['t_ac_ns'],flush=True)
        result.update(status='PASS_INDEPENDENT_PHYSICAL_SCRATCH_LIVE_VALIDATION_AND_NATIVE_RGB',live_report=str(lp.relative_to(ROOT)),live_report_sha256=sha(lp),live_modes=qualified,exact_native_RGB_outputs=8,rtl_sha_jobs=8200,
            scope='Supported native BR88 key/delta, actual scratch/candidate/reference/display traffic on one timed controller, exact validation and base RGB. Native HUD remains semantic software endpoint; serial workload, not complete hardware30fps/under10ms.')
        reports.append((lp,live))
    for path,report in reports:
        for name,digest in report['source_sha256'].items():need(sha(ROOT/name)==digest,'source changed during audit: '+name)
    (HERE/('audit-unit.json' if args.unit_only else 'audit.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],flush=True)
if __name__=='__main__':main()
