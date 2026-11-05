# V57 defined error diagnostics across custom and native frames

This study separates spatial error from coordinate-to-coordinate error changes.
It is not SSIM, VMAF, subjective quality or a validated perceptual flicker metric.
It reuses96 actual source canvases across20 policy/native-anchor cases, producing
480 decoded presentations. Four focused metric tests and independent full replay
pass. All native planes are freshly decoded from archived access units, not
freshly encoded; original source pixels and exact HUD are shared by all codecs.

For every active RGB565-expanded sample, error is decoded minus original. We
record source MSE, the fraction of pixels with a channel error at least16, and
squared error differences between adjacent pixels on/off the8-pixel grid. Both
pixels of a spatial pair must be active and outside the exact HUD rectangles.
Temporal error-change energy is `(error[t]-error[t-1])²` at fixed coordinates.
It removes source signal differences algebraically but does not follow scene
motion; persistent blur can have low error-change energy. Lower values therefore
do not establish less perceived flicker or better gameplay.

Native anchors are selected from actual stored first24 access units under the
fixed-zero mean-MSE plus complete-cap gate, using the sampled V40/V41 grid. They
are not optimized encoder frontiers or every-frame quality matches. Their exact
options, bytes, error records and selection provenance are retained. No new
native encoding or native FPGA decoder is supplied by this diagnostic.

The fixed global-grid and V53 mixed policies increase these error diagnostics
relative to zero in the four tested prefixes. Native anchors generally have
smaller error jumps and fewer bytes. Custom zero has lower coordinate temporal
error-change than native in some clips, but that does not override its larger
bit budget or demonstrate perceptual superiority. All positive and negative
results remain visible rather than reducing quality to one favorable statistic.

Source cadence differs across precompressed clips; comparisons are within each
clip. The study changes no encoded packet, reference, firmware or hardware. The
next display-only filter experiment can evaluate these diagnostics while keeping
canonical references and exact HUD unchanged.

```sh
python -m unittest -v test_model
python benchmark.py
python verify.py
```
