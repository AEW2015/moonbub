# V119 guarded parent results

The independent LIVE parent audit passes. V119 retains V118’s exact accepted bytes, ordered transform/canonical events, hash-job owners and cycles, and all six terminal record dictionaries for the four tested byte/row profiles. This qualification demonstrates functional preservation of the timing cuts; measured simulated cycle counts did not improve.

Audit: `experiments/python-gamebub-v119/audit/live-expert.json` (`18e3bc243b64744e1d54138df890bb66ecc662abbf8baf15ef1a4936b9bb087d`).

Selected receipt: `experiments/python-gamebub-v119/integrated-study/live-guard/attempts/20261109T170133436719Z/receipt.json` (`0cd25f1e3dec9c92526cde6b7b02ee0498df0e6be51837a9de7857d390fb436a`).

## Independently checked evidence

- Every selected source hash and all 86 retained artifact hashes match. The selected 18-source component identity matches the LIVE parent; reversible source derivation and all inherited C++ `need()` checks remain intact.
- All 518,400 canonical bytes match the independent golden. Accepted memory contains exactly those bytes plus 42,240 HUD bytes. Each profile’s 1,025 SHA/C2 leaf, empty-leaf, node, HUD and seal jobs were independently reconstructed in Python from those goldens; digests, owners and complete ordered job/cycle records match.
- Canonical and HUD producer/request/successful-ACK/hash byte counts agree. Every hash delivery is checked in the retained C++ bench against memory written by a successful matching ACK in the current epoch; commit follows root, HUD hash and seal completion.
- The wrong-token ACK is actually offered and accepted once. The original physical write lease survives error 0x81, retires only on the matching response, and the failed frame never publishes. A clean retry succeeds without reset. All physical write/reference/scratch owners drain before final publication.
- All four profiles retain 33,384 raw synchronous replay reads and 33,384 matching responses, with zero terminal raw pending debt. One discarded elastic input is accounted for by accepted = delivered + discarded.

## Parent fault boundary

The parent immediately revokes public request/input/cache/hash/HUD/start eligibility at fault. Producer-local cancellation crosses the preserved one-edge register boundary; the observation guard does not mask the raw internal work or its physical replay response. Each profile actually observes one first-fault gap and one private residual handshake, whose full owner/order/value is checked against the independent golden. Registered or external cancellation allows no later raw residual/read offer.

These fixtures contain no private gap-local read and no revoked replay response. They therefore do not prove those cases were exercised, or establish general simultaneous-fault priority. Existing focused reference/physical-debt and peer tests remain separate evidence.

## Latency result

| Service | Profile | Last outer byte → validated commit cycles | At 125 MHz, conditional | At 100 MHz, conditional | V118 delta |
| --- | --- | ---: | ---: | ---: | ---: |
| byte | 0 | 3,704,705 | 29.637640 ms | 37.04705 ms | 0 |
| byte | 1 | 9,484,147 | 75.873176 ms | 94.84147 ms | 0 |
| row | 0 | 1,145,104 | 9.160832 ms | 11.45104 ms | 0 |
| row | 1 | 1,553,197 | 12.425576 ms | 15.53197 ms | 0 |

Profile 0 uses the fast finite-service rule; profile 1 adds bounded stalls. The 1,145,104-cycle fast row profile would be 9.161 ms at a demonstrated 125 MHz parent clock; the stalled row profile would take 12.426 ms. Both row cases exceed 10 ms at 100 MHz. These arithmetic conversions are not validated hardware decoding times.

The service model uses a bounded single-lease 16-bit bus with explicit transfer/overhead cycles. HUD semantic decode remains software while SHA/C2/HUD/seal validation runs in RTL. This test uses one independent keyframe plus fault recovery per profile. It does not demonstrate physical SDRAM operation, sustained distinct-frame 30 fps, worst-case gameplay latency, or a routed full-parent clock. Native component routing and eventual hardware measurements remain required.
