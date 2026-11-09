# IV114.1: reserved command admission and registered peer kill

The focused actual-full-top proof is **PASS** for seeds 114101 and 114102.
The sole changed RTL body is
`fpga/experiments/cu66-v114-control/cs88_pipeline_v91k.sv`, frozen at SHA-256
`9e6d2b88ad0f06ca0df5a5218be0d78a9fa9d9e8151d3b0b43aebaafc3ba76bd`.
Its ports and the four child instance names are unchanged. It composes with the
other 17 frozen V113 sources; all earlier sources/checkers remain unchanged.
Full canonical/transport qualification and fresh native timing remain separate
required gates. This is not a clock-closure result.

| Edge/boundary | IV114.1 behavior |
| --- | --- |
| Idle reservation | A registered admission credit is issued only with producer/child/cache quiescence, empty coefficient boundary, inverse/reconstruction emptiness, no reference pending, no scratch outstanding and no refill queued/pending/active byte. |
| Public acceptance E | `command_accept = start && start_ready` consumes the held credit and snapshots packet size, epoch, accepted reference/Qcache validity and reference FID/generation, plus `serial_clear`, `write_overlap`, `read_prefetch`, `tile_overlap`. |
| Pending interval | Command fields remain stable. Public old done/error/cache-complete and all input/coefficient/residual/pixel/request transfers are masked. No second command fits. |
| Child delivery E+1 | Internal `accepted_start` is the actual child start/reset event. Every child receives the captured command, with no later dependence on those live external pins. This name retains its meaning for the original elastic oracle. |
| Cancellation before delivery | Reset/abort prevents the E+1 delivery and retires the queued command once. Admission sequence still advances on a publicly accepted command. |

The credit represents a reservation: while held, resource allocation can occur
only through that command acceptance or a cache beat with `!start`. A first
accepted cache beat consumes the frame credit and holds preload ownership.
Partial preload blocks start; a blocked start cannot reset or consume a cache
beat. An accepted last beat, or beat 1349 as in the original producer, atomically
returns the reserved frame credit. Invalid preload closure still preserves the
producer's original eligibility/error behavior. Start wins over coincident
cache when a frame credit exists. Cache abort may promptly return credit only
when the command/cache reservation certifies all other resources remained idle;
a live delivered frame's physical drains cannot use that shortcut.

Logical cache consumption is visible at public E (`cache_complete` becomes
ineligible), while the reserved actual producer cache is consumed at delivery
E+1. This preserves the original bench's immediate read-after-admission check
without permitting a hidden cache transfer. `blocked_starts` now counts public
blocked start offers rather than the child's later reserved delivery. Other
leaf diagnostics/counters reset at child delivery; during pending they still
describe the prior, ineligible child interval and must not be control oracles. A versioned API harness must advance the one delivery edge before arming new-frame leaf-diagnostic conservation checks; command-pin poisoning must remain before that edge. Every original accepted-event/value/physical-drain assertion remains active.

The first current-owner terminal cause is retained, with simultaneous priority
reconstruction, inverse, coefficient and unchanged reason encodings. Current
raw faults immediately suppress public transfers, then the retained cause keeps
the boundary revoked through local cleanup. Both valid and the ready returned
to the corresponding producer are masked for pixel, memory request, reference
request, coefficient and residual channels. Scratch/reference response valid,
ready, tags and payload remain forwarded so accepted physical requests retire
only on actual matching completion.

An inverse/reconstruction peer fault crosses a tagged local kill register
before reaching the producer's broad abort network. Coefficient self-failure
uses its existing local failure/drain path; it does not self-abort and erase
its provisional counters. External abort remains direct into the existing
producer, preserving its private replay cancellation edge. A private producer
operation can remain active during the bounded peer-kill delivery interval;
its externally visible requests cannot handshake behind the mask. Private
replay/debug traffic remains observable as the actual traffic, rather than
being hidden. This changes local cleanup timing and does not assert every old
private diagnostic cycle is identical.

`owner_open` prevents stage errors from a retired interval from killing a new
command. A pending command ignores old sticky child faults; delivery clears
those child statuses together. A local kill carries the admission sequence and
cannot apply to another sequence. Readiness stays low until genuine scratch
and reference debt drains. Admission sequence exhaustion blocks further credit;
the focused test uses a declared prepared wrap frontier, not 2^32 transactions.
Warm reset clears local commands/reservations and retains the unchanged leaf
physical-drain behavior. External channels still expose their legacy tags;
top-only sequence registers cannot distinguish aliased same-tag late duplicates.
A drained/quiescent external session condition remains required before reset
can reuse such identities. Full PCTL1 generation/session integration is not
implemented here.

Reproduce the reversible recipe and focused proof with:

```sh
python3 scripts/cu66-v114/control/prepare.py
python3 scripts/cu66-v114/control/qualify.py --run
```

The selected raw result is
`experiments/python-gamebub-v114/control/attempts/20261108T224203237983Z/results.json`,
with the hash-pinned summary `control/results.json`. Each seed passes 78
control checks and four real accepted scratch/reference abort/reset drain
checks. The control checks cover all 64 command flag combinations with all
live command pins poisoned after public acceptance, exact E+1 delivery and
accept/deliver/cancel conservation, held start, cache/start collision and partial
preload abort, seven explicitly declared prepared child-fault priority fixtures,
stale tagged kill and wrap guarding. Across the focused controls, 77 public
commands comprise 75 deliveries and two explicit cancellations. The physical
tests reuse every relevant check from the untouched 496-line bench on actual
RTL and immutable coefficient/residual/canonical fixtures.

The run uses the established Verilator image, assertions, fatal `-Wall`, C++
`-Werror`, one compiler worker, two CPUs and 8 GiB memory with the same swap
limit, finite watchdogs and host memory/PSI gates. No assertion was removed or
downgraded. No native/hardware job was run by this work. The remaining timing
risk is an immediate fault mask through returned producer ready/input paths;
registered command/kill delivery alone does not prove all such cones meet the
clock. Any subsequent owned-byte/skid cut or restricted scheduling profile
needs its own explicit contract and qualification.
