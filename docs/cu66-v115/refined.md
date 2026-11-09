# V115 refined implementation: header preparation and local tile writes

The initial V115 routes still fail setup at 100/125 MHz. Their final routed
paths, rather than the earlier synthesis estimates, select these two changes.
The refined candidate retains the initial inverse helpers, Rice parser and
reserved-command top. Only ingress and scratch change again.

## Ingress

The old HEADER edge computes four 32-bit length additions, a 34-bit size
comparison and error selection before updating the FSM. Its routed path is
15 levels, including six CARRY4 cells. The new implementation captures the
coherent length tuple at the owned response for header byte 29, forwarding its
current high byte. Three registered arithmetic steps finish well before byte
45 and the unchanged HEADER edge:

```mermaid
flowchart LR
    A["Owned WAIT29: four lengths + size"] --> B["E1: exact 33-bit pairs"]
    B --> C["E2: exact 34-bit sum and expected size"]
    C --> D["E3: one owned mismatch bit"]
    D --> E["Existing HEADER decision"]
```

The full carry and original 34-bit underflow semantics remain intact. Header
CRC/basic-format checks retain priority. Cancellation revokes predicate
ownership; every later HEADER must have a fresh complete preparation.

Both focused seeds pass, with 259 successful packets, 84 cancellations and
2,575,650 coefficient comparisons each. The original and candidate match all
56 public outputs across 59,264,429 checked edges. New cases exercise full
length carries, cancellation at each preparation phase and CRC-first error
priority. See [ingress details](refined-ingress.md).

## Scratch

The initial 125-MHz routed top-50 sample has 30 read-band-to-tile reset paths
and 18 read-band-to-tile enable paths. The new implementation captures each
existing clear/DC/AC write as one local bank/index/value tuple. Its 23 payload
bits plus valid bit replace distant combinational controls at the physical
payload write ports. One tuple can retire and another can arrive every edge.

```mermaid
flowchart LR
    A["Existing clear / DC / AC write event"] --> B["One local write tuple"]
    B --> C["Private tile payload commit"]
    B --> D["Visible tile: forwarding"]
    C --> D
    D --> E["Unchanged valid mask and reader"]
```

Forwarding preserves the original visible value on the original edge. An old
tuple retires even on reset or abort because its value was already visible.
Exact original branch priority also preserves late error effects. Controller,
tile-valid and bank ownership updates remain unchanged. No extra public cycle
is added by either refined cut.

Both focused seeds pass the inherited transaction, malformed-response,
read-owner, boundary and pending-descriptor cancellation suites. Every checked
edge also compares all 128 raw visible words. Eight added natural pending-write
kills per seed include complete retries on the same object; declared private
fixtures exercise back-to-back writes, error priority and held-bank retirement.
Earlier fixture mistakes and their runtime assertion failures remain archived.
See [scratch details](refined-scratch.md).

## Qualification boundary

Focused PASS does not establish whole-decoder correctness or timing. The
refined [full regression](../../experiments/python-gamebub-v115/refined/spatial)
and [peer campaign](../../experiments/python-gamebub-v115/refined/control-peer)
compile fresh against the frozen canonical oracle. New native cards require
both, all focused source bindings and an independent exact-card audit.

The separate [refined flow](native-refined-draft.md) retains the same synthesis,
placement/routing method and actual 8/10-ns clocks. It adds only reports for
the new preparation and write-slot registers. The routed reports must show
whether those registers survive mapping and improve the actual failing paths.
No source-level pipeline diagram, requested clock or focused PASS closes the
125-MHz, full-parent, hardware 30-fps or validated under-10-ms gates.
