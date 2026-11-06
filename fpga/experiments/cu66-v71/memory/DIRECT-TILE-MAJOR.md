# Canonical tile-major prototype

New modules: `cu71_memory_system_direct`, `cu71_word_bridge_direct` and
`cu71_tile_memory_direct`. Existing RGB/scalar/cache variants are preserved.
The exact selected SDR2 controller/clock/phase/read-wait remain unchanged.

The upstream logical API remains one512-bit row-major8×8u8 tile, with the same
generation/bank/plane/index request and completion identity. CU66 bytes and
canonical logical hash order do not change. The codec's logical row/SHA work
remains upstream of storage; this is a new **physical** storage layout.

All addresses below are x16 words:

```text
planeBase = canonical_base(bank) + [0, 172800, 216000][plane]
tilesWide = plane == Y ? 90 : 45
tileIndex = tileY * tilesWide + tileX
tileBase = planeBase + tileIndex * 32
sampleOffset = localY * 8 + localX
wordAddress = tileBase + sampleOffset / 2
byteLane = sampleOffset % 2       # even byte is low
```

Y has90×60tiles and each chroma plane45×30. Plane sizes/bases and total bank
sizes remain unchanged. Every tile occupies32contiguous aligned words, with
four full BL8 operations at offsets0/8/16/24. All write masks are zero. Read
responses carry all128bits internally and are assembled into the original
logical512-bit tile. No half-block cache is needed for canonical reads.

Completion means actual controller data/recovery completion. An abort stops
new chunks, drains the current accepted BL8, suppresses tile success and then
acknowledges drain. Private partial candidates must not be published or reused
before that acknowledgment. Reset still requires coordinated adapter/controller
and clock-domain flushing; these tests do not qualify arbitrary reset midburst.

The LCD128read interface is unchanged, including held responses, abort/drain
and one outstanding operation. It already permits any allocated aligned whole
BL8 block, so it can read canonical tiles and row-major HUD words. The retained
RGB port can be tied inactive by the direct architecture. Root ownership must
keep canonical/HUD front generations leased for the actual scanout lifetime.

## Executed component gates

`direct-reference-{fast,slow}01` and
`direct-reference-crossbank-{fast,slow}01` each pass5,346checks and94abort/drain
probes with the real non-`SIMULATION` controller and strict Icarus pin model.
They cover all planes/banks, highest physical word, map guards and row edges,
independent scalar physical readback, held response ownership and concurrent
LCD/auxiliary clients. A dedicated count checks exactly4read and4write BL8
operations per tile,32physical words and zero masked canonical write bytes.

Every one of32read-data and32write-data abort positions across all four bursts
is tested. Accepted write prefixes are read back physically; no canceled full
tile success is exposed. Four contended reference reads issue16actual BL8
commands and have an observed maximum477modeled clocks under the declared
LCD/aux workload. This workload holds RGB inactive and is not directly the
same traffic mix as the earlier four-client RGB-copy benchmark.

`verify_direct.py` binds the executed evidence to current source hashes. These
are memory-component results, not complete CU66 decode, exact direct YUV/HUD
display, FPGA fit/timing, physical playback or30fps gates. A direct-system host
readback accessor must reconstruct logical pixels using the tile-major formula;
reusing the old linear-plane physical peek would be incorrect.
