# Fixed-profile constant descriptors and addressed traffic

This experiment reserves descriptor value 3 for CONST128 **only at the 294
positions in the existing fixed hidden-tile profile**. At every visible
position, value 3 remains INVALID. Values 0–2 still identify physical tile
slots. The fixed position profile distinguishes the two meanings; this is not
a general fourth data slot or a claim that arbitrary constants need no validity
state. Geometry and hidden-mask identity are checked against the frozen profile.

The candidate map remains unpublished until validation completes. Clearing a
candidate map to all ones cannot make its visible entries readable, and the
active reference/display maps remain leased. The experiment retains every
descriptor access and explicitly writes the constant entries. It introduces no
new validity bitmap and claims no metadata-traffic saving.

## Actual native-content replay

All **457 sources** reconstruct the exact native tile arrays and C2 root/seal
using the new descriptor interpretation. The unchanged V88 layout runs beside
it, and its complete addressed accounts match the already published V88
controls on every source. Packed descriptor bytes are replayed across epochs.
Constant tiles never occupy a physical pixel slot in the new state model.

The new trace removes 1,176 write BL8 commands and 1,176 base-gather read BL8
commands per frame. Over the corpus that is **537,432 writes and 537,432 reads**.
It emits 8,598,912 logical constant bytes for candidate construction and the
same number for base gathering. These are separate generation events, not
zero-time work inferred from omitted memory commands.

| Descriptor placement | Maximum decoder memory-busy work | Maximum including base gather |
|---|---:|---:|
| On-chip | 9.80272 ms | 15.42304 ms |
| Small word cache | 9.88908 ms | 15.53226 ms |
| Uncached external | 15.49304 ms | 22.57136 ms |

At assumed 100 MHz and 18-cycle read / 16-cycle write service, the exact
memory-work reduction is 18,816 cycles for decoder stores and another 21,168
cycles for base gathers per frame. **These are memory-service reductions, not
decoder completion improvements.** Constant-generator ports, hash consumption,
display conversion and scheduling still need explicit timing. A pipeline may
avoid some candidate generation when no consumer needs it; this model retains
the full logical candidate output instead of assuming that optimization.

The physical address window remains 1,555,200 pixel bytes. Unused constant
positions are holes in the current layout, so this does not prove a smaller
memory allocation. The existing three packed maps remain 6,075 logical bytes
and 6,144 bytes with the current map alignment.

## State and failure checks

Twenty contract checks include an immutable-image oracle with **1,024 symbolic
accepted updates**. They test held scanout, partial candidates, invalid content,
false constant COPY operations, visible INVALID descriptors, packed constant
values, absent physical addresses for constants, and protection of accepted
state through abort. Publication cannot expose an unvalidated candidate map.

This is sequential functional and addressed-traffic proof. It does not qualify
asynchronous bus drain, atomic hardware map swaps, generator throughput or
continuous display. The joint Rice/alias timings in this iteration retain the
V88 layout and do **not** include this separate constant-sentinel change.

- [Selected trace results](../../experiments/python-gamebub-v89/constants/results.json)
- [Contract tests](../../experiments/python-gamebub-v89/constants/tests.json)
- [Independent accounting audit](../../experiments/python-gamebub-v89/constants/constants-audit.json)

```sh
python3 scripts/cu66-v89/prototype_constants.py
python3 scripts/cu66-v89/test_constants.py
python3 scripts/cu66-v89/audit_constants.py
```
