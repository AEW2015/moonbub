# V117 ingress descriptor extents

Status: prepared for Root qualification; no run or timing benefit is claimed here. This preparation note is a pinned input after launch; terminal receipts/audits report subsequent outcomes. All V117 A/B inputs and old evidence remain immutable.

The actual V117 A125 routed cause is [the terminal route](../../experiments/python-gamebub-v117/read-study/native/20261109T113046956485Z/receipt.json): WNS −1.925 ns, ingress `size_bytes[1]` → `offsets[0][0]/CE`, 16 logic levels including eight CARRY4. Its 9.636 ns data delay is 3.840 ns logic and 5.796 ns routing. The frozen source is V115 final ingress, SHA256 `e5ca00d03ca91050295da961e5793e7fd96bd183d83e668fbcd7a21b1784a2d6`. This actual path authorizes a descriptor arithmetic hypothesis; the earlier qmap note remains a separate unimplemented study.

## Same-cycle production cut

The packet size is retained on start and stays stable throughout this packet. Two private full-width registers compute `size_bytes-4` and `8*(size_bytes-46)` on preceding existing clocks, before any descriptor is reached. They have no reset or global payload enable. They use held internal size_bytes rather than an unregistered shortcut from packet_bytes.

On the existing SELECT_BAND edge, retain three additional descriptor facts alongside the original band/length tuple: remaining bytes `(packet_payload_end-cursor)`, cursor-out-of-range `(cursor>packet_payload_end)`, and expected descriptor payload bytes `(lengths[band]-6)`. The existing DESCRIPTOR edge still performs the short-length/remaining guard before initial fetch. On completed descriptor return it compares the unchanged descriptor byte count and bit count against the prepared limits before the original k/count/padding checks and exact offset/size/cursor commit.

All widths remain 32 bits. The code preserves subtraction underflow, cursor wrap and the modulo-2^32 `8*(size_bytes-46)` product; no natural valid-packet bound is used to narrow synthetic corrupt cases. Initial request address, descriptor last address, padded fetch byte 6, offset `cursor+6` and successor cursor `cursor+active_length` keep their original expressions and edges. The 34-bit header length pipeline, CRC-first handling, byte request/response ownership, metadata, context decoder and cancellation priorities are untouched. There is no new port, public state, queue, descriptor slot, status delay or extra parser edge.

Small verification-only certificates prove packet size/epoch maturation before selection, selected cursor/band/epoch ownership, and equality to every old full-width predicate at actual DESCRIPTOR consumes. Every old assertion block remains byte-identical. Source-level unreset storage does not predict physical reset mapping; native synthesis/routing must inspect the implemented registers and paths.

## Qualification and independent oracles

Root dispatches:

```sh
python3 scripts/cu66-v117/ingress/qualify.py --run --suite all --root-grant ROOT_GRANTED_INGRESS_FOCUS
```

The direct ingress proof uses the frozen final source as its original and the actual current Rice/context sources in both variants. The immutable all-public wrapper compares every original output, counter and invalid-data view on every clock. Two seeds retain 160 corpus profiles, 259 complete successful packets, 84 cancellation/retry checks, 11 malformed full-34-bit length/CRC-priority checks, all original dense-derived coefficient/memory/epoch oracles and real synchronous read conservation.

The additive descriptor bench uses real existing FINISHED/SELECT_BAND predecessor clocks to mature the candidate's private data; it never forces its new registers. It compares old/current state, error, cursor, request tuple, all four offsets/sizes/k fields after each edge and independently checks:

- 6,272 initial descriptor cases spanning all four bands, 14 packet sizes, eight cursor boundaries and 14 lengths, including uint32 underflow/wrap and independent MAX_PACKET_BYTES request eligibility.
- 21,860 completed descriptor cases spanning full-width bit counts, byte-ceil/length boundaries, offset/cursor wrap, k errors, zero-event and padding priority; successful commit values are checked independently.
- 56 reset/start/abort priority cases at selection/consume edges, followed by 56 fresh prepared retries. Real complete-packet retries remain in the unchanged inherited suite.

These synthetic full-width prepared predicates are not packet-reachability claims and do not clock out-of-range packet RAM reads. Actual corpora retain all natural RAM owner, CRC, malformed input, stalls and retry checks. No old assertion, comparison, clock edge or warning severity is removed or masked.

A second actual-caller pair uses the same current AC scratch in both old/new variants and distinct wrappers selecting the frozen or new synchronous ingress. It retains the established 207 common public/raw/counter fields, packet goldens, physical scratch memory checks and preparation/cancel cases. Thus it isolates this ingress change rather than accidentally running the new ingress on both sides. Seeds are 117701/117702 for direct ingress and 117801/117802 for the caller.

Every attempt preserves source/recipe/compile snapshots, strict `--assert -Wall` and C++ `-Werror` builds, log/trace hashes, and actual-RTL status persisted before invocation. Root alone owns the two globally bounded heavy slots; this agent launches none. The compact results selector binds the raw terminal receipt.

## Scope

Focused PASS would not be native timing closure. Root must freshly qualify the exact combined source map in full decoder/transport, peer and LIVE parent tests before an eligible source-bound routed trial and independent audits. This is a timing cut with zero claimed public cycle savings. The inverse/reconstruction latency result, physical memory/CDC/display integration, ESP32 execution, sustained hardware 30 fps and validated under-10-ms decoding remain separate gates.
