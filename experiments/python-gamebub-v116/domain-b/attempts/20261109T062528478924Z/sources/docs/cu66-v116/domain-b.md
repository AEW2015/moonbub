# V116B domain flag from the held coefficient tuple

Status: prepared, not yet RTL qualified. No compile or simulation was launched
by this worker. The source is isolated under fpga/experiments/cu66-v116b-domain.
The frozen selected source is cu66-v107-meta-flags/cu66_coefficient_elastic.sv,
SHA256 ea53b408aab5e522dfb2c4ffc2eefee41d58af37032cedc409e74815ab35dab9.

The actual V116 100 MHz routed report from native-study/native/
20261109T055009881384Z has WNS -0.108 ns and two failing setup endpoints.
Its worst path starts at scratch tile_pending_index[2] and ends at
coefficient_boundary/tuple_checks[0]/D: 10 logic levels, 10.056 ns data delay,
including 7.829 ns routing. Bit zero is the DOMAIN predicate. The path crosses
the forwarded tile payload selection and coefficient_value before computing
the predicate; it is not the quant-cell metadata flag. The other reported
failure is an ingress request-address endpoint. This candidate makes no claim
to fix that path, route setup, or achieve an operating clock.

The original edge captures the 130-bit payload and both check bits together on
in_valid && in_ready. Reset/start/cancel revoke eligibility but hold payload and
flags. The new source keeps tuple_checks[1] as the exact registered metadata
predicate and drives tuple_checks[0] from the already-held out_qscale/out_value:

```
out_qscale==3 || !(out_value[15:11]==5'd0 ||
                  out_value[15:11]==5'b11111 || out_value==16'h0800)
```

The expression retains all 16 bits and the +2048 exception. It accepts signed
values -2048 through +2048 for scales zero through two, and rejects every value
for scale three. No comparison is narrowed or removed. The public flag is
available on the same original capture edge; existing inverse acceptance and
registered validation remain untouched. There are no new cycles or timing
exceptions. This removes the input-side domain predicate FF endpoint while
placing a short predicate after an existing held tuple. Physical improvement
still requires a fresh actual route.

Every original nonsynthesis assertion block is retained text-exact, including
$stable(tuple_checks) and the consumed-token metadata/domain checks. A separate
nonsynthesis shadow captures the literal frozen input predicate on the exact
old payload write edge. Its seen certificate starts false and persists across
all warm reset/start/cancel events. Once initialized, it asserts equality with
the public derived flag even when invalid or killed. The shadow is excluded
from synthesis. Original unowned four-state initialization before the first
accepted tuple remains unspecified; the selected Verilator proof compares all
public two-state values from its first evaluation, without skipped intervals.

The reversible production recipe changes only the domain assignment, the
registered metadata bit write and the added shadow block. Main-module adapters
rename complete bodies only. meta_stage_probe compares every production output
on both clock edges, including full raw held payload, ready/valid, done,
occupied and both check flags. It additionally compares the unchanged geometric
helper over offered inputs. Its C++ adapter checks mismatch on every eval call.

The exact frozen V107 stage C++ bench is compiled unchanged inside the new
driver. Its flag transitions, randomized metadata/tuple traffic, all original
frame lengths and fence schedules, stalls, simultaneous replacement,
reset/start/cancel combinations and no-reset retries all run. The new focused
suite adds every 65,536 signed-16 bit pattern at all four scales, with an
independent integer threshold oracle; it repeatedly covers all plane/tile helper
inputs and checks raw metadata/domain values outside valid. Directed threshold
values include 0x07ff, 0x0800, 0x0801, 0xf7ff, 0xf800, 0xf801, signed extrema,
zero and -1. There are 1,680 scale/value/owner-phase/warm-kill cases, including
foreign offered tuples, stalled final offers, drained invalid holds, done,
replacement-versus-kill priority and clean retry. All accepted tuple fields
remain independently checked.

Default seeds are 116851 and 116852. The old bench's optional 67,108,864-case
metadata Cartesian loop remains byte-exact and can also run with
--legacy-exhaustive. The new 262,144-case signed16/scale sweep always runs;
the optional flag does not disable any new proof check. The unchanged geometric
function and registered metadata predicate are also verified by source reversal
and text-exact old assertions, rather than claiming an unexecuted Cartesian
regression as a fresh result.

Preparation-only check:

```
python3 scripts/cu66-v116/domain-b/qualify.py
```

Root dispatch after granting a global heavy slot:

```
python3 scripts/cu66-v116/domain-b/qualify.py --run --root-grant ROOT_GRANTED_DOMAIN_SLOT
```

The runner uses the pinned Verilator 5.020 image, --assert -Wall, C++17
-O2 -Wall -Wextra -Werror and -j 1, with no warning suppression. O2 affects host
speed only. Containers have two CPUs, 8 GiB RAM, memory+swap fixed to 8 GiB,
network disabled and finite inner/host watchdogs. Launch requires available RAM
at least 8 GiB, PSI full avg10 below 1 and combined memory+swap use below 0.85.
Stop thresholds are available RAM below 4 GiB, combined use at least 0.9, or
PSI full avg10 at least 5 twice. Root controls the global maximum two heavy jobs.

Every attempt preserves exact sources, commands, logs, resource snapshots,
binary hashes, old/new verdicts and partial traces on failure. actual_RTL_run
is written true before invoking simulation. Raw receipts exclude their own
mutable hash from artifact_sha256. The selector is plain status/path/sha256 at
experiments/python-gamebub-v116/domain-b/results.json. No automatic combination,
commit, push, native run, physical hardware operation or achieved-clock claim
is part of this preparation.
