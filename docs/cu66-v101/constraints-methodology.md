# V101 clock, reset and timing-obligation audit

**Source audit passed; timing signoff remains open.** This work implements
V101's constraints/methodology inventory and prepares an executable OOC flow.
It neither establishes routed timing nor closes the complete custom decoder's
30-fps or under-10-ms goals.

The [deterministic ledger](../../experiments/python-gamebub-v101/constraints/ledger.json)
pins 39 existing source/input files and the new recipe. Seven static checks
pass. Historical timing constraints and build flows are unchanged against
V100 commit `e8bb1c9cc3cec6775cf128c8fd538a56f022575f`; the ledger explicitly
records zero historical SCM timing edits.

## Source-backed findings

| Scope | Recorded result | Qualification |
| --- | --- | --- |
| OOC `cs88_pipeline_v91k` | 308 declared ports: 37 input, 271 output; nine unpacked output arrays retained | Names/order independently matched to the V100 inventory; widths and arrays are explicit in the ledger |
| Frozen source closure | 16 RTL files plus one include; 29 clocked source processes all use `posedge clk` | Includes source assertions; this is neither a synthesized register count nor proof that an external controller obeys this clock |
| Component clock | One 10-ns comparison clock; no generated clock primitives in this component | Proposed target, not achieved frequency; all 307 non-clock public ports still need integration timing contracts |
| Existing JPEG/MSV1 board image | One 50-MHz primary, four PLL/MMCM-derived internal clocks and two forwarded output clocks | Seven named clock roles, not seven independent oscillators; the custom CS88 component is not joined to that board top |
| Existing timing inputs | Five board pin XDCs, V100 component XDC, and two timing Tcl files | Eight inventoried timing files; do not combine alternate historical constraint sets |
| Timing obligations | Ten explicitly open interface/clock/reset/CDC/physical obligations | Unknown min/max delays, board requirements and netlist checks remain open |

The source board PLL derives 200 MHz, 100 MHz and a 100-MHz receive clock
shifted 279 degrees/7.75 ns. The panel MMCM derives
`50 MHz × 56.375 / 3 / 32 = 29.3619791667 MHz`. Both clock generators use the
same primary oscillator. The audit adds no asynchronous clock group between
them. A crossing protocol and appropriate physical timing bounds still need
review even for clocks with a common primary source.

`mcu_spi_clk` is sampled by the endpoint's `clk200` synchronizer and edge
detector; it is not a fabric clock in the inspected RTL. Its input sampling
aperture, read-output delays and bidirectional output-enable turnaround need
the actual ESP32/PCB contract. The source's digital-tested write/read rates
do not supply those electrical timing requirements.

The board source has separate four-stage reset-release chains in the 200-MHz,
100-MHz and pixel domains: PLL/MMCM loss of lock asserts them asynchronously,
then release advances on the receiving clock. The phased SDRAM input-capture
and negative-edge retime registers have no explicit reset; the controller
consumer gates their use. The OOC custom component provides no asynchronous
input synchronizer: reset, start, abort and response/control signals require
a synchronous integration boundary and intact cancellation/ownership drain.

## Historical constraints now included in the audit

The earlier XDC-only inventory omitted
[`timing.tcl`](../../fpga/scripts/timing.tcl) and
[`timing-reviewed.tcl`](../../fpga/scripts/timing-reviewed.tcl). The ledger
now records their exact command text and line numbers, source hashes and build
hooks. `build.tcl` uses the exploratory timing source;
`build_final.tcl` and `resume_impl.tcl` use the reviewed source. The separate
`close_timing.tcl` inherits constraints from an exact historical routed
checkpoint, rather than importing a new XDC. Its presence does not make that
checkpoint a current custom-codec implementation.

The reviewed source contains forwarded clocks, guarded identical-D1/D2 ODDR
falling-edge exclusions, a phased previous-beat SDRAM setup multicycle with
strong hold, first-stage token exceptions, Gray max-delay/bus-skew bounds and
held mailbox-payload bounds. It also labels the external SDRAM/PCB numbers as
**provisional**. The recorded SDRAM output `max=2.0/min=-1.3 ns`, SDRAM input
`max=7.0/min=2.0 ns` and LCD output `max=2.0/min=-1.0 ns` are historical
assumptions, not newly measured requirements or accepted constraints for a
different board/controller. No such delays or exceptions are imported into
the new OOC flow. Object guards and a source comment do not substitute for
checking a new netlist and the actual memory/panel timing at operating corners.

## Prepared executable flow

The new [component XDC](../../fpga/experiments/cu66-v101-constraints/component.xdc)
retains the same comparison clock as V100. Its [run recipe](../../fpga/experiments/cu66-v101-constraints/run.tcl)
loads that XDC **before** `synth_design`, so the constraint is a synthesis
input as well as an implementation input. V100 loaded its clock after
synthesis. This recipe correction is not a measured timing/resource gain and
is not a matched physical A/B result.

The XDC contains no invented input/output delays, false paths, multicycles,
asynchronous clock groups or waivers. Unqualified ports remain visible.
The [report recipe](../../fpga/experiments/cu66-v101-constraints/report.tcl)
requests native min/max paths, unconstrained timing, clocks/interactions,
check_timing, hierarchical utilization, methodology, DRC, CDC and exceptions
at synthesis, placement and routing. Version-specific methodology JSON has
an explicit availability receipt; a missing native required report fails the
flow. It writes checkpoints without creating a bitstream or programming a board.

From the repository root:

```sh
python3 scripts/cu66-v101/constraints.py
python3 scripts/cu66-v101/constraints.py --prepare /home/lori/gamebub-build/cu66-v69/v101-new-baseline
```

Use a never-created external directory. `--prepare` copies source/include and
recipe inputs, pins their hashes and prints the batch command; it launches no
Vivado build. `--scratch-override /path/to/candidate.sv` explicitly substitutes
only the scratch source after checking its public declaration, recording the
candidate hash separately. All other inputs must still match the frozen source
manifest. Candidate overrides never modify historical RTL or imply source
equivalence before the paired regressions run.

The existing Vivado container maps `/home/lori/gamebub-build/cu66-v69` as
`/build`; the prepared `inputs.tcl` uses those container paths. An equivalent
environment must preserve or regenerate that mapping. Apply the shared-host
available-RAM/PSI gate and heavy-job limits before manually starting a build.
The separate [2026.1 build runner](../../fpga/experiments/cu66-v101-constraints/run_vivado2026.py)
uses one owned container with an 8-GiB hard limit, two CPUs/two Vivado threads,
an 1800-second tool timeout and 30-second host/cgroup memory samples. It stops
only its own container if host available RAM falls below 4 GiB or full-memory
PSI avg10 stays at least 5 for two samples. Launch requires at least 8 GiB
available and full PSI avg10 below 1. Tools and an existing legitimate private
license are mounted read-only; that license file must remain outside Git.
The runner uses the real host network identity required by the existing
node-bound license and performs no HOSTID or MAC substitution.

The user supplied the reproduction path
`/home/lori/acorn-nexys4-ddr/cache/vivado.lic`. A private byte comparison found
it identical to the legitimate file used in the recorded successful run; no
license contents or fingerprint were recorded. The
[alias receipt](../../experiments/python-gamebub-v101/constraints/2026/provided-license-alias.json)
preserves that fact without rewriting executed commands. The now-redundant
private cache copy was removed after all owned containers exited; the original
and user-provided file were not changed. For future use, pass the user-provided
host path directly to the runner's `--license-file` option. It mounts the file
read-only and sets its container-local license environment explicitly.

For the user-provided container mapping, mount the same file read-only as
`/cache/vivado.lic` and explicitly run:

```sh
source /opt/amd-tools/2026.1/Vivado/settings64.sh
export XILINXD_LICENSE_FILE=/cache/vivado.lic
```

These are explicit setup commands, rather than an assumed default environment.
Keep the real host-network identity required by the existing binding. The
recorded runner used the exact vendor launcher and its own explicit license
mount/environment; no build or query was repeated merely to change that path
alias.

## Current tool evidence and methodology boundary

The [fresh read-only preflight](../../experiments/python-gamebub-v101/constraints/tool-preflight.json)
completed in Vivado 2025.2: exact target count **0**, Series-7 part count **0**,
504 other installed parts. Its immutable attempt retains the command, query
source and log hashes. That query started no synthesis or implementation.

The user then requested the newly installed 2026.1 and a fresh container.
The [selected 2026.1 runtime query](../../experiments/python-gamebub-v101/constraints/2026/results.json)
now succeeds: **Vivado 2026.1 build 6511674, exact target count 1, Series-7
part count 210 and 289 installed parts**. The existing tools are mounted
read-only into an isolated container from an already installed image. An
earlier minimal Ubuntu-24.04 image lacked `libX11`; an old-image wrapper path
was absent; fresh isolated-network attempts could not accept the node-bound
license. Those failed attempts remain separately classified. The existing
legitimate Vivado Basic license was accepted using its actual underlying host
network identity. No tool/license binary, license contents, host ID, MAC or
other project's files/container were modified. The installer/tool prerequisite
is restored; this query alone establishes no synthesized resources or timing.

The first real baseline launch stopped before synthesis because V100's
previously unexecuted `read_verilog -include_dirs/-define` flags are not valid
Vivado commands. The V101 retry sets `include_dirs` and `verilog_define` on
`current_fileset`, then calls `read_verilog -sv`, following the actual error
and [UG835's command syntax](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/read_verilog).
The failed prepared inputs are retained; the corrected retry uses a new
directory and does not rewrite historical V100 evidence.

The [terminal baseline selector](../../experiments/python-gamebub-v101/constraints/2026-build/results.json)
now records actual exact-target synthesis success followed by a placement
resource failure. The frozen original RTL synthesized successfully in about
355 seconds; the complete run stopped after 455.6 seconds. The source snapshots
are unchanged. No memory-pressure/timeout gate fired and no error was downgraded.

| Native post-synthesis resource | Used | Available | Utilization |
| --- | ---: | ---: | ---: |
| Slice LUTs | 74,340 | 63,400 | 117.26% |
| LUT as memory | 22,286 | 19,000 | 117.29% |
| Slice registers | 34,985 | 126,800 | 27.59% |
| Block RAM tiles | 16 | 135 | 11.85% |
| DSPs | 28 | 240 | 11.67% |

The [read-only checkpoint analysis](../../experiments/python-gamebub-v101/constraints/2026-build/analysis/20261107T205034716223Z/summary.json)
provides native capacity percentages and the exact 28-cell DSP/register ledger
without repeating synthesis or implementation. The hierarchy report attributes
44,040 LUTs to admission, including 19,956 memory LUTs. Those hierarchical
totals overlap their parents and must not be added together.

Three native `UTLZ-1` errors reject 22,286 memory LUTs against 19,000 compatible
sites, including 19,956 RAMD64E cells against 19,000 sites. The placer **did not
run** and routing **did not start**. Changing the resource-error severity would
not establish a legal placement and was not attempted. The next control
experiments must address memory read ports/latency/mapping before a routed
result is possible on this part.

Post-synthesis timing also fails the unchanged 10-ns target: WNS **−16.629 ns**,
TNS **−73,220.930 ns**, 8,776 failing setup endpoints. The first reported path
runs from `reconstruction/plane_reg[1]/C` to
`reconstruction/count_copy_tiles_reg[0]/CE`: 49 logic levels, including 32
CARRY4 levels, with 26.376-ns estimated data delay. Net names alone do not prove
the source-level cause. These are synthesis estimates, not routed delay, Fmax,
full-frame decoding time or achieved FPS. Keep the target and investigate the
actual control/predicate cone without dropping observable counters or checks.

The AMD methodology skill requires an actual synthesized design/run and
violation properties before resolving rule IDs. No current exact-target
candidate netlist had been available at the initial source audit. The selected
run now retains native methodology JSON/text, DRC, CDC, exceptions, clocks and
timing reports plus 2,451 extracted methodology findings. These are **reported
findings**, not a claim that every possible issue was enumerated. The reported
classes are SYNTH-5 378, SYNTH-6 8, TIMING-16 1,000, TIMING-18 1,000,
ULMTCS-2 1 and RTGT-1 64; none was declared resolved or waived.

`check_timing` reports zero no-clock/constant-clock register pins and zero
unconstrained internal endpoints, while 1,101 input bits and 12,885 output bits
have no I/O delay. The CDC report says all analyzed paths are safely timed, but
the tool explicitly skips ports without input delays. That single-clock OOC
report is not whole-board CDC signoff. There are no new rule waivers or guessed
board requirements. The
[methodology status report](../../fpga/experiments/cu66-v101-constraints/METHODOLOGY_RESOLUTION_REPORT.md)
and terminal build receipt distinguish available reports from signoff.

Run the prepared recipe twice from fresh directories and review the real
unconstrained paths, reset/crossing
objects, clock relationships, methodology and min/max paths. Actual board
identity, memory/panel/ESP32 min/max timing and the full custom-top joins are
required before V101 physical exit or the later hardware milestones can close.
