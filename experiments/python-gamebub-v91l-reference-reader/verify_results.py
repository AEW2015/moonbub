#!/usr/bin/env python3
"""Independent physical-reference / native pixel / validation / pin audit.

Writer/hash/RGB checking is a reviewed continuation of the frozen shared-service
checker, with added reference intent/mux/BL8 checking. Original helper hashes
remain pinned. No oracle is derived from the new DUT or its native C++ bench.
"""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OLD=ROOT/'experiments/python-gamebub-v91l-shared-service'
OLD_PINS={'verify_results.py':'e5fcc0a08d1e17a6b7b340fad698985d860bea034b9674c1f0d5425277be88c8',
          'memory_audit.py':'60fe164c88135a613ecc706556bcc21216cbcae7917673957a7cc22ae43f0c92'}
for name,digest in OLD_PINS.items():assert hashlib.sha256((OLD/name).read_bytes()).hexdigest()==digest,'frozen checker changed: '+name
sys.path.insert(0,str(OLD))
spec=importlib.util.spec_from_file_location('reference_frozen_shared_checker',OLD/'verify_results.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
from memory_audit import Replay,events,need,numeric,sha,native,physical_byte
from reference_trace import ReferenceTraffic,ordered_reference
from unit_trace import TileTrace,MuxTrace
merge,rows,LINE_ORDER,fnv=prior.merge,prior.rows,prior.LINE_ORDER,prior.fnv
BASELINE='380539d99164cc88b1b92b2620fcaca57ef2216c'
REVIEWED={
 'fpga/experiments/cu66-v91l-reference-reader/reference_tile_reader.sv':'b4d50c15cc57952aa20633d26691c07aef0924c8b6292a26ba41b71bfcd913d5',
 'fpga/experiments/cu66-v91l-reference-reader/reader_client_mux.sv':'dd95c307680225894d1e91a9239c3cb4105b89dab96f034a7dafcdd293ebd9d7',
 'fpga/experiments/cu66-v91l-reference-reader/reference_shared_timed.sv':'1990febcb3f454e95b0d2f6c1093a5ffd8bcf04f709398502e720d813f447bc9',
 'fpga/experiments/cu66-v91l-reference-live/reference_live.sv':'599cf87f7865b91dfc2903d0470067555110929b6dff675edc8ca513fca813db',
 'fpga/experiments/cu66-v91l-reference-live/tb_reference_live.cpp':'ffb5ababddd3c3ed2acd90eb60d84e5a6fb70613753cd9c54bdcee21faf0f827',
 'fpga/experiments/cu66-v91l-reference-live/make_wrapper.py':'4ddd5843303bb920f8f907ff5817272346a74486142af240ff18dc857f26b715',
 'fpga/experiments/cu66-v91l-reference-live/make_bench.py':'1148e5905b7e9bd84e5e34b71919ee38c1fc84ca49c6e5b35c0bd6ad3910a1f7',
 'fpga/experiments/cu66-v91l-reference-live/bench_extension.inc':'aaaeb8919e021948b2b06d63638f7bde23535a2fe3aa95bb53248f910e887e37',
 'scripts/cu66-v91l-reference-live/run_test.py':'77544add3747bfaadd304bf832f3688df76dfbf5ee1fee8d92d1ec69fa1ece6c',
}
prior.BASELINE=BASELINE
prior.REVIEWED=REVIEWED

def read_cases_modes(path):
    cases=native.read_cases(path)
    for raw in path.read_text().splitlines():
        if raw.strip():
            fields=raw.split('\t');cases[fields[0]]['operations']=bytes.fromhex(fields[11])
    return cases

def check_reference_counters(directory,reference,actual_frames):
    records=list(e for e in events(directory/'physical-events.jsonl.gz') if e['type'] in ('reference_frame','service_counts'))
    frames=[e for e in records if e['type']=='reference_frame'];service=[e for e in records if e['type']=='service_counts']
    need(len(frames)==len(service)==2,'reference/service counter receipts incomplete')
    for i,(f,s,observed) in enumerate(zip(frames,service,actual_frames)):
        expected=0 if i==0 else 7806
        need(f['tile_requests']==f['tile_responses']==expected and f['line_requests']==f['line_responses']==expected*4,'reference counter summary differs')
        need(f['x16_read_words']==expected*32,'reference x16 counter differs')
        need(s['writes']==(i+1)*280320 and s['readwords']==(259200 if i==0 else 768192),'pin word counters differ')
        need(s['writer_commands']==s['wr_words_accepted']==s['wr_words_retired']==(i+1)*280320,'writer acceptance/retirement counters differ')
        need(s['reader_commands']==s['rd_requests']==s['rd_responses']==(32400 if i==0 else 96024),'physical read counter summary differs')
        need(s['rd_count_beats']==s['readwords'],'captured/read pin word counters differ')
        need(f['last_canonical_pixel_cycle']<=f['commit_cycle']<=f['rgb_closed_cycle'],'reference stage/fence counters invalid')
        need(f['start_cycle']==observed['native_start_cycle'] and f['input_complete_cycle']==observed['packet_complete_cycle'] and
             f['commit_cycle']==observed['commit_cycle'] and f['rgb_closed_cycle']==observed['closed_cycle'],'reference frame counter fences differ')
    return records

def reference_negatives(trace,physical_trace):
    tests=[('ref_req',lambda e:dict(e,accepted_generation=e['accepted_generation']^(1<<32)),'legal owned tile'),
           ('ref_line_req',lambda e:dict(e,address=e['address']+16),'address/index/ticket'),
           ('ref_line_rsp',lambda e:dict(e,ticket=e['ticket']^1),'identity/ticket'),
           ('ref_line_rsp',lambda e:dict(e,data=f'{int(e["data"],16)^1:032x}'),'assembled reference bytes'),
           ('ref_rsp',lambda e:dict(e,generation=e['generation']^(1<<32)),'full identity'),
           ('ref_rsp',lambda e:dict(e,data=f'{int(e["data"],16)^1:0128x}'),'held reference reply')]
    results=[]
    for kind,mutation,cause in tests:
        index=next(i for i,e in enumerate(trace) if e['type']==kind)
        changed=[*trace];changed[index]=mutation(trace[index]);oracle=TileTrace()
        try:
            for event in changed:oracle.feed(event)
            oracle.finish()
        except AssertionError as error:
            need(cause in str(error),'reference negative failed for wrong reason: '+str(error))
            results.append(dict(kind=kind,index=index,original=trace[index],corrupted=changed[index],rejected=True,reason=str(error)))
        else:raise AssertionError('reference checker accepted corruption: '+kind)
    for kind,mutation,cause in [('mux_owner',lambda e:dict(e,owner=3-e['owner']),'fairness/grant'),
                                ('mux_rsp',lambda e:dict(e,data=f'{int(e["data"],16)^1:032x}'),'response data')]:
        index=next(i for i,e in enumerate(physical_trace) if e['type']==kind and (kind!='mux_owner' or e['old_owner']==0))
        changed=[*physical_trace];changed[index]=mutation(physical_trace[index]);oracle=MuxTrace()
        try:
            for event in changed:oracle.feed(event)
            oracle.finish()
        except AssertionError as error:
            need(cause in str(error),'mux negative failed for wrong reason: '+str(error))
            results.append(dict(kind=kind,index=index,original=physical_trace[index],corrupted=changed[index],rejected=True,reason=str(error)))
        else:raise AssertionError('mux checker accepted corruption: '+kind)
    return results

def audit_native_mode(attempt,mode,frames,goldens):
    directory=attempt/mode['directory'];bus=iter(native.iter_bus(directory/'bus.bin.gz'))
    memory=Replay(True);refs=ReferenceTraffic(read_cases_modes(attempt/'inputs/cases.tsv'),frames);current=None;done=[];line=None;delivered=[];pixel_rows=[];holds=[];presented=[]
    pipeline_cases=[]
    def observed_stdout():
        for event in events(attempt/f'pins-seed{mode["seed"]}-tac{mode["t_ac_ns"]}.jsonl.gz'):
            if event['type']=='case':pipeline_cases.append(event)
            yield event
    stream=ordered_reference(merge(observed_stdout(),events(directory/'physical-events.jsonl.gz')))
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
    need(result['physical_write_words']==560640 and result['physical_captured_words']==768192,'physical full-frame work differs')
    hashes=native.parse_hash_trace(directory/'hashes.jsonl.gz');need(len(hashes)==2,'native RTL SHA group count differs')
    for row in mode['live_cases']:
        f=frames[row['id']];key=(row['id'],0,row['epoch'])
        need(hashes.pop(key)==native.expected_hash_jobs(f),'actual RTL C2/HUD/seal digest differs from independent hashlib')
        need(row['root']==f['root'].hex() and row['hud_sha256']==f['hud_sha'].hex() and row['seal']==f['seal'].hex(),'accepted content commitments differ')
        need(row['hash_jobs']==1025 and row['hash_message_bytes']==628815 and row['hash_blocks']==10298,'hash work accounting differs')
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
    counters=check_reference_counters(directory,reference,done)
    return dict(reference=reference,reference_counters=counters,seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],physical=result,frames=done,rtl_sha_jobs=2050,
                source_canonical_HUD_bytes=1121280,publication_hold_checks=len(holds),presented_fids=presented)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--unit-only',action='store_true');args=ap.parse_args()
    up,unit=prior.provenance('fpga/experiments/cu66-v91l-reference-reader/results.json','PASS_REFERENCE_READER_DIRECTED')
    need(unit['new_payload_bytes']==64 and not unit['physical_hardware_tested'] and not unit['native_preload'],'unit scope/payload differs')
    need({m['mode'] for m in unit['modes']}=={'unit','timed2','timed7'} and len(unit['modes'])==3,'reference unit modes incomplete')
    modes=[];traces={};negatives=[]
    for mode in unit['modes']:
        raw=list(events(up.parent/mode['event_log']));checks=[e for e in raw if e['type']=='check']
        expected=698 if mode['mode']=='unit' else 611
        need(mode['verdict']['checks']==len(checks)==expected and all(e['status']=='PASS' for e in checks),'reference directed entries incomplete')
        trace=list(ordered_reference(raw));tile=TileTrace();mux=MuxTrace();memory=Replay(False)
        for event in trace:
            tile.feed(event)
            if mode['mode']!='unit':mux.feed(event);memory.feed(event)
        row=dict(mode=mode['mode'],t_ac_ns=mode['t_ac_ns'],tile=tile.finish(),checks=expected)
        if mode['mode']!='unit':
            row.update(mux=mux.finish(),physical=memory.finish())
            negatives.extend(dict(mode=mode['mode'],**n) for n in prior.negative_controls(trace))
        traces[mode['mode']]=trace;modes.append(row)
    negatives.extend(dict(mode='reference-unit/mux-timed2',**n) for n in reference_negatives(traces['unit'],traces['timed2']))
    result=dict(schema='cu66-v91l-reference-independent-audit-v1',status='PASS_INDEPENDENT_REFERENCE_UNIT_AND_PIN_AUDIT',
                unit_report=str(up.relative_to(ROOT)),unit_report_sha256=sha(up),unit_modes=modes,
                checker_negative_controls=negatives,prior_checker_sha256=OLD_PINS,original_helper_sha256=prior.HELPERS,
                reviewed_source_sha256=REVIEWED,verifier_sha256=sha(Path(__file__)),
                reference_verifier_sha256=sha(HERE/'reference_trace.py'),unit_verifier_sha256=sha(HERE/'unit_trace.py'))
    if not args.unit_only:
        lp,live=prior.provenance('fpga/experiments/cu66-v91l-reference-live/results.json','PASS_EXACT_PHYSICAL_REFERENCE_LIVE_TO_SAME_TIMED_MEMORY_RGB')
        need(live['physical_reference_service'] and live['accepted_reference_service_rtl'],'reference actor was not replaced')
        need(not live['scratch_service_rtl'] and not live['physical_preload'] and not live['full_live_physical_service_complete'] and
             not live['full_rtl_hud_decoder'] and not live['full_rtl_hud_overlay'] and not live['hardware_30fps_proven'] and not live['physical_hardware_tested'],'unsupported complete/hardware scope')
        need(len(live['modes'])==4 and {(m['seed'],m['t_ac_ns']) for m in live['modes']}=={(s,t) for s in (912901,912902) for t in (2,7)},'native seed/corner grid incomplete')
        frames=native.expected_frames(lp.parent);goldens={}
        for line in gzip.open(lp.parent/'inputs/rgb_goldens.tsv.gz','rt'):
            ident,data=line.rstrip().split('\t')
            if ident in ('actual_001','actual_006'):goldens[ident]=bytes.fromhex(data)
        qualified=[]
        for mode in live['modes']:
            qualified.append(audit_native_mode(lp.parent,mode,frames,goldens));print('AUDITED_PHYSICAL_REFERENCE',mode['seed'],mode['t_ac_ns'],flush=True)
        result.update(status='PASS_INDEPENDENT_PHYSICAL_REFERENCE_LIVE_VALIDATION_AND_NATIVE_RGB',
                      live_report=str(lp.relative_to(ROOT)),live_report_sha256=sha(lp),live_modes=qualified,
                      exact_native_RGB_outputs=8,rtl_sha_jobs=8200,
                      scope='Supported native BR88 key/delta physical candidate writes and accepted-reference reads, real validation and same-memory RGB. Scratch and native HUD remain software endpoints; serial run, no full physical service/hardware30fps/complete under10ms claim.')
    for path,report in [(up,unit)]+([] if args.unit_only else [(lp,live)]):
        for name,digest in report['source_sha256'].items():need(sha(ROOT/name)==digest,'source changed during audit: '+name)
    (HERE/('audit-unit.json' if args.unit_only else 'audit.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],flush=True)
if __name__=='__main__':main()
