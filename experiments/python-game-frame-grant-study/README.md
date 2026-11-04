# Frame-slot grants before application-codec commit

This Python study adds receiver frame ownership to the actual AR03 → GF03/PC18 →
decode → AF03 path from v18. Target stays **720×480 coded / 720×405 active / 30
scheduled source IDs/s**. Current firmware is still MSV1 JPEG; this contract is a
prospective, incompatible endpoint protocol. No ESP32 ISA/RF, native decoder,
FPGA memory/scanline service or physical 30 fps qualification is supplied.

## Three different permissions

- PC18 returns one consumed data-packet token. It grants no complete-frame capacity.
- FG19 grants one of two receiver frame owners before the encoder commits a
  candidate. A candidate retains its source lease while requesting capacity.
- AF03 acknowledges validated decoded-reference publication. A frame grant or a
  packet token never substitutes for that bank/frame/tag/body binding.

Each FG19 message has 32 field bytes and a four-byte CRC: **36 application bytes /
64 IPv4+UDP bytes**. Fields bind version, fixed laboratory epoch 1, message kind,
slot, frame ID, monotonically increasing request sequence, complete body size and
AR03 body CRC. CRC detects accidental corruption; it is not authentication.
Messages are REQUEST, GRANT, BUSY, CANCEL, CANCELED, FINISH, FINISHED and RELEASE.
There is no implemented reboot/reset/session rekey negotiation.

REQUEST names a slot the sender knows is free. The receiver grants only that slot;
it never substitutes a slot whose earlier RELEASE the sender might not have seen.
Only a matching received GRANT permits AR03 commit and data packetization. Requests
and frame metadata construction are paid; rejected candidates may send control
messages, but they never send DATA or receive AF03 publication. Their build and
cancel/discard costs remain paid.

After all the frame's exact PC18 packet permits return, the sender sends FINISH.
That is an explicit causal barrier after its DATA has drained the gateway worker.
FINISHED returns only the single request-control token, allowing another slot's
request to overlap the decoder. The frame owner remains held until the receiver's
reassembly and decoder/read owners drain and RELEASE arrives at the sender.
A serialized control profile omits FINISHED and holds the control token until
RELEASE; it is retained as a comparison, not the recommended overlap behavior.

A missing/corrupted fragment can leave partial ingress ownership until its declared
timeout. FINISH does not release that read/assembly owner. A valid header's unique
fragment indices are tracked separately; duplicates cannot satisfy that inventory.
The fragment index set is not itself permission to publish or release a frame.
Late old frame data and cancels fail the current identity/slot binding.

CANCEL is allowed only before the frame enters the DATA engine, including an
already-committed frame that misses its deadline before packetization. The receiver
rejects cancellation of an owner that has observed DATA. Sender cancellation also
refuses an existing queued/in-flight data-engine frame. A general mid-frame abort
and transport reorder/retry protocol is outside this study.

Wrong-kind, wrong-slot, stale or foreign-identity replies do not clear pending
control or another frame owner. A duplicate GRANT cannot clear an outstanding
FINISH, and an old RELEASE cannot clear a newer REQUEST. Lost GRANT, lost RELEASE
or an unanswered packet-credit query produces an explicit bounded safe stop;
unknown ownership stays owned. Those cases intentionally do not claim full drain.

## Bounded gateway and timing assumptions

Five DATA tokens reserve the sixth physical mailbox position for one FG19 or QC18
request. FG19 and packet-credit queries are mutually exclusive on the forward
control lane. Requests share the existing forward wire, RF aggregation queue and
single worker. Frame replies share reverse wire with PC18 and AF03. Forward and
reverse are independent virtual links; this is not calibrated shared Wi-Fi airtime.
Two frame owners, two ingress slots, three framebuffer roles, four AF03 descriptors
and a bounded FG19 reply set remain explicit. Receiver ownership includes incomplete
assembly and complete read-pinned frames. Byte counts include each real message,
IP/UDP overhead, loss injection and the one delayed duplicate RELEASE.

The `v18_median` service profile is a fixed historical Python model: milliseconds
are resize 3.25972, candidate build 29.4824, decoder begin 23.87022, candidate commit
0.09932, packetization 0.03485, decoder completion 0.01377 and ACK apply 0.00672.
Other timed Python stages use 0.005 ms. Actual reference functions still execute,
and their measured host wall costs are retained separately. Fixed costs let the
same policy toggle be compared without independent wall-timing jitter; they are
not target CPU calibration or a guarantee for every packet's complexity.

The measured profile uses actual Python stage durations. Both retain declared
ESP32 240 MHz / 60% CPU, bitwise CRC/copy/driver, 40 MHz quad-write, 8 KiB FIFO /
2 MB/s drain, link, feedback-latency and vblank assumptions. Map/resize/build,
route extraction, control construction/parse, DATA wrapping, ingress, decode,
ACK apply and all wires are charged. The Python event loop, policy bookkeeping,
source acquisition and correctness/quality oracles are not native CPU profiling.
Independent virtual servers are not a shared single-core execution schedule.

## Retained results

Twelve cases cover 790 scheduled capture events, with 58 conservative source/dependency
bindings and 28 passing unit tests. Seven native profiles reuse **180 unique source
acquisitions total** across the two windows. The 69.13-second Python campaign runtime
is not playback FPS. Each native diagnostic window is [500,2500) ms.

| Native profile | Strict / eventual out of 90 | Diagnostic IDs/s | GF03 busy feed rejects | Maximum all-presentation gap ms |
| --- | ---: | ---: | ---: | ---: |
| mass-effect-2600/fixed_base6 | 87 / 89 | 29.5 | 0 | 66.67 |
| mass-effect-2600/fixed_partition5 | 87 / 89 | 29.5 | 0 | 66.67 |
| mass-effect-2600/fixed_serialized_grants5 | 55 / 58 | 18.5 | 0 | 83.33 |
| mass-effect-2600/fixed_grants5 | 79 / 82 | 27.5 | 0 | 83.33 |
| mass-effect-2600/measured_grants5 | 79 / 82 | 27.0 | 0 | 66.67 |
| mass-effect-7200/fixed_base6 | 60 / 63 | 20.5 | 0 | 116.67 |
| mass-effect-7200/fixed_grants5 | 54 / 57 | 18.0 | 0 | 116.67 |

At the same fixed historical stage costs, separating FINISHED from RELEASE improves
the primary grant controller from **58 to 82** eventual presentations and 18.5 to
27.5 diagnostic IDs/s. This removes an avoidable serialization cost, but the
uncongested no-grant baseline remains faster at 89/90 and 29.5 IDs/s. The partition-
only five-token baseline is identical to its six-token counterpart here: this
native run peaks at four DATA tokens. A separate aggregated-control unit test
actually reaches five. Grants are a safety mechanism, not a blanket throughput
improvement. The measured pipeline result is separately remeasured and not a
controlled comparison with historical timings. No native case proves sustained,
evenly spaced 30 fps or target hardware throughput.

All selected RGB565 patch words are exact, with zero mismatch. **The secondary
7200 scene does not always fit all four requested HUD rectangles under the complete
49,152-byte cap.** Its baseline decodes 39 frames with all four patches and 24 with
only three; the grant run decodes 37 full and 20 partial. Missing the fourth rectangle
omits 5,760 exact words from each affected frame, leaving its lossy base reconstruction.
The primary 2600 scene retains all 21,120 requested words in every decoded frame.
`analysis.json` records requested, selected and omitted rectangles and word counts
for every decoded frame. Selected exactness must not be reported as full HUD coverage.

The secondary scene is also more byte-demanding: no-grant admission discards 23
builds, while the grant profile discards 16, spending 678.10 and 471.72 modeled
build milliseconds respectively. Discards may have paid REQUEST/CANCEL traffic;
they emit no DATA and publish no reference. The primary pipelined grant case pays
10,496 forward and 15,744 reverse FG19 IPv4/UDP bytes for 82 committed frames.

Lost GRANT, lost RELEASE and packet-credit blackhole controls stop explicitly with
unknown ownership retained; these three cases are bounded safe stops, not recovered
or fully drained streams. The other nine cases drain their candidates, ingress,
leases, data tokens, frame owners and pending controls. A dropped fragment and one
lost packet-credit/duplicate-release case recover with valid publication state.
The synthetic diagnostic window is only about 66.7 ms; its 45-ID/s phase count is
an artifact of that tiny window and carries no gameplay-rate claim.

## What this enables next

Reserve mandatory HUD bytes before adapting background quantization, rather than
silently omitting a requested patch in a complex scene. To recover controller
headroom, consider capacity leases reserved before candidate construction, followed
by exact body-identity binding at commit; that needs new generation/expiry proofs.
The present REQUEST is sent after build and keeps the single candidate busy during
an additional RTT. Connect actual AR03 block/refill demand to bounded incremental
FPGA decode and SDRAM/scanline timing, then calibrate ESP32 CRC/copy/DMA/heap and RF
batching/RTT before a native throughput claim. These are next experiments, not
features implemented by this study.

## Evidence and reproduction

`test_model.py` carries the sixteen prior end-to-end regressions. `test_grants.py`
adds lifecycle, delayed-control, exact no-data cancellation, frame-slot reuse,
unique-index, lost-control safe-stop, and combined DATA/control aggregation tests.
A deterministic slow-decoder pair reproduces GF03 `busy` without grants and
eliminates it with grants; this is a controlled mechanism test, not gameplay FPS.

The native campaign uses two existing precompressed 1280×720, 29.88 fps Mass Effect
windows, each 90 distinct source frames at four seconds. They are existing
regression inputs, not fresh held-out validation. Source acquisitions are shared
across profiles; repeated replay does not multiply the unique input corpus.
Five 32-frame flat controls test loss, query and replay ordering only. Their short
rolling-window ID rate can exceed 30 through phase; it is not capture or display
FPS and should not be used as a gameplay-rate result.

From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

`verify.py` checks retained source bindings, real packet/decode/reference records,
exact selected UI words, grant-before-commit, data/control accounting, bounds and
full drain or explicit safe-stop. It does not need external video. `benchmark.py`
regenerates evidence and needs NumPy, Pillow, PyAV and both external media files.
Set `GAMEBUB_MEDIA_DIR` if moving the media directory. It snapshots conservative
relative source/dependency hashes before and after the campaign. Keep those files
unchanged during a run. `failed-initial-probe.log` and `serialized-probe.log` are
historical preparation logs. `coverage-check-initial.log` records the useful
failed full-HUD assumption on the second scene; `pre-coverage-check-run.log` is its
superseded run. Only final `results.json`, `run.log`, `verify.log` and hash-bound
`analysis.json` are current.
