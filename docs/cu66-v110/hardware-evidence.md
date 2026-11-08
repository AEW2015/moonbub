# Offline V110 hardware-evidence numeric checker

[hardware_evidence.py](../../scripts/cu66-v110/hardware_evidence.py) checks numbers and file pins in a **proposed trace contract**. It reads local files only. It defines no implemented register map, telemetry firmware, device capture mechanism or device-counter assignment, and makes no hardware contact.

The normative requirements remain [the V110 hardware gates](hardware-gates.md) and [the development plan's product milestones](../gamebub-v91-v110-development-plan.md#product-milestone-gates): 1,800 distinct 720×480 frames over 60 seconds, followed by 18,000 over 600 seconds at fixed 30-Hz source releases; intended displayed identity, reference/pixel/HUD/hash integrity, finite queues and zero underruns; then **every** packet-complete → validated-publication sample strictly below 10 ms. Complete-parent integration, real contention and hardware qualification remain open.

Run the checker against a manifest and its actual pinned local files:

```bash
python3 scripts/cu66-v110/hardware_evidence.py capture.manifest.json --output numeric-result.json
```

Exit status is zero when the supplied numeric gates pass and two otherwise. JSON output always separates `numerical_gates_pass`, `evidence_kind`, `hardware_execution_verified` and `hardware_acceptance`. **The last two are always false offline**, including when a manifest labels itself `hardware_capture`. Synthetic results can pass arithmetic checks only. A capture label, matching file hashes and self-declared validation flags cannot attest that a device executed or that the trace represents complete real contention, correct calibration, real pixels or safe publication.

## Proposed manifest contract

The manifest is JSON with `schema: "v110-hardware-evidence-proposed-v1"`. Artifact pins are objects containing `path` and lowercase 64-digit `sha256`. Paths resolve relative to the manifest, with explicit absolute paths also supported. The checker requires the actual files to exist and hashes their bytes. It hashes the JSONL trace again while consuming it and rejects a concurrent change. It retains the manifest hash and verified artifact paths/hashes in its output.

| Field | Required meaning |
| --- | --- |
| `evidence_kind` | Exactly `synthetic` or `hardware_capture`; this is an input classification, not authentication. |
| `coded_width`, `coded_height`, `profile_id` | Exactly 720 and 480, plus a nonempty negotiated/profile identity. These are declarations, not pixel-content proof. |
| `calibration` | `kind`, `clock_id`, positive integer `tick_rate_numerator` and `tick_rate_denominator`, plus an `artifact` pin. No default frequency exists. |
| Calibration artifact | JSON repeating the same kind, clock identity and rational tick rate, with a nonempty `method` description. Kind must be `synthetic_fixture` for synthetic data or `measured` for a capture claim. The checker verifies consistency and the file hash, not the measurement's physical validity or uncertainty. |
| `provenance` | A nonempty list of actual artifact pins. Capture procedures can pin firmware, bitstream, capture tool, setup and clock-measurement evidence here. No particular implemented telemetry interface is implied. |
| `counter` | Explicit `clock_id`, integer `width_bits` in 1–64, nonempty `reset_epoch`, `wrap_policy: "explicit_wrap_count"`, and `reset_policy: "single_epoch"`. |
| `source_release_schedule` | Exactly `floor_30hz_from_window_start`, the scheduling convention proposed below. |
| `queue_capacity` | A positive integer fixed bound applying throughout both windows. |
| `windows` | Exactly two ordered, nonoverlapping objects: first a 60-second interval, then a 600-second interval. Each has unique `id`, `start`, `end` and complete-interval `health`. |
| Window `health` | Zero nonnegative integer totals for `underruns`, `hash_failures`, `reference_failures`, `hud_failures`, `pixel_failures`, `queue_overflows`; `queue_bounded: true`; and `max_queue_depth` no greater than capacity. Its peak must cover every per-frame depth. These totals cover the entire interval, including gaps between frame records. |
| `trace` | Artifact pin for the JSONL per-frame file. |

All timestamps use the same declared calibrated counter and the same reset epoch:

```json
{"tick": 1234, "wrap_count": 2, "reset_epoch": "capture-epoch-identity"}
```

`tick` must fit the explicit counter width; `wrap_count` is a nonnegative integer. Absolute ticks are `wrap_count * 2**width_bits + tick`. There is no inferred wrap, guessed epoch, inferred timebase or addition of unrelated clock-domain counts. A reset-epoch mismatch is rejected. This initial proposed contract supports a single common-counter epoch spanning both windows; captures with resets or independent clocks require an explicitly revised correlation/epoch contract, not silently repaired timestamps.

Window durations are checked exactly using rational arithmetic: `(end-start)*rate_denominator == seconds*rate_numerator`. The proposed source schedule is likewise explicit: release `i` is `start + floor(i*rate_numerator/(30*rate_denominator))`. This fixes the input sequence without assuming that 30 divides the counter frequency. It is a deliberately strict proposed schedule, not a claim that production capture already implements zero-jitter releases. A different allowed jitter/scheduling policy needs a reviewed contract revision. Stalls, repeated frames or missing releases are not normalized away.

## Proposed JSONL frame contract

One record describes one complete intended source/publication/display identity, in window order and source-release order:

| Field | Check |
| --- | --- |
| `window_id` | References one of the two declared windows; trace order cannot return to the earlier window. |
| `frame_id` | Nonempty string, globally unique across both windows. |
| `source_frame_id`, `published_frame_id`, `displayed_frame_id` | Each exactly equals `frame_id`. A repeated publication or mismatched displayed/source identity fails. |
| `source_release`, `packet_complete`, `validated_publication`, `displayed_at` | Explicit timestamps as above. Require `window.start <= release <= packet <= publication <= displayed < window.end`; displays strictly increase. |
| `flags` | Boolean true for each of `validated`, `pixels_valid`, `reference_valid`, `hud_valid`, `hash_valid`, `ownership_valid`, `displayed`. No omitted or truthy substitute passes. |
| `hash`, `expected_hash` | Matching lowercase 64-digit SHA-256 strings for the declared content/reference contract. The offline tool compares supplied digests; it does not recompute pixels or establish the independent expected-content oracle. |
| `underruns` | Nonnegative integer zero. |
| `queue_depth`, `queue_bounded` | Nonnegative depth at most declared capacity and literal true bounded flag. Full-window peak/health totals supplement these samples. |

The trace must include every scheduled source frame. At least 1,800/18,000 globally distinct completed displayed records are required in the respective exact windows. The fixed release schedule and half-open window bounds also prevent adding extra out-of-window records to repair a deficient count. Counts and identities establish supplied-trace distinctness, not independent physical image novelty or device provenance.

For latency ticks `L` and supplied tick rate `N/D`, the strict comparison is **`100 * L * D < N`**, using integers. Exactly 10 ms fails. No rounded milliseconds, average or percentile decides this gate. The tool also reports min/median/p95/p99/max in milliseconds, nearest-rank p95/p99, and the worst frame ID, trace line and exact latency ticks. The packet-complete/publication fences are declarations in this proposed trace contract; production firmware must separately establish that those fences include entropy/reconstruction, memory waits, all content/reference/HUD checks and safe ownership publication.

## Bounded synthetic self-test

The [self-test](../../scripts/cu66-v110/tests/test_hardware_evidence.py) constructs 1,800- and 18,000-frame fixtures independently in an external `/tmp` directory, including thousands of explicit 16-bit counter wraps, then deletes that directory. No large JSONL fixture is stored in the repository. It tests duplicate/repeated IDs, missing calibration/wrap policy, invalid ticks/wraps/reset epoch, one exact-10-ms outlier despite a 5-ms median, hash/reference/HUD/underrun failures, short windows, missing frames, source-release stalls, overflowing/unbounded queues, window-wide errors, missing or changed provenance and wrong resolution. An adversarial capture-labelled synthetic fixture also proves that a label cannot turn on either hardware-verification flag.

The final run passed **12 tests / 23 findings** in 3.17 seconds, with 28,228 KiB maximum RSS, under an explicit 256-MiB address-space limit and 55-second CPU limit. The [small receipt](../../experiments/python-gamebub-v110/hardware-evidence/selftest.json) retains source hashes, ephemeral input hashes, numeric results and false hardware-verification/acceptance flags. Receipt SHA-256: `0e793e6855bae041b3435f97dd1ff5c159ad5ebecd24f7b1c283bfae307dbd03`. The [test transcript](../../experiments/python-gamebub-v110/hardware-evidence/selftest.log) is retained. **This is synthetic checker preparation, not hardware qualification.**

To repeat the bounded self-test from the repository root:

```bash
ulimit -v 262144
ulimit -t 55
V110_HARDWARE_EVIDENCE_RECEIPT_DIR=experiments/python-gamebub-v110/hardware-evidence \
  python3 scripts/cu66-v110/tests/test_hardware_evidence.py
```
