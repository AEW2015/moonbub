#!/usr/bin/env python3
"""Independent native-row accounting and small symbolic alias-state checks."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import statistics

ROOT=Path(__file__).resolve().parents[3]
SUBJECT=ROOT/'experiments/python-gamebub-v87/alias/prototype.py'
NATIVE=ROOT/'experiments/python-gamebub-v82/native/data.py'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def digest(values):return None if values is None else hashlib.sha256(b''.join(values)).hexdigest()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--report',default='experiments/python-gamebub-v87/alias/results.json');p.add_argument('--output',required=True);a=p.parse_args()
    report_path=Path(a.report);report=json.loads(report_path.read_text());assert report['status']=='PASS_FUNCTIONAL_TILE_ALIAS_AND_LEASE_REPLAY'
    selected_path=ROOT/report['selected_report'];selected=json.loads(selected_path.read_text())
    assert {k:v for k,v in report.items()if k!='selected_report'}==selected
    pins=report['source_sha256']
    assert all(sha(ROOT/name)==value for name,value in pins.items())
    assert report['logical_data_storage_bytes']==3*8100*64
    assert report['descriptor_map_bytes']==3*((8100*2+7)//8)
    # Published summary rows are tied to native original tile arrays; no alias
    # implementation function is used to derive expected bytes or presentation.
    rows_path=report_path.with_name('frames.jsonl');rows=[json.loads(x)for x in rows_path.read_text().splitlines()]
    assert sha(rows_path)==report['rows_sha256'];assert len(rows)==914
    by_id={(r['scenario'],r['cohort'],r['fid']):r for r in rows};assert len(by_id)==914
    native=load('cu87_alias_audit_native',NATIVE);source_count=0;cohort=None;shown={}
    for frame in native.iter_frames():
        source_count+=1
        if cohort!=frame['cohort']:shown={};cohort=frame['cohort']
        expected_digest=digest(frame['tiles']);expected_writes=8100-sum(frame['copy_ref_mask'])
        for scenario in ('present_every_frame','hold_scanout_7_frames'):
            row=by_id[scenario,cohort,frame['fid']]
            assert row['ordinal']==frame['ordinal']and row['key']==frame['key']
            assert row['source_canonical_sha256']==frame['canonical_sha256']
            assert row['tile_order_sha256']==row['reconstructed_tile_order_sha256']==expected_digest
            assert row['copy_alias_tiles']==sum(frame['copy_ref_mask'])
            assert row['physical_written_tiles']==expected_writes
            assert row['physical_written_bytes']==expected_writes*64
            assert row['dense_baseline_written_bytes']==8100*64
            if scenario=='present_every_frame'or frame['ordinal']%7==0:shown[scenario]=expected_digest
            assert row['presented_tile_order_sha256']==shown[scenario]
    assert source_count==457
    for summary in report['summaries']:
        selected=[r for r in rows if r['scenario']==summary['scenario']];sizes=[r['physical_written_bytes']for r in selected]
        assert summary['sources']==len(selected)==457
        assert summary['copy_alias_tiles']==sum(r['copy_alias_tiles']for r in selected)
        assert summary['write_bytes']==dict(min=min(sizes),median=statistics.median(sizes),max=max(sizes),total=sum(sizes))
        assert summary['avoided_dense_baseline_write_bytes']==sum(8100*64-v for v in sizes)
    subject=load('cu87_alias_subject',SUBJECT);checks=[];steps=0
    # Reference oracle is immutable plaintext, with no slots, bank allocator,
    # candidate maps or calls to the subject's digest helper.
    for seed in range(8):
        rng=random.Random(seed);state=subject.TileSlots(3);accepted=None;displayed=None
        for fid in range(128):
            copies=[int(accepted is not None and rng.random()<0.6)for _ in range(3)]
            values=[accepted[i]if copies[i]else bytes([rng.randrange(256)])*64 for i in range(3)]
            olda=None if accepted is None else list(accepted);oldd=None if displayed is None else list(displayed)
            if fid%5==0:
                cut=rng.randrange(3);state.begin(values,copies,stop_after=cut)
                assert state.image(state.accepted)==olda and state.image(state.presented)==oldd
                try:state.commit(fid,digest(values))
                except ValueError:pass
                else:raise AssertionError('incomplete candidate accepted')
                if state.candidate is not None:state.abort()
                assert state.image(state.accepted)==olda and state.image(state.presented)==oldd
            state.begin(values,copies)
            try:state.begin(values,copies)
            except ValueError:pass
            else:raise AssertionError('nested candidate accepted')
            assert state.image(state.candidate)==values
            assert state.image(state.accepted)==olda and state.image(state.presented)==oldd
            if fid%7==0:
                try:state.commit(fid,'00'*32)
                except ValueError:pass
                else:raise AssertionError('bad digest accepted')
                assert state.candidate is None,'failed validation must abort provisional candidate'
                assert state.image(state.accepted)==olda and state.image(state.presented)==oldd
                state.begin(values,copies)
            state.commit(fid,digest(values));accepted=list(values)
            assert state.image(state.accepted)==accepted and state.image(state.presented)==oldd
            if rng.random()<0.2:state.present();displayed=list(accepted)
            assert state.image(state.presented)==displayed
            steps+=1
        checks.append(dict(name='immutable_plaintext_oracle',seed=seed,frames=128,status='PASS'))
    assert all(sha(ROOT/name)==value for name,value in pins.items()),'source mutation during audit'
    output=dict(schema='cu66-v87-independent-alias-audit-v1',status='PASS_NATIVE_ROWS_AND_SYMBOLIC_ALIAS_ORACLE',
                selected_report=str(selected_path.relative_to(ROOT)),selected_report_sha256=sha(selected_path),
                verified_subject_source_pins=pins,
                native_sources=source_count,native_scenario_rows=len(rows),symbolic_seeds=8,symbolic_accepted_frames=steps,
                report=str(report_path),report_sha256=sha(report_path),rows_sha256=sha(rows_path),
                source_sha256={str(p.relative_to(ROOT)):sha(p)for p in (SUBJECT,NATIVE,Path(__file__).resolve())},
                checks=checks,
                scope='Independent native source/row/accounting and presentation audit plus a small immutable-plaintext state oracle; no hardware timing, async bus or target-memory proof.')
    Path(a.output).write_text(json.dumps(output,indent=2)+'\n');print('V87_INDEPENDENT_ALIAS_AUDIT_PASS native_rows=914 symbolic_frames='+str(steps))

if __name__=='__main__':main()
