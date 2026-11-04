# Three PC credits with two receiver ingress slots

This Python sensitivity study keeps the full 720×480 coded canvas, 720×405 active
native-sample image and primary 30 fps requirement. It compares two versus three
PC sender transactions/P credits while retaining **two GF02 receiver ingress
slots and three metadata framebuffer roles**. GM01/HG01/GF02/GA01 bytes, the
49,152-byte frame cap, immutable ACKed key, age gates, feedback binding and
reader-drain rules remain unchanged.

Both performance arms enable all three exact execution optimizations: admission-
aware full-source P-payload reuse, the pixel-exact zero/DC fast decoder, and
bounded exact RGB565 UI patch reuse. These results therefore differ from the
parent execution study, which did not enable UI reuse. Differences against that
older study must not be attributed solely to credit count.

The model copy changes configured PC sender/credit bounds, their validation,
encoder-factory agreement and result metadata. It also rejects unsupported
controller labels and closes the deferred-ACK expiry edge described below.
`copy-origin.json` pins the frozen execution model and adapter from which it was
derived. The adapter fixes the normal rate controller and adds the UI-cache
callback. **Only `Config.controller='normal'` is accepted by this study.**

A valid ACK may wait for a duplicate reader to drain. If a later matching NACK
requests expiry before that drain completes, expiry must win. The inherited
model's deferred-promotion branch checked `ack_waiting` first and could install
the key after requested expiry. An actual small-packet regression emits serialized
GA01 ACK then NACK while a duplicate feed owns a reader; it reproduces the old
failure. This new copy blocks deferred promotion after requested expiry, pays all
reader work, and releases through expiry. A spy observes no encoder ACK call in
that case; a positive ACK-only control still promotes after drain. This repair
applies to both credit arms and is not credited as a window-size performance gain.
Frozen earlier study files are unchanged.

## Measured scenarios

Seven runs completed in 61.85 seconds of host wall time. There are 780 scheduled
capture-policy events, 661 actual preparations and 661 independently hash-checked
decodes. Every preparation, decoder, BOX resize and transport/feedback call pays
its newly observed wall cost; there is no fixed service tape or assumed decode
duration in the retained performance runs. Stages occupy independent virtual
servers; this is not a measurement of parallel execution on one physical CPU.

| Source / refresh | Credits | Strict / eventual deliveries | Middle-window IDs/s | P-credit wait |
| --- | ---: | ---: | ---: | ---: |
| Combat, 60 IDs, periodic30 | 2 | 53 / 54 | 28.0 | 262 ms |
| Combat, 60 IDs, periodic30 | 3 | 55 / 56 | 28.0 | 0 ms |
| Second, 60 IDs, periodic30 | 2 | 41 / 44 | 21.0 | 553 ms |
| Second, 60 IDs, periodic30 | 3 | 53 / 55 | 27.0 | 0 ms |
| Held-out second, 180 IDs, periodic30 | 2 | 121 / 123 | 20.0 | 1,661 ms |
| Held-out second, 180 IDs, periodic30 | 3 | 158 / 160 | 26.4 | 62 ms |
| Held-out second, 180 IDs, initial-only probe | 3 | 166 / 169 | 28.4 | 635 ms |

The 60-ID strict window is `[0,2000)` ms and the longer window `[0,6000)` ms,
with separate 1,000 ms drains. Diagnostic windows are `[500,1500)` and
`[500,5500)` ms. Counts are distinct presented **IDs**, not a claim that the
precompressed source supplied that many distinct native images. **No run delivers
all 60 or 180 IDs inside its strict window.** Initial-only is a separately labeled
six-second probe, not a qualified long-run default refresh policy.

The two-credit traces expose substantial waiting on ACKed credit. Three credits
largely remove that waiting with periodic refresh, but do not eliminate encoder,
refresh and startup/tail gaps. Holding an older key in the initial-only probe
increases residual work/packet cost and P-credit waiting again; removing refresh
does not make reference age free. Waiting-state intervals are exclusive categories,
not additive causal attribution of all lost frames.

All selected RGB565 patch words remain exact, with zero selected-region errors in
every run. Full-picture quality must still be compared because different admission
and refresh histories can change reference keys. Decoded active RGB565 MSE means
for the long periodic30 pair are 19.446 (two credits) and 19.454 (three); the
initial-only probe is 19.648. On common decoded IDs the long credit-pair mean MSE
delta is +0.0081, and periodic30-to-initial-only delta is +0.1690. These are sampled
run outcomes, not an established perceptual quality threshold.

The combat pair has identical complete packet hashes for all 54 commonly prepared
IDs under identical ACKed reference histories. The short second pair has 43 common
IDs but only 22 share the same reference/forced-key history and complete packet
hash. In the long credit pair, 116 IDs are common and 41 share that same history
and hash. The initial-only comparison has 153 common IDs and 28 identical-reference/
packet IDs. Re-measured host load and causal histories
remain confounders; these runs are not an isolated statistical proof of a policy
speedup. Same-packet component studies provide the exact arithmetic evidence.

## Ownership, memory and fault limits

The native performance runs reach three PC sender/pending credits where enabled,
two receiver ingress slots and three framebuffer roles. They have no GF02-busy
rejection. This is plausible when a PC transaction is waiting for feedback after
its receiver read has already drained; three PC transactions do not necessarily
mean three simultaneously owned receiver payloads.

Eight passing unit tests use actual small codec/transport packets and explicitly
declared test costs. They cover invalid bounds/factory disagreement, two-credit
trace equivalence to the frozen model, UI-cache byte equivalence, loss/corruption/
duplicate/wrong feedback, paid cap rejection, late ACK during parser read ownership,
deferred ACK followed by expiry, and forced overload. The overload reaches three
sender credits with two ingress
slots, actually receives `GF02 busy`, pays the failed feed/NACK work and recovers
after read-drain. A native run with no busy error does not establish that a third
credit is safe for arbitrary packet, decoder or network timing.

One additional PC sender slot permits another 49,152 bytes of logical outer packet
capacity. Pending GM packets, outer packet copies, transport queues, cached RGB/UI
payloads, full transform/reference/output arrays and Python object overhead are
extra. The UI cache remains bounded to four entries; its largest recorded
persistent source-word/payload total is 55,611 bytes, excluding object metadata
and transient buffers. The unchanged two-slot ingress allowance is 98,304 payload
bytes. Metadata framebuffer roles do not prove a physical three-buffer allocation.
No target memory allocation, SDRAM arbitration, native code or RTL fit is supplied.

The retained timing assumptions remain 8 Mb/s forward/reverse, 160 Mb/s QSPI,
10 ms feedback propagation and 60 Hz vblank. A 150 ms decode-age gate followed by
vblank is not a strict 150 ms optical-latency guarantee. Source clips are related
precompressed 25/29.88 fps files decoded offline; BOX work is charged, acquisition
is not. There are no real sockets, ESP32/Wi-Fi transfer, DMA/CDC or physical scanout
measurements and no sustained hardware 30 fps proof.

## Reproduce

Run from this directory with the study virtual environment:

```sh
python -m unittest -v test_credit_window.py
python verify.py
python benchmark.py > benchmark.log 2>&1
```

The read-only verifier checks 27 executed source pins, full cap/ownership/drain
and timing accounting, feedback/wire totals and selected-region exactness. Results
retain all per-commit active MSE, source hashes, actual call wall/service durations,
and common-ID/reference/packet comparisons. The initial failed import-check attempt
is retained separately; the successful benchmark uses an explicit local verifier
import so sibling study paths cannot select another checker.

The superseded pre-deferred-fix summary/model copy records the earlier research
iteration only. Its old timings are not the final result claim; the complete
seven-case benchmark is rerun after the repair with new executed-source hashes.

The next implementation experiment is negotiated, bounded sender credit sizing
with native service measurements. Keep decoder and memory ownership fixed while
measuring credit lifetime before committing to more complex codec hardware.
