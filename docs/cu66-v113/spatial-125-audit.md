# V113 prepared 125-MHz card and final spatial audit

Status: **PASS_V113_NATIVE_PREFLIGHT_AUDIT** for the exact prepared card below.
This is a read-only preflight and evidence audit. No Vivado/MCP job, simulation,
container execution, bitstream or hardware action was launched by this reviewer.
Reading the existing Docker image identity does not execute that image.

The [card](../../experiments/python-gamebub-v113/prepared/v113-spatial-125-20261108T213508223451Z-c7c92f/preflight.json)
is SHA-256
`6e5681813e98f4f262246c20f1f2007b2535c0996b98cedf9dd48c382770b1a7`.
Its policy is SHA-256
`3359380684401e5bacda1413b4c7891350bcef852638d27243d80e9794bab786`.
The machine-readable [preflight audit](../../experiments/python-gamebub-v113/audit/spatial-125-preflight.json)
binds these exact hashes and the selected spatial audit.

Independent checks verified:

- Both repository-prepared and external-build `inputs.json` copies equal the
  card and its input hash. All four prepared Tcl/XDC recipe copies match the
  current frozen flow and their declared hashes.
- All 18 external snapshot bodies match current qualified source origins and
  the selected focused proofs. The exact 17-SystemVerilog read order and ROM
  include path were reconstructed independently. Exactly geometry, scratch
  and inverse replace the V112 origins; the remaining 15 are unchanged.
- The current frozen driver/tooling and policy hashes match. The driver's
  read-only spatial/source qualification reproduces the complete card source
  contract. Actual geometry/scratch/inverse focused receipts and all their
  source/artifact pins pass verification.
- The only active XDC command creates `component_clk` at **8.000 ns**, waveform
  0/4 ns. The clock is loaded before fresh RTL synthesis. Synthesis uses
  Default by omission, opt/route use Default, placement uses
  ExtraNetDelay_high, and physical optimization is NONE. No retiming, timing
  exception, guessed I/O delay or bitstream/hardware command is introduced.
- The existing `acorn-nexys4-ddr:2026.1` tag resolves to the declared immutable
  image `sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`,
  matching the validated V112 image. The Tcl retains its 2026.1/build-6511674
  runtime guard. No tool version was newly executed in this audit.
- The initial 125-MHz dispatch budget was available at review. Policy limits
  each job to two CPUs, 8 GiB RAM and an equal RAM-plus-swap ceiling, with
  3,600-second native watchdog, memory/PSI/combined-pressure stop gates,
  two initial trials and at most one positive fresh repeat. Root must still
  check live resource, active-job and license conditions at dispatch.

The [final spatial audit](../../experiments/python-gamebub-v113/audit/spatial-final.json)
independently verifies the selected successful receipt at
`spatial/attempts/20261108T212355592057Z/receipt.json`: all **39 source pins**
and **55 artifact pins** match. Its reused full-component certificates cover
44 case/profile rows and 42 original directed checks from the retained parent
attempt. That parent's later adapter compile failed, and its overall FAIL
status remains intact. The selected adapter-only attempt reports **zero newly
executed full-component profiles/checks**.

Both actual V97-to-CS88 transport campaigns are newly executed: 12 successful
case/profile rows and two abort/reset retry checks per seed, 24 and four in
total. Each reaches 2,048 FIFO/reserved bytes and two owned descriptors, drives
16 wrong DMA tokens and 16 wrong software-completion tokens, and holds the ACK
for 17,230 checked cycles. Software completion matching is an explicit adapter
check; V97 has no incoming completion-token port. All 12 normal ingress commits
per seed precede decoder done, each complete candidate has 518,400 accepted
pixels, and both decompressed canonical streams exactly match V112.

The original coefficient/dequant/residual/pixel/owner/error/held/drain oracles
remain active. Exact old public cycles are not claimed under IV113.1. V97 and
CS88 share a simulated rising edge; the adapter does not serialize QSPI pins,
execute ESP32 firmware or native Sunshine, qualify physical CDC/memory/panel
service, or implement C2/HUD seal and final publication.

The generated performance report matches the independent read-only cycle
recomputation. Its 100/125-MHz conversions are conditional arithmetic; the
125-MHz fast-profile maximum is 11.072 ms from first accepted component byte
to local done. No sustained hardware 30 fps, complete validated decode below
10 ms, full-parent clock, or routed V113 timing qualification follows from
these proofs or this prepared card. Terminal reports and any required positive
fresh repeat remain separate acceptance gates.
