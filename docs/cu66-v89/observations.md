# Actual BR88 work and qualified mixed-policy observations

The V89 observer decodes the actual BR88 components introduced in V88. It does
not subtract feedback counts from an old AB38 trace. An instrumented native
plain-Rice parser records each bit read, Rice symbol, event, fetched byte and
chunk setup, while reconstructing the coefficients. Its output is compared
with the independent frozen native BR88 decoder for every actual chunk.

All **457 sources, 1,371 chunks and 86,444,480 encoded coefficient values** pass
native equality. The observer scatters those residual coefficients back into
canonical Y/Cb/Cr order, inserts the existing zero coefficients for COPY/CONST,
and checks the complete canonical coefficient SHA against the qualified source.
The encoded chunks contain 1,350,695 residual tiles; the canonical output has
3,701,700 tile commands across all sources.

## Actual work, not elapsed clocks

| Context | Plain bit accesses | Rice symbols | AC events | Payload bytes fetched |
|---|---:|---:|---:|---:|
| DC | 5,658,086 | 1,350,695 | 0 | 707,875 |
| AC positions 1–5 | 16,014,980 | 5,662,074 | 2,831,037 | 2,002,462 |
| AC positions 6–20 | 13,993,733 | 4,048,764 | 2,024,382 | 1,749,784 |
| AC positions 21–63 | 1,990,020 | 373,848 | 186,924 | 249,015 |

The total is **37,656,819 plain bit accesses**, 11,435,381 Rice symbols and
5,042,343 events. Adaptive decisions, renormalizations, probability
initialization and arithmetic raw/preload bits are all zero on these plain
streams. There is still actual bit extraction and symbol work; zero feedback
is not zero-time decoding. The middle two AC contexts account for most of the
plain bits, so equal division of total work by a lane count is not justified.

The shared work records 4,805,106 CRC-scan bytes, 36,936 stream-header/padding
read bytes and 3,701,700 canonical tile handoffs. The CRC convention is the same
as V86: scan the whole chunk, including its trailer, and capture the initial
42-byte fixed chunk header during that scan. Those captured bytes are not
charged again. Separately charge the four six-byte stream headers and one byte
for each partial-byte padding validation. Plain payload fetch counts advance
once when its bit reader first touches a byte. A final partial byte can be
visited by both padding validation and the bit reader. This is an explicit
prospective capture/fetch convention, not a count of host CPU memory loads.

There are 12 work fields: the frozen 11 AB38 fields plus `plain_bits`. The
`raw_bits` field retains its old arithmetic preload/renormalization meaning;
BR88 bit reads use `plain_bits` instead, avoiding double charging. Raw fallback
uses `raw_bytes` and does not execute the Rice bit reader. The corpus selected
no raw BR88 chunks; synthetic raw cases test that path separately.

## Per-context order and AC lookahead

A context's pending run/event state is preserved across tiles. Reading an event
whose position falls in a future tile is charged to the tile that actually
performs that lookahead. The event is later placed without rereading its bits.
The observer records the initial event on the first encoded tile and reads the
next event immediately after consuming the pending event, exactly as the native
interleaved traversal does. Every stream must reach exact bit consumption.

The retained arrays are per canonical tile and four ordered contexts. They are
batched operation observations, not an instruction-level waveform or a physical
cycle trace. A word-window/leading-zero implementation would require a separate
trace and calibration; the current bit-reader counts cannot establish its II.

## Mixing actual policies

The public [data loader](../../experiments/python-gamebub-v89/observations/data.py)
combines actual V89 BR88 planes with the frozen V86 AB38 whole-plane observations.
For each source it uses the exact selected mask from V88's qualified CS88
packet. The source always has three whole-plane chunks, so each mask bit selects
one entire plane's actual work. No primitive counter is scaled or projected.

Both branches retain the same canonical coefficient identity. The returned
`work_sha256` covers the actual mixed little-endian u32 work array. Each frame
also carries its real CS88 packet SHA, complete packet bytes and actual
header/map/quantizer/directory byte count. The model must use these new wire
lengths when pricing admission and CRC scans.

The [independent observation audit](../../experiments/python-gamebub-v89/observations/verification.json)
checks every BR88 record, full native coefficient identity, context totals and
all **2,285 source/policy combinations** against their qualified feedback,
renormalization, plain-bit and chunk-byte counts. It independently totals raw
arrays by plane and checks the public mixed-array interface on the 16 records
used by the four-source/four-policy causal comparison.

Use one pass for multiple policies:

```python
for frames in data.iter_policies(
    ('AB38_control', 'feedback_overhead5', 'feedback_overhead15', 'all_BR88'),
    only={(0, 0), (0, 1), (0, 3), (3, 50)},
):
    for frame in frames:
        consume(frame['shared_work'], frame['context_work'])
```

`iter_frames(policy=...)` is the single-policy wrapper. Optional filtering skips
array expansion while still reading and verifying the complete retained input.

## Verification and limits

The [18 native observer checks](../../experiments/python-gamebub-v89/observations/tests.json)
cover empty AC streams, raw fallback, DC resets, future-event lookahead,
multiple-event lookahead, long high-band runs, eight seeded sparse patterns and
the explicit 15-unary-bit plus 14-literal-bit DC escape. They compare native
coefficients, all bit/symbol/event totals, exact byte fetches and chunk setup
attribution. An initial test compile failed on misleading indentation; its
source and compiler receipt are retained, and the corrected selected run exits
zero. Production observer/collector/data files were unchanged during all runs.

```sh
python3 scripts/cu66-v89/collect_observations.py
python3 experiments/python-gamebub-v89/observations/verify.py
python3 experiments/python-gamebub-v89/observations/test_trace.py
```

The collector refuses to replace an existing index. It uses the existing
`gamebub-cu66-v69-build` compiler/container. The retained model still assumes
fully buffered input; ingress, physical RAM ports, outer/HUD semantics,
reconstruction arithmetic, display and ESP32 execution are not proved by this
observer. Counts and synthetic checks do not close sustained hardware 30 fps
or complete validated decoding below 10 ms.
