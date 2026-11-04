# Uncapped REQP-1839 classification: 199 warnings

This source/report review is separate from sealed v2. It reads the sealed
`akd1-compute-cancel-boundary-20261104` candidate (manifest
`ac3ea38161c6f6ca69a9ecba7917b3a4cbdf1d5d2b975558c64480d734df8e3b`).
No candidate edit, build, new Vivado process or hardware action was performed.
The accompanying JSON independently parses all 199 descriptions from the full
report and matches them to the supplied summary before classifying each warning.

| Memory role | Warnings | Exact affected pin classes |
| --- | ---: | --- |
| Audio PCM slots | 4 | 4 WEA[0] |
| QSPI write FIFO | 8 | WEBWE[0..7] on one RAM |
| Initialized fixture ROM | 32 | 16 ENARDEN + 16 RSTRAMARSTRAM |
| Outer envelope byte store | 64 | 16 each ENARDEN, ENBWREN, RSTREGB, WEA[0] |
| CP02 encoded packet store | 32 | 16 ENARDEN + 16 WEA[0] |
| CP02 rebuilt DC table | 4 | 4 WEA[0] |
| GM01 map store | 3 | ENARDEN + ENBWREN + WEA[0] |
| Raster stripe stores | 8 | 4 ENBWREN + 4 WEA[0] across two banks |
| Persistent overlay memory | 44 | 44 ENBWREN across 11 banks |

All 199 are accounted for. There is no additional immutable ROM among these
warning-associated RAM cells. The source's 384-byte quantizer table is not in
this inventory; absence from REQP does not prove its mapping or enumerate every
unflagged RAM/ROM.

## Mutable working stores: conditional source rationale

The FIFO resets pointers, synchronizers and `fetched`/read-state tokens. A newly
visible entry must follow a fresh RAM write and write-pointer publication; a
stale `queue_read` value cannot assert `core_write` without a new fetch.

Audio resets staging, enable/playing and both pointer domains, then rearms through
the offline/acknowledgment/settle handshake. A slot publishes only after all
declared PCM frames are freshly written and CRC checked. LAST is rewritten with
those words, preventing old unused-tail words from being consumed. This is an
audio-off AKD1 lab rationale, not active-audio PLL-loss or acoustic qualification.

Envelope memory is inaccessible to replay until the new bounded packet is fully
loaded and certified; replay address and owner/epoch checks restrict the range.
Its pending/response valid bits reset. GM map storage likewise loads and certifies
all used packed map bytes before bounded, identity-checked queries become valid.

CP02 reloads the entire declared packet before CRC/entropy validation or output.
Its DC table is rebuilt for all blocks in the current plane before AC replay
uses it. Reset invalidates cache/certificate/output state. Raster banks reset
full/output-valid ownership and publish a bank only after its visible samples
have been freshly filled in the checked order.

These source invariants make old mutable data logically unreachable after a
proper reset and fresh write, assuming later operations occur under stable
clocks with their timing met. They are not analog BRAM corruption proofs or
blanket waivers. The exact synthesized async-control warning still exists at
each listed pin. No new source-level stale private-data path was identified in
these working stores in this review.

## Initialized fixture: concrete startup gate remains failed

The fixture has no fresh-write-before-visible recovery path. The unchanged
reset-data source clause maps to the v2-proven active ROM EN/RSTRAM behavior;
that parent proof must be rebound to any repaired successor, not silently treated
as its netlist. Logical reset does not reload ROM. Expected counts/tag and stable
ownership at the ESP32 provide a fail-closed diagnostic check, not retention proof.

## Overlay: additional persistent read path, polarity still unproven

Overlay is mutable UI memory but its transparent initial state is loaded only by
configuration. Warm pixel reset clears scanout/control registers, not the RAM;
there is no full-redraw-valid barrier before old overlay pixels can be displayed
again. This persistence is intentional in the stock-style live update path, so
it cannot use the working-store fresh-write-before-visible rationale.

All 44 warning-associated ENBWREN pins are synthesized read-port enables whose
cones include `rstpixel_reg[3]`. Source read access is unconditional. The uncapped
warning does **not** identify the enable's polarity during reset or prove it is
high during pre-LOCK startup. The executed v2 checkpoint query did not select
overlay cells. Consequently both fresh pre-LOCK overlay protection and warm-reset
uncorrupted transparency remain **NOT_PROVEN** here. Stable initial address zero
is not a substitute for checking enable behavior while the clock is unstable.
A bounded checkpoint truth/cone inspection is required before claiming fresh
startup safe; no additional concrete EN-high blocker is asserted without it.

The relevant device rule remains [AMD/Xilinx UG473 v1.14, pp. 12–13](https://docs.amd.com/api/khub/documents/9gZGbqBxtlKXxBfkBt~lAg/content),
as summarized and bound in v2. Setup closure, startup/CDC review, warm reset,
external QSPI timing and physical playback remain distinct gates. No warning
severity or waiver was changed.
