"""Snapshot-bound restricted CP23 fixture-to-composite-scanout simulation."""
import argparse, hashlib, json, os, subprocess, time, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--label', required=True)
parser.add_argument('--smoke', action='store_true')
parser.add_argument('--rtl', choices=['v008'], default='v008')
parser.add_argument('--abort-pending', action='store_true')
parser.add_argument('--abort-mode', type=int, choices=[0,1,2], default=0)
parser.add_argument('--private-error',type=int,choices=[0,1,2,3,4],default=0)
parser.add_argument('--reset-load', action='store_true')
parser.add_argument('--case', type=int, choices=[0,1,2,3,4,5], default=0)
args = parser.parse_args()
if sum([args.smoke, bool(args.case), args.abort_pending, bool(args.abort_mode), args.reset_load, bool(args.private_error)]) > 1:
    parser.error("Select one independent scenario; mixed profiles invalidate coverage")
assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
out = ROOT / 'evidence' / args.label
out.mkdir(parents=True, exist_ok=False)
top = 'cp23_key_composite_scanout.sv' if args.rtl == 'v001' else 'cp23_key_composite_scanout_' + args.rtl + '.sv'
sv = [top, 'cp23_key_private_join.sv', 'tb_boundary_probe_v009.sv']
sv += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'compute').glob('*.sv'))]
sv += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'parents').glob('*.sv'))]
assets = ['fixture.hex', 'expected.hex', 'column.hex', 'composite.hex', 'hud.hex', 'quantizers.hex']
vectors = {1:'negative/01-outer-CRC.hex',2:'negative/06-nested-HUD-tag.hex',3:'negative/04-nested-base-CRC.hex',4:'negative/05-nested-HUD-CRC.hex',5:'negative/10-nested-base-tag.hex'}
files = sv + assets + ['parent-bindings.json']
if args.case:
    files += [vectors[args.case]]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
hashes = {f: sha(ROOT / f) for f in files}
for f in files:
    dest = out / 'inputs' / f
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes((ROOT / f).read_bytes())
for f in assets:
    (out / f).write_bytes((ROOT / f).read_bytes())
if args.case:
    vector = vectors[args.case]
    (out / 'fixture.hex').write_bytes((ROOT / vector).read_bytes())
(out / 'source-snapshot.json').write_text(json.dumps(hashes, indent=2) + '\n')
env = dict(os.environ)
def tool(name):
    value=os.environ.get(name.upper()) or shutil.which(name) or shutil.which(name+'.exe')
    fallback=Path('C:/msys64/ucrt64/bin')/(name+'.exe')
    if not value and fallback.exists(): value=str(fallback)
    if not value: raise SystemExit('Missing tool: '+name+'; put it on PATH or set '+name.upper())
    env['PATH']=str(Path(value).resolve().parent)+os.pathsep+env.get('PATH','')
    return value
steps = []
def run(label, cmd):
    started = time.monotonic()
    with (out / (label + '.log')).open('wb') as log:
        result = subprocess.run(cmd, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
    steps.append(dict(label=label, command=cmd, returncode=result.returncode,
                      wall_seconds=time.monotonic() - started))
    (out / 'execution.json').write_text(json.dumps(steps, indent=2) + '\n')
    print(label, result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
run('compile', [tool('iverilog'), '-g2012', '-Wall', '-DSIMULATION',
                '-s', 'tb', '-Ptb.SMOKE=' + str(int(args.smoke)), '-Ptb.CASE=' + str(args.case), '-Ptb.ABORT_PENDING=' + str(int(args.abort_pending)), '-Ptb.ABORT_MODE=' + str(args.abort_mode), '-Ptb.RESET_LOAD=' + str(int(args.reset_load)), '-Ptb.PRIVATE_ERROR='+str(args.private_error), '-o', str(out / 'test.vvp'),
                *[str(out / 'inputs' / f) for f in sv]])
run('simulation', [tool('vvp'), '-i', str(out / 'test.vvp')])
assert hashes == {f: sha(ROOT / f) for f in files}, 'source changed during run'
marker = 'CP23_BOUNDARY_PRIVATE_ERROR_PASS' if args.private_error else 'CP23_PHASE_ABORT_PASS' if args.abort_mode else 'CP23_PENDING_ABORT_PASS' if args.abort_pending else 'CP23_COMPOSITE_NEGATIVE_PASS' if args.case else 'CP23_COMPOSITE_SMOKE_PASS' if args.smoke else 'CP23_COMPOSITE_SCANOUT_PASS'
assert marker in (out / 'simulation.log').read_text()
(out / 'result.json').write_text(json.dumps(dict(status='PASS_OFFLINE_RESTRICTED_FIXTURE_ONLY',
    source_hashes=hashes, smoke=args.smoke, case=args.case, rtl=args.rtl, abort_pending=args.abort_pending, abort_mode=args.abort_mode, reset_load=args.reset_load, private_error=args.private_error, marker=marker, hardware_actions='NONE'), indent=2) + '\n')
print(marker)
