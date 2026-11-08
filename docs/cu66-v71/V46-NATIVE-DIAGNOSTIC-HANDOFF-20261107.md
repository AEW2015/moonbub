# V46 native-failure diagnostic handoff

V46 is an observational ESP32 update for the [V45 cached12 frame3 failure](V45-V027-CACHED12-FAILURE-20261107.md). It is not a decoder fix. V027, sequence-v3, native arena/reserve, ingress caching, ownership and admission semantics remain unchanged.

Selected application: `firmware/experiments/v46-dy71-native-failure-20261107/release-native-diagnostics-v001`.

- ELF SHA-256: `bd955c61ac3f23660b79edfcfdd79b1eb3f4c2fbe06ac5f916bdcd4da18ade10`.
- UF2 SHA-256: `290787f711908dac1283d6fe6ac9bdd37f5367d5fc7816465ec11f7b946ac674`.
- Static SRAM 132,060 bytes; guardrail 163,840. Effective SDK configuration checked.
- Production updater parsed all 13,680 blocks and verified application-only addresses and binary round trip.
- 77 Rust host tests, actual-native allocator exception checks and 253,440 golden HUD-word comparisons passed. Target source was unchanged during compilation. Independent review found no blocking defect.

The retained failure snapshot adds the actual last native opcode/identity, wrapper stage/FFI result, response argument, payload-check mask/tags, bounded native error text, allocator failure reason/request and valid heap samples. Six failure-only passive FPGA reads retain per-field errors; these are sequential observations, not an atomic snapshot. Fixed diagnostic storage and failure work can perturb memory layout/timing.

Hardware sequence:

1. Keep Windows stopped. Install the verified app-only UF2 through the existing physical update-mode workflow, clearing V45's retained failed endpoint. Verify exact post-reboot ELF and reset reason.
2. Before Wi-Fi or FPGA mutation, run USB `I`, the separate CPU-only twelve-frame HUD check. Preserve per-frame CRCs, native errors and measured stack/heap. This cold test cannot reproduce network-time fragmentation. Do not continue on a failed or incomplete result.
3. Reload the same qualified V027 after normal ownership/memory checks. Coordinate the pinned sequence-v3 uploader and arm one cached12 attempt only. Do not reinterpret changed behavior as a fix.
4. Freeze and validate the complete paced export and read-only re-export. Reconcile Windows status2/status3 results. Select the next fix only from the actual failure evidence. No long video, audio, controller or retry during this diagnostic trial.

Physical V46 runtime and maximum target stack use remain unverified. V45/V027 is still installed and held at its frame3 failure when this handoff is written. Exact evidence is indexed in the candidate's `evidence/readiness-v001/readiness.json`; no new FPGA build or V46 full-system RTL replay was performed.
