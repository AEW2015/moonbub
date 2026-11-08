from pathlib import Path
import subprocess,json,hashlib,time
p=Path(__file__).resolve().parent;e=p/'evidence/pure01';e.mkdir(exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
# The compiled files contain only predicates and tests; no P/Invoke/registry/device code.
for n in ['ControlPredicate.cs','CandidatePredicate.cs','Tests.cs']:
 text=(p/'tests'/n).read_text()
 assert all(word not in text for word in ['DllImport','DiInstallDevice','Registry.','SetupDi','USBDevice','CreateFile'])
candidate=(p/'candidate/BindGameBubWinUsb.cs').read_text();wrapper=(p/'tests/CandidatePredicate.cs').read_text()
start=candidate.index('    internal static void ValidateTargetSnapshot(');start=candidate.index('{',start)+1;end=candidate.index('\n    }',start)
assert candidate[start:end].strip() in wrapper
assert sha(Path('C:/moon/tools/usb-control-bootstrap/BindGameBubWinUsb.cs'))==json.loads((p/'source-bindings.json').read_text())['executed_source_sha256']
commands=[['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','/nologo','/platform:x64','/out:'+str(e/'PurePostcheckTests.exe'),str(p/'tests/ControlPredicate.cs'),str(p/'tests/CandidatePredicate.cs'),str(p/'tests/Tests.cs')],[str(e/'PurePostcheckTests.exe')]]
rows=[]
for phase,cmd in zip(['compile-pure','run-pure'],commands):
 t=time.monotonic();r=subprocess.run(cmd,cwd=e,capture_output=True,text=True,timeout=30);(e/(phase+'.log')).write_text(r.stdout+r.stderr);rows.append(dict(phase=phase,command=cmd,returncode=r.returncode,seconds=time.monotonic()-t));(e/'execution.json').write_text(json.dumps(rows,indent=2)+'\n');print(phase,r.returncode,r.stdout.strip(),flush=True);assert r.returncode==0
assert 'PURE_POSTCHECK_PASS'in(e/'run-pure.log').read_text()
(e/'bindings.json').write_text(json.dumps({str(f):sha(f)for f in [Path(__file__),p/'candidate/BindGameBubWinUsb.cs',p/'control/BindGameBubWinUsb.cs',p/'tests/ControlPredicate.cs',p/'tests/CandidatePredicate.cs',p/'tests/Tests.cs',e/'PurePostcheckTests.exe']},indent=2)+'\n')
print('OFFLINE_ONLY_FULL_HELPER_NOT_BUILT_OR_APPLIED')
