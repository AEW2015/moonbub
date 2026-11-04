# Iteration 15: one application-specific stream, retaining full resolution

The Python prototype now combines acknowledged recent references, GM/SR residual
choice and exact UI patches in **one AR02/GF02/AF02 stream**. The target remains
720×480 coded, 720×405 active and 30 fps. GM plus all four UI patches achieves
150 distinct decoded images in a five-second modeled window. This is a conditional
software result; target hardware, live capture and native 30 fps remain unproved.

## What is implemented

AR02 carries a validated GM01 or SR01 body followed by up to four length-prefixed
HP01/HR01 exact RGB565 patches. Its 65-byte envelope and all patch prefixes count
toward the 49,152-byte complete-frame cap. AF02 feedback binds the outer body CRC
and the actual published YUV bank/frame/tag. Selected display patches never enter
YUV prediction state. CRC and hashes detect mismatches; they do not authenticate.

A single analysis and three forward transforms produce the GM coefficients.
Exact mode reuses those coefficients and actual GM dense CP02 bodies, encodes real
SR zero/DC/full alternatives, pays all losing work, then chooses the shortest
complete inner body with GM fallback. This minimum does not compare different UI
coverage or different reference histories. Zero/DC inverse bypass is used on both
sender promotion and receiver reconstruction. Key bank 0 and recent bank 1 use
content-bound ACKs and explicit bank-specific read/write leases; uncertain/lost
promotion feedback cannot publish a usable future reference.

The UI selector supports four-entry region caching with exact source RGB565
comparison. It validates every patch before reference publication. UI is exact
only in selected original RGB565 words; the game background remains quantized.
Configured rectangles are not automatic HUD discovery.

## Measured results

| Same-input, same-reference base comparison | GM mean complete bytes | Exact mean complete bytes | Reduction |
| --- | ---: | ---: | ---: |
| Combat, 60 IDs | 6,640.30 | 6,326.15 | 4.73% |
| Second scene, 60 IDs | 8,734.90 | 8,646.27 | 1.01% |
| Held-out second scene, 180 IDs | 8,803.23 | 8,727.29 | 0.86% |

All 300 native base IDs have identical source/reference choices, base/display
hashes and quality metrics in GM versus exact mode. Forty-five canonical stored
YUV tags are also observed identically by their following P consumers. Exact is
lossless relative to corresponding quantized GM, not original-source lossless.

The integrated held-out 180-ID full-UI experiment is:

| Profile | Strict / eventual presentations | Diagnostic IDs/s | Mean preparation / decode ms |
| --- | ---: | ---: | ---: |
| GM + UI | 175 / 178 | 30.0 | 29.782 / 24.947 |
| Exact GM/SR + UI | 169 / 172 | 28.8 | 33.512 / 24.572 |
| Prune-4 + UI | 126 / 129 | 21.6 | 44.976 / 19.827 |
| Exact + UI + full refresh every 30 IDs | 155 / 157 | 26.0 | See retained stage trace |

GM+UI presents IDs 12–161 in [500,5500) ms: 150 distinct source hashes and 150
distinct decoded image hashes. Startup IDs 1 and 2 are the only drops. Every
decoded UI frame selects all 21,120 original RGB565 words with zero mismatch.
The other finite profiles admit different IDs/references, so their aggregate
bytes are not matched compression comparisons. Earlier v14 savings are not added
or multiplied into these results.

UI caching helps when regions repeat: combat selector time falls 6.028→1.695 ms,
but the distinct second scene shows essentially no benefit. The 84,592-byte peak
persistent host cache excludes Python objects and transient storage. A noisy
synthetic UI case pays for and rejects the fourth rectangle under a 32,768-byte
UI-only budget; coverage falls to 15,360 words. That isolated UI budget is not the
whole AR02 cap or a throughput result.

Prune-4 remains an explicit lossy option: its four-level YUV bound is against
quantized GM using the same current predictor, not original source or another
stream's evolving history. Protected chroma halo handling is retained. It reduces
bytes but adds enough host work to hurt cadence here.

## Negative result: fixed sparse-coefficient gate

A fixed 0.90 threshold samples at most 64 quantized blocks per plane after GM
analysis and enables SR only when all three planes are sufficiently zero/DC-only.
It never enables SR on 174 evaluated preparations and adds 0.107 ms each.
Separately executed exact controls, matched by source/reference/GM length, show
79 actual SR wins totaling 19,400 inner bytes. Those are control measurements,
not estimates of candidates the gate did not encode.

The final 60-ID validation split begins at 10.04 seconds: PTS 120000–144000,
strictly beyond the earlier window's last PTS 119600, with 60 distinct hashes and
no hash overlap. The threshold was fixed before this split. GM/exact/gated all
deliver 58 eventual frames there; exact saves only 5.19 bytes/frame while adding
about 3.71 ms preparation. Keep this gate as a negative experiment; **GM + exact
UI + recent references is the simpler current port candidate**.

## Evidence and reproduction

- [Unified codec](../experiments/python-game-unified-codec-study/README.md):
  1,020 decisions, 1,002 admissions and 18 paid over-cap rejections; 10 tests.
- [UI contract/cache](../experiments/python-game-unified-ui-study/README.md):
  160 paired IDs, 1,280 rectangle attempts across both variants; 8 tests.
- [Finite unified stream](../experiments/python-game-unified-stream-study/README.md):
  14 cases, 1,248 captures, 1,154 preparations, 1,152 commits; 11 tests.
- [Fixed gate](../experiments/python-game-cadence-gate-study/README.md):
  9 cases, 540 captures, disjoint validation and matched actual controls; 15 tests.
- [Independent audit](../experiments/python-game-audit-v15-study/README.md):
  all four studies verified; 5 audit guards.

There are 49 passing recorded tests and 94 executed-source hash bindings across
four runs. Run `python experiments/verify_prototype_v15.py` with the project's
NumPy/Pillow/PyAV environment to check the retained snapshot without rerunning
performance measurements. External media are hash-pinned but not redistributed;
the aggregate reports missing files rather than claiming a media recheck.
`prototype-v15-provenance.json` inventories evidence and paired Sunshine docs.

Costs are measured Python service on independently serialized virtual servers,
with assumed 8 Mb/s forward/reverse, 160 Mb/s QSPI, 10 ms feedback and 60 Hz
vblank. Sources are precompressed 25/29.88 fps files, preloaded offline and
hypothetically scheduled at 30 IDs/s; actual BOX scaling is charged. This is not
live 30 Hz acquisition, shared native CPU concurrency, RF, QSPI framing, external
memory arbitration or scanout proof. Two logical reference banks, three sender
slots, two ingress slots and three framebuffer roles exclude codec/UI scratch,
outputs and copies. Python banks are int16, twice logical 8-bit YUV storage.
Initial-key-only success is not a production refresh/loss-recovery qualification.

## Next implementation gates toward an application-specific codec

1. Freeze a small AR02 profile and export bounded golden vectors: complete wire
   packets, canonical YUV banks/tags, exact UI RGB565 and expected feedback. Add
   corrupt/truncated patches, wrong tag/CRC, late ACK, full ingress and recovery
   vectors. Start with GM+UI; retain optional exact SR as a separately negotiated
   rate/CPU choice. Installed JPEG/GM01 peers cannot accept AR02.
2. Port the decoder and host encoder to native code against those vectors. Keep
   capture, compression, transport, ESP32 gateway and FPGA decode independently
   measurable. Use the same integer transform/quantization/clamp and source tags;
   do not substitute display RGB hashes for reference identity.
3. Add a bounded cycle/memory model driven by actual AR02 traces: coefficient
   parsing, zero/DC bypass, fixed-point inverse transforms, upsampling, UI mux,
   reads/writes, display deadlines and feedback. Count actual storage, port
   conflicts, burst overhead and worst-case dense bodies. Map regular inverse
   transform multiply/accumulate work to FPGA DSPs; quantify this before RTL fit
   claims. Keep the ESP32 primarily a bounded transport/control gateway.
4. Qualify periodic refresh and fault recovery at 30 fps before production use.
   Full-key-every-30 currently falls to 26 modeled IDs/s. Test bounded refresh
   slices or bank-local refresh without weakening prediction/ACK correctness.
5. Broaden held-out gameplay and camera/UI motion before further policy tuning.
   Revisit SR selection only with causal measurable predictors that recover real
   byte wins without erasing encoder slack. Compare quality, matched input IDs,
   worst-frame latency, memory and full wire bytes together; avoid a smaller
   resolution or fewer distinct frames masquerading as a 30 fps improvement.

The paired branches are `handoff/gamebub-app-codec-v15-20261103` in Moonbub and
Sunshine. This publishes research/handoff artifacts, not a deployed native mode.
