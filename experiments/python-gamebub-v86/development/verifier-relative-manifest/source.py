#!/usr/bin/env python3
"""Independently reconstruct CS86 bytes and audit native/model evidence scopes."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re,statistics,struct,sys,tarfile,zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v86'
OLD=ROOT/'experiments/python-gamebub-v85'
CAPS=(256,65536)
KINDS=('copy_v2','copy_group','all_visible')
CONFIGS=[dict(name=f'{kind}_cap{cap}',kind=kind,cap=cap) for cap in CAPS for kind in KINDS]
C2=ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
MASK='e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5'


def local(name):
    p=Path(name);p=p.resolve() if p.is_absolute() else (ROOT/p).resolve();p.relative_to(ROOT);return p
def relative(name):return str(local(name).relative_to(ROOT))
def sha(path):return hashlib.sha256(local(path).read_bytes()).hexdigest()
def read(path):return json.loads(local(path).read_text())
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))
def module(name,path):
    s=importlib.util.spec_from_file_location(name,local(path));m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def pins_current(pins):
    for name,digest in pins.items():
        assert re.fullmatch('[0-9a-f]{64}',digest) and sha(name)==digest,('pin mismatch',name)
def archive_matches(path,pins):
    with tarfile.open(local(path),'r:gz') as tar:
        expected={n for n in pins if not n.endswith('.gz')};members=tar.getmembers()
        assert len(members)==len(expected) and {m.name for m in members}==expected
        for item in members:
            assert item.isfile() and hashlib.sha256(tar.extractfile(item).read()).hexdigest()==pins[item.name]
def manifest(path):
    d=read(path);pins_current(d['files_sha256']);return dict(path=relative(path),sha256=sha(path),files=len(d['files_sha256']))
def report_artifacts(path,report):
    path=local(path)
    actual={p.name for p in path.parent.iterdir() if p.is_file() and p.name!='results.json'}
    assert actual==report['artifacts_sha256'].keys()
    for name,digest in report['artifacts_sha256'].items():assert Path(name).name==name and sha(path.parent/name)==digest


def map_body(frame,hidden,kind):
    """Independent encoder of the specified grammar, not a producer import."""
    operations=[1 if h else 0 if kind!='all_visible' and not frame['key'] and frame['zero_mask'][i]=='1' else 2
                for i,h in enumerate(hidden)]
    if frame['key']:return 0,b'',bytes(operations)
    visible=[int(op==2) for op,h in zip(operations,hidden) if not h];assert len(visible)==7806
    bitset=bytearray(976)
    for i,v in enumerate(visible):bitset[i//8]|=v<<(7-i%8)
    runs=bytearray();at=0
    while at<7806:
        end=at+1
        while end<7806 and visible[end]==visible[at] and end-at<128:end+=1
        runs.append((visible[at]<<7)|(end-at-1));at=end
    candidates=[(1,bytes(bitset)),(2,bytes(runs))]
    if kind!='copy_v2':
        packed=[];offset=0
        for total in (5400,1350,1350):
            for start in range(0,total,16):
                values=[int(operations[i]==2) for i in range(offset+start,offset+min(start+16,total)) if not hidden[i]]
                tag=3 if not values else 0 if not any(values) else 1 if all(values) else 2
                packed.extend((tag>>1,tag&1))
                if tag==2:packed.extend(values)
            offset+=total
        packed.extend([0]*((-len(packed))%8))
        group=bytes(sum(packed[i+j]<<(7-j) for j in range(8)) for i in range(0,len(packed),8))
        candidates.append((3,group))
    method,body=min(candidates,key=lambda item:(len(item[1]),item[0]));assert len(body)<=976
    return method,body,bytes(operations)


def parse_map(method,body,key,hidden):
    assert method in (0,1,2,3) and len(body)<=976
    if key:
        assert method==0 and not body;return bytes(1 if h else 2 for h in hidden)
    assert method!=0
    if method==1:
        assert len(body)==976 and body[-1]&3==0
        visible=[(body[i//8]>>(7-i%8))&1 for i in range(7806)]
    elif method==2:
        visible=[]
        for token in body:
            visible.extend([token>>7]*((token&127)+1));assert len(visible)<=7806
        assert len(visible)==7806
    else:
        cursor=0;values=bytearray([1 if h else 255 for h in hidden]);offset=0
        def bit():
            nonlocal cursor
            assert cursor<len(body)*8,'group bit bound'
            value=(body[cursor//8]>>(7-cursor%8))&1;cursor+=1;return value
        for total in (5400,1350,1350):
            for start in range(0,total,16):
                indexes=[i for i in range(offset+start,offset+min(start+16,total)) if not hidden[i]]
                tag=(bit()<<1)|bit()
                if not indexes:assert tag==3;continue
                assert tag!=3
                bits=[0]*len(indexes) if tag==0 else [1]*len(indexes) if tag==1 else [bit() for _ in indexes]
                if tag==2:assert any(bits) and not all(bits)
                for index,value in zip(indexes,bits):values[index]=2 if value else 0
            offset+=total
        remaining=len(body)*8-cursor;assert 0<=remaining<8
        assert all(bit()==0 for _ in range(remaining)) and 255 not in values
        return bytes(values)
    cursor=0;out=[]
    for h in hidden:
        out.append(1 if h else 2 if visible[cursor] else 0)
        if not h:cursor+=1
    assert cursor==7806;return bytes(out)


def reconstruct_packet(frame,cap,kind,hidden,control):
    method,mode,operations=map_body(frame,hidden,kind);stream=bytearray();ab=chunks=0
    for plane in frame['variants'][str(cap)]:
        stream.extend(len(plane).to_bytes(4,'big'))
        for chunk in plane:
            stream.extend(chunk['blocks'].to_bytes(4,'big'));stream.extend(len(chunk['data']).to_bytes(4,'big'));stream.extend(chunk['data'])
            ab+=len(chunk['data']);chunks+=1
    # This field assembly deliberately does not call the producer frame_packet.
    prefix=(b'CS86'+bytes((1,int(frame['key']),16,method))+frame['fid'].to_bytes(4,'big')+
            frame['refid'].to_bytes(4,'big')+(frame['ordinal']+1).to_bytes(8,'big')+
            struct.pack('>4H',720,480,frame['block_size'],0)+struct.pack('>5I',cap,len(mode),338,len(frame['hud']),len(stream)))
    assert len(prefix)==52
    body=prefix+bytes.fromhex(control['root'])+bytes.fromhex(control['seal'])+bytes(12)+mode+frame['qmap']+stream+frame['hud']
    packet=body+zlib.crc32(body).to_bytes(4,'big')
    counts=dict(header=128,mode_body=len(mode),qmap=338,chunk_directory=12+8*chunks,AB38_payloads=ab,HUD=len(frame['hud']),outer_CRC=4)
    assert sum(counts.values())==len(packet)
    return packet,counts,method,operations


def parse_wire(packet,frame,hidden,ab38):
    assert 132<=len(packet)<=2097152 and zlib.crc32(packet[:-4])==int.from_bytes(packet[-4:],'big')
    magic,version,key,group,method=struct.unpack_from('>4sBBBB',packet)
    assert (magic,version,key,group)==(b'CS86',1,int(frame['key']),16)
    fid,refid,generation=struct.unpack_from('>IIQ',packet,8)
    assert (fid,refid,generation)==(frame['fid'],frame['refid'],frame['ordinal']+1)
    assert struct.unpack_from('>4H',packet,24)==(720,480,frame['block_size'],0)
    cap,map_n,q_n,hud_n,data_n=struct.unpack_from('>5I',packet,32)
    assert cap in CAPS and map_n<=976 and q_n==338 and 110<=hud_n<=49152
    assert len(packet)==128+map_n+q_n+data_n+hud_n+4 and packet[116:128]==bytes(12)
    pos=128;operations=parse_map(method,packet[pos:pos+map_n],bool(key),hidden);pos+=map_n
    quant=packet[pos:pos+338];pos+=338
    q=[(quant[i//4]>>(6-2*(i%4)))&3 for i in range(1352)]
    assert all(x<=2 for x in q[:1350]) and q[1350:]==[0,0]
    start=pos;chunks=ab=0
    for low,high in ((0,5400),(5400,6750),(6750,8100)):
        needed=sum(op==2 for op in operations[low:high]);count=int.from_bytes(packet[pos:pos+4],'big');pos+=4
        assert count==(needed+cap-1)//cap
        for i in range(count):
            blocks,length=struct.unpack_from('>II',packet,pos);pos+=8
            assert blocks==min(cap,needed-i*cap) and blocks>0
            chunk=packet[pos:pos+length];assert len(chunk)==length;ab38(chunk,blocks)
            pos+=length;chunks+=1;ab+=length
    assert pos-start==data_n
    hud=packet[pos:pos+hud_n];pos+=hud_n
    assert len(hud)==hud_n and hud[:4] in (b'HU25',b'HX32',b'HX33') and hud[4:6]==b'\x01\x04'
    assert struct.unpack_from('<IIIHH',hud,6)==(25,fid,refid,720,480)
    assert zlib.crc32(hud[:-4])==int.from_bytes(hud[-4:],'little') and pos==len(packet)-4
    counts=dict(header=128,mode_body=map_n,qmap=338,chunk_directory=12+8*chunks,AB38_payloads=ab,HUD=hud_n,outer_CRC=4)
    assert sum(counts.values())==len(packet)
    return dict(cap=cap,method=method,components=counts,root=packet[52:84].hex(),seal=packet[84:116].hex())


def scopes():
    result=[]
    for base in (AREA/'maps',AREA/'controls',OLD/'residual'):
        result.append(manifest(base/'artifact-manifest.json'))
    for base in (AREA/'controls',OLD/'residual'):
        index=read(base/'index.json');assert index['record_count']==457 and index['cohort_counts']==[119,119,119,100]
        pins_current(index['source_sha256']);assert sha(base/index['data']['path'])==index['data']['gzip_sha256']
        attempt=base/index['data']['path'];r=read(attempt.parent/'results.json');assert r['status']=='PASS' and r['records']==457
        assert sha(attempt.parent/'sources.tar.gz')==r['source_archive_sha256'];archive_matches(attempt.parent/'sources.tar.gz',r['source_sha256'])
        audit=read(base/'verification.json');assert audit['status']=='PASS' and audit['records']==457;pins_current(audit['source_sha256'])
    maps=read(AREA/'maps/results.json');assert maps['status']=='PASS' and maps['sources']==457 and maps['body_limit']==976
    pins_current(maps['source_sha256'])
    for name,digest in maps['artifacts_sha256'].items():assert sha(AREA/'maps'/name)==digest
    tests=read(AREA/'maps/tests.json');assert tests['status']=='PASS' and tests['checks']==len(tests['cases'])==maps['checks']==27
    assert all(c['status'] in ('PASS','PASS_REJECT') for c in tests['cases'])
    return result,maps


def verify_context(session_path):
    area=AREA/'contexts';session_path=local(session_path)
    if session_path.is_dir():session_path/='results.json'
    session=read(session_path);audit=read(area/'model-verification.json');index=read(area/'index.json');native=read(area/'verification.json')
    assert session['status']==audit['status']==native['status']=='PASS'
    assert index['native_sources']==native['native_sources']==audit['native_sources']==457
    assert index['record_count']==native['variant_records']==audit['variant_records']==914
    assert audit['schedules']==5484 and audit['synthetic_checks']==session['synthetic_checks']==18
    assert local(audit['session'])==session_path and sha(session_path)==audit['session_sha256']
    assert native['index_sha256']==sha(area/'index.json') and native['data_sha256']==sha(area/index['data']['path'])
    pins_current(index['source_sha256']);pins_current(audit['source_sha256']);pins_current(session['source_sha256'])
    assert native['verifier_sha256']==sha(area/'verify.py')
    records=session['cohorts'];assert len(records)==4 and [r['cohort'] for r in records]==list(range(4))
    rows=[];pins=None
    for record in records:
        assert record['exit_code']==0 and sha(record['log'])==record['log_sha256']
        path=local(record['report']);r=read(path)
        assert r['status']=='PASS_FULL_COHORT_REENCODED_FRONT_MODEL' and r['cohort']==record['cohort']
        assert r['full_corpus_scheduling'] is True and r['physical_timing_proven'] is False and r['limit_records']==0
        pins_current(r['source_sha256']);assert pins is None or pins==r['source_sha256'];pins=r['source_sha256']
        assert sha(path.parent/'sources.tar.gz')==r['source_archive_sha256'];archive_matches(path.parent/'sources.tar.gz',r['source_sha256'])
        report_artifacts(path,r);rows += [json.loads(line) for line in (path.parent/'rows.jsonl').read_text().splitlines()]
    keyed={(r['cap'],r['cohort'],r['fid'],r['cost'],r['lanes']):r for r in rows};assert len(rows)==len(keyed)==5484
    sources={(r['cohort'],r['fid']) for r in read(ROOT/'experiments/python-gamebub-v82/native/index.json')['frames']}
    assert keyed.keys()=={(cap,*key,cost,lanes) for cap in CAPS for key in sources for cost in ('LOW','HIGH') for lanes in (1,2,4)}
    summaries=[]
    for cap in CAPS:
        for cost in ('LOW','HIGH'):
            for lanes in (1,2,4):
                selected=[r for r in rows if (r['cap'],r['cost'],r['lanes'])==(cap,cost,lanes)]
                summaries.append(dict(cap=cap,cost=cost,window=8,lanes=lanes,sources=457,model_ms=stats([r['model_ms'] for r in selected]),conditional_front_under10ms=sum(r['finish_cycles']<1000000 for r in selected)))
    assert summaries==audit['summaries'] and len(audit['independently_reconstructed_witnesses'])==4
    for witness in audit['independently_reconstructed_witnesses']:assert sha(witness['path'])==witness['sha256']
    artifact=manifest(area/'artifact-manifest.json')
    return dict(index_sha256=sha(area/'index.json'),native_verification_sha256=sha(area/'verification.json'),
                audit_sha256=sha(area/'model-verification.json'),session=relative(session_path),session_sha256=sha(session_path),
                native_sources=457,variant_records=914,schedules=5484,synthetic_checks=18,summaries=summaries,
                independently_reconstructed_witnesses=audit['independently_reconstructed_witnesses'],manifest=artifact,
                scope='Full corpus on the actual re-encoded residual streams under standalone prospective frontend costs; map/outer parsing, HUD, reconstruction, memory/display and ESP32 excluded. No FPGA timing proof.')


def comparison(reference,candidate):
    assert reference.keys()==candidate.keys()
    deltas=[reference[k]['wire_bytes']-candidate[k]['wire_bytes'] for k in sorted(reference)]
    total=sum(reference[k]['wire_bytes'] for k in reference)
    return dict(sources=len(deltas),saved_bytes=stats(deltas),improved=sum(v>0 for v in deltas),equal=sum(v==0 for v in deltas),regressed=sum(v<0 for v in deltas),percent_saved=100*sum(deltas)/total)


def verify(wire_path,protocol_path,context_session):
    wire_path=local(wire_path);r=read(wire_path)
    assert r['schema']=='cu66-v86-full-wire-v1' and r['status']=='PASS_NATIVE_FULL_FRAME_PARITY'
    assert r['smoke_limit']==0 and r['sources']==457 and r['received_packets']==2742 and r['configurations']==CONFIGS
    assert r['receiver_exit_codes']=={c['name']:0 for c in CONFIGS}
    assert r['research_packet_limit']==2097152 and r['compatibility_packet_limit']==49152 and r['timing_is_FPGA'] is False
    pins_current(r['source_sha256']);archive_matches(wire_path.parent/'sources.tar.gz',r['source_sha256'])
    assert sha(wire_path.parent/'sources.tar.gz')==r['source_archive_sha256'];report_artifacts(wire_path,r)
    manifests,map_result=scopes()
    native_index=read(ROOT/'experiments/python-gamebub-v82/native/index.json');expected={(f['cohort'],f['fid']):f for f in native_index['frames']};assert len(expected)==457
    c2={(v['cohort'],v['fid']):v for v in map(json.loads,C2.read_text().splitlines())}
    rows=[json.loads(s) for s in (wire_path.parent/'frames.jsonl').read_text().splitlines()]
    keyed={(v['cohort'],v['fid'],v['configuration']):v for v in rows}
    assert len(rows)==len(keyed)==2742 and keyed.keys()=={(*key,c['name']) for key in expected for c in CONFIGS}
    residual=module('cu86_audit_residual',OLD/'residual/data.py');controls=module('cu86_audit_controls',AREA/'controls/data.py');native=module('cu86_audit_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    legacy=module('cu86_audit_frozen_ab38',ROOT/'scripts/cu66-v85/verify_evidence.py')
    map_rows={(v['cohort'],v['fid']):v for v in map(json.loads,(AREA/'maps/frames.jsonl').read_text().splitlines())}
    assert len(map_rows)==457
    fixtures={};count=0;group_lengths=[];old_lengths=[];savings=[];method_counts={str(i):0 for i in range(4)};native_operations={};hidden=None
    for frame,all_visible,original in zip(residual.iter_frames(),controls.iter_frames(),native.iter_frames(),strict=True):
        key=frame['cohort'],frame['fid'];source=expected[key];control=c2[key];hidden=original['hidden_mask']
        assert hashlib.sha256(hidden).hexdigest()==MASK
        for name in ('cohort','ordinal','fid','refid','key','packet_bytes','packet_sha256','canonical_sha256','hud_sha256','display_sha256'):
            assert frame[name]==all_visible[name]==source[name]
        assert frame['qmap']==all_visible['qmap'] and frame['hud']==all_visible['hud']
        assert hashlib.sha256(frame['hud']).hexdigest()==source['encoded_hud_sha256']
        assert frame['canonical_coefficients_sha256']==all_visible['canonical_coefficients_sha256']
        assert frame['zero_mask']==all_visible['zero_mask']==''.join(str(x) for x in original['zero_coeff_mask'])
        group_method,group_body,operations=map_body(frame,hidden,'copy_group');v2_method,v2_body,_=map_body(frame,hidden,'copy_v2')
        selected=map_rows[key];assert selected['method']==group_method and selected['body_bytes']==len(group_body)
        assert selected['old_method']==v2_method and selected['old_body_bytes']==len(v2_body)
        assert selected['saved_bytes']==len(v2_body)-len(group_body)
        assert selected['modes_sha256']==hashlib.sha256(operations).hexdigest()
        assert selected['body_sha256']==hashlib.sha256(group_body).hexdigest()
        assert parse_map(group_method,group_body,frame['key'],hidden)==operations
        group_lengths.append(len(group_body));old_lengths.append(len(v2_body));savings.append(len(v2_body)-len(group_body));method_counts[str(group_method)]+=1
        native_operations[key]=(frame['key'],operations)
        for config in CONFIGS:
            chosen=all_visible if config['kind']=='all_visible' else frame
            packet,counts,method,ops=reconstruct_packet(chosen,config['cap'],config['kind'],hidden,control)
            row=keyed[(*key,config['name'])]
            assert (row['kind'],row['cap'],row['map_method'],row['ordinal'],row['key'])==(config['kind'],config['cap'],method,frame['ordinal'],frame['key'])
            assert row['components']==counts and row['wire_bytes']==len(packet) and row['packet_sha256']==hashlib.sha256(packet).hexdigest()
            assert row['original_packet_bytes']==source['packet_bytes'] and row['byte_delta']==len(packet)-source['packet_bytes'] and row['fits_49152']==(len(packet)<=49152)
            d=row['decoded'];assert d['accepted'] is True and d['replayed'] is False and d['fid']==frame['fid'] and d['generation']==frame['ordinal']+1 and d['wire_bytes']==len(packet)
            assert d['coefficient_sha256']==frame['canonical_coefficients_sha256']
            assert all(d[name]==source[name] for name in ('canonical_sha256','hud_sha256','display_sha256'))
            assert d['root']==control['root'] and d['seal']==control['seal']
            if ((frame['cohort'] in (0,3) and frame['ordinal'] in (0,1)) or (frame['cohort']==3 and frame['fid']==50)) and config['kind']=='copy_group':
                fixtures[f'c{frame["cohort"]}-f{frame["fid"]}-{config["name"]}.cs86']=(packet,frame,row)
        count+=1
    assert count==457
    assert map_result['body_bytes']==stats(group_lengths) and map_result['old_body_bytes']==stats(old_lengths) and map_result['saved_body_bytes']==stats(savings) and map_result['method_counts']==method_counts
    vectors=read(AREA/'maps/vectors.json');assert vectors['fixed_hidden_mask_sha256']==MASK and len(vectors['vectors'])==map_result['vectors']==4
    for vector in vectors['vectors']:
        output=parse_map(vector['method'],bytes.fromhex(vector['body_hex']),vector['key'],hidden)
        assert hashlib.sha256(output).hexdigest()==vector['modes_sha256']
        if 'cohort' in vector:assert (vector['key'],output)==native_operations[(vector['cohort'],vector['fid'])]
    assert {p.name for p in wire_path.parent.glob('*.cs86')}==fixtures.keys() and len(fixtures)==10
    parsed=[]
    for name,(packet,frame,row) in sorted(fixtures.items()):
        path=wire_path.parent/name;assert path.read_bytes()==packet
        result=parse_wire(packet,frame,hidden,legacy.check_ab38)
        assert result['cap']==row['cap'] and result['method']==row['map_method'] and result['components']==row['components']
        assert result['root']==row['decoded']['root'] and result['seal']==row['decoded']['seal']
        parsed.append(dict(path=relative(path),sha256=sha(path),bytes=len(packet),independent_structural_parse=True))
    summaries=[]
    for config in CONFIGS:
        chosen=[v for v in rows if v['configuration']==config['name']]
        summaries.append(dict(configuration=config['name'],kind=config['kind'],cap=config['cap'],sources=457,
                              wire_bytes=stats([v['wire_bytes'] for v in chosen]),original_packet_bytes=stats([v['original_packet_bytes'] for v in chosen]),
                              paired_byte_delta=stats([v['byte_delta'] for v in chosen]),smaller=sum(v['byte_delta']<0 for v in chosen),equal=sum(v['byte_delta']==0 for v in chosen),
                              larger=sum(v['byte_delta']>0 for v in chosen),fits_49152=sum(v['fits_49152'] for v in chosen)))
    assert summaries==r['summaries']
    old_report=read(OLD/'wire-attempts/20261106T130658877580Z-53860fda/results.json')
    old_rows=[json.loads(s) for s in (OLD/'wire-attempts/20261106T130658877580Z-53860fda/frames.jsonl').read_text().splitlines()]
    old_lookup={(v['cohort'],v['fid'],v['cap']):v for v in old_rows}
    paired=[]
    for cap in CAPS:
        by_kind={kind:{key:keyed[(*key,f'{kind}_cap{cap}')] for key in expected} for kind in KINDS}
        for reference,candidate in (('copy_v2','copy_group'),('all_visible','copy_group')):
            paired.append(dict(reference=f'{reference}_cap{cap}',candidate=f'copy_group_cap{cap}',**comparison(by_kind[reference],by_kind[candidate])))
        baseline={key:old_lookup[(*key,cap)] for key in expected}
        assert all(baseline[key]['wire_bytes']-by_kind['copy_v2'][key]['wire_bytes']==148 for key in expected)
        paired.append(dict(reference=f'V85_CS85_cap{cap}',candidate=f'copy_group_cap{cap}',**comparison(baseline,by_kind['copy_group'])))
    contexts=verify_context(context_session)
    protocol=verify_protocol(protocol_path,r,keyed,wire_path)
    return dict(schema='cu66-v86-combined-evidence-v1',status='PASS_NATIVE_COMPACT_WIRE_AND_REENCODED_FRONT_EVIDENCE',
                wire_report=relative(wire_path),wire_report_sha256=sha(wire_path),verifier_sha256=sha(Path(__file__)),
                native_sources=457,cohorts=[119,119,119,100],native_wire_packets=2742,configurations=CONFIGS,
                source_sha256=r['source_sha256'],byte_summaries=summaries,paired_comparisons=paired,
                original_packet_bytes=sum(f['packet_bytes'] for f in native_index['frames']),
                independently_reconstructed_packet_hashes=2742,independently_parsed_fixtures=parsed,
                component_manifests=manifests,map_checks=27,map_vectors=4,map_body_totals=map_result['body_bytes'],
                map_saved_body_bytes=map_result['saved_body_bytes'],header_and_nested_wrapper_compaction_bytes_per_packet=148,
                actual_all_visible_wire_controls=True,old_wire_report_sha256=sha(OLD/'wire-attempts/20261106T130658877580Z-53860fda/results.json'),
                contexts=contexts,protocol=protocol,physical_30fps_proven=False,validated_under10ms_proven=False,esp32_simulated=False,
                scope=['Actual compact-header/map/residual/HUD native parity and matched all-visible wire controls.',
                       'All2742 packet hashes and complete application bytes independently reconstructed without encoder execution.',
                       'Context timing covers full457 sources/two actually re-encoded chunk profiles but remains a standalone prospective frontend model.',
                       'No FPGA fit/Fmax, ESP32 transport, full coupled decoder timing, sustained30fps or HEVC/AV1 superiority proof.'])


def verify_protocol(path,wire,keyed,wire_path):
    raise NotImplementedError('Actual protocol schema pending root test completion')


def main():
    p=argparse.ArgumentParser();p.add_argument('--wire-report',required=True);p.add_argument('--protocol-report',default='experiments/python-gamebub-v86/protocol-tests.json')
    p.add_argument('--context-session',required=True);p.add_argument('--output',default='experiments/python-gamebub-v86/summary.json');p.add_argument('--verify-summary',action='store_true');args=p.parse_args()
    result=verify(args.wire_report,args.protocol_report,args.context_session);dest=local(args.output)
    if args.verify_summary:assert read(dest)==result
    else:
        with dest.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print('V86_EVIDENCE_PASS sources=457 wire_packets=2742 reconstructed_hashes=2742 frontend_schedules=5484')
    print('V86_SUMMARY',dest)


if __name__=='__main__':main()
