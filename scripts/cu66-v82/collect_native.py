#!/usr/bin/env python3
"""Collect V82's frozen native tile oracle without touching V81 or earlier data."""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "experiments/python-gamebub-v82/native"
FROZEN = REPO / "experiments/cu66-native-v69"
PARENT = "83efb7ae627757aefdfd22e2a355720ff01bfb72"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(cmd, **kwargs):
    with (OUT / "commands.log").open("a") as log:
        log.write(json.dumps(cmd)+"\n")
    return subprocess.run(cmd, check=True, cwd=REPO, **kwargs)

def read_exact(stream, n):
    out = bytearray()
    while len(out)<n:
        part = stream.read(n-len(out))
        if not part:
            raise ValueError("truncated native stream")
        out.extend(part)
    return bytes(out)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/"data").mkdir(exist_ok=True)
    if (OUT/"index.json").exists():
        raise SystemExit("native/index.json already exists; refusing to overwrite frozen collection")
    (OUT/"commands.log").write_text("")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    container="gamebub-cu66-v69-build"
    binary=f"/build/v82-native-{stamp}"
    source=OUT/"collect_tiles.cpp"
    compile_cmd=["docker","exec",container,"g++","-std=c++17","-O2","-Wall","-Wextra","-Werror",str(source),"-o",binary]
    with (OUT/"compile.log").open("wb") as log:
        run(compile_cmd, stdout=log, stderr=subprocess.STDOUT)
    run(["docker","cp",f"{container}:{binary}",str(OUT/"collector.bin")],stdout=subprocess.DEVNULL)
    binary_hash=sha(OUT/"collector.bin")
    compiler=run(["docker","exec",container,"g++","--version"],capture_output=True,text=True).stdout
    (OUT/"compiler.txt").write_text(compiler)
    command=["docker","exec",container,binary,str(FROZEN/"index.tsv")]
    with (OUT/"commands.log").open("a") as log:
        log.write(json.dumps(command)+"\n")
    stderr=(OUT/"native.log").open("wb")
    process=subprocess.Popen(command,cwd=REPO,stdout=subprocess.PIPE,stderr=stderr)
    chunks=[]; records=[]; totals={"frames":0,"keys":0,"deltas":0,"copy_ref":0,"oracle_equal_visible_delta":0,"nonzero_equal_visible_delta":0,"hidden_tiles":0}
    chunk_data=bytearray(); chunk_records=0; cohort_counts=[0]*4
    def flush():
        nonlocal chunk_data,chunk_records
        if not chunk_records: return
        assert chunk_records<=32 and len(chunk_data)<17*1024*1024
        path=f"data/chunk-{len(chunks):03d}.bin.gz"
        compressed=gzip.compress(bytes(chunk_data),compresslevel=6,mtime=0)
        (OUT/path).write_bytes(compressed)
        chunks.append({"path":path,"record_count":chunk_records,"first_record":len(records)-chunk_records,"raw_bytes":len(chunk_data),"gzip_bytes":len(compressed),"raw_sha256":hashlib.sha256(chunk_data).hexdigest(),"gzip_sha256":hashlib.sha256(compressed).hexdigest()})
        chunk_data=bytearray();chunk_records=0
    try:
        while True:
            head=process.stdout.read(4)
            if not head: break
            if len(head)!=4: raise ValueError("truncated native header")
            n,=struct.unpack("<I",head)
            assert 1<=n<=16384
            metadata=read_exact(process.stdout,n)
            meta=json.loads(metadata)
            raw=read_exact(process.stdout,8100*68)
            tiles=raw[:8100*64]
            same,zero,hidden,copy=[raw[8100*64+i*8100:8100*64+(i+1)*8100] for i in range(4)]
            assert set(same+zero+hidden+copy)<={0,1}
            assert sum(hidden)==294
            assert sum(copy)==meta["copy_ref_count"]
            assert all(not c or (s and z and not h and not meta["key"]) for s,z,h,c in zip(same,zero,hidden,copy))
            assert all(tiles[i*64:(i+1)*64]==b'\x80'*64 for i,h in enumerate(hidden) if h)
            meta["tiles_sha256"]=hashlib.sha256(tiles).hexdigest()
            meta["masks_sha256"]=hashlib.sha256(same+zero+hidden+copy).hexdigest()
            # Preserve original native metadata verbatim in binary records. Index adds tile/mask digests.
            records.append(meta)
            chunk_data.extend(head+metadata+raw);chunk_records+=1
            totals["frames"]+=1;totals["keys"]+=int(meta["key"]);totals["deltas"]+=int(not meta["key"])
            totals["copy_ref"]+=sum(copy)
            totals["oracle_equal_visible_delta"]+=meta["same_visible_delta_count"]
            totals["nonzero_equal_visible_delta"]+=meta["nonzero_equal_visible_delta_count"]
            totals["hidden_tiles"]+=sum(hidden)
            cohort_counts[meta["cohort"]]+=1
            if chunk_records==32: flush()
        code=process.wait()
        if code: raise RuntimeError(f"collector exited {code}")
        flush()
    except BaseException:
        process.kill();process.wait();raise
    finally: stderr.close()
    assert totals["frames"]==457 and totals["keys"]==20 and totals["deltas"]==437
    assert cohort_counts==[119,119,119,100]
    source_paths=[source,OUT/"instrumented_decoder.hpp",OUT/"data.py",Path(__file__).resolve()]
    frozen_paths=[FROZEN/n for n in ("decoder.hpp","entropy.hpp","hud.hpp","bytes.hpp","generated_constants.hpp","index.tsv")]
    pins={str(p.relative_to(REPO)):sha(p) for p in source_paths+frozen_paths}
    frozen_commit_pins={}
    for p in frozen_paths:
        rel=str(p.relative_to(REPO))
        blob=run(["git","show",f"{PARENT}:{rel}"],capture_output=True).stdout
        assert hashlib.sha256(blob).hexdigest()==pins[rel], f"frozen file modified: {rel}"
        frozen_commit_pins[rel]=hashlib.sha256(blob).hexdigest()
    index={"schema":"cu66-v82-native-tiles-v1","parent":PARENT,"created_utc":stamp,"record_count":457,"cohort_counts":cohort_counts,"tile_counts":[5400,1350,1350],"tile_bytes":64,"mask_names":["same_mask","zero_coeff_mask","hidden_mask","copy_ref_mask"],"record_format":"uint32le JSON length; JSON UTF-8; 8100*64 tile bytes; four 8100-byte 0/1 masks in mask_names order","chunks":chunks,"frames":records,"totals":totals,"source_sha256":pins,"frozen_parent_sha256":frozen_commit_pins,"collector_binary_sha256":binary_hash,"compiler":compiler,"command":command,"capabilities":{"geometry":[720,480],"epoch":25,"zero_motion_only":True,"arithmetic_dispatch":[5,6]},"claims":{"packet_canonical_hud_display_verified":True,"instrumented_complete_planes_equal_frozen_decoder":True,"all_zero_copy_byte_equal_asserted":True,"physical_30fps_proven":False,"rtl_claim":False}}
    (OUT/"index.json").write_text(json.dumps(index,indent=2)+"\n")
    (OUT/"summary.json").write_text(json.dumps({"totals":totals,"cohort_counts":cohort_counts,"chunks":len(chunks),"gzip_bytes":sum(x["gzip_bytes"] for x in chunks),"max_raw_chunk_bytes":max(x["raw_bytes"] for x in chunks),"collector_binary_sha256":binary_hash},indent=2)+"\n")
    print(json.dumps(totals),flush=True)

if __name__=="__main__": main()
