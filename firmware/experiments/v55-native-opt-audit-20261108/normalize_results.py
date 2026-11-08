import hashlib,json,pathlib,re,datetime
O=pathlib.Path(r"C:\moon\dev\experiments\v55-native-opt-audit-20261108")
raw=json.loads((O/"initial-raw-result.json").read_text(encoding="utf-8"))
def frame_bytes(lines,key):
    for line in lines:
        if key in line:
            m=re.search(r"\t(\d+)\tstatic\s*$",line)
            return int(m.group(1)) if m else None
    return None
for run in raw["runs"]:
    opt=run["optimization"]
    if run.get("su"):
        frames=run["su"]["selected_frames"]
        run["su"]["selected_frame_bytes"]={key:frame_bytes(lines,key) for key,lines in frames.items()}
    if run.get("size",{}).get("stdout"):
        rows=[]
        for line in run["size"]["stdout"].splitlines():
            m=re.match(r"^\s*(\.[^\s]+)\s+(\d+)\s+\d+\s*$",line)
            if m: rows.append({"section":m.group(1),"bytes":int(m.group(2))})
        by={}
        for row in rows:
            name=row["section"]
            cls=name.split('.')[1] if name.startswith('.') else name
            by[cls]=by.get(cls,0)+row["bytes"]
        run["section_summary"]={"total_reported_bytes":next((int(x.split()[-1]) for x in run["size"]["stdout"].splitlines() if x.strip().startswith("Total ")),None),"section_class_bytes":by,"sections":rows}
    if run.get("nm",{}).get("stdout"):
        syms=[]
        for line in run["nm"]["stdout"].splitlines():
            m=re.match(r"^\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\w\s+(.+)$",line)
            if m and any(k in m.group(3) for k in ("cu66::huffman(","cu66::channel33(","v34::Endpoint::transact(","v34_hud_transact")):
                syms.append({"bytes":int(m.group(2),16),"symbol":m.group(3)})
        run["selected_symbol_sizes"]=syms
    stderr=pathlib.Path(run["logs"]["stderr"]).read_text(encoding="utf-8",errors="replace")
    if run["compile"]["returncode"] != 0:
        run["compile"]["failure_class"]="-Werror=maybe-uninitialized" if "maybe-uninitialized" in stderr else "compiler_error"
        run["compile"]["diagnostic_excerpt"]="; ".join([x.strip() for x in stderr.splitlines() if "error:" in x][:3])
keys=("huffman(","channel33(","Endpoint::transact(","v34_hud_transact(")
base=next(x for x in raw["runs"] if x["optimization"]=="-Os")
ref=pathlib.Path(raw["selected_v55_su_comparison"]["path"]).read_text(encoding="utf-8",errors="replace").splitlines()
base_lines=pathlib.Path(base["su"]["path"]).read_text(encoding="utf-8",errors="replace").splitlines()
comp={k:{"captured_bytes":frame_bytes(ref,k),"recompiled_os_bytes":frame_bytes(base_lines,k),"match":frame_bytes(ref,k)==frame_bytes(base_lines,k)} for k in keys}
raw["selected_v55_su_comparison"]={"path":raw["selected_v55_su_comparison"]["path"],"exists":True,"bytes":pathlib.Path(raw["selected_v55_su_comparison"]["path"]).stat().st_size,"sha256":hashlib.sha256(pathlib.Path(raw["selected_v55_su_comparison"]["path"]).read_bytes()).hexdigest(),"named_frame_comparison":comp}
raw["status"]="OS_BASELINE_PASS_O2_O3_COMPILE_FAIL" if base["compile"]["returncode"]==0 and all(comp[k]["match"] for k in keys) and not raw["source_changed"] else "AUDIT_FAILURE"
raw["initial_launcher_failure"]={"requested_tool_directory":r"C:\Users\lavat\.espressif\tools\xtensa-esp-elf\esp-14.2.0_20250730\xtensa-esp32s3-elf\bin","reason":"That directory name is absent on this host; no compiler process started.","resolved_installed_directory":str(pathlib.Path(raw["toolchain"]))}
raw["recommendation"]="Do not select O2/O3 from this audit: both fail the unchanged -Wall -Wextra -Werror compile on GCC maybe-uninitialized diagnostics. -Os reproduces the captured V55 per-function frames; no link, app-level code size, speed, or runtime stack data was obtained. A later candidate is justified only if warning handling is separately reviewed and linked target measurements show a useful code/stack tradeoff with all existing gates retained. No optimization is selected here."
raw["noncompile_outputs"]="For failed O2/O3 runs, size/nm/.su do not exist; compile stderr logs are preserved. -Os has isolated object, section report, nm output, and .su."
(O/"result.json").write_text(json.dumps(raw,indent=2)+"\n",encoding="utf-8")
requested=pathlib.Path(r"C:\Users\lavat\.espressif\tools\xtensa-esp-elf\esp-14.2.0_20250730\xtensa-esp32s3-elf\bin")
launch={"status":"FAILED_BEFORE_PROCESS_START","requested_tool_directory":str(requested),"directory_exists":requested.exists(),"observed_error":"WinError 2 FileNotFoundError; no compiler invocation occurred","resolved_tool_directory":raw["toolchain"]}
(O/"initial-launch-failure.json").write_text(json.dumps(launch,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":raw["status"],"runs":[{"opt":x["optimization"],"rc":x["compile"]["returncode"],"seconds":x["compile"]["seconds"],"object_bytes":x.get("object",{}).get("bytes"),"frames":x.get("su",{}).get("selected_frame_bytes"),"symbols":x.get("selected_symbol_sizes",[])} for x in raw["runs"]],"capturedSuComparison":comp,"sourceChanged":raw["source_changed"]},indent=2))
