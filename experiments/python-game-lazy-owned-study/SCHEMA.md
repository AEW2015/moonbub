# Owned capture/lazy analysis component contract

`CaptureLease` is an exact owned object with pool owner, epoch, slot0/1,
generation, token and immutable RGB ndarray. Caller-created equivalent objects
are not valid descriptors. Active descriptors are bounded by8; snapshot slots
by2; every array obeys the frozen bounded even RGB contract. Local token and
generation counters are uint32, failing on exhaustion; local epoch is positive,
strictly increasing and below0xffffffff. Reset requires drained readers.

`OwnedJointSender.build` returns the frozen joint `Candidate`, whose JSON
`info.capture` adds local ownership identity, `copied_bytes`, `snapshot_copy_ms`,
`peak_pool_pixel_bytes`, `peak_pool_slots`, `released`, `active_readers_after`
and `retained_pool_pixel_bytes_after`. An already-expired request records a zero
copy and does not open a capture or analysis context. A failed callback raises
after cleanup rather than returning a fabricated candidate.

`info.paid_service_ms` is the complete outer call including snapshot/release;
`joint_inner_service_ms` preserves the nested controller clock. The externally
measured outer call is authoritative for performance comparison. Deadline origin
includes pre-controller elapsed snapshot work.

`last_source_info`/`last_shared_info` retain JSON diagnostics after context end:
actual analysis/forward calls, cached map attempts, eliminated repeated analyses,
open/forward work, ownership-check counts, zero source-SHA counts/bytes, snapshot
array bytes, named prediction/transform bytes, reference read counts and bank
reader-descriptor costs. Prediction and raw coefficients remain zero until first
build, then at native geometry total5,184,000 bytes. The snapshot is counted once
by the pool even when several fields identify its same size.

Prepared-codec syntax stays AR03 within actual HC22/HD22 CP23/JA23 from v23. No new
wire negotiation, reset handshake, transport scheduling or hardware fencing is
introduced. Parent campaign results/source pins and its replay verifier document
measured native-source outcomes separately.
