# CN36: canonical hidden-reference and residual omission proof

This is a new Python research profile, **not firmware or an existing CP34 wire
extension**. Its two causal variants produce the exact same complete normalized
reference and exact same displayed image over both retained 48-frame windows.
The skip variant removes hidden residual coefficients in actual entropy-coded
GM27 inner payloads. An independently decoded CP34 baseline with the same fixed
zero-motion decisions also has identical displayed RGB565 in this campaign.

| 48-frame scene | Matched legacy CP34 bytes | CN36 full bytes | CN36 skip bytes | Skip saving vs matched legacy | Active MSE (all three) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary | 460,410 | 498,396 | 441,520 | 4.1029% | 14.38366067 |
| Complex | 1,106,678 | 1,190,696 | 1,060,332 | 4.1878% | 26.54469598 |

Every complete packet fits 49,152 bytes. Skip maxima are 22,569 / 41,224 bytes.
Its nominal rates at 30 decisions/second are 2.20760 / 5.30166 Mbps; these are byte
arithmetic, not measured physical frame rates. Background16 fits every frame;
background32 is a paired fallback if any of the three packets fails the cap.
Actual packets for every attempted tier are retained, including any losing
trials. Full canonical control resets hidden references to128 and consequently
resends hidden source content: the larger 11.41% / 10.95% savings against that
control must not replace the useful matched-legacy comparison above.

## Exact reference contract

The fixed720×480 YUV420 geometry and opaque HUD rectangles are bound by the
CN36 profile. Only complete aligned8×8 Y/Cb/Cr blocks whose entire reconstructed
RGB support lies under the rectangle union may normalize to128. The frozen
right/below chroma upsampler's support includes an above/left halo; partial
boundary blocks are preserved. There are256Y +19Cb +19Cr safe blocks.

Both variants share each frame's frozen preparation, prediction, qmap and chosen
visible coefficients. Full carries all selected coefficients; skip zeros all64
coefficients in every safe block before entropy coding. Both reconstruct the
GM27 inner payload and normalize the same hidden plane samples to128. Since
inverse transforms are local, all other plane values stay identical; the whole
normalized references match, not only pixels currently outside the HUD.

The new outer header is `struct '<4sBBHIIHH16s16s16sII'`, plus CRC32, totaling80
bytes versus CP34's60. It stores CN36/version1, key/skip flags, epoch25, frame and
reference IDs, fixed geometry, rectangle-profile digest, normalized input/output
reference tags, and exact inner/HUD lengths. Epoch25 permits reuse of the actual
retained HX33 HUD stream; new semantics are identified by CN36, never by
pretending it is an old CP34 packet. Inner GM27 output tags bind its own
pre-normalized reconstruction. The outer tag binds the subsequently normalized
committed reference. CRC, geometry, exact rectangles, IDs, tags, omitted hidden
coefficient grammar and HUD decode all pass before modeled state publication.
This models ordering, not hardware DMA/VSYNC fences or a new ACK protocol.

## Fractional-motion probe

Zero-motion windows alone cannot expose hidden references moving into future
visible prediction. A separate six-frame retained-input probe forces actual
block32 vectors(-3,+1) in half-pel units on its five P frames. Normative frozen
prediction reads hidden reference samples into visible luma at403 destinations
per P frame (2,015 events total). All12 actual full/skip packets decode and still
produce identical whole normalized references and displayed RGB565. Their
nonhidden coefficients also match, while skip hidden coefficients are zero.
This is a controlled prediction/causal equality probe, not searched-motion
quality, rate improvement over the old profile, or representative gameplay.

## Costs and limitations

Primary/complex proof encoder work averages94.38 /124.79ms per frame on this
host. It deliberately pays full frozen encode, parse, extra skip entropy and
reconstruction, both normalization passes, wrappers and every attempted tier.
The separately measured matched legacy encoder averages56.05 /67.69ms. The
proof path is slower: no whole-sender optimization or30fps claim follows.
Fixture/HUD reads, quality/equality assertions and archive I/O are excluded from
those encoder clocks. Receiver service is separately measured; original and
processed standard-codec inputs are not newly encoded here.

CN36 skip omits54,609 /103,846 nonzero coefficients across the scenes, but zero
blocks still consume the existing entropy representation. This is not yet an
implicit sparse-block grammar or an FPGA inverse-transform bypass. Hidden
reference writes and full-frame storage also remain in this Python model.
Root's separately measured precompiled mask plan is not integrated or credited
in these clocks. The two short gameplay windows are reused; no held-out corpus,
ESP32 timing, RF/QSPI/SDRAM arbitration, native firmware or RTL is proved.

The v35 independently searched control summaries are retained only as historical
context. They use different decisions and reference semantics. Equality against
this fixed-zero matched baseline does not guarantee equal quality to those
controls, nor to a future independently rate-selected motion codec. HEVC/AV1
superiority and hardware30fps remain unproved.

## Reproduction

```sh
python experiments/python-game-canonical-v36-study/test_model.py
python experiments/python-game-canonical-v36-study/test_verify.py
python experiments/python-game-canonical-v36-study/verify.py
```

`benchmark.py` regenerates actual compressed packets using retained source data.
The independent verifier imports no new encoder or normalization implementation;
it independently enumerates scalar support and validates packet syntax, causal
references, complete bytes, source hashes, exact HUD and visible coefficients.
Producer source pins intentionally exclude independently maintained verifier
files; the outer v36 snapshot manifest binds final replay files separately.
