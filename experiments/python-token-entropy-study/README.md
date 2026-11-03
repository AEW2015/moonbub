# CP02 token-list entropy prototype

This is a local Python host optimization of the frozen byte-compatible
[v5 serializer](../python-fast-entropy-study/README.md), applied to the
[v6 key preparation](../python-key-prepare-study/README.md). It changes no
quantization, Rice choice, DC reset, EOB/ZRL, RAW fallback, packet CRC or pixels.
No Sunshine/ESP32/FPGA source or installed mode is changed.

`token_coeff.py` converts coefficient positions, mapped values, bands and block
indices to Python integer lists once per plane. Its inner AC loop uses those
lists, sixteen precomputed run-prefix strings and four fixed ZRL strings. This
removes repeated NumPy scalar indexing, integer conversion and string formatting
from the loop. Existing vectorized coefficient discovery and Rice-cost analysis
remain unchanged. The lists add transient host allocations proportional to
coefficient count; this is not an FPGA memory or DSP optimization.

`token_key_encoder.py` is a local copy of the v6 encoder with its key serializer
import changed. It does not patch globals in old modules. Required reconstructed
YUV keys remain, with the same lazy RGB verification oracle. P preparation still
inherits the unchanged v5 P implementation, so this experiment claims a key-path
improvement only. Existing MA01 credits, reference/ACK and expiry semantics apply.

## Reproduce and evidence

Use the existing [pinned environment](../python-codec-study/requirements.txt)
(Python3.14.4, NumPy2.5.4). Source videos remain outside Git. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python scheduler_probe.py
```

Three tests exercise80 deterministic sparse/dense/extreme/RAW coefficient families,
all64 zigzag token positions, and actual key/P bytes and decoded RGB across
quantizers1/8/16/32/128, global motion and forced refresh. Both codecs use the
frozen independent decoder. This is finite regression evidence, not formal
all-input equivalence.

The paired benchmark uses the same24 independent key source indices as v6:
six alternating indices from twelve native frames starting1 s/4 s in each of
the two Mass Effect sources. Every source/PTS/canvas and executable-source hash
is recorded. All24 whole-key pairs and72 isolated entropy-plane pairs match byte
for byte; whole-key receiver RGB/hash also matches. Original source rates are
25/29.88 fps and some content repeats; these are not24 distinct native30 fps
capture samples.

Timing order alternates between variants. Preparation is actual Python wall
clock under uncontrolled host load, without CPU affinity or isolated warmup.
Source decode/scale, optional verification RGB/hash, receiver checks, network,
QSPI and presentation are excluded. Isolated entropy also excludes coefficient
preparation. No previous result artifact is overwritten.

## Measured results

| Same-run comparison | Previous mean | Token-list mean | Gain |
| --- | ---: | ---: | ---: |
|Entropy per plane,72 pairs|4.30 ms|2.43 ms|1.77×|
|Whole key,24 pairs|33.18 ms|27.67 ms|1.20×|

Whole-key median changes32.55→27.08 ms, p9537.91→33.35 ms, and calls over
33.33 ms fall7/24→2/24. The new maximum is35.85 ms. Therefore this sample
improves key preparation but **does not establish a passed per-key33.33 ms
budget or end-to-end30 fps**. The tail and additional host allocation must be
preserved in implementation/service decisions.

The four `scheduler-results.json` cases use the actual token-key factory with
the existing finite measured-service model. Each selected packet is re-encoded,
decoded and hash-checked; its measured preparation duration drives serialized
service. The compatibility config label remains `fast_key`, while the factory
and artifact explicitly identify the token encoder. Decoder variants either
assume8 ms or charge actual Python receive duration. Network8 Mb/s, QSPI160
Mb/s, feedback10 ms and60 Hz presentation remain assumptions. These are short
conditional offline service replays, not concurrent streaming or target timing.
Source acquisition, lazy host oracle, RF/feedback overhead, physical memory and
native capture are excluded. See the saved strict/eventual counts, diagnostic
window and per-packet durations instead of inferring FPS from the benchmark mean.

|60 primary inputs|Decoder service|Strict / eventual|Diagnostic IDs/s|
| --- | --- | ---: | ---: |
|Combat|Assumed8 ms|55 /56|28|
|Combat|Measured Python|46 /48|24|
|Second clip|Assumed8 ms|55 /57|29|
|Second clip|Measured Python|41 /44|21|

All four cases drain slots, pending display work and credits. Faster keys do
not by themselves yield30 diagnostic IDs/s in these runs. Values differ from
other measured-service runs because per-call timings and selected input IDs
are endogenous; these are not a controlled same-service proof of a particular
FPS gain. The strict interval remains `[0,2000)` ms, diagnostic `[500,1500)` ms,
and eventual delivery includes a separately declared1,000 ms drain.
