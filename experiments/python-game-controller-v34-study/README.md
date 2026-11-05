# Actual hierarchical frames and atomic exact-HUD composition

This host Python study integrates actual **GM34 + CP34 + HX33 + JA34** packets.
GM27 base packets remain a fallback. All three policies retain 720×480 coded /
720×405 active geometry, exact 21,120-word HUD, keys 0/24 and a 49,152-byte cap.
Each policy maintains its own accepted decoded base/HUD history and bank slots;
execution order rotates per source. No live negotiation, native device, FPGA
programming, physical timing or 30 fps result is claimed.

## Frame and publication contract

GM34 reuses the 76-byte GM27 header and four-byte CRC (80 bytes combined),
with magic `GM34`, version1, P flag0,
block size16 and ±18 half-luma-unit limit. Its vector-length field declares the
actual bounded HM34 component. Qmap and residual payloads stay unchanged; CRC
covers the complete new frame. Keys retain ordinary independent GM27 frames.
Every legacy child and GM34 alternative is serialized and archived, including
losing alternatives. HM34 is prepared once per source and reused for the child
incumbent/band variants; its packing and independent validation are charged once.

The receive adapter decodes HM34 with the independent syntax-only parser, emits
the frozen **literal raw-vector grammar** privately, and uses the exact frozen
prediction/inverse/tag checks. It never calls the motion encoder, canonical
minimum-size search or rate oracle. The compatibility packet is private host
scratch, not wire bytes. Its length is bounded by wire bytes plus 2,701 bytes;
the Python process also materializes vectors, coefficients, pixels and expression
temporaries. This is not a streaming RTL architecture or a fitted memory claim.

CP34 uses the existing 60-byte composition overhead with new profile magic.
It binds exact component lengths/SHA-128 digests, canvas, epoch/frame/reference
identities and ping-pong slots. Published frames only are accepted. HU25/HX32/
HX33 patch grammars remain supported, but **total HUD words are explicitly bounded
to 21,120**. Inner patch geometry is checked before any allocating legacy decode.
This makes the fixed-HUD payload bound explicit: 42,240 bytes per reference or
staging bank, unlike the generic legacy full-canvas domain. FIFOs, lookup tables,
DMA, compatibility scratch and implementation overhead are additional.

Receiver validates both staged outputs and constructs a tag-bound JA34 ACK before
the modeled publication. CRC/length/SHA errors, bad references, late HUD failure,
missing write-drain/vblank gates, stale frames and wrong slots leave receiver
state unchanged. Gates are synchronous host booleans, not simulated hardware
fences. Replay is rejected; live ACK retry/reconnection handling is not implemented.

## Policies and measured results

The control integrates v33's shared incumbent/band encoder pair into the complete
selector. All 96 selected legacy base packets and source metrics match v33
exactly. The previous same-HX33 byte budgets are now actual accepted Python
CP34 streams. Preencoded HX33 creation is still excluded from source timing.

Both hierarchy policies pay the same full control candidates as a shadow on
their **own** current reference, then add child16 incumbent/band variants and
their actual GM34 wrappers. A child must fit, save complete bytes strictly, and
have actual active RGB SSE no higher than the fitting control winner. Stable
ties retain control. The full policy uses v33 refinement; select25 uses the
predeclared 25% quota. Fixed-reference training outcomes did not choose that quota.

| Window | Policy | Actual complete bytes | Active RGB MSE | Paid policy ms/frame | Child / GM34 selections |
| --- | --- | ---: | ---: | ---: | ---: |
| Primary | Control | 441,224 | 14.386886 | 227.99 | 0 / 0 |
| Primary | Full hierarchy | 439,457 | 14.380495 | 410.34 | 19 / 19 |
| Primary | Select25 hierarchy | 441,224 | 14.386886 | 408.66 | 0 / 0 |
| Complex | Control | 1,068,678 | 26.303889 | 323.09 | 0 / 0 |
| Complex | Full hierarchy | 1,058,551 | 26.370030 | 574.79 | 28 / 19 |
| Complex | Select25 hierarchy | 1,066,019 | 26.382721 | 565.04 | 12 / 12 |

Full hierarchy saves 0.4005% / 0.9476% complete bytes versus the independent
control. Primary MSE falls 0.0444%; complex MSE rises 0.2514%. Select25 has no
primary gain and complex bytes fall 0.2488% while MSE rises 0.2997%. Local strict
guards cannot guarantee aggregate equal-quality across different future histories.
All 38 selected GM34 frames and nine selected legacy child frames are retained.
Do not promote these small gains as a default at their substantial extra host cost.

Control selected decoder predictions read 26,053,120 / 33,489,152 logical samples;
full hierarchy reads 26,137,984 / 33,626,368. These small increases are a resource
trade-off, not a bandwidth/latency win. Logical counts do not measure bus traffic,
cache behavior, physical RAM, power or routed clock.

## Paid work and reproducibility

Paid policy time sums all analyses, shared-pair calls once each, HM34 preparation
plus syntax validation once, all wrappers, every RGB quality score, component
binding/preflight and actual selection. Every losing frame is constructed.
All 748 shared pair groups produce 1,496 legacy frames and 368 actual GM34
wrappers: 1,864 candidates total. HUD generation, fixture read/conversion, offline
debug decoding, archive compression, receiver service, network and display are
separately excluded. Receiver mean time is separately retained. All Python
policies remain far above a 33.33 ms source period.

Nine focused tests check actual CP34/HX33/GM34/ACK exchange; literal-adapter
receive without encoder calls; CRC/length/profile errors; bad bank/reference/
output tags; late HUD failure; gates, replay and ACK binding; large/mismatched
inner HUD geometry rejection before pixel decode; strict integer guards and
complete unique cohort matrices. Verification checks all actual candidates and
288 accepted causal frames, repeats 184 child searches and HM34 encodes, compares
6,082,560 HUD words, and reconciles source hashes, pixel metrics, counts and costs.
The verifier uses explicit module loading to avoid historical basename imports;
its pin was refreshed after that replay-only import fix, with numerical results
and producer code unchanged.

```sh
python -m unittest discover -s experiments/python-game-controller-v34-study -v
python experiments/python-game-controller-v34-study/verify.py
```
