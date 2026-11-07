#!/usr/bin/env python3
"""Independent concurrent native decode/display, validation and pin replay."""
import collections
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
FROZEN=ROOT/'experiments/python-gamebub-v91l-scratch-service'
sys.path.insert(0,str(FROZEN))
spec=importlib.util.spec_from_file_location('frozen_scratch_audit',FROZEN/'verify_results.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
need,numeric,sha,native=prior.need,prior.numeric,prior.sha,prior.native
rows,LINE_ORDER,fnv,events,merge=prior.rows,prior.LINE_ORDER,prior.fnv,prior.events,prior.merge
physical_byte,ReferenceTraffic=prior.physical_byte,prior.ReferenceTraffic
from scratch_trace import ScratchReplay,ordered_scratch
from lease_trace import LeaseTrace


def audit_mode(attempt,mode,fixtures,goldens):
    directory=attempt/mode['directory'];bus=iter(native.iter_bus(directory/'bus.bin.gz'))
    memory=ScratchReplay(True);refs=ReferenceTraffic(prior.read_cases_modes(attempt/'inputs/cases.tsv'),fixtures)
    lease=LeaseTrace();concurrent=collections.Counter()
    decode=None;accepted=[];by_id={};rgb=None;outputs=[];line=None;pixel_rows=[];presented=[];pipeline=[];guards=[]
    def pins():
        for name in mode['pin_logs']:
            for e in events(attempt/name):
                if e['type']=='case':pipeline.append(e)
                yield e
    stream=ordered_scratch(merge(pins(),events(directory/'physical-events.jsonl.gz')))
    for e in stream:
        k=e['type']
        lease.feed(e)
        # Reference intent belongs to the current decoder; display intent has
        # a separate immutable owner and may overlap an uncommitted decoder.
        context=dict(decode,rgb=rgb) if decode is not None else None
        refs.feed(e,context,accepted)
        if k=='native_start':
            need(decode is None or decode['commit'] is not None,'second decoder starts over active candidate')
            need(e['fid']==len(by_id) and e['id'] not in by_id,'native source order/identity differs')
            fixture=fixtures[f'c0_f{e["fid"]}'];header=fixture['header']
            need(e['epoch']!=0 and e['generation']==header['generation'] and e['bank_active']==1,'allocation descriptor differs')
            protected=[e[p+'_bank'] for p in ('accepted_ref','front','pending') if e[p+'_valid']]
            need(e['bank'] not in protected,'candidate aliases allocator-protected bank')
            if rgb is not None:need(e['bank']!=rgb['bank'],'candidate allocation aliases active display source')
            if e['fid']:
                need(accepted and e['accepted_ref_valid'] and e['accepted_ref_bank']==accepted[-1]['bank'],'delta reference is not accepted key')
                need(e['accepted_fid']==0 and e['accepted_generation']==fixtures['c0_f0']['header']['generation'],'delta accepted key identity differs')
                need(rgb is not None and rgb['fid']==0 and rgb['closed'] is None,'delta does not actually begin during key display')
                need(e['front_valid'] and e['front_fid']==0 and not e['pending_valid'],'key must be front before concurrent delta starts')
            decode=dict(e,fixture=fixture,row_iter=iter(rows(fixture)),writes=0,acks=0,hashbytes=0,commit=None,rgb=None)
            by_id[e['id']]=decode
        elif k=='scratch_live_req':
            need(decode is not None and decode['commit'] is None and e['id']==decode['id'],'scratch outside its current native source')
        elif k=='wr_req':
            need(decode is not None and decode['commit'] is None,'candidate write outside provisional decode')
            need(e['bank']==decode['bank'] and e['epoch']==decode['epoch'],'candidate write descriptor differs')
            if rgb is not None:need(e['bank']!=rgb['bank'],'candidate write aliases active display source')
            if lease.active is not None:need(e['bank']!=lease.active['bank'],'candidate write aliases draining display lease')
            if rgb is not None:concurrent['candidate_requests_while_rgb']+=1
            need(next(decode['row_iter'],None)==(e['address'],numeric(e['data'])),'native candidate payload/order differs')
            record=next(bus);need(record[:9]==(0,0,e['bank'],8,decode['fid'],e['epoch'],e['token'],e['address'],numeric(e['data'])),'candidate binary request differs from SV')
            need(record[9]*10000-5000==e['time_ps'],'candidate request timestamp differs');decode['writes']+=1
        elif k=='wr_rsp':
            need(decode is not None and not e['error'],'unexpected native candidate error')
            a=memory.active;need(a is not None and a['writer'],'candidate ACK lacks physical writer')
            value=numeric(a['data']);record=next(bus)
            need(record[:9]==(1,0,e['bank'],8,decode['fid'],e['epoch'],e['token'],e['address'],value),'candidate binary ACK differs from SV')
            need(record[9]*10000-5000==e['time_ps'],'candidate ACK timestamp differs')
            for i in range(8):
                b=next(bus);need(b[:9]==(2,0,e['bank'],1,decode['fid'],e['epoch'],0,e['address']+i,(value>>(8*i))&255),'ACK-backed hash byte/order differs')
                need(b[9]>=record[9],'hash byte before physical ACK')
                word=memory.pin.value((e['bank']<<22)|(physical_byte(e['address']+i)>>1))
                need((word>>(8*((e['address']+i)&1)))&255==b[8],'hash byte not backed by physical pin WRITE')
                decode['hashbytes']+=1
            decode['acks']+=1
        elif k=='native_commit':
            need(decode is not None and decode['commit'] is None,'unexpected native commit')
            need(e['id']==decode['id'] and e['epoch']==decode['epoch'],'native commit source/epoch differs')
            need(memory.active is None or not memory.active['writer'],'native commit before physical candidate closure')
            need(memory.scratch is None,'native commit before scratch closure')
            need(refs.active is None and refs.line is None,'native commit before reconstruction reference drain')
            need(e['v_commit'] and e['bank']==e['accepted_ref_bank']==decode['bank'] and e['fid']==e['accepted_fid']==decode['fid'] and e['accepted_generation']==decode['generation'],'atomic accepted identity differs')
            need(decode['writes']==decode['acks']==70080 and decode['hashbytes']==560640 and next(decode['row_iter'],None) is None,'commit before source write/hash completion')
            for saved in [*accepted,decode]:
                expected=fixtures[f'c0_f{saved["fid"]}'];wanted=expected['tiles']+expected['hud']
                actual=b''.join(memory.pin.value((saved['bank']<<22)+i).to_bytes(2,'little') for i in range(280320))
                need(actual==wanted,'physical candidate/protected bank differs from native source')
            decode['commit']=e;accepted.append(decode)
        elif k=='reference_req' and rgb is not None:concurrent['reference_requests_while_rgb']+=1
        elif k=='rgb_start':
            need(rgb is None and e['id'] in by_id,'display overwrites lease or names unknown source')
            source=by_id[e['id']];need(source['commit'] is not None and source['rgb'] is None,'display before validated source commit')
            need(all(e[n]==source[n] for n in ('bank','epoch','fid','generation')),'display descriptor differs from its committed source')
            need(lease.offered is not None and all(e[n]==lease.offered[n] for n in ('bank','epoch','fid','generation')),
                 'actual RGB start not bound to qualified display lease request')
            rgb=dict(e,source=source,closed=None,reads=0,lineindex=0);source['rgb']=rgb;pixel_rows=[];line=None
        elif k=='lease_owner' and e['active']:
            need(rgb is not None and all(e[n]==rgb[n] for n in ('bank','epoch','fid','generation')),
                 'registered display lease differs from actual RGB owner')
        elif k=='rd_req':
            if refs.mux_owner==1:
                need(rgb is not None and all(e[n]==rgb[n] for n in ('bank','epoch','generation')),'display read escaped immutable consumer lease')
                rgb['reads']+=1
            else:need(refs.is_reference_read(e),'unowned physical read')
        elif k=='line_req':
            need(rgb is not None and line is None and e['epoch']==rgb['epoch'],'overlapping or mistagged display line')
            need(e['address']==LINE_ORDER[rgb['lineindex']],'display canonical line order differs');line=e
        elif k=='line_rsp':
            need(rgb is not None and line is not None and all(e[n]==line[n] for n in ('address','epoch','token')),'display line return identity differs')
            need(bytes.fromhex(e['data'])==rgb['source']['fixture']['raster'][e['address']:e['address']+16],'display line bytes differ from source')
            rgb['lineindex']+=1;line=None
        elif k=='pixel_row':
            need(rgb is not None and e['id']==rgb['id'] and e['epoch']==rgb['epoch'] and e['row']==len(pixel_rows),'display pixel row source/order differs')
            data=goldens[rgb['id']][e['row']*1440:(e['row']+1)*1440]
            need(e['pixels']==720 and e['hash_fnv64']==fnv(data) and e['first_cycle']<=e['last_cycle'],'actual display row pixels/timing differ');pixel_rows.append(e)
        elif k=='rgb_frame':
            need(rgb is not None and e['id']==rgb['id'] and all(e[n]==rgb[n] for n in ('bank','epoch','fid','generation')),'display closure descriptor differs')
            need(e['pixels']==345600 and e['bytes']==691200 and len(pixel_rows)==480,'native RGB frame incomplete')
            need(rgb['reads']==rgb['lineindex']==e['logical_reads']==e['physical_reads']==32400 and line is None,'native display read/line counts differ')
            need(e['first_pixel_cycle']==pixel_rows[0]['first_cycle'] and e['last_pixel_cycle']==pixel_rows[-1]['last_cycle'],'display row/frame fences differ')
            need(e['start_cycle']==rgb['cycle'] and e['native_start_cycle']==rgb['source']['cycle'] and e['commit_cycle']==rgb['source']['commit']['cycle'],'display closure borrowed current decoder fences')
            need(e['start_cycle']<e['first_pixel_cycle']<=e['last_pixel_cycle']<=e['engine_done_cycle']<e['closed_cycle'] and e['time_ps']==e['closed_cycle']*10000,'display closure actual counter/timestamp order differs')
            need(lease.active is not None and lease.idles==2 and e['time_ps']==lease.previous_fence+5000,
                 'display closure not on actual terminal drain release edge')
            need(not any(e[n] for n in ('display_active','display_draining','display_reader_busy','display_reader_pending')) and e['mux_owner']!=1,
                 'post-edge display closure still owns consumer work')
            raw=directory/e['output'];need(raw.read_bytes()==goldens[e['id']],'complete actual RGB file differs from source')
            rgb['closed']=e;outputs.append(dict(e,output_sha256=sha(raw),decode_cycles=e['commit_cycle']-e['native_start_cycle'],rgb_cycles=e['closed_cycle']-e['start_cycle']));rgb=None
        elif k=='native_presented':
            need(e['v_presented'] and e['front_valid'] and e['front_fid']==e['fid'],'actual publication identity differs')
            need(e['vblank'] and e['scanout_drained'],'publication before external vblank/drain')
            need(not e['display_active'] and lease.active is None,'publication escapes real display lease')
            if e['fid']==1:need(rgb is None or rgb['fid']!=0,'delta presents before old display consumer closure')
            presented.append(e['fid'])
        elif k.startswith('publication_wait_') or k.startswith('overlap_guard_'):guards.append(e)
        memory.feed(e)
        if k=='scratch_live_req' and rgb is not None:concurrent['scratch_requests_while_rgb']+=1
    physical=memory.finish();reference=refs.finish();lease_result=lease.finish()
    physical['pin_commands']={name:memory.pin.counts[code] for name,code in
                              (('mode_register',0),('refresh',1),('precharge',2),('activate',3),('write',4),('read',5))}
    need(len(by_id)==len(accepted)==len(outputs)==2 and next(bus,None) is None and rgb is None,'incomplete native overlap source/output/bus suffix')
    need([e['fid'] for e in outputs]==[0,1] and presented==[0,1],'native display/publication order differs')
    need(physical['video_write_words']==560640 and physical['video_captured_words']==768192,'native physical video work differs')
    need(physical['scratch_transactions']==14058 and physical['scratch_pin_write_words']==physical['scratch_captured_words']==56232,'native physical scratch work differs')
    hashes=native.parse_hash_trace(directory/'hashes.jsonl.gz');need(len(hashes)==2 and len(mode['live_cases'])==2,'native SHA group coverage incomplete')
    need([(row['id'],row['epoch']) for row in mode['live_cases']]==[(f'c0_f{f["fid"]}',f['epoch']) for f in accepted],'native SHA source summary differs')
    for row in mode['live_cases']:
        f=fixtures[row['id']];need(hashes.pop((row['id'],0,row['epoch']))==native.expected_hash_jobs(f),'RTL SHA/C2/HUD/seal differs from independent hashlib')
        need(row['root']==f['root'].hex() and row['hud_sha256']==f['hud_sha'].hex() and row['seal']==f['seal'].hex(),'accepted commitments differ')
        need(row['hash_jobs']==1025 and row['hash_message_bytes']==628815 and row['hash_blocks']==10298,'validation work accounting differs')
    need(not hashes,'unverified SHA group remains')
    archived={}
    for raw in gzip.open(directory/'actual.tsv.gz','rt'):
        tag,profile,data=raw.rstrip().split('\t');need(profile=='0','unsupported scratch profile');archived[tag]=bytes.fromhex(data)
    cases=native.read_cases(attempt/'inputs/cases.tsv');need(len(pipeline)==2,'ingress/decoder completion coverage incomplete')
    for item in accepted:
        key=item['id'];fixture=item['fixture']
        need(archived[key]==fixture['raster'] and archived['accepted_'+key]==fixture['raster']+fixture['hud'],'native canonical/HUD mirror differs')
        need(archived['qcache_'+key]==cases[key]['scales'],'actual RTL qcache differs')
        ingress=next(e for e in pipeline if e['id']==key);need(ingress['status']=='PASS' and ingress['frame_epoch']==item['epoch'] and ingress['last_input']<item['commit']['cycle'],'packet/commit fence differs')
        output=next(e for e in outputs if e['id']==key);need(output['packet_complete_cycle']==ingress['last_input'],'display source packet-complete counter differs');output['packet_complete_to_commit_cycles']=item['commit']['cycle']-ingress['last_input']
    need(cases['actual_006']['prior']==archived['qcache_actual_001'],'delta history is not captured accepted qcache')
    key,delta=outputs
    need(key['start_cycle']<delta['native_start_cycle']<key['closed_cycle'],'no actual native decode/display overlap')
    overlap=max(0,min(key['closed_cycle'],delta['commit_cycle'])-max(key['start_cycle'],delta['native_start_cycle']))
    records=list(events(directory/'physical-events.jsonl.gz'))
    summaries=[e for e in records if e['type']=='overlap_summary'];need(len(summaries)==1,'native contention summary coverage incomplete')
    summary=summaries[0]
    for name,value in concurrent.items():need(summary[name]==value and value>0,'actual concurrent handshake accounting differs: '+name)
    need(set(concurrent)=={'candidate_requests_while_rgb','reference_requests_while_rgb','scratch_requests_while_rgb'},'native producer clients did not all overlap display')
    need(summary['key_rgb_start_cycle']==key['start_cycle'] and summary['key_rgb_closed_cycle']==key['closed_cycle'] and summary['delta_start_cycle']==delta['native_start_cycle'] and summary['delta_commit_cycle']==delta['commit_cycle'] and summary['last_rgb_closed_cycle']==delta['closed_cycle'],'overlap summary substituted different actual fences')
    need(bool(summary['guard_mode'])==bool(mode['guard_mode']),'guard workload label differs')
    if mode['guard_mode']:
        witness=[e for e in guards if e['type']=='publication_wait_actual_display'];need(len(witness)==1,'native guard witness missing')
        e=witness[0]
        need(e['vblank'] and e['external_drained_hint'] and not e['scanout_drained'] and e['display_active'],'native guard relies on external hold instead of actual lease')
        need(e['accepted_fid']==1 and e['front_fid']==0 and e['pending_fid']==1 and e['display_fid']==0 and e['display_bank']==key['bank'] and e['accepted_ref_bank']==delta['bank'],'native guard source/front/accepted identity differs')
        need(key['last_pixel_cycle']>=delta['commit_cycle']+17 and key['closed_cycle']>delta['commit_cycle']+17,'guard did not actually retain old final pixel across new commit')
    else:need(not guards and summary['guard_hold_cycles']==0,'natural timing contaminated by directed hold')
    check_counters(records,outputs,physical,fixtures)
    return dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],guard_mode=mode['guard_mode'],physical=physical,reference=reference,lease=lease_result,frames=outputs,rtl_sha_jobs=2050,
                native_overlap_cycles=overlap,pair_start_to_final_rgb_cycles=delta['closed_cycle']-key['native_start_cycle'],presented_fids=presented,
                guard_records=guards,concurrent_handshakes=dict(concurrent),source_reviewed_observed_counters=summary)

def lease_negatives(trace):
    from lease_trace import LeaseTrace
    tests=[
        ('qualification',lambda e:e['type']=='lease_request' and e['accepted']==1,lambda e:dict(e,accepted=0),'qualification'),
        ('zero epoch',lambda e:e['type']=='lease_request' and e['accepted']==1,lambda e:dict(e,epoch=0),'qualification'),
        ('high generation',lambda e:e['type']=='lease_request' and e['accepted']==1,lambda e:dict(e,accepted_generation=e['accepted_generation']^(1<<32)),'qualification'),
        ('captured fid',lambda e:e['type']=='lease_request' and e['accepted']==1,lambda e:dict(e,accepted_fid=e['accepted_fid']^1),'captured descriptor'),
        ('captured bank',lambda e:e['type']=='lease_owner' and e['active']==1,lambda e:dict(e,bank=e['bank']^1),'captured descriptor'),
        ('captured full generation',lambda e:e['type']=='lease_owner' and e['active']==1,lambda e:dict(e,generation=e['generation']^(1<<32)),'captured descriptor'),
        ('released descriptor',lambda e:e['type']=='lease_owner' and e['active']==0,lambda e:dict(e,epoch=e['epoch']^1),'released lease descriptor'),
        ('drain count',lambda e:e['type']=='lease_fence',lambda e:dict(e,idle_samples=e['idle_samples']^1),'drain counter'),
        ('physical pending drain',lambda e:e['type']=='lease_fence' and e['terminal'] and e['idle_samples']==1 and not e['reader_pending'] and not e['engine_busy'] and not e['engine_draining'] and not e['reader_busy'] and e['mux_owner']!=1,lambda e:dict(e,reader_pending=1),'two consecutive terminal drain'),
        ('terminal latch',lambda e:e['type']=='lease_fence' and e['terminal']==1,lambda e:dict(e,terminal=0),'terminal/error history'),
        ('terminal error',lambda e:e['type']=='lease_fence' and e['terminal_error']!=0,lambda e:dict(e,terminal_error=e['terminal_error']^1),'terminal/error history'),
        ('alias active metadata',lambda e:e['type']=='lease_alias_block' and e['lease_active']==1,lambda e:dict(e,lease_active=0),'alias active metadata'),
        ('alias bank metadata',lambda e:e['type']=='lease_alias_block' and e['lease_active']==1,lambda e:dict(e,lease_bank=e['lease_bank']^1),'alias source-bank metadata'),
        ('alias reason',lambda e:e['type']=='lease_alias_block',lambda e:dict(e,candidate_bank=(e['candidate_bank']+1)%3),'candidate alias blocked')]
    results=[]
    for label,predicate,mutate,cause in tests:
        index=next(i for i,e in enumerate(trace) if predicate(e));original=trace[index];corrupted=mutate(original);oracle=LeaseTrace()
        try:
            for i,e in enumerate(trace):oracle.feed(corrupted if i==index else e)
            oracle.finish()
        except AssertionError as error:
            need(cause in str(error),'lease negative rejected for wrong cause '+label+': '+str(error))
            results.append(dict(label=label,index=index,original=original,corrupted=corrupted,rejected=True,reason=str(error)))
        else:raise AssertionError('lease oracle accepted corruption '+label)
    return results

def check_counters(records,outputs,physical,fixtures):
    scratches=[e for e in records if e['type']=='scratch_frame'];references=[e for e in records if e['type']=='reference_frame'];services=[e for e in records if e['type']=='service_counts']
    need(len(scratches)==len(references)==2 and len(services)==1,'per-decode/final global counter records incomplete')
    need(set(physical['scratch_by_native_id'])=={f['id'] for f in outputs},'scratch source set differs')
    total=collections.Counter()
    for frame,scratch,reference in zip(outputs,scratches,references):
        need(scratch['id']==reference['id']==frame['id'],'decode summary attributed to different RGB source')
        stats=physical['scratch_by_native_id'][frame['id']]
        for k in ('requests','responses','write_requests','read_requests','max_address'):need(scratch[k]==stats[k],'scratch source accounting differs: '+k)
        need(scratch['write_responses']==stats['write_requests'] and scratch['read_responses']==stats['read_requests'] and stats['errors']==0,'scratch endpoint response incomplete')
        need(scratch['write_words']==stats['write_requests']*8 and scratch['read_words']==stats['read_requests']*8 and stats['commands']==stats['write_requests']*8+stats['read_requests'],'physical scratch cost differs')
        need(scratch['first_cycle']*10000-5000==stats['first_request_ps'] and scratch['last_cycle']*10000-5000==stats['last_ack_ps'],'scratch source fences differ')
        need(frame['native_start_cycle']<=scratch['first_cycle']<=scratch['last_cycle']<=frame['commit_cycle'],'scratch work outside provisional decode')
        for k in ('requests','responses','commands'):total[k]+=stats[k]
        need(scratch['physical_requests']==total['requests'] and scratch['physical_responses']==total['responses'] and scratch['physical_commands']==total['commands'],'cumulative physical scratch counters differ')
        expected=0 if frame['fid']==0 else 7806
        need(reference['tile_requests']==reference['tile_responses']==expected and reference['line_requests']==reference['line_responses']==expected*4 and reference['x16_read_words']==expected*32,'reference work differs')
        need(reference['start_cycle']==frame['native_start_cycle'] and reference['input_complete_cycle']==frame['packet_complete_cycle'] and reference['commit_cycle']==frame['commit_cycle'],'reference/decode fences differ')
    service=services[0]
    need(service['writes']==physical['physical_write_words']==616872 and service['readwords']==physical['physical_captured_words']==824424,'final common pin word counters differ')
    need(service['writer_grants']==service['wr_rows']==140160 and service['writer_commands']==service['wr_words_accepted']==service['wr_words_retired']==560640,'final video writer counters differ')
    need(service['reader_grants']==service['reader_commands']==service['rd_requests']==service['rd_responses']==96024 and service['rd_count_beats']==768192,'final video reader counters differ')
    need(physical['native_scratch_observers']==dict(requests=14058,responses=14058),'native scratch witness count differs')


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--unit-only',action='store_true');args=ap.parse_args()
    reviewed=json.loads((HERE/'reviewed-source-hashes.json').read_text())
    for name,digest in reviewed.items():need(sha(ROOT/name)==digest,'reviewed overlap source differs: '+name)
    provenance=prior.control.prior.provenance
    prior.control.prior.BASELINE='4309c7a8b6c24f577b305cd11b124391aded4112';prior.control.prior.REVIEWED=reviewed
    up,unit=provenance('fpga/experiments/cu66-v91l-overlap-lease/results.json','PASS_DISPLAY_OVERLAP_LEASE_DIRECTED')
    need(len(unit['modes'])==1 and unit['payload_memory_bytes']==0 and not unit['hardware_tested'],'lease unit scope differs')
    raw=list(events(up.parent/unit['modes'][0]['event_log']));checks=[e for e in raw if e['type']=='check']
    need(len(checks)==unit['modes'][0]['verdict']['checks']==147 and all(e['status']=='PASS' for e in checks),'lease directed coverage incomplete')
    lease=LeaseTrace()
    for event in raw:lease.feed(event)
    lease_unit=lease.finish();negatives=lease_negatives(raw)
    need(lease_unit['requests']==13 and lease_unit['accepted']==lease_unit['releases']==6 and lease_unit['rejected']==7 and lease_unit['alias_blocks']==17,'unit lease raw receipt counts differ')
    inherited={str((FROZEN/n).relative_to(ROOT)):sha(FROZEN/n) for n in ('verify_results.py','scratch_trace.py')}
    expected=json.loads((FROZEN/'audit.json').read_text())
    need(inherited[str((FROZEN/'verify_results.py').relative_to(ROOT))]==expected['verifier_sha256'] and inherited[str((FROZEN/'scratch_trace.py').relative_to(ROOT))]==expected['scratch_trace_sha256'],'frozen scratch oracle changed')
    original_helpers={**expected['original_helper_sha256'],
        **{str((ROOT/'experiments/python-gamebub-v91l-shared-service'/n).relative_to(ROOT)):d for n,d in prior.control.OLD_PINS.items()}}
    result=dict(schema='cu66-v91l-overlap-independent-audit-v1',status='PASS_INDEPENDENT_DISPLAY_LEASE_UNIT',unit_report=str(up.relative_to(ROOT)),unit_report_sha256=sha(up),lease_unit=lease_unit,directed_checks=147,checker_negative_controls=negatives,reviewed_source_sha256=reviewed,inherited_checker_sha256={**inherited,**expected['inherited_checker_sha256']},original_helper_sha256=original_helpers,verifier_sha256=sha(Path(__file__)),lease_verifier_sha256=sha(HERE/'lease_trace.py'))
    if not args.unit_only:
        lp,live=provenance('fpga/experiments/cu66-v91l-overlap-live/results.json','PASS_EXACT_NATIVE_DECODE_DISPLAY_OVERLAP_SAME_TIMED_MEMORY')
        need(live['native_decode_display_overlap'] and not live['serial_live_commit_then_rgb'] and live['all_external_memory_endpoints_rtl'] and not live['scratch_memory_actors'],'native concurrency not real shared memory')
        need(not live['hardware_overlap_qualified'] and not live['physical_hardware_tested'] and not live['hardware_30fps_proven'] and not live['full_live_physical_service_complete'] and not live['full_rtl_hud_decoder'] and not live['full_rtl_hud_overlay'],'unsupported complete/hardware scope')
        need(len(live['modes'])==5 and {(m['seed'],m['t_ac_ns'],m['guard_mode']) for m in live['modes']}=={(s,t,False) for s in (912901,912902) for t in (2,7)}|{(912901,2,True)},'natural/guard campaign grid differs')
        fixtures=native.expected_frames(lp.parent);goldens={}
        for line in gzip.open(lp.parent/'inputs/rgb_goldens.tsv.gz','rt'):
            ident,data=line.rstrip().split('\t')
            if ident in ('actual_001','actual_006'):goldens[ident]=bytes.fromhex(data)
        modes=[]
        for mode in live['modes']:
            modes.append(audit_mode(lp.parent,mode,fixtures,goldens));print('AUDITED_NATIVE_OVERLAP',mode['seed'],mode['t_ac_ns'],mode['guard_mode'],flush=True)
        result.update(status='PASS_INDEPENDENT_NATIVE_DECODE_DISPLAY_OVERLAP',live_report=str(lp.relative_to(ROOT)),live_report_sha256=sha(lp),live_modes=modes,exact_native_RGB_outputs=10,distinct_native_source_images=2,rtl_sha_jobs=10250,
            scope='Four natural key-RGB/delta-decode overlaps and one separate directed native final-pixel hold; actual shared pins and immutable display ownership. Native HUD/software/network costs, hardware cadence and routed timing remain excluded.')
    (HERE/('audit-unit.json' if args.unit_only else 'audit.json')).write_text(json.dumps(result,indent=2)+'\n');print(result['status'],flush=True)
if __name__=='__main__':main()
