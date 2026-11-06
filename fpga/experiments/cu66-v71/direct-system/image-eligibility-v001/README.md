# DY71 final-image gate and read-only audit

This is a prepared tool, not an image qualification. No native audit, BIT generation or hardware action has been executed for this handoff. The current report-only build is `C:/mb70/dy71i03`; root owns selection, completed-build review and all later hardware decisions.

The helper is `scripts/cu66-v71/image_dy71_candidate.py`. Its default mode is `qualify`, which never invokes Vivado or writes a BIT. All output directories must be new. It never opens JTAG, accesses flash/SD, changes clocks or timing exceptions, reroutes a design, or overwrites the original DCP. Native audit and emission operate on an independently hashed private DCP copy.

## Required order

1. Let the full implementation finish. Verify the exact selection SHA, complete execution, all source/header/constraint hashes and frozen inputs. The automatic gate requires global **routed** setup, hold and pulse slacks strictly positive, zero failing timing endpoints, all routable nets routed and zero routing errors. Positive synthesis or placed slack is insufficient.
2. Run explicit `--mode audit` only after root selects the completed positive build. This opens the private DCP copy read-only, verifies exact DY71 part/top and USERID/USR_ACCESS, inventories every BITSTREAM property, queries uncapped unwaived native DRC violations, and refreshes timing/route/CDC/exception/skew/clock/check-timing reports. It writes no image or checkpoint. Native ERROR, missing output, changed DCP or DRC Error stops the operation. Each native process uses a unique short `C:/vtmp/dyimg-<timestamp>` TEMP/TMP without altering machine settings.
3. Generate `--mode template` from that audit. The resulting internal root-review JSON is unsigned, incomplete and unable to qualify an image. Root must review actual object/exception coverage, the held-payload CDC protocols and their bounds, pin/SDRAM/IO budgets, bus skew, reset/clock behavior, native warnings and DRC, exact final functional-source composition and actual application/profile binding. No fixed CPL1 counts, hierarchy, CDC exceptions or waivers are inherited. Every review category needs hashed evidence and an explicit finding. There must be no unresolved finding.
4. Root signs the review with its integration identity and UTC timestamp and pins its SHA256 on the command line. This records internal engineering review; it is not a request for user permission or an external cryptographic signature. For intended emission, set `image_emission_authorized=true` **before** qualification. A later change invalidates the qualification.
5. Run default `qualify`. It rechecks the complete artifact map and writes an exact `qualification.json`; no native process/image is created. `c_check_handoff` is unavailable, so the review must say `UNAVAILABLE_MANUAL_INTEGRITY_REVIEW`; no external checker PASS is invented.
6. Only after root selects generation, run `--mode emit` with both the exact prior qualification and SHA, plus the same signed review and SHA. The helper repeats the native DCP/DRC/identity checks before one `write_bitstream`. It then rechecks every bound source/report/review/DCP and compares the complete BITSTREAM property inventory with the audited DCP. Binary inspection checks the `.bit` top/device/compression/USERID header and the pre-FDRI AXSS/USR_ACCESS and IDCODE writes. Final BIT and evidence hashes are written. No hardware is programmed.

If any native/emission check fails, the new output and any partial BIT remain preserved and are explicitly **unqualified**. Do not use an image lacking the final image-hashes and eligibility record. The original report-only selection keeps BIT/PROGRAM false; the separate reviewed qualification is the only emitter authorization.

## Commands to adapt after gates pass

Use absolute paths, the exact frozen selection hash, and fresh output directories. These commands are examples and were **not run**.

```powershell
python C:/mb70/scripts/cu66-v71/image_dy71_candidate.py --mode audit --build C:/mb70/dy71i03 --selection C:/mb70/fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v008/selection.json --selection-sha256 3e5760ca6da2d593febe00655cb0a343d6d675f02db2ea8d1e9623df0fef6ba8 --output C:/mb70/dy71-image-audit-UNIQUE
```

For template/qualify/emit, retain those build/selection arguments, add `--audit C:/mb70/dy71-image-audit-UNIQUE`, and choose another new output. Qualify additionally needs `--review <signed-root.json> --review-sha256 <exact>`. Emit needs those same review arguments plus `--qualification <prior/qualification.json> --qualification-sha256 <exact>`.

## Honest limits and remaining review

- The helper's fail-closed parsers and generated Tcl syntax have focused executed tests; this does not qualify its native audit against a completed DY71 DCP yet. Root must review the helper before the first native audit.
- Root content review is required because file integrity and a client-authored PASS cannot establish CDC/IO correctness or exact test coverage. Existing manual CDC conditions remain protocol obligations; no analog MTBF/PVT claim is made.
- Native uncapped DRC is necessary because the build's standard report may cap warning details. A standard report showing no Error is insufficient by itself.
- The BIT parser checks identification before compressed FDRI data; final SHA256 binds the entire BIT. It does not decode or prove the compressed frame payload or physical FPGA behavior.
- The handoff manifest remains `INCOMPLETE` for hardware. No 30 fps, physical QSPI, display/audio/controller coexistence or physical playback claim follows from image generation.

The older CPL1 reset-replica helper was consulted only for its fail-closed audit/emission separation. No CPL1 constants, endpoint counts, reset ECO policy or physical qualification is reused.
