#!/usr/bin/env python3
"""Three physical slots per tile, accepted/scanout leases and COPY aliases.

Functional memory-layout prototype only. Does not model memory clocks/ports.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import datetime
import uuid

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent


class TileSlots:
    def __init__(self,count=8100):
        self.count=count
        self.physical=[[None]*count for _ in range(3)]
        self.accepted=None
        self.presented=None
        self.candidate=None
        self.written=[]
        self.fid=None

    def image(self,mapping):
        if mapping is None:return None
        data=[]
        for tile,slot in enumerate(mapping):
            if slot not in (0,1,2) or self.physical[slot][tile] is None:
                raise ValueError('invalid live physical descriptor')
            data.append(self.physical[slot][tile])
        return data

    def begin(self,tiles,copies,*,stop_after=None):
        if self.candidate is not None:raise ValueError('candidate already active')
        if len(tiles)!=self.count or len(copies)!=self.count:raise ValueError('coverage')
        if any(v not in (0,1) for v in copies):raise ValueError('copy code')
        if any(copies) and self.accepted is None:raise ValueError('COPY without accepted reference')
        self.candidate=[];self.written=[]
        for tile,(value,copy) in enumerate(zip(tiles,copies,strict=True)):
            if not isinstance(value,bytes) or len(value)!=64:raise ValueError('tile shape')
            if stop_after is not None and tile==stop_after:break
            if copy:
                slot=self.accepted[tile]
                if self.physical[slot][tile]!=value:raise ValueError('false COPY eligibility')
            else:
                leased=set()
                if self.accepted is not None:leased.add(self.accepted[tile])
                if self.presented is not None:leased.add(self.presented[tile])
                slot=next((s for s in range(3) if s not in leased),None)
                if slot is None:raise ValueError('no free tile slot')
                # Invalidate only an unleased old version, then write.
                self.physical[slot][tile]=None
                self.physical[slot][tile]=value
                self.written.append((tile,slot))
            self.candidate.append(slot)

    def abort(self):
        if self.candidate is None:raise ValueError('no active candidate')
        for tile,slot in self.written:
            assert self.accepted is None or self.accepted[tile]!=slot
            assert self.presented is None or self.presented[tile]!=slot
            self.physical[slot][tile]=None
        self.candidate=None;self.written=[]

    def commit(self,fid,expected_digest):
        if self.candidate is None or len(self.candidate)!=self.count:raise ValueError('incomplete candidate')
        actual=hashlib.sha256(b''.join(self.image(self.candidate))).hexdigest()
        if actual!=expected_digest:
            self.abort()
            raise ValueError('content validation failed')
        # One atomic descriptor-map publication in this sequential model.
        self.accepted=list(self.candidate);self.candidate=None;self.written=[];self.fid=fid

    def present(self):
        if self.accepted is None:raise ValueError('no accepted frame')
        self.presented=list(self.accepted)


def digest(tiles):
    return None if tiles is None else hashlib.sha256(b''.join(tiles)).hexdigest()


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=OUT/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    pinned=[Path(__file__).resolve(),ROOT/'experiments/python-gamebub-v82/native/data.py',ROOT/'experiments/python-gamebub-v82/native/index.json']
    pins={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned}
    (out/'prototype.py').write_bytes(Path(__file__).read_bytes())
    spec=importlib.util.spec_from_file_location('alias_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    histories={};rows=[];checks=[];cohort=None
    for frame in native.iter_frames():
        if frame['cohort']!=cohort:
            cohort=frame['cohort'];histories={name:TileSlots() for name in ('present_every_frame','hold_scanout_7_frames')}
        for name,state in histories.items():
            copies=frame['copy_ref_mask']
            before_accepted=digest(state.image(state.accepted));before_display=digest(state.image(state.presented))
            # Deterministic aborted candidates at three different write depths.
            if frame['ordinal']%17==0:
                cut=(0,4051,8099)[(frame['ordinal']//17)%3]
                state.begin(frame['tiles'],copies,stop_after=cut)
                assert digest(state.image(state.accepted))==before_accepted
                assert digest(state.image(state.presented))==before_display
                state.abort()
                assert digest(state.image(state.accepted))==before_accepted
                assert digest(state.image(state.presented))==before_display
                checks.append(dict(name='partial_abort_preserves_both_leases',scenario=name,cohort=cohort,fid=frame['fid'],cut=cut,status='PASS'))
            state.begin(frame['tiles'],copies)
            assert state.image(state.candidate)==frame['tiles']
            assert digest(state.image(state.accepted))==before_accepted
            assert digest(state.image(state.presented))==before_display
            written=len(state.written)
            assert written==8100-sum(copies)
            try:state.commit(frame['fid'],'00'*32)
            except ValueError as e:assert str(e)=='content validation failed'
            else:raise AssertionError('wrong content digest accepted')
            assert digest(state.image(state.accepted))==before_accepted
            assert digest(state.image(state.presented))==before_display
            assert state.candidate is None
            state.begin(frame['tiles'],copies)
            state.commit(frame['fid'],digest(frame['tiles']))
            assert state.image(state.accepted)==frame['tiles']
            if name=='present_every_frame' or frame['ordinal']%7==0:state.present()
            rows.append(dict(scenario=name,cohort=cohort,ordinal=frame['ordinal'],fid=frame['fid'],key=frame['key'],
                             source_canonical_sha256=frame['canonical_sha256'],tile_order_sha256=digest(frame['tiles']),
                             reconstructed_tile_order_sha256=digest(state.image(state.accepted)),
                             copy_alias_tiles=sum(copies),physical_written_tiles=written,
                             physical_written_bytes=written*64,dense_baseline_written_bytes=8100*64,
                             presented_tile_order_sha256=digest(state.image(state.presented))))
    # Focused interface/state failures and a prolonged pinned old scanout.
    state=TileSlots(1);a=[bytes([1])*64];b=[bytes([2])*64];c=[bytes([3])*64]
    for name,action in [('COPY_without_reference',lambda:state.begin(a,[1])),('present_without_frame',state.present),
                        ('commit_without_candidate',lambda:state.commit(0,digest(a))),('abort_without_candidate',state.abort)]:
        try:action()
        except ValueError:checks.append(dict(name=name,status='PASS_REJECT'))
        else:raise AssertionError(name)
    state.begin(a,[0]);state.commit(0,digest(a));state.present()
    for i in range(1,101):
        value=b if i%2 else c
        state.begin(value,[0]);state.commit(i,digest(value))
        assert state.image(state.presented)==a
    checks.append(dict(name='100_updates_with_old_scanout_pinned',status='PASS'))
    state.begin(b,[0],stop_after=0)
    try:state.commit(101,digest(b))
    except ValueError as e:assert str(e)=='incomplete candidate'
    else:raise AssertionError('incomplete commit accepted')
    state.abort()
    checks.append(dict(name='partial_candidate_cannot_publish',status='PASS_REJECT'))
    accepted_before=state.image(state.accepted);display_before=state.image(state.presented)
    try:state.begin(a,[1])
    except ValueError as e:assert str(e)=='false COPY eligibility'
    else:raise AssertionError('false COPY accepted')
    state.abort()
    assert state.image(state.accepted)==accepted_before and state.image(state.presented)==display_before
    checks.append(dict(name='false_COPY_reject_abort_preserves_leases',status='PASS_REJECT'))
    summaries=[]
    for name in histories:
        selected=[r for r in rows if r['scenario']==name];writes=[r['physical_written_bytes'] for r in selected]
        summaries.append(dict(scenario=name,sources=len(selected),copy_alias_tiles=sum(r['copy_alias_tiles'] for r in selected),
                              write_bytes=dict(min=min(writes),median=statistics.median(writes),max=max(writes),total=sum(writes)),
                              avoided_dense_baseline_write_bytes=sum(r['dense_baseline_written_bytes']-r['physical_written_bytes'] for r in selected)))
    (out/'frames.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
    report=dict(schema='cu66-v87-three-slot-copy-alias-v1',status='PASS_FUNCTIONAL_TILE_ALIAS_AND_LEASE_REPLAY',native_sources=457,scenario_source_replays=len(rows),
                source_sha256=pins,
                rows_sha256=hashlib.sha256((out/'frames.jsonl').read_bytes()).hexdigest(),summaries=summaries,checks=checks,
                logical_data_storage_bytes=3*8100*64,descriptor_map_bytes=3*((8100*2+7)//8),
                scope=['Sequential functional tile-physical-slot model; exact decoded-tile parity, not native entropy or RTL execution.',
                       'Accepted and one scanout map each pin at most one slot per tile. Third slot permits provisional residual writes. COPY aliases accepted slot.',
                       'All non-COPY tiles write; comparator is dense write-every-tile, NOT frozen bank-residency accounting or a timing prediction.',
                       'Tile-order digest differs from canonical raster SHA by layout; exact tile arrays are compared and native source canonical SHA retained.',
                       'Physical descriptor ports, metadata traffic, indirect display gather, hash reference reads, async abort/drain and bus atomicity are unimplemented.',
                       'Atomic publication is one sequential Python action. Async transaction fences and scanout leases require RTL implementation.',
                       'Logical maps require6075B packed plus ownership/version/control; physical arrays/Python objects are not target memory or fit claims.'],
                physical_30fps_proven=False,validated_under10ms_proven=False)
    assert pins=={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned},'executed sources changed'
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
    print(report['status'],'sources=457 scenario_replays=914 checks='+str(len(checks)))


if __name__=='__main__':main()
