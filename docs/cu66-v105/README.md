# V105: admission coordinates and memory locality

This partial implementation checkpoint preserves 720×480 video, the
49,152-byte CS88 packet cap and the tested public cycle schedule. It changes
representation and storage inference; it does not change the codec, quality
or measured network bitrate.

The admission candidate replaces repeated active-cell division/modulo with a
reachable-state coordinate cache. Full 32-bit tile/group counters and existing
validation remain. Successful header entry initializes the cache; reset,
replacement start and abort invalidate it. Assertions compare live coordinates
with the original integer function. [Admission evidence](admission-results.md)
covers 86 retained/mutated packet cases, 22 directed
checks and 6,376,122 clock edges, including dead-cache perturbation
and independent active-cell replay. These are not independent raw gameplay
captures or an arbitrary-state formal equivalence proof.

The memory candidate consolidates five guarded mode writes into a single
synchronous write port and retains the original registered, held lookup.
[Memory evidence](memory-results.md) covers 316,440 explicitly
prepared cases and 316,442 edges, all 8,100 valid addresses,
write branches, suppression and output holds. Invalid lookup addresses remain
undefined; physical mapped-netlist collision behavior is not qualified.

Both edit recipes recover their standalone source exactly and produce the
same composed bytes in either order. The module interface is byte-identical.
The eight integrated lanes pass **512 case/profile runs and 576 directed
checks** at seeds 105401/105402, comparing the selected V102 baseline with each
candidate. Transcripts, events, cycle counters and canonical bytes where
applicable are identical. Counts include both implementations, seeds, profiles
and expected rejects; they are not displayed frames or hardware FPS.
Fresh V91j lanes exercise admission, coefficient and inverse-transform stages;
canonical V91k lanes also include reconstruction.

The [native comparison](vendor-comparison.md) measures all five variants.
The selected next-study source is **geometry**.
For parent integration, apply `source_overrides` from the
[selection manifest](../../experiments/python-gamebub-v105/selection.json)
to the frozen source list, compiling exactly one production file per module.
The focused probe adapters belong in verification source sets. Requalify the
parent memory/clock/ownership contracts when integrating these component files.
[Machine-readable summary](../../experiments/python-gamebub-v105/summary.json),
[independent source audit](../../experiments/python-gamebub-v105/source-audit.json)
and [baseline audit](baseline-audit.md) retain the exact pins and limitations.
The source audit passes 24/24 checks on two deterministic runs.
Failed bootstrap, compile or resource-gated attempts remain in their ledgers.

Reproduce the source composition and functional matrix from this checkout:

```sh
python3 scripts/cu66-v105/compose.py
python3 scripts/cu66-v105/run_matrix.py
python3 scripts/cu66-v105/audit_sources.py
```

The matrix needs the existing `gamebub-cu66-v69-build` container (Verilator
5.020 and GCC 13.3) with this repository and external `/build` mount visible.
It uses assertions, strict warnings, two compilation jobs, finite timeouts,
available-RAM and memory-pressure gates. Host-side docker-exec timeouts are
retained from the prior runner; a timeout requires checking for an orphaned
container process before retrying. No test timed out in the selected receipts.

Native builds require the existing Vivado/Artix installation and legitimate
license. Run at most two heavy jobs; each native job is capped at 8 GiB and
two CPUs. Do not overlap this five-build sequence with the functional matrix
unless the shared resource policy permits it.

```sh
python3 scripts/cu66-v105/build.py --variant admission --synth-only --run
python3 scripts/cu66-v105/build.py --variant memory --synth-only --run
python3 scripts/cu66-v105/build.py --variant geometry --run
python3 scripts/cu66-v105/build.py --variant combined --run
python3 scripts/cu66-v105/build.py --variant locality --run
python3 scripts/cu66-v105/audit_native.py
python3 scripts/cu66-v105/analyze_paths.py
python3 scripts/cu66-v105/methodology.py --write-external
python3 scripts/cu66-v105/summarize.py
python3 scripts/cu66-v105/render.py
python3 scripts/cu66-v105/bundle_manifest.py --verify
```

Hardware remains on a different system. Whole-device external-memory service,
parent clock/I/O/CDC signoff, complete custom-path integration, sustained
hardware 30 fps and validated complete FPGA decoding below 10 ms remain open.
V106 should use the measured path/fanout/congestion evidence to choose the next
isolated change, while retaining the verified building blocks and exact source
selection from this checkpoint.
