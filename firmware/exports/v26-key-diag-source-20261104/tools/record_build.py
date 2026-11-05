"""Bind the built application and validation logs to this source inventory."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--target", type=Path, required=True)
args = parser.parse_args()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(role, path):
    assert path.is_file() and path.stat().st_size, path
    return {"role": role, "path": str(path.relative_to(root)),
            "bytes": path.stat().st_size, "sha256": digest(path)}


headers = list((args.target / "xtensa-esp32s3-espidf/release/build").glob(
    "esp-idf-sys-*/out/build/config/sdkconfig.h"))
selected = os.environ.get("MOONBUB_SDKCONFIG")
if selected:
    selected = Path(selected).resolve()
    headers = [p for p in headers if p.resolve() == selected]
assert len(headers) == 1, "Select the compiled ESP-IDF configuration unambiguously (MOONBUB_SDKCONFIG)"
saved = root / "evidence/compiled-sdkconfig.h"
shutil.copyfile(headers[0], saved)
sdkconfig = saved.read_text()
snapshot = json.loads((root / "source-snapshot.json").read_text())
source_files = {str(p.relative_to(root)): digest(p)
                for p in (root / "handheld").rglob("*") if p.is_file()}
def read_log(path):
    data = path.read_bytes()
    return data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")


logs = {name: read_log(root / "evidence" / name)
        for name in ("build-rev4-repro.log", "uf2-validation.log", "protocol-tests.log", "telemetry-tests.log", "udp-queue-tests.log", "overlap-tests.log")}
assert "Finished `release`" in logs["build-rev4-repro.log"]
assert "blocks parsed by production DFU parser" in logs["uf2-validation.log"]
protocol_result = re.search(r"test result: ok\. (\d+) passed; 0 failed;", logs["protocol-tests.log"])
assert protocol_result and int(protocol_result.group(1)) >= 9, "Protocol tests did not pass"
protocol_tests = int(protocol_result.group(1))
for name, minimum in (("telemetry-tests.log", 2), ("udp-queue-tests.log", 4), ("overlap-tests.log", 4)):
    result = re.search(r"test result: ok\. (\d+) passed; 0 failed;", logs[name])
    assert result and int(result.group(1)) >= minimum, f"{name} did not pass"
rustup = Path.home() / ".cargo/bin/rustup.exe"
manifest = {
    "overall": "INCOMPLETE",
    "reason": "Build and offline verification passed; no GameBub hardware execution.",
    "board": "GameBub Rev4 / ESP32-S3",
    "source_snapshot_revision": snapshot["revision"],
    "source_inventory": source_files,
    "build": {"command": "firmware/build.ps1 -TargetDirectory C:\\mbt -Package",
              "features": ["rev4"], "profile": "release", "cargo_locked": True,
              "application_optimization": "2" if '[profile.release.package.handheld]' in (root / 'handheld/Cargo.toml').read_text() else "s",
              "sdkconfig_source": str(headers[0]),
              "rustc": subprocess.check_output([str(rustup), "run", "esp193", "rustc", "-Vv"], text=True),
              "esp_idf": "5.4.3", "target": "xtensa-esp32s3-espidf"},
    "memory": {
        "esp32_external_psram_enabled": bool(re.search(r"^#define CONFIG_SPIRAM 1$", sdkconfig, re.M)),
        "physical_psram_population": "NOT_INSPECTED",
        "wifi_enabled": "#define CONFIG_ESP_WIFI_ENABLED 1" in sdkconfig,
        "dma_buffer_bytes": 1065,
        "whole_decoded_frame_allocated": False,
        "fpga_sdram_is_esp_psram": False,
    },
    "artifacts": [artifact(role, root / "release" / filename) for role, filename in (
        ("firmware_elf", "moonshine-rev4.elf"), ("firmware_binary", "moonshine-rev4.bin"),
        ("application_uf2", "moonshine-rev4.uf2"))]
        + [artifact("compiled_configuration", saved)]
        + [artifact("verification_log", root / "evidence" / name) for name in logs],
    "checks": {
        "rev4_firmware_build": "PASS",
        "production_msv1_protocol_tests": {"status": "PASS", "tests": protocol_tests},
        "frame_telemetry_and_udp_queue_host_tests": "PASS",
        "overlap_mode_and_abort_policy_host_tests": "PASS",
        "production_dfu_parser_identity_bounds_roundtrip": "PASS",
        "firmware_runtime_hardware": "NOT_RUN",
        "wifi_qspi_concurrent_throughput": "NOT_RUN",
        "streaming_gui_physical_controls": "NOT_RUN",
        "sustained_streaming_rate": "NOT_MEASURED",
    },
    "review": {
        "method": "source inspection; not hardware evidence",
        "queued_connect_cancelled_by_generation": True,
        "async_stop_ack_before_boot_core_restore": True,
        "connect_disabled_until_ui_enters_restored_menu": True,
        "fifo_commit_abort_guard_identity_under_device_mutex": True,
        "stock_argb1555_overlay_writes_preserved": True,
        "view_game_uses_transparent_renderer_background": True,
    },
}
(root / "evidence/build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("Firmware source/artifact evidence bound: firmware/evidence/build-manifest.json")
