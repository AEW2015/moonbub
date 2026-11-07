#!/usr/bin/env python3
"""Build and verify fresh causal CU66 ledgers with the unchanged v69 decoder.

No Python participates in decode. All hashes, gzip and file I/O are outside the
C++ receive-to-published-RGB565 clock. Each invocation creates a new attempt;
failed attempts, logs and the external binary are retained.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/python-gamebub-v99/native/main.cpp"
OLD = ROOT / "experiments/cu66-native-v69"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def run(args: list[str], logfile: Path) -> None:
    with logfile.open("w") as log:
        p = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT)
    if p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}); retained log: {logfile}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True, help="new attempt directory; must not exist")
    ap.add_argument("--build-root", type=Path,
                    default=Path("/home/lori/gamebub-build/cu66-v69/v99"))
    ap.add_argument("--container", default="gamebub-cu66-v69-build")
    ap.add_argument("--adversarial", action="store_true", help="compatibility flag; always enabled")
    args = ap.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "started", "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "argv": sys.argv, "python": sys.version, "platform": platform.platform(),
               "timing_scope": "C++ steady_clock immediately before Decoder.receive to return with immutable Frame.display RGB565 complete",
               "timing_excludes": ["packet read", "adversarial trials", "golden verification", "hashing", "output write", "gzip", "Python orchestration"],
               "hardware_scope": "host CPU C++17; not FPGA, ESP32, wire, or end-to-end deployment timing",
               "capabilities": {"wrapper": "CU66/GU66 v1", "epoch": 25,
                    "base_motion": "zero only", "entropy_dispatch": [5, 6], "geometry": [720, 480]},
               "sources": {str(p.relative_to(ROOT)): sha(p) for p in
                    [SOURCE, Path(__file__).resolve(), *(OLD / n for n in
                    ("decoder.hpp", "bytes.hpp", "entropy.hpp", "hud.hpp", "generated_constants.hpp"))]}}
    write_json(output / "receipt.json", receipt)
    try:
        ledger = args.ledger.resolve()
        receipt["ledger"] = {"path": str(ledger), "sha256": sha(ledger)}
        host_compiler = shutil.which("g++")
        receipt["host_g++"] = host_compiler
        container = None
        mounts = []
        if host_compiler:
            compiler = [host_compiler]
            compiler_version = subprocess.check_output([host_compiler, "--version"], text=True)
        else:
            container = args.container
            info = json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]
            mounts = info["Mounts"]
            receipt["container"] = {"name": container, "id": info["Id"], "image_id": info["Image"],
                                    "configured_image": info["Config"]["Image"], "mounts": mounts}
            compiler = ["docker", "exec", container, "g++"]
            compiler_version = subprocess.check_output(compiler + ["--version"], text=True)
        receipt["compiler_version"] = compiler_version

        def mapped(path: Path) -> str:
            if not container:
                return str(path)
            for mount in sorted(mounts, key=lambda x: len(x["Source"]), reverse=True):
                try:
                    rel = path.relative_to(mount["Source"])
                    return str(Path(mount["Destination"]) / rel)
                except ValueError:
                    pass
            raise ValueError(f"path is outside existing container binds: {path}")

        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        build = args.build_root.resolve() / stamp
        build.mkdir(parents=True, exist_ok=False)
        binary = build / "native_decoder"
        compile_args = compiler + ["-std=c++17", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
                                   mapped(SOURCE), "-o", mapped(binary)]
        receipt["compile_command"] = compile_args
        receipt["build_directory"] = str(build)
        write_json(output / "receipt.json", receipt)
        run(compile_args, output / "compile.log")
        receipt["binary"] = {"path": str(binary), "sha256": sha(binary), "bytes": binary.stat().st_size}
        rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
        if not rows:
            raise ValueError("empty ledger")
        frames = output / "frames"
        frames.mkdir()
        manifests, expected, input_receipts = [], [], []
        closed, current = set(), None
        for index, row in enumerate(rows):
            clip = str(row["clip_id"])
            if not re.fullmatch(r"[A-Za-z0-9_.:-]+", clip):
                raise ValueError(f"unsafe clip ID: {clip!r}")
            if clip != current:
                if clip in closed:
                    raise ValueError("causal clips must be contiguous")
                if current is not None:
                    closed.add(current)
                current = clip
            packet = Path(row["packet_path"])
            if not packet.is_absolute():
                packet = ledger.parent / packet
            packet = packet.resolve()
            exp = row.get("expected", row)
            hashes = [exp[k] for k in ("canonical_sha256", "hud_sha256", "rgb565_sha256")]
            if any(not re.fullmatch(r"[a-f0-9]{64}", x) for x in hashes):
                raise ValueError("expected SHA256 must be 64 lowercase hexadecimal characters")
            fid = int(row["frame_id"])
            prefix = frames / f"{index:06d}"
            fields = [clip, str(fid), mapped(packet), *hashes,
                      exp.get("canonical_tag", "-"), mapped(prefix)]
            if any("\t" in x or "\n" in x for x in fields):
                raise ValueError("TSV fields cannot contain tabs or newlines")
            manifests.append("\t".join(fields))
            expected.append((row, prefix))
            input_receipts.append({"clip_id": clip, "frame_id": fid, "packet_path": str(packet),
                                   "packet_sha256": sha(packet), "packet_bytes": packet.stat().st_size,
                                   "expected": dict(zip(("canonical_sha256", "hud_sha256", "rgb565_sha256"), hashes))})
        manifest = output / "causal_manifest.tsv"
        manifest.write_text("\n".join(manifests) + "\n")
        write_json(output / "inputs.json", input_receipts)
        receipt["manifest_sha256"] = sha(manifest)
        write_json(output / "receipt.json", receipt)
        command = (["docker", "exec", container] if container else []) + [mapped(binary), mapped(manifest)]
        receipt["execute_command"] = command
        started = time.monotonic()
        with (output / "native.jsonl").open("w") as stdout, (output / "native.stderr").open("w") as stderr:
            result = subprocess.run(command, stdout=stdout, stderr=stderr)
        receipt["native_total_wall_seconds_including_checks_and_IO"] = time.monotonic() - started
        receipt["native_exit_code"] = result.returncode
        if result.returncode:
            raise RuntimeError(f"native verifier failed; retained stderr: {output / 'native.stderr'}")
        observations = [json.loads(line) for line in (output / "native.jsonl").read_text().splitlines()]
        if len(observations) != len(expected):
            raise ValueError("native output count mismatch")
        for observation, (row, prefix) in zip(observations, expected):
            raw_path = Path(str(prefix) + ".rgb565")
            raw = raw_path.read_bytes()
            if len(raw) != 720 * 480 * 2 or hashlib.sha256(raw).hexdigest() != observation["rgb565_sha256"]:
                raise ValueError("native RGB565 dump differs from published output")
            zipped = Path(str(raw_path) + ".gz")
            with zipped.open("xb") as out:
                out.write(gzip.compress(raw, mtime=0))
            if gzip.decompress(zipped.read_bytes()) != raw:
                raise ValueError("gzip roundtrip mismatch")
            observation["display_rgb565_path"] = str(zipped)
            observation["display_rgb565_compression"] = "gzip; mtime=0; row-major u16le 720x480"
            observation["display_rgb565_file_sha256"] = sha(zipped)
            raw_path.unlink()  # Only this invocation's verified redundant raw dump.
        with (output / "observations.jsonl").open("w") as out:
            for observation in observations:
                out.write(json.dumps(observation, sort_keys=True) + "\n")
        timings = [r["receive_to_published_rgb565_ms"] for r in observations]
        ordered = sorted(timings)
        summary = {"pass": True, "frames": len(observations), "clips": len({r["clip_id"] for r in observations}),
                   "rejections": sum(r["rejections"] for r in observations),
                   "receive_to_published_rgb565_ms": {"min": min(timings), "mean": statistics.mean(timings),
                         "median": statistics.median(timings), "p95_nearest_rank": ordered[max(0, (95 * len(ordered) + 99)//100 - 1)],
                         "max": max(timings)}, "timing_is_fpga": False}
        write_json(output / "summary.json", summary)
        receipt["status"] = "passed"
        receipt["observations_sha256"] = sha(output / "observations.jsonl")
        receipt["summary_sha256"] = sha(output / "summary.json")
        print(json.dumps(summary, sort_keys=True))
        return 0
    except Exception as exc:
        receipt["status"] = "failed"
        receipt["error"] = str(exc)
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        receipt["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        write_json(output / "receipt.json", receipt)


if __name__ == "__main__":
    raise SystemExit(main())
