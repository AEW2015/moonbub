#!/usr/bin/env python3
"""Bind V111's executed baseline, guest provenance and explicit API gaps."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v111/harness'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return dict(path=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),sha256=sha(p))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
    summary=AREA/'results.json';s=json.loads(summary.read_text());receipt=ROOT/s['selected_receipt'];r=json.loads(receipt.read_text())
    assert s['selected_sha256']==sha(receipt) and r['status']=='PASS_FUNCTIONAL_EMULATED_RECEIVER_JPEG_RTL'
    for name,h in r['artifact_sha256'].items():assert sha(receipt.parent/name)==h
    for name,h in r['source_sha256'].items():assert sha(ROOT/name)==h and sha(receipt.parent/'sources'/name)==h
    guest=Path('/home/lori/gamebub-tools/esp-emu-study-0510/lcd-bypass/msv1-bridge-harness')
    repo_guest=ROOT/'fpga/experiments/throughput30/burst/esp-emulator-study/live-bridge/guest-main.rs'
    repo_receiver=ROOT/'firmware/handheld/src/streaming/protocol.rs'
    assert sha(guest/'src/main.rs')==sha(repo_guest)
    assert sha(guest/'src/streaming/protocol.rs')==sha(repo_receiver)
    elf=Path('/home/lori/gamebub-tools/esp-emu-study-0510/lcd-bypass/live-final-positive/guest.elf')
    comment=subprocess.run(['readelf','-p','.comment',str(elf)],capture_output=True,text=True,check=True).stdout
    compiler=Path('/home/lori/gamebub-tools/rustup/toolchains/esp/bin/rustc')
    observed=subprocess.run([str(compiler),'--version','--verbose'],capture_output=True,text=True,check=True).stdout
    assert '1.93.0-nightly' in comment and '1.97.0-nightly' in observed
    helptext=(receipt.parent/'emulator-help.log').read_text()
    assert '--gdb' in helptext and 'single-step' in helptext
    rtl=(receipt.parent/'rtl.log').read_text()
    match=re.search(r'BRIDGE_PRESENT seq=27 id=0 bytes=26159 events=28 commit_cycle=(\d+) present_cycle=(\d+) pixels=345600 credit_reads=(\d+)',rtl)
    assert match
    trace_summary=AREA/'trace-results.json';ts=json.loads(trace_summary.read_text());trace=ROOT/ts['selected_result'];tr=json.loads(trace.read_text());assert sha(trace)==ts['sha256']
    for name,h in tr['artifact_sha256'].items():assert sha(trace.parent/name)==h
    for name,h in tr['source_sha256'].items():assert sha(ROOT/name)==h
    assert len(tr['negative_controls'])==5 and tr['byte_trace']['datagrams']==26
    original_ref=Path('/home/lori/gamebub-tools/esp-emu-study-0510/lcd-bypass/live-final-positive/cmodel.ppm')
    fresh_ref=Path(r['external_build'])/'live-run/cmodel.ppm'
    assert sha(original_ref)==sha(fresh_ref),'fresh corrected oracle differs from historical reference'
    findings=dict(schema='v111-harness-provenance-capability-audit-v1',status='PASS_FUNCTIONAL_PROVENANCE_GAPS_EXPLICIT',
        baseline_summary=pin(summary),baseline_receipt=pin(receipt),trace_summary=pin(trace_summary),trace_result=pin(trace),
        all_selected_source_and_artifact_hashes_match=True,rtl_sources=33,legacy_compile_warnings=r['legacy_compile_warning_count'],
        fresh_corrected_reference_matches_historical_bytes=dict(fresh=pin(fresh_ref),historical=pin(original_ref)),
        guest_source_copy_matches_repository=True,guest_sources=[pin(repo_guest),pin(repo_receiver)],
        guest_reused_not_recompiled=True,guest_elf=pin(elf),guest_compiler_comment=comment,
        currently_installed_Rust_compiler=pin(compiler),current_rustc_observation=observed,
        exact_guest_rebuild_reproduced=False,
        guest_toolchain_gap='ELF records Rust1.93; currently installed esp compiler is1.97. Reusing exact pinned image is explicit; no invented current-toolchain guest build.',
        current_guest_build_files=[pin(guest/n) for n in ('Cargo.toml','Cargo.lock','rust-toolchain.toml','.cargo/config.toml')],
        guest_boot_reports_IDF='v5.4.3',guest_reports_cpu_Hz=240000000,PSRAM_bytes=0,
        production_SRAM_qualified=False,guest_contains_fixture_oracle=True,
        functional_results=dict(guest_datagrams=26,payload_bytes=26159,RTL_acknowledged_events=28,committed_frames=1,exact_RGB565_pixels=345600,
             commit_cycle=int(match[1]),present_cycle=int(match[2]),credit_reads=int(match[3]),
             counter_scope='100MHz testbench RTL counters with blocking socket freezes; not common-time latency or device timing'),
        capabilities=dict(actual_receiver_guest_boot=True,actual_loopback_network=True,actual_guest_payload_to_RTL=True,
             experimental_pin_level_QSPI_RTL=True,actual_ESP32_GP_SPI_registers=False,actual_ESP32_DMA=False,
             host_capture_clock='host_monotonic_ns',shared_simulation_time=False,CPU_cycle_accuracy_calibrated=False,
             gdb_CPU_single_step_advertised=True,dedicated_time_quantum_CLI_found=r['capability_observations']['dedicated_time_step_CLI_found'],
             controlled_time_API_exercised=False,emulator_source_level_step_API_inventory_complete=False),
        next_required=['Recover pinned Rust1.93 environment or build a new explicit guest with current compiler and rerun; never rename it as historical image.',
             'Implement/test a controlled emulator/RTL time coordinator; the current GDB single-step flag is not such a proof.',
             'Connect actual guest GP-SPI/DMA/IRQ/credit behavior; current test guest emits synthetic events and SV drives QSPI.',
             'Run the actual Sunshine backend/capture path rather than labeling the Python packetizer as Sunshine.',
             'Replace embedded guest golden data before SRAM accounting and full production-app claims.',
             'Review43 legacy RTL compile warnings before elevating this functional baseline to stricter verification.'],
        sunshine_executed=False,full_production_firmware=False,system_FPS_qualified=False,validated_decode_under10ms=False,hardware_contact=False)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(findings,indent=2,sort_keys=True)+'\n');print('V111_HARNESS_INSPECTION_PASS',sha(a.out))


if __name__=='__main__':main()
