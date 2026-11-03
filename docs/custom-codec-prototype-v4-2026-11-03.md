# Iteration4: actual re-encoding inside capture and feedback timing

This continues the [iteration3 codec plan](custom-codec-prototype-v3-2026-11-03.md).
The previous temporal results measured packets with immediate ACK. This
iteration selects captures in a timed model, **actually re-encodes after
skipped inputs**, checks decoded pixels, and applies feedback, cap and refresh
rules. It also compares a bounded immutable-anchor overlap policy.

The result is stronger algorithm/model evidence, not hardware30 fps. The
reference Python program is slower than real time; virtual native/FPGA service
times remain assumptions that must be measured in an implementation.

## What ran

* [Coupled MT02 stop-and-wait](../experiments/python-coupled-study/README.md):
  sixteen actual-codec scenarios, plus four decoder/cut/noise sensitivity cases.
  One replaceable capture slot and one ACK-waiting transaction; timeout work
  physically drains before new independent admission. Terminal capture
  outcomes are independently checked and disjoint.
* [MA01 immutable anchor](../experiments/python-anchor-study/README.md):
  sixteen actual-codec scenarios, plus three slower-decoder cases. Each P names
  one fixed ACKed key anchor, allowing two bounded P credits/packet slots and
  three logical framebuffer roles. P ACKs release credit without changing the
  anchor; refreshing a key waits for old credits to drain.
* [Reference service measurement](../experiments/python-service-study/README.md):
  actual Python encode/decode costs on this host, separately from virtual costs.
* Independent half-open presentation, ID/conservation and synthetic source
  checks. There are **32 new passing tests**: nineteen coupled/validation/stress
  and thirteen anchor/protocol/finite-stage tests. The39 actual-codec scenarios
  include declared negative conditions, not39 successful rate qualifications.

The normal video cases use60 consecutive decoded frames from each existing
Mass Effect file at starts1 s/4 s. Both models verify the same source/PTS/canvas
hashes. Unique-image counts are32/60 and60/60 in primary windows,51/60 and60/60
held out. These are two related, already-compressed source files at25/29.88 fps,
scheduled at hypothetical30 capture IDs/s. There is no interpolation or native
30-distinct-frame/s capture claim. The longer held-out window reveals cap
failures absent from the earlier30-frame sample.

## Conditional rate and feedback results

Virtual defaults are2 ms preparation, ideal8 Mb/s network,160 Mb/s QSPI,
8 ms receiver reconstruction,60 Hz vblank,48 KiB packet cap,200 ms timeout
and a periodic key after30 capture IDs. Network accounting adds40 application
and28 IPv4/UDP bytes per1,024-byte payload. RF/link framing, feedback/control
bytes, retries, audio/input, source capture/scale and actual memory service
are excluded. These service constants are not measured Python or FPGA timing.

Every60-input video case has strict window `[0,2000)` ms, separately declared
diagnostic window `[500,1500)` ms, then1,000 ms drain. The diagnostic window
is only one second: one boundary frame changes its count by1 ID/s. It cannot
establish sustained cadence. No window was moved to improve a failed result.

At20 ms feedback, fixed-q8 cases have these diagnostic results:

| Exact input cohort | MT02 chain IDs/s | MA01 anchor IDs/s | MT02 eventual/60 | MA01 eventual/60 |
| --- | ---: | ---: | ---: | ---: |
| Combat primary | 27 | 29 | 54 | 58 |
| Second clip primary | 25 | 29 | 51 | 59 |
| Combat held-out | 20 | 27 | 36 | 47 |
| Second clip held-out | 24 | 29 | 49 | 59 |

The [comparison artifact](../experiments/python-coupled-study/comparison.json)
checks fourteen matched input/service comparisons using an independent metric
helper. It records quality, actual selected IDs and transmitted bytes.
Different reference policies produce different pixels and may select different
IDs, so these are not matched-perceptual-quality compression comparisons.
Anchor fault cases also have NACK feedback on decode rejection; stop-and-wait
waits for timeout, so their fault totals must not be credited solely to anchors.

At0/10 ms feedback, some primary/second-clip cases count30 IDs/s in the short
diagnostic window. Primary MT02 combat counts29 despite all60 eventually
presenting. MA01 fixed-q8 counts range27–30 across the baseline; none of this
repairs a failed strict count or proves a general30 fps guarantee.

## The size-cap and quality tradeoff

Held-out combat has real oversize packets in both models. Fixed MT02 has9/8
cap rejects at0/10 ms feedback, with47/44 eventual presentations. A next-capture
scale ladder8→16→32 reduces cap rejects to one and increases totals to54/49.
Diagnostic rates remain28/25. Presented-scale counts use only8 and16, and
pooled presented PSNR falls from36.21/36.17 to35.87/35.88 dB over different
selected subsets. There is no same-frame retry, unbounded quality search or
quality restoration in this short policy.

For MA01, fixed held-out combat presents48/48, with9/9 cap rejects and a27
diagnostic rate. Backoff plus drained-key refresh presents55/54 and reduces
cap failures to one, while the diagnostic rate stays27. Presented-ID PSNR
changes36.08→35.74/35.76 dB. Actual sent bytes increase because more captures
are admitted; this is not a pure equal-quality rate improvement.

The synthetic cut/noise campaign is an explicit counterexample: both MT02
policies reject five high-entropy noise frames, eventually present53/60 and
recover to final ID59. Backoff retains scale32 afterwards and lowers pooled
PSNR36.38→34.49 dB without recovering those noise inputs. A permanent
quality downgrade is not an acceptable automatic solution to a capacity miss.

## Memory, overlap and receiver cost

MA01's16 main cases perform934 actual preparations,902 hash-checked commits
and901 eventual presentations. All slots, credits and capture waiting work
drain. Peak retained packet bytes are95,296 within two49,152-byte slots;
logical framebuffer roles stay within three. One persistent anchor is518,400
logical YUV420 sample bytes, but Python int16 arrays retain1,036,800 bytes per
endpoint; old/new construction and temporary work coexist. Physical memory,
CDC, reassembly and optical display behavior remain unqualified. The MT02
front/back representation is metadata, not a bounded framebuffer allocation.

Anchor aging and refresh drain are real costs: older anchors often need more
residual bytes, and a refresh can block otherwise available captures. At10 ms
feedback with assumed20 ms decode, primary MT02 rates are26/24 IDs/s versus
MA01's29/29. But40 ms decode limits MA01's second clip to24 IDs/s,48/60
eventual frames and100 ms p95 diagnostic age. More buffering does not remove
the receiver-service limit.

The separate Python measurement makes the implementation gap explicit:

| Actual reference loop | Encode median | Decode median | Whole offline loop |
| --- | ---: | ---: | ---: |
| Combat held-out | 43.35 ms | 20.71 ms | 12.91 frames/s |
| Second clip held-out | 57.26 ms | 27.70 ms | 11.27 frames/s |

Concurrent host load is uncontrolled, but these measured calls cannot justify
virtual2/8 ms assumptions. They neither prove nor disprove optimized native
host/FPGA performance. Native implementation and actual memory/link/feedback
measurements are required before hardware claims.

## Next work

1. Replace fixed assumed service with target measurements or source-bound RTL
   schedules; include native host encode and concurrent ESP32 Wi-Fi/QSPI costs.
2. Develop bounded quality restoration, scene-cut detection and age control.
   Keep a declared visual-quality floor; do not hide cap failures by dropping
   forever to coarse quantization. Compare common presented IDs and inspect HUD,
   motion and temporal artifacts on longer, varied native sources.
3. Evaluate whether an asynchronously prepared replacement anchor can reduce
   refresh stalls with a small, explicitly owned extra reference. Test delayed,
   duplicated/lost ACK, anchor retirement, reset and byte-cap pressure first.
4. Couple coefficient/temporal stripes to actual reference/framebuffer memory
   service. Select a bounded profile only after rate/quality, latency, storage,
   recovery and target fit gates pass; keep existing JPEG as the hardware control.

The [final snapshot](prototype-v4-provenance.json), component manifests, scripts
and test logs bind this iteration's sources and results. Older reports remain
archived evidence; this report does not retroactively turn their failures
into successful hardware runs.
