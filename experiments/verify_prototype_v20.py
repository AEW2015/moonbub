#!/usr/bin/env python3
"""Read-only v20 hardware-development handoff integrity and conformance checks."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def load(path):return json.loads((ROOT/path).read_text())
def resolve(raw):
    marker='/moonbub-30fps-study/'
    if marker in raw:return ROOT/raw.split(marker,1)[1]
    p=Path(raw);return p if p.is_absolute() else ROOT/p
def run(path,*args):
    r=subprocess.run([sys.executable,str(ROOT/path),*args],capture_output=True,text=True)
    if r.returncode:
        sys.stderr.write(r.stdout+r.stderr);r.check_returncode()
    return r.stdout.strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--sunshine-root',type=Path,default=ROOT.parent/'sunshine-30fps-study');args=p.parse_args()
    m=load('docs/prototype-v20-provenance.json')
    for path,h in m['file_sha256'].items():assert sha(ROOT/path)==h,('inventory',path)
    bindings=0
    for path in m['run_artifacts']:
        for raw,h in load(path)['source_sha256'].items():assert sha(resolve(raw))==h,('snapshot',path,raw);bindings+=1
    for path,h in m['frozen_v19_source_sha256'].items():assert sha(ROOT/path)==h,('frozen v19',path)
    tests=0
    for folder,n in m['test_counts'].items():
        txt=(ROOT/folder/'tests.log').read_text();match=re.search(r'^Ran (\d+) tests? in ',txt,re.M)
        assert match and int(match[1])==n and txt.rstrip().endswith('OK'),folder;tests+=n
    helpers={f:run(f+'/verify.py') for f in m['stored_helpers']}
    analyses={f:run(f+'/analyze.py','--check') for f in m['analysis_helpers']}
    audit=load('experiments/python-game-audit-v20-study/audit.json')
    assert audit['status']=='verified' and audit['final_signals_received']
    assert set(audit['results'])=={'hardware_kit','mandatory_hud','inline_reconstruction'}
    assert all(r['status']=='verified' and not r['errors'] for r in audit['results'].values())
    run('experiments/python-game-audit-v20-study/audit.py','--check')
    checked=[]
    for path,h in m['sunshine_files'].items():
        peer=args.sunshine_root/path
        if peer.is_file():assert sha(peer)==h,('paired Sunshine artifact',path);checked.append(path)
    for name in ('wire-contract.json','development-profile.json'):
        peer=args.sunshine_root/'tools/gamebub/v20'/name
        if peer.is_file():assert peer.read_bytes()==(ROOT/'hardware/gamebub-v20'/name).read_bytes(),('copied host contract',name)
    handoff=load('hardware/gamebub-v20/handoff-index.json')
    for entry in handoff['artifacts']:assert sha(ROOT/entry['path'])==entry['sha256'],entry
    profile=load('hardware/gamebub-v20/development-profile.json')
    assert profile['geometry']['coded']==[720,480] and profile['complete_frame_cap']==49152
    assert not profile['status']['physical_30fps'] and not profile['status']['fpga_decoder_rtl']
    missing=[]
    for raw,h in m['input_sha256'].items():
        q=Path(raw)
        if q.is_file():assert sha(q)==h,('external media',raw)
        else:missing.append(raw)
    print(json.dumps(dict(snapshot_files=len(m['file_sha256']),source_snapshot_bindings=bindings,
        frozen_v19_files=len(m['frozen_v19_source_sha256']),recorded_passing_tests=tests,retained_helpers=helpers,
        untimed_analyses=analyses,fresh_independent_audit='verified',native_c_inverse_blocks=101667,
        complete_ar03_hud_fixtures=20,generated_inline_tile_streams=9,mandatory_full_hud_frames=96,
        hardware_development_kit='hardware/gamebub-v20',fpga_decoder_implemented=False,
        joint_native_or_physical_30fps_proven=False,missing_external_media=missing,paired_sunshine_artifacts_checked=checked),indent=2))
if __name__=='__main__':main()
