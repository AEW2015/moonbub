# V114 SR14 syntax byte-cost audit

Read-only audit of the selected [`results.json`](../../experiments/python-gamebub-v114/syntax/results.json), its selected attempt, source/artifact pins, host completion, and `rows.csv`. The machine-readable audit is [`syntax-final.json`](../../experiments/python-gamebub-v114/audit/syntax-final.json). No code, tests, builds, or native study were run in this review.

## Selected evidence

Selected attempt `20261108T223815361379Z` reports `PASS_PYTHON_NATIVE_RESTART_CHUNK_ROUNDTRIPS_BYTE_COST_ONLY`: six retained CS88 packet fixtures, 48 real version/chunk profiles, eight synthetic version/pattern profiles, 784 malformed-input checks, and 392 recovery checks. All 12 selected source pins, 16 artifact pins, host-completion pins, and the 48-row CSV match. The selected host completion exits 0 with no resource stop.

Four attempt receipts remain retained. The first attempt's component checks passed, but host publication exited 1 because its read-only source mount also covered `syntax/results.json`. Its receipt/artifacts are retained and audited; it is not the selected result. Two subsequent attempts are also retained. Only the selected final 48-profile result is used for the counts above.

The executed Python code packs full SR14 containers. The selected native helper parses SR14 and encodes/decodes the individual BR88 chunks for comparison; the selected receipt does not run a native full-container SR14 encoder. [`native_encoder.cpp`](../../experiments/python-gamebub-v114/syntax/native_encoder.cpp) and [`run_native.py`](../../scripts/cu66-v114/syntax/run_native.py) are a separate unrun follow-up and are not part of this selected proof.

## 49,152-byte projected parent cap

Fits count the six existing canonical fixtures. Each projection replaces the old BR88 packet bytes with the SR14 container and leaves all other packet bytes unchanged.

| SR14 version | Chunk blocks | Fixtures at or below 49,152 bytes |
| --- | ---: | ---: |
| V1 | 32 | 4/6 |
| V1 | 64 | 5/6 |
| V1 | 128 | 5/6 |
| V1 | 256 | 6/6 |
| V2 | 32 | 5/6 |
| V2 | 64 | 5/6 |
| V2 | 128 | 6/6 |
| V2 | 256 | 6/6 |

For `actual_031`, V1's largest SR14 container is 45,474 bytes at 32-block chunks, projecting to 62,510 parent bytes. V2's largest is 37,754 bytes at 32-block chunks, projecting to 54,790 bytes. At 256-block chunks, V1 projects to 49,080 bytes and V2 to 48,080 bytes. These are byte-cost projections, not admitted or transmitted parent frames.

This study does not establish an FPGA parser or encoder, QSPI/ESP32/Sunshine integration, C2/HUD seal, pixel correctness, full-parent memory fit, decode time, or frame rate. Its hypothetical lane Rice-bit-work values are not cycle, clock, or hardware-throughput measurements.
