#!/usr/bin/env python3
"""Independent time-merged SDRAM pin/controller/BL8 audit for the timed RGB join."""
import collections
import gzip
import hashlib
import heapq
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
AREA=ROOT/'fpga/experiments/cu66-v91l-converter'
LIB=HERE/'verify_readbridge.py'
LIB_SHA='8fa8d4a666549a68174b6778b7c2fa93f52be53b5db0e86aaa1a7c1a6c91b590'
BASELINE='b96944dd9897e2bf4e9ed2978bdbade79cdccb7b'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def need(ok,why):
    if not ok:raise AssertionError(why)
need(sha(LIB)==LIB_SHA,'frozen readbridge oracle changed')
spec=importlib.util.spec_from_file_location('readbridge_pin_oracle',LIB)
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
ID=('bank','address','epoch','generation')
CPP_KINDS={'config','start','kill','controller_req','controller_read','controller_done','bridge_fence','phys_req','phys_rsp','frame','check','verdict'}
PIN_KINDS={'preload','pin','read'}


def checked_source(path,metadata,cpp):
    h=hashlib.sha256();rows=0;last_time=-1
    with gzip.open(path,'rb') as stream:
        for raw in stream:
            h.update(raw);rows+=1
            if not raw.startswith(b'{'):continue
            event=json.loads(raw)
            kind=event['type']
            if kind not in (CPP_KINDS if cpp else PIN_KINDS):
                if cpp:continue  # RGB/line/pixel receipts have a separate independent audit.
                raise AssertionError('unknown timed pin event '+kind)
            if cpp:
                if 'time_ps' in event:t=event['time_ps']
                elif 'cycle' in event:t=event['cycle']*10000+5000
                elif 'closed_cycle' in event:t=event['closed_cycle']*10000+5000
                elif kind=='verdict' and 'cycles' in event:t=event['cycles']*10000+5000
                elif kind=='config':t=0
                else:raise AssertionError('missing clock identity '+kind)
            else:
                need('time_ps' in event,'pin event missing simulation time');t=event['time_ps']
            need(t>=last_time,'source events reverse simulation time');last_time=t
            yield dict(event,time_ps=t)
    need(rows==metadata['rows'] and h.hexdigest()==metadata['raw_sha256'],'raw trace hash/row receipt differs')


def merged(pinpath,pinmeta,cpppath,cppmeta):
    # Both source streams are monotonic. Heap merge preserves each source's
    # order at equal timestamps, using one lookahead per source rather than sorting.
    sources=[checked_source(pinpath,pinmeta,False),checked_source(cpppath,cppmeta,True)]
    heap=[]
    for i,source in enumerate(sources):
        event=next(source,None)
        if event is not None:heapq.heappush(heap,(event['time_ps'],i,event))
    while heap:
        _time,index,event=heapq.heappop(heap);yield event
        item=next(sources[index],None)
        if item is not None:heapq.heappush(heap,(item['time_ps'],index,item))


def replay(stream,seed,tac,tiles,terminal=True):
    oracle=lib.PinOracle(tiles)
    controller=bridge=session=config=verdict=None
    counts=collections.Counter();checks=set();frames=[]
    last_time=-1;last_capture=None;fence_observations=0
    accepted_canceled_reads=0;unissued_cancellations=0;cancel_capture_histogram=collections.Counter()
    for event in stream:
        kind=event['type'];counts[kind]+=1;t=event['time_ps']
        need(t>=last_time,'merged time reversed');last_time=t
        if kind=='preload':
            need(counts[kind]==1 and controller is None and bridge is None,'preload during physical ownership')
            need('before_frame_fences' in event['scope'],'preload timing scope absent');oracle.preload()
        elif kind=='config':
            need(config is None,'duplicate config');config=event
            need(event['seed']==seed and event['retain']==1,'wrong static seed')
            need(event['service']=='ACTUAL_CONTROLLER_TIMED_SDRAM_PINS','logical actor substituted for physical controller')
        elif kind=='start':
            need(bridge is None and controller is None,'accepted start before physical drain')
            need(oracle.loaded and (session is None or not session['active']),'overlapping session')
            need(event['bank'] in (0,1) and event['image']==('actual_001','actual_006')[event['bank']],'preloaded bank/image identity differs')
            session=dict(event,active=True,requests=0,responses=0,commands=0,captures=0)
        elif kind=='phys_req':
            need(bridge is None and controller is None,'physical bridge owner overwritten')
            need(session is not None and session['active'],'physical request without active lease')
            need(all(event[k]==session[k] for k in ('bank','epoch','generation')),'physical request lease differs')
            need(event['address']%16==0 and event['address']<=518384,'physical alignment/range differs')
            bridge=dict(event,issued=False,words=[],capture_times=[],pin=None,done=None,killed=False,idles=0,last_fence=None,offered_at=None)
            session['requests']+=1
        elif kind=='controller_req':
            need(bridge is not None and not bridge['issued'] and not bridge['killed'] and controller is None,'controller acceptance without live physical owner')
            need(event['write']==0 and event['data']==0,'timed RGB lane unexpectedly writes')
            need(event['address']==(bridge['bank']<<22)|(bridge['address']>>1),'controller READ differs from accepted physical address')
            bridge['issued']=True;controller=dict(event,pin=None,words=[]);session['commands']+=1
        elif kind=='pin':
            oracle.command(event)
            if event['command'] in (4,5):
                need(event['command']==5 and controller is not None and controller['pin'] is None,'SDRAM column command lacks read owner')
                word=(event['bank']<<22)|(oracle.open_rows[event['bank']]<<9)|event['address']
                need(word==controller['address'],'pin READ address differs from accepted controller request')
                need(t>controller['time_ps'],'pin command precedes controller acceptance')
                controller['pin']=event;bridge['pin']=event
        elif kind=='read':
            oracle.read(event)
        elif kind=='controller_read':
            oracle.controller_read(event)
            need(controller is not None and controller['pin'] is not None and bridge is not None,'captured beat without read owner')
            need(len(controller['words'])<8,'more than eight captured words')
            controller['words'].append(event['data']);bridge['words'].append(event['data']);bridge['capture_times'].append(t);last_capture=t;session['captures']+=1
        elif kind=='controller_done':
            need(controller is not None and controller['pin'] is not None and bridge is not None,'controller drain without pin read')
            need(all(event[k]==controller[k] for k in ('write','address','data')),'controller drain identity differs')
            need(len(controller['words'])==8,'controller drain precedes eight captured words')
            need(t-controller['pin']['time_ps']>=131000,'controller drain precedes actual read recovery')
            bridge['done']=t;controller=None
        elif kind=='bridge_fence':
            need(bridge is not None and bridge['issued'] and len(bridge['words'])==8,'fence without eight captured words')
            need(event['beats']==8 and event['pending']==1,'fence lost physical ownership')
            need(event['ctrl_idle'] in (0,1),'invalid fence idle sample')
            if bridge['last_fence'] is not None:need(t-bridge['last_fence']==10000,'fence samples are not consecutive clocks')
            bridge['last_fence']=t;bridge['idles']=bridge['idles']+1 if event['ctrl_idle'] else 0
            if bridge['idles']==2:bridge['offered_at']=t+10000
            fence_observations+=1
        elif kind=='kill':
            need(event['reset'] or event['cancel'],'kill lacks asserted input')
            if session is not None:session['active']=False
            if bridge is not None and (bridge['offered_at'] is None or t<bridge['offered_at']):
                if not bridge['killed']:cancel_capture_histogram[sum(x<t for x in bridge['capture_times'])]+=1
                bridge['killed']=True
        elif kind=='phys_rsp':
            need(bridge is not None and all(event[k]==bridge[k] for k in ID),'tagged physical response differs from accepted owner')
            need(controller is None,'physical response precedes controller drain')
            expected_error=int(bridge['killed'])
            need(event['error']==expected_error,'physical response cancel/error status differs')
            if bridge['issued']:
                need(len(bridge['words'])==8 and bridge['done'] is not None,'accepted physical read did not capture and drain eight words')
                need(bridge['idles']>=2 and bridge['offered_at'] is not None and t>=bridge['offered_at'],'physical response precedes two consecutive idle fence observations')
                need(last_capture is not None and t-last_capture>=20000,'physical response precedes capture/data-release fence')
                if bridge['killed']:accepted_canceled_reads+=1
            else:
                need(bridge['killed'],'unissued physical success');unissued_cancellations+=1
            value=0 if expected_error else sum(v<<(16*i) for i,v in enumerate(bridge['words']))
            need(bytes.fromhex(event['data'])==value.to_bytes(16,'little'),'physical response bytes differ from gathered controller words')
            session['responses']+=1;bridge=None
        elif kind=='frame':
            need(bridge is None and controller is None and session is not None and session['active'],'full frame closes with active physical owner')
            need(all(event[k]==session[k] for k in ('bank','epoch','generation')) and event['name']==session['image'],'frame identity differs from preload lease')
            need(session['requests']==session['responses']==session['commands']==event['physical_reads']==32400,'full frame physical request/response count differs')
            need(session['captures']==32400*8,'full frame captured word count differs')
            frames.append(dict(name=event['name'],bank=event['bank'],epoch=event['epoch'],generation=event['generation'],physical_reads=session['commands'],captured_words=session['captures'],start_to_closed=event['start_to_closed']))
            session['active']=False
        elif kind=='check':
            need(event['status']=='PASS' and event['name'] not in checks,'failed/duplicate directed check');checks.add(event['name'])
        elif kind=='verdict':
            need(verdict is None,'duplicate verdict');verdict={k:v for k,v in event.items() if k!='time_ps'}
        else:raise AssertionError('unknown merged event '+kind)
    if terminal:
        need(config is not None and verdict is not None,'missing config/verdict')
        need(verdict['status']=='TEST_PASS' and verdict['seed']==seed and verdict['retain']==1,'bad verdict')
        need(bridge is None and controller is None and not oracle.reads and not oracle.controller_reads,'terminal physical work remains owned')
        need(len(frames)==2 and {f['bank'] for f in frames}=={0,1},'missing full native frame')
        need(verdict['checks']==len(checks),'directed check count differs')
        need(accepted_canceled_reads>=2 and unissued_cancellations>=2,'accepted and unissued cancellation coverage missing')
        need(cancel_capture_histogram[3]>=2,'cancel and reset after three captured beats were not exercised')
    return dict(seed=seed,t_ac_ns=tac,event_counts=dict(counts),checks=sorted(checks),frames=frames,
                accepted_canceled_reads=accepted_canceled_reads,unissued_cancellations=unissued_cancellations,completed_capture_edges_before_kill_histogram=dict(cancel_capture_histogram),
                fence_observations=fence_observations,command_counts={str(k):v for k,v in oracle.counts.items()},
                verdict=verdict,scope='Physical pin/controller/bridge cross-check only; RGB line/pixel correctness is independently audited separately.')


def provenance(path):
    report=json.loads(path.read_text());attempt=path.parent
    need(report['status']=='PASS_NATIVE_RGB565_ACTUAL_TIMED_SDRAM' and report['schema']=='cu66-v91l-timed-rgb-converter-v1','selected timed campaign is not passing')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for a,b in ((BASELINE,report['source_revision']),(report['source_revision'],head)):
        need(subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT,capture_output=True).returncode==0,'source ancestry differs')
    for name,h in report['source_sha256'].items():need(sha(ROOT/name)==sha(attempt/'sources'/name)==h,'source snapshot differs: '+name)
    for name,h in report['inputs_sha256'].items():need(sha(ROOT/name)==sha(attempt/'inputs'/Path(name).name)==h,'input snapshot differs: '+name)
    for name,h in report['artifacts_sha256'].items():need(sha(attempt/name)==h,'retained artifact differs: '+name)
    need(all(c['exit_code']==0 for c in report['commands']),'failed timed command')
    for source in ('fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv','fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv','fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv'):
        need(sha(ROOT/source)==hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+source],cwd=ROOT)).hexdigest(),'frozen source changed: '+source)
    need('5.020' in (attempt/'tool-version.log').read_text() and '13.3.0' in (attempt/'compiler-version.log').read_text(),'tool versions differ')
    builds=[c['argv'] for c in report['commands'] if '--build' in c['argv']]
    build_directories={}
    need(len(builds)==len(report['t_ac_ns']),'missing timed corner build')
    for argv in builds:
        need({'--timing','--assert','-Wall','-DSIMULATION','--cc','--exe','--build'}<=set(argv),'weak timed build flags')
        need(not any(str(a).startswith('-Wno-') for a in argv),'design warnings waived')
        need({'-std=c++20','-Wall','-Wextra','-Werror'}<=set(argv[argv.index('-CFLAGS')+1].split()),'weak C++ flags')
        need("-GRETAIN_ROWS=1'b1" in argv,'wrong static retention mode')
        tac=float(next(v.split('=')[1] for v in argv if v.startswith('-GT_AC_NS=')))
        need(tac not in build_directories,'duplicate corner build')
        build_directories[tac]=argv[argv.index('--Mdir')+1]
        for source in report['source_sha256']:
            if source.endswith(('.sv','.cpp')):need(str(attempt/'sources'/source) in argv,'compiled source absent from exact snapshot')
    need(set(build_directories)==set(report['t_ac_ns']),'compiled timing corner set differs')
    runs=[c['argv'] for c in report['commands'] if any(str(v).endswith('/Vcanonical_rgb565_timed') for v in c['argv'])]
    need(len(runs)==len(report['modes']),'missing mode executions')
    for mode in report['modes']:
        expected_binary=build_directories[mode['t_ac_ns']]+'/Vcanonical_rgb565_timed'
        expected_event=str(attempt/mode['event_log'].removesuffix('.gz'))
        matching=[a for a in runs if expected_binary in a and expected_event in a and str(mode['seed']) in a]
        need(len(matching)==1,'mode not bound to exact compiled corner and event path')
    need(report['actual_converter_rtl_join'] and report['physical_sdram_controller_join'],'actual timed join absent')
    for key in ('shared_service_complete','physical_hardware_tested','sustained_hardware_30fps_proven','validated_full_frame_decode_under10ms_proven'):need(report[key] is False,'unsupported scope claim '+key)
    return report


def negative_controls(events,seed,tac,tiles):
    prefix=[]
    for e in events:
        prefix.append(e)
        if len(prefix)>=12000:break
    def first(kind,predicate=lambda e:True):return next(i for i,e in enumerate(prefix) if e['type']==kind and predicate(e))
    pin=first('pin',lambda e:e['command']==5)
    read=first('read');capture=first('controller_read')
    fence=first('bridge_fence');response=first('phys_rsp',lambda e:e['error']==0)
    controls=(
        ('corrupt_pin_address',pin,'address',prefix[pin]['address']^8,'pin READ address differs'),
        ('corrupt_scheduled_read_data',read,'data',prefix[read]['data']^1,'SDR BL8 beat differs'),
        ('corrupt_captured_read_data',capture,'data',prefix[capture]['data']^1,'capture/retime/consume data mismatch'),
        ('corrupt_captured_read_time',capture,'time_ps',prefix[capture]['time_ps']+1,'capture/retime/consume timing mismatch'),
        ('remove_idle_fence_observation',fence,'ctrl_idle',0,'physical response precedes two consecutive idle'),
        ('corrupt_response_generation',response,'generation',prefix[response]['generation']^1,'tagged physical response differs'),
        ('corrupt_response_payload',response,'data',f"{int(prefix[response]['data'][:2],16)^1:02x}"+prefix[response]['data'][2:],'physical response bytes differ'),
    )
    rejected=[]
    for name,index,field,value,cause in controls:
        def mutate():
            for i,e in enumerate(prefix):yield {**e,field:value} if i==index else e
        try:replay(mutate(),seed,tac,tiles,terminal=False)
        except AssertionError as error:
            need(cause in str(error),'negative control rejected for unrelated cause: '+name+': '+str(error))
            rejected.append(dict(mutation=name,seed=seed,t_ac_ns=tac,rejected=True,reason=str(error)))
        else:raise AssertionError('checker accepted corrupted receipt '+name)
    return rejected


def main():
    alias=json.loads((AREA/'timed-results.json').read_text());path=ROOT/alias['selected_report']
    report=provenance(path);report_digest=sha(path)
    need({k:v for k,v in alias.items() if k!='selected_report'}==report,'selected alias differs')
    _metadata,_frames,tiles,_forward,_schedule=lib.fixture_check()
    modes=[];controls=[]
    for mode in report['modes']:
        pinmeta=report['compressed_artifacts'][mode['pin_log'].removesuffix('.gz')]
        cppmeta=report['compressed_artifacts'][mode['event_log'].removesuffix('.gz')]
        pinpath=path.parent/pinmeta['path'];cpppath=path.parent/cppmeta['path']
        need(sha(pinpath)==pinmeta['gzip_sha256'] and sha(cpppath)==cppmeta['gzip_sha256'],'compressed trace digest differs')
        result=replay(merged(pinpath,pinmeta,cpppath,cppmeta),mode['seed'],mode['t_ac_ns'],tiles)
        need(result['verdict']==mode['verdict'],'runner verdict differs from pin replay')
        need(result['checks']==sorted(mode['checks']),'directed check list differs')
        need(len(result['frames'])==len(mode['frames']),'frame summary count differs')
        for actual,summary in zip(result['frames'],mode['frames']):
            for field in ('name','bank','epoch','generation','physical_reads','start_to_closed'):
                need(actual[field]==summary[field],'runner frame summary differs: '+field)
        controls.extend(negative_controls(merged(pinpath,pinmeta,cpppath,cppmeta),mode['seed'],mode['t_ac_ns'],tiles))
        modes.append(result);print('AUDITED_TIMED_PINS',mode['seed'],mode['t_ac_ns'],flush=True)
    # Recheck freshness after the long streaming audit, not only at entry.
    for name,h in report['source_sha256'].items():need(sha(ROOT/name)==h,'source changed during audit: '+name)
    need(sha(path)==report_digest,'selected report changed during audit')
    need(sha(LIB)==LIB_SHA,'helper changed during audit')
    need(json.loads((AREA/'timed-results.json').read_text())==alias,'selected alias changed during audit')
    expected={(s,t) for s in report['seeds'] for t in report['t_ac_ns']}
    need(len(modes)==len(expected) and {(m['seed'],m['t_ac_ns']) for m in modes}==expected,'missing/duplicate timed modes')
    need(set(report['seeds'])=={912701,912702} and set(report['t_ac_ns'])=={2,7},'full timed qualification requires both seeds/corners')
    result=dict(schema='cu66-v91l-combined-timed-pin-audit-v1',status='PASS_INDEPENDENT_TIME_MERGED_RGB_SDRAM_PIN_AUDIT',
                selected_report=str(path.relative_to(ROOT)),report_sha256=sha(path),verifier_sha256=sha(Path(__file__)),
                helper_sha256=LIB_SHA,modes=modes,checker_negative_controls=controls,
                assertions=dict(exact_pinned_sources_inputs_and_artifacts=True,two_sorted_sources_heap_merged_by_simulation_time=True,
                                all_pin_commands_and_data_against_independent_memory=True,all_captured_words_and_timestamps_exact=True,
                                every_read_eight_words_drain_and_two_idle_observations=True,all_tagged_responses_exact=True,
                                accepted_and_unissued_cancel_reset_coverage=True,hardware_or_full_decoder_proven=False),
                scope='Combined actual retained RGB conversion through tagged BL8 bridge, frozen SDRAM controller and timed functional pin model. Native data is preloaded before all fences. This audit checks pins/physical ownership only; no live codec/publication, shared writer/traffic, electrical PVT/route timing or hardware qualification.')
    (HERE/'audit-timed-pins.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
