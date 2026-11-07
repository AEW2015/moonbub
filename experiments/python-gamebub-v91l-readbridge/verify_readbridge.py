#!/usr/bin/env python3
"""Independent preloaded SDRAM pin, BL8 ownership, beat and logical-output audit."""
from array import array
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v91l-readbridge'
OUT=Path(__file__).with_name('audit-readbridge.json')
BASELINE='b96944dd9897e2bf4e9ed2978bdbade79cdccb7b'
LIB=ROOT/'experiments/python-gamebub-v91l-writepipe/verify_results.py'
LIB_SHA='0a2d293add938e48f2a726481a90e197fb53b5bce293c5800212b027bfda3004'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def need(ok,why):
    if not ok:raise AssertionError(why)
need(sha(LIB)==LIB_SHA,'frozen pin library changed')
spec=importlib.util.spec_from_file_location('frozen_pin_oracle',LIB)
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
trace_events=parent.trace_events
CANONICAL=ROOT/'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz'
VECTOR=ROOT/'experiments/python-gamebub-v91l-tiled/vectors/prefill-lines.hex.gz'


def images():
    frames={}
    with gzip.open(CANONICAL,'rt') as stream:
        for line in stream:
            name,profile,hx=line.rstrip().split('\t')
            if profile=='0' and name in ('actual_001','actual_006'):frames[name]=bytes.fromhex(hx)
    need(set(frames)=={'actual_001','actual_006'},'missing source images')
    forward=array('I',[0])*518400
    for base,width,height in ((0,720,480),(345600,360,240),(432000,360,240)):
        address=base
        for ty in range(0,height,8):
            for tx in range(0,width,8):
                for y in range(8):
                    for x in range(8):
                        forward[base+(ty+y)*width+tx+x]=address;address+=1
        need(address==base+width*height,'plane geometry differs')
    need(len(set(forward))==518400,'tile alias')
    tiles={}
    for name,data in frames.items():
        physical=bytearray(518400)
        for logical,value in enumerate(data):physical[forward[logical]]=value
        tiles[name]=bytes(physical)
    return frames,tiles,forward


def fixture_check():
    metadata=json.loads((AREA/'fixtures.json').read_text())
    need(metadata['generator_sha256']==sha(AREA/'generate_fixtures.py'),'fixture generator changed')
    for name,h in metadata['inputs'].items():need(sha(ROOT/name)==h,'fixture source changed')
    frames,tiles,forward=images()
    schedule=[int(v,16) for v in gzip.decompress(VECTOR.read_bytes()).splitlines()]
    need(len(schedule)==len(set(schedule))==32400,'line vector extent')
    for name,receipt in metadata['artifacts'].items():
        packed=AREA/name;raw=gzip.decompress(packed.read_bytes())
        need(sha(packed)==receipt['gzip_sha256'],'fixture packed digest')
        need(hashlib.sha256(raw).hexdigest()==receipt['raw_sha256'] and len(raw.splitlines())==receipt['rows'],'fixture raw digest')
    words=iter(gzip.decompress((AREA/'preload.hex.gz').read_bytes()).splitlines())
    for bank,name in enumerate(('actual_001','actual_006')):
        need(next(words)==f'@{bank<<22:06x}'.encode(),'wrong preload bank address')
        for start in range(0,518400,2):
            need(int(next(words),16)==int.from_bytes(tiles[name][start:start+2],'little'),'preload word differs from tile golden')
    need(next(words,None) is None,'extra preload data')
    rows=iter(gzip.decompress((AREA/'native-lines.hex.gz').read_bytes()).splitlines())
    for bank,name in enumerate(('actual_001','actual_006')):
        for address in schedule:
            n=int(next(rows),16)
            need(n>>149==0 and (n>>147)&3==bank and (n>>128)&((1<<19)-1)==address,'logical fixture identity differs')
            need((n&((1<<128)-1)).to_bytes(16,'little')==frames[name][address:address+16],'logical fixture bytes differ')
    need(next(rows,None) is None,'extra logical fixture data')
    return metadata,frames,tiles,forward,schedule


class PinOracle(parent.PinOracle):
    def __init__(self,tiles):
        super().__init__();self.tiles=tiles;self.loaded=False
    def preload(self):
        need(not self.reads and not self.controller_reads,'preload over a pending read')
        self.loaded=True
        self.memory={a:v for a,v in self.memory.items() if (a>>22)>1 or (a&((1<<22)-1))>=259200}
    def value(self,address):
        if address in self.memory:return self.memory[address]
        bank=address>>22;offset=(address&((1<<22)-1))*2
        if self.loaded and bank in (0,1) and offset<518400:
            data=self.tiles[('actual_001','actual_006')[bank]]
            return int.from_bytes(data[offset:offset+2],'little')
        return (address&65535)^0x5a3c


def provenance(path):
    report=json.loads(path.read_text());attempt=path.parent
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for a,b in ((BASELINE,report['source_revision']),(report['source_revision'],head)):
        need(subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT,capture_output=True).returncode==0,'source ancestry differs')
    for name,h in report['source_sha256'].items():need(sha(ROOT/name)==sha(attempt/'sources'/name)==h,'source/snapshot differs: '+name)
    for name,h in report['artifacts_sha256'].items():need(sha(attempt/name)==h,'artifact differs: '+name)
    for name,h in report['inputs_sha256'].items():need(sha(ROOT/name)==sha(attempt/'inputs'/Path(name).name)==h,'input differs: '+name)
    need(all(c['exit_code']==0 for c in report['commands']),'failed command')
    frozen=['fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv','fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv','fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv']
    for name in frozen:
        need(sha(ROOT/name)==hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)).hexdigest(),'frozen design changed')
    for argv in (c['argv'] for c in report['commands'] if '--binary' in c['argv']):
        need({'--timing','--assert','-Wall','-DSIMULATION'}<=set(argv),'weak RTL flags')
        need(not any(str(v).startswith('-Wno-') for v in argv),'warning waived')
        need({'-std=c++20','-Wall','-Wextra','-Werror'}<=set(argv[argv.index('-CFLAGS')+1].split()),'weak C++ flags')
    return report

GATHER_LIB=ROOT/'experiments/python-gamebub-v91l-tiled/verify_rowpair.py'
GATHER_SHA='8e40414864dbe0a28d2e522b51fa65ac20e8ca8aabc14fe5c17dd306cfcf7454'
need(sha(GATHER_LIB)==GATHER_SHA,'frozen gather oracle changed')
spec=importlib.util.spec_from_file_location('frozen_gather_oracle',GATHER_LIB)
gatherlib=importlib.util.module_from_spec(spec);spec.loader.exec_module(gatherlib)
ID=('bank','address','epoch','generation')


def replay(stream,seed,retain,tac,frames,tiles,forward,schedule):
    oracle=PinOracle(tiles)
    controller=bridge=logical=frame=None
    checks=set();verdict=config=None
    counts=collections.Counter();fences=[];native=[]
    last_time=-1;held=0;captured=0;last_done=None
    reader_totals=collections.Counter()
    for e in stream:
        kind=e['type'];counts[kind]+=1
        if 'time_ps' in e:
            need(e['time_ps']>=last_time,'events reordered');last_time=e['time_ps']
        if kind=='config':
            need(config is None,'duplicate config');config=e
            need(e['seed']==seed and e['retain']==retain and e['t_ac_ns']==tac,'mode label differs')
            need(e['clock_flight_ns']==4 and e['read_phase_ns']==7.75 and e['bridge_idle_fence_cycles']==2,'timing contract differs')
        elif kind=='controller_req':
            need(controller is None,'controller owner overlap')
            if bridge is not None:
                need(bridge['valid'] and not bridge['killed'] and bridge['issued']==0,'command for invalid/canceled/issued bridge owner')
                need(e['write']==0 and e['address']==(bridge['bank']<<22)|(bridge['address']>>1),'controller read address differs')
                bridge['issued']=1
            controller=dict(e,pin=None,words=[],bridge=bridge)
        elif kind=='pin':
            oracle.command(e)
            if e['command'] in (4,5):
                need(controller is not None and controller['pin'] is None,'column command without unique controller owner')
                word=(e['bank']<<22)|(oracle.open_rows[e['bank']]<<9)|e['address']
                need(word==controller['address'] and (e['command']==4)==bool(controller['write']),'pin/controller identity differs')
                if controller['write']:need(e['dq']==controller['data'],'write DQ differs')
                controller['pin']=e
        elif kind=='read':oracle.read(e)
        elif kind=='controller_read':
            oracle.controller_read(e)
            need(controller is not None and not controller['write'] and controller['pin'] is not None,'capture without read owner')
            need(len(controller['words'])<8,'excess captured beats');controller['words'].append(e['data'])
            if controller['bridge'] is not None:
                bridge['words'].append(e['data']);bridge['last_capture']=e['time_ps'];captured+=1
        elif kind=='controller_done':
            need(controller is not None and controller['pin'] is not None,'drain without actual command')
            need(all(e[k]==controller[k] for k in ('write','address','data')),'controller drain identity differs')
            need(controller['write'] or len(controller['words'])==8,'controller drained before eight words')
            minimum=41000 if controller['write'] else 131000
            need(e['time_ps']-controller['pin']['time_ps']>=minimum,'controller drain before recovery')
            if controller['bridge'] is not None:
                bridge['done']=e['time_ps']
            last_done=e;controller=None
        elif kind=='bridge_req':
            need(bridge is None and controller is None,'bridge lease overwrite')
            valid=e['bank']<3 and e['epoch']!=0 and e['generation']!=0 and e['address']%16==0 and e['address']<=518384
            counts['invalid_inputs']+=not valid
            bridge=dict(e,valid=valid,killed=False,issued=0,words=[],offered=None,done=None,idles=0)
            if frame is not None:
                need(logical is not None,'native physical request without logical owner')
                i=logical['issued']
                need(i<len(logical['actions']) and e['address']==logical['actions'][i],'physical gather request differs from independent retention actions')
                need(all(e[k]==logical[k] for k in ('bank','epoch','generation')),'physical lease differs')
                logical['issued']+=1;frame['physical']+=1
        elif kind=='bridge_fence':
            need(bridge is not None and bridge['issued']==1 and len(bridge['words'])==8,'fence without complete accepted BL8')
            need(e.get('beats',e.get('beat_count'))==8 and e['pending']==1,'fence metadata differs')
            idle=e.get('idle',e.get('ctrl_idle'))
            need(idle in (0,1),'fence idle missing')
            bridge['idles']=bridge['idles']+1 if idle else 0
            fences.append((e['cycle'],idle))
        elif kind=='kill':
            need(e['reset'] or e['cancel'],'kill without asserted input')
            if e['state'] not in (0,4):counts['kill_active_edges']+=1
            if bridge is not None and bridge['offered'] is None:bridge['killed']=True
        elif kind in ('bridge_offer','bridge_rsp'):
            need(bridge is not None and all(e[k]==bridge[k] for k in ID),'bridge response identity differs')
            need(controller is None,'bridge ACK before controller drain')
            payload=tuple(e[k] for k in (*ID,'error','data'))
            if bridge['offered'] is None:
                expected_error=int(not bridge['valid'] or bridge['killed'])
                need(e['error']==expected_error,'bridge response error differs')
                if bridge['issued']:
                    need(len(bridge['words'])==8 and bridge['done'] is not None,'accepted read lost beats/drain')
                    need(bridge['idles']>=2,'response before two consecutive idle fence observations')
                    need(e['time_ps']-bridge['last_capture']>=20000,'response before read-data release fence')
                else:need(e['error']==1,'success without controller issue')
                expected=0 if e['error'] else sum(v<<(16*i) for i,v in enumerate(bridge['words']))
                need(int(e['data'],16)==expected,'bridge gathered data differs from controller words')
                bridge['offered']=payload
            need(payload==bridge['offered'],'held bridge response changed')
            if kind=='bridge_offer':held+=not e['ready']
            else:bridge=None
        elif kind=='preload':
            need(controller is None and bridge is None and logical is None,'preload over pending ownership')
            need('outside_fences' in e['scope'],'preload scope absent');oracle.preload()
        elif kind=='frame_begin':
            need(oracle.loaded and frame is None and bridge is None and controller is None,'frame starts without clean preload/drain')
            bank=e['bank'];name=('actual_001','actual_006')[bank]
            frame=dict(e,name=name,requests=0,responses=0,physical=0,row_hits=0,scratch_hits=0,output=bytearray(518400),
                       gather=gatherlib.GatherOracle(retain,tiles[name],forward),acts_before=oracle.counts[3],refs_before=oracle.counts[1])
        elif kind=='reader_req':
            need(frame is not None and logical is None and bridge is None,'logical reader ownership overwrite')
            i=frame['requests'];need(i<32400 and e['address']==schedule[i] and e['bank']==frame['bank'],'native logical schedule differs')
            actions,rh,sh=frame['gather'].request(e['address'])
            logical=dict(e,actions=actions,issued=0);frame['requests']+=1;frame['row_hits']+=rh;frame['scratch_hits']+=sh
        elif kind=='reader_rsp':
            need(logical is not None and bridge is None and controller is None,'reader response without drained owner')
            need(all(e[k]==logical[k] for k in (*ID,'token')) and e['error']==0,'reader response identity/error differs')
            need(logical['issued']==len(logical['actions']),'reader omitted physical action')
            data=int(e['data'],16).to_bytes(16,'little');a=e['address']
            need(data==frames[frame['name']][a:a+16],'native canonical response differs')
            frame['output'][a:a+16]=data;frame['responses']+=1;logical=None
        elif kind=='frame_end':
            need(frame is not None and logical is None and bridge is None and controller is None,'frame ended before drain')
            need(frame['requests']==frame['responses']==32400 and frame['physical']==(32400 if retain else 64800),'native frame counts differ')
            need(bytes(frame['output'])==frames[frame['name']],'complete native bank differs')
            for key,actual in (('reader_requests',32400),('reader_responses',32400),('physical_requests',frame['physical']),('physical_responses',frame['physical']),('row_hits',frame['row_hits']),('scratch_hits',frame['scratch_hits']+frame['physical'])):
                reader_totals[key]+=actual;need(e[key]==reader_totals[key],'cumulative reader count differs: '+key)
            need(e['valid_fragments']==(180 if retain else 0),'final fragment validity differs')
            cycles=e['cycle']-frame['cycle'];time=e['time_ps']-frame['time_ps']
            need(time==cycles*10000,'frame time differs from nominal clock')
            native.append(dict(bank=e['bank'],name=frame['name'],cycles=cycles,modeled_ms_at100mhz=cycles/100000,
                               requests=32400,physical_reads=frame['physical'],activate_commands=oracle.counts[3]-frame['acts_before'],
                               refresh_commands=oracle.counts[1]-frame['refs_before'],sha256=hashlib.sha256(frame['output']).hexdigest(),
                               fence='After accepted reader start / before first logical offer to after final logical response ACK.'))
            frame=None
        elif kind=='check':
            need(e['status']=='PASS' and e['name'].strip() not in checks,'duplicate/failed check');checks.add(e['name'].strip())
        elif kind=='verdict':need(verdict is None,'duplicate verdict');verdict=e
        else:raise AssertionError('unknown event '+kind)
    need(config is not None and verdict is not None and verdict['status']=='TEST_PASS','no explicit terminal pass')
    need(controller is None and bridge is None and logical is None and frame is None,'undrained terminal owner')
    need(not oracle.reads and not oracle.controller_reads,'unreturned physical/captured read beats')
    need(held>=5,'response backpressure not exercised')
    for name,value in (('checks',len(checks)),('requests',counts['bridge_req']),('responses',counts['bridge_rsp']),('commands',counts['controller_req']-oracle.counts[4]-1),('beats',captured),('invalid',counts['invalid_inputs']),('cancels',counts['kill_active_edges']),('writes',oracle.counts[4]),('read_words',oracle.counts['read_beats']),('refreshes',oracle.counts[1]),('activates',oracle.counts[3]),('precharges',oracle.counts[2])):
        need(verdict[name]==value,'verdict differs from replay: '+name)
    need(oracle.counts[5]*8==oracle.counts['read_beats']==oracle.counts['controller_read_beats'],'read word counts differ')
    return dict(seed=seed,retain=retain,t_ac_ns=tac,checks=sorted(checks),verdict=verdict,native_frames=native,
                event_counts=dict(counts),pin_counts={str(k):v for k,v in oracle.counts.items()},held_cycles=held,
                consecutive_idle_fence_observations=len(fences))


def negative_controls(trace,seed,retain,tac,frames,tiles,forward,schedule):
    events=list(trace_events(trace))
    first_success=next(i for i,e in enumerate(events) if e['type']=='bridge_offer' and e['error']==0)
    final_fence=max(i for i,e in enumerate(events[:first_success]) if e['type']=='bridge_fence')
    seen=set();held=None
    for i,e in enumerate(events):
        if e['type']=='bridge_offer':
            key=tuple(e[k] for k in ID)
            if key in seen and e['ready']==0:held=i;break
            seen.add(key)
    need(held is not None,'no held response control')
    def index(kind,predicate=lambda e:True):return next(i for i,e in enumerate(events) if e['type']==kind and predicate(e))
    controls=[('scheduled_read_data',index('read'),'data',None,'SDR BL8 beat differs'),
              ('captured_read_data',index('controller_read'),'data',None,'capture/retime/consume data mismatch'),
              ('response_epoch',first_success,'epoch',None,'bridge response identity differs'),
              ('gathered_words',first_success,'data',None,'bridge gathered data differs'),
              ('controller_drain_address',index('controller_done'),'address',None,'controller drain identity differs'),
              ('missing_second_idle',final_fence,'ctrl_idle',0,'two consecutive idle'),
              ('held_error_changes',held,'error',None,'held bridge response changed'),
              ('accepted_read_address',index('controller_req',lambda e:e['write']==0),'address',None,'controller read address differs')]
    rejected=[]
    for name,i,key,value,reason in controls:
        old=events[i][key]
        if value is None:value=format(int(old,16)^1,'032x') if key=='data' and isinstance(old,str) else old^1
        def changed():
            for j,e in enumerate(events):yield {**e,key:value} if j==i else e
        try:replay(changed(),seed,retain,tac,frames,tiles,forward,schedule)
        except AssertionError as error:
            need(reason in str(error),'negative failed for unrelated reason '+name+': '+str(error))
            rejected.append(dict(mutation=name,rejected=True,seed=seed,retain=retain,reason=str(error)))
        else:raise AssertionError('accepted corrupted trace '+name)
    return rejected


def main():
    metadata,frames,tiles,forward,schedule=fixture_check()
    alias=json.loads((AREA/'comparison-results.json').read_text())
    path=ROOT/alias['selected_report'];report=provenance(path)
    need(report['status']=='PASS_TIMED_BL8_BRIDGE_AND_NATIVE_RETENTION_COMPARISON' and report['native_replay'],'nonpassing/native campaign')
    need({k:v for k,v in alias.items() if k!='selected_report'}==report,'alias differs')
    for key in ('physical_hardware_tested','full_live_codec_join','actual_converter_rtl_join','shared_service_complete','sustained_hardware_30fps_proven','validated_full_frame_under10ms_proven'):
        need(report[key] is False,'unsupported scope claim')
    modes=[];mutations=[]
    for mode in report['modes']:
        meta=report['compressed_artifacts'][mode['event_log'].removesuffix('.gz')]
        trace={**meta,'path':path.parent/meta['path']}
        need(sha(trace['path'])==trace['gzip_sha256'],'trace packed digest differs')
        checked=replay(trace_events(trace),mode['seed'],mode['retain'],mode['t_ac_ns'],frames,tiles,forward,schedule)
        need(checked['verdict']==mode['verdict'],'verdict summary differs')
        need(checked['checks']==sorted(v.strip() for v in mode['checks']),'check list differs')
        need(len(checked['native_frames'])==len(mode['frames'])==(2 if mode['native_replay'] else 0),'native frame scope differs')
        for a,b in zip(checked['native_frames'],mode['frames']):
            need(a['bank']==b['bank'] and a['cycles']==b['cycles'],'native fence differs')
        if mode['t_ac_ns']==7:
            mutations.extend(negative_controls(trace,mode['seed'],mode['retain'],mode['t_ac_ns'],frames,tiles,forward,schedule))
        modes.append(checked)
        print('AUDITED_READBRIDGE',mode['retain'],mode['seed'],mode['t_ac_ns'],flush=True)
    need(len(modes)==8 and {(m['retain'],m['seed'],m['t_ac_ns']) for m in modes}=={(r,s,t) for r in (0,1) for s in (912601,912602) for t in (2,7)},'matrix differs')
    need(len(mutations)==32,'missing corrupted controls')
    comparisons=[]
    for seed in (912601,912602):
        before=next(m for m in modes if m['retain']==0 and m['seed']==seed and m['t_ac_ns']==2)
        after=next(m for m in modes if m['retain']==1 and m['seed']==seed and m['t_ac_ns']==2)
        for a,b in zip(before['native_frames'],after['native_frames']):
            need(a['sha256']==b['sha256'] and b['physical_reads']*2==a['physical_reads'],'matched native data/read count differs')
            comparisons.append(dict(seed=seed,bank=b['bank'],independent_cycles=a['cycles'],retained_cycles=b['cycles'],cycle_reduction_percent=(a['cycles']-b['cycles'])/a['cycles']*100,canonical_sha256=b['sha256']))
    for a,b in zip(comparisons,report['comparisons']):
        need(all(a[k]==b[k] for k in ('seed','bank','independent_cycles','retained_cycles','cycle_reduction_percent')),'runner comparison differs')
    result=dict(schema='cu66-v91l-readbridge-independent-audit-v1',status='PASS_TIMED_READBRIDGE_PIN_CAPTURE_FENCE_AND_NATIVE_OUTPUT_AUDIT',
                selected_report=str(path.relative_to(ROOT)),report_sha256=sha(path),verifier_sha256=sha(Path(__file__)),
                frozen_pin_library_sha256=LIB_SHA,frozen_gather_library_sha256=GATHER_SHA,
                fixture_sha256=sha(AREA/'fixtures.json'),modes=modes,comparisons=comparisons,checker_negative_controls=mutations,
                assertions=dict(eight_captured_words_per_read=True,physical_pin_words_and_capture_timestamps_exact=True,
                                two_consecutive_idle_fence_observations_before_ack=True,held_success_and_error_immutable=True,
                                cancel_drains_accepted_read=True,source_backed_native_inverse_outputs_exact=True,
                                model_preload_outside_fences=True,actual_converter_join=False,shared_controller_qualified=False,
                                hardware_or_full_decode_latency_qualified=False))
    OUT.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])


if __name__=='__main__':main()
