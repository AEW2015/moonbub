# V117 hardware-development handoff scope

This branch contains source-bound RTL experiments and retained simulation/native
reports. All five measured implementations still miss setup timing; there is no
clock-qualified source composition for hardware release. It does not contain a board-qualified production streaming image.
Use the terminal results in [README.md](README.md) and the machine-readable
`experiments/python-gamebub-v117/results.json` when selecting a composition.
A prepared runner, successful compile or negative routed result is not a pass.

## Integration units

- AC captures a complete owned selected read tuple on an existing acquisition
  edge, preserving public timing and error/physical-response semantics.
- The inverse uses registered capture/validate/commit tuples and an accepted
  reservation frontier for II1. Logical commit remains two edges after accept;
  malformed/canceled tuples are not counted as committed work.
- Reconstruction uses exactly two canonical owners, one arithmetic engine and
  a real storage-copy edge. Filling and ordered emission can overlap without
  overwriting the offered head or its reference lease.
- The optional ingress repair registers stable packet and selected descriptor
  bounds before validation. It preserves full uint32 wrap behavior, descriptor
  error priority and public request cycles.
- The isolated parent observation guard masks two exported observations after
  parent revocation. Raw private one-edge work is still observed and checked;
  these masks do not stop that work. Actual accepted physical responses remain
  unmasked. See [the boundary contract](parent-guard.md).

Packet formats, quantization and canonical output bytes are unchanged. There
is no new Sunshine or ESP32 endpoint deployment in this iteration. The pinned
Artix-7 timing target is `xc7a100tcsg324-1`, primarily 125 MHz with an explicitly
separate 100 MHz control. OOC decoder-body timing cannot qualify the parent
row join, SHA, memory, CDC, transport, display or board I/O.

## Remaining board acceptance

Integrate the exact selected source composition with the real memory controller
and transport endpoint, then constrain and route that complete parent. Keep
accepted physical-response ownership through cancellation and retry. Measure
final accepted outer byte, canonical completion, successful final physical ACK,
root/HUD/seal completion, validated commit and presentation as separate hardware
fences. Do not replace validated commit with the last pixel or last input.

For under-10-ms acceptance, use board timestamps at the actually achieved
clock. A simulated count below 1,250,000 cycles is only a conditional 125 MHz
budget result; the 100 MHz threshold is strictly below 1,000,000 cycles.
Sustained 30 fps requires continuous distinct-frame delivery and presentation,
not repetition of a single synthetic keyframe/retry test. Report dropped or
repeated frames, queue occupancy, memory stalls, recovery, payload throughput,
ESP32 execution cost and end-to-end input latency separately.

All V116 and older inputs and the unrelated marker-recovery work remain outside
the V117 edit scope. Original failed attempts and their exact source snapshots
remain evidence. Reproduction commands and resource limits are in
[reproduce.md](reproduce.md).
