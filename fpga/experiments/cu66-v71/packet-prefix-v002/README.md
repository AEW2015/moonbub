# Checked prefixes plus registered original-width validation sum

New isolated successor; v001 and selected sources remain immutable. `cu71_packet_presum.sv` has the same ports as v69/v001, with SHA-256 `9ab9f4abd82d130cd627a952f78efe841a0fc3505a832e40348f64d82d3ad7e2`. The direct parent v001 SHA is `b4c8dcb002adf8c3522a73a73f06bd928acb5bf83c953883647577486a9a8b1d`; original v69 SHA is `20d761a514073e8e5212eb70861f843441bc8d8f32b81bf7f02925cd202ae5a2`.

## Measured reason for this successor

Matched v001 unplaced exact-part OOC at100MHz/1ns scalar IO reports baseline−1.032ns and prefix-only−1.042ns, both `inner_header[40][0]`→`error_code[0]/CE`: the original32-bit validation/control sum remains the worst cone. Those measured leaf estimates are not routed timing. The earlier first-DY final paths motivating v001 were header→prefix/metadata CE; they do not prove that only prefix data arithmetic needed staging.

V002 captures the original inner-length equation in three new private states after byte135's response has installed the final header byte:

1. PAIRS: `s0=inner32(40)+inner32(44)`, `s1=inner32(48)+inner32(52)`, `s2=inner32(56)+32'd64`.
2. MERGE: `s01=s0+s1`.
3. TOTAL: `total=s01+s2`, then enter the original CHECK_INNER.

Every add/register is unsigned32 with the same modulo2^32 result as the original chained expression. CHECK_INNER's original header/profile/geometry/reference predicate remains first(code6), then original individual bounds/grammar and registered-total comparison(code7). Calculating provisional sums is not validation: no reads, metadata acceptance, qmap or commit occur in these stages. The original33-bit outer equation and16-bit modular prefix/address semantics are unchanged. Validated prefix staging remains the two states from v001.

No extra RAM reads are made. Successful parsing adds five clocks relative to v69; header failures reaching CHECK_INNER receive three additional private clocks before rejection. Existing state numbers0–9 are preserved; prefix states10/11 are preserved, new sum states12–14 are appended. Global reset and abort retain original priority; an abort in any new state has no outstanding read to drain. Only the shared reset/flush integration contract is supported, as before.

## Evidence

- `evidence/focused01`: four-state Icarus PASS25,303 checks. Includes all original focused-prefix checks plus exact32-bit staged sums,1000 full-width malformed/wrapping vectors, and explicit abort/reset/retry in all three sum states in addition to both prefix states. Exact code6-before7 remains checked.
- `evidence/controls01`: native actual byte-RAM baseline/candidate A/B, seeds6910/6911, each12 valid metadata/qmap goldens,23 exact-code structural rejections and five semantic-deferred/aborted packets. Each reads389,466 bytes and checks24,300 qmap results. Delayed RAM responses, request/metadata stalls, commit/qmap fences and original abort/drain scenarios pass. These40 cases are not a full457-packet rerun or canonical/HUD decode proof.
- `evidence/ooc01`: completed matched unplaced synthesis, maxThreads2, in short private `C:/px72a` directories with private TEMP/TMP. At100MHz/1nsIO, baseline WNS−1.032ns becomes candidate+0.215ns; candidate estimated hold+0.260ns/pulse+3.750ns, TNS0. Candidate worst path is HUDheader[58][7]→error_code[0]/CE (15levels,6CARRY), not the old inner sum. Resources:2436→2466LUT,3212→3420FF,72LUTRAM unchanged, no BRAM/DSP. These are **unplaced estimates**, not routed-board timing or hardware qualification. No extra HUD change was selected from this result.

`scripts/cu66-v71/packet-presum/derive.py` recreates this variant and its extended focused bench only from the hash-pinned v001. The scoped `run_focused.py`, `run_controls.py` and `ooc.py` require new output directories. Frozen executed runners, testbenches, fixtures and source manifests remain in evidence. The parent owns prospective full-system canonical/HUD/pixel goldens and any selected binding or board build.

No BIT, hardware update, PHY/map/quota change or30fps result is claimed.

`evidence/handoff.json` binds the source, proofs and reports. Its overall status remains INCOMPLETE for parent-owned full canonical/HUD/pixel integration and routed/hardware gates. `seal.py` manually checks final artifact hashes and source identity. `c_check_handoff` was unavailable in this session and is not claimed.
