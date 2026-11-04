# Shared source context statistics

`last_source_info` /`last_shared_info` are the final context's JSON-safe dictionary:

- `frame_id`, `actual_analyze_calls=1`, `actual_forward_calls=3` identify actual
  preparation work. Cumulative `Encoder.analysis_count` /`forward_calls` include
  preparation and any normal builds outside a context.
- `cached_attempts` counts completed source guards before candidate work.
  `eliminated_analysis_calls=max(0,cached_attempts-1)` is saved repeated analysis,
  not saved candidate/reconstruction/entropy work or a frame-rate measurement.
- `source_prepare_ms` and `forward_analysis_ms` are measured Python component
  wall times. The enclosing controller must also time the complete begin/build/
  discard/end group so no preparation/failed work is excluded.
- `source_guard_calls`, `source_guard_bytes`, `source_guard_ms` count the begin
  guard plus every attempt, including a hash-detected input mutation. Hashing
  uses a transient canonical byte copy, not a retained snapshot.
- `borrowed_source_array_bytes`, `retained_source_copy_bytes=0`,
  `retained_prediction_array_bytes`, `retained_transform_array_bytes` and their
  `retained_analysis_array_bytes` sum describe named ndarray storage only.
- `source_reference_read_bytes` and `source_reference_array_read_bytes` describe
  the one source prediction read. They are logical sample/array counts, not
  measured complete memory traffic. Cached build's corresponding reference-read
  counters are zero because that prediction is not recomputed.
- `additional_context_reader_descriptors` is one for a referenced source, zero
  for a key. `dedicated_context_lease` records whether it acquired that hold;
  `context_lease_released` records release of that hold on normal context end.

Per-build frozen candidate metrics retain every other original AR03 field and
add `shared_analysis_reused=True`, `shared_lookup_ms`, and zero actual per-attempt
`analyze_calls` /`forward_calls`. Candidate service time includes source guard
lookup and the complete map/entropy/reconstruction/packet work. The original
source frame, prepared arrays and local GM encoder are private runtime objects;
the statistics dictionary is not a wire format or an authority token.
