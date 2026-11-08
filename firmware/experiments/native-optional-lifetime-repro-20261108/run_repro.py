import hashlib, json, os, pathlib, subprocess, time

SOURCE = pathlib.Path(r"C:\moon\dev\experiments\native-optional-lifetime-repro-v001-20261108")
ROOT = pathlib.Path(r"C:\moon\publish\firmware\experiments\native-optional-lifetime-repro-20261108")
OUT = ROOT / "verified"
TEMP = pathlib.Path(r"C:\moon\tmp\native-optional-lifetime-repro-20261108")
BIN = pathlib.Path(r"C:\Users\lavat\.espressif\tools\xtensa-esp-elf\esp-14.2.0_20250730\xtensa-esp-elf\bin")
COMPILER = BIN / "xtensa-esp32s3-elf-g++.exe"
SIZE = BIN / "xtensa-esp32s3-elf-size.exe"
NAMES = ("minimal.cpp", "bounded.hpp")
COMMON = ["-std=c++17", "-mlongcalls", "-ffunction-sections", "-fdata-sections", "-fexceptions", "-fstack-usage", "-Wall", "-Wextra", "-Werror", "-c"]

def pins():
    result = []
    for name in NAMES:
        path = SOURCE / name
        data = path.read_bytes()
        result.append({"name": name, "path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return result

def run(command, cwd, env, stdout_path, stderr_path):
    start = time.monotonic()
    proc = subprocess.run(command, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
    seconds = time.monotonic() - start
    stdout_path.write_bytes(proc.stdout)
    stderr_path.write_bytes(proc.stderr)
    return proc.returncode, seconds

before = pins()
TEMP.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env["TEMP"] = str(TEMP)
env["TMP"] = str(TEMP)
runs = []
for opt in ("-Os", "-O2", "-O3"):
    label = opt[1:]
    folder = OUT / label
    folder.mkdir(parents=True, exist_ok=True)
    obj = folder / "minimal.o"
    command = [str(COMPILER), *COMMON[:1], opt, *COMMON[1:], "minimal.cpp", "-o", str(obj)]
    rc, seconds = run(command, SOURCE, env, folder / "compile.stdout.log", folder / "compile.stderr.log")
    entry = {"optimization": opt, "command": command, "returnCode": rc, "seconds": round(seconds, 4), "timedOut": False, "objectPath": str(obj), "objectExists": obj.exists()}
    su = folder / "minimal.su"
    entry["stackUsageExists"] = su.exists()
    if su.exists():
        entry["stackUsagePath"] = str(su)
        entry["stackUsageText"] = su.read_text(encoding="utf-8", errors="replace")
    if obj.exists():
        entry["objectBytes"] = obj.stat().st_size
        size_cmd = [str(SIZE), "-A", str(obj)]
        size_rc, size_sec = run(size_cmd, folder, env, folder / "size.stdout.log", folder / "size.stderr.log")
        entry["sizeCommand"] = size_cmd
        entry["sizeReturnCode"] = size_rc
        entry["sizeSeconds"] = round(size_sec, 4)
        entry["sizeStdout"] = (folder / "size.stdout.log").read_text(encoding="utf-8", errors="replace")
    else:
        err = (folder / "compile.stderr.log").read_text(encoding="utf-8", errors="replace")
        entry["failureClass"] = "-Werror=maybe-uninitialized" if "maybe-uninitialized" in err else "compiler failure"
    runs.append(entry)
after = pins()
changed = [b["name"] for b, a in zip(before, after) if (b["bytes"], b["sha256"]) != (a["bytes"], a["sha256"])]
result = {
    "schema": "native-optional-lifetime-repro-v1",
    "status": "FAIL_SOURCE_CHANGED" if changed else "SOURCE_UNCHANGED",
    "sourceRoot": str(SOURCE), "sourceHashesBefore": before, "sourceHashesAfter": after, "sourceChanged": changed,
    "compiler": str(COMPILER), "sizeTool": str(SIZE), "commonFlags": COMMON, "optimizationOnlyDiff": ["-Os", "-O2", "-O3"],
    "runs": runs, "tempDirectory": str(TEMP),
    "scope": "Compile only the reduced minimal.cpp as isolated Xtensa objects; no link, firmware build, hardware, or source edits.",
    "initialHarnessAttempt": "A first PowerShell native-command redirection attempt captured artifacts but PowerShell surfaced native stderr as an error record before recording return codes. Those Os/O2 artifacts are preserved in initial-harness-attempt. Final command and status records below come from subprocess.run with byte-captured stdout/stderr."
}
(ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
for item in runs:
    print(f"{item['optimization']} rc={item['returnCode']} seconds={item['seconds']} object={item['objectExists']} stackUsage={item['stackUsageExists']}" + (f" bytes={item.get('objectBytes')}" if item.get('objectExists') else f" cause={item.get('failureClass')}"))
print("sourceHashesUnchanged=" + str(not changed).lower())
