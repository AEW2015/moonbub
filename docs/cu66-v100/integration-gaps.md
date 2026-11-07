# V100 source inventory and integration gaps

This inventory is a source-level audit of the frozen V99 RC1 research profile
and the available production FPGA image and V91 CS88 components. The generated
[inventory JSON](../../experiments/python-gamebub-v100/inventory.json) records
the profile hash, source paths and SHA-256 hashes, module definitions, observed
ports, source-declared clock domains, constraints, and explicit storage ledger.
Regenerate it with `python3 scripts/cu66-v100/inventory.py`; it uses only the
Python standard library and does not invoke FPGA tools.

The profile remains **CS88-V99-RC1-Q16-BR88**, frozen as a research candidate
only. The profile JSON hash and frozen parameter subset are embedded in the
inventory. The relevant bounds are 720×480, zero motion, 32-pixel blocks,
BR88-only residuals, 65,536 maximum chunk blocks, 49,152 complete packet bytes
including outer CRC, key method 0, P method 3, QM87 methods 2 and 6, and default
uniform scale 16/code 1. Do not widen these bounds based on a component test.

## Existing image and candidate component chain

The existing source top is `moonshine_top` in
`fpga/rtl/moonshine_top.sv`. It wires the active QSPI endpoint and bus CDC to
the JPEG/MSV1 `moonshine_core`, shared SDRAM/scanout memory, LCD timing, and
ESP32 overlay. Its source-defined clock domains are 50 MHz input, 200 MHz QSPI,
100 MHz core/memory, 100 MHz phase-shifted SDRAM read, and an approximately
29.362 MHz LCD pixel clock. The existing source-backed device target is
`xc7a100tcsg324-1`. This identifies the historical image target; it does not
identify a physical board or establish candidate fit.

No complete CS88 custom top exists in the reviewed source. The highest present
candidate stream chain is:

```text
cs88_admission_v91i2a (separate admission component)
        │
        └── cs88_pipeline_v91j
              ├── V91i2b BR88 ingress/refill and coefficient placement
              ├── V91j dequantization and inverse transform
              └── cs88_pipeline_v91k
                    ├── V91k reference reconstruction
                    └── canonical_rgb565_v91k
```

`cs88_validate_publish_v91l` is a separate validation/publication experiment,
not a joined endpoint of this graph. The component build target to start from
is `cs88_pipeline_v91k` using its source and the dependency closure recorded in
the inventory. It is an elaboration or isolated component target. A wrapper
and actual joins are required before it could represent an integrated CS88
image.

## Typed stream boundaries

| Boundary | Present source-level payload | Status |
|---|---|---|
| V91j coefficients | Plane, tile, quantization cell, index, signed 24-bit dequantized coefficient value, epoch | BR88/dequant/IDCT component output; no validation acceptance or display commit |
| V91k canonical reconstruction | Plane, mode, tile, index, sample value, frame ID and epoch | Adds reference reads and residual/COPY/CONST reconstruction; no full-frame C2/HUD acceptance |
| V91l validation | Isolated validation/publication component signals | Not connected to the selected packet admission and reconstruction top |
| Existing front display | `moonshine_core` pixel valid/ready, address and RGB565 data into `moonshine_memory` and `moonshine_lcd` | Existing JPEG/MSV1 path; the CS88 component output is not connected to it |

The software golden replay boundary remains authoritative for exact packet,
canonical output, HUD and content identities. The current C++/host reference
path checks semantics; exporting RTL-facing vectors or running an isolated
child test does not make that work target RTL. Do not treat CU66's rectangle,
geometry and words HUD hash as the CS88 words-only RGB565 HUD hash preimage.

## Storage and physical accounting

The ledger records finite logical storage only where source declarations give
an explicit width and depth, including the 49,152-byte packet array and the
mode/quantization maps in `cs88_admission_v91i2a`. It distinguishes these
declarations from inferred physical resources: synthesis can map arrays to
registers, LUT RAM or block RAM, optimize unobservable state, or implement
interfaces differently. The inventory therefore makes no candidate LUT, FF,
DSP, BRAM, total RAM or frequency claim.

The whole system still needs a finite memory map across packet storage,
coefficient/reference/candidate/canonical/display storage, exact read/write
ports, write acknowledgements and ownership. Reference and candidate writes
must remain provisional until actual C2, HUD, frame-seal and write-drain checks
complete. Display publication must then wait for vblank and scanout drain.
SDRAM refresh, turnaround and arbitration must fit this same ownership and
port ledger.

## Integration work still open

- Bind transport epoch and core generation to the CS88 transaction. CS88 has
  a wire generation but no wire epoch; the active QSPI/MSV1 path is not custom
  CS88 capability negotiation or bounded packet ownership.
- Join actual packet ingress, admission, BR88 decode, reference reconstruction,
  exact HUD composition, C2 tree/root and frame-seal calculation, write ACKs,
  atomic accepted-reference publication, and display release.
- Keep typed coefficient and canonical streams as intermediate interfaces.
  Neither constitutes validated accepted frame pixels.
- Map reference, candidate and display stores through the actual shared memory
  service with bounded ports, refresh/turnaround, stale-response handling,
  cancellation drain and scanout protection.
- Add actual CS88-to-display conversion and RGB565 HUD selection to the front
  path. Existing LCD and overlay wiring only proves the current image path.
- Establish an actual selected source closure, build target, constraints,
  timing exceptions, memory initialization files and full-device resource
  accounting for each candidate build.
- Preserve key/reset and overflow behavior. The fixed q16 candidate has no
  universal packet-cap proof or implemented automatic overflow fallback.

## Verification and tool status

The [fresh V91j RTL report](../../experiments/python-gamebub-v100/rtl/results.json)
now passes both seeds 100401 and 100402: each runs six cases and thirteen
directed checks for signed dequantization and IDCT. The [paired V91k converted
RTL report](../../experiments/python-gamebub-v100/converted-rtl/verification.json)
passes seeds 911501 and 911502, including the pipeline and RGB replay sets. It
compares the original frozen SystemVerilog against the `sv2v` branch and its
public-array wrapper; all 308 public ports match, and per-seed simulation
transcripts, stage events and canonical bytes are identical. The converted
build retains its known warning classes; original assertions are enabled,
while `SYNTHESIS`-guarded RTL assertions are omitted in the converted branch
and the unchanged C++ checker remains active. These are bounded behavioral
component checks, not formal equivalence, mapped-netlist simulation, or proof
of full CS88 validation/publication. The [independent audit](../../experiments/python-gamebub-v100/audit.json)
rehashes the retained attempt artifacts and records the scope limits.

The Vivado MCP connection was closed. Vivado 2025.2 CLI preflight found zero
matches for `xc7a100tcsg324-1`, zero 7-series parts, and 504 other installed
parts; two cold exact-target preparations did not start synthesis or
implementation. See the [preflight receipt](../../experiments/python-gamebub-v100/preflight/results.json)
and [query log](../../experiments/python-gamebub-v100/preflight/vivado-query.log).
A separate Vivado 2026.1 Acorn installation probe crashed in allocator/libudev
startup both with and without `LD_PRELOAD`; it did not reach a part query, so
no part count is available from that installation. See the [default-environment log](../../experiments/python-gamebub-v100/preflight/vivado-2026-query.log)
and [no-preload log](../../experiments/python-gamebub-v100/preflight/vivado-2026-no-preload-query.log).

Yosys 0.33 and `synth_xilinx` family mapping are available, but family mapping
does not establish exact-device placement/routing or Fmax. Any isolated leaf
mapping or generic XC7 report must retain its component scope. Exact-target
Vivado synthesis, whole-pipeline fit, routed frequency, physical board
identity, sustained 30 fps and strictly-under-10-ms complete decode remain
unqualified. The source-backed JPEG target is not evidence of V100 candidate
fit.
