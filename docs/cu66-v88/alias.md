# V88 addressed alias traffic and selected causal replays

This study turns V87's three-slot functional layout into an addressed traffic
trace on all **457 native sources**. It preserves exact decoded tiles and the
frozen reference/residency/content identities. It is still a software model,
with assumed memory service and logical ports, rather than hardware timing.

## Physical addresses and descriptor values

Each canonical tile position has three 64-byte physical slots. Slot `s`, tile
`t` begins at `s * 518400 + t * 64`. The accepted reference and one scanout map
pin their slots. Every non-COPY tile writes an available slot, even if the old
whole-bank residency design would have elided that store. COPY points directly
to the accepted slot and requires no canonical data write.

Three packed descriptor maps contain 8,100 two-bit entries each: **6,075 logical
bytes**. External address strides are padded to 2,048 bytes/map, or 6,144 bytes.
Entry `t` uses byte `t // 4`, shift `2 * (t % 4)`, with physical slots 0–2 and
value 3 meaning INVALID. The candidate map is cleared before use. Physical
descriptor-bank roles rotate by pointer publication; no descriptor-map copy is
silently omitted from the command counts.

Every trace includes descriptor values as well as addresses. A packed-byte
replay persists descriptor RAM across all source epochs and checks accepted,
presented and scanout reads against those actual bytes. Independent native
tile gathers reproduce the original tiles. Clear, provisional data writes,
valid descriptors and publication are separate events.

Residual prediction reads the accepted slot. COPY reads are retained where a
dirty C2 leaf requires actual payload, but clean COPY groups do not materialize
the tile. All canonical writes, 2,640 HUD writes, 2,640 HUD readbacks and a
complete 32,400-BL8 YUV base gather have explicit aligned 16-byte data addresses.

## Descriptor-storage sensitivity

The policies retain the same pixel layout and decoded output:

| Descriptor policy | Model |
|---|---|
| On-chip | Dedicated nominal one-entry/cycle read and write ports; descriptor accesses do not consume the external data bus. |
| Cached external | One 16-byte word per accepted/presented/scanout role; full candidate-word accumulation and known INVALID padding permit full-word writes. |
| Uncached external | Each entry lookup reads a 16-byte word; each candidate entry update performs external read-modify-write. |

The cached policy is an explicitly assumed small cache/accumulator architecture,
not measured hardware. It retains separate role caches even when reference and
scanout name the same map. Controller row, refresh, direction switching and
physical map ports are not calibrated.

At assumed 100 MHz, 18 cycles/read BL8 and 16 cycles/write BL8:

| Policy | Median / maximum total memory-busy work | Maximum decoder-only memory-busy work | Improved / equal / regressed sources versus frozen residency |
|---|---:|---:|---:|
| On-chip | 13.18928 / 15.82288 ms | 9.99088 ms | 419 / 20 / 18 |
| Cached external | 13.29850 / 15.93210 ms | 10.07724 ms | 384 / 0 / 73 |
| Uncached external | 20.33760 / 22.97120 ms | 15.68120 ms | 7 / 0 / 450 |

The total includes complete base-gather pixel and descriptor reads. The
decoder-only figure excludes both post-publication gather classes. It is
**necessary service work, not decoder completion time**: resource overlap,
producer stalls, map-port latency and the remaining arithmetic still matter.

The frozen residency comparator gets the same 32,400-BL8 base gather and HUD
traffic. Its original reference/store totals are independently reproduced from
the native bank model and checked against published V82 rows. This is not a
comparison against dense write-every-tile. Actual data addresses are retained
for the alias design; the comparator uses the frozen bank-layout accounting.

The 18 on-chip regressions matter: avoiding COPY stores does not imply that
all non-COPY store elisions from another physical layout remain valid. The
uncached external descriptor policy largely erases the gain.

## Selected causal schedules

The selected replay changes actual V87 coupled task graphs. It removes only
COPY stores and unnecessary clean-COPY reference reads, and **adds stores for
non-COPY tiles previously elided by frozen whole-bank residency**. Added stores
also hold their group/map-publication fences until completion. The old C2 tree,
hash and certificate-map work remains conservatively priced; this does not
claim that the old certificate metadata itself implements alias ownership.

Dedicated nominal descriptor resources charge candidate clear, accepted and
scanout lease lookup, valid descriptor write and pointer publication. Every
selected schedule retains dependency, resource, output-group and finite
reference/inverse/coefficient lifetime checks. Publication and base-gather
completion are distinct fences. A fresh C0/frame-3 graph is reconstructed and
checked against its frozen V87 timing specifically to test restoration of 294
old-elided non-COPY stores.

Ten schedules compare alias and control on four unique sources:

| Source / frontend | Control publication | Alias publication | Alias full base-gather completion |
|---|---:|---:|---:|
| C0/f0, LOW two-lane key | 7.22181 ms | 7.30283 ms | 13.21583 ms |
| C0/f1, LOW two lanes | 12.10858 ms | 8.83972 ms | 14.75272 ms |
| C0/f3, LOW two lanes | 8.89402 ms | 7.94219 ms | 13.85519 ms |
| C3/f50, LOW two lanes | 12.82457 ms | 11.27666 ms | 17.18966 ms |
| C3/f50, HIGH two lanes | 18.58340 ms | 17.14844 ms | 23.06144 ms |

These are conditional schedule times under the inherited assumed primitive
costs, not measured decoding. The key gains no COPY-store reduction and gets
slower because descriptors add work. On C0/f3, 1,731 COPY stores are removed
but 294 non-COPY stores must be restored; both changes are explicitly scheduled.
The difficult source remains above 10 ms even before the later base gather.

The full source campaign is traffic accounting. Only the representative graphs
are causally scheduled; they do not constitute full-corpus alias latency data.
Their existing fixed CS86 frontend is unchanged, so the separate new entropy
format is not substituted into these timing numbers.

The post-publication gather uses a nominal 64-byte tile buffer and sequential
canonical tile order. It proves every YUV base tile is addressed once. It is
not a continuous raster LCD schedule, RGB565 conversion, HUD compositing or
proof of a sufficient raster line-buffer allocation. Those mechanisms require
a separately priced display design.

## Failures, drain and limits

Twelve retained tests exercise selected packed descriptor-byte replay and
mutations, plus a minimal delayed-write lease oracle. An aborted issued write
must drain before its physical slot can be reused. The oracle demonstrates
that merely ignoring an old response tag is insufficient if its physical write
can arrive after a new frame has reused the slot. This is an explicit contract
test and counterexample, not an implemented asynchronous controller.

The logical layout still uses 1,555,200 pixel bytes, descriptor storage, and
extra working/control state. Probability state, C2 trees, compressed input,
physical RAM packing/ports, actual raster buffers and target fit are extra.
Neither hardware 30 fps nor complete validated under-10-ms decoding is proven.

Evidence: [addressed campaign](../../experiments/python-gamebub-v88/alias/results.json),
[selected causal replays](../../experiments/python-gamebub-v88/alias/probe.json),
[restored-store witness](../../experiments/python-gamebub-v88/alias/extra-case.json),
and [value/drain tests](../../experiments/python-gamebub-v88/alias/tests.json).

```sh
python3 scripts/cu66-v88/prototype_alias.py
python3 experiments/python-gamebub-v88/alias/extra_case.py
python3 experiments/python-gamebub-v88/alias/test_trace.py
python3 experiments/python-gamebub-v88/alias/probe.py
```

Campaigns and probes create unique attempt directories. Interrupted early
revisions and the original eight-case probe are retained as development
history and excluded from the selected final verdicts.
