# V37 next deployment gates

V37 work is underway on two separate tracks: a direct CN36 sender and a
separate implicit-codec prototype. This document defines the evidence required
before either track can support deployment claims. No V37 results are recorded
here; implementation and measurement are still pending.

## Preserve the CN36 decision contract

Early hidden-coefficient suppression must happen inside the sender's coefficient
analysis and entropy path, without first completing a full encode and then
parsing/rebuilding it. It must preserve the unmasked plane-level rate-distortion
optimization (RDO) decisions and reversion decisions. Masking must not alter
candidate selection, visible coefficients, qmaps, motion vectors, or whether a
plane/block decision reverts. Record and independently verify these decisions
for paired full and skip encodes, including boundary and reversion cases.

## Measure paired end-to-end work

Report complete sender latency for paired full and skip runs under the same
inputs, configuration, quality decisions, and retained causal history. Include
analysis, support-plan use, entropy coding, reconstruction, normalization, and
packet framing in the stated sender scope. Report distributions and per-frame
results alongside totals. Do not infer end-to-end speed from the mask-plan
component's 38.81× ratio, subtract component timings, or extrapolate a component
gain to the sender. Keep receiver timing distinct and state exactly what is
inside every timing boundary.

## Specify and audit implicit fixed-HUD syntax

The separate implicit-codec prototype needs a bounded, explicit grammar for
omitting hidden transform blocks under the fixed opaque HUD profile. Define the
maximum syntax and byte budget, reset/key/reference binding, and malformed-input
behavior. Show that its decoder can identify omissions from the negotiated
profile and packet state without depending on encoder-only state or a side
channel. Measure actual serialized complete packets, including all wrappers and
bindings, and independently decode golden, boundary, reset, and malformed
packets. Keep this prototype's results separate from CN36 until compatibility
and equivalence are demonstrated.

## Close the comparison and deployment evidence gaps

- Compare against original native inputs with a fair, freshly generated native
  encode at matched quality. Apply identical source preprocessing and HUD
  treatment to custom and native paths, include complete-byte accounting, and
  report quality across the same retained content. Existing v36 native replay
  points are not matched-quality evidence and include no fresh native encode.
- Measure actual ESP32 transport behavior under the intended Wi-Fi/QSPI DMA,
  contention, retry, reset, and publication conditions. State payload and
  buffering limits and report sustained delivery and latency; host byte-derived
  Mbps is not device throughput.
- Measure FPGA decoder cycles and resource costs for the proposed skip and
  implicit paths, including entropy handling, inverse shortcuts, normalization
  stores, and memory arbitration. Pixel coverage and host timings do not predict
  FPGA cycles, DSP use, or 30 fps capability.
- Make no HEVC or AV1 victory claim without a matched-quality comparison on the
  same original inputs and scope. V36's sampled standards points are smaller at
  lower mean MSE, so the current evidence does not establish a win.

## V36 numerical baseline and consistency check

The matched fixed-policy v36 table reports CN36 skip savings versus legacy of
4.1029% (primary) and 4.1878% (complex), appropriately summarized as 4.10% /
4.19%. The separate precompiled mask-plan component reports 4.288245 ms versus
0.110502 ms per frame, a ratio of 38.81×; its 4.196960 ms compile cost and
amortized 96-frame result are separately stated. These are distinct metrics and
must not be conflated. The v36 comparison also explicitly says no fresh native
encode was performed and that sampled HEVC/AV1 points are smaller at lower mean
MSE. V37 reporting should retain those baselines and limitations until new,
paired measurements replace them.
