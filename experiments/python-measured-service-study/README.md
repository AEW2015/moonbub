# Per-packet measured Python service in the finite MA01 model

This extends the frozen [MA01 finite scheduler](../python-anchor-study/README.md)
in a new Python-only directory. It measures every **actually selected** prepare
call, then charges that exact duration to its virtual encoder stage. Captures
replaced in the one waiting slot are never encoded. Later frames are really
re-encoded against the ACKed reconstructed immutable anchor, so skipping does
not reuse bytes from a different reference history.

The experiment compares the original eager MA01 encoder, the iteration5 fast
P encoder, and the new [fast-key encoder](../python-key-prepare-study/README.md).
All cases use `motion_mode='zero'`, quantizer8, a refresh after30 capture IDs,
two packet slots/P credits, three logical front/pending/back roles, the same
48 KiB cap, and10 ms ACK feedback. Earlier finite models defaulted to global
motion estimation; those archived rates are not direct measurements of this
zero-motion comparison.

`Config` is immutable. `encoder_profile` selects `baseline`, `fast_p` or
`fast_key`; `decoder_service` selects `assumed` or `python_wall`. In either
mode actual `receive()` wall duration is recorded separately. The latter mode
charges the measured per-packet receive duration instead of the declared8 ms
receiver assumption. Receive runs offline at decoder admission to discover
that duration, holding its output until the virtual completion event; commit,
ACK and display publication only happen after service completion. This is not
a concurrent realtime sender/receiver benchmark or a native/FPGA decode result.

The prepare timer stops **before** `expected_hash()` integrity work. The
original encoder computes an RGB oracle eagerly inside its original prepare,
so that cost remains in the baseline; the optimized encoders defer it. Receiver
measurements exclude pixel-hash checking, RGB565 metrics and presentation.
Source video decode, capture/scale and all verification work still take real
wall time but are outside the charged services. Lazy P reconstruction remains
an optional verification cost, not free production decode.

Network8 Mb/s, QSPI160 Mb/s, feedback10 ms and60 Hz vblank remain assumptions.
Forward accounting charges68 application/IP/UDP bytes per1,024-byte payload.
RF/link/feedback overhead, physical memory transactions and true concurrent
host/network/ESP32/FPGA execution are absent. Actual Python services include
interpreter/NumPy and RGB receiver reconstruction costs that are not a target
RTL decoder schedule. Framebuffer roles are metadata ownership, not a physical
SDRAM allocation proof; source arrays and decoded verification buffers are
additional host memory.

## Reproduce and evidence

Use the common [pinned Python environment](../python-codec-study/requirements.txt).
Original clips remain outside Git. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

Six deterministic tests inject a work clock while still using real small
packets/decoders. They check exact7 ms prepare/11 ms receive service, exclusion
of a900 ms verification-oracle delay, assumed-vs-measured receiver selection,
real capture replacement under overload, finite slot/credit roles, loss and
corruption recovery, paid cap rejection, next-capture bounded backoff, immutable
configurations and mode validation. `tests.log` records passing checks.

`results.json` records twelve actual-codec cases: two60-frame primary windows
× three encoders × two receiver-service modes, with a one-second declared
`[500,1500)` ms diagnostic interval, strict `[0,2000)` ms capture interval and
1,000 ms drain. The independently reused validation helper checks exact
half-open counts, strictly increasing visible IDs and capture conservation.
No endpoint is shifted to manufacture a rate pass. Main cases must drain all
slots/credits and leave no unclassified capture IDs.

The source inputs are native25/29.88 fps already-compressed Mass Effect clips,
selected at1 s and scaled to720×480 using the common BOX letterbox. They are
scheduled at hypothetical30 capture IDs/s; repeated content and native PTS
remain in manifests. This is not native30-distinct-frame/s capture or broad
held-out game evidence. These60-frame windows do not cross the4 s held-out
boundary. Source/input/version hashes bind the measured run.

All cases run sequentially; external host load, frequency, affinity and warmup
are uncontrolled. Profile order is reversed between source clips, not a paired
randomized experiment. Re-running changes wall durations and potentially
selected IDs/packet histories; the artifact freezes one observed run. Comparing
quality or rate over different selected IDs is not an equal-quality codec
comparison. Link age and service results remain conditional.

## Recorded results

All twelve cases drain their slots, credits and capture dispositions. There
are no cap rejects, receiver rejects or injected faults in this primary-window
campaign; the overload manifests as latest-waiting-capture replacement. The
six deterministic tests contain the deliberate fault/cap conditions.

| Input / receiver service | Original diagnostic IDs/s | Fast P | Fast key+P | New strict / eventual of60 |
| --- | ---: | ---: | ---: | --- |
| Combat / assumed8 ms |15|26|28|55 /56|
| Combat / measured Python |14|22|24|47 /49|
| Second clip / assumed8 ms |14|27|29|55 /57|
| Second clip / measured Python |13|20|21|42 /44|

Thus optimizing key preparation admits additional captures beyond optimizing
P alone, but none of these measured-prepare cases reaches30 diagnostic IDs/s,
and every strict count remains below60. The results are not a phase-shifted
pass and do not claim native30 fps delivery. The gain cannot be credited to
buffer changes: all profiles use the same two-slot resource policy.

Each case prepares only two keys, so these key timing samples are small.
New key preparation means are36.91/30.33 ms, versus104.34/78.00 ms for the
fast-P-only cases in assumed-receiver mode. P means remain21.29/23.21 ms.
Measured Python P receive means are25.78/33.01 ms even when the model charges
only8 ms. Selecting actual receive service therefore exposes another service
bottleneck: the fast-key diagnostic count falls28→24 and29→21. These are
separate sequential timings with different selected packet histories, not a
paired decoder-speed ablation with identical packets.

For the fast-key cases, strict-window p95 presentation age is55.0/66.7 ms
with assumed8 ms receive and111.7/116.7 ms with measured Python receive.
Better frame admission alone does not close the latency budget. Peak staged
packet payload across this campaign is39,204 bytes; actual role/slot/credit
bounds remain two/two/three. Optional oracle packet retention and transform,
prediction, receiver/output and source arrays are additional Python memory.
This is not an optimized native sender or a bounded memory-fit report.

## Next gate

Use controlled native sender timings, incorporate source capture/scale and
receiver reference-memory/scanout service, and extend to long disjoint capture
windows. Keep separate key/P distributions and actual packet histories. A
short model diagnostic count cannot establish sustained30 fps or physical
latency; an actual overlapped sender/receiver and hardware qualification are
still required.
