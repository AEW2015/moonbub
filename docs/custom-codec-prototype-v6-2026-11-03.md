# Iteration6: key preparation, measured services and exact arithmetic

This continues the [iteration5 Python plan](custom-codec-prototype-v5-2026-11-03.md).
It removes avoidable keyframe work, replaces scalar encoder timing with actual
selected-packet service observations, and tests arithmetic widths and entropy
loops. Packet syntax and reconstructed pixels remain the frozen reference on
the tested paired inputs. These are Python experiments; the new methods are
not installed Sunshine/ESP32/FPGA modes or physical30 fps qualification.

## Keyframes: keep predictor reconstruction, defer verification

The [key preparation study](../experiments/python-key-prepare-study/README.md)
combines the faster CP02 serializer with lazy key RGB verification. A future
predictor still needs reconstructed YUV; only the optional host RGB/hash oracle
is deferred. Newly owned reconstructed planes are frozen read-only directly,
avoiding another full snapshot copy. The previous lazy-P implementation is
retained, and key ACK/expiry/refresh rules remain unchanged.

Across24 independent keys, mean preparation falls **90.29→33.27 ms (2.71×)**
versus the iteration5 key path. Median34.15 ms and p9536.00 ms still miss the
33.33 ms frame budget:12/24 keys exceed it. Separate mixed runs have key means
44.11 ms for combat and32.76 ms for the second clip, demonstrating why the
independent-key mean cannot be substituted for every packet's service.

The benchmark records96 triples (72 mixed key/P and24 independent keys), each
checking original MA01, iteration5 and new key-preparation wire bytes plus the
frozen receiver's RGB hash. Cyclic variant order reduces order bias, but host
load, warmup and CPU affinity are uncontrolled. Source acquisition/scale,
verification, receiver, network and presentation are outside preparation timing.

Independent key stage means are5.85 ms color/prediction,8.71 ms transform and
quantization,12.92 ms entropy,5.71 ms required reconstruction and0.02 ms packet
assembly/state. One persistent Python int16 YUV anchor remains1,036,800 bytes
per endpoint. A lazy key oracle needs no compressed key cache; P verification
still retains bounded host packet references until ACK/expiry. Source,
prediction, coefficient and reconstruction/oracle temporaries are additional.

## The finite model now pays observed preparation costs

The [measured-service model](../experiments/python-measured-service-study/README.md)
times each actually selected preparation and schedules its serialized encoder
stage with that duration. It re-encodes after capture replacement against the
actual ACKed immutable anchor. Verification starts after the preparation timer.
Two receiver modes either charge the declared8 ms service or the observed
per-packet Python receive duration. Output is held until virtual completion;
commit/ACK/display cannot occur at the earlier offline measurement call.

All profiles use quantizer8, zero motion, two packet slots/credits, three logical
framebuffer roles, one replaceable waiting capture and refresh after30 capture
IDs. Earlier models' global-motion rates are not directly comparable. Ideal
8 Mb/s network,160 Mb/s QSPI,10 ms feedback and60 Hz presentation remain
assumptions; source capture/scale, RF/feedback overhead, physical memory and
true concurrent endpoint execution are absent.

| Primary60 / receive service | Original diagnostic IDs/s | Fast P | Fast key+P | New strict / eventual |
| --- | ---: | ---: | ---: | --- |
| Combat / assumed8 ms |15|26|28|55 /56|
| Combat / measured Python |14|22|24|47 /49|
| Second clip / assumed8 ms |14|27|29|55 /57|
| Second clip / measured Python |13|20|21|42 /44|

Every case preserves strict `[0,2000)` ms, diagnostic `[500,1500)` ms, then
1,000 ms drain. No window is shifted to pass. The12 cases perform519 actual
preparations and519 hash-checked commits; slots, credits, waiting work and
capture dispositions drain. None reaches even30 diagnostic IDs/s. These are
observed Python services replayed offline into assumed stages, not concurrent
wall-clock streaming throughput or native/FPGA timing measurements.

Measured receive costs expose a second limit: new-profile Python P receive
means are25.78/33.01 ms in the assumed-receiver cases, instead of8 ms. With
observed receive charged, diagnostic rates fall to24/21 and strict-window p95
presentation ages reach111.7/116.7 ms. The runs select different source IDs and
packet histories, so comparing their pooled quality is not an equal-quality
codec ablation. The audit reports common IDs and their MSE separately.

Six injected-clock tests still execute actual small packets and verify7 ms
preparation,11 ms receive, exclusion of a900 ms verification oracle, capture
replacement, loss/corruption, paid cap rejection and finite ownership. This
validates service accounting, not physical scheduling, DMA, memory or CDC.

## Exact arithmetic widths: useful bounds, little Python speed gain

The [arithmetic study](../experiments/python-arithmetic-study/README.md) derives
conservative Q14 intermediate bounds and tests an exact int32 host fast path.
Forward residuals ±255 need at most25/26 signed accumulator bits. Full legal
inverse syntax has dequantized inputs ±522,240 and needs36/37 accumulator bits;
it must retain the wider fallback. A conservative absolute dequantized cutoff
of18,779 permits the int32 inverse path. Frozen rounding and clipping remain.

The constants need14 signed bits, while full-domain inverse data operands need
20/22 bits. AMD's DSP48E1 has a signed25×18 multiplier and48-bit accumulator;
these arithmetic widths are compatible by assigning data to the wider port.
This is a width-compatibility inference, not an RTL schedule, one-DSP claim,
resource count or clock result. The primary source is
[AMD UG479](https://docs.amd.com/api/khub/documents/gu4oRPFEh_Pm2uaAlfY6Kg/content).

Forty-eight paired stage checks cover eight source capture IDs, two quantizers
and three repetitions; coefficients, YUV, complete key bytes and decoded RGB
match. Transform+inverse mean time only improves17.17→17.04 ms and18.50→18.16 ms
(0.8%/1.9%). The inverse alone gets slightly slower because range checks and
casts add work. Sampled dequantized values peak at1,024, so they do not exercise
the wide fallback; explicit extreme-syntax tests do. This is retained as a
negative performance result and useful precision evidence, not an integrated
host optimization. No full-key gain is inferred by subtracting stage times
from an unrelated run.

## Entropy token lists: a useful additional key-path optimization

The [token entropy study](../experiments/python-token-entropy-study/README.md)
converts AC positions, values, bands and block indices to Python integer lists
once per plane, and caches the sixteen run prefixes and four ZRL strings.
This removes repeated NumPy scalar conversions and formatting in the hot loop.
Quantization, Rice selection, RAW fallback, complete packets and pixels match
the frozen decoder on the tests. Extra lists are transient host allocations,
not a receiver memory reduction or DSP optimization.

In a new same-run paired comparison,72 entropy-plane samples improve
**4.30→2.43 ms mean (1.77×)**. Twenty-four whole-key pairs improve
**33.18→27.67 ms mean (1.20×)**, median32.55→27.08 ms. Keys above33.33 ms drop
7/24→2/24, but p95 is still33.35 ms and maximum35.85 ms. Keep the tail visible:
there is no passed per-key33.33 ms guarantee or end-to-end30 fps qualification.
These sequential benchmarks have uncontrolled host load; do not infer a
cumulative speedup by dividing timings recorded in different runs.

The local token key encoder changes only key serialization; P frames still
use the iteration5 path. No old module globals are patched. Twenty-four complete
key pairs and72 entropy-plane pairs are byte-identical, with whole-key RGB/hash
checks. Three tests cover80 coefficient families, all64 zigzag token positions,
quantizers1/8/16/32/128, global motion, key/P and forced refresh.

Four additional service replays use this encoder with real selected-frame
preparation/receive calls. Combat strict/eventual counts are55/56 with assumed
8 ms receive and46/48 with observed Python receive; the second clip is55/57
and41/44. Diagnostic counts remain28/24 and29/21 respectively. All resources
drain. These unpaired service runs have different wall costs and selected
histories; they do not demonstrate a controlled FPS gain versus the earlier
encoder. They demonstrate that the faster key path still does not close the
whole pipeline's cadence/latency gates under the stated model.

## Reproducibility and next work

Twenty-eight new tests pass: five key preparation, six measured scheduler,
eleven arithmetic (including four independent review checks), three entropy
and three audit-helper tests. The twelve main model cases plus four token
cases are actual re-encoding/decoding runs, not additional unit-test counts.
Results, commands, source/input hashes, versions and test logs are in the
component folders. The [independent evidence audit](../experiments/python-evidence-v6-study/README.md)
checks seven stored result artifacts, input pins and per-packet key/P summary
statistics, separating strict, diagnostic and eventual counts and comparing
quality on common presented IDs. The [final snapshot](prototype-v6-provenance.json)
binds this iteration; snapshots apply to their recorded checkout state.

The same short, related, already-compressed Mass Effect sources remain native
25/29.88 fps, letterboxed to720×480 and scheduled at hypothetical30 capture
IDs/s. Repeated content is explicit. Main60-frame primary windows do not cross
the4-second held-out boundary. Ninety combat-primary frames would overlap it,
as the previous audit established. These improvements are not broad game,
visual quality or native30-distinct-frame/s evidence.

Next steps, preserving the JPEG hardware control:

1. Prototype a bounded word/window-based CP02 bit reader and batch coefficient
   decode in Python, comparing exact output **and malformed-packet rejection**
   against the frozen parser. Measure receive components before selecting a
   decoder optimization. Decoder speed and reference-memory service are now
   visible limits; encoder means alone cannot establish30 fps.
2. Combine token key preparation with the reference-only asynchronous refresh
   protocol under measured per-call services. Charge the second key decode,
   retry/retirement traffic, old-reader drain and extra reference memory. Keep
   a bounded packet lifetime; do not credit reference-only keys as display FPS.
3. Measure long, varied native capture with source scaling and a declared
   quality floor. Repeat controlled timing under stable load, retain service
   tails and same-ID quality checks, and add long cut/loss/recovery campaigns.
4. Couple the selected decoder to explicit physical reference/scanout memory
   traffic and a source-bound RTL/native schedule. The arithmetic widths are
   a starting contract, not proof of DSP count, target fit or bandwidth. Close
   the existing1,800-distinct-frame model and physical10-minute30 fps gates
   before a production handoff or hardware throughput claim.
