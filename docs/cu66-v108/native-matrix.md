# V108 bounded implementation matrix

The initial matrix freezes the eighteen-file V107 threshold decoder source set,
the fixed 10.000 ns comparison clock and `xc7a100tcsg324-1`. The selected source
already passed exact canonical pixels, events and cycles. This phase changes
implementation directives, not the decode function, packet cap or quality.

The [matrix manifest](../../experiments/python-gamebub-v108/native-matrix.json)
binds every source alias/origin/hash, the actual canonical qualification, the
original native input card and receipt, and the read-only synthesis checkpoint.
The parent synthesis used RuntimeOptimized with the clock loaded before synthesis.
Its checkpoint SHA-256 is
`d762de8acc382a9d3a2aaacca6e6b4f613b63e92881643d0b8cad65e80d32c0e`.
Reopening that checkpoint is not a new synthesis run.

| Trial | Placement | Pre-route physical optimization | Routing | Question |
| --- | --- | --- | --- | --- |
| m0 | Default | none | Default | Reopened-checkpoint control |
| m1 | Explore | none | Default | Can extra placement effort improve locality? |
| m2 | ExtraNetDelay_high | none | Default | Does pessimistic long-net/fanout estimation help? |
| m3 | AltSpreadLogic_high | none | Default | Does spreading reduce congestion? |
| m4 | Default | AggressiveFanoutOpt | Default | Does placement-aware replication improve critical control nets? |
| m5 | Default | none | AggressiveExplore | Does additional critical-route search help? |

All six use Default `opt_design`. Each varies one factor from m0. No post-route
physical optimization or undocumented seed is included. V107's post-route
AggressiveExplore crash remains separate evidence; this matrix does not retry it.

AMD 2026.1 [place_design](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/place_design),
[route_design](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/route_design)
and [phys_opt_design](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/phys_opt_design)
document these directives. The documented placement spelling is
`AltSpreadLogic_high`. `AlternateCLBRouting` is UltraScale-only and is excluded
from this Artix-7 study.

## Preparation and execution boundary

The [preparer](../../scripts/cu66-v108/native.py) snapshots source/recipes into a
fresh external build, validates the native report parser against the immutable
V107 route, and records a separate `PREPARED_NOT_RUN` preflight. Preparation does
not run Vivado. A launch requires root's matching policy, per-build heavy-slot
grant, and an independent audit binding the exact preflight, grant and policy.

The immutable dispatch is created exclusively before runner handoff. It is never
rewritten to record completion; completion has its own file. Each native receipt
copies that dispatch, exact sources/recipes, logs, resource samples, report hashes
and source/checkpoint before/after hashes. Parent DCP, installed tools and the
existing legitimate license are mounted read-only. No license contents are logged
and no host identity is replaced.

Per trial: 2 CPUs, 2 Vivado threads, 8 GiB RAM with no additional swap allowance,
2,400-second tool watchdog. Root allocates at most two heavy jobs globally.
Launch requires at least 8 GiB available RAM and full PSI average10 below 1;
owned jobs stop below 4 GiB or after two full PSI samples at least 5. Stale swap
occupancy alone does not block a build. Failures and timeouts remain recorded.

The flow inherits exactly one 10 ns clock from the checkpoint and checks its
name, period, waveform and part before optimization. A clean RTL repeat reads
the same XDC before RuntimeOptimized synthesis. No input/output delay is guessed;
no false/multicycle exception, clock relaxation, `HD.CLK_SRC` or pblock is added.

## Selection and clean repeat

Only a completed legal route with matching source/constraint provenance is
eligible. Internal component 100 MHz requires nonnegative setup/hold/pulse slack,
zero corresponding failing endpoints, no unclocked/unconstrained internal or
loop endpoints, complete routing and zero routing errors. Negative setup remains
a failure even when it is the best measured frontier.

The selected strategy is then repeated from **fresh RTL synthesis**, using the
seventeen exact RTL bodies and include header, RuntimeOptimized synthesis and
the selected implementation directives. The separate
[clean-repeat preparer](../../scripts/cu66-v108/native_clean.py) preserves the
exact original V107 RTL read order and include-directory order from the retained
parent `inputs.tcl` (SHA-256
`f8c35c66119ebd1be349a5c64af24a46af965e9a4ebfe6d2326f5d0284e5611c`).
The checkpoint matrix preparer remains frozen; its unused sorted RTL list is not
used for the clean repeat. This repeat must not reuse a placed or routed
checkpoint. One successful exploratory route does not prove robustness.

Full board I/O/parent-clock integration, sustained hardware 30 fps, and complete
validated decoding below 10 ms remain separate gates. Checkpoints/binaries stay
at their recorded external paths; portable evidence retains their hashes.
