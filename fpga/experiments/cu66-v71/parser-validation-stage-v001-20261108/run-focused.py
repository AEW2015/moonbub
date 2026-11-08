from pathlib import Path
import argparse, subprocess, json, time, hashlib, shutil, os
p = Path(__file__).resolve().parent
a = argparse.ArgumentParser(); a.add_argument('--out', required=True); args = a.parse_args()
e = p / 'evidence' / args.out; e.mkdir(parents=True, exist_ok=False)
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
bind = json.loads((p/'source-bindings.json').read_text())
assert sha(p/'control/cu71_packet_rxstage_v001.sv') == bind['control_sha256']
assert sha(p/'candidate/cu71_packet_rxstage_v001.sv') == bind['candidate_sha256']
for f in ['header.hex', 'hud.hex']: shutil.copyfile(p/'fixtures'/f, e/f)
env = dict(os.environ, PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'], TEMP='C:/moon/tmp', TMP='C:/moon/tmp')
env.pop('NoDefaultCurrentDirectoryInExePath', None)
records = []
for label in ['control', 'candidate']:
    cmd = ['C:/msys64/ucrt64/bin/iverilog.exe', '-g2012'] + (['-DSTAGED'] if label=='candidate' else []) + ['-I', str(p/'fixtures'), '-s', 'tb_prefix', '-o', str(e/(label+'.vvp')), str(p/label/'cu71_packet_rxstage_v001.sv'), str(p/'tests/tb_focused.sv')]
    for kind, argv in [('compile', cmd), ('run', ['C:/msys64/ucrt64/bin/vvp.exe', str(e/(label+'.vvp'))])]:
        t = time.monotonic(); r = subprocess.run(argv, cwd=e, capture_output=True, text=True, env=env, timeout=180)
        (e/f'{label}-{kind}.log').write_text(r.stdout+r.stderr)
        records.append({'label':label, 'kind':kind, 'command':argv, 'returncode':r.returncode, 'seconds':time.monotonic()-t})
        (e/'execution.json').write_text(json.dumps(records, indent=2)+'\n')
        print(label, kind, r.returncode, flush=True)
        if r.returncode: print(r.stdout[-2000:]+r.stderr[-2000:]); raise SystemExit(1)
    assert 'PACKET_RX_FOURSTATE_FOCUSED_PASS' in (e/f'{label}-run.log').read_text()
(e/'bindings.json').write_text(json.dumps({str(f):sha(f) for f in [Path(__file__), p/'source-bindings.json', p/'control/cu71_packet_rxstage_v001.sv', p/'candidate/cu71_packet_rxstage_v001.sv', p/'tests/tb_focused.sv',p/'fixtures/cu66_profile.svh', p/'fixtures/header.hex',p/'fixtures/hud.hex']}, indent=2)+'\n')
print('FOCUSED_BOTH_PASS', flush=True)
