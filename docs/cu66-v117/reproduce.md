# V117 reproduction and evidence scope

Run from the moonbub study repository. The frozen master execution policy is
`experiments/python-gamebub-v117/study-policy.json`; its SHA-256 is
`77419a3c09b0020b963f6059a36ae4dcacb796e164bafa759672b705ac13a692`.
Read it before dispatch. Root owns the two global heavy slots; each job uses
2 CPUs, 8 GiB RAM, no additional swap and one compiler job. The memory/PSI gates
remain active even when the host has spare RAM. A failed timing measurement is
not eligible for an unchanged-source repeat.

## Functional proofs

The focused suites are independently executable after their source contracts
are verified. Run them serially unless Root explicitly grants another slot:

```sh
python3 scripts/cu66-v117/ac/qualify.py --run --suite all
python3 scripts/cu66-v117/throughput/qualify_inverse.py --run --root-grant ROOT_GRANTED_V117_INVERSE
python3 scripts/cu66-v117/throughput/qualify_reconstruct.py --run --root-grant ROOT_GRANTED_V117_RECON_LOCAL_COPY
```

Integrated composition A retains public cycles. Composition B deliberately
changes scheduling, retaining exact values, ordering, held transfers, physical
response debt, cancellation, first-fault priority and canonical reconstruction:

```sh
python3 scripts/cu66-v117/spatial_a.py --run
python3 scripts/cu66-v117/peer_a.py --run
python3 scripts/cu66-v117/live_a/qualify.py --run --root-grant ROOT_GRANTED_V117_A_LIVE
python3 scripts/cu66-v117/spatial_b.py --run
python3 scripts/cu66-v117/peer_b.py --run
python3 scripts/cu66-v117/live_b/qualify.py --run --root-grant ROOT_GRANTED_V117_B_LIVE
```

The default integrated runner uses one seed at a time. Its optional pair-grant
file requires a source-bound completed peer proof and exclusive ownership of
both heavy slots. It is never a way to exceed the global two-job limit.

A frozen single-owner test fixture originally assumed that the first residual
stall must last seven more cycles. The two-owner candidate can legitimately
resume filling its second slot. The new reversible harness derivation waits
for both actual owners to become READY while the head is held, then executes
all original seven held-transfer checks plus a both-READY check. The first
failed run is retained. The independent tick-by-tick held-transfer oracles
were not removed. Peer prepared-fault setup similarly accounts for the new
private stage/owner state and retains its original physical debt ledgers.

## Parent observation-boundary qualification

The original B parent run and its additive diagnostic replay both failed and
remain evidence. The trace showed one raw residual acceptance during the
existing one-edge registered producer-cancellation gap, with every external
grant already masked. The isolated guard changes only the exported residual
and replay-request observations. It does not block or conceal private work:
independent raw owner/golden and replay-response ledgers account for it, and
require no raw offers after registered or external cancellation. Every original
need/assertion remains active. See [the decision and limits](parent-guard.md).

```sh
python3 scripts/cu66-v117/live_guard_final/qualify_b.py --run --root-grant ROOT_GRANTED_V117_B_LIVE_GUARD
python3 scripts/cu66-v117/live_guard_final/qualify_c.py --run --root-grant ROOT_GRANTED_V117_C_LIVE_GUARD
```

These fresh guarded-parent proofs have distinct selectors under `live-guard`;
they cannot turn the original failed B wrapper into a pass. The parent wrapper
has no routed full-system clock qualification. Composition C additionally
requires its source-bound ingress focus, full/transport and peer proofs:

```sh
python3 scripts/cu66-v117/ingress/qualify.py --run --suite all --root-grant ROOT_GRANTED_INGRESS_FOCUS
python3 scripts/cu66-v117/ingress_bytecount/qualify.py --run --suite all --root-grant ROOT_GRANTED_INGRESS_BYTECOUNT_FOCUS
python3 scripts/cu66-v117/reconstruct_wordbank/qualify.py --run --root-grant ROOT_GRANTED_V117_RECONSTRUCT_WORDBANK
python3 scripts/cu66-v117/spatial_c.py --run
python3 scripts/cu66-v117/peer_c.py --run
```

## Routed timing

Use `native.py --composition read` for A, `native_throughput.py` for B and
`native_repair.py` for the optional actual-cause repair C. Each performs a
read-only prepare, then requires an independent preflight audit of that exact
card before dispatch:

```sh
python3 scripts/cu66-v117/native_throughput.py --trial integrated-125
python3 scripts/cu66-v117/native_throughput.py --run --preflight PATH_TO_CARD --audit PATH_TO_PASS_AUDIT
```

Preparation verifies selected full, transport, peer and focused receipts,
current source hashes, canonical bytes, lossless compilation fragments, old
harness derivations and fixed native budget. The pinned image uses Vivado
2026.1 for `xc7a100tcsg324-1`, default synthesis/opt/route, ExtraNetDelay_high
placement and the original 8 ns or 10 ns clock loaded before synthesis.
There are no added timing exceptions, I/O-delay guesses, retiming or fanout
attributes. Reproduction must retain real failed results and tool warnings.
License contents and private authentication data must not be published.

The reports include setup/hold/pulse, actual clocks, route status, methodology,
DRC, CDC, fanout, effective XDC and mapped primitive/control observations.
The decoder body is an out-of-context component. External I/O, integrated
memory/CDC/hash/display timing and actual ESP32 execution are separate gates.

## Parent latency and milestones

LIVE tests execute real clock edges, wrapper logic and memory service models.
They retain independent canonical/HUD bytes, ACK, owner, C2, SHA, physical debt,
retry and publication-fence checks. The B/C bench adds observed staged inverse
accepts and different-tile fill/emit overlaps without extra tick/RNG calls.
The baseline exact-cycle comparator remains in A; B/C explicitly compare
semantic results and report measured cycle changes under the new schedule.

At 125 MHz, strictly below 10 ms means fewer than 1,250,000 cycles from the
accepted final outer byte to validated commit. At 100 MHz the threshold is
1,000,000 cycles. These are conditional normalizations, not hardware latency.
A passing component route alone does not establish the full parent clock.
Sustained distinct-frame 30 fps and board-validated decoding below 10 ms
require separate hardware tests.

```sh
python3 scripts/cu66-v117/collect.py
```

The collector binds terminal receipts to current source hashes and keeps
hardware milestones separate from simulated cycles and component timing.
