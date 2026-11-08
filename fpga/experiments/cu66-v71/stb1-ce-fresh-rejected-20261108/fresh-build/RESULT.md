# CE factoring fresh implementation ? setup timing FAIL

The approved one-line zero-latency Boolean factoring completed synthesis and full fresh placement/routing without source changes or native errors. It is **not selected** and has no BIT or hardware result. The passing V028/V001 baseline remains untouched.

| Gate | Fresh CE final |
|---|---:|
| WNS / TNS | ?0.382 / ?80.561 ns |
| Failing setup endpoints | 638 |
| WHS / pulse | +0.031 / +2.000 ns |
| Routes | 56,032 / 56,032, zero errors |
| DRC | 208 warnings, no errors |
| Internal unconstrained endpoints / no-clock / loops | 0 / 0 / 0 |

The final worst setup path is parser metadata_reference_tag_reg[25] ? metadata_plane_bytes_reg[0][9]/CE, with 15 levels (9 CARRY4, 5 LUT6, 1 LUT2), 9.917 ns data delay and 6.771 ns routing (68.276%). This differs from both the original baseline HUD metadata?ticket/CE path and the fresh placed held_coefficients path. The selected design has +0.005 ns setup margin; a structurally simpler cone does not establish better whole-design physical closure.

Implementation returned 0 after 2,581.375 s with completion marker, no native errors and all 79 frozen inputs unchanged. Exit 0 means flow completion, not timing closure. The 17 no-input-delay, two no-output-delay and one partial-input-delay entries are inherited, not silently treated as complete I/O constraints. CDC must retain its actual classifications and inherited two critical LCD endpoints.

A separate approved read-only exact-ticket-CE query is pending. Its result will establish whether the intended metadata feedback was removed; that fact is independent of this full-design setup failure. A further incremental option is prepared but remains explicitly blocked pending root review and time budget. No source, clock, constraint or pin changes are made by that option.

See RESULT-bindings.json for exact reports/checkpoint/source hashes. All measurements here are static implementation evidence, not hardware playback.

Final read-only cone query completed: intended HUD metadata feedback is absent, exact ticket CE setup+0.289ns/hold+0.787ns. Net E[0] remains324loads but driver is now parser LUT6. See C:/moon/dev/evidence/stb1-ce-final-cone-20261108-v001/REVIEW.md. This does not override full-design setup failure.
