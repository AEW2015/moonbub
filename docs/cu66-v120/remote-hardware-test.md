# V120 remote hardware bring-up

This branch supplies a decoder-component development handoff for another Game Bub system. It does not supply a complete board bitstream or an updated production Sunshine/ESP32/JPEG pipeline. The component is `cs88_pipeline_v91k`, targeting `xc7a100tcsg324-1`. Preserve the working JPEG image and the independently qualified [V118 control](../cu66-v118/handoff.md) for comparisons.

Source export requires Git and Python 3.10 or newer, using only the standard library. Reproducing the native component implementation requires Vivado 2026.1 build 6511674, installed Artix-7 support for the exact part and a valid local license for that tool/device. License files and AMD tool binaries are not supplied by this branch. Reproducing the retained behavioral proof uses its separately pinned Verilator 5.020/C++17 environment.

## Select the measured source

The [handoff manifest](../../experiments/python-gamebub-v120/handoff.json) is the authority for the selected Source B composition, qualified 100 MHz clock, original run and separate positive fresh repeat. Its 18 source/include files remain byte-identical to `69c0f145`; the qualification commit adds evidence without a decoder RTL change. The exporter requires this manifest and both receipts. A passing V118/V119 clock does not qualify a V120 source substitution. The [measured results](../../experiments/python-gamebub-v120/results.json) retain the failed 125 MHz target and all other trials as well.

Prepare the exact source alias tree in a new directory:

```bash
git clone --branch study/gamebub-v120-range-ingress-timing-20261109 \
  https://github.com/AEW2015/moonbub.git moonbub-v120
cd moonbub-v120
git rev-parse HEAD
python3 scripts/cu66-v120/prepare_handoff.py \
  --output /absolute/new/v120-component
```

The exporter checks both positive routed receipts, source/tool/recipe identity, clock period and source hashes before copying all 18 source/include files. It does not run Vivado or contact hardware. `snapshot/` is the selected alias tree; use the manifest's read order and include directories. Do not collect files by version number or compile both an old and new module definition. The prepared Tcl reproduces the component-only study, including its strict Vivado 2026.1 build check; it is not a board project. If relocating an export before running its Tcl, regenerate with `--mapped-path /absolute/path/as-seen-by-vivado` so its absolute file references are correct.

After loading the licensed Vivado environment on the other system, an optional fresh **component-only** implementation uses:

```bash
vivado -mode batch -nojournal -nolog -source /absolute/new/v120-component/run.tcl \
  -tclargs /absolute/new/v120-component
```

Treat that as a new measured campaign and retain its reports. The local study dispatchers include host-specific Docker and external build-archive paths; the exporter is the portable handoff entry point. Neither the exported recipe nor the study dispatcher generates a board image.

The same checkout includes the stable, repeat-qualified V118 100 MHz control. To prepare that comparison source independently of the qualified V120 Source B handoff, export it with its own exporter and manifest:

```bash
python3 scripts/cu66-v118/prepare_handoff.py \
  --output /absolute/new/v118-100mhz-control
```

Keep that source and its reports labeled V118. It is a fallback/control, not evidence that V120 meets 100 MHz.

## Board-team integration

Use the actual Game Bub board revision, oscillator, PLL/MMCM, pin assignment, I/O timings, SDRAM controller and display constraints. Generate a real 100 MHz decode clock and qualify the complete design at that clock, including hold/pulse checks, CDC/reset handling, clock uncertainty, memory arbitration and scanout deadlines. Do not apply the component's single-port clock constraint as a replacement for the board constraints or waive its intentionally missing external I/O delays in the board build.

The existing [board top](../../fpga/rtl/moonshine_top.sv) and [platform constraints](../../fpga/scripts/platform.xdc) are integration references for the existing JPEG design. That top instantiates `moonshine_core`, not V120 `cs88_pipeline_v91k`; building it unchanged does not test this custom decoder. The component's full interface is in [cs88_pipeline_v91k.sv](../../fpga/experiments/cu66-v115-owner/cs88_pipeline_v91k.sv), whose exact selected version is pinned by the exported manifest.

The integration must provide bounded packet ingress, the complete reference-request/response tuple, accepted reference/generation and cache state, output backpressure and physical write acknowledgments. Keep provisional output separate from the displayed/accepted reference until all required checks and physical writes finish. A cancellation must drain accepted work before storage ownership is reused. The full interface and its debug/counter ports are in the selected top RTL.

Keep the wide debug vectors internal to the board design; they are not a physical pin interface. Expose selected diagnostic counters through a registered, epoch-consistent snapshot or debug instrument. Preserve functional handshakes, error/revocation signals and ownership fences at their required latency. The OOC study preserves extensive observability, so a board design with different diagnostic connections needs its own implementation measurements and functional verification.

The custom CS88/CU66 study uses a 720×480 coded profile and a 49,152-byte complete-packet cap. Production JPEG transport does not implicitly accept those packets. Profile negotiation, actual HUD semantics, C2/content/seal verification and safe presentation require the production adapter described in the [existing receiver contract](../cu66-v99/hardware-handoff.md). The study's abstract parent and software HUD oracle do not implement those missing production pieces.

## Staged tests and data to return

1. Replay local, known packets before enabling networking. The full-component receipt pins `experiments/python-gamebub-v91i2/vectors/cases.tsv`, `experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz` and `experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz`. Use their exact packet histories and independent golden bytes. Compare all canonical outputs and expected failures, not just a displayed image or decoder `done` signal.
2. Exercise output stalls, real memory wait states, cancellation with outstanding requests, malformed input and a clean retry. Reconcile request/response/write-ACK counts and verify bounded ownership. Run scanout concurrently to measure its actual contention.
3. Feed distinct frames through the real host → ESP32 → QSPI → FPGA path. Keep received, decoded, validated, presented and dropped counts separate. Record source and presented frame identities; a repeated image must not count as a new frame.
4. Run the defined 60-second/1,800-frame and 600-second/18,000-frame gates, then evaluate strict packet-complete → validated-publication latency below 10 ms. The [product gates](../cu66-v110/hardware-gates.md) define the acceptance conditions. The [offline evidence checker](../cu66-v110/hardware-evidence.md) can check supplied trace arithmetic and hashes; it cannot authenticate physical execution.

Return the tested Git commit, selected manifest hash, exact board/part, complete-top RTL/XDC/firmware hashes, bitstream hash, full-board routed timing/utilization/methodology reports, clock calibration, raw logs and per-frame trace. Capture first/last input acceptance, canonical output, final write ACK, validated commit and actual presentation timestamps, plus FIFO high-water marks, memory/display stalls, outstanding owners, underruns and all error causes. Define counter widths, wraps and reset epochs explicitly.

## Expected performance, pending hardware measurement

At an assumed 100 MHz for the complete parent, the fast and bounded-stall row fixtures take 11.45104 and 15.53197 ms from the final accepted input byte to validated commit. This leaves 21.88229 or 17.80136 ms within a 33.33333 ms frame period for all excluded work. It is a budget estimate, not sustained throughput or measured device latency. Both fixtures remain above the strict 10 ms target. Byte-at-a-time service already takes 37.04705/94.84147 ms and is unsuitable for the intended frame budget.

The current Source B 125 MHz route still fails at −1.517 ns. Further 125 MHz source experiments remain separate from this pinned 100 MHz handoff; they need their own functional regression and fresh routed timing qualification.
