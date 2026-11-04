# Unified codec, exact UI and acknowledged-reference finite stream

One experimental AR02/GF02/AF02 path now combines GM/SR selection, two acknowledged
YUV reference banks and four exact RGB565 display patches. The canvas remains
720×480 with 720×405 active game content. These are offline Python measurements
and finite scheduling experiments; no firmware, FPGA or Sunshine mode is installed.

## Results

The 180-ID held-out native scene gives:

| Profile | Strict presentations | Eventual presentations | Diagnostic IDs/s |
| --- | ---: | ---: | ---: |
| GM + four exact UI patches | 175 | 178 | 30.0 |
| Minimum actual GM/SR + UI | 169 | 172 | 28.8 |
| GM/prune-4 + UI | 126 | 129 | 21.6 |
| Exact GM/SR + UI, full key every 30 IDs | 155 | 157 | 26.0 |

GM+UI presents IDs 12–161 in [500,5500) ms: 150 distinct native input hashes and
150 distinct decoded RGB hashes, giving 30 modeled IDs/s over five seconds.
Only startup IDs 1 and 2 are dropped. All decoded UI frames select 21,120 original
RGB565 words with zero mismatch. The rectangles are configured regions, not
verified semantic HUD detection. Short one-second diagnostics can report 31
because of backlog/window phase; input remains scheduled at 30 IDs/s.

Exact SR minimizes complete **inner** bytes among actually coded alternatives.
It pays every losing candidate and uses one analysis/three forward transforms.
GM+UI preparation averages 29.782 ms versus 33.512 ms for exact+UI; decode averages
24.947 versus 24.572 ms. That host encoder cost offsets the byte benefit here.
Different finite profiles admit different IDs/reference histories; their average
packet sizes or total wire bytes cannot establish matched compression gains.
Prune-4 is lossy against its own current-reference quantized GM reconstruction,
not globally bounded against original pixels or another stream history.

## Executed model and limits

The 14 cases contain 1,248 capture events, 1,154 paid preparations and 1,152 decode
commits. Eight short factorial cases compare GM/exact with UI off/on; four longer
cases test full UI and refresh; two synthetic cases inject lost promotion ACK
and conflicting feedback. The measured host run totals 124.85 seconds.

Actual BOX scaling, map generation, encoding/rejections, UI cache/validation,
packetization, GF02 feeds, decode begin/complete/abort, feedback parse/apply and
expiry work are paid. Decoder publication and ACK visibility are staged until
charged completion; expiry/deadline wins. Bank-specific reader/writer reservations
permit bank-0 work while bank-1 promotion waits. Reference tags bind canonical
YUV; UI changes only the display image. AF02 binds the outer AR02 body CRC and
published reference identity. CRC/hash binding is not authentication.

The finite model assumes independent serialized servers, 8 Mb/s forward/reverse,
160 Mb/s QSPI, 10 ms feedback and 60 Hz vblank. Host stages are measured Python
wall time, not ESP32/FPGA cycles or concurrent execution on a shared CPU.
Source files are precompressed 25/29.88 fps clips loaded offline, then hypothetically
scheduled at 30 IDs/s. Capture/desktop acquisition is unmeasured. The first clip
contains duplicate source frames; the longer result uses 180 distinct native IDs.

Bounds are two retained YUV banks per peer, three sender transactions, two actual
GF ingress buffers, four feedback descriptors and three framebuffer roles. Python
int16 YUV banks use twice their logical 8-bit size. Source, scratch, UI caches,
outputs and temporary copies are additional; these counts do not prove peak RAM,
BRAM/SDRAM fit, memory bandwidth, RF behavior or physical 30 fps. Initial-key-only
success does not qualify periodic refresh/recovery for a production stream.

## Verification

`results.json` pins 25 executed sources. `verify.py` checks retained evidence.
`analyze.py --check` independently rederives the five-second unique-image claim.
`tests.log` records 11 passing tests. The supplemental `test_ingress_feedback.py`
forces a two-ingress overload, derives an actual GF02 busy AF02 NACK and checks
paid feedback/error work, safe expiry and complete pool draining. Supplemental
analysis/tests were added after timing; pinned benchmark sources remain frozen.

```sh
python verify.py
python analyze.py --check
python -m unittest -v test_model.py test_ingress_feedback.py
```

Run from this directory with the project NumPy/Pillow/PyAV environment. Re-running
`benchmark.py` creates new measurements and replaces evidence; use the read-only
checks for this snapshot.
