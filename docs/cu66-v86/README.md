# V86 compact codec, matched wire controls and new-stream context replay

V86 implements a distinct **CS86** research profile with a compact frame
envelope and an embedded binary operation map. Its native receiver verifies
the same reconstructed content/HUD seals while deriving fixed context/mask
identity, the accepted previous root and the actual semantic HUD hash locally.
It does not silently reinterpret the published CS85 header.

All **457 sources × six configurations = 2,742 actual packets** reproduce the
native coefficients, canonical pixels, semantic HUD, rendered RGB565, C2 root
and frame seal exactly. The all-visible controls are actual re-encoded and
receiver-qualified packets under the same envelope, not projected lengths.
Resolution and quantized picture quality are unchanged.

## Complete application-packet bytes

All counts include header, embedded map, quantizers, chunk directories, AB38
headers/termination/CRC, encoded HUD and outer CRC. Link/network overhead is
excluded equally. The original 457 CU66 packets total 7,946,811 bytes, median
16,851 and maximum 44,016.

| Profile | Residual chunk cap | Median packet | Maximum packet | Corpus bytes |
|---|---:|---:|---:|---:|
| All-visible matched control | 256 | 19,941 B | 48,158 B | 9,379,045 B |
| COPY, inherited V2 map bodies | 256 | 18,069 B | 48,158 B | 8,483,744 B |
| COPY, adaptive grouped map | 256 | 17,923 B | 48,158 B | 8,410,466 B |
| All-visible matched control | Whole plane | 16,984 B | 44,833 B | 8,008,725 B |
| COPY, inherited V2 map bodies | Whole plane | 16,985 B | 44,833 B | 8,004,231 B |
| COPY, adaptive grouped map | Whole plane | 16,854 B | 44,833 B | 7,930,953 B |

The smallest fixed profile is **15,858 bytes (0.20%) smaller overall** than
original CU66. This is a small corpus result: 306 sources shrink, two are equal
and 149 grow. The independently sorted packet median is three bytes larger
than the original median, while the median of paired changes is 46 bytes
smaller. The maximum also remains larger than the original maximum. All six
profiles fit the old 49,152-byte packet budget on all 457 sources.

Against the actual whole-plane all-visible control, grouped COPY saves
77,772 bytes (0.97%) overall, with 406 sources improving, 20 equal and 31
regressing. At chunk cap 256 it saves 968,579 bytes (10.33%) against that cap's
matched control, but that complete profile is still larger than original CU66.
Component savings alone are not used as whole-wire savings.

## Where the bytes were removed

The header is 128 bytes instead of 256. Fixed context/mask identity, cached
previous root and separately transmitted expected HUD hash are omitted; their
semantic bindings remain in the C2 checks. Moving the map method into the
outer header removes the nested 20-byte CM84 wrapper. Every inherited-map
packet is **exactly 148 bytes smaller** than its same-cap V85 counterpart,
with unchanged quantizers, AB38 data, HUD and chunk directories.

The new group method uses two bits per canonical 16-tile group: uniform visible
COPY, uniform visible RESIDUAL, mixed visible bits, or an empty/hidden group.
Hidden CONST positions are fixed by the profile. The encoder compares actual
bitset, run and group body lengths; all 437 native deltas choose group coding.
Bodies total **301,684 bytes versus 374,962 V2 body bytes**, saving another
73,278 bytes across the corpus. Each body remains at most 976 bytes through
fallback; native selected bodies have median/max 712/950 bytes. The independent
parser checks tag legality, mixed/uniform spelling, exact coverage and padding.

## Native protocol and mixed-history selection

**30 actual native cases** exercise malformed/resealed headers, group maps,
quantizers and chunks, late root/seal failure, missing/stale references,
recovery, replay, and rejection of a valid legacy CS85 packet as the wrong
profile. A valid foreign HUD is re-identified and re-CRC'd: a positive original
HUD companion accepts, while substituting the other valid HUD fails at the C2
seal and leaves the prior reference intact. Another case uses the same frame
ID with a different cached image/HUD branch and requires correct recovery.

A separate **rate-only host selector** constructs all six actual candidates,
checks them against the qualified packet hashes, and sends the smallest with
stable tie-breaking through one mixed-history receiver. It passes 457 new
packets plus 457 exact replays and 72 configuration transitions. Those are 457
content sources, not 914 distinct gameplay frames.

The selector chooses 406 grouped-COPY whole-plane packets, 31 all-visible
whole-plane packets and the inherited-map key spelling for 20 ties. Its total
is **7,929,974 bytes**, only 979 bytes below fixed grouped COPY. It removes the
31 matched-control byte regressions. The entropy components were pre-encoded
offline, and all six complete packets are assembled before selection. This is
not a live host-encoder benchmark or a decode-deadline policy. In particular,
the all-visible choices are outside the COPY-only frontend timing model below.

## Full-corpus frontend replay on actual re-encoded streams

The new observer validates **914 profile/source records and 7,432 actual
AB38 chunks**, including real per-chunk initialization, CRC, fetch, preload,
termination and coefficient work. It qualifies all 457 sources at caps 256 and
whole-plane. No old-stream counters are scaled into new-stream predictions.

The frontend model covers **5,484 schedules**: both chunk profiles, LOW/HIGH
primitive costs and one/two/four arithmetic lanes with an eight-tile window.
It retains context order, shared fetch/control and tile rendezvous. Whole-plane
results at the assumed 100 MHz are:

| Arithmetic lanes | LOW median / maximum | HIGH median / maximum |
|---|---:|---:|
| 1 | 3.84096 / 13.01751 ms | 7.37003 / 24.92039 ms |
| 2 | 2.34734 / 7.23107 ms | 4.47110 / 13.83299 ms |
| 4 | 2.19716 / 6.56867 ms | 4.17342 / 12.53027 ms |

LOW two/four-lane frontend cases fit 10 ms for all 457 sources, but HIGH still
exceeds it on some sources even with four lanes. These are **standalone
conditional frontend times**, not measured RTL clocks or full validated FPGA
decoding. Map/envelope parsing, outer CRC, HUD, dequant/reconstruction, pixel
memory/display, physical ports and ESP32 execution are excluded. Operations
are batched by context/tile, rather than traced instruction by instruction.

Two lanes remain the first controlled implementation comparator. Combine the
actual new-stream arrivals with bounded pixel-memory/hash/display scheduling
before drawing an end-to-end conclusion. The unchanged memory-service floor
from earlier studies is not removed by smaller packets or faster entropy.

## Evidence and next step

The combined verifier independently reconstructs all 2,742 packet hashes,
parses ten retained fixtures, checks protocol recovery against native positive
responses and binds all component/model manifests. Context audits check all
5,484 rows and reconstruct four full witness DAGs. Map tests pass 27 checks and
four vectors; controls have independent retained-data verification. The
adaptive receiver run and its separate audit are retained separately.

The host parser's 2-MiB limit and whole-packet/coefficient allocations are not
FPGA/ESP32 memory claims. All 457 sources come from one walkthrough family in
four reset histories. No hardware 30-fps, full validated under-10-ms, target
fit/Fmax or general HEVC/AV1 superiority milestone is closed.

- [Next codec and implementation plan](next-steps.md)
- [Wire format](wire-format.md)
- [Map grammar and actual all-visible controls](maps-controls.md)
- [New-stream context observations and full model](contexts.md)
- [Rate-only mixed-history selector](adaptive.md)
- [Evidence and reproduction](evidence-scope.md)
- [Audited combined results](../../experiments/python-gamebub-v86/summary.json)
- [Independent paired byte audit](../../experiments/python-gamebub-v86/byte-audit.json)
- [Adaptive native run](../../experiments/python-gamebub-v86/adaptive/results.json)
- [Independent adaptive selection/replay audit](../../experiments/python-gamebub-v86/adaptive-audit.json)
