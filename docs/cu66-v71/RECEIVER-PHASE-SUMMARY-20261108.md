# Receiver phase summary: V48 baseline record

The published offline analyzer processes one hash-bound, prevalidated structured `NETWORK-RESULT.json` at a time. For V48 physical run `13880965209089969554` (manifest SHA-256 `8ec27984dc2865a33134c48800f3da79ed51d382dda0acf84314ec2e77458220`), the retained tail ordinals 9, 10, and 11 report `native_wall_us` values of 212,382, 196,723, and 124,060 microseconds.

These are wall intervals around the native FFI call, not CPU-exclusive time. They are a V48 record only; there are no physical V54 or V55 `NETWORK-RESULT.json` timing exports available here, so no cross-version speed claim is made. The analyzer does not infer QSPI timing or recompute the USB export CRC; it requires and preserves the existing validated-export receipt and exact input SHA-256.

The summary is [v48-phase-summary.json](../../host/receiver-phase-summary-v1/v48-phase-summary.json). Implementation, tests, fixture, and hash bindings are in [receiver-phase-summary-v1](../../host/receiver-phase-summary-v1/README.md).

