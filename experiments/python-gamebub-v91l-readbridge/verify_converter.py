#!/usr/bin/env python3
"""Independent RGB join lease/line/burst/row/file audit; no hardware inference."""
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
AREA=ROOT/'fpga/experiments/cu66-v91l-converter'
BASELINE='b96944dd9897e2bf4e9ed2978bdbade79cdccb7b'
LIB=ROOT/'experiments/python-gamebub-v91l-tiled/verify_rowpair.py'
LIB_SHA='8e40414864dbe0a28d2e522b51fa65ac20e8ca8aabc14fe5c17dd306cfcf7454'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def need(ok,message):
    if not ok:raise AssertionError(message)
need(sha(LIB)==LIB_SHA,'frozen gather oracle changed')
spec=importlib.util.spec_from_file_location('frozen_rowpair_oracle',LIB)
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
GatherOracle=legacy.GatherOracle
CANONICAL=legacy.CANONICAL
RGB=ROOT/'experiments/python-gamebub-v91k/vectors/rgb_goldens.tsv.gz'
PHYSICAL=('address','bank','epoch','generation')
REQUIRED_CHECKS={
    'invalid_start_bank_epoch_generation_rejected',
    'cancel_pending_drains_both_adapters','reset_pending_drains_both_adapters',
    'cancel_unaccepted_physical_offer_closes_without_bus_owner',
    'wrong_physical_generation_ignored_until_matching_return',
    'physical_error_propagates_and_drains_line_and_byte_owners',
    'cancel_on_matching_physical_return_edge','cancel_on_logical_line_response_edge',
    'reset_on_matching_physical_return_edge','reset_on_logical_line_response_edge',
    'held_rgb_pixel_stable_then_cancel_invalidates_output',
    'actual_full_RGB565_actual_001','actual_full_RGB565_actual_006',
}


def load_inputs():
    images,tiles,forward=legacy.load_images()
    schedule=legacy.derived_schedule()
    rgb={}
    with gzip.open(RGB,'rt') as stream:
        for line in stream:
            name,hx=line.rstrip().split('\t')
            if name in images:rgb[name]=bytes.fromhex(hx)
    need(set(rgb)==set(images) and all(len(v)==691200 for v in rgb.values()),'missing native RGB goldens')
    return images,tiles,forward,schedule,rgb


def fnv(data):
    value=1469598103934665603
    for byte in data:value=((value^byte)*1099511628211)&((1<<64)-1)
    return value


def replay(stream,seed,retain,images,tiles,forward,schedule,rgb,attempt=None,timed=False):
    config=session=line=bus=verdict=None
    last_cycle=-1
    counts=collections.Counter();checks=set();frames=[]
    held_pixel=None;held_receipts=0;wrong_tags=0
    for event in stream:
        kind=event['type'];counts[kind]+=1
        cycle=event.get('cycle',event.get('closed_cycle',event.get('last_cycle',last_cycle)))
        need(cycle>=last_cycle,'receipts move backward in time')
        last_cycle=cycle
        if kind=='config':
            need(config is None and event['seed']==seed and event['retain']==retain,'config/static seed differs')
            need(event['service']==('ACTUAL_CONTROLLER_TIMED_SDRAM_PINS' if timed else 'BL8_8payload_plus1to5wait_seeded_ready'),'read service differs')
            config=event
        elif kind=='start':
            need(line is None and bus is None,'start overwrites accepted owner')
            need(session is None or not session['active'],'new start before previous lease closed')
            need(event['image'] in images,'unknown native image')
            valid=event['bank']<3 and event['epoch']!=0 and event['generation']!=0
            session=dict(event,active=valid,valid=valid,killed=False,lines=0,line_acks=0,phys_reads=0,phys_acks=0,
                         rows=0,first_pixel=None,last_pixel=None,physical_error=False,
                         oracle=GatherOracle(retain,tiles[event['image']],forward))
            held_pixel=None
        elif kind=='kill':
            need(session is not None,'kill without initialized session')
            need(event['reset'] or event['cancel'],'kill input absent')
            need(bool(event['physical_pending'])==(bus is not None),'kill physical ownership differs')
            need(bool(event['line_pending'])==(line is not None),'kill line ownership differs')
            session['active']=False;session['killed']=True;session['last_kill_cycle']=cycle
            held_pixel=None
        elif kind=='line_req':
            need(session is not None and session['active'] and line is None and bus is None,'line request without free valid lease')
            need(event['epoch']==session['epoch'] and event['token']==session['lines'],'line lease/token differs')
            index=session['lines']
            need(index<len(schedule) and event['address']==schedule[index],'actual converter line order differs from independent FSM schedule')
            actions,row_hits,scratch_hits=session['oracle'].request(event['address'])
            line=dict(event,actions=actions,issued=0,returned=0,memory_error=False,row_hits=row_hits,scratch_hits=scratch_hits)
            session['lines']+=1
        elif kind=='phys_req':
            need(session is not None and session['active'] and line is not None and bus is None,'physical read without a free live line owner')
            need(all(event[key]==session[key] for key in ('bank','epoch','generation')),'physical lease differs from accepted descriptor')
            index=line['issued']
            need(index<len(line['actions']) and event['address']==line['actions'][index],'physical burst differs from independent tile gather/retention')
            need(event['address']%16==0 and 0<=event['address']<=518384,'physical burst range/alignment')
            if not timed:need(9<=event['due']-cycle<=13,'physical service delay differs')
            line['issued']+=1;session['phys_reads']+=1;bus=dict(event,controller_accepted=False,captured=[],controller_drained=False,idle_fences=0)
        elif kind=='controller_req':
            need(timed and bus is not None and not bus['controller_accepted'],'controller request without unique bridge owner')
            need(event['write']==0 and event['address']==(bus['bank']<<22)|(bus['address']>>1),'controller command address differs')
            need(event['time_ps']==cycle*10000+5000,'controller request time differs from upcoming posedge')
            bus['controller_accepted']=True
        elif kind=='controller_read':
            need(timed and bus is not None and bus['controller_accepted'] and len(bus['captured'])<8,'unowned/excess controller read beat')
            index=len(bus['captured']);offset=bus['address']+2*index
            need(event['data']==int.from_bytes(tiles[session['image']][offset:offset+2],'little'),'controller beat bytes differ')
            need(event['time_ps']==cycle*10000+5000,'controller read time differs from sampling posedge')
            bus['captured'].append(event['data']);bus['last_beat_cycle']=cycle
        elif kind=='controller_done':
            need(timed and bus is not None and bus['controller_accepted'] and len(bus['captured'])==8 and not bus['controller_drained'],'controller drain before eight beats or duplicated')
            need(event['write']==0 and event['address']==(bus['bank']<<22)|(bus['address']>>1),'controller drain identity differs')
            bus['controller_drained']=True
        elif kind=='bridge_fence':
            need(timed and bus is not None and bus['controller_accepted'] and len(bus['captured'])==8,'bridge fence before accepted read completed')
            need(event['beats']==8 and event['pending']==1,'bridge fence ownership differs')
            bus['idle_fences']=bus['idle_fences']+1 if event['ctrl_idle'] else 0
        elif kind=='wrong_tag':
            need(bus is not None and event['ready']==0,'wrong tag consumed physical owner')
            need(event['address']==bus['address'] and event['generation']!=bus['generation'],'wrong tag not distinct')
            need(cycle>=bus['due'],'wrong-tag response before service due')
            wrong_tags+=1;bus['due']=cycle+1
        elif kind=='phys_rsp':
            need(bus is not None and line is not None and session is not None,'physical response has no owner')
            need(all(event[key]==bus[key] for key in PHYSICAL),'physical response identity differs')
            if not timed:need(cycle==bus['due'],'physical response timing differs from accepted due cycle')
            elif bus['controller_accepted']:
                need(len(bus['captured'])==8 and bus['controller_drained'] and bus['idle_fences']>=2,'physical response before capture/drain/idle fence')
                if not event['error']:need(bytes.fromhex(event['data'])==b''.join(v.to_bytes(2,'little') for v in bus['captured']),'bridge response packing differs')
            else:need(session['killed'] and event['error']==1,'physical response without accepted controller read')
            expected_physical=bytes(16) if timed and event['error'] else tiles[session['image']][event['address']:event['address']+16]
            need(bytes.fromhex(event['data'])==expected_physical,'physical bytes differ from independent tiled image')
            need(event['error'] in (0,1),'invalid physical error')
            if event['error']:
                line['memory_error']=True;session['physical_error']=True
            line['returned']+=1;session['phys_acks']+=1;bus=None
        elif kind=='line_rsp':
            need(line is not None and session is not None and bus is None,'line response before physical drain or without owner')
            need(all(event[key]==line[key] for key in ('address','epoch','token')),'line response logical identity differs')
            need(event['bank']==session['bank'] and event['generation']==session['generation'],'line response lease changed')
            need(line['issued']==line['returned'],'line response before all issued reads returned')
            already_offered_success=session['killed'] and session.get('last_kill_cycle')==cycle and event['error']==0 and not line['memory_error']
            error=0 if already_offered_success else 4 if session['killed'] else 5 if line['memory_error'] else 0
            need(event['error']==error,'line error differs from cancellation/memory contract')
            data=bytes.fromhex(event['data'])
            if error:
                need(data==bytes(16),'error line leaked stale data')
            else:
                need(line['issued']==len(line['actions']),'successful line omitted a required physical burst')
                need(data==images[session['image']][event['address']:event['address']+16],'canonical line bytes differ')
            if error:session['active']=False
            session['line_acks']+=1;line=None
        elif kind=='pixel_hold':
            need(session is not None and session['active'] and event['epoch']==session['epoch'],'held pixel outside accepted lease')
            need(event['ready']==0,'hold receipt not stalled')
            payload=tuple(event[key] for key in ('address','epoch','word'))
            if held_pixel is None:held_pixel=payload
            need(payload==held_pixel,'held pixel identity/data changed')
            offset=event['address']*2
            need(int.from_bytes(rgb[session['image']][offset:offset+2],'little')==event['word'],'held pixel differs from native RGB golden')
            held_receipts+=1
        elif kind=='pixel_row':
            need(session is not None and session['active'],'RGB row outside live lease')
            row=session['rows']
            need(event['row']==row and event['pixels']==720 and event['epoch']==session['epoch'],'pixel row identity/order differs')
            expected=rgb[session['image']][row*1440:(row+1)*1440]
            need(event['hash_fnv64']==fnv(expected),'RGB row digest differs from frozen golden')
            need(event['first_cycle']<=event['last_cycle'],'pixel row cycle order differs')
            if row==0:session['first_pixel']=event['first_cycle']
            elif session['last_pixel'] is not None:need(event['first_cycle']>session['last_pixel'],'pixel rows overlap/reorder')
            session['last_pixel']=event['last_cycle'];session['rows']+=1
        elif kind=='frame':
            need(session is not None and session['active'] and line is None and bus is None,'frame closes before all owners drain')
            need(event['name']==session['image'] and all(event[k]==session[k] for k in ('bank','epoch','generation')),'frame lease differs')
            need(event['pixels']==345600 and event['bytes']==691200 and session['rows']==480,'incomplete RGB frame')
            need(session['lines']==session['line_acks']==event['logical_reads']==32400,'logical frame traffic mismatch')
            need(session['phys_reads']==session['phys_acks']==event['physical_reads']==(32400 if retain else 64800),'physical frame traffic mismatch')
            need(event['start_cycle']==session['cycle'],'frame start differs from accepted descriptor')
            need(event['first_pixel_cycle']==session['first_pixel'] and event['last_pixel_cycle']==session['last_pixel'],'pixel cycle fence differs')
            need(event['closed_cycle']>session['last_pixel'],'closure before final pixel')
            for key,terminal in (('start_to_first_pixel','first_pixel_cycle'),('start_to_last_pixel','last_pixel_cycle'),('start_to_closed','closed_cycle')):
                need(event[key]==event[terminal]-event['start_cycle'],'frame latency arithmetic differs')
            if timed:
                for key,length in (('state_cycles',16),('adapter_state_cycles',4),('reader_state_cycles',8)):
                    need(isinstance(event.get(key),list) and len(event[key])==length,'timed histogram shape differs: '+key)
                    need(all(isinstance(v,int) and not isinstance(v,bool) and v>=0 for v in event[key]),'negative/noninteger timed histogram count: '+key)
                    need(sum(event[key])==event['start_to_closed'],'timed histogram does not cover frame fence: '+key)
                for key in ('reader_pending_cycles','adapter_pending_cycles','controller_busy_cycles','bridge_pending_cycles'):
                    need(isinstance(event.get(key),int) and 0<=event[key]<=event['start_to_closed'],'timed overlapping pending count out of range: '+key)
            digest=hashlib.sha256(rgb[session['image']]).hexdigest()
            if attempt is not None:
                output=(attempt/event['output']).resolve()
                need(output.is_relative_to(attempt.resolve()),'RGB output escapes bundle')
                need(output.read_bytes()==rgb[session['image']],'actual RGB binary differs from frozen native golden')
            frames.append(dict(event,sha256=digest));session['active']=False
        elif kind=='check':
            need(event['status']=='PASS' and event['name'] not in checks,'duplicate/failed check')
            checks.add(event['name'])
            if event['name']=='physical_error_propagates_and_drains_line_and_byte_owners':
                need(session is not None and session['physical_error'] and line is None and bus is None,'physical-error closure not observed')
                session['active']=False
        elif kind=='verdict':
            need(verdict is None,'duplicate verdict');verdict=event
        else:raise AssertionError('unknown receipt '+kind)
    need(config is not None and verdict is not None and verdict['status']=='TEST_PASS','missing passing terminal verdict')
    need(verdict['seed']==seed and verdict['retain']==retain,'terminal mode/seed differs')
    need(line is None and bus is None and session is not None and not session['active'],'terminal owners/session not closed')
    need(len(frames)==2 and {f['name'] for f in frames}==set(images),'missing native RGB frame pair')
    required=({'timed_cancel_unissued_bridge_request_drains','timed_reset_unissued_bridge_request_drains','timed_cancel_after_three_controller_beats_drains_eight','timed_reset_after_three_controller_beats_drains_eight','timed_held_pixel_then_cancel','actual_full_RGB565_actual_001','actual_full_RGB565_actual_006'} if timed else REQUIRED_CHECKS)
    need(verdict['checks']==len(checks) and checks==required,'check verdict count/set differs')
    need((timed or wrong_tags>=1) and held_receipts>=8,'wrong-tag or held-pixel probe unobserved')
    return dict(seed=seed,retain=retain,event_counts=dict(counts),checks=sorted(checks),frames=frames,
                verdict=verdict,wrong_tag_responses=wrong_tags,held_pixel_receipts=held_receipts)


def negative_controls(path,seed,retain,images,tiles,forward,schedule,rgb):
    # A finite prefix containing the complete directed probes and first RGB row.
    prefix=[]
    for event in legacy.events(path):
        prefix.append(event)
        if event['type']=='pixel_row':break
    need(prefix and prefix[-1]['type']=='pixel_row','no RGB row for corrupted control')
    def first(kind,predicate=lambda e:True):return next(i for i,e in enumerate(prefix) if e['type']==kind and predicate(e))
    def fliphex(value):return f'{int(value[:2],16)^1:02x}'+value[2:]
    phys=first('phys_rsp');line=first('line_rsp',lambda e:e['error']==0)
    holds=[i for i,event in enumerate(prefix) if event['type']=='pixel_hold']
    need(len(holds)>=2,'missing repeated held-pixel receipts')
    hold=holds[1];wrong=first('wrong_tag');request=first('phys_req');row=len(prefix)-1
    due=prefix[request]['due'];delay=due-prefix[request]['cycle']
    controls=[
        ('corrupt_physical_bytes',phys,'data',fliphex(prefix[phys]['data']),'physical bytes differ'),
        ('corrupt_canonical_line',line,'data',fliphex(prefix[line]['data']),'canonical line bytes differ'),
        ('corrupt_line_identity',line,'token',prefix[line]['token']^1,'line response logical identity differs'),
        ('wrong_generation_releases_owner',wrong,'ready',1,'wrong tag consumed'),
        ('change_physical_due_cycle',request,'due',due+(1 if delay<13 else -1),'physical response timing differs'),
        ('corrupt_RGB_row_digest',row,'hash_fnv64',prefix[row]['hash_fnv64']^1,'RGB row digest differs'),
        ('change_held_RGB_word',hold,'word',prefix[hold]['word']^1,'held pixel identity/data changed'),
        ('drop_physical_response',phys,None,None,'line response before physical drain'),
    ]
    rejected=[]
    for name,index,field,value,reason in controls:
        def modified():
            for i,event in enumerate(prefix):
                if i==index:
                    if field is not None:yield {**event,field:value}
                else:yield event
        try:replay(modified(),seed,retain,images,tiles,forward,schedule,rgb)
        except AssertionError as error:
            need(reason in str(error),'negative control rejected for unrelated prefix reason: '+name+': '+str(error))
            rejected.append(dict(mutation=name,seed=seed,retain=retain,rejected=True,reason=str(error)))
        else:raise AssertionError('checker accepted mutation '+name)
    return rejected


def provenance(path):
    report=json.loads(path.read_text());attempt=path.parent
    need(report['schema']=='cu66-v91l-actual-rgb-converter-comparison-v1' and report['status']=='PASS_ACTUAL_RGB565_TILE_RETENTION_COMPARISON','selected actor campaign is not passing')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for a,b in ((BASELINE,report['source_revision']),(report['source_revision'],head)):
        need(subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT,capture_output=True).returncode==0,'source ancestry differs')
    for name,h in report['source_sha256'].items():
        need(sha(ROOT/name)==sha(attempt/'sources'/name)==h,'source/snapshot differs: '+name)
    for name,h in report['inputs_sha256'].items():
        need(sha(ROOT/name)==sha(attempt/'inputs'/Path(name).name)==h,'input snapshot differs: '+name)
    for name,h in report['artifacts_sha256'].items():need(sha(attempt/name)==h,'artifact differs: '+name)
    need(all(command['exit_code']==0 for command in report['commands']),'failed command')
    frozen=('fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',
            'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',
            'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv',
            'fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv')
    for name in frozen:
        expected=hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)).hexdigest()
        need(report['source_sha256'].get(name)==expected,'frozen converter/reader changed: '+name)
    builds=[command['argv'] for command in report['commands'] if '--build' in command['argv']]
    need(len(builds)==2,'expected two separately compiled retention modes')
    parameters=set()
    for argv in builds:
        need({'--cc','--exe','--build','--assert','-Wall'}<=set(argv),'weak RTL build flags')
        need(not any(str(v).startswith('-Wno-') for v in argv),'warning waived')
        need({'-std=c++20','-Wall','-Wextra','-Werror'}<=set(argv[argv.index('-CFLAGS')+1].split()),'weak C++ build flags')
        need(argv[argv.index('-j')+1]=='2','unexpected compile concurrency')
        need('--timescale-override' not in argv,'frozen timescales overridden')
        parameters.add(next(v for v in argv if str(v).startswith('-GRETAIN_ROWS=')))
        for name in frozen:
            need(str(attempt/'sources'/name) in argv,'frozen source not compiled from pinned snapshot')
        for name in ('fpga/experiments/cu66-v91l-converter/canonical_rgb565_tiled.sv','fpga/experiments/cu66-v91l-converter/tb_converter.cpp'):
            need(str(attempt/'sources'/name) in argv,'new source not compiled from snapshot')
    need(parameters=={"-GRETAIN_ROWS=1'b0","-GRETAIN_ROWS=1'b1"},'static mode matrix differs')
    need(report['actual_converter_rtl_join'] is True,'actual converter join flag absent')
    for key in ('physical_sdram_controller_join','shared_service_complete','physical_hardware_tested','sustained_hardware_30fps_proven','validated_full_frame_decode_under10ms_proven'):
        need(report[key] is False,'unsupported qualification claim: '+key)
    need('5.020' in (attempt/'tool-version.log').read_text() and '13.3.0' in (attempt/'compiler-version.log').read_text(),'tool version differs')
    return report


def checked_events(path,metadata):
    count=0;digest=hashlib.sha256()
    with gzip.open(path,'rb') as stream:
        for line in stream:
            digest.update(line);count+=1;yield json.loads(line)
    need(count==metadata['rows'] and digest.hexdigest()==metadata['raw_sha256'],'raw receipt digest/count differs')


def main():
    alias=json.loads((AREA/'comparison-results.json').read_text())
    path=(ROOT/alias['selected_report']).resolve()
    need(path.parent.parent==AREA/'comparison-attempts','selected report escapes actor attempt roots')
    report=provenance(path)
    need({k:v for k,v in alias.items() if k!='selected_report'}==report,'alias differs from retained report')
    images,tiles,forward,schedule,rgb=load_inputs()
    modes=[];mutations=[]
    for mode in report['modes']:
        meta=report['compressed_artifacts'][mode['event_log'].removesuffix('.gz')]
        trace=path.parent/meta['path']
        need(sha(trace)==meta['gzip_sha256'],'compressed event digest differs')
        audited=replay(checked_events(trace,meta),mode['seed'],mode['retain'],images,tiles,forward,schedule,rgb,trace.parent)
        need(audited['verdict']==mode['verdict'],'reported verdict differs')
        need(audited['checks']==sorted(mode['checks']),'reported checks differ')
        need(len(mode['frames'])==2,'missing native output pair')
        for actual,summarized in zip(audited['frames'],mode['frames']):
            for key in ('name','epoch','generation','bank','pixels','bytes','logical_reads','physical_reads',
                        'start_cycle','first_pixel_cycle','last_pixel_cycle','closed_cycle','start_to_first_pixel',
                        'start_to_last_pixel','start_to_closed','held_pixel_cycles','physical_ready_stalls','output'):
                need(actual[key]==summarized[key],'frame summary differs: '+key)
            need(actual['sha256']==summarized['output_sha256'],'frame output hash differs')
        mutations.extend(negative_controls(trace,mode['seed'],mode['retain'],images,tiles,forward,schedule,rgb))
        modes.append(audited);print('AUDITED_RGB_ACTOR',mode['variant'],mode['seed'],flush=True)
    need(len(modes)==4 and {(m['seed'],m['retain']) for m in modes}=={(s,r) for s in (912701,912702) for r in (0,1)},'missing/duplicate actor modes')
    seeds={m['seed'] for m in modes};need(len(seeds)==2 and {m['retain'] for m in modes}=={0,1},'incomplete static seed matrix')
    comparisons=[]
    for seed in sorted(seeds):
        before=next(m for m in modes if m['seed']==seed and m['retain']==0)
        after=next(m for m in modes if m['seed']==seed and m['retain']==1)
        for a,b in zip(before['frames'],after['frames']):
            need(a['name']==b['name'] and a['sha256']==b['sha256'],'matched native RGB changed')
            need(a['physical_reads']==2*b['physical_reads'],'retention physical-read gain differs')
            comparisons.append(dict(seed=seed,name=a['name'],independent_cycles=a['start_to_closed'],retained_cycles=b['start_to_closed'],
                                    independent_reads=a['physical_reads'],retained_reads=b['physical_reads'],sha256=a['sha256'],
                                    cycle_reduction_percent=(a['start_to_closed']-b['start_to_closed'])/a['start_to_closed']*100))
    need(len(report['comparisons'])==len(comparisons)==4,'comparison extent differs')
    for checked,reported in zip(comparisons,report['comparisons']):
        for ours,theirs in (('seed','seed'),('name','frame'),('independent_cycles','independent_cycles'),('retained_cycles','retained_cycles'),('independent_reads','independent_bursts'),('retained_reads','retained_bursts'),('cycle_reduction_percent','cycle_reduction_percent')):
            need(checked[ours]==reported[theirs],'reported comparison differs: '+ours)
    result=dict(schema='cu66-v91l-converter-independent-audit-v1',status='PASS_INDEPENDENT_NATIVE_RGB565_JOIN_AUDIT',
                selected_report=str(path.relative_to(ROOT)),report_sha256=sha(path),verifier_sha256=sha(Path(__file__)),
                frozen_oracle_sha256=LIB_SHA,canonical_input_sha256=sha(CANONICAL),rgb_golden_sha256=sha(RGB),
                modes=modes,comparisons=comparisons,checker_negative_controls=mutations,
                assertions=dict(actual_frozen_converter_and_reader_joined=True,all_native_RGB_words_exact=True,
                                source_derived_line_order_matches_actual_requests=True,all_physical_bursts_and_data_exact=True,
                                leased_identity_and_cancellation_drains=True,held_pixel_probe_stable=True,
                                physical_controller_qualified=False,shared_live_decode_qualified=False,hardware_qualified=False),
                scope='Actual joined native base RGB565 converter and retention-reader RTL with declared read actor. Source/golden bytes, line/burst owners, row digests, native output binaries and closure fences independently audited. Physical controller, semantic HUD decode/overlay, live decode/publication/shared service, achieved frequency and hardware30fps/full-under10ms are not qualified.')
    timed_alias=AREA/'timed-results.json'
    if timed_alias.exists():
        timed_pointer=json.loads(timed_alias.read_text())
        if timed_pointer.get('status')=='PASS_NATIVE_RGB565_ACTUAL_TIMED_SDRAM' and set(timed_pointer.get('seeds',[]))=={912701,912702} and set(timed_pointer.get('t_ac_ns',[]))=={2,7}:
            result['timed_rgb']=audit_timed(timed_pointer,images,tiles,forward,schedule,rgb)
    (HERE/'audit-converter.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],flush=True)



def timed_provenance(pointer):
    path=(ROOT/pointer['selected_report']).resolve()
    need(path.parent.parent==AREA/'timed-attempts','timed report escapes retained roots')
    report=json.loads(path.read_text());attempt=path.parent
    need(report['schema']=='cu66-v91l-timed-rgb-converter-v1' and report['status']=='PASS_NATIVE_RGB565_ACTUAL_TIMED_SDRAM','timed report not passing')
    need({k:v for k,v in pointer.items() if k!='selected_report'}==report,'timed alias differs')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for a,b in ((BASELINE,report['source_revision']),(report['source_revision'],head)):
        need(subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT,capture_output=True).returncode==0,'timed source ancestry differs')
    for name,h in report['source_sha256'].items():need(sha(ROOT/name)==sha(attempt/'sources'/name)==h,'timed source/snapshot differs: '+name)
    for name,h in report['inputs_sha256'].items():need(sha(ROOT/name)==sha(attempt/'inputs'/Path(name).name)==h,'timed input differs: '+name)
    for name,h in report['artifacts_sha256'].items():need(sha(attempt/name)==h,'timed artifact differs: '+name)
    need(all(c['exit_code']==0 for c in report['commands']),'failed timed command')
    frozen=('fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',
            'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',
            'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv',
            'fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv',
            'fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv',
            'fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv')
    for name in frozen:
        expected=hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)).hexdigest()
        need(report['source_sha256'].get(name)==expected,'frozen timed child changed: '+name)
    builds=[c['argv'] for c in report['commands'] if '--build' in c['argv']]
    need(len(builds)==2,'timed requires both read-delay builds')
    corners=set()
    for argv in builds:
        need({'--cc','--exe','--build','--timing','--assert','-Wall','-DSIMULATION'}<=set(argv),'weak timed build flags')
        need(not any(str(v).startswith('-Wno-') for v in argv),'timed warning waived')
        need({'-std=c++20','-Wall','-Wextra','-Werror'}<=set(argv[argv.index('-CFLAGS')+1].split()),'weak timed C++ flags')
        need("-GRETAIN_ROWS=1'b1" in argv,'timed retention mode differs')
        corners.add(float(next(v.split('=')[1] for v in argv if str(v).startswith('-GT_AC_NS='))))
        for name in (*frozen,'fpga/experiments/cu66-v91l-converter/canonical_rgb565_tiled.sv','fpga/experiments/cu66-v91l-converter/canonical_rgb565_timed.sv','fpga/experiments/cu66-v91l-converter/tb_timed.cpp','fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv'):
            need(str(attempt/'sources'/name) in argv,'timed compiled source not pinned: '+name)
    need(corners=={2,7},'missing timed read-delay corner')
    need(report['actual_converter_rtl_join'] is True and report['physical_sdram_controller_join'] is True,'timed child join flags absent')
    for key in ('shared_service_complete','physical_hardware_tested','sustained_hardware_30fps_proven','validated_full_frame_decode_under10ms_proven'):
        need(report[key] is False,'unsupported timed full-path/hardware claim')
    return path,report


def timed_negative_controls(path,seed,images,tiles,forward,schedule,rgb):
    prefix=[]
    for event in legacy.events(path):
        prefix.append(event)
        if event['type']=='pixel_row':break
    need(prefix and prefix[-1]['type']=='pixel_row','no timed RGB row for corruption controls')
    def first(kind,predicate=lambda e:True):return next(i for i,e in enumerate(prefix) if e['type']==kind and predicate(e))
    def fliphex(value):return f'{int(value[:2],16)^1:02x}'+value[2:]
    phys=first('phys_rsp',lambda e:e['error']==0);line=first('line_rsp',lambda e:e['error']==0)
    beat=first('controller_read');fence=first('bridge_fence');done=first('controller_done')
    holds=[i for i,e in enumerate(prefix) if e['type']=='pixel_hold'];need(len(holds)>=2,'no repeated timed held pixels')
    hold=holds[1];row=len(prefix)-1
    controls=(
        ('timed_corrupt_controller_beat',beat,'data',prefix[beat]['data']^1,'controller beat bytes differ'),
        ('timed_drop_controller_drain',done,None,None,'physical response before capture/drain/idle fence'),
        ('timed_corrupt_fence_ownership',fence,'pending',0,'bridge fence ownership differs'),
        ('timed_corrupt_bridge_bytes',phys,'data',fliphex(prefix[phys]['data']),'bridge response packing differs'),
        ('timed_corrupt_canonical_line',line,'data',fliphex(prefix[line]['data']),'canonical line bytes differ'),
        ('timed_corrupt_RGB_row',row,'hash_fnv64',prefix[row]['hash_fnv64']^1,'RGB row digest differs'),
        ('timed_change_held_RGB',hold,'word',prefix[hold]['word']^1,'held pixel identity/data changed'),
        ('timed_drop_physical_response',phys,None,None,'physical read without a free live line owner'),
    )
    result=[]
    for name,index,field,value,reason in controls:
        def modified():
            for i,event in enumerate(prefix):
                if i==index:
                    if field is not None:yield {**event,field:value}
                else:yield event
        try:replay(modified(),seed,1,images,tiles,forward,schedule,rgb,timed=True)
        except AssertionError as error:
            need(reason in str(error),'timed corruption rejected for unrelated prefix reason: '+name+': '+str(error))
            result.append(dict(mutation=name,seed=seed,rejected=True,reason=str(error)))
        else:raise AssertionError('checker accepted timed corrupted receipt '+name)
    return result


def audit_timed(pointer,images,tiles,forward,schedule,rgb):
    path,report=timed_provenance(pointer)
    need(report['seeds']==[912701,912702] and report['t_ac_ns']==[2,7] and len(report['modes'])==4,'timed requires two seeds and both corners')
    modes=[];mutations=[]
    for mode in report['modes']:
        metadata=report['compressed_artifacts'][mode['event_log'].removesuffix('.gz')]
        trace=path.parent/metadata['path']
        need(sha(trace)==metadata['gzip_sha256'],'timed event gzip differs')
        output=replay(checked_events(trace,metadata),mode['seed'],1,images,tiles,forward,schedule,rgb,trace.parent,timed=True)
        need(mode['retain']==1 and output['verdict']==mode['verdict'],'timed retention/verdict differs')
        need(output['checks']==sorted(mode['checks']) and len(mode['frames'])==2,'timed frame/check set differs')
        for actual,summarized in zip(output['frames'],mode['frames']):
            for key in ('name','epoch','generation','bank','pixels','bytes','logical_reads','physical_reads','start_cycle','first_pixel_cycle','last_pixel_cycle','closed_cycle','start_to_first_pixel','start_to_last_pixel','start_to_closed','held_pixel_cycles','physical_ready_stalls','output'):
                need(actual[key]==summarized[key],'timed frame summary differs: '+key)
            need(actual['sha256']==summarized['output_sha256'],'timed RGB output hash differs')
            for key in ('state_cycles','adapter_state_cycles','reader_state_cycles','reader_pending_cycles','adapter_pending_cycles','controller_busy_cycles','bridge_pending_cycles'):
                need(actual[key]==summarized[key],'timed observer summary differs: '+key)
        output['t_ac_ns']=mode['t_ac_ns'];modes.append(output)
        mutations.extend(timed_negative_controls(trace,mode['seed'],images,tiles,forward,schedule,rgb))
        print('AUDITED_TIMED_BASE_RGB',mode['seed'],mode['t_ac_ns'],flush=True)
    need({(m['seed'],m['t_ac_ns']) for m in modes}=={(s,t) for s in (912701,912702) for t in (2,7)},'duplicate/missing timed modes')
    return dict(schema='cu66-v91l-timed-base-RGB-lines-audit-v1',status='PASS_INDEPENDENT_TIMED_BASE_RGB_FILES_AND_CONTROLLER_WORDS',
                selected_report=str(path.relative_to(ROOT)),report_sha256=sha(path),modes=modes,checker_negative_controls=mutations,
                independent_SDRAM_pin_timing_audit_required=True,
                histogram_scope='Pinned-source observations: each state histogram partitions the full frame fence; pending/busy categories overlap and are only bounded, never added as disjoint latency costs.',
                scope='Native base RGB565 through actual frozen converter, retained reader, BL8 bridge and controller. This audit checks line/burst/controller-word ownership, eight data beats and two idle-fence observations, complete RGB row/file goldens and timing arithmetic. Root separately checks SDRAM pin protocol/capture timing. Semantic HUD decode/overlay, shared live codec and physical hardware milestones remain unqualified.')


if __name__=='__main__':main()
