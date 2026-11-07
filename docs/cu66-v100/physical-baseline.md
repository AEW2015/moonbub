# V100 physical baseline and reproducible prerequisites

The [selected machine-readable results](../../experiments/python-gamebub-v100/physical/results.json)
identify each success, failure, partial checkpoint and superseded diagnostic.

The exact target flow is **blocked before synthesis**: the installed Vivado
2025.2 cannot find `xc7a100tcsg324-1` or any `xc7*` part. Two independent cold
directories reproduce that result. No target checkpoint, placed/routed clock,
whole-device fit, board timing, 30-fps or complete-decode result exists here.

The available baseline top is the unchanged `cs88_pipeline_v91k` component,
not a complete custom decoder/board top. It joins packet admission, BR88,
dequantization, inverse transform and canonical reconstruction; the real HUD,
C2/seal/publication, shared SDRAM/display and transport/CDC endpoints remain
outside this component. All its existing diagnostic ports remain public.
The source-backed JPEG target part is established; physical board identity
and a complete custom top remain prerequisites.

## Frozen inputs and flow

[Frozen inputs](../../fpga/experiments/cu66-v100-baseline/frozen-inputs.json)
pin all 16 RTL sources and their equality to baseline commit
`f403a5f5149de60ebc128ac57911c4912bec0ddf`, the sole include
`cu66_quant_rom.svh`, the recipe, runner and policy. There are no external
memory-init files, generated IP, board preset, or imported checkpoints.
Power-on values/initial blocks already in the RTL remain part of those hashes.
No existing `.xpr` is the source of this component, so the revision-control
skill's project-export pipeline is inapplicable; this is a self-contained
nonproject recipe with a source snapshot and explicit settings.

The [policy](../../fpga/experiments/cu66-v100-baseline/policy.json) freezes OOC
synthesis, rebuilt hierarchy, Default synthesis/opt/place/route directives,
two Vivado threads, no retiming, no physical optimization, no incremental DCP
and no seed override. The [XDC](../../fpga/experiments/cu66-v100-baseline/component.xdc)
defines only a 10-ns component clock, the roadmap's 100-MHz comparison target.
Synthesis precedes loading that clock constraint; placement/routing and timing
reports use it. This ordering is part of the frozen recipe, not evidence of
clock-driven synthesis or achieved 100-MHz operation.

External memory/refill/cache/reference/output handshakes have no qualified
board arrival/required-time contract. There are deliberately no invented
input/output delays, clock uncertainty overrides, pin assignments or blanket
false paths. External paths stay visibly unconstrained. OOC omits I/O buffers;
only reported internal paths can assess the comparison target. A board top
must supply actual controller/port timing and CDC constraints before signoff.

If target support is available, [build.tcl](../../fpga/experiments/cu66-v100-baseline/build.tcl)
exports synthesis/place/route DCPs, hierarchical utilization, min/max timing
summaries including unconstrained paths, 50 setup paths, clocks, check_timing,
methodology and DRC, plus primitive and DSP48E1 instance ledgers. Version
dependent RAM/fanout/clock-utilization reports record explicit availability.
No bitstream or hardware programming is part of this recipe. The timing skill's
full 2026.1+ JSON workflow is unavailable in installed 2025.2; native supported
reports remain the specified evidence, with no waivers or inferred fixes.

## Selected cold exact-part attempts

| Attempt | Receipt | Result |
|---|---|---|
| A | [receipt](../../experiments/python-gamebub-v100/physical/v100-final-exact-a/receipt.json) | Target count 0; Series-7 count 0; synthesis/implementation never started |
| B | [receipt](../../experiments/python-gamebub-v100/physical/v100-final-exact-b/receipt.json) | Same frozen inputs and same missing target prerequisite |

The [repeatability receipt](../../experiments/python-gamebub-v100/physical/repeatability.json)
reports `NOT_ESTABLISHED` for the physical baseline. Repeating an unavailable
part query is a reproducible prerequisite failure, not a repeated synthesis or
route. Root's [independent tool query](../../experiments/python-gamebub-v100/preflight/vivado-query.log)
also found 504 other installed parts. No alternative part substitutes for the
target. The connected Vivado MCP transport was unavailable, so these attempts
use the already installed batch tool in `gamebub-cu66-v69-vivado`.
The separate installation under the 2026.1 tool path in `acorn-nexys4-ddr` crashes
with allocator/libudev errors before the read-only query executes; its
[two probe results](../../experiments/python-gamebub-v100/preflight/secondary-results.json)
leave that installation's device support **unknown**, not absent. The Acorn
project and installation were not changed. Neither installation produced a
usable exact-target implementation session.

## Unchanged-source technology-mapping diagnostic

Already installed Yosys 0.33 advertises generic `synth_xilinx -family xc7`
mapping. This provides a useful diagnostic without target device installation;
it does not provide exact-part capacity, routing or timing.

Both cold direct-source attempts stop at the same frontend limitation for the
whole component: `br88_rice_elastic.sv:50`, `unexpected TOK_INT` at an `int'`
cast. Direct dequant and inverse-transform leaf reads similarly stop at lines
41 and 73. The retained local primary help explicitly says the native frontend
supports only a small SystemVerilog subset. No source edits, tied inputs or
removed ports turn these failures into passes.

The unchanged `cu66_reconstruct_tile` leaf does map twice. All 18 original
ports retain their names, directions and widths. Its primitive counts are:

| LUT2–6 | FDRE | CARRY4 | INV | DSP48E1 | BRAM | SRL |
|---|---|---|---|---|---|---|
| 2,202 | 546 | 704 | 128 | 0 | 0 | 0 |

The [A receipt](../../experiments/python-gamebub-v100/physical/v100-final-yosys-a/receipt.json),
[B receipt](../../experiments/python-gamebub-v100/physical/v100-final-yosys-b/receipt.json)
and [repeatability report](../../experiments/python-gamebub-v100/physical/yosys-repeatability.json)
pin matching mapped-netlist hashes, original source/tool/library/settings
hashes, premap memory inventory, primitive counts and intact port checks.
This leaf has no inferred memory; it cannot inventory the missing complete
system's packet/coefficient/reference/candidate/display storage. The mapping
uses default DSP/BRAM/LUTRAM/SRL inference with `-noiopad -noclkbuf`, preserves
hierarchy, and does not retime. Zero DSP in this leaf says nothing about IDCT
DSP mapping, which direct native parsing did not reach.

An additional lexical int-cast compatibility probe is retained separately. It
lowers 17 packed-integer `int'` casts to signed 32-bit size casts without
modifying originals. The syntax probe passes, but the component then stops at
the independent unpacked constant-array initialization at
`br88_context.sv:30`. This failed compatibility probe does not establish a
mapped whole component or functional equivalence. Its
[status/hashed artifacts](../../experiments/python-gamebub-v100/physical/int-cast-frontend-probe/status.json)
and [lexical adapter](../../fpga/experiments/cu66-v100-baseline/lower_int_casts.py)
are separate from the unchanged-source baseline.

## Standard sv2v frontend investigation

The official [sv2v v0.0.13 release](https://github.com/zachjs/sv2v/releases/tag/v0.0.13)
provides a standard SystemVerilog conversion frontend. The external 2.2-MB
release archive and binary are self-hashed; the release does not provide a
publisher checksum, so the receipt does not claim one. The
[separate conversion runner](../../fpga/experiments/cu66-v100-baseline/sv2v_mapping.py)
does not alter the direct frozen recipe or originals. It retains all original
inputs and passes `-D SYNTHESIS`; original simulation-only assertions guarded
by that define are excluded, and the standard assertion conversion applies.
The behavior checker must keep its original terminal/pixel/event checks.

Conversion attempt A failed before parsing because the Haskell runtime could
not create OS threads under the generic address-space limit. Conversion uses
one GHC capability and a 1-GiB managed-heap limit instead; Yosys retains its
2.5-GiB address limit. Attempt B converted successfully but native Verilog mode
rejected residual sized casts around `$countones`. Attempt C used Yosys SV
mode, exposing sv2v's explicit sensitivity lists containing bare memory arrays,
which old Yosys rejects. The standard `--exclude=Always` option retains original
`always_comb`/`always_ff` semantics and avoids that sensitivity-list lowering.

The resulting stable converted component has SHA256
`f2d9fc81b19d3f8f268a28c2dcfca5bbc1fc3f706e5dce4100887b1be31ad98d`.
It flattens the original public unpacked-array ports in declared element order;
a verification-only wrapper must restore that exact contract for the unchanged
C++ checker. The [attempt-D conversion receipt](../../experiments/python-gamebub-v100/physical/v100-sv2v-converted-d/conversion.json)
retains commands, warnings and tool/input hashes. Current Yosys 0.33 then
rejects an internally generated `$shl` with signed RHS parameter in
`cu66_inverse_stream_v91j`. Its supported `read_verilog -noopt` option delays
the same internal-cell rejection until hierarchy checking; this is still a
failed full-component frontend attempt. Conversion itself is not behavioral
qualification or technology-mapping success.

The subsequent [paired full-component qualification](../../experiments/python-gamebub-v100/converted-rtl/verification.json)
passes both seeds 911501/911502. Each original/converted run passes 22 cases
and 21 directed checks, with byte-identical full transcripts, cycle counters,
378,996 event rows and actual canonical-memory bytes for each same-seed pair.
Both RGB replays pass 12 cases and eight directed checks. The public-port audit
covers all 308 names, declared order, directions and total bit widths. These
are bounded behavioral checks, not formal equivalence or mapped-netlist tests.

Installed primary `/usr/share/yosys/simlib.v` declares but never uses
`B_SIGNED` in `$shl`, `$shr`, `$sshl` and `$sshr`; those models always treat the
B port as unsigned, and only `A_SIGNED` controls left-operand extension.
A version-specific compatibility flow therefore normalizes `B_SIGNED` from
one to zero on exactly those four cell types. It applies at most two stages,
immediately after optimized reading and after hierarchy derivation. The
[independent delta auditor](../../fpga/experiments/cu66-v100-baseline/audit_shift_ir.py)
compares complete before/after RTLIL dumps and rejects any other byte change.
No source or converted-Verilog edits occur. Each selected cold elaboration
changes exactly two mask cells at stage 1 and two data cells at stage 2, all
`$shl` in `cu66_inverse_stream_v91j`; widths, `A_SIGNED`, connections and every
other IR byte remain identical across each normalization stage. There are no
further compatibility passes during synthesis. The earlier `-noopt` full
process characterization timed out after 120 s and remains a failed attempt.

Selected final [A conversion](../../experiments/python-gamebub-v100/physical/v100-sv2v-baseline-a/conversion.json)
and [B conversion](../../experiments/python-gamebub-v100/physical/v100-sv2v-baseline-b/conversion.json)
pin the same behavior-qualified generated Verilog, all converter/Yosys/ABC/
simlib/library hashes and both complete IR delta audits. The
[logical premap memory ledger](../../experiments/python-gamebub-v100/physical/v100-sv2v-baseline-a/reports/premap-memory-ledger.json)
contains 32 frontend arrays totaling 818,108 bits; this is a declaration
inventory before primitive inference and excludes arrays already replaced by
registers, which remain visible in frontend warnings. Technology mapping reads
that validated elaborated IR with standard `synth_xilinx -family xc7 -noiopad
-noclkbuf`, one process and a 2.5-GiB address limit. Exact-part physical gates
remain blocked regardless of this diagnostic's result.

The first complete-component generic synthesis attempt
[failed after 361.85 s](../../experiments/python-gamebub-v100/physical/v100-sv2v-baseline-a/mapping-diagnosis.json)
in `proc_dlatch`: old Yosys treats converted block-local loop iterator
`packed_scratch_v91g2.sv2v_autoblock_3.b` as an inferred latch in retained
`always_comb`. The original construct is the conditional loop at
`packed_scratch_v91g2.sv:231`; generated source is at line 1448. No additional
source, process-attribute or IR rewrite suppresses that failure. It occurs
before DSP inference and complete primitive mapping, so full-component LUT,
FF, DSP, BRAM and SRL counts and a mapped netlist are **unavailable**. The second
cold directory repeats conversion, normalization and full hierarchy only;
complete synthesis was not repeated after this known failure.

Serial arithmetic-leaf experiments preserve the same behavior-qualified
converted source, all original public ports and native deferred Yosys reads,
with **no shift-IR normalization**. The initial small concurrent IDCT run
hit its 180-s timeout; the initial dequantization run reached fine mapping
but exhausted its 512000-KiB address cap. Two subsequent sole-job dequant
attempts also fail with `std::bad_alloc` under the 2.5-GiB cap. These outcomes
do not establish zero resource counts or completed technology maps. A shared
physical lock, host/PSI gate, below-2-GB launch cgroup gate and 3.5-GB leaf
termination threshold protect the existing 4-GiB build container.

The standard `synth_xilinx -run` end label is exclusive. An early attempted
`begin:map_dsp` checkpoint therefore stops **before** DSP inference; its
generic `$mul` cells are not DSP primitives. Those two diagnostic checkpoints
are explicitly superseded and excluded from primitive claims. Correct
post-DSP captures use `begin:coarse`, with `coarse:` as the matching continuation
when a complete leaf map is attempted. No further resource, tool, timeout or
compatibility expansion is part of this baseline.

The final corrected
[dequantization post-DSP pair](../../experiments/python-gamebub-v100/physical/dequant-dsp-repeatability.json)
passes complete-checkpoint raw and canonical netlist equality, source/tool/
library/recipe fingerprints and all 14 public ports. Both actual DSP-stage
checkpoints contain **15 DSP48E1** cells with `AREG=BREG=MREG=PREG=0`.
The single correct
[IDCT checkpoint](../../experiments/python-gamebub-v100/physical/v100-solo-idct-b/leaf-receipt.json)
preserves all 13 public ports and contains **21 DSP48E1** cells: eight product
lanes have `MREG=1` with `AREG=BREG=PREG=0`; 13 index/address-expression cells
have all four register parameters zero. Its full continuation exhausts the
2.5-GiB address limit in fine mapping after 252.67 s. IDCT repeatability is
**not established** because only one correct checkpoint is retained.

These are actual intermediate DSP objects with pinned parameters and bit
connections. Generic cells remain at this stage, and later optimization can
change counts; **15/21 are not final resource budgets**. No complete arithmetic
leaf LUT/FF/BRAM/SRL map or physical clock is claimed. Complete component
primitive mapping remains failed. All jobs have stopped; no further variants
or resource escalation were run.

## Reproduce and resume

From the repository root, verify before preparing a never-used directory:

```bash
python3 scripts/cu66-v100/physical.py --verify
python3 scripts/cu66-v100/physical.py --prepare /home/lori/gamebub-build/cu66-v69/v100-new-a
python3 scripts/cu66-v100/physical.py --run /home/lori/gamebub-build/cu66-v69/v100-new-a \
  --container gamebub-cu66-v69-vivado --vivado /opt/Xilinx/2025.2/Vivado/bin/vivado
```

Run a second newly prepared directory and use `--compare DIR_A DIR_B` after
both finish. The `--yosys DIR --container gamebub-cu66-v69-build` alternative
reproduces only the direct diagnostic described above. `--collect DIR` imports
compact reports and hash receipts, leaving logs, snapshots, binary/netlist and
checkpoint outputs outside Git. The supplied container mapping is the existing
host `/home/lori/gamebub-build/cu66-v69` mounted as `/build`.

Each launch requires at least 8 GiB host available memory and memory full-PSI
avg10 below 1.0. A shared lock permits one physical/mapping job; Yosys has a
2.5-GiB address-space cap, one job, 600-s leaf timeouts and no parallel leaves.
Do not overlap it with another large compile in the shared 4-GiB build
container. The selected runs record passing gates and completed commands.

Resume the exact flow after Artix-7 support is installed in working 2025.2, or
the separate installation's startup is repaired, and an actual
`get_parts xc7a100tcsg324-1` query returns exactly one result. Use
fresh directories, retain both actual route attempts and review unconstrained
ports and all DRC/methodology findings. Then integrate the actual missing
whole-top endpoints and board constraints; component evidence cannot discharge
the V100 complete-candidate, V109 closure or V110 hardware gates.
