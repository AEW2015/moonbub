# V117 full-width descriptor byte-count comparison

Status: prepared for Root qualification. No run, mapped timing improvement or cycle saving is claimed by this preparation note. It becomes a frozen input when dispatched; terminal receipts and audits report subsequent outcomes.

The actual B125 [terminal receipt](../../experiments/python-gamebub-v117/throughput-study/native/20261109T121229166037Z/receipt.json) is SHA256 `d8ea9755f43ee1551d13929a24f755f34cc82fb44ce6ed437c435dafbe96be85`. The [Routed report](../../experiments/python-gamebub-v117/throughput-study/native/20261109T121229166037Z/reports/route-setup-paths.rpt) measures ingress fetch_bytes[2][3] → offsets[0][28]/CE at **−2.202 ns**, 17 logic levels including eight CARRY4, 9.913 ns data delay (60.546% routing). The placed −2.250 ns estimate is superseded by this actual routed cause.

This isolated candidate derives from the already focused-PASS [descriptor-extents source](../../fpga/experiments/cu66-v117-ingress/br88_packet_ingress_sync_v91h.sv), SHA256 `abfcef202b0c6792c89a45723bf0916c33c3ed7259ad756a59c120d03b7f6882`. That source's [selected proof](../../experiments/python-gamebub-v117/ingress/results.json), complete prior tests and old failure/snapshot history stay intact. All V115 assertions and the descriptor-extents assertions remain byte-identical in the new production source.

## Exact arithmetic cut

The original private view remains literally unchanged:
`descriptor_bytes=(descriptor_bits>>3)+32'(descriptor_bits[2:0]!=0)`.
Only its equality predicate in the completed-DESCRIPTOR branch changes.

Let `u=descriptor_bits>>3`, `f=(descriptor_bits[2:0]!=0)` and `L=active_length-6`, all compared at full unsigned 32-bit width. The original condition is `u+f!=L`. For every 32-bit descriptor:

| Fraction | Equivalent bad-byte-count test |
| --- | --- |
| f=0 | `u!=active_length_minus6` |
| f=1 | `u!=active_length_minus7` |

SELECT_BAND prepares `active_length_minus7=lengths[band]-7` on its existing edge beside the unchanged minus-six owner tuple. Subtraction keeps modulo-2^32 semantics. There is no new state, capture edge, queue, public signal or status delay.

The identity follows by subtracting f from both sides modulo 2^32. In addition, u is at most `0x1fffffff`, so its increment cannot overflow 32 bits. At L=0 and f=1, the new right side is `0xffffffff`, which cannot equal this 29-bit u; it must reject, just as the original ceil does. At L=`0x20000000`, a zero u must not match: narrowing either comparison to 29 bits would introduce a false acceptance. At maximum u with f=1 the original ceil reaches `0x20000000` and the full-width identity still holds.

The original packet-bit bound remains the independent second operand in the same error-4 branch. k/count/padding ordering, error 7, descriptor_ready clearing, offset/size/k/cursor writes, physical request/response handling and CRC/header priority are unchanged. The private descriptor_bytes view and every old assertion are retained. A new assertion checks minus-seven ownership and compares the substituted bad flag against the original ceil equality at every actual DESCRIPTOR edge, even when the independent bit bound would already cause rejection.

The intended timing hypothesis is to remove the ceil increment from the late descriptor commit qualification cone, replacing it with full-width equality comparisons against existing-edge registered values. Synthesis may retain carries for comparisons or optimize the expression differently; only an eligible actual route can establish its mapped structure or timing. There is no KEEP, DONT_TOUCH, fanout directive, false/multicycle path or implementation-strategy change.

## Fresh proof

Root dispatches:

```sh
python3 scripts/cu66-v117/ingress_bytecount/qualify.py --run --suite all --root-grant ROOT_GRANTED_BYTECOUNT_FOCUS
```

The direct original is the exact focused-PASS abf descriptor-extents source; the current parser/context is shared unchanged. The immutable all-output wrapper and all old 259-packet/84-cancel/11-header-malformed tests run first, followed by the unchanged 6,272 initial and 21,860 completed descriptor cases and 56 cancellation/prepared-retry cases. The new source does not modify those tests or skip clocks.

The additive bench performs **1,920** more completed-descriptor cases: ten full32 expected-byte values, six u boundaries, all eight low-bit remainders and all four bands. It uses the old independent ceil-byte and state/offset/request/commit oracles through real existing preparation clocks. This includes 168 L=0/nonzero-remainder cases, 320 maximum-u cases and 960 high-expected-byte cases. For maximum-u nonaligned values, the packet-bit-limit branch can mask a terminal difference; the new equality assertion still checks the byte-count predicate independently at the consuming edge.

The actual-caller pair uses the exact abf synchronous ingress as its reference and the new byte-count source as its candidate, with distinct reference wrapper types. Both retain the same current AC scratch and all old 207 common public/raw/counter checks, packet goldens and preparation/cancel tests. Direct seeds are 117901/117902; caller seeds are 118001/118002. All old SVAs, `--assert -Wall`, C++ `-Werror`, actual-RTL-before-run persistence, source snapshots and failure retention remain required. No heavy job is launched by this agent.

Focused success does not imply full decoder/transport/peer/LIVE qualification or routed timing closure. Root must bind the exact combined source and both actual routed causes to fresh functional receipts before an eligible native trial. The separate II=1/reconstruction latency evidence, hardware 30 fps, full parent memory/CDC/display/ESP32 integration and validated under-10-ms decoding remain distinct gates.
