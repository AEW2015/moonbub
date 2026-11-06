#!/usr/bin/env python3
"""Independently audit native receipts, archived artifacts, fixtures and timings."""
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import struct
import tarfile

ROOT=Path(__file__).resolve().parents[2]
AREA=Path(__file__).resolve().parent


def sha(data):return hashlib.sha256(data).hexdigest()


def audit():
    storage=json.loads((AREA/'native-artifact-storage.json').read_text())
    archive=AREA/storage['archive']
    assert sha(archive.read_bytes())==storage['archive_sha256']
    with tarfile.open(archive,'r:gz') as tar:
        assert set(tar.getnames())==set(storage['members'])
        for name,digest in storage['members'].items():
            assert sha(tar.extractfile(name).read())==digest
        for alias in storage['existing_frozen_aliases'].values():
            assert sha((ROOT/alias['path']).read_bytes())==alias['sha256']
        def artifact(path):
            name=str(path.relative_to(AREA))
            # Prefer archived data even when ignored local copies exist: the
            # remote Git package must not rely on those unpacked copies.
            if name in storage['members']:return tar.extractfile(name).read()
            if name in storage['existing_frozen_aliases']:
                return (ROOT/storage['existing_frozen_aliases'][name]['path']).read_bytes()
            return path.read_bytes()
        all_reports=[]
        for result in sorted((AREA/'native-attempts').glob('*/results.json')):
            report=json.loads(result.read_text())
            for name,digest in report['artifact_sha256'].items():
                assert sha(artifact(result.parent/name))==digest,(result,name)
            for name,digest in report['source_sha256'].items():
                assert sha(artifact(result.parent/'sources'/name))==digest
            all_reports.append(result)
        selected=json.loads((AREA/'native-results.json').read_text())
        attempt=ROOT/selected['selected_attempt']
        assert json.loads((attempt/'results.json').read_text())==selected
        assert selected['status']=='PASS'
        for name,digest in selected['source_sha256'].items():
            assert sha((ROOT/name).read_bytes())==digest,name
        fixture=ROOT/selected['input_fixture']['path']
        assert sha(fixture.read_bytes())==selected['input_fixture']['gzip_sha256']
        raw=gzip.decompress(fixture.read_bytes())
        assert sha(raw)==selected['input_fixture']['raw_sha256']
        at=0
        def u32():
            nonlocal at
            value=struct.unpack_from('<I',raw,at)[0];at+=4;return value
        count=u32();accepted=[];bench=[]
        for i in range(count):
            blocks,length,benchmark,accept=u32(),u32(),u32(),u32()
            assert 0<=blocks<=65536 and length<=1000000 and benchmark in (0,1) and accept in (0,1)
            packet=raw[at:at+length];at+=length
            expected=raw[at:at+64].decode();at+=64
            assert len(packet)==length and len(expected)==64
            accepted.append(bool(accept))
            if benchmark:bench.append(i)
        assert at==len(raw) and count==1388 and len(bench)==12
        for file in ('optimized-output.jsonl','sanitizer-output.jsonl'):
            rows=[json.loads(x) for x in (attempt/file).read_text().splitlines()]
            cases=[r for r in rows if r['kind']=='case']
            assert len(cases)==count
            for i,row in enumerate(cases):
                assert row['id']==i and row['accepted']==accepted[i] and row['status']=='PASS'
            done=[r for r in rows if r['kind']=='done']
            assert len(done)==1 and done[0]['status']=='PASS' and done[0]['cases']==count
            if file.startswith('sanitizer'):
                assert not any(r['kind']=='timing' for r in rows)
        timings=[json.loads(x) for x in (attempt/'optimized-output.jsonl').read_text().splitlines()
                 if json.loads(x)['kind']=='timing']
        assert timings==selected['optimized']['timings'] and len(timings)==168
        keys=set();totals={}
        for row in timings:
            key=(row['repeat'],row['id'],row['variant'])
            assert key not in keys and row['repeat'] in range(7) and row['id'] in bench
            assert row['variant'] in ('bit','word32') and row['iterations']==20 and row['ns']>0
            keys.add(key);pair=(row['repeat'],row['variant'])
            totals[pair]=totals.get(pair,0)+row['ns']
        pairs=[]
        for repeat in range(7):
            a,b=totals[(repeat,'bit')]/20,totals[(repeat,'word32')]/20
            pairs.append(dict(repeat=repeat,bit_ns_per_singlepass_12_chunks=a,
                              word32_ns_per_singlepass_12_chunks=b,bit_over_word32=a/b))
        assert pairs==selected['optimized']['paired_repeat_summary']
        ratio=statistics.median(r['bit_over_word32'] for r in pairs)
        assert ratio==selected['optimized']['median_bit_over_word32']
    return dict(schema='cu66-v91-independent-native-audit-v1',status='PASS',
                prior_and_selected_attempts=len(all_reports),selected_attempt=selected['selected_attempt'],
                archived_members=len(storage['members']),frozen_aliases=len(storage['existing_frozen_aliases']),
                input_cases=count,optimized_and_sanitizer_case_rows=2*count,timing_rows=len(timings),
                median_paired_bit_over_word32=ratio,uses_ignored_unpacked_artifacts=False,
                scope='Saved native receipts and host timing; no rerun or hardware timing claim.')


if __name__=='__main__':
    report=audit();(AREA/'native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS_NATIVE_AUDIT',report['input_cases'],report['timing_rows'])
