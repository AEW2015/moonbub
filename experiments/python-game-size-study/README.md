# Exact GM01 packet-size preflight

This follow-up tests an implementation-specific optimization: decide whether a
candidate fits before building its full Rice strings/packet. It preserves GM01
bytes, quantization and the priority floor. No prior codec/controller source is
modified, and no old module globals are patched.

## Exact length, not an entropy estimate

`coefficient_size()` validates CP02 input and selects the same DC and three AC
Rice parameters as the frozen serializer. It counts each Rice code, DC row reset,
nonzero5-bit run prefix,16-zero ZRL and per-incomplete-block EOB. It includes
DC/AC parameter bytes and byte padding, then applies the identical raw fallback
length (including the tie) and26-byte CP02 header/CRC. No Rice bit strings or
payload bytes are built by this size calculation.

For N blocks, AC bits are5×nonzero count + Rice bits +2×ZRL count +2×(N minus
blocks ending with a nonzero at zigzag63). DC and AC bit counts are byte-rounded
separately. The whole GM01 size includes50 outer header/CRC bytes, the338-byte
map at720×480, and all three complete CP02 payload lengths. This is exact for
this syntax; it is not a statistical predictor of a different codec.

`Encoder.estimate_candidate(prepared,map)` quantizes the existing shared raw
transforms once and retains a read-only coefficient/map plan and exact size.
`emit_sized()` serializes only a fitting plan, reusing its quantized coefficients,
and checks each actual length against the preflight. The emitted object is a
legitimate GM01 candidate registered with that encoder. It retains the original
owner/generation/epoch/credit checks; a stale/foreign/cloned plan is rejected.

The local controller tries one ROI8/background16 map and at most one
ROI8/background32 fallback. It commits only the first fitting candidate.
Rejected previews neither admit a frame nor clear/consume a reference credit.
Normal49152-byte capacity and a separately declared28672-byte pressure case
are used. This is not a relaxed priority floor or an unbounded quality search.

## Actual paired result

Thirty-two independent-key call pairs alternate measurement order: eight seeded
720×480 noise frames, twelve real pressure cases and twelve real normal cases.
The real cases use six predeclared native indices from each existing4-second
source window, reused across the two caps. The noise fixture is separately
labeled. Every selected packet, admission decision and candidate length matches
the full-serialization controller; admitted receiver RGB/hash also matches.
Rejected packets are not emitted. Original native25/29.88 fps, repeated footage
and the independent-key sampling do not prove sustained capture/feedback rate.

| Paired calls | Full serialization mean | Exact preflight mean | Result |
| --- | ---: | ---: | --- |
|8 noise rejects, two attempts|113.48 ms|43.24 ms|61.9% less service, no entropy serialization|
|12 normal real keys|32.66 ms|34.62 ms|6.0% regression|
|6 pressure calls fitting first try|25.45 ms|28.42 ms|11.7% regression|
|6 pressure calls needing fallback|46.47 ms|46.32 ms|0.3% lower; negligible under load|

Thus preflight is **not selected as the default normal path**. Vectorized cost
selection is duplicated by serialization for admitted candidates, so it adds
work when no large candidate is avoided. It helps the very expensive fully
rejected noise inputs, but their mean43.24 ms and maximum46.70 ms still exceed
33.33 ms. The fallback-only branch does not show a meaningful gain. A pooled
pressure mean can hide these branch differences; `summary.json` retains them.

Timing covers map construction, one source/predictor/forward analysis, every
preflight and actual serialization, selection and admitted-key reconstruction.
Source acquisition/scaling, verification/hash oracles, receiver checks, transport
and display are excluded. Host load/frequency/warmup/affinity are uncontrolled.
This is an actual paired Python preparation observation, not concurrent
real-time throughput or a native/FPGA service claim.

The preflight still retains raw analysis, quantized coefficients, map and
vectorized cost arrays. It avoids rejected entropy strings/full packet buffers,
not all host work or receiver reference memory. It makes no hardware buffer,
physical bandwidth, target-fit or worst-case deadline guarantee. A selective
preflight guard based on past pressure is a future policy experiment; it has
not been implemented/qualified here.

## Verification and reproduction

Three tests cover80 sparse/dense/extreme coefficient families (including raw
fallback/DC endpoints), all64 zigzag positions, small actual key/P histories,
exact selected bytes, rejected-state preservation and stale/forged plans.
`verify_prior.py` separately regenerates all72 frozen GM01 packets and checks
their exact prior SHA hashes, then verifies216 parsed CP02 plane lengths against
the exact-size function. This is finite protocol evidence, not formal all-input
equivalence.

Use the common pinned environment and external source media:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify_prior.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python analysis.py
```

`results.json` and `prior-check.json` bind executed code, input manifests and
packet hashes. `summary.json` binds their derived branch analysis. The study
keeps the negative admitted-path timing alongside the rejection gain and does
not change the chosen codec syntax or installed hardware/software.
