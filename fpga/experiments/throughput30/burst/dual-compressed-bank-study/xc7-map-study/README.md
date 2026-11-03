# Exploratory 7-series mapping of compressed-frame storage

The current experimental two-bank wrapper's RAM inference has **not** been
established in Vivado on the target. In this isolated study Yosys 0.33's
`synth_xilinx -family xc7` fails to map its forced-block-RAM read port with
`no valid mapping found for memory two_bank_storage.compressed0`. This is a
tool-specific result: it does not show that Vivado will fail to infer the RAM.

`make_candidate.py` creates a separate, non-production variant. Each bank has
its own unreset synchronous read-data register; reset clears the external
valid/selection state, and a mux selects the last-read bank. It retains the
one-cycle accepted-read response and holds the previous data between reads.
Under the same Yosys xc7 flow, the candidate wrapper maps to **24 RAMB36E1**
cells. `single_bank_extract.sv` separately preserves the original production
compressed array and its read/write block, exposing the controls as inputs; it
maps to **64 RAMB36E1**. The wrapper confirms the extracted block matches the
current original source exactly. Both are standalone top modules; the candidate
also includes experimental ownership/control logic, and the baseline extract
does not. The counts are not complete-design estimates and must not be
subtracted directly from the retained Vivado routed BRAM utilization.

The original and candidate wrappers ran in lockstep for **204,890 clock
cycles** during the existing directed storage workload, comparing all external
outputs every cycle after the same reset. The workload checks 51,715 reads,
1,024 simultaneous read/receive cycles on different banks, reset, CRC rejection,
abort, 48 KiB boundaries and shorter-bank reuse. A local mutant which inverts
one bank's read data fails the lockstep comparison at cycle 5,142. These are
bounded directed, two-state Verilator checks; they do not prove equivalence for
all input sequences, uninitialized state or physical RAM collision behavior.

The local Vivado 2025.2 installation returned no installed `xc7a*` parts and
does not recognize the target `xc7a100tcsg324-1`. Therefore there is no target
Vivado synthesis, BRAM packing, placement, routing, slack or bitstream result in
this study. The old routed baseline had only 14.5 arithmetic BRAM-tile
equivalents free and very small positive timing slack; see
[`../baseline-resource-audit/`](../baseline-resource-audit/README.md). Changes
in memory packing, new buffering, clock-domain logic, port widths, placement and
routing mean neither our inferred primitive counts nor simple arithmetic prove
the redesigned pipeline fits or meets timing.

To reproduce the storage study with Verilator 5.x, Yosys with `synth_xilinx`, a
C++ compiler and Python 3, set `BUILD_DIR` to a new empty scratch directory and
run `./run.sh`. It checks pinned source hashes, generates the candidate and
lockstep bench, runs normal and expected-failure mutant simulations, maps the
original wrapper, candidate and baseline extract, and writes JSON/logs to the
scratch directory. The observed independent run used Verilator 5.020 and Yosys
0.33. The full output is `/home/lori/gamebub-tools/xc7-map-independent-v3/`;
compact logs and mapping counts are retained in `results/`. Other Yosys
versions may map the original differently or produce different cell counts.

`./run-cadence.sh` exercises the generated candidate in the existing ten-frame
QSPI/JPEG/display behavioral test; set `BUILD_DIR` and `FIXTURE_DIR` to separate
scratch and pinned fixture paths. The run at
`/home/lori/gamebub-tools/xc7-map-cadence-v1/run/` admitted and presented all ten
synthetic frames, checked all pixels against the related C decoder, and completed
21 modeled display scans with no reported underruns or overflow. All ten
framebuffer dump SHA-256 values and 41 arrival/admission/decode/presentation
records match the prior original-wrapper run. `results/cadence-compare.json`
retains the hashes and `results/cadence-run.log` retains the run. This is a
digital simulation, not a complete physical-timing or 30 fps proof.
Recompute the identity check with `python3 compare_cadence.py ORIGINAL_RUN
CANDIDATE_RUN` using two complete run directories containing `run.log` and
`dumps/`. The script compares pixel-dump hashes and event records; the prior
standalone run is `/home/lori/gamebub-tools/bank-qspi-cadence10-v4/`.
