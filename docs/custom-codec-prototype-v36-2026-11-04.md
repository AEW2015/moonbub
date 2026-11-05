# V36: canonical hidden references without skip-induced drift

V36 turns the v35 occlusion hypothesis into a working **new Python codec
profile, CN36**. Its full and skip variants keep identical complete normalized
references and displayed pixels throughout the retained causal histories. Against
a matched fixed-policy legacy baseline, skip saves **4.10% / 4.19% of complete
bytes**, including its larger wrapper, with identical displayed frames on these
two zero-motion-policy clips. A fractional-motion probe also preserves full/skip
reference equality when hidden pixels contribute to future visible prediction.

This is a useful application-specific exactness result. It does not establish
general equality with the old codec, superior HEVC/AV1 compression, an optimized
sender, or physical 30 fps. Geometry remains 720×480 coded / 720×405 active, with
21,120 exact RGB565 HUD words and 49,152-byte complete packet cap. All gameplay
inputs are the same two short retained Mass Effect windows, not held-out content.

## Actual canonical-reference profile

[Implementation and scope](../experiments/python-game-canonical-v36-study/README.md).
Both variants first use identical prediction, qmap and selected visible
coefficients. Full encodes all coefficients; skip sets coefficients to zero only
in complete aligned 8×8 blocks whose entire RGB interpolation support lies inside
the declared opaque HUD. Each decoder normalizes those reconstructed reference
samples to 128 **before committing the reference for future prediction**.

This makes hidden reconstruction differences irrelevant to future predictions:
both committed references are identical, including hidden samples. Source-only
masking in v35 did not provide this property. The frozen chroma interpolator's
support is independently enumerated by the verifier, including clamped edges.
The fixed geometry admits 256 Y and 19 blocks on each chroma plane.

CN36 has an explicit 80-byte wrapper including CRC, profile identity, incoming
normalized-reference tag, committed-output tag and bound GM27/HX33 identities.
Inner GM27/HX33 syntax remains frozen; CN36 changes the reference contract and
must be negotiated as a new profile. It is not compatible with an unchanged
CP34 receiver. Decode stages base, HUD and normalized output before modeled
atomic publication. Independent malformed-packet tests check rejection without
publishing reference state; this is Python behavior, not a hardware fence proof.

Skip emits actual serialized GM27 residual components with hidden coefficients
zeroed. Their zero representation still costs entropy bits. It does not yet have
an implicit omitted-block grammar. Visible coefficient values, qmaps and motion
vectors must remain identical between full and skip; selecting different rate
winners independently would invalidate the equality argument.

## Matched causal baseline and measured rate

The main experiment uses zero motion, block 32, key interval 24 and ROI scale 8 /
background 16, with a common background 32 fallback if needed. Every selected
frame fits at 16; no fallback savings are hidden. Three actual decoded histories
are retained: legacy fixed policy, canonical full and canonical skip.

| 48-frame window | Legacy fixed complete bytes | CN36 full bytes | CN36 skip bytes | Skip saving vs legacy | Active MSE, all three |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary | 460,410 | 498,396 | 441,520 | 4.1029% | 14.383661 |
| Complex | 1,106,678 | 1,190,696 | 1,060,332 | 4.1878% | 26.544696 |

Every displayed frame hash is identical across all three histories on these
zero-motion-policy clips. Peak per-frame MSE is 15.037663 / 28.517118; mean adjacent
frame-MSE change is 0.086852 / 0.362991, identical across variants. Adjacent scalar
MSE change is diagnostic, not a perceptual temporal-quality metric.

CN36 skip maxima are 22,569 / 41,224 bytes. Its budget charges 80 binding bytes per
frame versus legacy CP34's 60. Nominal complete rates at 30 decisions/s are
2.207600 / 5.301660 Mbps, derived from bytes rather than measured transport FPS.

Comparing skip only against canonical full gives larger 11.41% / 10.95% savings,
because full repeatedly encodes hidden residuals against a normalized reference.
Those inflated full-baseline savings are secondary. The matched legacy comparison
above is the useful complete-byte improvement.

The older v35 searched controller is a different policy. Against it, CN36 skip
uses 0.067% more bytes on primary and 0.781% fewer on complex; primary MSE falls
0.0224% while complex MSE rises 0.9155%. Thus the new fixed-policy experiment is
not a quality-neutral replacement for the strongest previous searched controller.

## Nonzero-motion proof and independent replay

A separate six-frame probe applies actual forced [-3,+1] half-pixel block 32
vectors to retained source frames, with five causal P frames. It records 2,015
hidden-to-visible luma sample events. Full/skip normalized references and visible
outputs remain exactly equal at every frame. This is a directed probe, not a
full searched-motion campaign or equality against noncanonical legacy motion.

The independent verifier does not import the new encoder, wrapper parser,
receiver or source-mask implementation. It uses frozen GM27/HX33 decoding,
independent scalar support enumeration and its own CN36 framing/publication.
It checks 288 main causal frames, 96 exact full/skip pairs, 288 actual main candidate
packets, 6,082,560 exact HUD words and 158,455 omitted nonzero hidden coefficients.
The motion probe adds 12 actual frame decodes. Producer tests 3 and independent
verifier tests 5 pass; source pins, actual packets and logs are retained.

## Sender work remains to be removed

The proof encoder first pays for a complete frozen encode, then parses its
coefficients and performs another entropy encode and reconstruction for skip.
This guarantees identical visible decisions, but deliberately duplicates work.
Paid proof encoder means 94.38 / 124.79 ms/frame versus matched legacy fixed
56.05 / 67.69 ms. The proof clock includes analysis, full encode, extra skip work,
both normalizations and both wrappers. Fixture/HUD loading, metrics, equality
assertions and archive I/O are excluded; receivers are measured separately.

Do not treat those proof clocks as an efficient skip implementation or 30 fps.
Hidden 8×8 blocks cover 18,816 of 518,400 planar samples (3.63%). Actual FPGA savings
depend on inverse/zero shortcuts, entropy grammar, normalization stores and memory
arbitration; a pixel fraction alone is not a cycle or DSP saving.

## Separate exact host component: compile the fixed geometry

[Mask-plan experiment](../experiments/python-game-maskplan-v36-study/README.md)
compiles safe blocks into 88 merged row spans once. Across 96 retained frames,
three paired repetitions with alternating order reproduce frozen mask output
exactly. Both paths validate inputs and make owned plane copies.

| Mean of per-frame paired medians | Time |
| --- | ---: |
| Frozen masking, geometry derived each call | 4.288245 ms |
| Precompiled run application | 0.110502 ms |
| Compile once | 4.196960 ms |

The per-frame component ratio is 38.81×; amortizing compilation across 96 frames
gives 0.154220 ms/frame, about 27.8×. A hypothetical packed uint16 run plan is 528
bytes; this is not measured Python tuple memory or new transmitted metadata.
Current owned int16 planes occupy 1,036,800 bytes. These are host allocations,
not ESP32 buffering requirements. Three tests cover unions, holes, interpolation
edges, ownership and invalid inputs. This component has not been integrated into
CN36's measured proof sender or multiplied by v35's map-reuse improvement.

## HEVC/AV1 comparison remains unfavorable

[Retained standards replay](../experiments/python-game-comparison-v36-study/README.md)
freshly decodes 192 existing original-input v35 AUs. **No fresh native encode is
claimed.** PTS/DTS, keys, immediate outputs, exact HUD, output hashes, source
metrics, packet lengths and once-only extradata are checked. CN36 and standards
receive the same original common YUV input; CN36 reference normalization is an
internal codec operation, not a source preprocessing benefit withheld from native.

All budgets below charge 80 binding bytes/frame, actual identical HX33 and native
extradata once. The native 80-byte binding is explicitly modeled accounting, not
CN36 syntax support or a newly generated native wire packet.

| Window / codec | Complete budget bytes | Active MSE |
| --- | ---: | ---: |
| Primary CN36 skip | 441,520 | 14.383661 |
| Primary HEVC q32 | 239,698 | 11.210939 |
| Primary AV1 q48 | 223,411 | 12.248229 |
| Complex CN36 skip | 1,060,332 | 26.544696 |
| Complex HEVC q28 | 607,492 | 22.161878 |
| Complex AV1 q38 | 602,347 | 19.767521 |

All sampled standards points fit the complete frame cap and are smaller at lower
mean MSE. This is not matched-quality BD-rate, perceptual equivalence, an optimal
standard encoder, or equal FPGA resources. We have not beaten HEVC/AV1.

## Next experiments toward an application-specific deployment

1. Integrate precompiled support plans and early hidden-coefficient suppression
   into the actual analysis/entropy path. Preserve selected visible coefficients
   exactly while avoiding the paid full encode/reparse/rebuild. Time the complete
   sender rather than subtracting independent component measurements.
2. Add a bounded implicit hidden-block grammar so an omitted transform need not
   spend zero-run syntax or inverse work. Bind it to the fixed opaque profile,
   preserve reset/key/reference tags and exact-HUD atomic publication, and retain
   independent malformed/golden tests. This is proposed, not implemented.
3. Run canonical full/skip with the real searched-motion controller and a matched
   noncanonical controller. Prove full/skip equality, separately quantify changed
   old-profile quality and test motion crossing opaque boundaries. Extend the
   directed motion probe into long held-out pans, scene cuts and changing HUDs.
4. Seek larger gains from host-generated bounded temporal prediction/residual
   decisions that the FPGA can decode with predictable memory traffic. Credit
   identical application preprocessing and HUD treatment to native anchors.
   Four percent occlusion savings alone cannot close the measured standards gap.
5. Promote only with a measured application objective: complete latency, visual
   quality, decoder memory/DSP/clock and ESP32 transport behavior. Keep host image
   work off the gateway; include Wi-Fi/QSPI DMA, contention, retries, reset and
   publication timing in eventual device qualification. Hardware 30 fps remains open.

[Acceptance checklist](v36-application-codec-acceptance-checklist.md) separates
same-profile exactness, old-profile quality, fair native comparison and physical
deployment gates. JPEG, the v20 hardware handoff and all prior frozen studies are
unchanged. No firmware, bitstream or physical device was modified this iteration.

## Reproduction

```sh
python experiments/verify_prototype_v36.py
```

The portable manifest freezes the v35 inventory except the two mutable indexes,
new producer/source dependencies, actual archived custom packets, code, test
logs, comparison evidence and replay helpers. There are 11 focused passing tests,
300 actual custom frame decodes including the motion probe, 96 exact mask-plan
input/output checks and 192 replayed native AUs. The replay verifies contents and
causal behavior; host timings remain the recorded measurements, not remeasured
speed guarantees.
