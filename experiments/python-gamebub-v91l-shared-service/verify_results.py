#!/usr/bin/env python3
"""Independent native source/ACK/hash/RGB and shared physical SDRAM audit."""
import argparse
import collections
import gzip
import heapq
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess

from memory_audit import ROOT,HELPERS,Replay,events,identity,native,need,numeric,ordered,physical_byte,sha

HERE=Path(__file__).resolve().parent
BASELINE='298961c64ae947c01eeb55ea1b0815a3e87a3fdb'
FABRIC='fpga/experiments/cu66-v91l-shared-service'
LIVE='fpga/experiments/cu66-v91l-shared-live'
# Expert source review pins. These are not learned from the runner's verdict.
REVIEWED={
 FABRIC+'/shared_sdram_service.sv':'9b820b4de7e4a156acff60de078b7deb9311d1bcaa81c04684759a403dd43158',
 FABRIC+'/shared_sdram_timed.sv':'ee53aa99773d01e78f2e35b6ffc9d7e2ea33b61dfa4703a56bb7a94a35a3ecb9',
 LIVE+'/shared_live.sv':'d1f5bbee09ba97bd4d533737a2dac1d747d30e3f556ad2c862c6f4cb35e58b63',
 LIVE+'/tb_shared_live.cpp':'cde4542e98bfa5118479d66d99053ca081605232b37ba0947b994b2e9bfa1c64',
 LIVE+'/make_wrapper.py':'9b9612ad891ac614768e84be270813fc026feb88cd68b242a5046d39ac72288d',
 LIVE+'/make_bench.py':'15b46aa55ad5b414949a1b05f6b72cb9aea779e3b9d9b72551be25da1ea0c4ab',
 LIVE+'/bench_extension.inc':'d6d1a4c9a4fefe8ded3e5a3ea2afe71f8ed49f743a67f2ffc84babb8609f1528',
 'scripts/cu66-v91l-shared-live/run_test.py':'9367a8815d5b308565e66ccc2122489a82e75de00df324ce53c2757a111834f6',
}

def provenance(alias_name,status):
    alias=json.loads((ROOT/alias_name).read_text());path=ROOT/alias['selected_report'];report=json.loads(path.read_text())
    need(alias==dict(report,selected_report=str(path.relative_to(ROOT))),'selected alias differs')
    need(report['status']==status,'selected campaign failed')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for old,new in ((BASELINE,report['source_revision']),(report['source_revision'],head)):
        need(subprocess.run(['git','merge-base','--is-ancestor',old,new],cwd=ROOT,capture_output=True).returncode==0,'source ancestry differs')
    for name,digest in report['source_sha256'].items():
        need(sha(ROOT/name)==sha(path.parent/'sources'/name)==digest,'source snapshot differs: '+name)
        if name in REVIEWED:need(digest==REVIEWED[name],'reviewed new source differs: '+name)
        else:
            old=subprocess.run(['git','show',BASELINE+':'+name],cwd=ROOT,capture_output=True)
            if old.returncode==0:
                need(__import__('hashlib').sha256(old.stdout).hexdigest()==digest,'frozen source changed: '+name)
    for name,digest in report.get('inputs_sha256',{}).items():
        need(sha(ROOT/name)==sha(path.parent/'inputs'/Path(name).name)==digest,'input snapshot differs: '+name)
    for name,digest in report['artifacts_sha256'].items():need(sha(path.parent/name)==digest,'retained artifact differs: '+name)
    for item in report.get('input_expansions',[]):
        packed=path.parent/item['compressed_path'];need(sha(packed)==item['compressed_sha256'],'packed input differs')
        need(__import__('hashlib').sha256(gzip.decompress(packed.read_bytes())).hexdigest()==item['raw_sha256'],'expanded input differs')
    need(all(c['exit_code']==0 for c in report['commands']),'campaign contains failed command')
    need('5.020' in (path.parent/'tool-version.log').read_text() and '13.3.0' in (path.parent/'compiler-version.log').read_text(),'tool versions differ')
    for c in report['commands']:
        argv=c['argv']
        if '--binary' not in argv and '--build' not in argv:continue
        need({'--timing','--assert','-Wall','-DSIMULATION'}<=set(argv),'weak RTL build flags')
        need(not any(str(x).startswith('-Wno-') for x in argv),'HDL warning waived')
        need({'-std=c++20','-Wall','-Wextra','-Werror'}<=set(argv[argv.index('-CFLAGS')+1].split()),'weak C++ build flags')
        for value in argv:
            if str(value).endswith(('.sv','.cpp')):
                p=Path(value);need(p.is_relative_to(path.parent/'sources'),'compile outside snapshot')
                need(str(p.relative_to(path.parent/'sources')) in report['source_sha256'],'compiled source not pinned')
    return path,report

def negative_controls(stream):
    original=list(stream)
    trials=[('wr_req',lambda e:dict(e,token=e['token']^1),'bridge response identity'),
            ('ctrl_req',lambda e:dict(e,address=e['address']^1),'physical command address'),
            ('pin',lambda e:dict(e,dq=e['dq']^1),'pin DQ'),
            ('read',lambda e:dict(e,data=e['data']^1),'SDR BL8 beat'),
            ('controller_read',lambda e:dict(e,data=e['data']^1),'capture/retime/consume data'),
            ('controller_read',lambda e:dict(e,time_ps=e['time_ps']+1),'capture/retime/consume timing'),
            ('wr_rsp_offer',lambda e:dict(e,error=e['error']^1),'response error'),
            ('wr_rsp',lambda e:dict(e,bank=e['bank']^1),'bridge response identity'),
            ('rd_rsp',lambda e:dict(e,data=f'{numeric(e["data"])^1:032x}'),'held response mutated'),
            ('ownership',lambda e:dict(e,owner=2),'round-robin grant')]
    results=[]
    for kind,mutate,causal in trials:
        index=next(i for i,e in enumerate(original) if e['type']==kind and
                   (kind!='pin' or e['command']==4) and
                   (kind!='ownership' or e['old_owner']==0 and e['owner']==1))
        bad=[*original];bad[index]=mutate(original[index]);oracle=Replay()
        try:
            for event in bad:oracle.feed(event)
            oracle.finish()
        except AssertionError as error:
            need(causal in str(error),'negative rejected for wrong reason: '+str(error))
            results.append(dict(kind=kind,index=index,original=original[index],corrupted=bad[index],rejected=True,reason=str(error)))
        else:raise AssertionError('checker accepted deliberate corruption: '+kind)
    return results

def rows(frame):
    base=0
    for count,width in zip((5400,1350,1350),(720,360,360)):
        for tile in range(count):
            ty,tx=divmod(tile,width//8)
            for row in range(8):
                address=base+((ty*8+row)*width)+tx*8
                value=int.from_bytes(frame['tiles'][base+tile*64+row*8:base+tile*64+row*8+8],'little')
                yield address,value
        base+=count*64
    for i in range(0,42240,8):yield 518400+i,int.from_bytes(frame['hud'][i:i+8],'little')

def line_addresses():
    tags={}
    for y in range(480):
        fills=(0,1) if y==0 else ((y//2+1,) if y%2==0 and y<=476 else ())
        chunks=[(p,range(base+r*360,base+(r+1)*360)) for r in fills for p,base in ((1,345600),(2,432000))]
        chunks.append((0,range(y*720,(y+1)*720)))
        for plane,addresses in chunks:
            for address in addresses:
                line=address&~15
                if tags.get(plane)!=line:tags[plane]=line;yield line
LINE_ORDER=tuple(line_addresses());need(len(LINE_ORDER)==32400,'canonical line order extent differs')

def stamp(stream):
    last=-1
    for e in stream:
        if 'time_ps' not in e:
            if 'cycle' in e:e=dict(e,time_ps=e['cycle']*10000+5000)
            elif 'last_cycle' in e:e=dict(e,time_ps=e['last_cycle']*10000+5000)
            else:continue
        need(e['time_ps']>=last,'source events reverse simulation time');last=e['time_ps'];yield e
def merge(a,b):
    yield from heapq.merge(stamp(a),stamp(b),key=lambda e:e['time_ps'])
def fnv(data):
    h=1469598103934665603
    for b in data:h=((h^b)*1099511628211)&((1<<64)-1)
    return h

def live_mode(attempt,mode,frames,goldens):
    directory=attempt/mode['directory'];bus=iter(native.iter_bus(directory/'bus.bin.gz'))
    memory=Replay(True);current=None;done=[];line=None;delivered=[];pixel_rows=[];holds=[];presented=[]
    pipeline_cases=[]
    def observed_stdout():
        for event in events(attempt/f'pins-seed{mode["seed"]}-tac{mode["t_ac_ns"]}.jsonl.gz'):
            if event['type']=='case':pipeline_cases.append(event)
            yield event
    stream=ordered(merge(observed_stdout(),events(directory/'physical-events.jsonl.gz')))
    for e in stream:
        k=e['type']
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
            need(current is not None and current['rgb'] is not None,'physical RGB read before validated start')
            need(all(e[x]==current[x] for x in ('bank','epoch','generation')),'physical read lease differs');current['physical_reads']+=1
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
    need(result['physical_write_words']==560640 and result['physical_captured_words']==518400,'physical full-frame work differs')
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
    return dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],physical=result,frames=done,rtl_sha_jobs=2050,
                source_canonical_HUD_bytes=1121280,publication_hold_checks=len(holds),presented_fids=presented)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--unit-only',action='store_true');a=ap.parse_args()
    up,unit=provenance(FABRIC+'/results.json','PASS_TIMED_SHARED_SERVICE_DIRECTED')
    units=[];negatives=[]
    for mode in unit['modes']:
        need(mode['status']=='PASS' and mode['verdict']['checks']==89 and len(mode['checks'])==89,'unit directed cases incomplete')
        trace=list(ordered(events(up.parent/mode['event_log'])));oracle=Replay()
        for event in trace:oracle.feed(event)
        units.append(dict(t_ac_ns=mode['t_ac_ns'],**oracle.finish()))
        negatives.extend(dict(t_ac_ns=mode['t_ac_ns'],**e) for e in negative_controls(trace))
    result=dict(schema='cu66-v91l-shared-independent-audit-v1',status='PASS_INDEPENDENT_SHARED_SERVICE_UNIT_AUDIT',
                unit_report=str(up.relative_to(ROOT)),unit_report_sha256=sha(up),unit_modes=units,
                checker_negative_controls=negatives,helper_sha256=HELPERS,reviewed_source_sha256=REVIEWED,
                verifier_sha256=sha(Path(__file__)),memory_verifier_sha256=sha(HERE/'memory_audit.py'))
    if not a.unit_only:
        lp,live=provenance(LIVE+'/results.json','PASS_EXACT_LIVE_COMMIT_TO_SAME_TIMED_MEMORY_RGB')
        need(len(live['modes'])==4 and {(m['seed'],m['t_ac_ns']) for m in live['modes']}=={(s,t) for s in (912801,912802) for t in (2,7)},'native seed/corner grid incomplete')
        need(live['physical_preload'] is False and live['actual_physical_candidate_writes'] and live['actual_rgb_from_same_pin_memory'],'native physical join flags differ')
        need(not live['full_live_physical_service_complete'] and not live['scratch_reference_service_rtl'] and not live['full_rtl_hud_decoder'] and not live['full_rtl_hud_overlay'] and not live['hardware_30fps_proven'] and not live['physical_hardware_tested'],'unsupported full-codec/hardware claim')
        frames=native.expected_frames(lp.parent);goldens={}
        for line in gzip.open(lp.parent/'inputs/rgb_goldens.tsv.gz','rt'):
            ident,data=line.rstrip().split('\t')
            if ident in ('actual_001','actual_006'):goldens[ident]=bytes.fromhex(data)
        results=[]
        for mode in live['modes']:
            results.append(live_mode(lp.parent,mode,frames,goldens));print('AUDITED_SHARED_LIVE',mode['seed'],mode['t_ac_ns'],flush=True)
        result.update(status='PASS_INDEPENDENT_LIVE_PHYSICAL_WRITE_VALIDATION_AND_SAME_MEMORY_RGB',
                      live_report=str(lp.relative_to(ROOT)),live_report_sha256=sha(lp),live_modes=results,
                      exact_native_RGB_outputs=8,rtl_sha_jobs=8200,
                      scope='Serial live supported BR88 key/delta candidate physical writes, real C2/HUD/seal validation, then same pin-memory RGB. Finite logical scratch/reference and C++ HUD remain; no full physical service, routed frequency, hardware30fps or complete under10ms proof.')
    for path,report in [(up,unit)]+([] if a.unit_only else [(lp,live)]):
        for name,digest in report['source_sha256'].items():need(sha(ROOT/name)==digest,'source changed during audit: '+name)
    (HERE/('audit-unit.json' if a.unit_only else 'audit.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],flush=True)
if __name__=='__main__':main()
