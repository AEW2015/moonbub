# Private KEY diagnostic timing closure

These are isolated Vivado 2025.2 synthesized estimates on xc7a100tcsg324-1 at
100 MHz. None is a routed board image. Interface timing, physical playback and
sustained frame rate remain unqualified. The simulations check private pre-HUD
samples and tags, with no reference publication, HUD, external-memory drain or
scanout. Raw failed reports and immutable source variants are retained.

Latest completed gate: the combined compute source now passes internal100MHz
setup/hold with a clock XDC loaded **before** synthesis: **+0.456/+0.180 ns**,
zero failing endpoints and +3.750 ns pulse slack. Resource estimates are12294
LUT/13513 FF/57 RAMB36/33 DSP. This is still not routed board closure.

The exact same epoch-owned RTL previously measured -0.153 ns when synthesis
ran before clock constraints were loaded. The additive flow A/B retains both
reports; its positive result is a timing-driven mapping change, not another
RTL speedup. Source/part/default capacities and the10ns period are unchanged.
The qualifying report is `timing-driven/ooc/timing.rpt`, bound by local manifest
`93b61cc6fb05f157554aefa7fa5770a34934e38ab28469d476a5214a858947f6`
under `fpga/experiments/ar03-epoch-owned-20261104`.

That final source also adds an owned PRODUCT25 elastic coefficient slot and
removes one provably equal-value epoch assignment. Its full fixture checks
518400 samples/tag in **3000322 actual simulated clocks**. The slot carries
the old coefficient/quantizer product atomically and fences the next block after
raw last; inverse arithmetic is unchanged. Directed hold/cancel/error and real
wire-epoch/CRC tests pass. At nominal100MHz this one private result takes
30.00322ms; it excludes HUD, reference publication, external memory and scanout.
It is not30 unique physical presentations/s or a sustained pipeline benchmark.

## Measured iterations

| Variant | OOC context | LUT / FF / RAMB36 / DSP | Setup slack | Finding |
| --- | --- | --- | ---: | --- |
| Fixture diagnostic baseline | Whole private compute + fixture ROM | 15428 / 13503 / 53 / 33 | -2.961 ns | GM01 header arithmetic |
| GM01 staged validation | Same whole diagnostic, GM change only | 15430 / 13640 / 53 / 33 | -2.920 ns | Descriptor/query path remains |
| GM01 registered dimensions | Same whole diagnostic, GM change only | 15436 / 13692 / 53 / 33 | -2.913 ns | Raster becomes worst; GM paths still fail |
| GM01 offsets and query pipeline | Same whole diagnostic, GM change only | 15414 / 13812 / 53 / 33 | -2.913 ns | GM origin/destination improve to -0.489/-0.389 ns; parent request qualification remains |
| Cached parent block counts | Whole diagnostic with GM01 query pipeline | 15564 / 13916 / 53 / 35 | -2.913 ns | GM-origin/destination now +0.349/+0.695 ns; unchanged raster still dominates |
| Raster BRAM inference | Standalone raster | 658 / 367 / 4 / 3 | -2.284 ns | Memory inference fixed; address math remains |
| Raster address counters | Standalone raster | 692 / 408 / 4 / 1 | -0.892 ns | Address multipliers removed; boundary arithmetic remains |
| Raster validated narrow geometry | Standalone raster | 426 / 310 / 4 / 1 | -0.239 ns | Four boundary-enable endpoints still fail |
| Raster registered block geometry | Standalone raster | 466 / 318 / 4 / 1 | +2.375 ns | Internal setup and hold pass; whole combined design still needs checking |

Standalone raster counts must not be subtracted directly from whole-design counts
as a controlled area comparison. Synthesis context differs. The last row closes
standalone internal setup and hold only. Hold is +0.186 ns through the earlier
variants, +0.182 ns for narrow geometry and +0.180 ns for registered block geometry,
with the stated OOC constraints and unconstrained external interfaces. This is
not board I/O signoff or combined timing closure.

The baseline fixture replay checked 518,400 samples and all 16 stored tag bytes
in 2,997,214 actual simulated clocks. All three GM variants replay it in
2,997,218 clocks. The additional query latency in the third variant is hidden
by prefetch on this fixture; it does not prove every workload hides it. Both
sealed raster variants preserve the baseline replay and all 37 raster test
metrics exactly; later geometry variants also pass 11 asserted boundary/high-bit
cases. The cached parent preserves the GM replay's 2,997,218 clocks. These are
not physical 30 fps measurements or complex-scene
upper bounds.

GM validation/query regressions include 62 cases, 178,469 descriptors, malformed
full-width arithmetic and cancellation/held-response tests. The newest query
pipeline adds cancellation coverage at each phase and reads map RAM only for
validated requests. Subsequent work caches parent plane block counts and
registers bounded raster geometry/edge data. Those variants passed their
individual gates. The combined full-default path exposed the dequant/classification seam
and control paths addressed in the final result above. No routed candidate
follows automatically from those tests.

## Sealed local manifests

The following paths are local experiment records, not portable source exports.
All 335 artifact bindings across the five variant manifests below were rechecked
after sealing. The baseline's 42 bindings were checked separately.

| Experiment under `fpga/experiments/` | Manifest SHA-256 |
| --- | --- |
| `ar03-board-diagnostic-20261104` | `4b1edb00c306ae8e71a003a2d6b67bff6e250c255465f5fb5f0ee400d7147a4b` |
| `ar03-gm01-timing-20261104` | `062f3019e43381f26f8215b9cdc8d17b66c006a56209d3a12d5d733874ef97ff` |
| `ar03-gm01-timing-v002-20261104` | `e2e7582dc1ef7202823f7960c09bbc23968db85d8d8567aa8dc8db1f621182cc` |
| `ar03-gm01-timing-v003-20261104` | `4de0190a761c7e0245dbd18d2ff32f8b2001e028b11621b911dbd578b129fa44` |
| `ar03-raster-bram-20261104` | `9ac5c6fbffdc298df2d9c9a6ca33a2a96fc62a110dddd823b485903a66c84182` |
| `ar03-raster-address-20261104` | `479889cd967b33915206bb86c4574da967c173223cb135c1e53779fea22f95c9` |
| `ar03-parent-count-cache-20261104` | `459ab4951eaed976e09661e1206f589d589366521b07ceb2a34154db987768f8` |
| `ar03-raster-geometry-20261104` | `dd32c3eb8fa00b88b620d64eb617b7889a82546401bbe0dffc52419fc775212e` |
| `ar03-raster-boundaries-20261104` | `981aace3deea709e7e8d9ab2b2c386e4680862313d440a3d09e5e60b8ed6445d` |

The additional three manifests' 431 artifact bindings were also rechecked. The
geometry experiment retains the initial Icarus-accepted/Vivado-rejected lexical
source separately; only the final whitespace-corrected source is qualified by
its completed replay and synthesis evidence.

## Next implementation gate

Close the remaining internal paths in a combined full-capacity diagnostic, then
prepare an explicit decoder-exclusive board variant. Internal closure is now
complete as qualified above. The actual-top wrapper passed153 real-source QSPI
checks,16 reset cases/96 checks, two natural LCD frames and the full golden job.
Its source/test manifest is
`a6e521238b6e6843940d0100bc85397aa21f91cd3da76856a04da1a3bff4f15d`.
It is moving to a separate board implementation candidate; netlist constraints,
routed timing, route/DRC/CDC and hardware remain separate gates. Build50 uses
120.5/135 BRAM tiles; adding another full decoder is not the chosen assumption.
Removing JPEG can prune currently constrained SDRAM/CDC paths: the variant needs
an actual-design constraint review, not dummy logic, broad exceptions or stale
cell-count checks. Retain electrical pin/clock budgets and positively check all
remaining live paths. An unused interface is not physically qualified by removal.

The [AKD1 local contract](AKD1-COMPUTE-DIAGNOSTIC-20261104.md) defines the reserved
diagnostic identity and restricted access. The ESP accessor is not installed,
and there is no custom UDP endpoint. A source-bound routed image, guarded app
and coordinated physical window must precede hardware compute measurements.

The first board implementation stopped at its strict netlist gate: 188 obsolete
framebuffer LCD cells survived through inherited ASYNC_REG attributes. That
failed candidate is preserved under manifest
`64fe98bc68a9bbb3902652a3c4dc7d00a82a7b6b4f40218cbd34d0ea012b3710`.
The additive `akd1-compute-lcd-prune-20261104` candidate removes only attributes
on those inactive paths, preserving live pattern synchronization. Executable
tokens and declaration widths/initializations compare identically after
attribute removal and declaration canonicalization. Its real-source platform
and reset checks pass again; no constraint was relaxed.

The successor's strict gates now find zero inactive external-memory, unused
receive-clock or obsolete framebuffer LCD cells, and positively find the real
compute, LCD counter, overlay/audio memories and exact margin/timing crossings.
Full board routing completed with setup **-2.184 ns**, hold **+0.007 ns** and
pulse-width **+2.000 ns**. There are 13,629 failing setup endpoints, zero hold or
pulse failures and zero DRC errors. No bitstream or physical readiness is claimed.
The worst setup path launches from `bridge/queue_reg` BRAM and traverses command,
admission, cancellation/error and coefficient-write-enable logic to
`inverse/coeff_reg[3][9]/CE`: eleven LUT levels and 11.960 ns data delay, of which
8.142 ns is routing. This is a command/control path, not the initially suspected
coefficient operand-read mux. The next candidate should introduce a reviewed
command/control register boundary while preserving ordered MMIO, reset priority
and abort semantics. Do not add inverse fetch latency to address a different cone.
Selected [routed failure records](measurements/akd1-routed-failure-20261104/README.md)
are retained under manifest
`a36bcaa4d7e3cd1d7722b9ef7cf49bdc8b3d735c6cc467ce910a2cb81a0d84d1`.
