#!/usr/bin/env python3
"""Exact native tile reuse and explicitly hypothetical data-write-elision counts."""
import argparse
import datetime
import hashlib
import json
import shutil
import statistics
import subprocess
import tarfile
import time
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v81/tile-reuse'
NATIVE=ROOT/'experiments/cu66-native-v69'
CONTAINER='gamebub-cu66-v69-build'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v)) if v else None

def hidden(plane,tile):
    x,y=tile%(90 if plane==0 else 45),tile//(90 if plane==0 else 45)
    return (((3<=x<22 and (7<=y<9 or 11<=y<13)) or (21<=x<61 and 45<=y<48) or (21<=x<51 and 49<=y<51)) if plane==0 else (11<=x<30 and y==23))


def derive(rows):
    assert len(rows)==457 and {c:sum(r['cohort']==c for r in rows) for c in range(4)}=={0:119,1:119,2:119,3:100}
    per_frame=[];groups=[]
    for r in rows:
        assert len(r['planes'])==3 and [p['plane'] for p in r['planes']]==[0,1,2]
        total_same=0;hidden_same=0
        for p in r['planes']:
            plane=p['plane'];n=5400 if plane==0 else 1350;assert p['tiles']==n
            mask=bytes.fromhex(p['same_mask_u8_lsb_hex']);assert len(mask)==(n+7)//8
            assert all(not(mask[i//8]>>(i%8)&1) for i in range(n,len(mask)*8))
            equal={i for i in range(n) if mask[i//8]>>(i%8)&1};h={i for i in range(n) if hidden(plane,i)}
            assert len(h)==p['hidden_tiles']==(256 if plane==0 else 19)
            assert len(equal&h)==p['same_hidden'] and len(equal-h)==p['same_visible']
            assert r['comparable'] or not equal
            if r['comparable']:assert len(equal&h)==len(h)
            total_same+=len(equal);hidden_same+=len(equal&h)
        eligible=total_same if not r['key'] else 0
        assert r['key'] or r['comparable']
        per_frame.append(dict(cohort=r['cohort'],ordinal=r['ordinal'],fid=r['fid'],key=r['key'],comparable=r['comparable'],same_tiles=total_same,same_visible=total_same-hidden_same,same_hidden=hidden_same,
            hypothetical_elidable_canonical_BL8_writes=eligible*4,
            baseline_canonical_BL8_writes=32400,unchanged_HUD_BL8_writes=2640,
            hypothetical_remaining_data_BL8_writes=35040-eligible*4,
            unchanged_reference_BL8_reads=(0 if r['key'] else 32400),unchanged_HUD_BL8_reads=2640,
            metadata_commands_priced=False,latency_savings_claimed=False))
    for cohort in range(4):
        for key in (True,False):
            rr=[r for r in rows if r['cohort']==cohort and r['key']==key];ff=[f for f in per_frame if f['cohort']==cohort and f['key']==key]
            groups.append(dict(cohort=cohort,key=key,sources=len(rr),comparable_sources=sum(r['comparable'] for r in rr),
              same_tiles=stats([f['same_tiles'] for f in ff]),same_visible=stats([f['same_visible'] for f in ff]),same_hidden=stats([f['same_hidden'] for f in ff]),
              planes=[dict(plane=p,tiles_per_source=5400 if p==0 else 1350,hidden_tiles_per_source=256 if p==0 else 19,
                same_visible_total=sum(r['planes'][p]['same_visible'] for r in rr),same_hidden_total=sum(r['planes'][p]['same_hidden'] for r in rr)) for p in range(3)],
              hypothetical_elidable_canonical_BL8_writes_total=sum(f['hypothetical_elidable_canonical_BL8_writes'] for f in ff),
              hypothetical_elidable_canonical_BL8_writes_per_source=stats([f['hypothetical_elidable_canonical_BL8_writes'] for f in ff])))
    return per_frame,groups


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/f'attempt-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True,exist_ok=False);started=time.monotonic();commands=[]
    report=dict(schema='cu81-exact-native-tile-reuse-v1',status='FAIL',native_only=True,rtl_or_protocol_implemented=False,commands=commands)
    def run(argv,name,timeout):
        entry=dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=None,timed_out=False,timeout_seconds=timeout);commands.append(entry);begin=time.monotonic()
        try:
            with (out/name).open('w') as stream:result=subprocess.run(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
            entry['exit_code']=result.returncode
        except subprocess.TimeoutExpired:entry['timed_out']=True
        finally:
            entry.update(wall_seconds=time.monotonic()-begin,sha256=sha(out/name))
        assert entry['exit_code']==0 and not entry['timed_out'],f'{name}: retained failed command'
        return (out/name).read_text()
    try:
        index=NATIVE/'index.tsv';fields=[line.split('\t') for line in index.read_text().splitlines()]
        files=sorted(set([Path(__file__).resolve(),AREA/'tile_reuse.cpp',index,NATIVE/'manifest.json',*NATIVE.glob('*.hpp'),*[NATIVE/f[2] for f in fields]]))
        pins={str(p.relative_to(ROOT)):sha(p) for p in files};report['source_sha256']=pins
        for f in fields:assert sha(NATIVE/f[2])==Path(f[2]).stem,'content-addressed packet mismatch'
        with tarfile.open(out/'sources.tar.gz','w:gz') as archive:
            for p in files:
                if 'cu66-v81' in p.parts:archive.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
        report['source_snapshot']=dict(path=str((out/'sources.tar.gz').relative_to(ROOT)),sha256=sha(out/'sources.tar.gz'))
        builddir='/build/v81-tile-reuse-'+uuid.uuid4().hex;binary=builddir+'/tile_reuse'
        run(['docker','exec',CONTAINER,'mkdir','-p',builddir],'mkdir.log',30)
        run(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        run(['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'tile_reuse.cpp'),'-o',binary],'build.log',120)
        report['binary_sha256']=run(['docker','exec',CONTAINER,'sha256sum',binary],'binary.log',30).split()[0]
        body=run(['docker','exec',CONTAINER,'timeout','--signal=TERM','--kill-after=5s','300s',binary,str(index)],'run.log',310)
        assert body.count('TILE_REUSE_NATIVE_PASS ')==1 and 'FAIL' not in body
        rows=[json.loads(line) for line in body.splitlines() if line.startswith('{')]
        frames,groups=derive(rows)
        assert pins=={rel:sha(ROOT/rel) for rel in pins},'screening inputs changed'
        (out/'frames.json').write_text(json.dumps(frames,indent=2)+'\n')
        report.update(status='PASS_EXACT_NATIVE_TILE_EQUALITY_SCREEN',frames_path=str((out/'frames.json').relative_to(ROOT)),frames_sha256=sha(out/'frames.json'),sources=len(rows),key_sources=sum(r['key'] for r in rows),delta_sources=sum(not r['key'] for r in rows),groups=groups,
            hypothetical=dict(eligible_delta_equal_tiles=sum(f['same_tiles'] for f in frames if not f['key']),elidable_canonical_BL8_writes=sum(f['hypothetical_elidable_canonical_BL8_writes'] for f in frames),baseline_all_source_canonical_BL8_writes=457*32400,baseline_all_source_data_BL8_writes=457*35040,baseline_delta_canonical_BL8_writes=sum(not r['key'] for r in rows)*32400,metadata_commands_priced=False,reference_read_reduction_claimed=False,latency_savings_claimed=False),
            limitations=['Exact equality to immediately previous accepted frame only; four independent histories, one walkthrough family.','Keys measured separately and excluded from hypothetical write elision.','Hidden fixed-128 canonical tiles counted separately; whole-frame canonical SHA and packet/HUD/display digests remain checked.','Copy-on-write tile map, allocation/refcounts, alias-safe bank/scanout drain and protocol are NOT implemented.','Counts omit all new metadata/indirection traffic and may overestimate net benefit.','No entropy/arithmetic/read/authentication work is claimed removed; no decode/transport/display latency savings or 30fps/under10ms proof.'])
    except Exception as exc:report['failure']=str(exc);raise
    finally:
        report['wall_seconds']=time.monotonic()-started;(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(status=report['status'],results_path=str(out/'results.json'))),flush=True)


if __name__=='__main__':main()
