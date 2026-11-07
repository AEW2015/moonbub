#!/usr/bin/env python3
"""Emit a deterministic, source-backed CU66 V100 inventory (stdlib only).

Run from any directory. The output is written beside this script's experiment
JSON. Hashes cover present source RTL, includes, initialization files and XDCs;
no vendor tools or board access are used.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/python-gamebub-v100/inventory.json"
SOURCE_ROOTS = [
    ROOT / "fpga/rtl",
    ROOT / "fpga/scripts",
    ROOT / "fpga/experiments/cu66-v91i",
    ROOT / "fpga/experiments/cu66-v91i2",
    ROOT / "fpga/experiments/cu66-v91i2b",
    ROOT / "fpga/experiments/cu66-v91j",
    ROOT / "fpga/experiments/cu66-v91k",
    ROOT / "fpga/experiments/cu66-v91l",
    ROOT / "fpga/experiments/cu66-v91",
    ROOT / "fpga/experiments/cu66-v91b",
    ROOT / "fpga/experiments/cu66-v91d",
    ROOT / "fpga/experiments/cu66-v91g2",
    ROOT / "fpga/experiments/cu66-v91h",
    ROOT / "fpga/experiments/cu66-v69/inverse",
    ROOT / "fpga/experiments/cu66-v69/banks",
    ROOT / "fpga/experiments/cu66-v69/hash",
]
EXTENSIONS = {".sv", ".v", ".vh", ".svh", ".mem", ".hex", ".coe", ".xdc"}
EXCLUDED_PARTS = {"attempts", "lint-attempts", "smoke-attempts", "pipeline-attempts", "admission-attempts"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files() -> list[Path]:
    result = set()
    for base in SOURCE_ROOTS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXTENSIONS and not (EXCLUDED_PARTS & set(path.parts)):
                result.add(path)
    return sorted(result, key=lambda p: p.relative_to(ROOT).as_posix())


def modules(files: list[Path]) -> list[dict]:
    found = []
    for path in files:
        source = path.read_text(errors="replace")
        for match in re.finditer(r"(?m)^\s*module\s+(?:automatic\s+)?([A-Za-z_]\w*)\b", source):
            found.append({"name": match.group(1), "source": path.relative_to(ROOT).as_posix()})
    return sorted(found, key=lambda m: (m["name"], m["source"]))


def module_ports(path: Path, name: str) -> list[dict]:
    """Read ANSI module-header port declarations without evaluating SV."""
    source = path.read_text(errors="replace")
    match = re.search(r"\bmodule\s+(?:automatic\s+)?" + re.escape(name) + r"\b(.*?)\);", source, re.S)
    if not match:
        return []
    header = re.sub(r"/\*.*?\*/|//[^\n]*", "", match.group(1), flags=re.S)
    header = re.sub(r"#\s*\([^)]*\)", "", header, flags=re.S)
    header = header.strip().lstrip("(").rstrip()
    ports = []
    inherited = None
    for item in header.split(","):
        item = " ".join(item.strip().split())
        if not item:
            continue
        decl = re.match(r"(input|output|inout)\s+(?:(wire|logic|reg|tri)\s*)?(signed\s+)?(\[[^]]+\]\s*)?(.*)", item)
        if decl:
            direction, kind, signed, packed, names = decl.groups()
            is_signed = bool(signed)
            inherited = (direction, kind or "implicit", bool(signed), packed.strip() if packed else None)
        elif inherited:
            direction, kind, is_signed, packed = inherited
            names = item
        else:
            continue
        for raw_name in names.split(","):
            port_name = raw_name.strip().rstrip(")")
            if not port_name:
                continue
            unpacked = re.search(r"(\[[^]]+\])+$", port_name)
            identifier = re.match(r"([A-Za-z_]\w*)", port_name)
            if not identifier:
                continue
            width = None
            width_expr = None
            if packed:
                dim = re.fullmatch(r"\[\s*(-?\d+)\s*:\s*(-?\d+)\s*\]", packed.strip())
                if dim:
                    width = abs(int(dim.group(1)) - int(dim.group(2))) + 1
                else:
                    width_expr = packed
            ports.append({"name": identifier.group(1), "direction": direction, "kind": kind, "signed": is_signed, "packed_range": packed, "packed_width_bits": width, "packed_width_expression": width_expr, "unpacked_range": unpacked.group(0) if unpacked else None})
    return ports


files = source_files()
known_modules = modules(files)
module_names = {m["name"] for m in known_modules}

# These ledgers count only statically explicit source-level storage. They are
# logical declarations, not inferred BRAM/URAM/register usage or a fit claim.
storage = [
    {"module": "cs88_admission_v91i2a", "source": "fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv", "objects": [
        {"name": "memory", "width_bits": 8, "depth": 49152, "logical_bits": 393216, "basis": "MAX_BYTES=49152; byte packet buffer"},
        {"name": "header", "width_bits": 8, "depth": 128, "logical_bits": 1024, "basis": "explicit declaration"},
        {"name": "qbuffer", "width_bits": 8, "depth": 354, "logical_bits": 2832, "basis": "qbuffer[0:353]"},
        {"name": "modes", "width_bits": 2, "depth": 8100, "logical_bits": 16200, "basis": "modes[0:8099]"},
        {"name": "scales", "width_bits": 2, "depth": 1350, "logical_bits": 2700, "basis": "scales[0:1349]"},
    ]},
    {"module": "cs88_pipeline_v91i2a", "source": "fpga/experiments/cu66-v91i2/cs88_pipeline_v91i2a.sv", "objects": [
        {"name": "fork_blocks/fork_offsets/fork_lengths", "width_bits": 32, "depth_each": 3, "logical_bits_total": 288, "basis": "three arrays [0:2]"},
        {"name": "fork_entropy", "width_bits": 2, "depth": 3, "logical_bits": 6, "basis": "explicit declaration"},
        {"name": "dbg_bank_block", "width_bits": 16, "depth": 2, "logical_bits": 32, "basis": "port array"},
        {"name": "dbg_bank_epoch", "width_bits": 32, "depth": 2, "logical_bits": 64, "basis": "port array"},
        {"name": "count_emitter_state", "width_bits": 64, "depth": 4, "logical_bits": 256, "basis": "port array"},
        {"name": "count_packet_state", "width_bits": 64, "depth": 16, "logical_bits": 1024, "basis": "port array"},
        {"name": "count_scratch_state", "width_bits": 64, "depth": 32, "logical_bits": 2048, "basis": "port array"},
        {"name": "ts_first_coef_band/ts_last_coef_band/ts_band_end", "width_bits": 64, "depth_each": 4, "logical_bits_total": 768, "basis": "three port arrays"},
    ]},
    {"module": "br88_packet_ingress_sync_v91h", "source": "fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv", "status": "source is archived in the selected V91i2b/V91j pipeline attempt snapshots; no standalone live file at this path", "objects": [
        {"name": "memory", "width_bits": 8, "depth": 49152, "logical_bits": 393216, "basis": "MAX_PACKET_BYTES default 49152"},
        {"name": "fetch_bytes", "width_bits": 8, "depth": 46, "logical_bits": 368, "basis": "[0:45]"},
        {"name": "lengths/counts/offsets/sizes", "width_bits": 32, "depth_each": 4, "logical_bits_total": 512, "basis": "four arrays [0:3]"},
        {"name": "k0s/k1s", "width_bits": 8, "depth_each": 4, "logical_bits_total": 64, "basis": "two arrays [0:3]"},
    ]},
    {"module": "cu66_inverse_stream_v91j", "source": "fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv", "objects": [
        {"name": "coefficient/dequantized debug buses", "width_bits": 1024, "depth": 1, "logical_bits": 2304, "basis": "1024-bit coefficients and 1280-bit dequantized exposed transaction buses, not persistent memory"},
        {"name": "inverse banks", "width_bits": None, "depth": 2, "logical_bits": None, "basis": "two explicit transaction banks; exact primitive/register mapping needs synthesis"},
    ]},
    {"module": "cu66_reconstruct_stream_v91k", "source": "fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv", "objects": [
        {"name": "reference tile response", "width_bits": 512, "depth": 1, "logical_bits": 512, "basis": "port transaction carries 8x8 8-bit sample tile"},
    ]},
    {"module": "canonical_rgb565_v91k", "source": "fpga/experiments/cu66-v91k/rgb/canonical_rgb565_v91k.sv", "objects": [
        {"name": "samples", "width_bits": 8, "depth": 9, "logical_bits": 72, "basis": "explicit [0:8] neighborhood"},
    ]},
]

existing = {
    "status": "present production source; JPEG/MSV1 design only",
    "top": "moonshine_top",
    "top_source": "fpga/rtl/moonshine_top.sv",
    "device_part_source_backed": "xc7a100tcsg324-1",
    "device_part_basis": "existing source-backed JPEG target records; not evidence of physical board identity or CS88 fit",
    "clock_domains_source_declared": [
        {"name": "clk50", "source": "clk_50mhz", "frequency_mhz": 50},
        {"name": "clk200", "source": "PLLE2_BASE CLKOUT0", "frequency_mhz": 200, "purpose": "QSPI endpoint / SPI domain"},
        {"name": "clk100", "source": "PLLE2_BASE CLKOUT1", "frequency_mhz": 100, "purpose": "core and memory domain"},
        {"name": "read_clk100", "source": "PLLE2_BASE CLKOUT2", "frequency_mhz": 100, "phase_degrees": 279, "purpose": "SDRAM read domain"},
        {"name": "pclk", "source": "MMCME2_BASE CLKOUT0", "frequency_mhz": "derived from 50 MHz * 56.375 / 3 / 32 = 29.361979", "purpose": "LCD pixel clock"},
    ],
    "xdc": [],
    "custom_cs88_top": {"present": False, "module": None, "source": None, "status": "no complete selected CS88 custom top found; component experiments are not a top-level image"},
}

for p in sorted((ROOT / "fpga").rglob("*.xdc")):
    if not (EXCLUDED_PARTS & set(p.parts)):
        existing["xdc"].append({"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)})

ports = {
    "cs88_admission_v91i2a": ["clk/reset", "packet_valid/ready/byte/last", "frame metadata", "plane_blocks/offset/length/entropy[0:2]", "mode/quant-cell lookup", "admission status"],
    "cs88_pipeline_v91j": ["clock/reset/start/abort", "cache/ref identity", "BR88 packet byte stream", "dequantized coefficient stream: plane[1:0], tile[12:0], qcell[10:0], index[5:0], signed value[23:0], epoch[31:0]", "inverse transform outputs, busy/done/error, counts; validation/publication absent"],
    "cs88_pipeline_v91k": ["V91j coefficient/residual path", "reference request/response: exact frame id/generation/plane/tile plus 512-bit tile pixels", "canonical reconstructed sample stream: plane/mode/tile/index/value/epoch/fid", "reference reconstruction output; C2/HUD acceptance and publication absent"],
    "canonical_rgb565_v91k": ["canonical sample read request/response", "RGB565 output valid/ready with pixel address/data"],
}
port_modules = [
    ("moonshine_top", "fpga/rtl/moonshine_top.sv"),
    ("moonshine_core", "fpga/rtl/moonshine_core.sv"),
    ("moonshine_memory", "fpga/rtl/moonshine_memory.sv"),
    ("moonshine_sdram", "fpga/rtl/moonshine_sdram.sv"),
    ("cs88_admission_v91i2a", "fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv"),
    ("cs88_pipeline_v91j", "fpga/experiments/cu66-v91j/cs88_pipeline_v91j.sv"),
    ("cs88_pipeline_v91k", "fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv"),
    ("cs88_validate_publish_v91l", "fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv"),
    ("canonical_rgb565_v91k", "fpga/experiments/cu66-v91k/rgb/canonical_rgb565_v91k.sv"),
]
port_ledger = []
for module_name, relative in port_modules:
    source_path = ROOT / relative
    declared = module_ports(source_path, module_name) if source_path.exists() else []
    port_ledger.append({"module": module_name, "source": relative, "port_count": len(declared), "ports": declared})

result = {
    "schema": "cu66-v100-source-inventory-v1",
    "inventory_kind": "read-only source inventory; generated with Python standard library",
    "baseline": {"branch": "study/gamebub-v100-baseline-20261107", "commit": "f403a5f5149de60ebc128ac57911c4912bec0ddf"},
    "frozen_profile": {"path": "experiments/python-gamebub-v99/profile.json", "sha256": sha(ROOT / "experiments/python-gamebub-v99/profile.json"), "name": "CS88-V99-RC1-Q16-BR88", "status": "FROZEN_RESEARCH_CANDIDATE_ONLY", "parameters": {"coded_width": 720, "coded_height": 480, "wire_version": 1, "motion_block_size": 32, "base_motion": "zero only", "coefficient_codec": "BR88 only", "chunk_block_cap": 65536, "complete_packet_cap_bytes_including_outer_CRC": 49152, "key_mode_method": 0, "P_mode_method": 3, "QM87_methods": [2, 6], "default_uniform_quant_scale": 16, "default_uniform_quant_code": 1, "C2_profile_id": "CU66-V82-CONTENT-SHA256-TREE-2", "C2_tree_granularity_tiles": 16}},
    "current_status": {"v100_tools": {"vivado_mcp": "connection transport closed; CLI fallback used", "vivado_cli": {"version": "2025.2", "path": "/opt/Xilinx/2025.2/Vivado/bin/vivado", "container": "gamebub-cu66-v69-vivado", "exact_target_matches": 0, "all_7_series_part_matches": 0, "other_installed_parts": 504, "evidence_log": "experiments/python-gamebub-v100/preflight/vivado-query.log"}, "vivado_2026_1_secondary": {"status": "allocator/libudev startup crash before part query", "logs": ["experiments/python-gamebub-v100/preflight/vivado-2026-query.log", "experiments/python-gamebub-v100/preflight/vivado-2026-no-preload-query.log"], "part_count": None}, "yosys": {"version": "0.33", "availability": "native build container", "xilinx_family_mapping": "synth_xilinx family mapping available", "exact_device_place_route_or_fmax": "not available"}, "fresh_v91j_component_rtl": {"status": "PASS", "seeds": [100401, 100402], "cases_per_seed": 6, "directed_checks_per_seed": 13, "scope": "signed dequantization and IDCT component; no complete CS88 publication"}, "paired_converted_v91k_component_rtl": {"status": "PAIRED_RTL_PASS", "seeds": [911501, 911502], "public_ports": 308, "array_wrappers": 9, "scope": "bounded behavioral component comparison; no formal or physical qualification"}}, "synthesis": "exact-target Vivado synthesis not started; generic Yosys leaf mapping exists and full converted component mapping is incomplete", "place_route": "no exact-target route; xc7a100tcsg324-1 absent from installed Vivado part database", "physical_board_identity": "not established", "resource_utilization": None, "routed_frequency": None},
    "existing_image": existing,
    "source_files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files],
    "module_definitions": known_modules,
    "explicit_sv_parameters": [
        {"module": "cs88_pipeline_v91i2b", "source": "fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv", "parameters": {"REFILL_OVERLAP": 1}},
        {"module": "br88_packet_ingress_sync_v91h", "source": "fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv", "parameters": {"MAX_PACKET_BYTES": 49152}},
        {"module": "br88_packet_ingress_v91h", "source": "fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv", "parameters": {"MAX_PACKET_BYTES": 49152, "SYNC_STAGING": 1}},
        {"module": "moonshine_top", "source": "fpga/rtl/moonshine_top.sv", "parameters": {}},
    ],
    "candidate_components": [
        {"module": "cs88_admission_v91i2a", "source": "fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv", "role": "bounded CS88 admission, CRC/metadata/QM87 mode and scale maps", "present": True},
        {"module": "cs88_pipeline_v91j", "source": "fpga/experiments/cu66-v91j/cs88_pipeline_v91j.sv", "role": "V91i2b BR88 ingress/replay + V91j dequantization/IDCT", "present": True},
        {"module": "cs88_pipeline_v91k", "source": "fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv", "role": "V91k adds reference reconstruction and canonical sample stream", "present": True},
        {"module": "canonical_rgb565_v91k", "source": "fpga/experiments/cu66-v91k/rgb/canonical_rgb565_v91k.sv", "role": "base RGB565 conversion candidate", "present": True},
        {"module": "cs88_validate_publish_v91l", "source": "fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv", "role": "V91l validation/publication component only; no selected complete top-level join", "present": (ROOT / "fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv").exists()},
    ],
    "interfaces": {"port_ledger": port_ledger, "typed_outputs": [
        {"name": "coefficient stream", "type": "signed residual coefficients plus plane/tile/qcell/index/epoch", "source": "cs88_pipeline_v91j"},
        {"name": "reconstructed canonical stream", "type": "unsigned reconstructed sample with plane/mode/tile/index/fid/epoch", "source": "cs88_pipeline_v91k"},
        {"name": "validation acceptance", "type": "V91l isolated validation/publication signals; not connected to actual complete CS88 front end", "source": "cs88_validate_publish_v91l", "status": "component only; no all-RTL acceptance"},
        {"name": "front display", "type": "existing moonshine_core pixel_valid/ready/address/RGB565 to moonshine_memory then moonshine_lcd", "source": "fpga/rtl/moonshine_top.sv", "status": "existing JPEG/MSV1 path; custom CS88 stream not joined"},
    ], "component_ports": ports},
    "logical_storage_ledger": storage,
    "physical_resource_claim": {"status": "unavailable until V100 synthesis and implementation", "logical_vs_physical": "declared logical bits are source-level counts only; arrays may map to registers, distributed RAM or block RAM; unconnected/debug observability and synthesis optimization can alter mapping", "whole_device_budget": "not established for candidate"},
    "integration_gaps": ["CS88 capability negotiation, transport epoch/core generation binding and packet ownership are absent from active firmware/QSPI path", "Actual C2 content root construction and checking do not join the selected CS88 reconstruction path", "Exact words-only CS88 HUD pixels are not composed/hashed in a joined RTL path; CU66 geometry/rectangle/words hash is a distinct preimage", "Accepted reference/candidate/canonical/display buffer ownership and write acknowledgements do not form one atomic transaction", "Vblank plus scanout drain gate is not joined to validated CS88 publication", "Full software golden replay and exact source RGB565 HUD semantics remain authoritative in current C++/host path; RTL-facing vectors are not proof of complete RTL decode", "No production-source custom CS88 top, selected build target, selected XDC, or finite whole-device RAM/DSP/LUT map is present", "External memory/controller ownership, candidate/reference/display sharing, refresh and turnaround arbitration require a finite integrated port map", "No board-level V100 route/timing or sustained 30 fps/under-10-ms evidence in this inventory"],
    "recommended_build_target": {"name": "cs88_pipeline_v91k", "top_source": "fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv", "supporting_sources": [x["path"] for x in [{"path": m["source"]} for m in known_modules if m["source"].startswith("fpga/experiments/cu66-v91")]], "status": "component elaboration target recommendation only; add actual dependency closure and wrapper before candidate full-design build", "reason": "the highest existing stream endpoint in the reviewed V91i2/j/k chain includes coefficient decode, inverse transform and reference reconstruction; a wrapper is still needed for C2/HUD/atomic acceptance/display"},
    "limitations": ["Module inventory is syntactic/source-backed; it does not assert all modules elaborate together", "Attempt snapshots and tool-attempt directories are excluded from the current source hash set; the source files in the selected source directories are hashed", "Vivado CLI exists but does not contain the exact Artix-7 target or any 7-series parts; Yosys family mapping is not exact-part place/route or Fmax evidence", "Part is source-backed from the existing JPEG target; physical board identity and candidate fit are unqualified"],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(OUT.relative_to(ROOT))
print(f"hashed_source_files={len(files)} modules={len(known_modules)}")
