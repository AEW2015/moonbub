# Same-cycle transport nonzero precompute

This isolated successor replaces the high-fanout fault reduction of the
registered binary lost-word count with a registered Gray nonzero predicate.
The new flag samples `|transport_gray_sync` on exactly the edge/reset branch
that samples `ungray_transport(transport_gray_sync)` into the original counter.
Only the second synchronizer stage is used. The quarantine expression still
uses the existing second-stage quarantine value. No clock, CDC synchronizer,
reset sequence, port, on-wire protocol, exception, FIFO or added cycle changes.

`PATCH.diff` and `derivation.json` bind exactly four reversible edits to the
actual v005-selected top: declaration/init (with MAX_FANOUT64), reset assignment,
same-edge update and fault expression. The original counter declaration/update
remain. It had no external statistics readback in the selected top, so retaining
its RTL does not force physical counter retention: synthesis may prune it now
that it has no fault consumer. No KEEP/DONT_TOUCH or new statistics port is added.
The parent reference is a snapshot, **not a source to compile alongside the top**.

Executed proof in `evidence/verification01`:

- Exhaustive SAT identity for all 32-bit two-state Gray values, using the actual
  extracted `ungray_transport` function.
- Temporal induction proves the strengthened full-state relation from the
  explicit zero initial states: meta/sync/count/quarantine histories, flag/count
  relation and fault output. Induction length 1 succeeds for arbitrary inputs
  and synchronous reset/quarantine histories.
- Simulation runs 50,253 core edges, including 50,000 randomized cycles and 190
  reset edges. Directed checks cover third-edge assertion/clear, nonsticky
  zero recovery, one-hot/complement/wrap cases, and quarantine shifting through
  transport reset exactly as before.

This is **not four-state-X equivalence**. A directed `gray=000x0001` example with
quarantine zero produces old fault X versus new fault 1: prefix-XOR pessimism
and reduction-OR differ. Both results and this scope limit are retained. The
proof does not model analog metastability, establish MTBF, or certify physical
CDC/skew/timing. MAX_FANOUT64 is only an implementation hint; no replication or
fanout result has been measured. No large Vivado job, BIT or hardware operation
was performed. Whole-board selection/implementation remains a root review gate.
