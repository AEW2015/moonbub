#!/usr/bin/env python3
"""Independent CS88 candidate/selected packet reconstruction, never producer calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v88'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(data):return hashlib.sha256(data).hexdigest()
def lines(path):return list(map(json.loads,path.read_text().splitlines()))
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


def main():
    selected=json.loads((AREA/'wire/results.json').read_text())
    report_path=ROOT/selected['selected_report'];report=json.loads(report_path.read_text());run=report_path.parent
    assert selected==dict(report,selected_report=selected['selected_report'])
    assert report['status']=='PASS_FULL_NATIVE_MIXED_CODEC_PARITY'
    candidates=lines(run/'candidates.jsonl');rows=lines(run/'frames.jsonl')
    assert len(candidates)==3656 and len(rows)==2285
    candidate_by_key={(r['cohort'],r['fid'],r['mask']):r for r in candidates}
    row_by_key={(r['policy'],r['cohort'],r['fid']):r for r in rows}
    assert len(candidate_by_key)==len(candidates) and len(row_by_key)==len(rows)
    paths=[Path(__file__).resolve(),ROOT/'scripts/cu66-v86/verify_evidence.py',ROOT/'scripts/cu66-v87/audit_quantizers.py',
           AREA/'entropy/data.py',AREA/'entropy/index.json',report_path,run/'candidates.jsonl',run/'frames.jsonl',
           ROOT/'experiments/python-gamebub-v82/native/data.py',ROOT/'experiments/python-gamebub-v82/native/index.json',
           ROOT/'experiments/python-gamebub-v87/quantizers/results.json']
    v86path=ROOT/'experiments/python-gamebub-v86/wire-attempts/20261106T135235884295Z-2a73a26a/frames.jsonl'
    c2path=ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
    qselection=json.loads((ROOT/'experiments/python-gamebub-v87/quantizers/results.json').read_text())
    qpath=(ROOT/qselection['selected_report']).with_name('frames.jsonl');paths.extend([v86path,c2path,qpath])
    pins={str(p.relative_to(ROOT)):sha(p) for p in paths}
    for name,value in report['source_sha256'].items():assert sha(ROOT/name)==value; pins[name]=value
    builder=load('cs88_independent_v86',ROOT/'scripts/cu66-v86/verify_evidence.py')
    quant=load('cs88_independent_q87',ROOT/'scripts/cu66-v87/audit_quantizers.py')
    components=load('cs88_independent_data',AREA/'entropy/data.py')
    native=load('cs88_independent_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    v86={(r['configuration'],r['cohort'],r['fid']):r for r in lines(v86path)}
    qqualified={(r['configuration'],r['cohort'],r['fid']):r for r in lines(qpath)}
    commitments={(r['cohort'],r['fid']):r for r in lines(c2path)}
    previous={};sources=set();actual_candidates=actual_selected=0;fixture_checks=[]
    fixture_paths={p.name:p for p in run.glob('*.cs88')};seen_fixtures=set()
    for frame,original in zip(components.iter_frames(),native.iter_frames(),strict=True):
        identity=(frame['cohort'],frame['fid']);assert identity not in sources;sources.add(identity)
        for field in ('cohort','fid','ordinal','key','canonical_sha256','hud_sha256','display_sha256'):assert frame[field]==original[field]
        frozen,counts,method,operations=builder.reconstruct_packet(frame,65536,'copy_group',original['hidden_mask'],commitments[identity])
        assert digest(frozen)==v86['copy_group_cap65536',*identity]['packet_sha256']
        values=quant.quantizer_values(frame['qmap']);needed=quant.needed_mask(operations)
        prior=None if frame['key'] else previous.get(frame['cohort'])
        qmethod,qbody=min(quant.method_candidates(values,needed,prior),key=lambda pair:(len(pair[1]),pair[0]))
        qblock=quant.make_qblock(qmethod,qbody,needed)
        qvalues=values if qmethod<3 or qmethod==6 else [v for v,n in zip(values,needed) if n]
        previous[frame['cohort']]=quant.decoded_map(qmethod,qvalues,needed,prior)
        mode_length=int.from_bytes(frozen[36:40],'big');mode=frozen[128:128+mode_length]
        header=bytearray(frozen[:128]);header[:4]=b'CS87';struct.pack_into('>I',header,40,len(qblock))
        qcontent=bytes(header)+mode+qblock+frozen[128+mode_length+338:-4]
        qpacket=qcontent+struct.pack('>I',zlib.crc32(qcontent))
        qualified=qqualified['copy_group_cap65536',*identity]
        assert digest(qpacket)==qualified['packet_sha256'] and len(qpacket)==qualified['wire_bytes']
        chunks=[chunk for plane in frame['variants']['65536'] for chunk in plane]
        assert len(chunks)==3
        reconstructed={}
        for mask in range(1<<len(chunks)):
            stream=bytearray();chunk_payloads=0;remaining_decisions=remaining_renorm=brbits=brvalues=brevents=brcount=0;position=0
            for plane in frame['variants']['65536']:
                stream.extend(struct.pack('>I',len(plane)))
                for chunk in plane:
                    bypass=bool(mask&(1<<position));position+=1;payload=chunk['br88'] if bypass else chunk['data']
                    stream.extend(struct.pack('>II',chunk['blocks'],len(payload)));stream.extend(payload);chunk_payloads+=len(payload)
                    if bypass:
                        brbits+=sum(chunk['br88_bits']);brvalues+=sum(chunk['rice_values']);brevents+=sum(chunk['events']);brcount+=1
                    else:
                        remaining_decisions+=sum(chunk['old_decisions']);remaining_renorm+=sum(chunk['old_renorm'])
            candidate_header=bytearray(header);candidate_header[:4]=b'CS88';struct.pack_into('>I',candidate_header,48,len(stream))
            raw=bytes(candidate_header)+mode+qblock+stream+frame['hud'];packet=raw+struct.pack('>I',zlib.crc32(raw))
            expected=dict(header=128,mode_body=len(mode),qmap=len(qblock),chunk_directory=12+8*len(chunks),HUD=len(frame['hud']),outer_CRC=4,chunk_payloads=chunk_payloads)
            key=(*identity,mask);candidate=candidate_by_key[key]
            assert candidate['ordinal']==frame['ordinal'] and candidate['components']==expected
            assert candidate['wire_bytes']==len(packet)==sum(expected.values()) and candidate['packet_sha256']==digest(packet)
            assert candidate['remaining_decisions']==remaining_decisions and candidate['remaining_renorm']==remaining_renorm
            assert candidate['BR88_bits']==brbits and candidate['BR88_rice_values']==brvalues and candidate['BR88_events']==brevents and candidate['BR88_chunks']==brcount
            reconstructed[mask]=packet;actual_candidates+=1
        for policy in report['policies']:
            row=row_by_key[policy,*identity];mask=row['mask'];packet=reconstructed[mask]
            assert row['packet_sha256']==digest(packet) and row['wire_bytes']==len(packet)
            assert row['components']==candidate_by_key[*identity,mask]['components']
            assert row['CS87_wire_bytes']==len(qpacket) and row['qmap_sha256']==digest(qblock)
            assert row['decoded']['accepted'] and not row['decoded']['replayed'] and row['decoded']['wire_bytes']==len(packet)
            for field in ('fid','generation','coefficient_sha256','canonical_sha256','hud_sha256','display_sha256','root','seal'):
                assert row['decoded'][field]==qualified['decoded'][field]
            actual_selected+=1
            name=f'c{frame["cohort"]}-f{frame["fid"]}-{policy}.cs88'
            if name in fixture_paths:
                path=fixture_paths[name];assert path.read_bytes()==packet
                fixture_checks.append(dict(path=str(path.relative_to(ROOT)),sha256=digest(packet),bytes=len(packet)));seen_fixtures.add(name)
    assert len(sources)==457 and actual_candidates==3656 and actual_selected==2285
    assert seen_fixtures==set(fixture_paths) and len(fixture_checks)==35
    assert {r['cohort'] for r in rows}==set(range(4))
    assert pins=={name:sha(ROOT/name) for name in pins},'executed inputs changed'
    audit=dict(schema='cu66-v88-independent-packet-reconstruction-v1',status='PASS_ALL_CANDIDATE_AND_SELECTED_PACKET_HASHES',
               source_sha256=pins,native_sources=457,independently_reconstructed_candidates=actual_candidates,
               independently_verified_selected_packets=actual_selected,qualified_CS87_baseline_packets=457,
               retained_fixtures=len(fixture_checks),fixtures=fixture_checks,
               scope='Independent field/map/qmap/chunk assembly; no import of V88 producer/candidate/policy code. Policy objective is separately audited. Native positives joined to frozen qualified CS87 results. No physical timing qualification.')
    (AREA/'packet-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(audit['status'],'candidates='+str(actual_candidates),'selected='+str(actual_selected),'fixtures='+str(len(fixture_checks)))


if __name__=='__main__':main()
