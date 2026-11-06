#!/usr/bin/env python3
"""Independently bind V84's finite-credit campaign to native and frozen evidence.

All retained row identities/counts/statistics are checked. Four retained full
timelines are reaudited and their augmented DAGs independently reconstructed.
This is software-model evidence, not physical timing or transport qualification.
"""
from __future__ import annotations
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import statistics
import struct
import sys
import tarfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v84'
ENTROPY = AREA/'entropy'
NATIVE = ROOT/'experiments/python-gamebub-v82/native/index.json'
CONTROL = ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
V83 = ROOT/'experiments/python-gamebub-v83/summary.json'
COHORTS = (119,119,119,100)
FIELDS = ('decisions','renorm','stream_bytes','rice_values','events','raw_bytes',
          'header_bytes','crc_bytes','emits','raw_bits','prob_init')
LOW = dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,
           raw_bytes=2,header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1)
HIGH = dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,
            raw_bytes=4,header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1)
RESERVED = dict(period=10000,blocked=[[0,2000]])
CONFIGS = [
    dict(name='v83_control',slots=None,weights=None,read_gap=18,write_gap=16,windows=None),
    dict(name='credits64_zero_arrival',slots=64,weights=None,read_gap=18,write_gap=16,windows=None),
    dict(name='credits8_zero_arrival',slots=8,weights=None,read_gap=18,write_gap=16,windows=None),
    dict(name='credits2_zero_arrival',slots=2,weights=None,read_gap=18,write_gap=16,windows=None),
    dict(name='credits8_primitive_low',slots=8,weights=LOW,read_gap=18,write_gap=16,windows=None),
    dict(name='credits8_primitive_high',slots=8,weights=HIGH,read_gap=18,write_gap=16,windows=None),
    dict(name='credits8_low_reserved20',slots=8,weights=LOW,read_gap=18,write_gap=16,windows=RESERVED),
    dict(name='credits8_low_service12_reserved20',slots=8,weights=LOW,read_gap=12,write_gap=12,windows=RESERVED),
]
CONFIG_BY_NAME={c['name']:c for c in CONFIGS}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def local(path):
    p=Path(path)
    p=p.resolve() if p.is_absolute() else (ROOT/p).resolve()
    p.relative_to(ROOT)
    return p


def relative(path):
    return str(local(path).relative_to(ROOT))


def pins_current(pins):
    assert pins
    for name,digest in pins.items():
        assert relative(name)==name and re.fullmatch('[0-9a-f]{64}',digest)
        assert sha(local(name))==digest, ('source mismatch',name)


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    sys.modules[name]=obj
    spec.loader.exec_module(obj)
    return obj


def stats(values):
    return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def summarize(rows):
    out=[]
    for config in CONFIGS:
        for key in (True,False,None):
            group=[r for r in rows if r['configuration']==config['name'] and (key is None or r['key']==key)]
            if group:
                out.append(dict(configuration=config['name'],key=key,sources=len(group),
                                model_ms=stats([r['finish_cycles']*1e-5 for r in group]),
                                entropy_work_ms=stats([r['entropy_work_cycles']*1e-5 for r in group]),
                                conditional_under10ms=sum(r['finish_cycles']<1_000_000 for r in group),
                                conditional_within30fps_period=sum(r['finish_cycles']<=100_000_000//30 for r in group)))
    return out


def test_records():
    credits_path=AREA/'credits-tests.json';credit=read(credits_path)
    assert credit['status']=='PASS' and credit['checks']==len(credit['check_names'])==557
    assert credit['native_frames']==8 and credit['synthetic_frames']==6 and len(credit['cases'])==42
    pins_current(credit['source_sha256'])
    audit_path=AREA/'audit-tests.json';audit=read(audit_path)
    assert audit['passed']==len(audit['checks'])==9 and audit['failed']==0
    assert all(c['result'] in ('accepted_as_expected','rejected_as_expected') for c in audit['checks'])
    pins_current(audit['source_sha256'])
    return {relative(p):sha(p) for p in (credits_path,audit_path)}


def entropy_records():
    index=read(ENTROPY/'index.json')
    assert index['schema']=='cu66-v84-native-entropy-v1'
    assert index['record_count']==len(index['frames'])==457 and tuple(index['cohort_counts'])==COHORTS
    assert tuple(index['fields'])==FIELDS
    pins_current(index['source_sha256'])
    data=ENTROPY/index['data']['path']
    assert sha(data)==index['data']['gzip_sha256']
    verification=read(ENTROPY/'verification.json')
    assert verification['status']=='PASS' and verification['records']==457
    assert verification['native_coefficient_plane_checks']==1371
    assert verification['totals']==index['totals']
    assert verification['index_sha256']==sha(ENTROPY/'index.json')
    assert verification['verifier_sha256']==sha(ENTROPY/'verify.py')
    manifest=read(ENTROPY/'artifact-manifest.json')
    for name,entry in manifest['files'].items():
        path=local(name)
        assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256']
    assert len({(f['cohort'],f['fid']) for f in index['frames']})==457
    assert index['totals']=={field:sum(f['totals'][field] for f in index['frames']) for field in FIELDS}
    return index,dict(index_sha256=sha(ENTROPY/'index.json'),data_sha256=sha(data),
                      verification_sha256=sha(ENTROPY/'verification.json'),
                      artifact_manifest_sha256=sha(ENTROPY/'artifact-manifest.json'),
                      records=457,native_coefficient_plane_checks=1371,
                      primitive_counts_are_measured_cycles=False,
                      scope='Observed coefficient/primitive parity; cycle weights are assumptions; raw fallback absent from this corpus.')


def metadata_packet(packet,hidden,version,key):
    """Independent retained-vector grammar parser, not either encoder/parser."""
    assert 20<=len(packet)<=(2045 if version==1 else 996)
    magic,ver,method,flags,group,width,height,tiles,size,crc=struct.unpack('>4sBBBBHHHHI',packet[:20])
    assert magic==b'CM84' and ver==version and flags==int(key)
    assert (group,width,height,tiles)==(16,720,480,8100) and size==len(packet)-20
    body=packet[20:]
    assert zlib.crc32(body if version==1 else packet[:16]+body)==crc
    if version==1:
        if method==0:
            assert len(body)==2025
            modes=[(body[i//4]>>(6-2*(i%4)))&3 for i in range(8100)]
        elif method==2:
            modes=[]
            for token in body:
                modes.extend([token&3]*((token>>2)+1))
                assert len(modes)<=8100
        else:
            assert method==1
            modes=[];cursor=0
            for count in (5400,1350,1350):
                for start in range(0,count,16):
                    n=min(16,count-start);tag=body[cursor];cursor+=1
                    if tag<3:
                        modes.extend([tag]*n)
                    else:
                        assert tag==3
                        encoded=body[cursor:cursor+(n+3)//4];cursor+=(n+3)//4
                        assert len(encoded)==(n+3)//4
                        modes.extend((encoded[i//4]>>(6-2*(i%4)))&3 for i in range(n))
                        if n%4:
                            assert encoded[-1]&((1<<(2*(4-n%4)))-1)==0
            assert cursor==len(body)
    else:
        assert method in (0,1,2)
        if key:
            assert method==0 and not body
            visible=[1]*7806
        elif method==1:
            assert len(body)==976 and body[-1]&3==0
            visible=[(body[i//8]>>(7-i%8))&1 for i in range(7806)]
        else:
            assert method==2
            visible=[]
            for token in body:
                visible.extend([token>>7]*((token&127)+1))
                assert len(visible)<=7806
            assert len(visible)==7806
        cursor=0;modes=[]
        for h in hidden:
            modes.append(1 if h else 2 if visible[cursor] else 0)
            if not h:
                cursor+=1
        assert cursor==7806
    assert len(modes)==8100 and all(v in (0,1,2) for v in modes)
    assert all((mode==1)==bool(h) and not (key and mode==0) for mode,h in zip(modes,hidden))
    return bytes(modes)


def metadata_records(native,entropy_index):
    reports=[];row_sets=[];pins={};vectors=[]
    for area,schema in (('mode-map','cu66-v84-mode-map-v1'),('mode-map-v2','cu66-v84-mode-map-v2-v1')):
        folder=AREA/area;path=folder/'results.json';report=read(path)
        assert report['schema']==schema and report['status']=='PASS' and report['sources']==457
        pins_current(report['source_sha256'])
        for name,digest in report['artifacts_sha256'].items():
            assert Path(name).name==name and sha(folder/name)==digest
        rows=[json.loads(line) for line in (folder/'frames.jsonl').read_text().splitlines()]
        assert len(rows)==457 and len({(r['cohort'],r['fid']) for r in rows})==457
        tests=read(folder/'tests.json')
        assert tests['status']=='PASS' and report['tests']==tests['count']==len(tests['checks'])==28
        assert all(c['status'] in ('PASS','PASS_REJECT') for c in tests['checks'])
        vector=read(folder/'vectors.json')['vectors'];assert len(vector)==report['vectors']
        reports.append(report);row_sets.append(rows);vectors.append(vector)
        pins[relative(path)]=sha(path)
        pins.update({relative(folder/name):digest for name,digest in report['artifacts_sha256'].items()})
    v1,v2=reports;a,b=row_sets
    assert v2['fixed_hidden_mask_sha256']=='e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5'
    loader=module('cu84_metadata_native',NATIVE.parent/'data.py')
    hidden=next(loader.iter_frames())['hidden_mask']
    assert hashlib.sha256(hidden).hexdigest()==v2['fixed_hidden_mask_sha256']
    # Verify every reported mode digest from independently retained zero-mask
    # observations. This parses data only and does not rerun either encoder.
    with gzip.open(ENTROPY/entropy_index['data']['path'],'rt') as stream:
        for index,line in enumerate(stream):
            frame=json.loads(line);identity=frame['cohort'],frame['fid']
            left,right=a[index],b[index];original=native[identity]
            assert identity==(left['cohort'],left['fid'])==(right['cohort'],right['fid'])
            assert left['key']==right['key']==original['key']
            assert left['packet_sha256']==right['original_packet_sha256']==original['packet_sha256']
            mode=bytes(1 if h else 0 if not frame['key'] and z=='1' else 2 for h,z in zip(hidden,frame['zero_mask']))
            assert len(mode)==8100
            assert hashlib.sha256(mode).hexdigest()==left['decoded_modes_sha256']==right['decoded_modes_sha256']
            counts={str(k):mode.count(k) for k in (0,1,2)}
            assert left['operation_counts']==counts and counts['1']==294
            names=('flat2','group16','rle64')
            choice=min(range(3),key=lambda i:(left['candidate_body_bytes'][names[i]],i))
            assert choice==left['method'] and left['candidate_body_bytes']['flat2']==2025
            assert left['selected_body_bytes']==left['candidate_body_bytes'][names[choice]]
            assert left['header_bytes']==20 and left['total_bytes']==20+left['selected_body_bytes']<=2045
            assert right['fixed_hidden_mask_sha256']==v2['fixed_hidden_mask_sha256']
            assert right['total_bytes']==20+right['body_bytes']<=996
            if right['key']:
                assert right['method']==0 and right['body_bytes']==0
            else:
                assert right['method'] in (1,2) and right['body_bytes']<=976
                if right['method']==1:
                    assert right['body_bytes']==976
            assert right['v1_total_bytes']==left['total_bytes']
            assert right['saved_metadata_bytes']==left['total_bytes']-right['total_bytes']>=0
        assert index+1==457
    assert v1['selected_body_bytes']==stats([r['selected_body_bytes'] for r in a])
    assert v1['total_bytes']==stats([r['total_bytes'] for r in a])
    assert v1['method_counts']=={name:sum(r['method']==i for r in a) for i,name in enumerate(('flat2','group16','rle64'))}
    assert v2['body_bytes']==stats([r['body_bytes'] for r in b])
    assert v2['total_bytes']==stats([r['total_bytes'] for r in b])
    assert v2['saved_vs_v1_metadata_bytes']==stats([r['saved_metadata_bytes'] for r in b])
    assert v2['method_counts']=={name:sum(r['method']==i for r in b) for i,name in enumerate(('implicit_key','visible_bits','visible_RLE'))}
    assert v2['v1_total_bytes']==v1['total_bytes']['total'] and v2['keys']==20 and v2['deltas']==437
    assert v2['visible_count']==7806 and v2['body_cap']==976 and v2['packet_cap']==996
    unique_vectors=[]
    for version,records,rows in zip((1,2),vectors,row_sets):
        by_id={(r['cohort'],r['fid']):r for r in rows};seen=set()
        for vector in records:
            packet=bytes.fromhex(vector['packet_hex']);record=by_id[(vector['cohort'],vector['fid'])]
            digest=hashlib.sha256(packet).hexdigest()
            assert digest==record['encoded_sha256']
            expected=vector.get('packet_sha256',vector.get('encoded_sha256'));assert digest==expected
            decoded=metadata_packet(packet,hidden,version,record['key'])
            assert hashlib.sha256(decoded).hexdigest()==record['decoded_modes_sha256']
            seen.add(digest)
        unique_vectors.append(len(seen))
    saved=v2['saved_vs_v1_metadata_bytes']['total']
    return dict(status='PASS',reports_sha256=pins,frames=457,checks_per_version=28,
                v1_total_bytes=v1['total_bytes'],v2_total_bytes=v2['total_bytes'],
                saved_metadata_bytes=saved,reduction_of_metadata_percent=100*saved/v1['total_bytes']['total'],
                retained_vectors=[len(v) for v in vectors],unique_retained_packets=unique_vectors,
                all_mode_arrays_independently_tied_to_native_zero_masks=True,
                scope='Metadata only. No residual reencoding, complete stream savings, entropy skip, frame/reference binding or hardware/parser timing proof. Selected V2 protects header prefix plus body with CRC32; it is not authentication.')


def frontend_records(entropy_index):
    path=AREA/'frontend-audit.json';report=read(path)
    assert report['schema']=='cu66-v84-frontend-audit-v1' and report['status']=='PASS' and report['records']==457
    pins_current(report['source_sha256'])
    assert report['native_primitive_totals']==entropy_index['totals']
    for f in entropy_index['frames']:
        t=f['totals'];assert t['raw_bits']==t['renorm']+216
        assert (t['header_bytes'],t['prob_init'],t['emits'])==(84,1056,8100)
    for name,weights in (('LOW',LOW),('HIGH',HIGH)):
        values=[sum(f['totals'][k]*weights[k] for k in FIELDS)*1e-5 for f in entropy_index['frames']]
        actual=report['assumed_isolated_entropy_work'][name]
        expected=stats(values)
        assert actual['isolated_work_ms']=={k:expected[k] for k in ('min','median','max')}
        assert actual['frames']==457 and actual['clock_mhz_assumption']==100
        assert actual['frames_under_10ms']==sum(v<10 for v in values)
    for slots in (64,8,2):
        budget=report['logical_stage_allocation'][str(slots)]
        assert budget['v84_bytes']==4096+slots*384
        assert budget['v83_reference_plus_inverse_bytes']==4096+slots*256
        assert budget['v84_added_coefficient_reservation_bytes']==slots*128
    return dict(path=relative(path),sha256=sha(path),source_sha256=report['source_sha256'],
                assumed_isolated_entropy_work=report['assumed_isolated_entropy_work'],
                scope='Observed counters and formula audit; weighted clocks are assumptions, not measured or end-to-end timings.')


def capacities():
    return dict(memory=1,inverse=1,reconstruct=1,hash=1,tree_r=1,tree_w=1,map_r=1,map_w=1,entropy=1)


def check_row(row,native,entropy,control,old):
    config=CONFIG_BY_NAME[row['configuration']]
    assert (row['cohort'],row['ordinal'],row['fid'],row['key'])==(native['cohort'],native['ordinal'],native['fid'],native['key'])
    assert (row['root'],row['seal'])==(control['root'],control['seal'])
    assert row['native_entropy_totals']==entropy['totals']
    weights=config['weights']
    work_cycles=sum(entropy['totals'][f]*weights[f] for f in FIELDS) if weights else 0
    assert row['entropy_work_cycles']==work_cycles
    c=row['counts']
    expected=dict(reference_read_BL8=control['logical_BL8']['reference_reads'],
                  canonical_write_BL8=control['logical_BL8']['canonical_writes'],
                  HUD_read_BL8=control['logical_BL8']['HUD_reads'],HUD_write_BL8=control['logical_BL8']['HUD_writes'],
                  tree_r_words32=control['metadata']['tree_read_words32'],tree_w_words32=control['metadata']['tree_write_words32'],
                  map_r_entries=control['metadata']['map_read_entries'],map_w_entries=control['metadata']['map_write_entries'],
                  hash_compression_blocks=control['hash_compression_blocks'],tree_clone_nodes=control['metadata']['tree_clone_nodes'],
                  physical_store_tiles=control['physical_store_tiles'],resident_store_elisions=control['resident_store_elisions'])
    assert all(c.get(k,0)==v for k,v in expected.items())
    mode=dict(CONST128=control['const_tiles'],COPY_REF=control['copy_tiles'],RESIDUAL=8100-control['const_tiles']-control['copy_tiles'])
    assert {k:c['mode_tiles'].get(k,0) for k in mode}==mode and sum(c['mode_tiles'].values())==8100
    assert c.get('inverse_tiles',0)==c.get('reconstruct_tiles',0)==mode['RESIDUAL']
    assert c['groups']==508 and c['group_payload_buffer_bytes']==4096 and c['clone_temporary_bytes']==32
    assert 'group_starts' not in c and 'group_releases' not in c
    assert c['hash_cycles']==c['hash_compression_blocks']*64
    if config['slots']:
        assert c['entropy_tiles']==8100 and c['entropy_work_cycles']==work_cycles
        assert c['task_count']==old['counts']['task_count']+8100
    else:
        assert c=={k:v for k,v in old['counts'].items() if k not in ('group_starts','group_releases')}
        assert row['finish_cycles']==old['finish_cycles']
    audit=row['audit']
    assert audit['jobs']==c['task_count']
    assert type(row['finish_cycles']) is int and row['finish_cycles']>0
    assert audit['finish_cycles']==row['finish_cycles'] and row['model_ms']==row['finish_cycles']*1e-5
    work=dict(memory=(expected['reference_read_BL8']+2640)*config['read_gap']+(expected['canonical_write_BL8']+2640)*config['write_gap'],
              inverse=mode['RESIDUAL']*64,reconstruct=mode['RESIDUAL']*64,hash=c['hash_cycles'],
              tree_r=c['tree_r_words32'],tree_w=c['tree_w_words32'],map_r=c['map_r_entries'],map_w=c['map_w_entries'],entropy=work_cycles)
    assert audit['resource_work_cycles']=={k:v for k,v in work.items() if v}
    assert all(0<=peak<=capacities()[r] for r,peak in audit['resource_peak'].items())
    assert 0<audit['group_peak']<=4 and row['finish_cycles']>=max(work.values())
    assert re.fullmatch('[0-9a-f]{64}',row['timeline_sha256'])
    stage=row['staging']
    slots=config['slots']
    if not slots:
        assert stage is None
    else:
        expected_producers=dict(reference=expected['reference_read_BL8']//4,inverse=mode['RESIDUAL'],coefficient=8100)
        for name,size in (('reference',64),('inverse',192),('coefficient',128)):
            s=stage['stages'][name]
            assert s['capacity_slots']==slots and s['bytes_per_slot']==size
            assert 0<=s['peak_slots']<=slots and s['peak_bytes']==s['peak_slots']*size
            assert s['producers']==expected_producers[name]
        assert 0<=stage['output_peak_bytes']<=4096
        assert stage['conservative_logical_capacity_bytes']==4096+slots*384
        assert max(s['peak_bytes'] for s in stage['stages'].values())<=stage['combined_peak_bytes']<=stage['conservative_logical_capacity_bytes']


def expected_augmented(base,costs,slots):
    """Independent reconstruction of all admitted/credit edges from frozen V83."""
    jobs=copy.deepcopy(base['jobs']);by_id={j['id']:j for j in jobs}
    kinds={}
    for job in jobs:
        if 'tile' in job:
            kinds.setdefault(job['kind'],{})[job['tile']]=job
    next_id=max(by_id)+1
    entropy=[]
    for tile,duration in enumerate(costs):
        lookup=kinds['map_lookup'][tile];group=lookup['group']
        deps=[base['groups'][group]['start']]
        if entropy:
            deps.append(entropy[-1]['id'])
        j=dict(id=next_id,deps=sorted(set(deps)),resource='entropy',duration=duration,kind='entropy_tile',tile=tile,group=group)
        next_id+=1;jobs.append(j);entropy.append(j);by_id[j['id']]=j
        lookup['deps']=sorted(set(lookup['deps']+[j['id']]))
    for kind in ('reference_read','inverse','entropy_tile'):
        producers=entropy if kind=='entropy_tile' else sorted(kinds.get(kind,{}).values(),key=lambda j:j['tile'])
        consumers=[]
        for i,j in enumerate(producers):
            t=j['tile']
            consumer=(kinds['inverse'].get(t,kinds['map_lookup'][t]) if kind=='entropy_tile' else
                      kinds['reconstruct'].get(t,kinds.get('copy_ready',{}).get(t)))
            assert consumer is not None
            consumers.append(consumer)
            if i>=slots:
                j['deps']=sorted(set(j['deps']+[consumers[i-slots]['id']]))
    by_id[base['complete']]['deps']=sorted(set(by_id[base['complete']]['deps']+[entropy[-1]['id']]))
    return jobs


def witness_check(path,rows,observed,old_summary,generic,auditor):
    match=re.fullmatch(r'witness-c0-f([01])-(credits8_primitive_low|credits2_zero_arrival)\.json\.gz',path.name)
    assert match
    fid=int(match[1]);config=CONFIG_BY_NAME[match[2]];row=rows[(0,fid,config['name'])]
    with gzip.open(path,'rt') as f:
        witness=json.load(f)
    assert witness['config']==config and witness['capacities']==capacities()
    base_record=next(w for w in old_summary['independently_reaudited_witnesses']
                     if Path(w['path']).name==f'witness-c0-f{fid}-bounded_groups_current.json.gz')
    base_path=local(base_record['path']);assert sha(base_path)==base_record['sha256']
    with gzip.open(base_path,'rt') as f:
        base=json.load(f)['workload']
    costs=[sum(t[k]*v for k,v in config['weights'].items()) for t in observed[fid]['tile_work']] if config['weights'] else [0]*8100
    work=witness['workload'];result=witness['result'];timeline=result['timeline']
    assert work['jobs']==expected_augmented(base,costs,config['slots'])
    assert work['groups']==base['groups'] and work['complete']==base['complete']
    counts={k:v for k,v in work['counts'].items() if k not in ('group_starts','group_releases')}
    assert counts==row['counts']
    checked=generic.verify(work['jobs'],timeline,capacities(),config['windows'],work['groups'],4)
    assert checked==witness['audit']==row['audit']
    life=auditor.verify(work,timeline,ref_slots=config['slots'],inverse_slots=config['slots'],coefficient_slots=config['slots'])
    assert life==witness['staging']==row['staging']
    by_id={r['id']:r for r in timeline}
    assert result['finish_by_id']=={str(i):r['finish'] for i,r in by_id.items()}
    assert by_id[work['complete']]['finish']==result['finish_cycles']==row['finish_cycles']
    digest=hashlib.sha256(json.dumps(timeline,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest==row['timeline_sha256']
    assert result['physical_timing_proven'] is False
    for resource,r in result['resources'].items():
        assert r['work_cycles']==checked['resource_work_cycles'].get(resource,0)
        assert r['max_active']==checked['resource_peak'].get(resource,0) or r['work_cycles']==0
    return dict(path=relative(path),sha256=sha(path),jobs=len(work['jobs']),finish_cycles=row['finish_cycles'],
                old_workload_path=relative(base_path),old_workload_sha256=sha(base_path),
                exact_augmented_DAG_reconstructed=True,independently_reaudited=True)


def verify(session_path):
    session_path=local(session_path)
    if session_path.is_dir():
        session_path/='results.json'
    session=read(session_path)
    assert session['schema']=='cu66-v84-parallel-session-v1' and session['status']=='PASS'
    assert session['runner_sha256']==sha(ROOT/'scripts/cu66-v84/run_campaign.py')
    assert len(session['cohorts'])==4 and [r['cohort'] for r in session['cohorts']]==list(range(4))
    tests=test_records();entropy_index,entropy_summary=entropy_records()
    native_index=read(NATIVE);native={(f['cohort'],f['fid']):f for f in native_index['frames']}
    entropies={(f['cohort'],f['fid']):f for f in entropy_index['frames']}
    controls={(f['cohort'],f['fid']):f for f in map(json.loads,CONTROL.read_text().splitlines())}
    assert len(native)==len(entropies)==len(controls)==457 and native.keys()==entropies.keys()==controls.keys()
    for identity,f in native.items():
        for name in ('cohort','ordinal','fid','key','packet_sha256','canonical_sha256','hud_sha256','display_sha256'):
            assert f[name]==entropies[identity][name]
    metadata=metadata_records(native,entropy_index)
    frontend=frontend_records(entropy_index)
    old_summary=read(V83);assert old_summary['status']=='PASS_CONDITIONAL_MODEL_EVIDENCE'
    old_rows={};old_paths=[]
    for name,digest in old_summary['evidence_sha256'].items():
        if name.endswith('/results.json'):
            report=local(name);assert sha(report)==digest
            path=report.with_name('frames.jsonl');old_paths.append(path)
            assert sha(path)==read(report)['artifacts_sha256']['frames.jsonl']
            for line in path.read_text().splitlines():
                r=json.loads(line)
                if r['configuration']=='bounded_groups_current_hash1':
                    old_rows[(r['cohort'],r['fid'])]=r
    assert old_rows.keys()==native.keys()
    expected_sources={
        'scripts/cu66-v84/prototype_pipeline.py','experiments/python-gamebub-v84/audit.py','experiments/python-gamebub-v84/credits.py',
        'experiments/python-gamebub-v83/workload.py','experiments/python-gamebub-v83/scheduler.py','experiments/python-gamebub-v83/audit.py',
        'scripts/cu66-v82/prototype_commitment.py','experiments/python-gamebub-v82/execution.py',
        'fpga/experiments/cu66-v81/residency/model.py','experiments/python-gamebub-v82/native/data.py',relative(NATIVE),
        'experiments/python-gamebub-v84/entropy/data.py','experiments/python-gamebub-v84/entropy/index.json',
        relative(ENTROPY/entropy_index['data']['path']),relative(CONTROL),relative(V83),*(relative(p) for p in old_paths)}
    chunk_pins={relative(NATIVE.parent/c['path']):c['gzip_sha256'] for c in native_index['chunks']}
    expected_sources.update(chunk_pins)
    all_rows={};all_pins=None;artifact_pins={};witness_paths=[]
    for record in session['cohorts']:
        cohort=record['cohort'];assert record['exit_code']==0
        assert record['command'][1:]==['scripts/cu66-v84/prototype_pipeline.py','--cohort',str(cohort)]
        log=local(record['log']);assert log.parent==session_path.parent and log.name==f'cohort{cohort}.log'
        assert sha(log)==record['log_sha256']
        report_path=local(record['report']);report=read(report_path)
        assert report['schema']=='cu66-v84-entropy-credit-campaign-v1' and report['status']=='PASS_CONDITIONAL_COHORT_SCHEDULES'
        assert report['cohort']==cohort and report['smoke_limit']==0 and report['configurations']==CONFIGS
        assert report['native_sources']==COHORTS[cohort] and report['schedules']==COHORTS[cohort]*8
        assert report['clock_mhz_assumption']==100 and report['timing_is_physical'] is report['rtl_changed'] is report['esp32_simulated'] is False
        assert log.read_text().splitlines()[-1]==f"V84_PIPELINE_REPORT {report_path} {report['status']}"
        pins=report['source_sha256'];assert pins.keys()==expected_sources
        pins_current(pins);assert all(pins[k]==v for k,v in chunk_pins.items())
        if all_pins is None:
            all_pins=pins
        assert pins==all_pins
        archive=report_path.with_name('sources.tar.gz');assert sha(archive)==report['source_archive_sha256']
        with tarfile.open(archive,'r:gz') as tar:
            members=tar.getmembers();expected={name for name in pins if not name.endswith('.gz')}
            assert len(members)==len(expected) and {m.name for m in members}==expected
            for member in members:
                assert member.isfile() and hashlib.sha256(tar.extractfile(member).read()).hexdigest()==pins[member.name]
        artifacts=report['artifacts_sha256']
        actual={p.name for p in report_path.parent.iterdir() if p.is_file() and p.name!='results.json'}
        expected_witness={f'witness-c0-f{fid}-{config}.json.gz' for fid in (0,1)
                          for config in ('credits8_primitive_low','credits2_zero_arrival')} if cohort==0 else set()
        assert actual==artifacts.keys()=={'sources.tar.gz','frames.jsonl'}|expected_witness
        for name,digest in artifacts.items():
            assert Path(name).name==name and sha(report_path.parent/name)==digest
        cohort_rows=[json.loads(line) for line in report_path.with_name('frames.jsonl').read_text().splitlines()]
        assert len(cohort_rows)==COHORTS[cohort]*8
        seen=set()
        for row in cohort_rows:
            key=(row['cohort'],row['fid'],row['configuration']);identity=key[:2]
            assert key not in seen and key not in all_rows and key[0]==cohort and identity in native
            check_row(row,native[identity],entropies[identity],controls[identity],old_rows[identity])
            seen.add(key);all_rows[key]=row
        assert seen=={(c,f,config['name']) for c,f in native if c==cohort for config in CONFIGS}
        assert report['summaries']==summarize(cohort_rows)
        for p in (report_path,log):
            artifact_pins[relative(p)]=sha(p)
        witness_paths.extend(report_path.parent/name for name in sorted(expected_witness))
    assert len(all_rows)==3656 and len(witness_paths)==4
    loader=module('cu84_verify_native_entropy',ENTROPY/'data.py')
    observations={}
    for i,frame in enumerate(loader.iter_frames()):
        if i==2:
            break
        assert frame['cohort']==0
        observations[frame['fid']]=frame
    generic=module('cu84_verify_generic_audit',ROOT/'experiments/python-gamebub-v83/audit.py')
    auditor=module('cu84_verify_credit_audit',AREA/'audit.py')
    witnesses=[witness_check(path,all_rows,observations,old_summary,generic,auditor) for path in witness_paths]
    ordered=[all_rows[(f['cohort'],f['fid'],c['name'])] for f in native_index['frames'] for c in CONFIGS]
    peaks={}
    for config in CONFIGS:
        if config['slots']:
            chosen=[r for r in ordered if r['configuration']==config['name']]
            peaks[config['name']]=dict(capacity_slots=config['slots'],
                static_logical_capacity_bytes=4096+config['slots']*384,
                maximum_combined_reserved_bytes=max(r['staging']['combined_peak_bytes'] for r in chosen),
                maximum_slots={name:max(r['staging']['stages'][name]['peak_slots'] for r in chosen)
                               for name in ('reference','inverse','coefficient')})
    zero_deltas=[all_rows[(f['cohort'],f['fid'],'credits64_zero_arrival')]['finish_cycles']-
                 all_rows[(f['cohort'],f['fid'],'v83_control')]['finish_cycles'] for f in native_index['frames']]
    zero_comparison=dict(equal=sum(v==0 for v in zero_deltas),faster=sum(v<0 for v in zero_deltas),
                         slower=sum(v>0 for v in zero_deltas),paired_cycles_delta=stats(zero_deltas),
                         scope='Measured within conditional schedules; zero-arrival equality is checked as a result, not assumed.')
    pins_current(all_pins)
    return dict(schema='cu66-v84-evidence-summary-v1',status='PASS_CONDITIONAL_MODEL_EVIDENCE',
                session=relative(session_path),session_sha256=sha(session_path),verifier_sha256=sha(Path(__file__)),
                native_sources=457,cohorts=list(COHORTS),schedules=3656,keys=20,deltas=437,configurations=CONFIGS,
                source_sha256=all_pins,test_reports_sha256=tests,evidence_sha256=artifact_pins,
                credits_checks=557,audit_checks=9,native_entropy=entropy_summary,
                operation_metadata=metadata,frontend_assumption_audit=frontend,
                independently_reaudited_witnesses=witnesses,staging_highwaters=peaks,
                zero64_control_comparison=zero_comparison,
                summaries=summarize(ordered),physical_timing_proven=False,sustained_30fps_proven=False,
                validated_under10ms_proven=False,esp32_simulated=False,
                scope=['All 3,656 rows checked against native/V82 identities, work counts, native entropy primitive totals, frozen V83 baseline and source/log/archive pins.',
                       'Four full augmented DAGs independently rebuilt from frozen V83 witnesses and actual per-tile native primitive records, then timeline/lifetime reaudited.',
                       'Remaining 3,652 timelines were producer-audited; only hashes and summaries retained.',
                       'Native primitive counts are observations; LOW/HIGH cycle weights and 64-cycle compute costs are conditional assumptions, not physical timing bounds.',
                       'Finite staging lifetimes cover reference/inverse/coefficients/group output only; RAM ports, dequant working state, descriptors/transport and CDC unpriced.',
                       'Per-source fixed reservation phase; no continuous scanout/refresh or sustained distinct-source 30-fps qualification.',
                       'No new wire format, ESP32 throughput, target fit or HEVC/AV1 quality/bitrate superiority proof.'])


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--session',required=True)
    p.add_argument('--output',default='experiments/python-gamebub-v84/summary.json')
    p.add_argument('--verify-summary',action='store_true')
    args=p.parse_args();result=verify(args.session);dest=local(args.output)
    if args.verify_summary:
        assert read(dest)==result,'retained summary differs from recomputed evidence'
    else:
        with dest.open('x') as stream:
            stream.write(json.dumps(result,indent=2)+'\n')
    print('V84_EVIDENCE_PASS sources=457 schedules=3656 witnesses=4 credits=557 audit=9')
    print('V84_SUMMARY',dest)


if __name__=='__main__':
    main()
