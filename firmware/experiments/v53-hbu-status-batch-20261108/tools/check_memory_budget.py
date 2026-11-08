"""Check the built Rev4 streaming configuration and static shared SRAM.

This is a build guardrail, not a proof of runtime heap or stack margin.
"""
import argparse
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdkconfig", required=True, type=Path)
    parser.add_argument("--elf", required=True, type=Path)
    parser.add_argument("--size-tool", required=True, type=Path)
    args = parser.parse_args()
    config = args.sdkconfig.read_text(encoding="utf-8")
    definitions = dict(re.findall(r"^#define\s+(CONFIG_\w+)\s+(\S+)", config, re.MULTILINE))
    required = {
        "CONFIG_ESP32S3_INSTRUCTION_CACHE_16KB": "1",
        "CONFIG_ESP32S3_DATA_CACHE_16KB": "1",
        "CONFIG_ESP32S3_DATA_CACHE_SIZE": "0x8000",
        "CONFIG_ESP_WIFI_STATIC_RX_BUFFER_NUM": "4",
        "CONFIG_ESP_WIFI_DYNAMIC_RX_BUFFER_NUM": "8",
        "CONFIG_ESP_WIFI_DYNAMIC_TX_BUFFER_NUM": "4",
        "CONFIG_TINYUSB_MSC_BUFSIZE": "512",
    }
    disabled = ("CONFIG_ESP_WIFI_AMPDU_TX_ENABLED", "CONFIG_ESP_WIFI_AMPDU_RX_ENABLED",
                "CONFIG_ESP_WIFI_SOFTAP_SUPPORT", "CONFIG_ESP_WIFI_IRAM_OPT",
                "CONFIG_ESP_WIFI_RX_IRAM_OPT")
    for key, value in required.items():
        if definitions.get(key) != value:
            raise SystemExit(f"Incorrect built configuration: {key}={definitions.get(key)!r}, expected {value}")
    for key in disabled:
        if definitions.get(key) not in (None, "0"):
            raise SystemExit(f"Expected disabled: {key}={definitions[key]}")
    result = subprocess.run([str(args.size_tool), "-A", str(args.elf)],
                            check=True, capture_output=True, text=True)
    sections = dict((name, int(size)) for name, size in
                    re.findall(r"^(\.\S+)\s+(\d+)\s+\d+\s*$", result.stdout, re.MULTILINE))
    needed = (".dram0.dummy", ".dram0.data", ".dram0.bss")
    if any(name not in sections for name in needed):
        raise SystemExit("Missing shared SRAM sections in ELF size report")
    # .dram0.dummy is the shared DRAM reservation for IRAM; do not add IRAM twice.
    total = sum(sections[name] for name in needed)
    print(f"STATIC_SHARED_SRAM_BYTES={total}; guardrail={160 * 1024}")
    print("DATA_CACHE_OPTION=16KiB; IDF configures 32KiB with 16KiB returned to heap")
    if total > 160 * 1024:
        raise SystemExit("Static SRAM guardrail exceeded")
    print("MEMORY_BUILD_GUARDRAIL_PASS; runtime heap/stack require device measurements")


if __name__ == "__main__":
    main()
