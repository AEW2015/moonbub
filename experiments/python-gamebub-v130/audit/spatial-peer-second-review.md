# V130 spatial and peer independent second review

## Scope

Read-only review of the V130 spatial and control-peer PASS receipts, their prepared preflights, V129 baselines, source snapshots, comparators, and derivation records. No simulations or builds were run for this review.

## Receipt and selector integrity

The spatial selector is `experiments/python-gamebub-v130/spatial-peer/spatial/results.json` (SHA-256 `89ef4b5e57f0b753b22afc5783e86cc8552e0cf03529072ddb8ed547dd2a92e3`); it selects `experiments/python-gamebub-v130/spatial-peer/spatial/attempts/20261111T025725692282Z/receipt.json`, whose SHA-256 is `d760b6cf0942ae37068b584f5c52c2d7dce49d72d6371fc29f34cd201153db10`. The spatial selector itself carries the receipt path but not its hash. The independent audit below binds both hashes.

The peer selector is `experiments/python-gamebub-v130/spatial-peer/control-peer/results.json` (SHA-256 `ebcba6709bd949c0281d0ce0842d937b65a4db2a722365d2ce0cef540712de67`); it selects `experiments/python-gamebub-v130/spatial-peer/control-peer/attempts/20261111T031628229116Z/receipt.json` and pins that receipt at SHA-256 `06218321edcea51cd027094e46bcc5a78791bd56bdb48f82c9fcaf4c443ec6bf`.

Independent evidence is recorded in `experiments/python-gamebub-v130/audit/spatial-peer-independent.json` (SHA-256 `8abb24dc9e9070686fb4100637aa11c8fcfcc16063d5cb6e9e6e28ad76d235a4`, status `PASS_V130_EXPLORATORY_SPATIAL_PEER_EVIDENCE`). It pins the V130 receipt hashes above and the V129 baselines:

- Spatial baseline receipt `experiments/python-gamebub-v129/integrated-study/spatial/attempts/20261111T000845338598Z/receipt.json`, SHA-256 `d894da1d351e81d77e486a37c0037f869ce2e7361d8245c3d365df55fa0c4903`.
- Peer baseline receipt `experiments/python-gamebub-v129/integrated-study/control-peer/attempts/20261111T001501995181Z/receipt.json`, SHA-256 `e8f249079a4a9813808efe9c6e86ba49f518dec12ec77ead331361c79190740a`.

## Source snapshots and artifact hashes

The V130 spatial receipt lists 108 source hashes and 108 output artifact hashes; the peer receipt lists 121 source hashes and 112 output artifact hashes. I recomputed each listed hash against its saved file: all source snapshots and output artifacts matched. Both receipts report actual RTL execution, Verilator, strict warnings, and no disabled or downgraded assertions. The peer receipt reports zero removed original oracle checks.

Comparing V129 and V130 `source_origins`, both runs retain the same origin keys and differ at exactly one origin: `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv`, now sourced from `fpga/experiments/cu66-v130-spec-read/cs88_admission_v91i2a.sv` with SHA-256 `0b7131bbccc7c9cbc794b51a205210a32138f74bc751d5d8679a87745acb7168`. The ordered RTL inputs are unchanged except for that admission source path at the same position. The frozen preflights are `PREPARED_NOT_RUN`; both state that actual V129 stdout/event/canonical bytes must match, no new comparator masks are allowed, whole-parent timing/board qualification is false, and hardware contact is false.

## Comparator review

The spatial runner uses the frozen V129 spatial receipt as its comparison source and requires byte-exact simulation stdout for both candidate seeds (107601, 107602) and both custom-transport seeds (107601, 107602). It also compares decompressed event and canonical outputs against V129 raw streams. I independently checked all four seed/type pairs: stdout, events, and canonical bytes match exactly. The audit records those raw hashes and byte counts. The runner derives from the V129 spatial script with explicit edits; its derivation says zero parent-oracle checks removed and zero masks added. The candidate receipt says the old exact checker was not modified and all original functional oracles were retained.

The peer runner resolves and verifies the V129 peer stage closure, records V129 simulation/event/canonical inputs in its source snapshot, and compares raw stdout plus decompressed event and canonical streams for seeds 115501 and 115502. I independently checked both pairs: all three streams match byte for byte. Peer checks also retain the canonical retry, accepted read/write, queued replay, prepared-child fault injection, and six parent abort/reset cases across all three scratch preparation boundaries. The derivation and receipt record zero removed original oracle checks and no comparator masks.

## Limits

These PASS receipts establish the recorded exploratory RTL runs and the stated V129 raw-stream comparisons for the frozen inputs. They do not establish all-public-port cycle equivalence: both receipts explicitly mark that comparison false. The focused data contract only compares `replay_data` when `replay_rsp_valid` and `stage_read_data` when `stage_read_rsp`; invalid-cycle data may differ, and the external debug-consumer contract remains unverified. The independent audit also marks hardware and timing qualification false. These results therefore do not prove board behavior, timing closure, or that arbitrary invalid-cycle consumers are unaffected.
