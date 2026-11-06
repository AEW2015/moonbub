# COPY tile aliases with bounded physical slots

The [Python memory-layout prototype](../../experiments/python-gamebub-v87/alias/prototype.py)
tests an application-specific way to avoid rewriting unchanged COPY tiles.
Each canonical tile position has three physical 64-byte slots. A descriptor
map names the slot used by each tile; aliases point directly to a physical
slot, rather than to another generation of descriptors.

The accepted reference map and one active scanout map each pin at most one
slot per tile. They may name the same slot. At least one of the three remains
available for a provisional residual or CONST write. A COPY operation uses the
accepted reference's slot without a data write. Thus a long chain of COPY
frames does not pin an unbounded chain of whole-frame banks.

## What is checked

Two schedules replay all 457 frozen native content sources: present every
accepted frame, or retain the old scanout for seven source intervals. All 914
scenario/source replays reproduce the exact 8,100 decoded tile arrays. The
source's canonical raster hash is retained separately; the model's tile-order
digest has a different layout and is not mislabeled as the canonical hash.

The [independent alias audit](../../experiments/python-gamebub-v87/memory/alias-audit.json)
ties all 914 rows back to native tiles and presentation identities. It also
uses an immutable-image oracle for eight seeded histories of 128 updates each,
checking mixed COPY/write operations, held scanout and failed candidates.

Before publication, every provisional data write is outside both live leases.
The tests compare accepted and displayed content before and after those writes.
An invalid content digest aborts the candidate, invalidates its written slots
and preserves both live maps. Separate tests inject incomplete candidates at
three write depths, reject false COPY eligibility and retain an old scanout
through 100 accepted updates. **61 retained checks** accompany the replay.

The [selected result](../../experiments/python-gamebub-v87/alias/results.json)
binds a unique attempt with source and row hashes. Initial development evidence
is retained under `alias/development/initial` and excluded from the selected
result. Native input gzip/raw digests are checked by the frozen loader.

## Storage and traffic scope

The three physical slots require **1,555,200 logical pixel bytes**. Three
packed two-bit descriptor maps require **6,075 logical bytes**, before validity,
ownership/version state, queues, port replication or RAM rounding. The Python
lists and byte objects are not an FPGA resource estimate.

Both replay schedules create 2,216,647 COPY aliases across the corpus. The
prototype writes 95,043,392 pixel bytes instead of the dense write-every-tile
comparator's 236,908,800 bytes. **This comparator differs from the existing
candidate-bank residency model**, which already elides some stores. These
savings cannot be subtracted from its reported memory time or used as the
realization of the separate memory-study counterfactual without rebuilding
the actual command and metadata traces.

All non-COPY operations write in this prototype, including CONST. Reference
reads for residual prediction and dirty leaf hashes are not modeled away.
Address-map traffic and display-gather operations are not priced. The model
does not run the encoded stream, dequantization, C2 tree or physical controller;
it operates on the already verified decoded tile corpus.

## Next implementation work

Descriptor publication is one sequential Python action. Hardware needs explicit
transaction fences, provisional write completion/drain, generation/replay
policy and scanout lease handoff. It must never free a slot while a physical
reader still holds it. Derive a command trace that includes descriptor accesses,
tile-address translation, cache misses and indirect display prefetch. Feed that
trace into the coupled decoder model before projecting a latency improvement.

The current result proves a bounded **functional layout contract** for one
accepted reference, one scanout and one provisional candidate. It establishes
neither target RAM fit nor hardware 30 fps or under-10-ms decoding.

```sh
python3 experiments/python-gamebub-v87/alias/prototype.py
```
