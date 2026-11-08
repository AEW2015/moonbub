# V111 capacity study: one immutable canonical anchor in external SRAM

Status: **read-only capacity/source study; no codec, controller, RTL, timing or hardware implementation**. The [machine-readable calculations and source pins](../../experiments/python-gamebub-v111/sram-anchor-study.json) reproduce the arithmetic. This is a possible spatial-data-reuse option for V112+, separate from the active header timing trials.

## Actual data format and capacity

The actual Count reconstruction stream outputs an8-bit `out_value` and finishes after518,400 canonical samples. Its unchanged full-decoder bench stores references as `std::vector<uint8_t>` and requires reference/output length518,400. The independent address oracle uses Y/U/V bases0/345600/432000, plane widths720/360/360 and8×8 tile addresses. Thus the candidate is the codec's canonical planar-u8 4:2:0 reference, including its exact normalization/rounding rules—not converted RGB565 or an arbitrary YUV representation.

| Allocation | Bytes | Result in nominal512KiB |
| --- | ---: | --- |
| Y720×480 | 345,600 | — |
| U360×240 | 86,400 | — |
| V360×240 | 86,400 | — |
| One tightly packed canonical frame | **518,400** | Fits524,288bytes with **5,888bytes** left |
| Two canonical frames | 1,036,800 | Does not fit |
| One RGB565720×480 frame | 691,200 | Does not fit;166,912bytes over capacity |
| Canonical frame with64-byte-aligned per-row strides768/384/384 | 552,960 | Does not fit |

The tight plane bases are byte-aligned and even: Y `[0,345600)`, U `[345600,432000)`, V `[432000,518400)`. The nominal unused tail is `[518400,524288)`. A256K×16 organization holds262,144words; the frame needs259,200words and leaves2,944words. Define byte/word addressing and both byte lanes explicitly. No padding, tile headers, ring, stack, compressed staging or unreserved firmware region may silently consume that tail. The49,152-byte compressed-frame control cannot coexist there.

A proposed **tile-major** physical layout could use8,100 contiguous64-byte records (`5400Y+1350U+1350V`), matching the current64-sample reference response. This avoids raster-stride gathers for one tile and follows the existing tile-ordered reconstruction output. It changes physical layout only if the logical canonical bytes and tag/hash order remain identical. Plane/tile/index→address conversion, two-byte word endianness, byte masks and every tile boundary need independent tests; no such SRAM writer/reader exists here. New formats, row padding, greater precision, extra references or pixel metadata require a new capacity calculation.

## Board evidence and open access requirements

The retained [v69 source catalog](../cu66-v69/source-catalog.md) and [pins](../cu66-v69/source-pins.json) identify Rev4.1 U1402 as **IS61WV25616BLL-10TLI**, asynchronous256K×16=512KiB, from board commit `88f578a1a4c4096a33ab038eae82348cafab1229`. They record the RAM schematic SHA and a nominal10ns family description. This is a board-design record, not confirmation of the fitted board/lot. The catalog notes that automated manufacturer-datasheet retrieval was blocked and distinguishes the non-E schematic MPN from the EDBLL family PDF name. Exact part/PVT timing remains **OPEN** until the appropriate datasheet and assembled hardware are checked.

The generic firmware's `sram_read`/`sram_write` helpers use address region `0x05000000`,16-bit transfers, byte swap and a three-system-cycle comment. Those helpers belong to a generic framework contract; they do not prove this video bitstream has that address mapping, control signals or service rate. Current `moonshine_top` has no SRAM ports and current `moonshine_memory` only instantiates SDRAM. The documented raw SRAM interface is separate, but no streaming SRAM controller/arbiter/pin constraints are qualified. SRAM attached to FPGA pins is not ordinary ESP32 address-space RAM.

Do not assume one8ns access at125MHz. The catalog's nominal10ns description alone does not support that. Qualify address/OE access, read/write cycles, WE pulse, setup/hold, byte masks, output-disable/turnaround, FPGA/PCB delay and I/O voltage/bank constraints. Use a real bounded multi-edge controller or an independently qualified clock domain with owned CDC. A separate physical bus would still share decoder logic, tags, arbiters or clocks; independent usable bandwidth is unproved.

## Single-bank anchor replacement

The current canonical reference interface can bind epoch/FID/generation/plane/tile and drain a pending response across cancel/reset. It is not an SRAM implementation. The historical [GM01 contract](../custom-codec-prototype-v9-2026-11-03.md) uses an ACKed immutable reconstructed anchor; predicted output does not automatically advance that predictor. That idea is compatible with this proposal, without implying GM01 deployment or changing current CS88 hardware.

Keep one valid immutable SRAM anchor and a **separate SDRAM candidate-anchor staging allocation**. Also retain RGB565 front/back display buffers in qualified memory; the small SRAM cannot hold those as well. Replacement must use a barrier because two complete SRAM anchors do not fit:

1. Build and validate the complete candidate canonical frame in a reserved SDRAM region. Bind geometry, layout, content identity, FID and generation. Keep it immutable through copy/retry; it cannot alias display or scratch writes.
2. Stop admission/credits for old-anchor-dependent work and coordinate the host's old-generation queue. Finish or cancel accepted dependents, drain every real reference read/response and acquire exclusive SRAM replacement ownership. Keep the old anchor intact until this join; a logical abort is not a physical drain.
3. While copying, neither old nor new SRAM identity is readable. Block dependent requests; preserve the prior SDRAM display front. Use an FPGA-resident copy path to transfer all518,400bytes with exact address/lane accounting and bounded source/destination service; an ESP32 read-then-write loop would add QSPI copies and a different service budget. Do not call this physical copy atomic.
4. Complete every accepted write and required integrity/readback check. Only then atomically publish the **logical** new anchor identity/valid bit and send a content-bound ACK. The host may select the new anchor only after that ACK. A lost/duplicate/stale ACK cannot release storage or manufacture an anchor.
5. If reset, bus error or verification failure interrupts the copy, SRAM anchor validity remains false. Retain the validated SDRAM candidate for a controlled retry, or request an independent refresh. The partly overwritten old SRAM anchor cannot be restored merely by changing its generation register. Old packets must be rejected before they read new-generation storage.

An alternative that keeps serving old requests from an SDRAM copy during replacement needs an explicit dual-provider identity/lease contract and its own memory budget. It is not a free property of this single-bank proposal. Refresh/reference-only frames must not inflate displayed FPS.

## Traffic and service accounting

One full canonical reference read per30-Hz frame costs **15.552MB/s** of payload. Actual copy/constant/residual choices and tile reuse change demand; new motion windows or repeat reads may increase it. This is not a universal codec bandwidth bound. Current CS88 already uses canonical-u8 references, so moving them to SRAM would relocate traffic rather than reduce the canonical byte count. It also leaves SDRAM display, output, validation and refresh obligations.

One anchor copy needs at least518,400bytes read from SDRAM plus518,400bytes written to SRAM. A full SRAM readback adds another518,400bytes. Copy/arbitration/turnaround and CRC/tag work count against refresh pause and frame age. Define display-frame validation and reference-anchor commit as distinct fences and report both. If safe frame publication requires the new anchor, copy/readback belongs inside that frame’s latency interval; moving it after display publication does not erase reference-ACK or freshness cost. For illustration only, at125MHz a controller delivering one16-bit word every2/3/4decoder cycles would need4.1472/6.2208/8.2944ms for SRAM payload writes alone. These are parameterized arithmetic floors—not demonstrated rates, valid datasheet schedules, complete copy times or <10ms decoder results.

The opportunity is a regular, immutable tile provider with local buffering and a separately scheduled data path. Selection needs a source-bound SRAM controller/model, exact canonical/layout/tag parity, wrap/alias/byte-mask/turnaround tests, shared-service and replacement-stall traces, actual fit/clock/I/O reports and remote hardware correlation. Capacity fits; allocation, service speed, copy latency,125MHz access, added pin availability, independent bandwidth and gameplay benefit all remain **OPEN**.
