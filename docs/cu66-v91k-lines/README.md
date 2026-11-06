# Aligned 128-bit gathering behind the exact chroma cache

This experiment joins the frozen two-row RGB565 converter to a new bounded
memory adapter. Three 16-byte line slots retain separate Y, Cb and Cr tails,
so switching planes does not discard prefetched row-boundary bytes. Cache hits
return a registered byte; misses accept one aligned physical line request and
then return the selected byte after its matching response.

## Results and service assumptions

| Per 720×480 frame | Frozen byte cache | Gathered line adapter |
|---|---:|---:|
| Converter byte requests | 518,400 | 518,400 |
| External transactions | 518,400 byte responses | 32,400 × 128-bit responses |
| Priced x16 payload transfers | 518,400 | 259,200 |
| FAST complete conversion cycles | 2,938,320 | 2,743,921 |
| FAST first byte request → first RGB word | 4,328 cycles | 3,797 cycles |

The adapter adds **48 logical payload bytes** plus tags, byte response and
control registers. There are exactly 486,000 local line hits and 32,400 misses.
The physical read sequence covers every aligned canonical 16-byte line once:
21,600 Y, 5,400 Cb and 5,400 Cr. No padding, duplicate line fetch or extra frame
bytes are hidden in the transaction reduction. The RTL endpoint receives an
assembled 128-bit response; wiring an actual eight-word SDRAM gather/command
bridge is still required. Any physical gather-buffer storage and timing belong
to that future controller integration, beyond the 48-byte local line slots. Each accepted returned byte is
checked against the actual immutable candidate memory before RGB comparison.

Game Bub has an [x16 SDRAM interface](https://docs.gamebub.net/developing-cores/reference-interfaces/).
The wider logical response is charged as **eight x16 data beats**, not one wide
physical bus transfer. FAST ACK is nine edges after line acceptance, versus
two for the byte control; SLOW is nine–thirteen versus two–six. Both use the
same one-edge response overhead plus optional zero–four extra stall edges.
Changed schedules consume randomness differently; absolute SLOW stall traces
are not identical. These are finite service assumptions, not command-accurate
SDRAM CAS/row/refresh or concurrent display measurements.

FAST uses about **6.62% fewer conversion cycles** beyond the frozen chroma
cache. Closing the adapter's frame lease is included in its completion fence.
The [summary](../../experiments/python-gamebub-v91k-lines/summary.json) retains
all case/profile fences and SLOW observations. There is no inferred physical
clock, measured frame rate or complete validated decoding latency.

## Ownership and verification

The inner byte request and outer line request have distinct owners. Reset or
abort can discard/acknowledge the inner byte while the outer read continues to
drain. A new frame cannot start until both owners retire. A wrong physical
response epoch fails closed and retains the genuine pending request; a matching
bus-error response retires that physical owner and fails the inner byte lease.
Slots are invalidated on start, cancellation or error, without bulk resetting
payload. Sticky faults issue a one-shot abort to the frozen byte consumer and
permit a later clean retry.

Both strict final seeds compare the unchanged byte-cache control and line path
on the six retained case identities under both profiles, plus a separate
nonuniform synthetic edge fixture. Each path checks **9,676,800 RGB565 words**
across the campaign. These include four related native source frames and
separately labeled synthetic data; repetitions are not new gameplay content.

The line path has 33 directed checks. They cover unaccepted physical offers,
pending Cb/Cr/luma line requests, later row eviction, registered local lookup,
held RGB output, inner last-fill ACK and outer physical ACK coincident with
reset/abort, wrong epochs, matching errors, invalid starts and retry. The
unchanged cache control retains its 29 checks. The independent auditor checks
both byte and aligned-line address/data hashes, all row-fill receipts, actual
output bytes, source snapshots, strict commands and failure evidence.

The first strict draft rejected unused high address bits. The adapter now
retains only the required offset and aligned address; the warning was fixed
without waivers, and the failed snapshot/log remain available. Earlier passes
before the two physical-ACK coincidence probes are retained as superseded
coverage evidence.

See [the exact read contract](read-contract.md) and
[independent audit](../../experiments/python-gamebub-v91k-lines/audit.json).
The source controller's fixed 100-MHz/one-chip mapping remains unchanged.
Physical memory adapter wiring, command timing, refresh, scanout contention,
FPGA mapping and ESP32 service still require their separate qualification.

## Reproduce

```sh
python3 scripts/cu66-v91k-lines/run_comparison.py --seed 911701
python3 scripts/cu66-v91k-lines/run_comparison.py --seed 911702
python3 experiments/python-gamebub-v91k-lines/verify_results.py
python3 scripts/cu66-v91k-lines/summarize.py
```

Use the existing `gamebub-cu66-v69-build` container. The runner preserves strict
Verilator/GCC commands, hashes, compressed inputs and row events. Input pixels
are captured V91k canonical-memory replay, with the prior independent RGB
and edge goldens. No original packet bytes or quantization change.
