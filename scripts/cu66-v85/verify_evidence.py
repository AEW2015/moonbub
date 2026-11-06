#!/usr/bin/env python3
"""Audit actual CS85 bytes/native verdicts and retain component/model scopes."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re,statistics,struct,sys,tarfile,zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v85'
CAPS=(16,64,256,65536)
C2=ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
CTX=hashlib.sha256(b'{"geometry":[720,480,5400,1350,1350],"granularity":16,"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"}').digest()
MASK='e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5'


def local(name):
    path=Path(name);path=path.resolve()if path.is_absolute()else(ROOT/path).resolve();path.relative_to(ROOT);return path
def relative(path):return str(local(path).relative_to(ROOT))
def sha(path):return hashlib.sha256(local(path).read_bytes()).hexdigest()
def read(path):return json.loads(local(path).read_text())
def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,local(path));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def pins_current(pins):
    for name,digest in pins.items():
        assert re.fullmatch('[0-9a-f]{64}',digest)and sha(name)==digest,('source/artifact mismatch',name)
def archive_matches(path,pins):
    with tarfile.open(local(path),'r:gz')as tar:
        expected={name for name in pins if not name.endswith('.gz')}
        members=tar.getmembers();assert len(members)==len(expected)and{m.name for m in members}==expected
        for m in members:
            assert m.isfile()and hashlib.sha256(tar.extractfile(m).read()).hexdigest()==pins[m.name],m.name
def artifact_manifest(base,path):
    manifest=read(path)
    for name,digest in manifest['files_sha256'].items():
        target=ROOT/name if name.startswith(('scripts/','docs/','experiments/'))else local(base)/name
        assert sha(target)==digest,('manifest',str(target))
    return dict(path=relative(path),sha256=sha(path),files=len(manifest['files_sha256']))


def mode_block(frame,hidden,selected):
    visible=[int(frame['key']or frame['zero_mask'][i]!='1')for i,h in enumerate(hidden)if not h]
    assert len(visible)==7806
    method=selected['method']
    if frame['key']:
        assert method==0;body=b''
    elif method==1:
        body=bytearray(976)
        for i,value in enumerate(visible):body[i//8]|=value<<(7-i%8)
        body=bytes(body)
    else:
        assert method==2;body=bytearray();at=0
        while at<7806:
            end=at+1
            while end<7806 and visible[end]==visible[at]and end-at<128:end+=1
            body.append((visible[at]<<7)|(end-at-1));at=end
        body=bytes(body)
    prefix=struct.pack('>4sBBBBHHHH',b'CM84',2,method,int(frame['key']),16,720,480,8100,len(body))
    packet=prefix+struct.pack('>I',zlib.crc32(prefix+body))+body
    assert len(packet)==selected['total_bytes']and hashlib.sha256(packet).hexdigest()==selected['encoded_sha256']
    return packet


def parse_mode(packet,key,hidden):
    assert 20<=len(packet)<=996
    magic,version,method,flag,group,width,height,tiles,length,crc=struct.unpack_from('>4sBBBBHHHHI',packet)
    assert(magic,version,flag,group,width,height,tiles)==(b'CM84',2,int(key),16,720,480,8100)
    assert method in(0,1,2)and len(packet)==20+length and zlib.crc32(packet[:16]+packet[20:])==crc
    body=packet[20:]
    if key:assert method==0 and not body;visible=[1]*7806
    elif method==1:
        assert len(body)==976 and not(body[-1]&3);visible=[(body[i//8]>>(7-i%8))&1 for i in range(7806)]
    else:
        assert method==2;visible=[]
        for token in body:
            visible.extend([token>>7]*((token&127)+1));assert len(visible)<=7806
        assert len(visible)==7806
    at=0;out=[]
    for h in hidden:
        if h:out.append(1)
        else:out.append(2 if visible[at]else 0);at+=1
    assert at==7806
    return out


def check_ab38(packet,blocks):
    assert 46<=len(packet)<=46+128*blocks
    header=struct.unpack_from('<4sBBIHH4I3I',packet)
    magic,version,flags,n,bw,reserved=header[:6];lengths=header[6:10];counts=header[10:13]
    assert(magic,version,n,bw,reserved)==(b'AB38',1,blocks,1,0)and flags in(0,1)
    assert len(packet)==46+sum(lengths)and zlib.crc32(packet[:-4])==struct.unpack_from('<I',packet,len(packet)-4)[0]
    if flags:
        assert lengths==(128*blocks,0,0,0)and counts==(0,0,0)
        values=struct.unpack_from('<'+'h'*(blocks*64),packet,42)
        assert all(-2048<=v<=2048 for v in values)
    else:
        position=42
        for stream,length in enumerate(lengths):
            assert length>=9
            k0,k1,bits=struct.unpack_from('<BBI',packet,position);data=packet[position+6:position+length]
            assert bits>=18 and len(data)==(bits+7)//8
            if bits%8:assert not(data[-1]&((1<<(8-bits%8))-1))
            if stream==0:assert k0<=13 and k1==255
            else:assert k0<=19 and k1<=11 and counts[stream-1]<=blocks*(5,15,43)[stream-1]
            assert all(not((data[b//8]>>(7-b%8))&1)for b in(bits-2,bits-1))
            position+=length
        assert position==len(packet)-4
    return flags


def parse_wire(packet,expected,hidden):
    assert 260<=len(packet)<=2097152
    assert zlib.crc32(packet[:-4])==int.from_bytes(packet[-4:],'big')
    assert packet[:4]==b'CS85'and packet[4]==1 and packet[5]in(0,1)and packet[6:8]==b'\x10\x00'
    flag=bool(packet[5]);fid=int.from_bytes(packet[8:12],'big');refid=int.from_bytes(packet[12:16],'big');generation=int.from_bytes(packet[16:24],'big')
    assert(fid,refid,generation,flag)==(expected['fid'],expected['refid'],expected['ordinal']+1,expected['key'])
    assert struct.unpack_from('>4H',packet,24)==(720,480,expected['block_size'],0)
    cap,map_n,q_n,hud_n,data_n=struct.unpack_from('>5I',packet,32)
    assert cap in CAPS and q_n==338 and 20<=map_n<=996 and 110<=hud_n<=49152
    assert len(packet)==256+map_n+q_n+data_n+hud_n+4 and packet[244:256]==bytes(12)
    assert packet[180:212]==CTX and packet[212:244].hex()==MASK
    pos=256;operations=parse_mode(packet[pos:pos+map_n],flag,hidden);pos+=map_n
    quant=packet[pos:pos+338];pos+=338
    scales=[(quant[i//4]>>(6-2*(i%4)))&3 for i in range(1352)]
    assert all(v<=2 for v in scales[:1350])and scales[1350:]==[0,0]
    start=pos;ab=chunks=0
    for lo,hi in((0,5400),(5400,6750),(6750,8100)):
        needed=sum(op==2 for op in operations[lo:hi]);n=int.from_bytes(packet[pos:pos+4],'big');pos+=4
        assert n==(needed+cap-1)//cap
        for i in range(n):
            count,length=struct.unpack_from('>II',packet,pos);pos+=8
            assert count==min(cap,needed-i*cap)and count>0
            chunk=packet[pos:pos+length];assert len(chunk)==length;check_ab38(chunk,count)
            pos+=length;ab+=length;chunks+=1
    assert pos-start==data_n
    hud=packet[pos:pos+hud_n];pos+=hud_n
    assert hud[:4]in(b'HU25',b'HX32',b'HX33')and hud[4:6]==b'\x01\x04'
    assert struct.unpack_from('<IIIHH',hud,6)==(25,fid,refid,720,480)
    assert zlib.crc32(hud[:-4])==int.from_bytes(hud[-4:],'little')and pos==len(packet)-4
    counts=dict(header=256,mode_map=map_n,qmap=338,chunk_directory=12+8*chunks,AB38_payloads=ab,HUD=hud_n,outer_CRC=4)
    assert sum(counts.values())==len(packet)
    return dict(cap=cap,components=counts,root=packet[84:116].hex(),seal=packet[116:148].hex(),
                previous_root=packet[52:84].hex(),hud_sha256=packet[148:180].hex())


def packet_from_retained(frame,cap,map_packet,c2,previous):
    stream=bytearray();chunks=ab=0
    for plane in frame['variants'][str(cap)]:
        stream.extend(struct.pack('>I',len(plane)))
        for c in plane:
            stream.extend(struct.pack('>II',c['blocks'],len(c['data'])));stream.extend(c['data']);chunks+=1;ab+=len(c['data'])
    prefix=struct.pack('>4sBBBBIIQHHHHIIIII',b'CS85',1,int(frame['key']),16,0,frame['fid'],frame['refid'],frame['ordinal']+1,
                       720,480,frame['block_size'],0,cap,len(map_packet),338,len(frame['hud']),len(stream))
    header=prefix+(bytes(32)if frame['key']else bytes.fromhex(previous))+bytes.fromhex(c2['root'])+bytes.fromhex(c2['seal'])+bytes.fromhex(frame['hud_sha256'])+CTX+bytes.fromhex(MASK)+bytes(12)
    body=header+map_packet+frame['qmap']+stream+frame['hud']
    return body+struct.pack('>I',zlib.crc32(body)),dict(header=256,mode_map=len(map_packet),qmap=338,chunk_directory=12+8*chunks,
                                                  AB38_payloads=ab,HUD=len(frame['hud']),outer_CRC=4)


def verify_component_scopes():
    residual=AREA/'residual';contexts=AREA/'contexts'
    manifests=[artifact_manifest(residual,residual/'artifact-manifest.json'),artifact_manifest(contexts,contexts/'artifact-manifest.json')]
    ri=read(residual/'index.json');ci=read(contexts/'index.json')
    assert ri['record_count']==ci['record_count']==457 and ri['cohort_counts']==ci['cohort_counts']==[119,119,119,100]
    pins_current(ri['source_sha256']);pins_current(ci['source_sha256'])
    for area,index in((residual,ri),(contexts,ci)):
        assert sha(area/index['data']['path'])==index['data']['gzip_sha256']
        report_path=(area/index['data']['path']).parent/'results.json';report=read(report_path)
        assert report['status']=='PASS'and report['records']==457
        if 'source_archive_sha256'in report:assert sha(report_path.parent/'sources.tar.gz')==report['source_archive_sha256']
        archive_matches(report_path.parent/'sources.tar.gz',report['source_sha256'])
    rv=read(residual/'verification.json');cv=read(contexts/'verification.json');mv=read(contexts/'model-verification.json')
    assert rv['status']==cv['status']==mv['status']=='PASS'
    assert rv['records']==cv['frames']==457 and cv['tiles']==3701700
    pins_current(rv['source_sha256']);pins_current(cv['source_sha256']);pins_current(mv['source_sha256'])
    assert mv['selected_sources']==25 and mv['schedules']==300 and mv['synthetic_checks']==18
    assert len(mv['independently_reconstructed_witnesses'])==2
    model_report_path=next(local(name)for name in mv['source_sha256']if name.endswith('/results.json'))
    model=read(model_report_path);assert model['status']=='PASS_SELECTED_CONTEXT_MODEL'
    pins_current(model['source_sha256'])
    for name,digest in model['artifacts_sha256'].items():assert sha(model_report_path.parent/name)==digest
    archive_matches(model_report_path.parent/'sources.tar.gz',model['source_sha256'])
    matched=read(residual/'matched-control.json');assert matched['status']=='PASS'and matched['frames']==457 and matched['encoder_corner_checks']==22
    pins_current(matched['source_sha256']);assert sha(matched['frames_path'])==matched['frames_sha256']
    rows=[json.loads(s)for s in local(matched['frames_path']).read_text().splitlines()];assert len(rows)==457
    assert matched['all_visible_AB38_bytes']==stats([r['all_visible_AB38_bytes']for r in rows])
    assert matched['residual_AB38_bytes']==stats([r['residual_AB38_bytes']for r in rows])
    assert matched['component_bytes_reduction']==stats([r['all_visible_AB38_bytes']-r['residual_AB38_bytes']for r in rows])
    assert matched['improved_sources']==sum(r['all_visible_AB38_bytes']>r['residual_AB38_bytes']for r in rows)
    assert matched['regressed_sources']==sum(r['all_visible_AB38_bytes']<r['residual_AB38_bytes']for r in rows)
    assert matched['all_visible_encoder_decisions']==sum(r['all_visible_encoder_decisions']for r in rows)
    assert matched['residual_encoder_decisions']==sum(r['residual_encoder_decisions']for r in rows)
    for record,source in zip(rows,ri['frames'],strict=True):
        assert(record['cohort'],record['fid'],record['key'])==(source['cohort'],source['fid'],source['key'])
        assert record['residual_AB38_bytes']==source['variant_stats']['65536']['AB38_bytes']
    run=read(local(matched['frames_path']).parent/'results.json');assert run['status']=='PASS'and run['result_sha256']==sha(residual/'matched-control.json')
    assert sha(local(matched['frames_path']).parent/'sources.tar.gz')==run['source_archive_sha256'];archive_matches(local(matched['frames_path']).parent/'sources.tar.gz',run['source_sha256'])
    return dict(manifests=manifests,residual_index=ri,contexts_index=ci,matched=matched,matched_rows=rows,
                context_model=dict(path=relative(model_report_path),sha256=sha(model_report_path),sources_scheduled=25,schedules=300,
                                   summaries=model['summaries'],scope='Selected front-end-only conditional model; not full457 latency or FPGA/ESP32 timing.'))


def verify(wire_report_path,protocol_path):
    wire_report_path=local(wire_report_path);report=read(wire_report_path)
    assert report['schema']=='cu66-v85-full-wire-v1'and report['status']=='PASS_NATIVE_FULL_FRAME_PARITY'
    assert report['smoke_limit']==0 and report['sources']==457 and report['received_packets']==1828
    assert report['research_packet_limit']==2097152 and report['compatibility_packet_limit']==49152 and report['timing_is_FPGA']is False
    assert report['receiver_exit_codes']=={str(c):0 for c in CAPS}
    pins_current(report['source_sha256']);assert sha(wire_report_path.parent/'sources.tar.gz')==report['source_archive_sha256']
    archive_matches(wire_report_path.parent/'sources.tar.gz',report['source_sha256'])
    actual={p.name for p in wire_report_path.parent.iterdir()if p.is_file()and p.name!='results.json'}
    assert actual==report['artifacts_sha256'].keys()
    for name,digest in report['artifacts_sha256'].items():assert sha(wire_report_path.parent/name)==digest
    scopes=verify_component_scopes();ri=scopes['residual_index']
    assert report['residual_index_sha256']==sha(AREA/'residual/index.json')
    native=read(ROOT/'experiments/python-gamebub-v82/native/index.json');assert native['record_count']==457
    expected_native={(f['cohort'],f['fid']):f for f in native['frames']}
    c2={(r['cohort'],r['fid']):r for r in map(json.loads,C2.read_text().splitlines())}
    mode_rows={(r['cohort'],r['fid']):r for r in map(json.loads,(ROOT/'experiments/python-gamebub-v84/mode-map-v2/frames.jsonl').read_text().splitlines())}
    rows=[json.loads(line)for line in(wire_report_path.parent/'frames.jsonl').read_text().splitlines()]
    keyed={(r['cohort'],r['fid'],r['cap']):r for r in rows}
    assert len(rows)==len(keyed)==1828 and keyed.keys()=={(*k,cap)for k in expected_native for cap in CAPS}
    loader=module('cu85_final_components',AREA/'residual/data.py')
    oracle=module('cu85_final_native_mask',ROOT/'experiments/python-gamebub-v82/native/data.py')
    hidden=next(oracle.iter_frames())['hidden_mask'];assert hashlib.sha256(hidden).hexdigest()==MASK
    fixture_expected={};previous={};component_frames=0
    for frame in loader.iter_frames():
        key=frame['cohort'],frame['fid'];source=expected_native[key];control=c2[key]
        for name in('cohort','ordinal','fid','refid','key','packet_bytes','packet_sha256','canonical_sha256','hud_sha256','display_sha256'):
            assert frame[name]==source[name],name
        assert hashlib.sha256(frame['qmap']).hexdigest()==ri['frames'][component_frames]['qmap_sha256']
        assert hashlib.sha256(frame['hud']).hexdigest()==source['encoded_hud_sha256']
        map_packet=mode_block(frame,hidden,mode_rows[key]);operations=parse_mode(map_packet,frame['key'],hidden)
        assert hashlib.sha256(bytes(operations)).hexdigest()==mode_rows[key]['decoded_modes_sha256']
        for cap in CAPS:
            row=keyed[(*key,cap)];packet,counts=packet_from_retained(frame,cap,map_packet,control,previous.get(frame['cohort'],'00'*32))
            assert row['components']==counts and row['wire_bytes']==len(packet)
            assert row['original_packet_bytes']==source['packet_bytes']and row['byte_delta']==len(packet)-source['packet_bytes']
            assert row['fits_49152']==(len(packet)<=49152)and row['packet_sha256']==hashlib.sha256(packet).hexdigest()
            assert(row['ordinal'],row['key'])==(frame['ordinal'],frame['key'])
            decoded=row['decoded'];assert decoded['accepted']is True and decoded['replayed']is False
            assert decoded['fid']==frame['fid']and decoded['generation']==frame['ordinal']+1 and decoded['wire_bytes']==len(packet)
            assert decoded['coefficient_sha256']==frame['canonical_coefficients_sha256']
            for name in('canonical_sha256','hud_sha256','display_sha256'):assert decoded[name]==source[name]
            for name in('root','seal'):assert decoded[name]==control[name]
            if(frame['cohort']==0 and frame['ordinal']in(0,1)and cap in(16,65536))or(frame['cohort']==3 and frame['fid']==50):
                fixture_expected[f'c{frame["cohort"]}-f{frame["fid"]}-cap{cap}.cs85']=(packet,frame,row,previous.get(frame['cohort'],'00'*32))
        previous[frame['cohort']]=control['root'];component_frames+=1
    assert component_frames==457
    fixtures=[]
    assert {p.name for p in wire_report_path.parent.glob('*.cs85')}==fixture_expected.keys()
    for name,(packet,frame,row,prior)in sorted(fixture_expected.items()):
        path=wire_report_path.parent/name;assert path.read_bytes()==packet
        parsed=parse_wire(packet,frame,hidden)
        assert parsed['cap']==row['cap']and parsed['components']==row['components']
        assert parsed['root']==row['decoded']['root']and parsed['seal']==row['decoded']['seal']and parsed['hud_sha256']==frame['hud_sha256']
        assert parsed['previous_root']==('00'*32 if frame['key']else prior)
        fixtures.append(dict(path=relative(path),sha256=sha(path),bytes=len(packet),independent_structural_parse=True))
    assert len(fixtures)==8
    summaries=[]
    for cap in CAPS:
        selected=[r for r in rows if r['cap']==cap]
        summaries.append(dict(cap=cap,sources=457,wire_bytes=stats([r['wire_bytes']for r in selected]),
                              original_packet_bytes=stats([r['original_packet_bytes']for r in selected]),
                              paired_byte_delta=stats([r['byte_delta']for r in selected]),smaller=sum(r['byte_delta']<0 for r in selected),
                              equal=sum(r['byte_delta']==0 for r in selected),larger=sum(r['byte_delta']>0 for r in selected),fits_49152=sum(r['fits_49152']for r in selected)))
    assert summaries==report['summaries']
    protocol=verify_protocol(protocol_path,report,keyed[(0,1,65536)]['decoded'])
    matched=scopes['matched'];projection=[]
    matched_by_id={(r['cohort'],r['fid']):r for r in scopes['matched_rows']}
    for frame in ri['frames']:
        row=keyed[(frame['cohort'],frame['fid'],65536)];control=matched_by_id[(frame['cohort'],frame['fid'])]
        # Exact byte accounting projection only: retained all-visible encoder
        # bytes exist in matched control, but that full-envelope receiver run
        # was not executed. No-COPY visible mode is all RESIDUAL: RLE61 bytes.
        assert frame['variant_stats']['65536']['chunks']==3
        all_visible_map=20 if frame['key']else 81
        projected=row['wire_bytes']-row['components']['mode_map']-row['components']['AB38_payloads']+all_visible_map+control['all_visible_AB38_bytes']
        projection.append(projected-row['wire_bytes'])
    return dict(schema='cu66-v85-combined-evidence-v1',status='PASS_NATIVE_WIRE_AND_PROTOTYPE_EVIDENCE',
                wire_report=relative(wire_report_path),wire_report_sha256=sha(wire_report_path),verifier_sha256=sha(Path(__file__)),
                native_sources=457,cohorts=[119,119,119,100],native_wire_packets=1828,caps=list(CAPS),
                source_sha256=report['source_sha256'],byte_summaries=summaries,independently_parsed_fixtures=fixtures,
                independently_reconstructed_packet_hashes=1828,component_manifests=scopes['manifests'],
                matched_component_control=dict(path=relative(AREA/'residual/matched-control.json'),sha256=sha(AREA/'residual/matched-control.json'),
                                               encoder_corner_checks=22,component_bytes_reduction=matched['component_bytes_reduction'],
                                               all_visible_AB38_bytes=matched['all_visible_AB38_bytes'],residual_AB38_bytes=matched['residual_AB38_bytes'],
                                               scope='Matched same-encoder bw1 whole-plane COMPONENT comparison; no whole-envelope claim.'),
                matched_envelope_projection=dict(projected_saving_bytes=stats(projection),
                                                 scope='Byte-accounting projection using retained matched component sizes plus exact all-visible map grammar; this all-visible full envelope was not receiver-tested.'),
                contexts=scopes['context_model'],protocol=protocol,
                new_encoder_profile=True,physical_30fps_proven=False,validated_under10ms_proven=False,esp32_simulated=False,
                scope=['Fullnative coefficient/canonical/HUD/display/content-root/seal parity through actual research receiver.',
                       'Original CU66 and new CS85 framing/content commitments differ; byte comparison is factual, not equal hardware-cost or standard compatibility proof.',
                       'Research receive limit2MiB; existing49152-byte compatibility counted separately.',
                       'Context lane timing is selected25-source standalone conditional model, not full457 or fullcodec/RTL timing.',
                       'No hardware fit/timing, ESP32 forwarding or HEVC/AV1 quality/bitrate superiority proof.'])


def verify_protocol(path,wire,full_native_recovery):
    report=read(path)
    assert report['schema']=='cu66-v85-native-protocol-tests-v1'and report['status']=='PASS_ACTUAL_NATIVE_REJECT_RETAIN_RECOVER'
    assert report['hardware_test']is False and report['count']==23
    pins_current(report['source_sha256'])
    assert report['source_sha256']['experiments/python-gamebub-v85/receiver.cpp']==wire['source_sha256']['experiments/python-gamebub-v85/receiver.cpp']
    selected=local(report['selected_report']);original=read(selected)
    assert original=={k:v for k,v in report.items()if k!='selected_report'}
    assert set(report['artifacts_sha256'])=={p.name for p in selected.parent.iterdir()if p.is_file()and p.name!='results.json'}
    for name,digest in report['artifacts_sha256'].items():assert sha(selected.parent/name)==digest
    prior_wire_path=next(local(name)for name in report['source_sha256']if name.endswith('/results.json'))
    prior_wire=read(prior_wire_path)
    assert report['binary']==prior_wire['binary']
    assert prior_wire['artifacts_sha256']['receiver.bin']==wire['artifacts_sha256']['receiver.bin']
    assert sha(prior_wire_path.parent/'receiver.bin')==wire['artifacts_sha256']['receiver.bin']
    key_path=prior_wire_path.parent/'c0-f0-cap65536.cs85';delta_path=prior_wire_path.parent/'c0-f1-cap65536.cs85'
    key=key_path.read_bytes();delta=delta_path.read_bytes()
    def reseal(p):return bytes(p[:-4])+struct.pack('>I',zlib.crc32(p[:-4]))
    def edit(offset,value,width=1):
        p=bytearray(delta);p[offset:offset+width]=value.to_bytes(width,'big');return reseal(p)
    malformed={'outer_crc':delta[:-1]+bytes([delta[-1]^1])}
    for name,offset,value,width in(
        ('profile_version',4,2,1),('flags',5,2,1),('unsupported_cap',32,32,4),
        ('overflow_data_length',48,0xffffffff,4),('qmap_length',40,337,4),('stale_generation',16,1,8),
        ('wrong_reference',12,1,4),('previous_root',52,delta[52]^1,1),('content_root',84,delta[84]^1,1),
        ('content_seal',116,delta[116]^1,1),('HUD_digest',148,delta[148]^1,1),
        ('context_domain',180,delta[180]^1,1),('hidden_profile',212,delta[212]^1,1),('reserved_header',244,1,1)):
        malformed[name]=edit(offset,value,width)
    map_n=int.from_bytes(delta[36:40],'big');qpos=256+map_n;data=qpos+338
    malformed['qmap_code']=edit(qpos,delta[qpos]|0xc0)
    malformed['qmap_padding']=edit(qpos+337,delta[qpos+337]|1)
    malformed['chunk_count']=edit(data,0,4);malformed['chunk_blocks']=edit(data+4,0,4)
    size=int.from_bytes(delta[data+8:data+12],'big');pos=data+12
    changed=bytearray(delta);changed[pos]^=1;changed[pos+size-4:pos+size]=struct.pack('<I',zlib.crc32(changed[pos:pos+size-4]))
    malformed['AB38_magic_resealed']=reseal(changed)
    changed=bytearray(delta);changed[261]=3
    changed[272:276]=struct.pack('>I',zlib.crc32(changed[256:272]+changed[276:256+map_n]))
    malformed['mode_method_resealed']=reseal(changed)
    malformed['truncated_body_resealed']=reseal(delta[:-5]+delta[-4:])
    checks=report['checks'];assert len(checks)==23 and len({c['name']for c in checks})==23
    expected={r['fid']:r['decoded']for r in map(json.loads,(prior_wire_path.parent/'frames.jsonl').read_text().splitlines())if r['cap']==65536}
    assert expected[1]==full_native_recovery, 'same native-positive packet and binary across smoke/full runs'
    actual_names=set()
    for check in checks:
        if check['name']=='missing_reference_key_recovery_and_stale_replay':
            assert check['result']=='PASS'
            assert check['missing']['accepted']is False and check['missing']['retained_fid']is None
            assert 'reference'in check['missing']['error']
            assert check['stale']['accepted']is False and check['stale']['retained_fid']==1 and 'stale'in check['stale']['error']
            continue
        name=check['name'];actual_names.add(name)
        assert check['result']=='PASS_REJECT_RETAIN_RECOVER_REPLAY'
        assert check['packet_sha256']==hashlib.sha256(malformed[name]).hexdigest()
        assert check['rejected']['accepted']is False and check['rejected']['retained_fid']==0
        assert check['expected_error_contains']in check['rejected']['error']
        assert check['recovered']==full_native_recovery
    assert actual_names==malformed.keys()
    # The captured report retains rejected/recovered responses. Exact replay
    # equality was asserted in the source-bound live test, not saved separately.
    source=local('scripts/cu66-v85/test_receiver.py').read_text()
    assert "replayed['accepted'] and replayed['replayed']"in source
    assert "assert all(replayed[k]==recovered[k]"in source
    return dict(path=relative(path),sha256=sha(path),selected_report_sha256=sha(selected),checks=23,
                independently_reconstructed_malformed_packet_hashes=len(malformed),receiver_binary_sha256=wire['artifacts_sha256']['receiver.bin'],
                recovery_matches_full_native_wire=True,
                scope='Actual research receiver reject/retain/recover/replay tests; rejected/recovered responses retained and replay equality asserted in pinned test source. No physical hardware fault injection.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wire-report',required=True);parser.add_argument('--protocol-report',default='experiments/python-gamebub-v85/protocol-tests.json')
    parser.add_argument('--output',default='experiments/python-gamebub-v85/summary.json');parser.add_argument('--verify-summary',action='store_true');args=parser.parse_args()
    result=verify(args.wire_report,args.protocol_report);out=local(args.output)
    if args.verify_summary:assert read(out)==result
    else:
        with out.open('x')as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print('V85_EVIDENCE_PASS sources=457 native_wire_packets=1828 reconstructed_hashes=1828 fixtures=8')
    print('V85_SUMMARY',out)


if __name__=='__main__':main()
