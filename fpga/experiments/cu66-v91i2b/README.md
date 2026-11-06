# V91i2b RTL: bounded registered-read refill overlap

`cs88_pipeline_v91i2b.sv` changes only the outer-packet to child-byte refill
schedule. `REFILL_OVERLAP=0` retains the V91i2a request/wait/send loop;
`REFILL_OVERLAP=1` instantiates `byte_refill_queue_v91i2b.sv`. The existing
V91i2a admission/table implementation and V91h BR88/scratch pipeline remain
unchanged. Mode-map initialization, wire bytes, quantization and coefficient
placement are not optimized in this checkpoint.

The enabled helper has two physical byte/last slots and at most one pending
registered read, with **queued slots + pending owner ≤ 2**. A request reserves
its eventual slot before launch. On each edge, a consumer handshake pops the
old head, the prior accepted read may push its one-edge response, and a new
read may launch if `count + pending - pop < 2`. There is no response-to-child
bypass. Simultaneous push/pop use separate ring positions. An offered request
holds address/epoch until accepted, and a valid head holds byte/last until pop.

Responses must match the pending address and frame epoch exactly one edge
after acceptance. Missing, unsolicited or mismatched active responses fail
closed. The span is already checked by CS88 admission; this helper assumes
upstream-provided offset/length describe a legal bounded packet span. It does
not add an independent untrusted-address protocol or a physical memory
controller.

Child start, accepted frame start, abort, warm reset and failure invalidate
local refill ownership. They do not invent an acknowledgment or erase an
already accepted external packed-store request. The unchanged child retains
that request through real ACK drain, and replacement remains blocked until
quiescence. The source packet bank remains owned throughout refill and decode.

Per-frame `refill_queue` receipts report request/response/pop/stall counters,
canceled queued/pending owners, high-water marks and final owners, along with
independently observed counterparts. Disabled-mode added counters are zero.
The integrated C++ test checks every source byte, signed coefficient, full
placement tuple, stable offers, one-edge response binding and external ACK
ownership. Its original 11-case prefix retains the original RNG call order;
new directed cases run afterward so disabled-cycle comparisons are meaningful.

The actual child receiver normally accepts bytes continuously, so sustained
ready-low testing belongs in the standalone `tb_refill_queue.cpp`, which drives
the same helper through its public ready/valid interface. It tests full-queue
hold, simultaneous push/pop, held read offers, abort/reset/replacement of queued
and pending owners, empty/single/tail cases and malformed response rejection.
This adds no product test-only control or hierarchical force. Mode 1 also runs
two integrated abort/reset checks while a queued byte and response are owned.

The helper's two byte registers and existing registered RAM-return value are
logical storage descriptions, not proof of a mapped resource count or timing.
The 98,304-byte duplicate packet staging budget from V91i2a is unchanged.
Pixels, dequantization/IDCT, reference reconstruction, HUD/content validation
and publication remain later consumers; no hardware 30-fps or complete
under-10-ms result follows from these simulations. The next planned stage is
V91j dequantization/IDCT on the qualified BR88 path.
