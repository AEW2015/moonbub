# V67 final evidence audit

Audit date: 2026-11-05. Scope: the [six-hour report](custom-codec-prototype-v67-2026-11-05.md), [hardware/software handoff](gamebub-v67-hardware-research-handoff.md), [figure and table evidence](figures/prototype-v67/evidence.json), render source, frozen result rows, retained verification logs and relevant protocol/receiver contracts. This review did not encode new media, run a new campaign or modify frozen implementations/results.

**Assessment:** the corrected documents support a research handoff for implementing and measuring the proposed pipeline. They do not support a deployed codec, total-memory fit, better compression than HEVC/AV1, or physical 30 fps. The native comparison and figure are numerically consistent with the stored rows. The remaining limitations below must travel with the handoff.

## Corrections checked during review

| Item | Corrected interpretation |
| --- | --- |
| Legacy SHA call total | New-profile spies cover all 577 receives/profile. The legacy 1,705 calls are calculated from the directed-test-validated schedule: 26 keys × 2 + 551 P frames × 3. They were not directly spied on all 577 legacy receives in that campaign. The report now states this distinction. |
| Integrated receiver compatibility | V48 supports arithmetic dispatches 5/6, not every legal CS38 packet. Legacy dispatches 0–4 require a separate tested path or explicit restricted-capability selection; frozen v43 is the compatibility control. The handoff now names this restriction. |
| Candidate profile negotiation | CS66/CU66 are explicitly configured Python profiles at fixed epoch 25 and 720×480. Live capability negotiation is not implemented. The report and handoff no longer imply that a handshake exists. |
| Native packet accounting | Native complete sizes include actual AU/HUD/extradata lengths plus an 80 B binding allowance. No deployed native wrapper was serialized by that comparison. The report now states the distinction. |
| Packet cap | The 49,152 B experimental comparison/profile cap is distinct from the current JPEG transport parser's 262,144 B acceptance bound. Neither proves available BRAM/SRAM. The report now distinguishes them. |
| Source provenance | The source-v40 manifest has hashes and formation details, but its reviewed shared provenance manifest does not document the original 1600/combat extracts. The report now retains this limitation. |
| Scanout output lifetime | The 7,200 B logical row-data bound assumes one outstanding returned line. Additional queued/retained lines need their own storage bound. This assumption is now explicit. |
| Hash finalization | Bad input during an active context poisons it; input after a successful finish raises while the completed digest remains idempotent. A controller must honor that exception and abort an unpublished transaction rather than reuse a completed tag for another frame. The corrected report and integration audit retain this obligation. |

The [separate integration audit](v67-integration-audit.md) covers bank leases, normalization before hashing, SHA strip fill/drain and publication fences in more detail. Those are implementation obligations, not additional completed system tests.

## Native/custom comparison and figure

The figure's three input hashes match their actual files. I independently rebuilt all 77 plotted records from per-frame rows rather than trusting plot summaries, including complete sizes, channel-sample-weighted MSE, nominal rate and cap failures. I also independently reselected the eight displayed table winners from all native rows and both fixed display options using integer mean-error and complete-packet-cap gates.

The resulting table is:

| Clip | Custom strong bytes | HEVC bytes | HEVC fewer | AV1 bytes | AV1 fewer |
| --- | ---: | ---: | ---: | ---: | ---: |
| 10000 | 359,645 | 185,445 | 48.44% | 177,871 | 50.54% |
| 4500 | 554,439 | 295,226 | 46.75% | 282,462 | 49.05% |
| 1600 | 95,180 | 41,520 | 56.38% | 32,728 | 65.61% |
| Combat | 776,074 | 520,851 | 32.89% | 485,066 | 37.50% |

All eight winning native options actually use the same strong display filter as the custom baseline, although the declared selection algorithm also permits native identity filtering. All qualify after filtering and have zero complete-packet-cap failures. This avoids incorrectly carrying forward v62's pre-filter anchor: the earlier combat AV1 anchor fails the equally filtered zero-motion mean-quality gate and is not the displayed winner.

The comparison charges actual access-unit bytes, exact HUD, a common binding allowance and extra data once. Source IDs are 24–47 for both sides; native PTS 0–23 are an encoding-local numbering scheme, not new source identities. The common input conversion and original RGB565 metric reference are retained. Quality is squared error of expanded RGB565 channel values on the active crop, with exact HUD checks, not squared numeric differences between packed 16-bit words.

Important boundaries:

- These are sampled minima under the **mean** quality gate. A mean winner need not be no worse on every frame. Mean-plus-peak and every-frame gates remain separate in the comparison artifact.
- The plot contains 69 native parameter-point instances and eight custom instances: 77 records but only 72 distinct plotted coordinates. Some combat rate-control settings produce identical points. These are not 77 independent sources or distinct compression outcomes.
- Eight native parameter-point instances contain at least one cap failure. The figure retains their crosses and the displayed table excludes them. The plot does not interpolate an optimal encoder frontier.
- The figure's horizontal axis is `complete_bytes × 8 × 30 / frame_count`, a nominal rate normalization. It is not measured Wi-Fi goodput, source capture rate or endpoint presentation throughput.
- Native CPU x265/SVT output is a compression reference. It does not establish an implementable decoder with equal FPGA resources, encoder latency, or the behavior of Sunshine/NVENC on the eventual live host.

The PNG was also inspected: the sampled-point caption, cap-failure markers, quality-trading mixed-motion legend and nominal-rate axis convey these limits. Exact HUD restoration is shared by the compared wrappers; it is not exclusive evidence of a custom-codec compression advantage.

## Source counts and repeated use

The source-v40 manifest contains 119/119/119/100 frames, with **457 distinct RGB24 canvas SHA-256 values** across the four clips. The declared PTS windows and source formats match the report: three `[6,10)` intervals at reported average rate 747/25, and one `[20,24)` combat interval at 25 fps from 512×288 material. The latter is upscaled into the chosen canvas; none is an uncompressed native-30-fps capture.

The fresh native runs contain 5,484 + 2,100 + 1,152 + 504 = **9,240 access-unit instances** across 48 + 21 + 48 + 21 = **138 parameter-point instances**. That count describes actual encode invocations/output records, not 9,240 unique captured frames or unique bitstreams. Later native/filter work reuses the same 96 source canvases at IDs 24–47.

The v66 decoder campaign's **577 presentations** are 24 + 96 + 457 retained records across eight histories, with 553 unique old packet digests. They must not be added to 457 to advertise a larger unseen-source dataset. Packet uniqueness is also not capture uniqueness.

The v67 full-filter extension covers all 457 existing causal frames, including **265** after ID 47 across the four sequences. It does not add new source media. This distinction is preserved in the report. The provenance gap for two extract origins and the related/precompressed single-game lineage remain reasons not to generalize the outcome to Elden Ring, Deadlock, new captures or unrelated games.

## Quality and timing claims

The independent [v67 replay](../experiments/python-game-filter-qual-v67-study/verify.log) checked all 157,939,200 strong-filter luma samples, 9,651,840 exact HUD words, 2,212 producer input pins and 384 overlapping identity/strong variants against frozen v60/v62. All 457 frames improve source SSE, with no ties/regressions in this corpus. Aggregate SSE 8,266,662,386 → 8,055,798,880 gives weighted MSE 20.67784268 → 20.15039857, a 2.55077% reduction. The preset was fixed before the later window; encoded bytes and canonical references remain unchanged.

This is evidence for the stated error metric on these retained inputs. It is not subjective quality, perceptual noise, motion clarity or flicker proof. The directed perfect-source counterexample shows that the same fixed filter can worsen other input. The report's defined grid-error-jump improvement is likewise not a subjective flicker measurement.

The reported mixed-motion trade is also consistent with the row totals: the first window saves 0.9613% of complete bytes while increasing source SSE 1.6849%; the later window saves 1.2929% while increasing SSE 4.5148%. Local Pareto checks did not constrain future distortion over a changed reference history. These policies should not be described as lossless or quality-preserving defaults.

Python timing scopes remain separate:

- V42's approximately 4× gain is a HUD component-stage comparison with upstream HUD generation excluded.
- V43 removes proof-adapter overhead; v48's bounded tile receiver is slower in Python and has a different baseline campaign.
- V64's host row-model time includes assertions/hashes and is not a native scanout clock.
- V66's measured whole-call mean medians are 77.038744/76.135247/75.938611 ms for CS38/CS66/CU66. The small 1.17%/1.43% differences were observed under a non-isolated workload and do not establish reliable target speedup.

The SHA arithmetic is correct: an i16 canonical tag has 1,036,804 preimage bytes / 16,201 padded SHA blocks; the validated u8 domain has 518,404 bytes / 8,101 blocks. At assumed one round/cycle and 100 MHz, the serial-round scenarios are 31.10592 ms for three i16 passes, 10.36864 ms for one i16 pass and 5.18464 ms for one u8 pass. This is **not** synthesized cycle timing, a measured clock, memory traffic, or a latency budget for the whole decoder. Other HUD/CRC integrity work still exists. CPU ratios, inverse-product savings, bus inequalities and SHA ratios must not be multiplied or added into a system 30 fps claim.

## Storage, ESP32 and hardware gaps

The row and strip bounds describe logical payload ownership. V64 excludes external canonical/reference banks, HUD, mask, metadata, temporaries, FIFO depth, ports, alignment and CDC. V67's 5,760 B hash strip additionally needs a transient serialized row, SHA state and a real stall-safe fill/drain schedule. The two components operate at different frame lifetimes; safe sharing is not proved. A compact rectangle-based mask program can replace the full boolean mask oracle in a separately checked design, but its small constants/row buffer do not establish total memory fit or change the frozen v64 proof's exclusions.

The current source-based forwarding budget correctly follows the 40 B header / 1,024 B chunks and requests 1,065 runtime DMA-buffer bytes. It does not include the complete ESP32 heap, Wi-Fi/socket buffers, SDK descriptors, stacks or UI state. Its 7,988 hypothetical CS38 fragments and 4.46248 Mbps mean / 11.26944 Mbps maximum frame-equivalent L3 requirements omit RF airtime, retransmissions and other traffic.

For the largest 44,032 B frame, `16×43 + 2×44032` ideal SPI phase clocks at assumed 40 MHz give 2.2188 ms. The approximately 491 µs/fragment allowance subtracts an **assumed**, unmeasured 10 ms reserve. Unknown successful-path CPU/CRC/lock/MMIO/SDK/jitter work must fit that residual; the inequality does not demonstrate that it does. Failure sweeps retain misses. A shorter hypothetical network header does not reduce payload QSPI work and is not an implemented replacement protocol.

The existing Rust/FPGA backend is JPEG-only. A codec-1 parser can structurally accept mislabeled arbitrary payload bytes and return a completion ACK without proving those bytes are a decodable JPEG or a displayed frame. CS38, CS66 and CU66 require new capability handling and a matching FPGA decoder. Unkeyed CRC/SHA fingerprints provide no traffic authentication; readonly Python state/cached tags provide no general DDR ECC proof.

Before a physical result, engineering still needs the fitted FPGA and panel geometry, DSP/BRAM mapping and signed widths, routed clocks and ports, full bank format/capacity, memory arbitration, normalized-tile hash integration, bank/HUD lifetime fences, reset/recovery behavior and end-to-end timing with input/audio/UI active. Reference publication and safe display-front switching are distinct events. The handoff's requirement for at least ten minutes of unique completed presentations, bounded queues, drops/repeats and latency distributions is appropriate; the existing Python evidence does not satisfy it.

## Publication check

The reviewed unit inventory contains 79 passing new test cases across 17 logs; every listed log has the matching `Ran N tests` line and ends in `OK`. Stored replay and render helpers read retained evidence rather than initiating new encoding. The final helper count must come from the regenerated inventory after any additional proofs are included. Stored replay is distinct from reproducing native encoding with another library build.

Regenerate the final provenance inventory **after** all report, handoff, figure and audit edits, include this audit, then run the portable verifier so its post-replay hash checks cover the final publication. This audit adds no benchmark or hardware result. The final claim should remain: independently verified component/reference models and a constrained research handoff, with compression still behind the sampled HEVC/AV1 references and hardware capacity unproven.
