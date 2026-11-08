# V44 bounded-three CU66 lab candidate

November 7, 2026 (America/Denver). Derived into a new source directory from V43 release-v002. V43 and its release artifacts are unchanged. This is a finite three-frame correctness/timing diagnostic, not a continuous streaming release or a 20/30 fps claim.

## Explicit profile and ownership

The network worker explicitly runs `dy71-bounded3-v2` on UDP5535. DYN1/DYA1 header byte4 is **2**; v1 packets are rejected by the parser before staging. Field widths, maximum 1024-byte chunk, 49,152-byte packet limit, whole-datagram CRC and stored-prefix/presentation distinctions remain. It requires the separate matching `host/dy71-bounded3-v2` uploader and its exact KEY0/P1/P2 package; do not use the original two-frame v1 uploader.

Firmware `~` invokes this lab worker after identity/heap checks. It never programs the FPGA automatically. Required FPGA profile remains V027 DY71 ABI2, caps31, HBU1. After three observed presentations it retains the final endpoint/maintenance lease for duplicate presentation replies. Mutated failures retain/quarantine; there is no new session STOP/restart or automatic recovery claim. Recovery still requires the qualified paired reset/reconfiguration procedure. Do not reconfigure underneath a live owner.

`network_driver::run` retains the original two-frame source/API control; `run_sequence(...,frame_count)` accepts1..=3 before any bus IO. Reports use fixed capacity3 arrays. Each transaction preserves staged-byte count/CRC, native HU identity, actual HUD writes and complete actual readback, drain, native commit acknowledgment and observed presentation. New timings split HUD-pending wait, stable request snapshot, extraction start/end/command count and native computation start/end.

## Actual third-frame memory finding

The initial real native endpoint refused the third packet at the98,304-byte arena budget. A larger diagnostic cap proved a genuine redundant prediction-allocation issue (host64-bit peak103,484), rather than a fixture-reference mismatch. The final candidate fixes HSplain1 modes1/9 by borrowing immutable accepted reference words instead of copying an identical prediction buffer. Modes2/3 retain their owned motion prediction; output semantics, tags and integrity checks are unchanged. Final native `hud.hpp` SHA-256 is `cd65e262b66efe5e5b70db685b8f6cc417d35c113cb34b902d23a49b6d77bd70`.

**Final V44 arena ceiling is restored to98,304bytes**, with the original114,688free/24,576largest initial admission and8,192per-allocation physical reserve unchanged. The isolated fixed-native test with modeled117,524free measured peak92,379, zero allocation failures and all63,360words verified. Host/model structure sizes and simulated free heap do not establish actual target fit; effective ELF SRAM and physical runtime minimum/largest/stack still require their separate gates. Earlier failed and larger-cap test logs remain historical evidence, not current configuration.

## Host gates completed

`python run-host.py` builds the actual C++ endpoint DLL and production Rust driver tests with modeled FPGA MMIO, plus the actual DYN1 parser. Final fixed-native evidence is `evidence/host-final-borrow01`:

- Driver21tests: original pair controls, actual distinct KEY/P/P including63,360actual HUD words written/readback-compared under the original98,304cap, invalid finite bounds before writes, missing third, lost third commit ACK, borrowed-reference allocation regression and low physical heap reserve on third. Native acceptance is not fabricated after the lost ACK/failure.
- Batch17tests: existing actual-native controls plus partial/ambiguous batch submission and future-ACK rejection.
- Wire8tests: framing/CRC/bounds, stored versus presented, explicit version1 rejection despite validCRC and version2 feedback.

All46tests passed against the final fixed native code and original arena cap. Earlier host01/02 failures are preserved: an initial test-harness fault was corrected, then the real third-frame arena refusal was found. Host03 proved the issue with a larger diagnostic budget; host04/05 validated the intermediate106,496ceiling. Those were superseded by the reference-borrowing repair and final original-cap regression. Tests are not target scheduling, actual SDRAM or complete FPGA proof.

## Bounded report export

The original single-line Debug report has been replaced by allocation-free synchronous `fmt::Arguments` export after the trial. Summary, word counts,5stage lines per slot,2arena lines and2IO/health lines remain separately labeled. Host tests cover maximum u64/u32/usize, every Error variant, zero frames and invalid maximum frame count; largest payload161bytes plus80-byte conservative prefix=241bytes, below300. Failure explicitly reports `partial_stages_retained=false`; driver partial timing arrays are not returned onErr and must not be inferred. This logging-only repair does not alter driver/native/RTL semantics. New target image/source identity is required after applying it.

## Offline gates completed; physical testing pending

Final-source three-frame selected-system RTL replay passed with V027, the corrected actual native code and original98,304-byte cap: all canonical bytes and1,036,800 composed pixels/borders match,3accepted/3presented, zero rejects/underruns,63,360 actual HUD readbacks. Final-source localhost socket integration also passed. Target03 compiled with unchanged input hashes; effective SDK/static SRAM guard passed at130,948bytes. The production updater parser verified13,290 app-only UF2 blocks and exact BIN round trip. Independent final review and short-record logging checks passed.

The selected package is `release-bounded3-v001`: ELF SHA`f92e3df64a104657957e0d9c86e7a1b79d4f07e2febb5f6fb40a6dd11da76110`, UF2 SHA`e2f5a90143015cefeea367158f957638de4eeac4bdc3838eb49077a70952c903`. Do not install target01/02 intermediates. See `evidence/readiness-v001/readiness.json` for exact executed evidence/hashes and [the hardware handoff](../../../docs/cu66-v71/V44-V027-HARDWARE-HANDOFF-20261107.md) for the controlled trial. Physical heap/stack/RF/SDRAM/LCD qualification remains pending; the overall manifest stays INCOMPLETE for that reason while its offline candidate gate is ready.

The expected first hardware trial is this exact original pair plus distinct retained frame2, with USB timing/counter capture and visual checks. It is historical Mass Effect-family content, not the requested two-minute source. Only after verified multi-frame lifecycle and measured service improvements should the actual full clip be attempted.

New source is about2.3MiB. Build/cache/evidence directories remain beneath `C:/moon`; no old C: root aliases are required.
