#!/usr/bin/env python3
"""Build and verify the V91 elastic Rice component in the existing container.

Only source/log/JSON artifacts are retained in the repository. Compiled objects
and binaries stay under the container's /build. Each invocation preserves its
own attempt, including failed compile or simulation logs.
"""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid


ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v91"
CONTAINER = "gamebub-cu66-v69-build"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=910032)
    parser.add_argument("--vectors", type=Path,
                        default=ROOT / "experiments/python-gamebub-v91/rtl-vectors/cases.jsonl.gz")
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    name = stamp + "-" + uuid.uuid4().hex[:8]
    out = AREA / "attempts" / name
    out.mkdir(parents=True)
    build = "/build/v91-rtl-" + name
    sources = [Path(__file__).resolve(), AREA / "br88_rice_elastic.sv", AREA / "tb_rice.cpp"]
    report = dict(schema="cu66-v91-elastic-rice-rtl-v1", status="FAIL", seed=args.seed,
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  vectors=str(args.vectors.relative_to(ROOT)), vectors_sha256=sha(args.vectors),
                  build_directory=build, commands=[],
                  fence="stream_start edge excluded; every subsequent rising edge through final response delivery included",
                  scope="Behavioral symbol component, not whole packet CRC/scatter/decoder or routed hardware timing.")
    started = time.monotonic()

    def command(argv, log_name, timeout):
        with (out / log_name).open("w") as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        report["commands"].append(dict(argv=argv, exit_code=result.returncode, log=log_name))
        if result.returncode:
            raise RuntimeError(f"Command failed ({result.returncode}); see {out / log_name}")

    try:
        command(["docker", "exec", CONTAINER, "verilator", "--version"], "tool-version.log", 30)
        command(["docker", "exec", CONTAINER, "g++", "--version"], "compiler-version.log", 30)
        text_vectors = out / "vectors.txt"
        cases = requests = 0
        with gzip.open(args.vectors, "rt") as stream, text_vectors.open("w") as target:
            for line in stream:
                case = json.loads(line)
                target.write(f"{case['id']} {case['bit_size']} {case['data_hex'] or '-'} {len(case['requests'])}\n")
                for request in case["requests"]:
                    target.write(" ".join(map(str, request)) + "\n")
                cases += 1
                requests += len(case["requests"])
        report.update(vector_cases=cases, vector_requests=requests,
                      text_vectors_sha256=sha(text_vectors))
        command(["docker", "exec", CONTAINER, "verilator", "--cc", "--exe", "--build", "-j", "2",
                 "--assert", "-Wall", "-Wno-fatal", "--top-module", "br88_rice_elastic",
                 "--Mdir", build, "-CFLAGS", "-std=c++17 -O2 -Wall -Wextra",
                 str(AREA / "br88_rice_elastic.sv"), str(AREA / "tb_rice.cpp")], "compile.log", 300)
        command(["docker", "exec", CONTAINER, build + "/Vbr88_rice_elastic", str(text_vectors), str(args.seed)],
                "simulation.jsonl", 300)
        rows = [json.loads(line) for line in (out / "simulation.jsonl").read_text().splitlines()]
        verdicts = [r for r in rows if r["type"] == "verdict"]
        assert len(verdicts) == 1 and verdicts[0]["status"] == "TEST_PASS"
        assert verdicts[0]["cases"] == cases and verdicts[0]["requests_per_configuration"] == requests
        case_rows = [r for r in rows if r["type"] == "case"]
        assert len(case_rows) == cases * 8
        totals = [r for r in rows if r["type"] == "total"]
        ratios = []
        for word in (16, 32):
            for stalls in (0, 1):
                fast = next(r for r in totals if not r["serial"] and r["word_bits"] == word and r["stalls"] == stalls)
                serial = next(r for r in totals if r["serial"] and r["word_bits"] == word and r["stalls"] == stalls)
                assert fast["input_accepted"] == serial["input_accepted"]
                assert fast["symbols"] == serial["symbols"] == requests
                assert fast["consumed_bits"] == serial["consumed_bits"]
                ratios.append(dict(word_bits=word, stalls=stalls, fast_cycles=fast["cycles"],
                                   serial_cycles=serial["cycles"], serial_over_fast=serial["cycles"] / fast["cycles"]))
        report.update(status="PASS_COMPONENT_SIMULATION", verdict=verdicts[0], totals=totals, comparisons=ratios)
        # Keep the compact reproducible gzip oracle instead of a second 7MB text copy.
        text_vectors.unlink()
        assert report["source_sha256"] == {str(p.relative_to(ROOT)): sha(p) for p in sources}
    finally:
        report["wall_seconds"] = time.monotonic() - started
        report["artifacts_sha256"] = {str(p.relative_to(out)): sha(p) for p in out.rglob("*") if p.is_file()}
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
        selected = dict(report, selected_report=str((out / "results.json").relative_to(ROOT)))
        (AREA / "results.json").write_text(json.dumps(selected, indent=2) + "\n")
        print("V91_RTL_REPORT", out / "results.json", report["status"], flush=True)


if __name__ == "__main__":
    main()
