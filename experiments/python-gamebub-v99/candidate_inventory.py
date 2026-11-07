#!/usr/bin/env python3
"""Regenerate the V99 candidate and interface inventory using only stdlib."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).with_name("inventory.json")

# These are the executable source boundaries reviewed for this inventory.
# Include the production path, compact prototype, current FPGA top, reviewed
# V91 RTL component path, and native/CS88 software references. Hashes are
# calculated from the checkout at generation time; missing inputs are explicit.
INTERFACES = [
    ("firmware/handheld/src/streaming/mod.rs", "active ESP-IDF Wi-Fi worker and FPGA register use"),
    ("firmware/handheld/src/streaming/protocol.rs", "active MSV1 datagram parser"),
    ("firmware/handheld/src/streaming/protocol97.rs", "portable V97 compact setup/fragment/gateway prototype"),
    ("host/moonshine/protocol97.py", "V97 host wire protocol prototype"),
    ("host/moonshine/transport97_sender.py", "V97 host sender/preparation prototype"),
    ("fpga/rtl/moonshine_qspi_endpoint.sv", "existing production QSPI endpoint"),
    ("fpga/rtl/moonshine_core.sv", "existing production JPEG core wrapper"),
    ("fpga/rtl/moonshine_memory.sv", "existing shared SDRAM/scanout service"),
    ("fpga/rtl/moonshine_sdram.sv", "existing external SDRAM controller"),
    ("fpga/rtl/moonshine_top.sv", "existing Rev4.1 top and clock integration"),
    ("experiments/python-gamebub-v88/wire/receiver.cpp", "independent native CS88 receiver used by RC1 encoder evidence"),
    ("experiments/cu66-native-v69/decoder.hpp", "restricted CU66/GU66 native software reference decoder"),
    ("experiments/cu66-native-v69/bytes.hpp", "native CU66/GU66 bounded wire and CRC primitives"),
    ("experiments/python-gamebub-v99/cs88/encode_dense.cpp", "RC1 dense all-BR88 CS88 source encoder"),
    ("fpga/experiments/cu66-v91i/cs88_admission_v91i1.sv", "V91i restricted CS88 frame admission frontend"),
    ("fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv", "V91i2 provisional CS88 mode/qmap ownership"),
    ("fpga/experiments/cu66-v91i2/cs88_pipeline_v91i2a.sv", "V91i2 BR88 child dispatch and coefficient placement"),
    ("fpga/experiments/cu66-v91j/cs88_pipeline_v91j.sv", "V91j BR88 dequantization and IDCT integration"),
    ("fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv", "V91j inverse-transform arithmetic endpoint"),
    ("fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv", "V91k candidate coefficient transaction path"),
    ("fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv", "V91k reference reconstruction and canonical pixel path"),
    ("fpga/experiments/cu66-v91k/rgb/canonical_rgb565_v91k.sv", "V91k base RGB565 conversion path"),
    ("fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv", "V91l C2/HUD/root/seal validation and publication control"),
]


def file_record(relative: str, role: str) -> dict:
    path = ROOT / relative
    if not path.is_file():
        return {"path": relative, "role": role, "status": "missing", "sha256": None}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": relative, "role": role, "status": "present", "sha256": digest}


def build_inventory() -> dict:
    return {
        "schema": "gamebub-v99-rc1-candidate-inventory-v1",
        "inventory_scope": "source/document audit; not a build, hardware test, or full-path qualification",
        "candidate": {
            "name": "CS88 all-BR88 restricted profile matching the existing V91 RTL subset",
            "decision": "selected conditional RTL research candidate for RC1; not a production-supported codec",
            "condition": "native parity is qualified for the research scope; whole-path integration, held-out evidence and physical gates remain prerequisites for promotion",
            "production_fallback": "baseline 720x480 JPEG over the existing MSV1 worker and FPGA interface; separate fallback, no simultaneous-fit claim",
            "profile_bounds": {
                "coded_width": 720,
                "coded_height": 480,
                "wire_profile": "CS88",
                "wire_generation_field": "present",
                "wire_epoch_field": "absent; do not assign the upstream CU66 epoch 25 to CS88 wire",
                "residual_entropy": "BR88 only; AB38 and mixed frames reject before child start",
                "block_size": 32,
                "chunk_block_cap": 65536,
                "complete_wire_cap_bytes": 49152,
                "key_mode_method": 0,
                "delta_group_mode_method": 3,
                "QM87_methods": [2, 6],
                "QM87_method_2": "run map",
                "QM87_method_6": "inherited accepted-reference cache; requires valid exact snapshot",
                "uniform_quantization_default": 16,
                "diagnostic_quantization_profiles": [8, 32],
                "canonical_pixels_and_hud": "preserve intended 720x480 canonical pixels and exact semantic HUD",
                "validation_and_publication": "C2 SHA root, frame seal and atomic ownership publication are required product semantics; complete selected-top integration remains open",
            },
            "software_control": {
                "name": "fresh CU66/GU66 arithmetic 5/6 zero-motion profile",
                "status": "fresh RGB to current receiver parity passed; software control, not RC1 RTL candidate",
                "fresh_attempts": 360,
                "native_atomic_trials": 3948,
                "input_provenance": "shared fresh RGB arrays from frozen V98 source NPZs; no old decoded-pixel recompression",
                "fresh_audit": "experiments/python-gamebub-v99/audit-fresh.json",
                "qualification_pointer": "experiments/python-gamebub-v99/qualification.json",
            },
            "rejected_candidate_variants": [
                "native-accepted minimum-map profile with delta mode method 2 (23 P cases) and key QM87 method 1 (12 key cases): outside the documented V91 RTL profile",
                "AB38 or mixed-entropy CS88 frames: V91i2 all-BR88 candidate rejects before child decode",
            ],
        },
        "production_and_research_support": {
            "verified_current_default": {
                "format": "baseline JPEG, 720x480, sender selects 4:2:0 and standard tables",
                "transport": "MSV1 over the existing UDP worker",
                "firmware_frame_limit_bytes": 262144,
                "fpga_endpoint": "existing QSPI/register endpoint and JPEG decoder",
                "evidence": ["fpga/README.md", "firmware/handheld/src/streaming/mod.rs", "firmware/handheld/src/streaming/protocol.rs"],
            },
            "v97_compact_interface": {
                "status": "portable prototype; not the active network worker and not mapped to production FPGA QSPI registers",
                "setup_and_ack_bytes": 40,
                "fragment_header_bytes": 12,
                "frame_start_metadata_bytes": 16,
                "payload_fragment_bytes": [1024, 1400],
                "research_cap_bytes": 49152,
                "opaque_profile_ids": ["CS92", "CS94", "CS95", "CS96"],
                "negotiates_CS88": False,
                "CS88_alias_under_CS92": False,
                "does_not_install_decoder_or_publish_validated_frames": True,
                "evidence": ["docs/cu66-v97/protocol.md", "docs/cu66-v97/README.md"],
            },
            "research_profile_distinctions": {
                "CU66_GU66": "upstream fresh software-control capability; fixed epoch 25, 720x480 YUV420, arithmetic dispatches 5/6, zero motion only; not the RC1 RTL candidate",
                "CS88": "selected conditional RC1 RTL research profile constrained to documented V91i through V91l interfaces; header contains generation but no epoch field; wire is distinct from CU66 epoch 25",
                "CS92": "versioned complete research frame profile used by V92 and an opaque V97 transport ID; it is not CU66/GU66 decoder support",
            },
            "parameter_evidence_scope": "RC1 profile values are frozen from existing V91 contract/README documentation; this audit performs no new RTL run",
            "source_audit": "admission/dispatch source and tests must enforce the documented mode/QM fields; broader native acceptance is insufficient",
        },
        "target_and_memory": {
            "current_artix_tool_support": {
                "status": "unknown_not_rechecked",
                "evidence": "retained routed JPEG evidence is from Vivado 2025.2 win64; no current tool installation/support probe was performed for the candidate",
                "v100_action": "verify the exact installed tool/device support against the selected part before clean synthesis",
            },
            "verified_source_facts": [
                {
                    "property": "prototype_board_revision",
                    "value": "Game Bub native Rev4.1 prototype",
                    "evidence": "fpga/README.md",
                    "qualification": "repository documentation; current physical board identity has not been re-probed in this task",
                },
                {
                    "property": "target_part",
                    "value": "xc7a100tcsg324-1",
                    "evidence": "docs/gamebub-v91-v110-development-plan.md and fpga/build-final/utilization.rpt",
                    "qualification": "retained JPEG routed report; V100 must reconfirm exact board/part/top for a new candidate",
                },
                {
                    "property": "existing_core_clock_domains",
                    "value": {"processing": "100 MHz", "QSPI": "200 MHz", "LCD_pixel": "29.361979 MHz", "SDRAM_forwarded": "100 MHz"},
                    "evidence": "fpga/README.md and fpga/build-final/clocks.rpt",
                    "qualification": "existing JPEG prototype clocks; not a constraint/clock claim for a CU66 candidate",
                },
                {
                    "property": "existing_memory_architecture",
                    "value": {"compressed_frame_BRAM_bytes": 262144, "external_framebuffers": 2, "sdram_service": "16-bit SDR SDRAM, 100 MHz, BL8/CAS3; scanout priority at burst boundaries"},
                    "evidence": "fpga/README.md and fpga/rtl/moonshine_memory.sv",
                    "qualification": "existing JPEG design only; no CU66 memory map or service budget is qualified",
                },
                {
                    "property": "existing_routed_resource_baseline",
                    "value": {"LUT": 7362, "registers": 5994, "BRAM_tiles": 120.5, "DSP": 32},
                    "evidence": "fpga/build-final/utilization.rpt",
                    "qualification": "historical JPEG top; must not be treated as available CU66 headroom without replacement accounting and a new implementation",
                },
            ],
            "candidate_assumptions_not_yet_qualified": [
                {"property": "RC1_complete_wire_admission", "value": "at most 49152 bytes per packet; chunk block-count cap parameter 65536", "status": "documented CS88 profile values; not target memory capacity proof"},
                {"property": "V97_gateway_staging", "value": "two aligned 1400-byte stages", "status": "portable prototype; target heap and DMA behavior unmeasured"},
                {"property": "V97_standalone_ingress", "value": "2048-byte FIFO plus two held descriptor slots", "status": "standalone RTL boundary; not production QSPI adapter"},
                {"property": "CS88_candidate_decoder_workspace_and_ports", "value": None, "status": "unknown; no complete RTL primitive/port budget exists"},
                {"property": "complete_candidate_fit_and_service", "value": None, "status": "not established; must include JPEG fallback, display/control, references, HUD, validation and SDRAM contention"},
            ],
        },
        "deferred_tools": [
            {"tool": "dispatches 0-4 and nonzero motion", "status": "outside restricted v69 native capability; deferred"},
            {"tool": "CS92 profile adoption", "status": "opaque V97 transport only; no CU66 support implied; deferred"},
            {"tool": "HEVC and AV1", "status": "software rate/quality anchors only; no Game Bub decoder support"},
            {"tool": "historical GM01 and unconditional global motion", "status": "not promoted by V98 controls"},
            {"tool": "V94 ANS, V95 palette, V96 COPY/CONST128 display optimization", "status": "research results do not qualify integrated candidate tools; defer unless separately gated"},
        ],
        "open_integration_gates": [
            {"gate": "fresh_CU66_software_control", "status": "closed for current software ledger: 360 fresh attempts pass current-receiver parity; native comparison records 3948 atomic trials; CU66 remains software control, not RTL candidate"},
            {"gate": "RC1_native_all_BR88_subscope", "status": "closed for native/source-grammar research scope: 360 exact frames; independent BR88/C2 audit; selected q16 has120 complete cap-fitting frames; see qualification.json"},
            {"gate": "independent_original_capture_and_quality", "status": "open; raw held-out 30-fps gameplay, HUD readability/temporal checks and calibrated packet tails required"},
            {"gate": "V91l_complete_functional_path", "status": "open; full RTL HUD decode/overlay, shared-service/source-cadence integration and complete publication path"},
            {"gate": "V97_production_transport_adapter", "status": "open; actual capability probe, QSPI/register adapter, opt-in ESP-IDF worker, bounded mailbox/heap and hardware service calibration"},
            {"gate": "complete_recovery_and_goldens", "status": "open; broader corpus, whole-path transaction/recovery and independent decoder/RTL-facing goldens"},
            {"gate": "candidate_resource_and_port_budget", "status": "open; decoder workspace, RAM/DSP/LUT mapping, shared memory arbitration and full-top fit"},
            {"gate": "RC1_selected_profile_RTL_regression", "status": "profile parameters were audited against V91 contracts only; no new RTL run was performed by this inventory task"},
            {"gate": "V100_7_series_physical_baseline", "status": "future gate; exact board/top/XDC/tool/source freeze, clean build, synthesis/route and valid constraints"},
            {"gate": "V110_hardware_30fps", "status": "open; 1800 distinct frames/60 s then 18000/600 s at 30 Hz under real contention"},
            {"gate": "V110_validated_decode_under_10ms", "status": "open; packet-complete through validated publication, every qualified sample strictly below 10 ms"},
        ],
        "interface_files": [file_record(path, role) for path, role in INTERFACES],
        "evidence_documents": [
            "docs/gamebub-v91-v110-development-plan.md",
            "docs/cu66-v97/README.md",
            "docs/cu66-v97/protocol.md",
            "docs/cu66-v98/README.md",
            "docs/cu66-v98/results.md",
            "docs/cu66-v91i/README.md",
            "docs/cu66-v91i/admission-contract.md",
            "docs/cu66-v91i2/README.md",
            "docs/cu66-v91i2/contract.md",
            "docs/cu66-v91j/README.md",
            "docs/cu66-v91k/README.md",
            "docs/cu66-v91l/README.md",
            "experiments/cu66-native-v69/README.md",
            "fpga/README.md",
            "fpga/build-final/utilization.rpt",
            "fpga/build-final/clocks.rpt",
        ],
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(build_inventory(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
