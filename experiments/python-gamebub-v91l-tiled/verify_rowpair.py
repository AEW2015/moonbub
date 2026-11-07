#!/usr/bin/env python3
"""Independent logical/physical ownership and tile-byte replay for row retention RTL."""
from __future__ import annotations
import collections
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v91l-rowpair'
HERE = Path(__file__).resolve().parent
BASELINE = '438dbb2e8d5ccfa2fa38ad34706dc3c2fd904080'
CANONICAL = ROOT / 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz'
VECTOR = HERE / 'vectors/prefill-lines.hex.gz'
PLANES = ((0,720,480),(345600,360,240),(432000,360,240))
IDENTITY = ('address','bank','epoch','generation','token')
PHYSICAL = ('address','bank','epoch','generation')
REQUIRED_CHECKS = {
    'finish_has_priority_over_simultaneous_request',
    'zero_epoch_generation_reserved_bank_start_rejected',
    'order_alignment_extent_and_lease_reject_without_physical_work',
    'cancel_after_physical_accept', 'cancel_before_physical_accept',
    'reset_after_physical_accept', 'reset_before_physical_accept',
    'cancel_held_error', 'cancel_held_success', 'reset_held_error', 'reset_held_success',
    'wrong_generation_response_rejected_then_matching_response_drained',
    'physical_error_invalidates_rows_and_retires_owner',
    'same_bank_changed_generation_and_content_cannot_hit_stale_rows',
    'independent_plane_cursors_and_bank_switch',
    'derived_prefill_full_canonical_actual_001', 'derived_prefill_full_canonical_actual_006',
}


def need(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_images():
    images = {}
    with gzip.open(CANONICAL, 'rt') as stream:
        for line in stream:
            name, profile, data = line.rstrip().split('\t')
            if name in ('actual_001','actual_006') and profile == '0':
                need(name not in images, 'duplicate canonical golden')
                images[name] = bytes.fromhex(data)
    need(set(images) == {'actual_001','actual_006'}, 'missing canonical images')
    tiles, inverse = {}, [None] * 518400
    # Geometry traversal avoids sharing the DUT's arithmetic mapper.
    for name, canonical in images.items():
        need(len(canonical) == 518400, 'bad canonical extent')
        output = bytearray(518400)
        for base,width,height in PLANES:
            physical = base
            for ty in range(0,height,8):
                for tx in range(0,width,8):
                    for y in range(8):
                        for x in range(8):
                            logical = base+(ty+y)*width+tx+x
                            output[physical] = canonical[logical]
                            if name == 'actual_001':
                                inverse[physical] = logical
                            physical += 1
            need(physical == base+width*height, 'tile extent differs')
        tiles[name] = bytes(output)
    need(len(set(inverse)) == 518400, 'non-bijective independent tile geometry')
    forward = [0] * 518400
    for physical,logical in enumerate(inverse):
        forward[logical] = physical
    return images,tiles,forward


def derived_schedule():
    # Direct line intervals at each source-defined prefill trigger; no model import.
    out, tags = [], [None,None,None]
    def row(plane, y):
        base,width,_ = PLANES[plane]
        low = (base+y*width) & ~15
        high = (base+(y+1)*width-1) & ~15
        for address in range(low,high+1,16):
            if address != tags[plane]:
                out.append(address)
                tags[plane] = address
    for y in range(480):
        if y == 0:
            for r in (0,1):
                row(1,r);row(2,r)
        elif y % 2 == 0 and y <= 476:
            r = y//2+1
            row(1,r);row(2,r)
        row(0,y)
    with gzip.open(VECTOR,'rt') as stream:
        fixture = [int(line,16) for line in stream]
    need(out == fixture and len(out) == len(set(out)) == 32400, 'source-derived schedule differs')
    need(set(out) == set(range(0,518400,16)), 'derived schedule misses canonical lines')
    return out


class GatherOracle:
    def __init__(self, retain, tiles, forward):
        self.retain,self.tiles,self.forward = retain,tiles,forward
        self.fragments = [{},{},{}]
        self.row = [None,None,None]
        self.scratch = None

    def request(self,address):
        actions=[]
        row_hits=scratch_hits=0
        if not self.retain:
            self.scratch=None
        for logical in (address,address+8):
            plane=0 if logical<345600 else 1 if logical<432000 else 2
            base,width,_=PLANES[plane]
            y,x=divmod(logical-base,width)
            fragment=x//8
            burst=self.forward[logical] & ~15
            if self.retain and self.row[plane]==y and fragment in self.fragments[plane]:
                row_hits+=1
            elif self.scratch==burst:
                scratch_hits+=1
            else:
                actions.append(burst)
                self.scratch=burst
                if self.retain and y%2==0:
                    if self.row[plane]!=y+1:
                        self.fragments[plane]={}
                    self.fragments[plane][fragment]=self.tiles[burst+8:burst+16]
                    self.row[plane]=y+1
        return actions,row_hits,scratch_hits


def events(path):
    with gzip.open(path,'rt') as stream:
        for line in stream:
            yield json.loads(line)


def replay(stream, expected_seed, expected_retain, images, tiles, forward, schedule):
    session=owner=bus=config=verdict=None
    counts=collections.Counter()
    checks=set()
    frames=[]
    last_cycle=-1
    offered=held_cycles=wrong_tags=0
    global_row_hits=0
    witnesses=[]
    difference=next(i for i,(a,b) in enumerate(zip(images['actual_001'],images['actual_006'])) if a!=b)
    for event in stream:
        kind=event['type']
        counts[kind]+=1
        cycle=event.get('cycle',event.get('last_cycle',last_cycle))
        need(cycle>=last_cycle,'events go backward in time')
        last_cycle=cycle
        if kind=='config':
            need(config is None,'duplicate config')
            config=event
            need(event['seed']==expected_seed and event['retain']==expected_retain,'wrong seed/static mode')
            need(event['data_storage_bytes']==(1472 if expected_retain else 32),'data allocation differs')
            need(event['service']=='one_BL8_8payload_plus1to5wait_cycles_seeded_ready_stalls','memory service contract differs')
        elif kind=='start':
            need(owner is None and bus is None,'new lease before full logical/physical drain')
            need(session is None or not session['active'],'accepted start while session active')
            need(event['image'] in images,'unknown source image')
            session=dict(event, active=event['bank']<3 and event['epoch']!=0 and event['generation']!=0,
                         next=[0,345600,432000], requests=[], successes=[],physical_reads=0,
                         output=bytearray(518400), written=bytearray(518400), row_hits=0,
                         oracle=GatherOracle(expected_retain,tiles[event['image']],forward))
        elif kind=='finish':
            need(session is not None and owner is None and bus is None,'finish before logical/physical drain')
            session['active']=False
        elif kind=='kill':
            need(session is not None,'kill without initialized session')
            need(event['reset'] or event['cancel'],'kill without asserted input')
            need(bool(event['pending'])==(bus is not None),'kill pending receipt disagrees with accepted owner')
            session['active']=False
            if owner is not None and event['state']!=4:
                owner['killed']=True
        elif kind=='req':
            need(config is not None and session is not None and session['active'],'request without valid active lease')
            need(owner is None and bus is None,'logical owner overwritten before response/drain')
            address=event['address']
            error=0
            if address>=518400 or address%16:
                error=1
            elif any(event[k]!=session[k] for k in ('bank','epoch','generation')):
                error=3
            else:
                plane=0 if address<345600 else 1 if address<432000 else 2
                if address!=session['next'][plane]:
                    error=2
                else:
                    session['next'][plane]+=16
            actions,row_hits,scratch_hits=([],0,0) if error else session['oracle'].request(address)
            owner=dict(event,expected_error=error,killed=False,offered=None,actions=actions,
                       issued=0,returned=0,row_hits=row_hits,scratch_hits=scratch_hits,
                       memory_error=False)
            session['requests'].append(address)
            if error:
                session['active']=False
        elif kind=='phys_req':
            need(owner is not None and not owner['killed'] and owner['expected_error']==0,'physical request for invalid/canceled owner')
            need(session['active'] and bus is None,'physical ownership overflow/inactive request')
            need(all(event[k]==session[k] for k in ('bank','epoch','generation')),'physical lease differs from accepted session')
            need(event['image']==session['image'],'physical image changed under lease')
            i=owner['issued']
            need(i<len(owner['actions']) and event['address']==owner['actions'][i],'physical burst differs from independent gather/retention schedule')
            need(event['address']%16==0 and event['address']<=518384,'unaligned/out-of-range physical read')
            need(9<=event['due']-cycle<=13,'declared eight-payload plus1..5 wait service differs')
            owner['issued']+=1
            bus=dict(event)
            session['physical_reads']+=1
        elif kind=='wrong_tag_rsp':
            need(bus is not None and event['ready']==0,'wrong response tag released accepted owner')
            need(event['address']==bus['address'] and event['generation']!=bus['generation'],'wrong-tag stimulus not distinct from owner')
            need(cycle>=bus['due'],'wrong-tag response before service due')
            wrong_tags+=1
            bus['due']=cycle+1
        elif kind=='phys_rsp':
            need(bus is not None and owner is not None,'physical response without accepted owner')
            need(all(event[k]==bus[k] for k in PHYSICAL),'physical response identity differs')
            need(cycle==bus['due'],'physical response delay differs from service receipt')
            expected=tiles[session['image']][event['address']:event['address']+16]
            need(bytes.fromhex(event['data'])==expected,'physical bytes differ from independent tile image')
            need(event['error'] in (0,1),'invalid physical error')
            if event['error']:
                owner['memory_error']=True
                session['active']=False
            owner['returned']+=1
            bus=None
        elif kind in ('rsp_offer','rsp_accept'):
            need(owner is not None,'response without logical owner')
            need(all(event[k]==owner[k] for k in IDENTITY),'response logical identity differs')
            need(bus is None and owner['issued']==owner['returned'],'response before physical drain')
            payload=tuple(event[k] for k in (*IDENTITY,'error','data'))
            if owner['offered'] is None:
                error=4 if owner['killed'] else 5 if owner['memory_error'] else owner['expected_error']
                need(event['error']==error,'response error differs from contract')
                if error==0:
                    need(owner['issued']==len(owner['actions']),'successful response omitted required physical read')
                    address=owner['address']
                    need(bytes.fromhex(event['data'])==images[session['image']][address:address+16],'logical data differs from immutable source image')
                else:
                    need(bytes.fromhex(event['data'])==bytes(16),'error response leaked stale payload')
                owner['offered']=payload
            need(owner['offered']==payload,'held response data/identity/error changed')
            if kind=='rsp_offer':
                offered+=1
                held_cycles+=not event['ready']
            else:
                if event['error']==0:
                    address=owner['address']
                    session['successes'].append(address)
                    need(not any(session['written'][address:address+16]),'duplicate successful bytes within lease')
                    session['written'][address:address+16]=b'\1'*16
                    session['output'][address:address+16]=bytes.fromhex(event['data'])
                    session['row_hits']+=owner['row_hits']
                    global_row_hits+=owner['row_hits']
                    if session['bank']==0 and session['epoch'] in (302,303) and address<=difference<address+16:
                        witnesses.append(dict(bank=session['bank'],epoch=session['epoch'],generation=session['generation'],
                                              image=session['image'],logical_byte=difference,
                                              value=bytes.fromhex(event['data'])[difference-address]))
                session['last_response_cycle']=cycle
                owner=None
        elif kind=='frame':
            need(session is not None and owner is None and bus is None and session['active'],'frame fence before drain or after invalidation')
            need(event['name']==session['image'],'frame image differs from lease')
            need(session['requests']==session['successes']==schedule,'frame request/response order differs from independent source-derived schedule')
            need(all(session['written']) and bytes(session['output'])==images[session['image']],'full canonical output mismatch')
            need(event['requests']==32400 and event['bytes']==518400,'frame extent differs')
            need(event['physical_reads']==session['physical_reads']==(32400 if expected_retain else 64800),'frame physical count differs')
            need(event['row_hits']==session['row_hits']==(32400 if expected_retain else 0),'frame row-hit count differs')
            need(event['first_cycle']==session['cycle']+1,'frame timing start does not follow accepted start')
            need(event['last_cycle']==cycle==session['last_response_cycle']+1 and event['cycles']==cycle-event['first_cycle'],'frame timing fence differs')
            need(cycle>0,'empty frame timing')
            frames.append(dict(event,sha256=digest(session['output']),
                               fence='Accepted start +1 cycle to after final logical response tick; includes C++ driver, seeded service-ready and output hold delays.'))
        elif kind=='check':
            need(event['status']=='PASS' and event['name'] not in checks,'duplicate/failing check')
            checks.add(event['name'])
        elif kind=='verdict':
            need(verdict is None,'duplicate verdict')
            verdict=event
        else:
            raise AssertionError('unknown event type '+kind)
    need(config is not None and verdict is not None,'missing config/verdict')
    need(verdict['status']=='TEST_PASS' and verdict['seed']==expected_seed and verdict['retain']==expected_retain,'wrong verdict/static seed')
    need(owner is None and bus is None and session is not None and not session['active'],'terminal lease not drained')
    need(REQUIRED_CHECKS==checks,'missing/extra directed check set')
    need(offered>counts['rsp_accept'] and held_cycles>10,'held response path untested')
    need(wrong_tags>=1,'generation mismatch path untested')
    for field,actual in (('checks',len(checks)),('requests',counts['req']),('responses',counts['rsp_accept']),
                         ('physical_requests',counts['phys_req']),('physical_responses',counts['phys_rsp'])):
        need(verdict[field]==actual,'verdict count differs: '+field)
    need(counts['req']==counts['rsp_accept'] and counts['phys_req']==counts['phys_rsp'],'unmatched accepted/retired receipts')
    need(verdict['row_hits']==global_row_hits,'row-hit total differs from independently modeled successful requests')
    need(len(frames)==2 and [f['name'] for f in frames]==['actual_001','actual_006'],'native frames incomplete/reordered')
    need(len(witnesses)==2 and witnesses[0]['epoch']==302 and witnesses[1]['epoch']==303
         and witnesses[0]['generation']!=witnesses[1]['generation']
         and witnesses[0]['image']!=witnesses[1]['image']
         and witnesses[0]['logical_byte']==witnesses[1]['logical_byte']==23293
         and witnesses[0]['value']!=witnesses[1]['value'], 'same-bank generation test did not observe changed source content')
    return dict(seed=expected_seed,retain=expected_retain,status='PASS_INDEPENDENT_ROWPAIR_RECEIPT_AND_DATA_REPLAY',
                event_counts=dict(counts),checks=sorted(checks),frames=frames,verdict=verdict,
                same_bank_generation_content_witnesses=witnesses,
                held_response_cycles=held_cycles,wrong_tag_responses_rejected=wrong_tags,
                algorithm='Single forward replay; one logical owner and one physical owner; independent geometric tile image and gather retention policy.')


def negative_controls(path, seed, retain, images, tiles, forward, schedule):
    prefix=[]
    for event in events(path):
        prefix.append(event)
        if len(prefix)>=3000:
            break
    def first(kind,predicate=lambda event:True):
        return next(i for i,event in enumerate(prefix) if event['type']==kind and predicate(event))
    repeated=set()
    held=None
    for i,event in enumerate(prefix):
        if event['type']=='rsp_offer':
            key=tuple(event[k] for k in IDENTITY)
            if key in repeated and event['ready']==0:
                held=i
                break
            repeated.add(key)
    need(held is not None,'no held response for corruption control')
    physical=first('phys_rsp')
    success=first('rsp_offer',lambda e:e['error']==0)
    accept=first('rsp_accept')
    wrong=first('wrong_tag_rsp')
    request=first('phys_req')
    controls=[
        ('corrupt_physical_bytes',physical,'data','00'+prefix[physical]['data'][2:],'physical bytes differ'),
        ('corrupt_logical_success_bytes',success,'data',f"{int(prefix[success]['data'][:2],16)^1:02x}"+prefix[success]['data'][2:],'logical data differs'),
        ('corrupt_logical_response_token',accept,'token',prefix[accept]['token']^1,'response logical identity differs'),
        ('change_held_response_error',held,'error',prefix[held]['error']^1,'held response data/identity/error changed'),
        ('wrong_generation_consumes_owner',wrong,'ready',1,'wrong response tag released'),
        ('alter_declared_physical_due_cycle',request,'due',prefix[request]['due']+(-1 if prefix[request]['due']-prefix[request]['cycle']==13 else 1),'physical response delay differs'),
        ('corrupt_physical_burst_address',request,'address',prefix[request]['address']^16,'physical burst differs'),
        ('drop_accepted_physical_response',physical,None,None,'response before physical drain'),
    ]
    # Always flip a real byte; the selected physical source may already begin 00.
    controls[0]=(*controls[0][:3],f"{int(prefix[physical]['data'][:2],16)^1:02x}"+prefix[physical]['data'][2:],controls[0][4])
    rejected=[]
    for name,index,field,value,reason in controls:
        def modified():
            for i,event in enumerate(prefix):
                if i==index:
                    if field is not None:
                        yield {**event,field:value}
                else:
                    yield event
        try:
            replay(modified(),seed,retain,images,tiles,forward,schedule)
        except AssertionError as error:
            need(reason in str(error),'negative control failed for unrelated/incomplete-prefix reason: '+name+': '+str(error))
            rejected.append(dict(mutation=name,seed=seed,retain=retain,rejected=True,reason=str(error)))
        else:
            raise AssertionError('checker accepted mutated receipt '+name)
    return rejected


def pinned_path(base,relative):
    path=(base/relative).resolve()
    need(path.is_relative_to(base.resolve()),'artifact path escapes bundle')
    return path


def provenance(path):
    report=json.loads(path.read_text())
    need(report['schema']=='cu66-v91l-rowpair-comparison-v1' and report['status']=='PASS_STATIC_ROWPAIR_PREFILL_COMPARISON','nonpassing/unknown comparison')
    attempt=path.parent
    revision=report['source_revision']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for a,b in ((BASELINE,revision),(revision,head)):
        need(subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT,capture_output=True).returncode==0,'source revision not ancestor of current tree')
    required_sources={
        'fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv',
        'fpga/experiments/cu66-v91l-rowpair/tb_rowpair.cpp',
        'scripts/cu66-v91l-rowpair/run_comparison.py',
        'experiments/python-gamebub-v91l-tiled/prefill_model.py',
        'fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',
        'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',
        'fpga/experiments/cu66-v91k-lines/tb_lines.cpp',
        'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv',
    }
    need(set(report['source_sha256'])==required_sources,'source set differs')
    for name,h in report['source_sha256'].items():
        need(sha(pinned_path(ROOT,name))==sha(pinned_path(attempt/'sources',name))==h,'source/snapshot changed: '+name)
    need(report['inputs_sha256'],'inputs not pinned')
    for name,h in report['inputs_sha256'].items():
        need(sha(pinned_path(ROOT,name))==sha(attempt/'inputs'/Path(name).name)==h,'input changed: '+name)
    for expansion in report['input_expansions']:
        packed=pinned_path(attempt,expansion['compressed_path'])
        need(sha(packed)==expansion['compressed_sha256'],'input expansion compressed hash differs')
        need(digest(gzip.decompress(packed.read_bytes()))==expansion['sha256'],'input expansion payload hash differs')
    need(report['artifacts_sha256'],'empty artifact manifest')
    for name,h in report['artifacts_sha256'].items():
        need(sha(pinned_path(attempt,name))==h,'artifact changed: '+name)
    need(all(c['exit_code']==0 for c in report['commands']),'failed command')
    builds=[c['argv'] for c in report['commands'] if '--build' in c['argv']]
    need(len(builds)==2,'missing matched builds')
    retain=set()
    for argv in builds:
        need({'--cc','--exe','--build','--assert','-Wall'}<=set(argv),'weak RTL flags')
        need(not any(str(x).startswith('-Wno-') for x in argv),'disabled design warning')
        need(argv[argv.index('-j')+1]=='2','unexpected compile concurrency')
        need({'-std=c++20','-Wall','-Wextra','-Werror'}<=set(argv[argv.index('-CFLAGS')+1].split()),'weak C++ flags')
        parameter=next(x for x in argv if str(x).startswith('-GRETAIN_ROWS='))
        need(parameter in ("-GRETAIN_ROWS=1'b0","-GRETAIN_ROWS=1'b1"),'unexpected retention parameter')
        retain.add(parameter)
        for source in ('fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv','fpga/experiments/cu66-v91l-rowpair/tb_rowpair.cpp'):
            need(str(attempt/'sources'/source) in argv,'compiled source not pinned snapshot')
    need(retain=={"-GRETAIN_ROWS=1'b0","-GRETAIN_ROWS=1'b1"},'static comparison not compiled separately')
    for key in ('physical_hardware_tested','physical_sdram_controller_join','actual_converter_rtl_join','shared_service_complete','sustained_hardware_30fps_proven','validated_full_frame_under10ms_proven'):
        need(report[key] is False,'unsupported qualification claim: '+key)
    need('No SDRAM commands/refresh/arbiter' in report['service'],'service scope absent')
    need('5.020' in (attempt/'tool-version.log').read_text(),'Verilator version differs')
    need('13.3.0' in (attempt/'compiler-version.log').read_text(),'compiler version differs')
    return report


def checked_events(path,metadata):
    count=0
    h=hashlib.sha256()
    with gzip.open(path,'rb') as stream:
        for line in stream:
            h.update(line)
            count+=1
            yield json.loads(line)
    need(count==metadata['rows'] and h.hexdigest()==metadata['raw_sha256'],'raw trace digest/row count differs')


def main():
    alias=json.loads((AREA/'comparison-results.json').read_text())
    path=pinned_path(ROOT,alias['selected_report'])
    need(path.parent.parent==AREA/'comparison-attempts','selected report outside attempt root')
    report=provenance(path)
    need({k:v for k,v in alias.items() if k!='selected_report'}==report,'alias differs from retained report')
    images,tiles,forward=load_images()
    schedule=derived_schedule()
    modes=[]
    mutations=[]
    need(report['seeds']==[912501,912502] and len(report['modes'])==4,'missing seed/mode campaign')
    for mode in report['modes']:
        need(mode['variant']==('retained' if mode['retain'] else 'independent'),'mode/static label differs')
        metadata=report['compressed_artifacts'][mode['event_log'].removesuffix('.gz')]
        trace=pinned_path(path.parent,metadata['path'])
        need(sha(trace)==metadata['gzip_sha256'],'compressed trace digest differs')
        audited=replay(checked_events(trace,metadata),mode['seed'],mode['retain'],images,tiles,forward,schedule)
        need(audited['verdict']==mode['verdict'],'runner verdict differs from receipts')
        need(audited['checks']==sorted(mode['checks']),'runner checks differ from receipts')
        for actual,summary in zip(audited['frames'],mode['frames']):
            need(actual['sha256']==summary['output_sha256']==digest(images[actual['name']]),'output bank hash differs')
            output=pinned_path(trace.parent,actual['output'])
            need(sha(output)==actual['sha256'] and output.read_bytes()==images[actual['name']],'saved canonical output differs')
            for key in ('cycles','physical_reads','requests','bytes','row_hits','first_cycle','last_cycle'):
                need(actual[key]==summary[key],'runner frame summary differs: '+key)
        mutations.extend(negative_controls(trace,mode['seed'],mode['retain'],images,tiles,forward,schedule))
        modes.append(audited)
        print('AUDITED_ROWPAIR',mode['variant'],mode['seed'],flush=True)
    need({(m['seed'],m['retain']) for m in modes}=={(s,r) for s in (912501,912502) for r in (0,1)},'duplicate/missing static seed modes')
    comparisons=[]
    for seed in (912501,912502):
        old=next(m for m in modes if m['seed']==seed and m['retain']==0)
        new=next(m for m in modes if m['seed']==seed and m['retain']==1)
        for before,after in zip(old['frames'],new['frames']):
            need(before['sha256']==after['sha256'] and before['name']==after['name'],'matched output changed')
            need(after['physical_reads']*2==before['physical_reads'] and after['cycles']<before['cycles'],'retention did not improve matched workload')
            comparisons.append(dict(seed=seed,frame=after['name'],independent_bl8=before['physical_reads'],retained_bl8=after['physical_reads'],
                                    independent_cycles=before['cycles'],retained_cycles=after['cycles'],
                                    component_cycle_reduction_percent=(before['cycles']-after['cycles'])/before['cycles']*100,
                                    sha256=after['sha256']))
    for audited,summary in zip(comparisons,report['comparisons']):
        for key in ('seed','frame','independent_bl8','retained_bl8','independent_cycles','retained_cycles','component_cycle_reduction_percent'):
            need(audited[key]==summary[key],'runner comparison differs: '+key)
    # The changed-content lease test must reach bytes that differ between native images.
    first_difference=next(i for i,(a,b) in enumerate(zip(images['actual_001'],images['actual_006'])) if a!=b)
    need(first_difference==23293,'native content-change witness moved; review directed test extent')
    result=dict(schema='cu66-v91l-rowpair-independent-audit-v1',status='PASS_INDEPENDENT_TWO_SEED_ROWPAIR_AUDIT',
                selected_report=str(path.relative_to(ROOT)),report_sha256=sha(path),source_revision=report['source_revision'],
                verifier_sha256=sha(Path(__file__)),
                canonical_input_sha256=sha(CANONICAL),derived_schedule_gzip_sha256=sha(VECTOR),
                source_sha256=report['source_sha256'],modes=modes,comparisons=comparisons,checker_negative_controls=mutations,
                content_change_witness=dict(first_differing_canonical_byte=first_difference),
                assertions=dict(exact_current_sources_and_snapshots=True,strict_build_flags=True,
                                single_logical_and_physical_owner=True,all_logical_bytes_exact=True,
                                independent_geometric_tile_image=True,source_derived_chroma_prefill_schedule_exact=True,
                                per_plane_order_and_bank_epoch_generation_leases=True,
                                cancel_and_reset_drain_accepted_physical_reads=True,
                                held_success_and_error_immutable=True,wrong_generation_never_releases_owner=True,
                                all_complete_output_banks_match_canonical_goldens=True,
                                physical_controller_or_converter_top_join=False,physical_hardware_qualified=False,
                                sustained_30fps_or_validated_full_decode_under10ms_qualified=False),
                scope='Component RTL with declared one-BL8 owner, eight payload plus1..5 seeded wait/ready cycles and source-derived actual prefill order. Frame fence includes driver/ready/held-response delays; no SDRAM timing/refresh/shared arbiter, actual converter top, RGB output, achieved frequency, hardware FPS or full validated decode claim.')
    (HERE/'audit-rowpair.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],flush=True)


if __name__=='__main__':
    main()
