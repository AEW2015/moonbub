#!/usr/bin/env python3
"""Read-only integrity verification for the frozen CU66 v69-v73 baseline."""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "fpga/experiments/cu66-v74/baseline-sources.json"
COUNTS = {"v69":4879,"v70":460,"v71":122,"v72":131,"v73":161}
PINNED_COMMIT = "78d35ddc45fb22732804967748f31042860dbdce"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=json.loads(PIN.read_text())
    if p["baseline_commit"] != PINNED_COMMIT: raise ValueError("unexpected v73 commit pin")
    if subprocess.run(["git","merge-base","--is-ancestor",PINNED_COMMIT,"HEAD"],cwd=ROOT).returncode:
        raise ValueError("pinned v73 commit is not an ancestor of HEAD")
    for rel,h in p["source_sha256"].items():
        f=ROOT/rel
        if not f.is_file() or sha(f)!=h: raise ValueError("pinned source mismatch: "+rel)
    counts={}
    for v,n in COUNTS.items():
        manifest=ROOT/f"docs/cu66-{v}/bundle-manifest.json"
        entries=json.loads(manifest.read_text())["files_sha256"]
        if len(entries)!=n or p["bundle_file_counts"].get(v)!=n: raise ValueError(f"{v} count mismatch")
        for rel,h in entries.items():
            f=ROOT/rel
            if not f.is_file() or sha(f)!=h: raise ValueError(f"{v} bundle mismatch: {rel}")
        counts[v]=n
    # The v73 verifier chains through v72, v71, v70 and v69 authorities.
    r=subprocess.run([sys.executable,str(ROOT/"scripts/cu66-v73/verify_baseline.py")],cwd=ROOT,text=True,capture_output=True)
    if r.returncode: raise ValueError("prior baseline verifier failed: "+(r.stdout+r.stderr).strip())
    print("V74_BASELINE_INTEGRITY_PASS "+" ".join(f"{v}={n}" for v,n in counts.items())+
          f"; {PINNED_COMMIT} ancestor of HEAD; v73 and prior baseline verifiers passed; integrity only")
if __name__=="__main__":
    try: main()
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("V74_BASELINE_INTEGRITY_FAIL",e,file=sys.stderr);sys.exit(1)
