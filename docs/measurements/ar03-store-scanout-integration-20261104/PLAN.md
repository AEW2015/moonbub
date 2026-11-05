# Selected512 store → column-major scanout integration checklist

Design/checking only: no RTL implementation, parent edits, publication checkout,
wire capabilities, board build or hardware. `source-bindings.json` pins the
actual modules/fixtures. Keep selected AR03 kit/native semantics; GM27/CP27/JA27
and v28 tap rules are not adopted. Other periodic KEY/P backlog studies are
context, not an accepted production map or throughput certificate.
The current source is **AR03/GM01/CP02 private KEY, pre-HUD**. It is not a complete
CP23/HC22/HD22 or CP25/GM25/HD25 implementation. Windows retaining CP23 does not
make it compatible with this private seam, and the AKD1 BIT is not a complete
negotiated receiver. Profile/code/image/loader readiness needs the separate audit.

## Exact mismatch and selected seam

`ar03_key_tagged` produces Y, then Cb, then Cr, each in **plane-local row order**.
Its exposed sample transfer jointly advances canonical SHA and the observer.
SHA hashes `<HH` dimensions then **sample byte, zero byte** per uint8 sample.
The selected admission-guarded `ar03_yuv_elastic(DEPTH=512)` stores only the sample
byte/last/owner stream; plane/x/y are not retained in its byte FIFO.

Its unchanged sink pairs adjacent canonical bytes into16-bit words and sets
`pixel_address = start_base + (accepted_bytes >> 1)`. At720x480 the first word
contains Y(0,0),Y(1,0). The gather instead needs Y(0,0),Y(0,1) in column word0:
the old pair maps to destination byte0 and byte480, **different words**. An
address-only remap cannot fix the data. `mapping-checks.json` proves all259,200
source words are incompatible with a simple word remap in this profile.

**Selected additive boundary:** keep the512-byte FIFO/owned sink unchanged;
insert an owner-scoped **word-input transpose coalescer** between its
`pixel_valid/ready/address/data` and the shared memory service's pixel port.
Capture each whole source word in a two-byte skid before acknowledging it;
split its canonical low/high bytes, validate the expected source ordinal/address,
fill a transpose stripe, then emit newly assembled vertical16-bit words at
column-major addresses. Do not send the old addresses directly to memory.

For the first join, restrict the local fixture/profile to720x480. Relative byte
layout, with symbolic region base B in16-bit words:

```text
Y:  byte_offset =             x*480 + y
Cb: byte_offset = 345600 + cx*240 + cy
Cr: byte_offset = 432000 + cx*240 + cy
physical_word = B + floor(byte_offset/2); lane = byte_offset mod2
```

This is518,400 bytes/259,200 words; no installed capacity, physical base or bank
assignment is selected. Wider end-address arithmetic and disjoint region leases
must validate the entire footprint before START.

## Bounded transpose storage

| Plane | Geometry | Practical one16-row bank | Double bank for fill/drain overlap |
| --- | ---: | ---: | ---: |
| Y |720x480|11,520 bytes|23,040 bytes|
| Cb |360x240|5760 bytes|11,520 bytes|
| Cr |360x240|5760 bytes|11,520 bytes|

One maximum-sized bank can be reused sequentially across planes with
backpressure; do not sum three double banks unnecessarily. The minimal simple
first implementation is **one11,520-byte bank + two-byte input skid + held
output-word state**, retaining the existing512-byte ingress FIFO and memory
packer's burst storage. It pauses input while draining. Double buffering is a
later measured initiation-interval improvement, not required for correctness.

These are practical full-useful-BL8 stripe bounds, not an absolute minimum over
byte-scatter/RMW architectures. Before the first full column fragment can finish,
15 complete rows plus its first16th-row sample must have arrived:10,801 Y bytes
or5401 chroma bytes in this profile. Even the first vertical16-bit Y pair needs
one whole720-byte row plus a new sample; the512-byte FIFO alone cannot transpose.
Current raster RAMs are two8-row banks already owned by block→canonical/SHA;
sharing them requires a new port/lifetime proof, not an assumed free resource.

General geometry is a separate decision. Native34x18 has17x9 chroma and a source
word spanning final Cb/first Cr. Compact34x34 and718x478 require respectively17
and359 pending halfword records at column-fragment boundaries in the checked
drain ordering. The current packer **unmasks both bytes** of every16-bit input:
partial-byte output is not supported. A generic successor needs explicit carry/
byte enables or padded column descriptors, plus changed gather strides and full
padding bounds. Padded examples are planning alternatives, not an adopted map.

## Implementation and acceptance checklist

- [ ] **Join START atomically.** Owner/epoch/frame/base and fixed geometry belong
  to one job. Gate each child START by the other's ready and all cancel guards;
  preserve `!reset&&!abort&&!fault` admission dominance. The key start has no
  frame/geometry inputs; its accepted metadata is internal. Validate the declared
  fixture geometry and all exposed sample plane/x/y/last against that admission,
  or expose accepted metadata through a new additive variant before generalizing.
  Do not treat `ks`/store-ready independently as a joint launch.
- [ ] **Keep the canonical handshake exact.** Feed selected `sample_ready` from
  FIFO ready/checker-ready; each sample hashes and enqueues exactly once. Never
  hash column-drain order or padding. Track original plane/x/y before the FIFO,
  then reconstruct/check it from the canonical word ordinal in the coalescer.
  A word may contain bytes from two planes in generic geometry; reserve both
  byte lanes before acknowledging it. Hold all output fields under backpressure.
- [ ] **Do not forward FLUSH too early.** Upstream store `force_flush` is a
  level in FLUSH. Latch it as end-of-input, seal/drain the final local stripe and
  word first, then assert downstream packer flush. Packer `pixel_ready` is false
  while flush is high; passing that level directly would deadlock local drain.
- [ ] **Compose real empty/drain.** Give the unchanged store
  `memory_idle = coalescer_empty && real_memory.physical_idle`, where empty includes
  input skid, stripe banks, issued reads of those banks and held output word.
  Require final packer flush plus accepted physical writes completed before
  private DONE. Its `accepted_words` then counts words accepted **by the
  coalescer**, not completed physical words; report those counters separately.
  Sample settled clock edges, never a transient asynchronous `wait(idle)`.
- [ ] **Abort without ownership loss.** Stop acceptance, invalidate only unissued
  local/packer data, and let accepted physical bursts drain. Keep owner/base held
  through ABORT_DRAIN and explicit full-tuple release. Store `discard` is normally
  high in IDLE, including the valid START edge: distinguish idle-empty discard
  from active cancellation so it cannot erase a newly admitted job. No runtime
  global reset/rekey or timeout may manufacture empty/drain/release.
- [ ] **Hold integrity completion.** Keep the tagged KEY result until full-tuple
  match, all FIFO/coalescer state empty and physical drain. The selected fixture
  has3 HUD patches/16,181 patch bytes; its certificate is pre-HUD YUV. For this
  first lab compare `native render565(planes)` **base pixels**, not final native
  `display565`. Complete AR03 reference/AF03/display publication additionally
  requires patch validation/application; do not relabel base-ready as acceptance.
- [ ] **First immutable front only.** Use a distinct private candidate region;
  keep the sealed gather locally in initialization until validated base+drain,
  instantiate its base/owner/epoch/frame to this one fixture, then prime chroma
  before enabling LCD scan. This is a one-job offline seam, not runtime reset
  recovery or reusable front descriptors. Preserve preset0/margin13.
- [ ] **Future descriptor/swap seam.** The current gather's base/owner/frame are
  parameters and it issues initial reads automatically. A continuous successor
  needs held front descriptors/generations and admission, captured per line/read.
  Keep LCD `front_buffer=0`: its selector adds legacy RGB offset0x080000, which
  the YUV gather rejects as a logical column address. It is not a YUV bank switch.
  Commit a new descriptor at the actual frame boundary only after new write
  drain/integrity and old read/response/cache/kernel/line-bank leases retire;
  otherwise retain the old front. Never retag a late old response as the new job.
- [ ] **Separate worker release from region release.** Store release clears its
  execution owner; it does not implement immutable display/reference leases.
  Transfer/add the front lease atomically before releasing worker context, and
  free old backing only after every reader retires. `physical_idle` may coexist
  with a held owned response; descriptor reuse additionally needs the relevant
  `owned_quiescent`/consumer fences. No-store P still needs persistent display
  YUV backing; it cannot overwrite a predictor. General P/reference publication
  is absent, and the growing P-backlog study remains a separate unresolved gate.
- [ ] **Prove the real joined workload.** Compare every stored byte, canonical
  tag and base display pixel to selected native data; test byte/word/stripe/plane
  boundaries, FIFO full, final flush, stalls, high-owner mismatches and abort at
  skid/fill/drain/accepted-burst/verification fences. Verify guards/nonalias and
  real physical writes. Then repeat actual LCD latch timing with the bounded
  reservation service using the **actual coalescer output**, not the synthetic
 11,520-byte source. Retain any missed lines, candidate backlog and initiation
  interval; prior finite static/load passes do not establish this joined path.

## Reproducible mapping evidence

Run `python prepare.py` then `python check_mapping.py` here with the existing
MSYS2 compiler/OpenSSL. No HDL build is performed. Five geometries are checked:
2x2,34x18,34x34,718x478,720x480. A direct ordinal→column formula is compared with
an independent nested-row `zip` transpose and inverse, uniqueness, compact/padded
bounds, source-word cross-plane examples and order-only masked-BL8 grouping.
Those grouping counts are **not cycle simulations or resource proofs**.

The checker also compiles the unchanged pinned native `canonical_tag` function,
using real OpenSSL rather than a stub. Its tags match Python canonical order for
all cases and the selected actual518,400 sample fixture. The fixture's wire-byte
tag is `c6c97dee75f2be10adddff19f0985885`, corresponding to the existing reversed
scalar RTL notation. Hashing transpose drain order is explicitly checked to
produce a different tag. `mapping-checks.json` contains machine-readable layouts,
sample/word examples, padding costs, carry observations, source/tool hashes and
the exact native results. This proves the design arithmetic/order only, not an
implemented transpose or successful end-to-end codec/store/scanout.
