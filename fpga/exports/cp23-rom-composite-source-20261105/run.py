"""Portable replay helper for the sealed CP23 ROM composite."""
import argparse, hashlib, json, os, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"
SOURCES = [
    "cp23_rom_composite.sv",
    "cp23_key_composite_scanout_local.sv",
    "loader/cp23_fixed_rom_loader.sv",
    "parent/cp23_key_private_join.sv",
    "tb_rom_composite.sv",
]
SOURCES += [
    p.relative_to(ROOT).as_posix()
    for folder in ("parent/compute", "parent/parents")
    for p in sorted((ROOT / folder).glob("*.sv"))
]
ASSETS = ["fixture.hex", "expected.hex", "column.hex", "composite.hex", "hud.hex", "quantizers.hex", "key.cp23.hex", "key.cp23.bin"]
MARKERS = {
    0: "CP23_ROM_COMPOSITE_SCANOUT_PASS",
    1: "CP23_ROM_LOAD_CANCEL_PASS",
    2: "CP23_ROM_PHYSICAL_ABORT_PASS",
    3: "CP23_ROM_RESET_FENCE_PASS",
    4: "CP23_ROM_RESET_FENCE_PASS",
    5: "CP23_ROM_PENDING_ABORT_PASS",
    6: "CP23_ROM_PRESTART_FETCH_CANCEL_PASS",
    7: "CP23_ROM_LOAD_CANCEL_PASS",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_package():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = {row["path"]: row for row in manifest["artifacts"]}
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p != MANIFEST}
    if actual != set(expected):
        raise RuntimeError("package file set differs from manifest")
    for rel, row in expected.items():
        p = ROOT / rel
        if p.stat().st_size != row["bytes"] or sha(p) != row["sha256"]:
            raise RuntimeError(f"package hash/size mismatch: {rel}")

def find_tool(env_name, name, fallback):
    configured = os.environ.get(env_name)
    found = configured or shutil.which(name) or (fallback if Path(fallback).is_file() else None)
    if not found:
        raise RuntimeError(f"{name} not found; set {env_name} or add it to PATH")
    return str(Path(found).resolve())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", type=int, choices=range(8), required=True)
    ap.add_argument("--evidence", required=True, help="new writable directory outside this package")
    args = ap.parse_args()
    out = Path(args.evidence).expanduser().resolve()
    if out == ROOT or ROOT in out.parents or out in ROOT.parents:
        raise RuntimeError("evidence must be a separate external directory")
    if out.exists():
        raise RuntimeError("evidence directory already exists")
    verify_package()
    iverilog = find_tool("IVERILOG", "iverilog", "C:/msys64/ucrt64/bin/iverilog.exe")
    vvp = find_tool("VVP", "vvp", "C:/msys64/ucrt64/bin/vvp.exe")
    if bytes(int(x,16) for x in (ROOT / "key.cp23.hex").read_text().split()) != (ROOT / "key.cp23.bin").read_bytes():
        raise RuntimeError("canonical ROM text/binary mismatch")
    if sha(ROOT / "key.cp23.bin") != "3255ef9bbdb71f8678547aaadd72a41bf92991b7b09ee7cd88ad2a073df08107":
        raise RuntimeError("canonical ROM fixture hash mismatch")
    out.mkdir(parents=True)
    compile_inputs = SOURCES + ASSETS + ["parent-bindings.json"]
    for rel in compile_inputs:
        target = out / "inputs" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    for rel in ASSETS:
        shutil.copy2(ROOT / rel, out / rel)
    bindings = {rel: sha(ROOT / rel) for rel in compile_inputs}
    (out / "source-snapshot.json").write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")
    executable = out / "test.vvp"
    compile_cmd = [iverilog, "-g2012", "-Wall", "-DSIMULATION", "-s", "tb", f"-Ptb.MODE={args.mode}", "-o", str(executable), *[str(out / "inputs" / p) for p in SOURCES]]
    sim_cmd = [vvp, "-i", str(executable)]
    tool_dirs = [str(Path(tool).parent) for tool in (iverilog, vvp)]
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(tool_dirs + [env.get("PATH", "")])
    steps=[]
    for label, cmd in (("compile", compile_cmd), ("simulation", sim_cmd)):
        start=time.monotonic()
        with (out / f"{label}.log").open("wb") as log:
            result=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
        steps.append({"label":label,"command":cmd,"returncode":result.returncode,"seconds":time.monotonic()-start})
        (out / "execution.json").write_text(json.dumps(steps,indent=2)+"\n",encoding="utf-8")
        result.check_returncode()
    output=(out/"simulation.log").read_text(errors="replace")
    marker=MARKERS[args.mode]
    if marker not in output:
        raise RuntimeError(f"completion marker missing: {marker}")
    if bindings != {rel:sha(ROOT/rel) for rel in compile_inputs}:
        raise RuntimeError("package inputs changed during run")
    verify_package()
    (out/"result.json").write_text(json.dumps({"status":"PASS_OFFLINE_FIXED_ROM_COMPOSITE","mode":args.mode,"marker":marker,"summary":[s for s in output.splitlines() if "PASS" in s],"source_bindings":bindings,"hardware":"NONE","implementation":"NOT_RUN"},indent=2)+"\n",encoding="utf-8")
    print(marker)

if __name__ == "__main__":
    main()
