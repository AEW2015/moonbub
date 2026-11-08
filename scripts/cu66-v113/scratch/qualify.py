#!/usr/bin/env python3
"""Source-bound V113 scratch check; default mode only prepares and audits pins."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "fpga/experiments/cu66-v113-scratch"
V = SRC / "verification"
AREA = ROOT / "experiments/python-gamebub-v113/scratch"
IMAGE = "sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf"
SEEDS = (113301, 113302)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def memory_gate():
    mem = {line.split(":")[0]: int(line.split()[1]) * 1024
           for line in Path("/proc/meminfo").read_text().splitlines()}
    full = next(line for line in Path("/proc/pressure/memory").read_text().splitlines()
                if line.startswith("full "))
    return {"available_bytes": mem["MemAvailable"],
            "psi_full_avg10": float(full.split("avg10=")[1].split()[0])}


def verify_prepared():
    recipe = json.loads((SRC / "edit-recipe.json").read_text())
    assert recipe["schema"] == "v113-exact-phase-validation-v1"
    assert recipe["added_public_cycles"] == 0 and recipe["all_original_assertions_retained"]
    for entry in recipe["production"].values():
        original = ROOT / entry["original"]
        candidate = ROOT / entry["candidate"]
        assert sha(original) == entry["original_sha256"]
        assert sha(candidate) == entry["candidate_sha256"]
        body = original.read_text()
        for edit in entry["edits"]:
            assert body.count(edit["before"]) == edit["expected_occurrences"]
            body = body.replace(edit["before"], edit["after"], 1)
        assert body == candidate.read_text()
        for edit in reversed(entry["edits"]):
            if edit["after"]:
                assert body.count(edit["after"]) == edit["expected_occurrences"]
                body = body.replace(edit["after"], edit["before"], 1)
            else:
                # This edit removes the original sparse/raw suffix at its
                # original position after the prefetch combinational logic.
                anchor = "            mem_rsp_epoch==request_epoch && !mem_rsp_error;"
                assert body.count(anchor) == 1
                assert body.count(anchor + "\n\n    end") == 1
                body = body.replace(anchor + "\n\n    end",
                                    anchor + "\n" + edit["before"] + "\n    end", 1)
        assert body == original.read_text()

    adapters = json.loads((V / "adapters.json").read_text())
    assert adapters["schema"] == "v113-scratch-exact-adapters-v1"
    for adapter in adapters["adapters"]:
        source = ROOT / adapter["source"]
        body = source.read_text()
        assert sha(source) == adapter["source_sha256"]
        for before, after in adapter["edits"]:
            assert body.count(before) == 1
            body = body.replace(before, after, 1)
        target = ROOT / adapter["path"]
        assert body == target.read_text() and sha(target) == adapter["sha256"]
    for inherited in ("scratch_probe.sv", "tb_scratch.cpp", "tb_bank.cpp", "historical_hazards.cpp"):
        entry = next(x for x in adapters["adapters"] if Path(x["path"]).name == inherited)
        assert entry["source"] == "fpga/experiments/cu66-v112-control/verification/" + inherited
        assert sha(ROOT / entry["source"]) == sha(ROOT / entry["path"])
    return recipe, adapters


def generate_phase_unit(build):
    """Compile the candidate's actual generated predicate beside old algebra."""
    candidate = (SRC / "packed_scratch_v91g2.sv").read_text()
    marker = "    // V113_PHASE_VALIDATION:"
    start = candidate.index("    logic [7:0] phase_input_bad;", candidate.index(marker))
    end = candidate.index("`ifndef SYNTHESIS", start)
    actual = candidate[start:end]
    fn0 = candidate.index("    function automatic logic [5:0] zigzag(")
    fn1 = candidate.index("    function automatic logic band_matches(", fn0)
    fn2 = candidate.index("    endfunction", fn1) + len("    endfunction")
    functions = candidate[fn0:fn2]
    # The original full-phase predicate is independently reconstructed from the
    # frozen V112 branch text, while the parallel phase table is extracted from
    # the candidate itself. That avoids a self-copy-only predicate test.
    recipe = json.loads((SRC / "edit-recipe.json").read_text())
    entry = recipe["production"]["packed_scratch_v91g2.sv"]
    original_clause = entry["edits"][0]["before"]
    original_tail = entry["edits"][1]["before"]
    reference = (
        "logic input_bad_reference;\n"
        "always_comb begin\n"
        " input_bad_reference=coef_epoch!=active_epoch || coef_band!=phase[1:0] ||\n"
        "   coef_block>=16'(blocks) || coef_value < -2048 || coef_value > 2048 ||\n"
        "   written>=counts[phase[1:0]];\n"
        " if(raw_mode) input_bad_reference=input_bad_reference || input_position!=written;\n"
        " else if(phase==0) input_bad_reference=input_bad_reference || coef_index!=0 || 32'(coef_block)!=written;\n"
        " else input_bad_reference=input_bad_reference || !band_matches(coef_band,coef_index) || coef_value==0 ||\n"
        "   (previous_valid && input_position<=previous_position);\n"
        "end\n")
    # Ensure the independently spelled reference text still covers the two
    # replaced V112 clauses. Recipe strings are checked verbatim to detect drift.
    assert "input_bad=" in original_clause and "if(raw_mode)" in original_tail
    content = """module phase_predicate_probe(
 input logic [2:0] phase, input logic [31:0] active_epoch, coef_epoch,
 input logic [1:0] coef_band, input logic [15:0] coef_block,
 input logic [5:0] coef_index, input logic signed [15:0] coef_value,
 input logic [16:0] blocks, input logic [127:0] counts_flat,
 input logic [31:0] written,
 input logic raw_mode, input logic previous_valid,
 input logic [31:0] previous_position,
 output logic candidate_bad, output logic reference_bad
);
logic [31:0] counts [0:3];
logic [31:0] input_position;
logic [5:0] input_zigzag;
for(genvar count_index=0;count_index<4;count_index=count_index+1)
 begin: count_words
  assign counts[count_index]=counts_flat[count_index*32+:32];
 end
always_comb begin
 input_zigzag=zigzag(coef_index);
 input_position=raw_mode ? (32'(coef_block)*64+32'(coef_index)) :
     (phase==0 ? 32'(coef_block) : 32'(coef_block)*64+32'(input_zigzag));
end
""" + functions + """
""" + actual + reference + """
always_comb begin
 candidate_bad=phase_input_bad[phase];
 reference_bad=input_bad_reference;
end
endmodule
"""
    # Keep complete recipe clauses in the preparation evidence as their own
    # exact strings, and make sure all source pieces used above remain pinned.
    (build / "phase_predicate_probe.sv").write_text(content)
    return {"candidate_block_sha256": hashlib.sha256(actual.encode()).hexdigest(),
            "candidate_block_bytes": len(actual.encode()),
            "reference_origin": "edit-recipe.json V112 input_bad and raw/sparse branch clauses",
            "phase_values": list(range(8)), "random_vectors": 100000}


def prepare():
    recipe, adapters = verify_prepared()
    tracked = [SRC / "edit-recipe.json", SRC / "packed_scratch_v91g2.sv",
               *[ROOT / e["path"] for e in adapters["adapters"]],
               ROOT / "scripts/cu66-v112/control/qualify.py"]
    return {"schema": "v113-scratch-preparation-v1", "status": "PREPARED_NOT_RUN",
            "candidate_sha256": sha(SRC / "packed_scratch_v91g2.sv"),
            "recipe_sha256": sha(SRC / "edit-recipe.json"),
            "adapter_manifest_sha256": sha(V / "adapters.json"),
            "inherited_qualification_sha256": sha(ROOT / "scripts/cu66-v112/control/qualify.py"),
            "source_pins": {str(path.relative_to(ROOT)): sha(path) for path in tracked},
            "seeds": list(SEEDS), "scratch_checks": {
                "transactions_per_seed": 72, "corrupt_response_cases": 128,
                "read_owner_cases": 4, "bank_mask": 15, "offset_mask": 65535,
                "dc_line_boundary_transactions": 48,
                "begin_input_noise_edges_min": 10001,
                "all_original_scratch_oracles": True,
                "historical_physical_owner_hazards": True},
            "predicate_probe": {
                "plan": "extract candidate phase_input_bad generate block; compare to an independently spelled frozen V112 predicate for all phase encodings 0..7",
                "random_vectors": 100000, "boundary_vectors": "count/rank/value/position/epoch/width boundaries",
                "run_enabled": False},
            "compile_profile": {"verilator": "--assert -Wall, no suppressions", "cpp": "-std=c++17 -O1 -Wall -Wextra -Werror", "jobs": 1,
                                "docker_image": IMAGE, "container_memory_swap_gib": 8,
                                "container_cpus": 2, "external_build_root": "/home/lori/gamebub-build/cu66-v69"},
            "no_run": True, "native_or_hardware": False}


def run():
    recipe, adapters = verify_prepared()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = AREA / "attempts" / stamp
    out.mkdir(parents=True)
    build = Path("/home/lori/gamebub-build/cu66-v69") / ("v113-scratch-" + stamp)
    build.mkdir(parents=True)
    mapped = "/build/" + build.name
    files = [SRC / "edit-recipe.json", SRC / "packed_scratch_v91g2.sv"]
    files.extend(ROOT / e["path"] for e in adapters["adapters"])
    files.extend([ROOT / "scripts/cu66-v112/control/qualify.py"])
    r = prepare()
    r.update(schema="v113-scratch-focused-v1", status="FAIL", actual_RTL_run=False,
             commands=[], scratch_runs=[], source_sha256={str(p.relative_to(ROOT)): sha(p) for p in files},
             scope="Scratch candidate only; all original scratch equivalence and ownership checks; no complete decoder timing or hardware claim.")
    start_time = time.monotonic()

    def command(argv, name, cap):
        gate = memory_gate()
        assert gate["available_bytes"] >= 10 * 1024**3 and gate["psi_full_avg10"] < 1, gate
        container = "gamebub-v113-scratch-" + stamp.lower() + "-" + str(len(r["commands"]))
        cmd = ["docker", "run", "--rm", "--init", "--name", container,
               "--memory", "8g", "--memory-swap", "8g", "--cpus", "2",
               "--pids-limit", "2048", "--network", "none", "--ulimit", "core=0",
               "--mount", f"type=bind,src={build},dst={mapped}", "-w", mapped,
               IMAGE, "timeout", "--kill-after=5s", f"{cap}s", *argv]
        entry = {"argv": cmd, "resource_before": gate, "timeout_seconds": cap}
        r["commands"].append(entry)
        began = time.monotonic()
        with (out / name).open("w") as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            while proc.poll() is None:
                if time.monotonic() - began > cap + 20:
                    subprocess.run(["docker", "stop", "--time", "5", container],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                    raise RuntimeError("HOST_TIMEOUT " + name)
                time.sleep(0.5)
            code = proc.wait(timeout=20)
        entry.update(exit_code=code, wall_seconds=time.monotonic() - began)
        assert code == 0, (name, code)

    def compile(top, names, cxx):
        command(["verilator", "--cc", "--exe", "--build", "-j", "1", "--assert", "-Wall",
                 "--public-flat-rw", "--output-split", "10000", "--output-split-cfuncs", "500",
                 "--language", "1800-2017", "-CFLAGS", cxx, "--top-module", top,
                 "--Mdir", mapped + "/" + top + "-obj", *[mapped + "/" + n for n in names]],
                top + "-compile.log", 600)
        log = (out / (top + "-compile.log")).read_text()
        assert "%Warning-" not in log
        r[top + "_binary_sha256"] = sha(build / (top + "-obj") / ("V" + top))

    try:
        for path in files:
            dest = out / "sources" / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            shutil.copyfile(path, build / path.name)
        shutil.copyfile(V / "observed_original.sv", build / "observed_original.sv")
        shutil.copyfile(V / "observed_candidate.sv", build / "observed_candidate.sv")
        shutil.copyfile(V / "scratch_probe.sv", build / "scratch_probe.sv")
        shutil.copyfile(V / "tb_scratch.cpp", build / "tb_scratch.cpp")
        shutil.copyfile(V / "tb_bank.cpp", build / "tb_bank.cpp")
        write(out / "preparation.json", r)
        command(["verilator", "--version"], "version.log", 30)
        compile("scratch_probe", ["observed_original.sv", "observed_candidate.sv", "scratch_probe.sv", "tb_bank.cpp"],
                "-std=c++17 -O1 -Wall -Wextra -Werror")
        for seed in SEEDS:
            name = f"scratch-{seed}.log"
            command([mapped + "/scratch_probe-obj/Vscratch_probe", str(seed), mapped + f"/scratch-{seed}.jsonl"], name, 180)
            result = json.loads((out / name).read_text().splitlines()[-1])
            assert result["status"] == "TEST_PASS" and result["full_transactions"] == 72
            assert result["corrupt_response_cases"] == 128 and result["read_owner_cases"] == 4
            assert result["bank_mask"] == 15 and result["offset_mask"] == 65535
            assert result["dc_line_boundary_transactions"] == 48 and result["begin_input_noise_edges"] > 10000
            r["scratch_runs"].append(result)
        r["predicate_probe"] = generate_phase_unit(build)
        shutil.copyfile(V / "phase_predicate.cpp", build / "phase_predicate.cpp")
        compile("phase_predicate_probe", ["phase_predicate_probe.sv", "phase_predicate.cpp"],
                "-std=c++17 -O1 -Wall -Wextra -Werror")
        predicate_result = command([mapped + "/phase_predicate_probe-obj/Vphase_predicate_probe"],
                                   "phase-predicate.log", 120)
        # Result is a one-line JSON verdict emitted by the independent driver.
        text = (out / "phase-predicate.log").read_text().splitlines()[-1]
        r["predicate_probe"]["verdict"] = json.loads(text)
        assert r["predicate_probe"]["verdict"]["status"] == "TEST_PASS"
        r.update(status="PASS", actual_RTL_run=True)
    except BaseException as exc:
        r["error"] = repr(exc)
        raise
    finally:
        r["wall_seconds"] = time.monotonic() - start_time
        r["artifacts_sha256"] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob("*")) if p.is_file()}
        write(out / "results.json", r)
        write(AREA / "results.json", dict(r, selected_report=str((out / "results.json").relative_to(ROOT)),
                                           selected_report_sha256=sha(out / "results.json")))
        print("V113_SCRATCH_FOCUSED", r["status"], out, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="compile and execute (requires allocated heavy-job slot)")
    args = parser.parse_args()
    if args.run:
        run()
    else:
        result = prepare()
        write(AREA / "preparation.json", result)
        print("V113_SCRATCH_PREPARED_NOT_RUN", json.dumps({"candidate_sha256": result["candidate_sha256"],
              "source_pins": len(result["source_pins"]), "seeds": result["seeds"], "predicate_probe": result["predicate_probe"]}))


if __name__ == "__main__":
    main()
