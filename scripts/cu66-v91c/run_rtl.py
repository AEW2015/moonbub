#!/usr/bin/env python3
"""Build and verify the V91c packet wrapper in the existing container.

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
import shutil
import subprocess
import time
import uuid


ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v91c"
CONTAINER = "gamebub-cu66-v69-build"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=910232)
    parser.add_argument("--vectors", type=Path,
                        default=ROOT / "experiments/python-gamebub-v91c/packet-vectors/packets.jsonl.gz")
    args = parser.parse_args()
    args.vectors = args.vectors.resolve()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    name = stamp + "-" + uuid.uuid4().hex[:8]
    out = AREA / "attempts" / name
    out.mkdir(parents=True)
    build = "/build/v91c-rtl-" + name
    sources = [Path(__file__).resolve(), ROOT / "fpga/experiments/cu66-v91/br88_rice_elastic.sv", ROOT / "fpga/experiments/cu66-v91b/br88_context.sv", AREA / "br88_packet.sv", AREA / "tb_packet.cpp"]
    report = dict(schema="cu66-v91c-packet-rtl-v1", status="FAIL", seed=args.seed,
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  vectors=str(args.vectors.relative_to(ROOT)), vectors_sha256=sha(args.vectors),
                  build_directory=build, commands=[],
                  source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  fence="start edge excluded; every byte-input/CRC/metadata/replay/context/output edge through sticky packet done included",
                  scope="Bounded complete BR88 packet simulation including CRC/metadata and autonomous replay; no live ingress, framegraph, synthesis, memory-fit, reconstruction, or physical claim.")
    started = time.monotonic()
    for source in sources:
        snapshot = out / "sources" / source.relative_to(ROOT)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, snapshot)
    shutil.copyfile(args.vectors, out / "cases.jsonl.gz")
    vector_index = args.vectors.with_name("index.json")
    if vector_index.exists():
        report["vector_index_sha256"] = sha(vector_index)
        shutil.copyfile(vector_index, out / "index.json")

    def command(argv, log_name, timeout):
        record = dict(argv=argv, exit_code=None, log=log_name)
        report["commands"].append(record)
        with (out / log_name).open("w") as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        record["exit_code"] = result.returncode
        if result.returncode:
            raise RuntimeError(f"Command failed ({result.returncode}); see {out / log_name}")

    try:
        command(["docker", "exec", CONTAINER, "verilator", "--version"], "tool-version.log", 30)
        command(["docker", "exec", CONTAINER, "g++", "--version"], "compiler-version.log", 30)
        text_vectors = out / "vectors.txt"
        cases = requests = 0
        actual_cases = 0
        with gzip.open(out / "cases.jsonl.gz", "rt") as stream, text_vectors.open("w") as target:
            for line in stream:
                case = json.loads(line)
                expected = case.get("expected", case.get("outputs"))
                assert expected is not None
                target.write(" ".join(map(str, (case["id"], case["blocks"], case["packet_hex"], case.get("expected_error", 0), len(expected)))) + "\n")
                for coefficient in expected:
                    target.write(" ".join(map(str, coefficient)) + "\n")
                cases += 1
                actual_cases += case["id"].startswith("actual:")
                requests += len(expected)
        report.update(vector_cases=cases, vector_requests=requests,
                      text_vectors_sha256=sha(text_vectors), actual_packets=actual_cases)
        command(["docker", "exec", CONTAINER, "verilator", "--cc", "--exe", "--build", "-j", "2",
                 "--assert", "-Wall", "--top-module", "br88_packet",
                 "--Mdir", build, "-CFLAGS", "-std=c++17 -O2 -Wall -Wextra -Werror",
                 str(out / "sources" / "fpga/experiments/cu66-v91/br88_rice_elastic.sv"),
                 str(out / "sources" / "fpga/experiments/cu66-v91b/br88_context.sv"),
                 str(out / "sources" / (AREA / "br88_packet.sv").relative_to(ROOT)),
                 str(out / "sources" / (AREA / "tb_packet.cpp").relative_to(ROOT))], "compile.log", 300)
        command(["docker", "exec", CONTAINER, build + "/Vbr88_packet", str(text_vectors), str(args.seed)],
                "simulation.jsonl", 300)
        rows = [json.loads(line) for line in (out / "simulation.jsonl").read_text().splitlines()]
        verdicts = [r for r in rows if r["type"] == "verdict"]
        assert len(verdicts) == 1 and verdicts[0]["status"] == "TEST_PASS"
        assert verdicts[0]["cases"] == cases and verdicts[0]["outputs_per_configuration"] == requests
        case_rows = [r for r in rows if r["type"] == "case"]
        assert len(case_rows) == cases * 8
        totals = [r for r in rows if r["type"] == "total"]
        grouped = {}
        counters = ("cycles", "input_accepted", "outputs", "output_stall")
        for row in case_rows:
            populations = ["actual" if row["id"].startswith("actual:") else "synthetic"]
            if populations[0] == "actual":
                populations.append(":".join(row["id"].split(":")[:3]))
            for population in populations:
                key = (population, row["word_bits"], row["serial"], row["stalls"])
                aggregate = grouped.setdefault(key, dict(population=population, word_bits=row["word_bits"],
                                                         serial=row["serial"], stalls=row["stalls"], streams=0,
                                                         **{field: 0 for field in counters}))
                aggregate["streams"] += 1
                for field in counters:
                    aggregate[field] += row[field]
        ratios = []
        for word in (16, 32):
            for stalls in (0, 1):
                fast = next(r for r in totals if not r["serial"] and r["word_bits"] == word and r["stalls"] == stalls)
                serial = next(r for r in totals if r["serial"] and r["word_bits"] == word and r["stalls"] == stalls)
                assert fast["input_accepted"] == serial["input_accepted"]
                assert fast["outputs"] == serial["outputs"] == requests
                ratios.append(dict(word_bits=word, stalls=stalls, fast_cycles=fast["cycles"],
                                   serial_cycles=serial["cycles"], serial_over_fast=serial["cycles"] / fast["cycles"] if fast["cycles"] else None))
        group_ratios = []
        for key, fast in grouped.items():
            population, word, serial, stalls = key
            if serial:
                continue
            control = grouped[(population, word, 1, stalls)]
            assert fast["input_accepted"] == control["input_accepted"]
            assert fast["outputs"] == control["outputs"]
            group_ratios.append(dict(population=population, word_bits=word, stalls=stalls,
                                     fast_cycles=fast["cycles"], serial_cycles=control["cycles"],
                                     serial_over_fast=control["cycles"] / fast["cycles"] if fast["cycles"] else None))
        report.update(verdict=verdicts[0], totals=totals, comparisons=ratios,
                      population_totals=list(grouped.values()), population_comparisons=group_ratios,
                      stall_schedule="Per-case FNV hash xor seed; xorshift64 exactly two draws/cycle for byte offer/output ready. All serial/word configurations share cycle-indexed offers/ready; byte producer holds until accepted. Context metadata and requests are derived internally.")
        # Keep the compact reproducible gzip oracle instead of a second 7MB text copy.
        text_vectors.unlink()
        assert report["source_sha256"] == {str(p.relative_to(ROOT)): sha(p) for p in sources}
        assert report["vectors_sha256"] == sha(args.vectors) == sha(out / "cases.jsonl.gz")
        if vector_index.exists():
            assert report["vector_index_sha256"] == sha(vector_index) == sha(out / "index.json")
        for source in sources:
            assert sha(out / "sources" / source.relative_to(ROOT)) == report["source_sha256"][str(source.relative_to(ROOT))]
        report["status"] = "PASS_PACKET_SIMULATION"
    except BaseException as error:
        report.update(status="FAIL", error_class=type(error).__name__, error=str(error))
        raise
    finally:
        report["wall_seconds"] = time.monotonic() - started
        report["artifacts_sha256"] = {str(p.relative_to(out)): sha(p) for p in out.rglob("*") if p.is_file()}
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
        selected = dict(report, selected_report=str((out / "results.json").relative_to(ROOT)))
        (AREA / "results.json").write_text(json.dumps(selected, indent=2) + "\n")
        print("V91C_RTL_REPORT", out / "results.json", report["status"], flush=True)


if __name__ == "__main__":
    main()
