# V117 baseline inventory (V116 parent)

This is an additive, read-only baseline inventory for the V117 throughput and
read-validation work. Baseline commit is `971279616a3025426f5d21a56a24cf2cefc50374`
(`publishedV116`); branch is `study/gamebub-v117-read-validation-throughput-20261109`.
The independently retained audit is
[`baseline-v116.json`](../../experiments/python-gamebub-v117/audit/baseline-v116.json).

## Accepted parent evidence

- C is the best measured 125 MHz component candidate: WNS −1.847 ns, TNS
  −7365.672 ns, 16,725 setup endpoints fail. Hold WNS is +0.092 ns with zero
  failures; pulse margin +2.750 ns with zero failures; all routable nets routed
  and zero routing errors. The classification is route completed, timing fail,
  signoff open. This is component timing, not complete-parent timing closure.
- The selected actual-RTL LIVE parent result is 1,416,449 cycles for fast row
  service and 1,844,338 stalled; byte control is 4,166,111 fast and 9,873,327
  stalled. It checks 518,400 canonical plus 42,240 HUD bytes, 1,025 hash jobs
  and abstract publication. It uses software HUD decoding and abstract memory
  service. It does not establish achieved hardware latency or sustained 30 fps.
- Canonical no-header accounting is 4 main/transport TSVs × 12 records = 48
  records and 24,883,200 sample bytes. Peer accounting is 2 × 14 = 28 records
  and 14,515,200 sample bytes. These are comparisons, not sustained-stream
  frames.
- No full parent has achieved routed 125 MHz timing; no hardware validated
  decode under 10 ms or sustained hardware 30 fps is established.

## Source receipts and pins

| Evidence | Path | SHA-256 |
|---|---|---|
| C native raw receipt | `experiments/python-gamebub-v116/control-c-study/native/20261109T081825861048Z/receipt.json` | `0538b8b2c533638851923ba2508cb51d0f30c25c8607f6961fe038e6258b4ffc` |
| C native terminal audit | `experiments/python-gamebub-v116/audit/nativeC125-terminal.json` | `5c6c68b28e268aa3f52cce22622255e4c930fff2fedcfafe2133c1a59b7b3033` |
| C LIVE raw receipt | `experiments/python-gamebub-v116/control-c-study/live-parent/attempts/20261109T081648108920Z/receipt.json` | `080c4d0b59b80fb4612445ffe92b2025012ab6d21d5882372b78529dba4a0853` |
| C LIVE selector | `experiments/python-gamebub-v116/control-c-study/live-parent/results.json` | `3087bebfebabebcaa0a3dffa54cc5a4eb930ec66b42564fe9f7a8a13e10fe1a9` |
| C LIVE terminal audit | `experiments/python-gamebub-v116/audit/live-c-terminal.json` | `bbb077d3193ee75d51832ecc388285dfb633a7cfbdf0a6a4aecf0d2d20d290d1` |
| Final bundle audit | `experiments/python-gamebub-v116/audit/final-bundle.json` | `78347fe1c286b020f8ba53f73096185d15346f51472a515586c8df7596b2bab6` |
| Results selector | `experiments/python-gamebub-v116/results.json` | `516ab78120effa6b4831b3dff90ecb3d469dec6bddc52ff5f2fe86794d50266c` |

The selected C native audit rehashed 99 archived and 72 external artifacts;
source alias count is 18 and source pin mismatches are zero. The C LIVE audit
rehashed its selected receipts and confirms four exact A-parent field matches
(`live_case`, fences, service, verdict). The final bundle audit reports 155
result pins checked with no mismatches. Its publication inventory is Git-eligible
V116 scope; ignored attempt-local `build/` compiler/trace products are excluded,
not treated as publication artifacts. The pre-existing untracked
`fpga/experiments/throughput30/burst/marker-recovery/` remains protected and
outside this inventory.

## Interpretation boundary

The 125 MHz native result is setup FAIL despite clean hold, pulse and routing.
The LIVE result is a selected component in an abstract publication harness.
Neither is proof of a complete parent, physical SDRAM behavior, an achieved
clock, hardware under-10-ms decode, or sustained distinct-frame 30 fps.

## V117 current measurement snapshot

This additive snapshot was taken on 2026-11-09 after the selected A125 and B
component receipts completed. It records component evidence and current open
work separately; `RUNNING` or mid-campaign receipts are not terminal results.
The independently checked A125, B full, and cycle-comparison records are in the
V117 audit directory.

- A read composition: 44 directed candidate profiles across two seeds and 24
  successful custom-transport profiles plus four abort/reset retries. Four
  canonical no-header streams contain 12 records each: 48 records and
  24,883,200 samples. Selected receipt:
  [`read spatial`](../../experiments/python-gamebub-v117/read-study/spatial/attempts/20261109T110439596315Z/receipt.json).
- B throughput composition: the same profile/record counts, with each of its
  four canonical streams byte-identical to the frozen V113 canonical output.
  Its initial stale held-output fixture failure is retained separately; the
  corrected full harness recipe is pinned in the terminal receipt. Selected
  receipt:
  [`throughput spatial`](../../experiments/python-gamebub-v117/throughput-study/spatial/attempts/20261109T114031167273Z/receipt.json).
- The independently reviewed cycle report covers 44 A/B event rows. The 24
  successful full-frame rows save 5.269–23.409% in measured component cycles.
  Two profile-1 error-147 malformed partial outputs differ in sample count;
  they carry no exact partial-output or savings claim. This is bench-cycle
  evidence, not native clock or end-to-end latency evidence.
- A125 completed a fresh OOC RTL route at the fixed 8 ns target. WNS is −1.925
  ns, TNS −9909.251 ns, and 19,863 setup endpoints fail. Hold WHS is +0.099 ns
  and pulse WPWS +2.750 ns, both with zero failing endpoints; 73,346/73,346
  routable nets completed with zero errors. Its selected worst path is ingress
  `size_bytes_reg[1]/C` to `offsets_reg[0][0]/CE`, 16 logic levels. This is
  worse than V116C125 (WNS −1.847 ns, TNS −7365.672 ns, 16,725 setup failures).
  The retained reports are under
  [`A125 native reports`](../../experiments/python-gamebub-v117/read-study/native/20261109T113046956485Z/reports/).
- A peer remains the selected peer PASS: 28 canonical retry records and
  14,515,200 sample bytes. The current B peer receipt visible at snapshot time
  had one seed verdict and another simulation command in progress; its
  provisional `FAIL` status is not terminal and is excluded from passing
  campaign counts. The B peer slot must be treated as active until Root records
  its terminal result.
- The selected A LIVE parent attempt was still `RUNNING` before its actual RTL
  command completed. B LIVE has a retained actual-RTL `FAIL` on cancel-time
  local traffic; keep that failure visible and do not count it as a passing LIVE
  result. The independent read LIVE retry remains open. None of these results
  establishes full-parent 125 MHz timing, hardware-validated sub-10-ms decode,
  or sustained hardware 30 fps.

The source-bound per-attempt receipts and raw timing reports remain the
measurement records; this inventory does not replace them.
