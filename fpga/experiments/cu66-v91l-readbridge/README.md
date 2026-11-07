# Tagged BL8 read bridge through real SDRAM pins

`bl8_read_bridge.sv` accepts one aligned 16-byte physical request with bank,
epoch and generation. It issues one read to the unchanged controller, captures
all eight unbackpressured x16 return beats, then requires two consecutive
observed controller-idle clocks before offering its immutable 128-bit response.
The extra data staging is one 128-bit register (16 bytes), plus ownership,
status and counters; no frame buffer is added. There is no physical memory-error
input in the original controller, so error responses report invalid/canceled
requests, not detected silent SDRAM faults.

## Measured component result

The final matched eight-mode campaign passes 132 check entries and checks
3,111,744 controller/model read words, including the raw fourth-bank probes.
Both seeds reproduce these full native windows at the 2-ns data-delay corner:

| Native canonical frame | Independent gathers | Retained rows |
|---|---:|---:|
| actual_001, bank 0 | 1,565,404 clocks / 15.65404 ms | 846,844 clocks / 8.46844 ms |
| actual_006, bank 1 | 1,565,402 clocks / 15.65402 ms | 846,703 clocks / 8.46703 ms |

Times assume the same 10-ns clock and cover the read-client/bridge/controller
component, including refresh and the explicit final response fence. Retention
reduces this component by 45.90–45.91%, with the same exact canonical bytes.
These are not full decoder/publication or actual RGB565-converter windows.
The 7-ns corner runs units only. The two native frames are fixed source-backed
fixtures, not a multi-clip quality or sustained-cadence corpus.

The protocol matches the physical side of `tile_rowpair_reader`. Bank IDs 0..2,
nonzero epoch/generation, 16-byte alignment and canonical extent 0..518399 are
checked. Bank-role authorization is the caller's contract; this bridge does
not implement reference/front protection or frame publication. The raw unit
mux separately probes bank 3 to test the physical controller, without allowing
that reserved bank through the client interface.

Warm cancel/reset prevents unaccepted issue. An accepted read retains its
identity and captures/drains every remaining controller beat before returning a
zero-payload error after the idle fence. An offered response remains stable
through later cancel/reset and backpressure. Cold reset while a physical read
is owned is forbidden and asserted. The controller receives only cold reset;
warm cancellation never resets a partially active SDRAM burst.

`tb_readbridge.sv` joins the actual controller and the unchanged functional
SDRAM pin model using the established 10-ns source clock, 4-ns forwarded-clock
flight and 7.75-ns capture phase. Static independent/retained row-reader clients
consume the source-derived 32,400-line prefill sequence. The matched frame
window begins after accepted reader start, before the first logical offer, and
ends after the final canonical response ACK. It includes client/bridge/controller
scheduling, ACT/PRE/refresh and two-idle response fencing. It does not run the
actual RGB565 converter, decoder, hash/publication, live source transport or
shared arbitration.

Native memory contents are **direct testbench model preloads** from pinned
canonical goldens mapped into tile8×8 bank 0/bank 1; they are loaded after units
and before all native frame fences. This is explicitly not a physical write
join. `generate_fixtures.py` pins the source canonical gzip and ordered logical
line vector, plus raw/compressed hashes for the preload and request fixtures.
The root-level independent checker can reconstruct every pin read and canonical
response against those source bytes.

Unit probes cover three permitted client banks plus a raw fourth-bank read,
write→read→write turnaround, seeded exact read values, invalid bank/alignment/
extent/zero lease IDs without controller side effects, cancellation before
physical acceptance and after 0/3/7 captured beats, held error/success responses,
periodic refresh and the last canonical burst. The final matrix uses two seeds,
static retain 0/1 clients and tAC 2/7-ns unit corners. Native two-frame replays run
at the 2-ns corner; selected read delays are functional tests, not a vendor/PVT
model or routed electrical signoff.

Reproduce from the repository root with the existing
`gamebub-cu66-v69-build` container:

```sh
python3 scripts/cu66-v91l-readbridge/run_comparison.py
```

The runner retains exact source snapshots, input expansions/digests, strict
Verilator 5.020/GCC 13.3.0 build commands, simulation exits and compressed JSONL
receipts. It uses `--binary --timing --assert -Wall`, C++20 strict warnings and
two compile jobs, without adding a warning or assertion waiver. Early diagnostics
remain retained. Actual hardware sustained 30 fps and complete validated decode
below 10 ms are not established by this component.
