# CS88 mixed arithmetic/plain-Rice packets

CS88 keeps the quantized 720×480 coefficients, prediction, grouped COPY map,
QM87 quantizer cache, HUD and C2 commitments unchanged. Its new four-byte frame
magic is `CS88`; version and 128-byte envelope field layout remain unchanged.
Each residual chunk can contain either the existing `AB38` arithmetic format
or the new `BR88` plain bounded-Rice format. Chunk directories still transmit
block count and exact byte length. The native receiver dispatches on chunk
magic and reconstructs pixels directly.

This is an explicit research profile requiring negotiation and a new target
decoder. Existing CS87 receivers reject it; no FPGA or ESP32 implementation is
included. The C2 content/HUD commitment domain is intentionally retained. CRC
checks detect errors and do not authenticate a sender.

## Actual complete-packet tradeoff

All five policies pass 457 sources through independent native receiver
histories: **2,285 packets** reproduce the qualified coefficients, canonical
pixels, semantic HUD, rendered RGB565, C2 root and frame seal exactly. The
comparison preserves existing quantization; it introduces no additional image
loss. Application byte counts include framing, maps, quantizers, directories,
entropy streams, HUD and CRCs. Link overhead is excluded equally.

| Policy | Corpus bytes | Change versus CS87 | Adaptive decisions removed | Frames within 49,152 B |
|---|---:|---:|---:|---:|
| AB38 control | 7,784,499 | 0 | 0% | 457/457 |
| Minimum bytes | 7,781,672 | −0.04% | 0.47% | 457/457 |
| Feedback policy, 5% per-frame budget | 7,877,561 | +1.20% | 26.15% | 457/457 |
| Feedback policy, 15% per-frame budget | 8,273,629 | +6.28% | 96.16% | 457/457 |
| All BR88 diagnostic | 8,323,868 | +6.93% | 100% | 456/457 |

Whole-plane coding has three chunks per source, so the host enumerates all
eight AB38/BR88 combinations. Byte-minimum chooses complete bytes, then fewer
remaining adaptive decisions, then the lower mask. Feedback policies minimize
remaining observed adaptive decisions under a per-frame budget of
`min(49152, floor(CS87_bytes × 1.05 or 1.15))`; ties prefer smaller complete
packets, then the lower mask. A policy's corpus increase can be much smaller
than its individual-frame allowance.

The 15% policy switches 1,359 of 1,371 chunks, leaving 1,444,956 adaptive
decisions and 1,042,137 renormalizations. It parses 36,211,863 plain Rice bits.
All-BR88 removes 37,656,819 adaptive decisions and 33,238,189 renormalizations,
but still parses 37,656,819 plain bits. Its maximum packet is 49,779 bytes,
which exceeds the old limit by 627 bytes on one source. The 15% policy's maximum
is 48,744 bytes. These are corpus observations, not general packet-size bounds.

## What this changes in a prospective FPGA

BR88 replaces probability updates, interval multiplication and renormalization
feedback with bounded unary/remainder parsing. A run symbol requires at most
39 bits, a level symbol at most 27, and a DC symbol at most 29. Those are grammar
limits, not cycles. A prospective decoder could use leading-zero detection,
shifts and counters, leaving DSP resources for dequantization and inverse
transforms; fit, clock and throughput still require RTL measurement.

The policy is **not a calibrated decode-deadline optimizer**. A plain bit read
is not free, extra bytes affect ingress/fetch, and variable-length symbols need
bounded storage and ordering. Old arithmetic timing counters cannot be deleted
from V87 to manufacture a BR88 latency. Collect actual BR88 per-tile/context
arrivals and couple them to memory, transforms, hashing and consumers first.

Both component encodings are prepared offline before selection. This campaign
does not measure live host encoding, ESP32 execution or a sustained 30-fps
pipeline. A live encoder needs candidate-generation cost, allocation limits and
transport admission in its policy.

## Verification

The [native packet campaign](../../experiments/python-gamebub-v88/wire/results.json)
retains per-packet identities, components, decisions/renormalizations/plain bit
counts and candidate masks. The
[independent packet reconstruction](../../experiments/python-gamebub-v88/packet-audit.json)
rebuilds **all 3,656 candidate packets**, checks all 2,285 selected hashes and
matches 35 retained fixtures. It uses separately written frozen map/quantizer
builders and never calls the CS88 producer's candidate or selection functions.

The [independent policy audit](../../experiments/python-gamebub-v88/wire-audit.json)
checks argmins, budgets, tie breaks, complete-byte sums, source identities,
native parity fields, source/artifact pins and all fixture CRCs. The
[20 native protocol checks](../../experiments/python-gamebub-v88/wire/tests.json)
exercise inner BR88 grammar/CRC errors, wrong frame profile, outer CRC,
rejection/retention/recovery/replay and mixed coding histories. A syntactically
valid coefficient mutation is rejected at the reconstructed content root.
The separate [BR88 study](entropy.md) adds 35 cross-language grammar checks.

An initial receiver compile failed on a local variable name collision; its
source and failed compiler receipt are retained in the unselected attempt.
The selected campaign compiled successfully and all five receivers exited zero.

```sh
python3 scripts/cu66-v88/run_wire.py
python3 scripts/cu66-v88/test_wire.py
python3 scripts/cu66-v88/audit_wire.py
python3 scripts/cu66-v88/verify_packets.py
```

The native tools use the existing `gamebub-cu66-v69-build` Docker container.
The research receiver's 2-MiB cap and whole-frame allocations are host software
choices, not target memory limits. Hardware 30 fps, complete validated decoding
below 10 ms and HEVC/AV1 rate-quality superiority remain unproven.
