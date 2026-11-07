# V99 RC1 candidate contract and audit

This contract records the selected conditional RTL research profile and its
audited support boundaries. The generated source inventory is
[`inventory.json`](../../experiments/python-gamebub-v99/inventory.json), built
by [`candidate_inventory.py`](../../experiments/python-gamebub-v99/candidate_inventory.py).
It records SHA-256 hashes for the active transport, existing JPEG hardware,
V91 functional RTL chain, native CU66 reference and CS88 software receiver.
Regenerate it when an inventoried source changes.

## RC1 decision

The selected **conditional RTL research candidate** is the documented V91
CS88/all-BR88 subset. Fresh CU66/GU66 arithmetic 5/6 is now a software control,
not the RTL candidate. The fresh campaign's independent ledger audit passed all
360 fresh-RGB attempts through the current receiver. A separate native campaign
records 3,948 atomic trials. These results close the fresh software parity
control; they do not make CU66 the V91 RTL wire profile or establish its RTL fit.
The forced 360-frame native rerun for the RC1 all-BR88 subset and its independent
coefficient/C2 audit also pass. See the
[qualification pointer](../../experiments/python-gamebub-v99/qualification.json).

The candidate keeps the existing 720×480 canonical pixel and exact semantic
HUD contract. Complete success must validate the C2 SHA-256 content root, frame
seal and atomic ownership publication. Those behaviors are product semantics;
the full selected-top transaction is not yet integrated or qualified.

## Selected profile bounds

| Field | RC1 setting | Evidence status |
|---|---|---|
| Outer wire format | CS88 | Existing V91 RTL contract |
| Entropy | BR88 chunks only; AB38 and mixed frames reject before child decode | Existing V91i2 contract |
| Geometry | 720×480, canonical YUV420 path | Existing V91 contracts |
| Block size | 32 | Existing V91i admission profile |
| Chunk block-count cap | 65,536 blocks | CS88 header/profile parameter in V91i contract |
| Complete wire cap | 49,152 bytes | Existing V91i admission limit |
| Key mode method | 0 | Empty key mode body in V91i contract |
| Delta mode method | 3 | Grouped mode map in V91i contract |
| QM87 methods | 2 run-map or 6 inherited-cache | V91i supported forms; method 6 needs a valid accepted-reference snapshot |
| Default quantization | Uniform scale 16 | RC1 candidate default |
| Diagnostic quantization | Scales 8 and 32 | Diagnostic profiles, not the RC1 default |

The original minimum-map run had 23 P frames using mode method 2 and 12 key
frames using QM87 method 1. The native receiver accepted those packets, but
those fields are outside the documented V91 RTL subset; RC1 rejects that
profile. The independent source audit checks the actual mode/QM fields rather
than accepting the receiver's broader support as evidence of RTL support.

CU66/GU66 uses upstream epoch 25. **CS88 has a generation field and no epoch
field in its wire header.** Do not describe epoch 25 as a CS88 wire field. Any
internal frame or child epoch used by an RTL transaction is an implementation
ownership tag, distinct from the CS88 wire generation.

These parameters are audited against the existing V91i/V91i2 contracts and
README files. This inventory task ran no new RTL regression, so it freezes the
documented profile boundary and source hashes, not a newly qualified RTL
configuration.

## Transport and production support

The production path remains baseline JPEG over the active MSV1 UDP worker and
existing QSPI/register interface into the Rev4.1 JPEG top. JPEG is the separate
fallback profile. The retained JPEG design uses 120.5 of 135 BRAM tiles; no
claim is made that it and the proposed CS88 decoder fit simultaneously, or that
those historical BRAM figures are available candidate headroom.

V97 compact MB97 negotiation remains an undeployed prototype. Its opaque
research profile IDs are CS92/CS94/CS95/CS96. It does **not** negotiate CS88;
CS88 is not aliased under the CS92 ID. V97 packetization does not install a
decoder, accepted-reference history or validated publication path. The
production adapter and worker integration remain open.

CS92 is a distinct versioned research frame format. The fresh CU66/GU66
software-control profile is also distinct: epoch 25, 720×480 YUV420, arithmetic
dispatches 5/6 and zero base motion. Neither profile changes RC1's selected
CS88/all-BR88 RTL wire candidate.

## Existing RTL interfaces and memory assumptions

The inventory hashes these existing paths for review: V91i CS88 admission and
mode/qmap ownership; V91i2 BR88 dispatch and coefficient placement; V91j
dequantization and Q14 IDCT; V91k reference reconstruction and base RGB565;
and V91l C2/HUD/root/seal validation and publication control. It also hashes
the existing native v69 CU66/GU66 decoder and the CS88 receiver source used by
the current software evidence.

The current repository documentation identifies the native Rev4.1 prototype
and target part `xc7a100tcsg324-1`. The retained JPEG implementation reports
7,362 LUTs, 5,994 registers, 120.5/135 BRAM tiles and 32 DSPs, with the existing
100 MHz processing/SDRAM, 200 MHz QSPI, and approximately 29.361979 MHz LCD
pixel clocks. Its shared memory uses two 16-bit SDR SDRAM framebuffer slots,
BL8/CAS3 service and scanout priority at burst boundaries. These are facts for
the existing JPEG top. The CU66 software decoder uses dense host arrays, and
the V91 RTL pieces have local logical storage and simulated service models;
neither supplies a mapped complete-top resource/port budget. Candidate fit,
SDRAM contention cost, placed/routed timing and joint JPEG fallback fit remain
unknown. Current Vivado/Artix tool support remains unknown/pending its V100
check.

## Remaining gates

The software CU66 fresh-input/current-receiver control is closed by the
360-attempt audit in
[`audit-fresh.json`](../../experiments/python-gamebub-v99/audit-fresh.json).
That receipt covers software packets, source identity, nested CRCs, exact
canonical/HUD/RGB565 goldens and the component artifact ledger. It does not
establish native RC1 subprofile qualification, original raw gameplay coverage,
or hardware performance.

The independent [CS88 audit](../../experiments/python-gamebub-v99/audit-cs88.json)
separately qualifies that native/source-grammar subset. Before product promotion,
RC1 still needs a native real-time host encoder; original held-out 30-fps captures and HUD/temporal quality
checks; broader complete-path recovery goldens; full V91l HUD, shared-service
and source-cadence integration; a production V97 adapter and ESP-IDF resource
and service calibration; and candidate memory/port/whole-top fit. V100 must
reconfirm the target board, part, tool support and constraints, then provide a
clean physical implementation baseline. V110 still requires 1,800 distinct
frames over 60 seconds and 18,000 over 600 seconds at 30 Hz under real
contention, followed by every qualified packet-complete-to-validated-publication
sample strictly below 10 ms.

RC1 therefore selects the CS88/all-BR88 profile for bounded RTL research while
keeping product promotion conditional on these integration and hardware gates.
