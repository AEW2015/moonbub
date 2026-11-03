"""Assemble honest task-specific handoff gates and content hashes.

Evidence presence is not independent functional acceptance. Report contents are
reviewed separately; physical gates cannot be promoted by this script.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    file = ROOT / rel
    if not file.is_file():
        return ""
    data = file.read_bytes()
    encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
    return data.decode(encoding, errors="replace")


def marked(rel, marker):
    return {"status": "pass" if marker in read(rel) else "incomplete", "evidence": rel}


def main():
    checks = {
        "firmware_build": marked("firmware/evidence/build-rev4-repro.log", "Finished `release` profile"),
        "firmware_uf2": marked("firmware/evidence/uf2-validation.log", "parsed by production DFU parser"),
        "firmware_protocol": marked("firmware/evidence/protocol-tests.log", "9 passed; 0 failed"),
        "host_tests": marked("host/evidence/host-tests.log", "OK"),
        "qspi_cdc": marked("fpga/evidence/qspi-simulation.log", "QSPI_CDC_PASS"),
        "transport_overflow": marked("fpga/evidence/transport-overflow.log", "TRANSPORT_OVERFLOW_PASS"),
        "native_lcd": marked("fpga/evidence/lcd-simulation.log", "LCD_PASS"),
        "stock_overlay": marked("fpga/evidence/overlay-simulation.log", "ESP32_OVERLAY_PASS"),
        "jpeg_rtl": marked("fpga/sim/core.log", "CORE_PASS"),
        "sdram_controller": marked("fpga/evidence/sdram-simulation.log", "SDRAM_PASS"),
        "sdram_arbitration": marked("fpga/evidence/memory-simulation.log", "MEMORY_PASS"),
        "jpeg_sdram_integration": marked("fpga/evidence/pipeline-simulation.log", "PIPELINE_PASS"),
        "jpeg_sdram_backpressure": marked("fpga/evidence/pipeline64-simulation.log", "PIPELINE64_PASS"),
    }
    for name, rel, key, expected in [
        ("cross_language_protocol", "evidence/integration/result.json", "status", "pass"),
        ("jpeg_software_reference", "host/evidence/decoder-comparison.json", "fixed_color_bitexact_pass", True),
        ("streaming_gui_desktop", "firmware/evidence/ui-streaming-preview/result.json", "overall", "PASS"),
    ]:
        data = json.loads(read(rel) or "{}")
        checks[name] = {"status": "pass" if data.get(key) == expected else "incomplete", "evidence": rel}

    candidates = [ROOT / "fpga/evidence/vivado-final.log", ROOT / "fpga/evidence/vivado-final-resume.log",
                  ROOT / "fpga/evidence/vivado-close-timing.log"]
    candidates += list((ROOT / "fpga/evidence").glob("vivado-v*.log"))
    existing_logs = [file for file in candidates if file.is_file()]
    final_log_path = max(existing_logs, key=lambda file: file.stat().st_mtime).relative_to(ROOT).as_posix() if existing_logs else "fpga/evidence/vivado-final.log"
    final_log = read(final_log_path)
    gate = read("fpga/build-final/gate.txt")
    timing = {}
    for key, value in re.findall(r"(setup_wns|hold_whs|drc_errors)=([-+.\d]+)", gate):
        timing[key] = float(value)
    execution_gate = re.search(r"MOONSHINE_ROUTED_SETUP=([-+.\d]+) HOLD=([-+.\d]+) DRC_ERRORS=(\d+)", final_log)
    latest_gate = bool(execution_gate) and len(timing) == 3 and (
        float(execution_gate[1]), float(execution_gate[2]), float(execution_gate[3])) == (
        timing.get("setup_wns"), timing.get("hold_whs"), timing.get("drc_errors"))
    routed = latest_gate and timing["setup_wns"] > 0 and timing["hold_whs"] > 0 and timing["drc_errors"] == 0
    checks["routed_timing_drc"] = {"status": "pass" if routed else "incomplete", "evidence": "fpga/build-final/gate.txt", "values": timing}
    checks["programming_image"] = marked(final_log_path, "MOONSHINE_BITSTREAM_READY=1")
    if not (ROOT / "fpga/build-final/moonshine-rev4.1.bit").is_file():
        checks["programming_image"]["status"] = "incomplete"
    route_report = read("fpga/build-final/route_status.rpt")
    route_counts = {}
    for key, title in [("routable", "routable nets"), ("fully_routed", "fully routed nets"), ("errors", "nets with routing errors")]:
        match = re.search(r"# of " + title + r"\.+\s*:\s*(\d+)", route_report)
        if match:
            route_counts[key] = int(match[1])
    route_ok = latest_gate and len(route_counts) == 3 and route_counts["errors"] == 0 and route_counts["routable"] == route_counts["fully_routed"]
    checks["routing_completion"] = {"status": "pass" if route_ok else "incomplete", "evidence": "fpga/build-final/route_status.rpt", "values": route_counts}
    timing_row = re.search(r"^\s*WNS\(ns\)[^\n]*\n[^\n]*\n([^\n]+)", read("fpga/build-final/timing_summary.rpt"), re.M)
    pulse_values = timing_row[1].split() if timing_row else []
    pulse_ok = latest_gate and len(pulse_values) == 12 and float(pulse_values[8]) > 0 and all(int(pulse_values[n]) == 0 for n in (2, 6, 10))
    checks["timing_endpoint_pulse_checks"] = {"status": "pass" if pulse_ok else "incomplete", "evidence": "fpga/build-final/timing_summary.rpt", "summary_columns": pulse_values}
    io_match = re.search(r"MOONSHINE_FINAL_SDRAM_INPUT_SETUP=([-+.\d]+) HOLD=([-+.\d]+)", read("fpga/evidence/audit-final-io.log"))
    io_ok = latest_gate and bool(io_match) and float(io_match[1]) > 0 and float(io_match[2]) > 0
    checks["final_sdram_io_audit"] = {"status": "pass" if io_ok else "incomplete", "evidence": "fpga/evidence/audit-final-io.log", "scope": "Delivered routed checkpoint, unchanged provisional external budgets"}
    checks["source_preservation"] = {
        "status": "pass" if read("evidence/source-before.json") == read("evidence/source-after.json") and read("evidence/source-before.json") else "incomplete",
        "evidence": "evidence/source-after.json",
        "scope": "Original firmware tracked contents, revision and dirty status; the firmware snapshot also records copied untracked files. Unrelated workspace inventory is omitted from this publication.",
    }
    for name, scope in {
        "external_pin_qualification": "SDRAM and MCU pin budgets are provisional; digital simulation and internal STA do not qualify board margins.",
        "physical_pattern_jpeg": "No FPGA programming or observed LCD output in this task.",
        "wifi_qspi_concurrency": "No sustained ESP32 Wi-Fi to actual FPGA sink measurements.",
        "sustained_gameplay": "No physical 720x480/30 gameplay, frame-age or input-latency qualification.",
        "sunshine_extension": "Standalone MSV1 sender only; negotiate JPEG in a future matching Sunshine extension after physical path works.",
    }.items():
        checks[name] = {"status": "incomplete", "reason": scope}

    files = {}
    def artifact(role, rel):
        path = ROOT / rel
        if path.is_file() and path.stat().st_size:
            files[rel] = {"role": role, "path": rel, "bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    for pattern, role in [
        ("firmware/release/*", "firmware_image"),
        ("fpga/build-final/*.bit", "programming_image"),
        ("fpga/build-final/*.dcp", "checkpoint"),
        ("fpga/build-final/*.rpt", "implementation_report"),
        ("fpga/build-final/*.json", "source_binding"),
        ("fpga/rtl/*.sv", "rtl"),
        ("fpga/sim/*.sv", "simulation_source"),
        ("fpga/vendor/core_jpeg/src_v/*.v", "decoder_rtl"),
        ("fpga/scripts/*.tcl", "rebuild"),
        ("fpga/scripts/*.ps1", "rebuild"),
        ("fpga/scripts/*.xdc", "constraints"),
        ("fpga/evidence/*pins_rev4.xdc", "constraints"),
        ("scripts/*.py", "verification"),
        ("scripts/*.ps1", "verification"),
    ]:
        for file in sorted(ROOT.glob(pattern)):
            artifact(role, file.relative_to(ROOT).as_posix())
    for check in checks.values():
        if "evidence" in check:
            artifact("check_evidence", check["evidence"])
    for rel in ["firmware/source-snapshot.json", "firmware/evidence/build-manifest.json",
                "evidence/source-snapshot-preservation.json",
                "host/evidence/source-manifest.json", "host/evidence/c-model-build-manifest.json",
                "host/evidence/loopback.json", "host/evidence/loopback-motion.json",
                "firmware/evidence/ui-streaming-preview/streaming-view-focus.png",
                "firmware/evidence/ui-streaming-preview/README.md",
                "docs/timing-review.md", "docs/verification-inventory.md",
                "README.md", "firmware/README.md", "firmware/build.ps1", "fpga/README.md",
                "fpga/SDRAM_READ_TIMING.md", "docs/integration.md", "fpga/PROTOCOL.md", "host/PROTOCOL.md"]:
        artifact("provenance_or_documentation", rel)

    # Independently check source bindings against the files now being handed off.
    mismatches = []
    binding_file = ROOT / "fpga/build-final/source-bindings.json"
    if binding_file.is_file():
        for binding in json.loads(read("fpga/build-final/source-bindings.json")):
            file = ROOT / binding["path"]
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != binding["sha256"]:
                mismatches.append(binding["path"])
            if binding["path"].endswith(".dcp"):
                artifact("implementation_seed", binding["path"])
    checks["fpga_source_binding"] = {"status": "fail" if mismatches else "pass" if binding_file.is_file() else "incomplete",
                                      "evidence": "fpga/build-final/source-bindings.json", "mismatches": mismatches}
    firmware_manifest = json.loads(read("firmware/evidence/build-manifest.json") or "{}")
    firmware_mismatches = []
    for rel, expected in firmware_manifest.get("source_inventory", {}).items():
        file = ROOT / "firmware" / rel
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            firmware_mismatches.append(rel)
    for artifact_entry in firmware_manifest.get("artifacts", []):
        file = ROOT / "firmware" / artifact_entry["path"]
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != artifact_entry["sha256"]:
            firmware_mismatches.append(artifact_entry["path"])
    checks["firmware_source_binding"] = {
        "status": "fail" if firmware_mismatches else "pass" if firmware_manifest else "incomplete",
        "evidence": "firmware/evidence/build-manifest.json", "mismatches": firmware_mismatches,
        "source_files": len(firmware_manifest.get("source_inventory", {})),
    }
    result = {
        "overall": "INCOMPLETE",
        "offline_prototype": "PASS" if all(checks[name]["status"] == "pass" for name in (
            "firmware_build", "firmware_uf2", "firmware_source_binding", "host_tests",
            "cross_language_protocol", "jpeg_rtl", "jpeg_software_reference", "qspi_cdc",
            "transport_overflow", "native_lcd", "stock_overlay", "streaming_gui_desktop",
            "sdram_controller", "sdram_arbitration", "jpeg_sdram_integration", "jpeg_sdram_backpressure",
            "routed_timing_drc", "routing_completion", "timing_endpoint_pulse_checks", "final_sdram_io_audit",
            "programming_image", "fpga_source_binding", "source_preservation")) else "INCOMPLETE",
        "scope": "Offline prototype implementation/build/simulation; physical streaming qualification and Sunshine extension pending.",
        "hardware_programmed": False,
        "gamebub_sustained_fps": None,
        "gamebub_latency_ms": None,
        "checks": checks,
        "artifacts": list(files.values()),
        "limitations": ["Native dock output not supplied by standalone prototype.",
                        "SDRAM writes are single-word with BL8 scanout reads; no sustained 30fps claim.",
                        "PC localhost performance is not Game Bub performance."],
    }
    destination = ROOT / "evidence/manifest.json"
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print("HANDOFF", result["overall"], "artifacts", len(files), "gates", len(checks))


if __name__ == "__main__":
    main()
