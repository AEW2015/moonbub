import hashlib, json, pathlib, re, subprocess, time, datetime

ROOT = pathlib.Path(r"C:\moon\dev\experiments\v55-stb1-performance-20261108")
NATIVE = ROOT / "native"
OUT = pathlib.Path(r"C:\moon\dev\experiments\v55-native-opt-audit-20261108")
BIN = pathlib.Path(r"C:\Users\lavat\.espressif\tools\xtensa-esp-elf\esp-14.2.0_20250730\xtensa-esp-elf\bin")
V55_SU = pathlib.Path(r"C:\moon\publish\firmware\experiments\v55-dy71-stb1-performance-20261108\evidence\target-stack-v001\v34_hud.su")
FILES = sorted(p for p in NATIVE.iterdir() if p.is_file())

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd, cwd, timeout=75):
    start=time.perf_counter()
    try:
        p=subprocess.run([str(x) for x in cmd],cwd=str(cwd),capture_output=True,text=True,timeout=timeout)
        return {"command":[str(x) for x in cmd],"returncode":p.returncode,"seconds":round(time.perf_counter()-start,4),"stdout":p.stdout,"stderr":p.stderr,"timed_out":False}
    except subprocess.TimeoutExpired as e:
        return {"command":[str(x) for x in cmd],"returncode":None,"seconds":round(time.perf_counter()-start,4),"stdout":e.stdout or "","stderr":e.stderr or "","timed_out":True}

before={p.name: {"bytes":p.stat().st_size,"sha256":sha(p)} for p in FILES}
# Bind the exact current build command used by V55.
build_rs=ROOT / "handheld" / "build.rs"
build_text=build_rs.read_text(encoding="utf-8")
assert '"-std=c++17","-Os","-mlongcalls","-ffunction-sections","-fdata-sections","-fexceptions","-fstack-usage","-Wall","-Wextra","-Werror","-c"' in build_text
assert 'root.join("endpoint.cpp")' in build_text
build_binding={"path":str(build_rs),"bytes":build_rs.stat().st_size,"sha256":sha(build_rs)}
results=[]
for opt in ("Os","O2","O3"):
    d=OUT / opt
    d.mkdir(parents=True,exist_ok=True)
    obj=d/"endpoint.o"
    cmd=[BIN/"xtensa-esp32s3-elf-g++.exe","-std=c++17",f"-{opt}","-mlongcalls","-ffunction-sections","-fdata-sections","-fexceptions","-fstack-usage","-Wall","-Wextra","-Werror","-c","endpoint.cpp","-o",obj]
    c=run(cmd,NATIVE)
    (d/"compile.stdout.log").write_text(c["stdout"],encoding="utf-8")
    (d/"compile.stderr.log").write_text(c["stderr"],encoding="utf-8")
    rec={"optimization":"-"+opt,"compile":{k:v for k,v in c.items() if k not in ("stdout","stderr")},"logs":{"stdout":str(d/"compile.stdout.log"),"stderr":str(d/"compile.stderr.log")}}
    if c["returncode"] == 0 and obj.exists():
        for tool,label,args in (("xtensa-esp32s3-elf-size.exe","size",["-A",obj]),("xtensa-esp32s3-elf-nm.exe","nm",["-S","--size-sort","-C",obj])):
            tr=run([BIN/tool,*args],d)
            (d/f"{label}.stdout.log").write_text(tr["stdout"],encoding="utf-8")
            (d/f"{label}.stderr.log").write_text(tr["stderr"],encoding="utf-8")
            rec[label]={"command":tr["command"],"returncode":tr["returncode"],"seconds":tr["seconds"],"timed_out":tr["timed_out"],"stdout_log":str(d/f"{label}.stdout.log"),"stderr_log":str(d/f"{label}.stderr.log"),"stdout":tr["stdout"]}
        su=d/"endpoint.su"
        if su.exists():
            lines=su.read_text(encoding="utf-8",errors="replace").splitlines()
            rec["su"]={"path":str(su),"bytes":su.stat().st_size,"sha256":sha(su),"selected_frames":{}}
            for key in ("huffman(","channel33(","Endpoint::transact(","v34_hud_transact("):
                rec["su"]["selected_frames"][key]=[line for line in lines if key in line]
        rec["object"]={"path":str(obj),"bytes":obj.stat().st_size,"sha256":sha(obj)}
    else:
        rec["object"]={"path":str(obj),"exists":obj.exists()}
    results.append(rec)

after={p.name:{"bytes":p.stat().st_size,"sha256":sha(p)} for p in FILES}
changed=[name for name in before if before[name]!=after.get(name)]
# Compare -Os named static frames with the already preserved selected V55 .su.
base=next((x for x in results if x["optimization"]=="-Os"),None)
existing={"path":str(V55_SU),"exists":V55_SU.exists()}
if V55_SU.exists() and base and base.get("su"):
    ref=V55_SU.read_text(encoding="utf-8",errors="replace").splitlines()
    existing.update({"bytes":V55_SU.stat().st_size,"sha256":sha(V55_SU),"named_frame_matches":{key:next((ln for ln in ref if key in ln),None)==next((ln for ln in pathlib.Path(base["su"]["path"]).read_text(encoding="utf-8",errors="replace").splitlines() if key in ln),None) for key in ("huffman(","channel33(","Endpoint::transact(","v34_hud_transact(")}})
result={"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"status":"PASS" if all(x["compile"]["returncode"]==0 for x in results) and not changed else "FAIL_OR_SOURCE_CHANGED","scope":"Compile only exact frozen V55 native/endpoint.cpp as isolated object; no link, app build, target cache, Vivado or hardware","initial_launcher_failure":{"requested_tool_path":"C:\\Users\\lavat\\.espressif\\tools\\xtensa-esp-elf\\esp-14.2.0_20250730\\xtensa-esp-elf\\bin","failure":"Directory missing on installed host; process did not launch. Correct installed tool path was resolved to xtensa-esp-elf\\bin."},"source_root":str(NATIVE),"source_hashes_before":before,"source_hashes_after":after,"source_changed":changed,"build_rs_binding":build_binding,"toolchain":str(BIN),"optimization_flag_only_diff":["-Os","-O2","-O3"],"common_flags":["-std=c++17","-mlongcalls","-ffunction-sections","-fdata-sections","-fexceptions","-fstack-usage","-Wall","-Wextra","-Werror","-c"],"runs":results,"selected_v55_su_comparison":existing,"limitations":["No linking or application ELF size comparison.","Object code size is not a runtime speed measurement.","Static per-function frames do not prove complete call-chain or runtime stack safety.","No physical throughput or stack-safety claim."]}
(OUT/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":result["status"],"runs":[{"opt":r["optimization"],"rc":r["compile"]["returncode"],"seconds":r["compile"]["seconds"],"objectBytes":r.get("object",{}).get("bytes")} for r in results],"sourceChanged":changed,"suCompare":existing},indent=2))



