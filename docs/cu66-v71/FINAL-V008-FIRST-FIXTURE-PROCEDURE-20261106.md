# Final v008 / sealed v36 first local hardware fixture

Preparation only: no hardware is installed or exercised by this document or the runner default. Preserve currently installed B50/v32 for the separate25fps regression first. This is a fixed local KEY/P diagnostic, not network CU66 streaming or a30fps acceptance test.

## Exact versions and evidence

- Sealed ESP32 release: `firmware/experiments/v36-dual-local-fixture-20261106/release-dual-local-fixture-v001`; ELF SHA `13278b1f5a16afbcc5c1ed2f3c4c225c628a05b4491cc8e9ec489d02c88d3535`.
- Frozen firmware snapshot SHA `ff083a2b7b3a3438fe35a27b855f1ca01396e54e585845912e2562b5a64283e3`.
- Actual FPGA source manifest: `C:/mb70/fpga/experiments/cu66-v71/direct-system/final-integration-v008/sources.json`, SHA `15cc325a837720ae4f54dbb98b30d457d76271f416b7ef1576c198a68fde4b69`; top `cu71_system_final_v008`.
- Explicit local DY71 profile: magic `44593731`, ABI `00010000`, capabilities `0000000f`. Never alias the incompatible CU71 identity.
- Actual frozen v36/native HU through safe CSR/stager/finalv008/qualified SDRAM model KEY/P proof: `C:/mb70/fpga/experiments/cu66-v71/direct-system/final-local-v008`, qualification SHA `e3ef92ef75b1d2ccaf200385b3ab3ed859cf96581f70677f6a2126bf8c62a14e`. Two frames and42,240 actual write/readback words passed. Simulation does not establish physical SPI, timing or target performance.

No qualified BIT follows merely from these source and simulation records. Wait for exact-image reviewed routed setup/hold/pulse, route, native DRC, CDC/constraints/source binding and their hash-bound handoff. No BIT hash or ready receipt is invented here.

## Separate installation/programming window

1. Finish the separate B50/v32 25fps test; retain final counters, STOP/power-save results and logs. Stop all host senders and other hardware agents.
2. Use the established unique backup-and-verify **application-only** workflow. Preserve exact installed BIN/ELF/UF2 metadata, settings and SD files. Never erase whole flash or replace partition tables for this test.
3. Only after BIT gates are ready, perform the one physical update-mode step if still required by the Windows driver: power off, wait ten seconds, hold Volume-minus while pressing Power with USB attached. Install only the verified v36 app UF2 SHA `20cdbd6db030b0e99f363f93d0b081d2ca1f718c5e6dc6cb4d5d7edeff52ed97`. The runner never enters updater mode, resets, copies files, flashes, or uses JTAG.
4. Separately program the qualified finalv008 volatile BIT via controlled JTAG. Retain exact BIT SHA, device identity, programming/DONE evidence, profile and fresh paired app/FPGA lifecycle. App startup can restore the normal boot FPGA: record ordering. An epoch change alone is not a proven lifecycle fence.
5. Record the reviewed programming/operator receipt. Fresh means no old accepted frame/reference/HUD state or retained maintenance lease; it does not mean merely zero frame IDs. Y checks actual profile/freshness before writing. '?' identifies firmware only: it cannot establish the installed FPGA BIT. The programming receipt is an operator/JTAG witness, not a runtime BIT readback proof.
6. Identify the **physical Razer Kiyo** freshly by PnP instance/container ID and friendly name. Never trust cached DirectShow index1, which may be SmartConnect. Only in the authorized window, separately open the verified camera, show all four active panel corners and record through completion plus post-run hold. Metadata enumeration alone is not camera coverage proof. Preparation never opens camera/microphone.

Do not execute before exact images, fresh paired state, operator steps and camera coverage are verified. Installation remains separate from this runner.

## Runner usage and qualification adapter

Offline usage performs no serial import, discovery or open:

```powershell
python scripts/final_v008_first_fixture.py
python -m unittest discover -s scripts/tests -p test_final_v008_first_fixture.py -v
```

Future explicit execution, with a new unique output directory and an operator-selected port:

```powershell
python scripts/final_v008_first_fixture.py --execute --port COM_REPLACE_AFTER_ENUMERATION --output C:/ai/moonbub-evidence/final-v008-fixture-UNIQUE --qualification-manifest C:/ai/moonbub-evidence/reviewed-first-fixture-qualification.json --operator-receipt C:/ai/moonbub-evidence/reviewed-programming-receipt.json
```

PySerial is needed only for explicit execution; none was installed for preparation. DTR/RTS are inactive before open and never intentionally pulsed. USB-driver line behavior is not proven by host code. Any detected reboot/panic/disconnect aborts without reopen/retry.

The runner requires reviewed adapter schema `MOONBUB_FINAL_V008_FIRST_FIXTURE_QUALIFICATION_V1`:

- `overall: "PASS"` means eligible for this first controlled fixture, not completed hardware qualification.
- Exact `source_manifest_sha256` above and actual `bit_sha256`.
- `artifacts`: `{path, sha256}` list, all rehashed. Include BIT, exact source manifest, exact ELF, every gate report and the actual programming record.
- `checks`: `source_binding`, `functional`, `sdk_rtl_pairing`, `timing_setup_hold_pulse`, `route`, `native_drc`, `cdc_constraints`, each `{status:"PASS", evidence_sha256:"..."}` pointing to an artifact. A reviewer maps actual native build reports into this adapter. The runner does not independently interpret timing text or generate qualification. Never replace an open gate with a handwritten PASS.

The separate receipt schema `MOONBUB_FIRST_FIXTURE_OPERATOR_RECEIPT_V1` binds `qualification_manifest_sha256`, `programmed_bit_sha256`, `installed_elf_sha256`, `programming_record_sha256` and `profile: {magic:"44593731", abi:"00010000", capabilities:"0000000f"}`. All these observed preconditions must be true: `separate_B50_25fps_test_complete`, `host_senders_stopped`, `hardware_exclusive`, `fresh_paired_app_and_fpga_state`, `camera_coverage_verified`, `no_held_or_quarantined_lease`. These are operator attestations, not independently measured facts. Preparation generates no ready/PASS receipt.

## Exact USB sequence and measurements

Only **`?`, `W`, `Y`, `?`** are sent. Lowercase **`q` starts a QSPI benchmark**, never an identity query. G selects incompatible CU71 and is not sent. A wrong-profile G prewrite probe needs separate review.

1. **?**: one complete matching capture ID of USB_D24 reset/variant/memory/ELF/end pages. Require exact v36 variant and SDK ELF hash. Record uptime/reset reason, internal free/largest allocation and raw UsbTest stack high-water. Runtime pages are independent samples, not an atomic snapshot. Require at least170,000 free internal bytes and24,576 largest block before W/Y, matching Y's launch threshold.
2. **W**: actual CPU-only key/P native HU probe; no FPGA/QSPI/network/file writes. Require two21,120-word CRC rows (`358486a6`, `9b082f5c`), actual `caught_allocation_failure=true`, and terminal `result=Ok(...)`. Record per-frame prepare_us, allocator arrays, raw free heap before-negative/before-throw/after-throw/after-drop and worker stack_low. **Largest-block values at the throw are not logged by sealed W**; report them unavailable, separately from initial/final runtime largest samples. Allocator order is `[limit,live,peak,maximum_allocation,allocations,failures]`. W declares8,192 stack bytes. One deliberate caught throw does not establish every future exception behavior.
3. **Y**: guarded DY71 local KEY/P fixture. Require `completed_profile=Dy71 success=true`, Report `frames=2 accepted=2 presented=2 rejected=0 underruns=0 words_written=42240 words_verified=42240`, then `state=completed_held endpoint_retained=true lease_retained=true reconfigure_required=true`. Retain whole Report: elapsed/native CPU time, packet/admission/HUD/write/readback/drain/commit/presentation timestamps, allocator, QSPI scalar read/write **attempt** counts (including failed I/O), epoch, free/largest heap pairs, stack_low. Y declares12,288 stack bytes and131,072 native arena bytes. Raw SDK high-water units remain unconverted. Local fixtures have no network received counter: mark not applicable.
4. **?**: same firmware identity, nondecreasing uptime, reset reason and post-fixture free/largest/UsbTest high-water. Retained endpoint/lease and allocated memory are expected after success. This does not imply a clean/free paired state.

Host chunk timestamps are receive-API observations. Keep host/device/camera clock domains separate; never subtract monotonic clocks across machines/devices.

## Failure handling and scope

Capture retains exact raw bytes, UTC/monotonic timestamped per-chunk base64, decoded lines, command records, terminal rows and parsed fields. Bounds:16MiB raw,64KiB lines, identity10s, W120s, Y180s; firmware40-second per-frame deadline remains authoritative. Timeout means unknown state, not cancellation proof.

Heap/launch refusal, allocation/identity/profile/I/O/readback errors, missing completion, reboot or capture limit stops subsequent mutations. No automatic retry, reset, updater, radio/SD change, JTAG, unquarantine or lease release occurs. A mutated failure retains the actual quarantined-held endpoint/lease record. Success is also one-shot held. Never issue Y again automatically. Recovery requires a separately reviewed **paired** application/FPGA reconfiguration fence; one-sided reboot is not asserted sufficient.

A physical pass establishes one local KEY/P pairing plus observed target CPU/memory metrics. It does not establish sustained network video, audio/controller coexistence,30 unique displayed fps,<10ms decoding or analog SDRAM/PVT margin. B50/v32 remain untouched until the separate authorized installation window.
