# V97 measured results and limits

Compact framing reduces overhead and the bounded gateway now interoperates
with actual FIFO/credit RTL in a native test. This is not a deployed streaming
release or a complete decoder benchmark. V97a and portable parts of V97b have
software evidence; V97c has a native-host/RTL substitute; on-device integration
and V97d calibration remain open.

## Host preparation and complete framing

The PC helper encoded and validated twelve synthetic 720×480 baseline JPEG
images using the existing encoder, then formed compact datagrams. Complete
encode/validation/CRC/packetization time was **1.141 ms median**, **0.558–1.789 ms**
across those twelve frames. It excludes capture, live Sunshine/NVENC service,
network transmission and receiver work. It does not establish production 30 fps.

A second lane framed all **457 frozen CS92 payloads**, totaling 7,781,939 bytes,
through an explicitly configured opaque research sink. It preserved exact
payloads, with CRC/packetization taking **8.226 µs median** on this host
(1.754–25.327 µs). These are already encoded inputs; no codec preparation or
CS92 decoder/reference behavior was measured by this lane.

The independent header checker imports no protocol/parser/sender and fully
decodes the twelve JPEG files with Pillow at 720×480. It recounts all 469 rows:

| Metric, combined payload set | Legacy MSV1 | Compact V97 |
|---|---:|---:|
| Unchanged payload bytes | 8,614,501 | 8,614,501 |
| Data datagrams | 8,650 | 6,384 |
| Application header bytes, data only | 346,000 | 84,112 |
| Complete application bytes including setup | 8,960,501 | 8,699,013 |
| Complete IPv4/UDP bytes including setup | 9,202,701 | 8,878,045 |

V97 charges five setup/ACK exchanges: 400 application bytes plus 280 IPv4/UDP
header bytes. Net savings are **261,488 application bytes** and **324,656
IPv4/UDP bytes (3.528%)**. MAC, radio retries, feedback and contention are outside
both columns. Header reduction is not codec compression or measured RF goodput.
A larger accepted JPEG cap is not a guaranteed interactive bandwidth budget.

## Parser and bounded native gateway

The selected native Rust proof passes **23 tests**, including nine unchanged
MSV1 controls. Python/Rust share **138 wire cases / 865 operations**, with
600 accepted fragments, 143 transport-complete frames and 121 rejections.
Cases cover negotiated caps/profiles, malformed/truncated packets, loss/order/
duplicate errors, CRC, frame/epoch wrap, setup replay, core change, timeout,
credit/ACK staleness, queue bounds, padding and commit fences.

Native gateway plus receive storage measures **4,480 bytes**: a 3,048-byte
native gateway, including its two 1,400-byte stages, plus a 1,432-byte aligned
receive allowance. This is x86_64 ABI accounting, excluding stack, socket/pbuf,
RTOS, allocator and driver descriptors; it is not ESP32 heap fit or a measured
DMA-capable allocation. No PSRAM or complete ESP compressed frame is credited.

FIFO queries reject values above the prototype's 2,048-byte capacity. Single-use
credit probes bind epoch/core identity and charge current reservations plus
completions since the observation began. Wrong or duplicate completions cannot
release a new stage. Logical DMA slices exclude alignment padding. After a
commit request, a fresh frame cannot replace its context until the exact
matching ingress commit ACK; display/reference publication is a later gate.

The final native C ABI passes three additional tests. Both static-library and
FFI test compilation pass `-D warnings` with clean logs. Earlier raw warning
and failed attempts remain retained; they are not the selected qualification.

## Live native Rust ↔ FPGA RTL

The C++ bench links the actual portable Rust gateway, gives it actual RTL
free-space, forwards its aligned logical bytes, and retires Rust transfers only
on real simulated hardware ACKs. It holds the Rust commit context until the
actual RTL ingress commit pulse. Separate token namespaces are explicitly
mapped by the test adapter.

The final regression passes **4,423,970 checks over 933,669 simulated clocks**.
FIFO occupancy and reservations each reach their **2,048-byte** bound; descriptor
slots reach **two**. Strict Verilator/GCC builds use no warning suppression.

| Boundary | Result |
|---|---|
| Live callback join | 11 completed ingress transactions, 231,416 exact bytes |
| Live malformed cases | Two rejected frames; zero commits for those frames |
| Live queue behavior | Two native slots; at most 1,956 native reserved bytes |
| Live DMA | 176 transfers; 20 storage-padding bytes excluded from wire |
| Bad software completion tokens | 175 rejected; ownership preserved |
| Open-loop native trace control | 12 transactions, 298,765 bytes, 291 DMA transfers, 19 padding bytes excluded |

Live fixtures include genuine 720×480 JPEG payloads (21,950 and 176,956 bytes),
a 25,496-byte retained CS92 payload under explicit opaque configuration, and
synthetic tail/stress payloads. Synthetic payloads test framing/CRC, not valid
JPEG decoding. Corrupt/truncated trials recover on the **same gateway/session**
with a newer frame ID after actual drain. Two early harness attempts wrongly
retried the retired ID; the native sequence check caught them. The corrected
fixture uses a fresh ID and preserves that rejection rule.

The 50 combined RTL commits include unit, trace and live fixtures. They are
**ingress commits**, not decoded, validated or displayed video frames. The
933,669-clock total mixes scenarios and stalls; it cannot be converted into
complete decode latency, QSPI throughput or 30-fps video cadence.

## Fidelity and next decision

The boundary is synchronous parallel DMA/command input. Actual QSPI pin timing,
CDC, ESP32-S3 instructions, Wi-Fi/lwIP/FreeRTOS, target DMA allocation/arbitration,
continuous display and C2/HUD/root/seal publication are not modeled here. Renode
was not run and no configured ESP32-S3 platform was qualified. This native
Rust/Verilator join is explicitly the substitute, not claimed ESP emulation.

The runtime streaming worker remains MSV1; its body and legacy wire source are
unchanged. No release image or board flash was produced. V97 still needs the
production capability/register adapter, blocked-datagram handling, paced host
and bounded UDP worker, target heap/stack telemetry and actual Sunshine capture/
codec service calibration with input/audio/UI active. A blocked portable API
call cannot backpressure the radio by itself.

Retain the old path and hand off the tested components. See the
[summary](../../experiments/python-gamebub-v97/summary.json),
[protocol and recovery evidence](../../experiments/python-gamebub-v97/protocol/README.md)
and [RTL boundary](../../fpga/experiments/cu66-v97-forward/README.md).
Sustained hardware 30 fps and complete validated FPGA decode below 10 ms remain
open, alongside the earlier full-path and V100–V110 physical gates.
