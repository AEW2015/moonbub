# V22 whole-video/HUD transaction model

This Python component closes v21's **functional admission and logical joint
publication gap**. It keeps 720×480 coded /720×405 active content and all four
exact RGB565 HUD regions. It does not implement native Sunshine/ESP32/FPGA
endpoints, negotiated capabilities/reset/rekey, GF03/FG19 carriage, DMA ordering,
RTL clock-domain behavior, physical vblank or 30-fps operation.

## Prepare, admit and commit together

`JointSender.build` constructs HC21 on a private bookkeeping fork of its last
ACKed display cache. The actual legacy full-patch and HD21 candidates are both
paid. The clone shares immutable confirmed patch arrays; it does not copy whole
published banks. The legacy selector's bounded performance cache may be updated
by speculative work, but this does not authorize a display reference.

The sender then builds actual patch-free AR03 base candidates under at most four
declared ROI/background maps: `(8,16)`, `(8,32)`, `(16,32)`, `(32,32)`. Every actual
map/analysis/forward transform/serialization/discard is paid. This first version
does not share forward analysis across losing maps. A candidate fits only when
the complete **AR03 +HC21 +57-byte CB21 binding** is at most 49,152 bytes. A fitting
base alone grants no permission to commit an oversized pair. An optional per-call
`profiles=((roi,bg),)` override supports matched fixed-quality controls.

Rejected maps and deadlines, all-map exhaustion, callback errors and explicit
discard leave issued video ID, HUD generation, pending publications and published
bank identities unchanged. A retained accepted candidate holds the frozen base
API's source-reader lease until discard or commit. Independent pre-existing
reader leases survive retries, rejection, discard, commit and ACK.

Commit executes all fallible base work on a metadata fork. Only then does one
`_state` tuple assignment expose both the committed video and HUD endpoints.
Whole-pair stop-and-wait allows one unresolved pair. A later mutation of a public
component's identity/bank semantics invalidates its candidate; late independent
reader additions remain legal and are rechecked at publication.

## One bound acknowledgement

JA22 has a 33-byte header, exact 43-byte AF03 and 54-byte HA21, and final four-byte
CRC: **134 complete application bytes**. Header fields bind version, epoch, frame,
SHA256[:16] of the complete pair and exact inner ACK lengths. Both component
identities are validated before sender state is forked. The full bytes must match
the exact outstanding pair's expected AF03/HA21. Both inner ACK applications occur
on private metadata; one tuple swap publishes their results. A wrong, stale,
mixed-half or wrong-pair ACK cannot confirm only video or only HUD.

JA22 is a proposed lab ACK grammar. Its hashes/CRC provide consistency, not
authentication. It does not replace PC18 packet permits or FG19 frame ownership.
Those transports have not been integrated with this transaction model. JA22's
134 bytes and any lower-layer overhead must be counted; combining ACKs is not
free latency or bandwidth.

A dropped packet leaves the sender unresolved and permits only an exact
`retry()`. After successful receiver presentation, `retry_ack(packet)` returns
the exact prior JA22 without republishing. It rejects any different bytes. There
is no automatic timeout, retry budget or ambiguous-ownership recovery policy.

## Decode privately, then expose a matching display epoch

`JointReceiver.prepare` validates the complete pair cap/framing/identity, decodes
both real component packets on private bookkeeping forks, compares full HUD
identity and composes a private RGB565 display. Base and HUD publication results
remain private. A corrupt fourth HUD patch cannot expose the already-decoded
base, any of the first three patches, new YUV banks or an ACK.

A non-key preparation holds a live parent source-reader lease until abort or
presentation. `snapshot()` includes this legitimate private read ownership;
`published_snapshot()` excludes reader bookkeeping and compares visible bank/
frame identities, display digest and last ACK. Failed preparation and abort must
restore the full ownership snapshot, while successful preparation must preserve
the published snapshot.

Publication requires **two explicit injected model events**:

```python
task = receiver.prepare(packet)
receiver.mark_writes_drained(task)
ack = receiver.present(task, vblank=True)
```

Decoder completion alone never sets the write-drained flag. Presentation checks
both events, candidate identity/generation/publication semantics, optional
caller-supplied deadline, and current base/HUD destination readers. A reader
acquired after preparation can still block presentation. Release it and retry
the same presentation; do not fabricate a free destination.

Two alternating HUD banks and the existing two video-reference banks remain
independent. Eight unique top-level reader descriptors cover base/HUD leases;
duplicate releases cannot drain another owner. Tokens fail closed at uint32
exhaustion until a later local epoch reset. Component leases are preserved across
metadata swaps. Caller-provided event times and fence/vblank events are trusted
functional inputs, not a simulated clock, measured write completion or hardware
fence implementation.

Local reset calls require a later epoch and drained active/pending/read owners.
They deliberately do not implement a wire reset handshake or recovery from a
one-sided reboot/lost reset message. The known-safe choice under unknown ownership
is to remain stopped; a production session-reset protocol is still required.

## Arrays, memory and proof boundary

Bookkeeping forks copy dictionaries/sets/lists, not full YUV/HUD bank arrays.
Newly produced YUV planes, patches and displays are marked NumPy read-only and
are shared unchanged through later ordinary decisions. This is a normal trusted
local API contract, not adversarial memory protection: owning NumPy arrays can
have their write flag re-enabled by a deliberately mutating caller.

The frozen codec uses **int16 oracle YUV**, 1,036,800 array bytes per full native
reconstruction, rather than the uint8 compact storage proposed for hardware.
Private base RGB conversion and the 691,200-byte RGB565 display also exist.
HUD storage still includes two 42,240-byte banks and one 42,240-byte private
replacement, before parser/packet/hash scratch and descriptors. Retained golden
oracles and exports add further storage. No heap peak, bank placement, BRAM/DSP
fit, external-memory service or physical scanout deadline is established here.

## API and retained checks

```python
s = JointSender()
r = JointReceiver()
c = s.build(rgb, frame_id, force_key=key, promote=promote)
if not c.accepted:
    # c.info retains all paid losing work; no issued identity advanced.
    pass
else:
    packet = s.commit(c)
    task = r.prepare(packet)
    r.mark_writes_drained(task)
    ack = r.present(task, vblank=True)
    s.ack(ack)
```

`Candidate.info` is JSON-compatible diagnostic data; control uses private owned
records and actual bytes, not caller-edited metrics. `ReceiveCandidate` exposes
private `planes` and `display` for oracle comparisons. `C`, `hc` and `compose`
export the frozen AR03, HC21 and CB21 helpers. `base`/`hud` properties resolve the
current state and should be fetched afresh after a tuple swap.

Twenty-one tests cover whole-pair cap failure after a fitting base, all four paid
noisy rejections, ID reuse, deadline rejection, patch exceptions, source leases,
late destination readers, explicit fence/vblank, abort, bad fourth patch, packet/
ACK loss, mixed ACK halves, wrong epoch, stale/tampered handles, component mutation,
read-only shared banks, duplicate leases, bounded tokens, fixed receive geometry
and drained local reset.

From this directory, with the project Python environment:

```sh
python -m unittest -v test_model.py
python verify.py
```

The parent campaign/retained verifier supplies real-source packet and quality
results. Component correctness is separate from scheduling, hardware throughput,
physical ownership and sustained fresh gameplay qualification.
