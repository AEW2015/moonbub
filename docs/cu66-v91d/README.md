# V91d: packet-to-packed-memory RTL and dense coefficient delivery

Parent: `4ff660d4be06ef522de977bb78badd2b64a79e72` (V91c).

**The packed scratch model now has RTL connected to packet validation.** The
integrated test receives BR88 bytes, validates them, allocates bounded external
scratch, acknowledges writes, rereads the image and delivers dense coefficients.
A 64-bit validity mask replaces 64 sequential tile clears, reducing actual-packet
service cycles **34.43% with idealized one-cycle memory** and **27.10% with the
slower memory scenario**.

This is the residual-coefficient endpoint. Inverse transforms, reconstructed
pixels, reference/HUD/hash publication and display remain outside it. Memory
service is a finite-latency simulation, not physical SDRAM qualification.

## Implemented path

- [Packet ingress](../../fpga/experiments/cu66-v91d/br88_packet_ingress.sv) is a
  V91c-derived copy with validated metadata credit and explicit context-end
  handshakes. Block/count/raw/epoch metadata appears only after the complete BR88
  chunk CRC, header and descriptors pass. Replay waits for scratch allocation.
- [Packed scratch](../../fpga/experiments/cu66-v91d/packed_scratch.sv) implements
  one 16-byte assembler, acknowledged writes, zero padding, deferred descriptor
  write/readback, four line caches, three AC heads and one local 64-entry tile.
  It preserves V91c's packed bytes; there is no full dense scratch array.
- [Integrated top](../../fpga/experiments/cu66-v91d/br88_pipeline.sv) joins
  metadata, coefficients, context ends, successful packet completion, memory ACKs
  and dense-output credit. Sticky `done` follows final accepted dense output and
  includes the final controller edge.

The profile supports 1–8,192 blocks in one 256-KiB bank. DC is signed16; each AC
record is block13 | raster6 | signed13. RAW stores all raster values, including
zeros. Segments are 16-byte aligned/padded. Counts, ranges, band order, epoch and
allocation size are checked. Wire syntax and quantization are unchanged.

Writes are provisional until packet success and all write ACKs permit sealing.
Dense output also waits for descriptor readback. A late semantic or memory error
cannot publish a partial coefficient transaction. This local seal is distinct
from the outer frame/reference seal.

## Memory ownership and recovery

The port supports **one outstanding 128-bit transaction**, aligned byte addresses
and matching-epoch responses. Reads and writes both require ACKs, at least one
edge after acceptance. Requests/output stay stable under backpressure.

Accepted writes remain real after cancellation. Reset/abort drains the accepted
response before new allocation or bank reuse. New packet ingress can proceed in
its separate buffer while validated metadata waits for that credit. Stale aborts
are ignored. Epochs increase strictly across warm reset/abort; wrap/reuse requires
cold recovery with an empty external bus. Initial FSM/outstanding/epoch state
relies on FPGA power-on register initialization. Cold initialization does not
clear the external RAM bank.

The integrated harness delays an accepted write by 501 edges, then aborts,
resets or replaces its packet. The old write still commits at ACK; new allocation
waits and the replacement image remains exact. Poisoned RAM is reused without
clearing. See the [full interface/reset contract](../../fpga/experiments/cu66-v91d/README.md).

Peer review found and reproduced a restart race: an old store error could drive
internal packet abort on the edge that the outer controller accepted replacement
start. Ingress reset to idle while the outer controller waited for new data.
The fix gives start priority over internal old-owner cancellation; external
reset/abort retains priority. The exact-edge regression fails on the retained
pre-fix snapshot and passes on both final seeds.

## Tile clearing and measured results

The serial control clears 64 payload entries before each coded tile. The candidate
clears a 64-bit validity mask in one cycle; writes mark entries and reads select
zero for untouched positions. Old tile payload cannot leak. RAW bypasses coded
tile clearing. Both modes preserve exact outputs and memory images. Runtime
modes coexist in this prototype; separate mapped/routed variants are needed for
area and achieved-clock comparisons.

Independent vectors include 12 actual packets from C0/f0, C0/f1, C0/f3 and C3/f50,
four coded/raw synthetic packets, and a valid 8,192-block packet whose AC value
is at the last supported block/index. Frozen V88 decoding reconstructs the
expected sparse order, dense bytes and packed image. Selected V91c image hashes
also match.

| Campaign | Result |
| --- | --- |
| Standalone scratch | 17 cases × four configurations; 26 directed checks |
| Integrated seed 910432 | 17 cases × four configurations; 11 directed checks |
| Integrated seed 910433 | Same coverage and identical final sources |
| Dense comparisons per integrated seed | 7,519,744; 1,879,936 per configuration |
| Packed images | Every case/configuration matches byte-for-byte |
| Memory work per successful case | Exactly `used_bytes/16` reads and writes |

The configurations cross mask/serial clearing with FAST/SLOW service. FAST
accepts requests/outputs continuously and ACKs one cycle later. SLOW uses write16
and read18 delays plus deterministic 0–3-cycle jitter, with seeded byte-offer,
request-ready and output-ready stalls. Jitter depends on address/seed, so distinct
epoch tags do not alter A/B costs. Paired modes see the same cycle-indexed
offer/ready traces, although their actual accepted stalls differ. These are
explicit scenarios, not calibrated controller timings or network guarantees.

Seed 910433, actual 12 packets only:

| Memory | Serial-clear cycles | Mask cycles | Reduction |
| --- | ---: | ---: | ---: |
| FAST | 3,875,484 | 2,541,333 | 34.43% |
| SLOW | 4,923,445 | 3,588,964 | 27.10% |

Each row delivers 1,355,328 dense coefficients from 65,602 packet bytes, with
18,454 read and 18,454 write bursts. FAST saves exactly 1,334,151 cycles:
63 removed clear cycles × 21,177 coded blocks. SLOW retains identical request
counts and memory-pending work. Synthetic/maximum-block results remain separate
so mostly-zero fixtures do not inflate the gameplay comparison.

The fence includes ingress, CRC/descriptors, metadata/end/seal credits, write
ACKs, descriptor readback, merge, positive read latency, output stalls and sticky
completion. Start edges are excluded. V91c ended at sparse output, so its smaller
cycle total represents a different endpoint.

The three serialized chunk-service sums per selected source provide a useful
budget check, **not complete-frame latency**:

| Source | FAST mask cycles | SLOW mask cycles |
| --- | ---: | ---: |
| C0/f0 | 770,983 | 1,067,754 |
| C0/f1 | 459,873 | 645,985 |
| C0/f3 | 341,132 | 476,834 |
| C3/f50 | 969,345 | 1,398,391 |

The roadmap's unachieved 100-MHz comparison target would require fewer than
1,000,000 **complete-fence** cycles for strictly under 10 ms. Two SLOW sums
already exceed it before remaining stages; the largest FAST sum leaves just
30,655 cycles. This identifies work to remove and does not pass that deadline.

Directed checks cover held transfers, ACK errors, unsolicited/stale responses,
delayed-write cancellation, reset held through ACK, epochs, count/order/range,
capacity, premature seal, descriptor/value corruption and restart. A separately
rebuilt valid BR88 packet is 17,584 bytes but needs 280,256 scratch bytes:
integrated admission rejects it before any memory request or dense output.
Holding the final dense value for 257 cycles cannot assert completion early.

The fixed-cap RTL admits the metadata boundary of 262,144 bytes (8,192 blocks,
61,432 AC3 records) and rejects the next aligned allocation. RAW 2,047 blocks
uses 262,048 bytes and fits; RAW 2,048 uses 262,176 and fails admission. The vector
index's `exact_capacity_case` describes that latter mathematical RAW size and a
one-burst-smaller hypothetical budget, not a supported 262,176-byte RTL bank.

Structural memory checks are not ECC or arbitrary corruption proof. Full-frame
hash/reference validation still needs integration. The real RTL selection covers
four sources from one related precompressed walkthrough family; repeated seeds
do not add distinct gameplay or sustained live frames.

- [Standalone receipt](../../fpga/experiments/cu66-v91d/scratch-results.json)
- [Integrated receipt](../../fpga/experiments/cu66-v91d/pipeline-results.json)
- [Independent vectors](../../experiments/python-gamebub-v91d/vectors/index.json)
- [Independent audit](../../experiments/python-gamebub-v91d/audit.json)
- [Combined evidence](../../experiments/python-gamebub-v91d/summary.json)

## Next work and remaining milestones

1. Overlap bounded assembler, memory and tile service. Preserve explicit ACK
   ownership/drain when adding queues or requests; multiple outstanding work
   requires a response-order/tag contract.
2. Connect actual dequantization/IDCT/reconstruction, reference/HUD/hash consumers
   and their cycle fences. Frame acceptance cannot follow from coefficients alone.
3. Continue V92 finer entropy/group choices with actual byte/memory/host costs.
   Keep the existing native CPU reader after V91's negative CPU result.
4. Reserve V100–V110 for 7-series mapping, placement, routing and timing. The
   packet copy still assumes combinational multi-address staging reads; real
   RAM ports/banking/latency require remeasurement. External controller service,
   transforms, CDC, transport and continuous scanout need whole-top qualification.

**Hardware 720×480 at sustained 30 distinct fps and complete validated decoding
strictly under 10 ms remain open.** No achieved clock, calibrated controller,
live ESP32/Wi-Fi/QSPI test, hardware run or deployed firmware/bitstream is claimed.

## Reproduction

Run from the repository using `gamebub-cu66-v69-build`. No additional Python
packages are needed. Builds use fatal Verilator warnings, assertions, C++
`-Werror`, two jobs and watchdogs.

```sh
python3 scripts/cu66-v91d/build_vectors.py
python3 scripts/cu66-v91d/run_scratch_rtl.py
python3 scripts/cu66-v91d/run_pipeline.py --seed 910432
python3 scripts/cu66-v91d/run_pipeline.py --seed 910433
python3 experiments/python-gamebub-v91d/verify_results.py
python3 scripts/cu66-v91d/summarize.py --write-manifest
python3 scripts/cu66-v91d/summarize.py --check
```

Attempts retain sources, inputs/hashes, tools, commands, exits and logs. Earlier
passes and the pre-fix regression failure remain distinct. Its duplicate text
fixture is represented by the pinned gzip and exact serializer; original hashes
are unchanged and existing unpacked local text stays on disk. Restore it with
`python3 scripts/cu66-v91d/retain_vectors.py --restore`. Regeneration selects new
attempts; re-audit and bind them rather than rewriting historical receipts.
