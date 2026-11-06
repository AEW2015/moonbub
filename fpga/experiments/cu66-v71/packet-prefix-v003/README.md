# Isolated HUD length validation staging

`cu71_packet_hudsum.sv` is a new same-port successor of frozen v002. Source SHA-256 is `aae2623f41459b064b99f05404b0796c84dae5ab7871c2d4a7bddb5c8b10f3c3`; parent v002 SHA is `9ab9f4abd82d130cd627a952f78efe841a0fc3505a832e40348f64d82d3ad7e2`.

## Measured reason and exact change

V002's unplaced exact-part OOC worst path is HUDheader[58][7]→error_code[0]/CE,15levels/6CARRY, with only+0.215ns estimated setup margin at100MHz/1ns scalar IO. Root authorized this isolated follow-on from that measured cone. It is not a HUD semantic decoder change or a prediction of routed timing.

After the last HUD header byte is captured, three new private states register:

1. `s0=hud32(54)+hud32(58)`, `s1=hud32(62)+hud32(66)` in parallel;
2. `s01=s0+s1`;
3. `total=s01+32'd110`, then enter the original CHECK_HUD.

All operands/registers remain unsigned32 and preserve the exact original modulo2^32 expression. `hud_bad` compares the registered total with the same zero-extended16-bit metadata length. Individual32-bit lengths, packet bounds, rectangle checks, type rules, all fixed fields and code11-before12 priority are unchanged. Computing provisional sums is not successful validation. No byte request/metadata/qmap/commit is accepted in these private states.

Existing v002 states0–14 keep their values; HUD stages15–17 are appended. No additional RAM reads occur. Successful parsing adds three clocks over v002, eight over v69. A HUD header failure reaching CHECK_HUD receives the same additional three private clocks before rejection. Abort/reset priority and the original shared reset/flush contract remain intact; no byte response is outstanding during these stages. Original CRC byte coverage/order and downstream ownership/publication gates are unchanged.

## Executed functional evidence

- `evidence/focused01`: four-state Icarus PASS65,811 checks. Includes all inherited prefix/inner-sum checks,1002 legal HUD header/tag cases,1000 full-width malformed/wrapping HUD sums, boundary-length/total-mismatch tests, exact11-before12 with simultaneous fixed-header and bounds/rectangle/type faults, plus abort/reset/retry in all three new states.
- `evidence/controls01`: originalv69→v003 native byte-RAM A/B, seeds6910/6911, each12 valid metadata/qmap goldens+23 exact-code structural rejects+5 semantic-deferred/aborted cases.
- `evidence/controls02`: explicit frozenv002→v003 A/B on those same40 actual cases per seed. Every structural error code matches; all metadata/qmap goldens, delayed-response/stall/held-commit and abort/drain checks pass. Each run reads389,466 packet bytes and checks24,300 qmap responses. This is not a full457-packet rerun or a canonical/HUD reconstructed-pixel claim.
- `evidence/ooc01` completed **v002→v003**, same exact part/100MHz/1nsIO, two threads, short private `C:/px73a` and TEMP/TMP, with immutable source copies. Estimated WNS improves+0.215→+1.156ns; candidate hold+0.260ns/pulse+3.750ns, TNS0. Resources2466→2499LUT,3420→3549FF,72LUTRAM unchanged/no BRAM/DSP. Worst moves to outer_header[72][4]→error_code[0]/CE,14levels/7CARRY. No additional outer-header change was selected. These are unplaced estimates, not routed-board or hardware qualification.

Scripts are under `scripts/cu66-v71/packet-hudsum`. `derive.py` recreates RTL from hash-pinned v002; `derive_tb.py` derives the extended focused bench; other runners require new unique evidence directories. No old evidence, selected parser, profile/ABI, PHY, map, quota, IO or clock constraint was changed.

Whole-system canonical/HUD/pixel goldens and any selected board binding remain parent-owned. No BIT, hardware or30fps claim follows from these component gates.

`evidence/handoff.json` binds305 source/evidence artifacts and keeps overall status INCOMPLETE for those parent-owned integration and routed/hardware gates. `seal.py` checks final source identity and artifact hashes manually. `c_check_handoff` is unavailable in this session and is not claimed.
