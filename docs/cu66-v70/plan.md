# V70 — integrated CU66 receiver and hardware-test readiness

Status: v70 prototype implemented and qualified at the scopes in [hardware-handoff.md](hardware-handoff.md). Functional reconstruction passes; clean native scanout cadence fails, and target implementation/physical gates remain open.
Baseline: v69 commit `1e10566ec6df50577919c8782941b404e37e00e0`.
Reviewed source hashes are in [baseline.json](baseline.json).

## Main goal

Move from qualified decoder components to a receiver that accepts complete
CU66 packets, reconstructs against its own stored references, and publishes
matching video/HUD descriptors safely through the actual memory/display path.
Keep 720×480 coded resolution, the existing CU66 profile and the 30 fps goal.
Do not make a new compression format a prerequisite for this iteration.

The native decoder remains the independent scoreboard. It must no longer
supply the packet metadata, quantizer map or golden reference pixels that
substitute for receiver hardware in the v69 base-layer integration bench.
The qualified software HUD endpoint is an explicit processor partition;
feeding its real decoded output is different from injecting golden HUD words.

V69's worst valid base-layer run was 2,708,663 modeled cycles. At a hypothetical
100 MHz that alone would be 27.087 ms, leaving about 6.247 ms of a 33.333 ms
frame period. This is a planning constraint, not a measured FPGA latency or
clock result: packet scanning, HUD processing/transfer, actual memory service
and display work still need accounting and overlap analysis.

## Gaps found in the source review

| Current boundary | V70 change |
|---|---|
| Packet RTL and base decoder tested separately | Wire the real parser, qmap and AB38 address descriptors into one frame owner |
| Reference pixels provided by native golden arrays | Read the previous accepted RTL-written bank through the memory adapter |
| Synthetic x16 service slots and display reservations | Exercise controller commands, actual refresh and concurrent LCD line requests |
| Single-clock bank controller tested separately | Join packet/base/HUD/write fences and implement safe cross-clock presentation |
| HUD gate is Linux C++, with a typed API only | Define an encoded command/response contract and test its RTL-facing completion path |
| Portrait layout is Python-only | Implement deterministic RGB565/HUD conversion and portrait writes, then use real LCD scanout |
| No target resource/timing result | Stage reproducible leaf/OOC/full integration builds and run exact-device checks when available |

Two specific memory-model corrections matter:

- `moonshine_sdram.sv` defaults to `REFRESH_CYCLES=750`; v69's shared-slot
  experiment reserves 16 of 7,800 cycles. Those are different schedules. V70
  must use the actual selected controller's configuration and commands, not
  treat the synthetic reservation as controller qualification.
- `fpga/sim/sdram_model.sv` declares 1,048,576 x16 words, or 2 MiB. That is a
  test-model allocation, not the fitted SDRAM capacity. Extend its checked
  address coverage for the chosen map, or use a checked sparse model. Detect
  aliases and out-of-range accesses rather than truncating addresses.

The existing burst-write experiments are useful starting evidence. They are
explicitly experimental; the basic arbiter lacks partial/abort support. Audit
their completion, masking, drain and timing assumptions before reuse. Leave
the unrelated untracked `marker-recovery/` work untouched.

## Ordered work packages and exit gates

### 1. One transaction owner: packet to accepted reference

Implement a top-level frame transaction wrapper around v69 packet control,
base decode, HUD completion and three-bank ownership. It owns the active
generation, compressed allocation, reference descriptor and candidate banks.

- Acquire one immutable packet allocation and snapshot the accepted reference.
- Route parser and entropy requests through an arbiter with registered response
  ownership, correct descriptor offsets and no packet-bank reuse before drain.
- Serve qmap from the parser's synchronous local port, not a bench array.
- Store accepted canonical tags alongside reference-bank descriptors.
- Join base success, exact HUD semantic/transfer success and write completions
  for the same generation/frame before a commit decision.
- Preserve reference and front buffers after CRC, entropy, hidden-block, tag,
  HUD or write failures. Reject delayed completions from older generations.
- Retain one authoritative commit decision. Retry the software HUD COMMIT
  idempotently after a lost ACK; block the next dependent preparation until
  processor and FPGA accepted state agree. Do not roll back an already
  published reference because an acknowledgment was lost.

Exit gate: original complete packets from all 457 retained frames pass the
integrated parser/base path. Predicted frames fetch actual previous RTL output.
Golden arrays exist only in the scoreboard. Inject every v69 failure class
and lost/delayed/duplicate HUD commit acknowledgments without partial commits.

### 2. Real memory adapters and complete ownership

Generate one checked memory-map description shared by RTL configuration,
native tests and future firmware. Include compressed staging, three canonical
reference/candidate banks, HUD banks, RGB565 buffers and guards/alignment.
Use the controller's current single mapped 32 MiB chip initially; do not
assume the second schematic chip is implemented.

Implement packed-u8 canonical tile readers/writers over x16 transactions.
Specify byte order, plane bases, tile/row traversal, partial-word masks and
burst alignment. Every accepted read/write carries enough ownership to route
completion and survive abort. A write queue's ready is not write completion.

- First qualify against the conservative existing controller.
- Then compare an abort-safe BL8 write adapter using identical packets and
  output hashes. Keep it only with actual command-count/cycle benefits.
- Count row hits/misses, ACT/PRE/RD/WR/REF commands, turnaround, queue stalls,
  refresh deferral and worst service latency per client.
- Exercise row/bank boundaries, adjacent allocation guards, packed odd-byte
  cases, partial bursts, backpressure and abort at every accepted beat boundary.
- A watchdog stops new work and requests recovery. It must not release a live
  allocation while a memory operation remains outstanding. Require drain or
  an explicit controller-reset/flush acknowledgment.

Exit gate: readback matches complete canonical/HUD/RGB565 data; no guard,
ownership or command-timing assertion fails with scanout and refresh active.
The modeled capacity and controller geometry are documented separately from
vendor timing/electrical signoff.

### 3. Display a complete frame using existing scanout

For the first implementation, keep canonical YUV references separate from a
presentation-only RGB565 buffer. Convert once after candidate validation and
write portrait-oriented RGB565, then reuse the existing LCD line reader. This
spends additional memory traffic but isolates scanout from codec/HUD work;
measure that cost before considering direct YUV scanout.

- Preserve the qualified native chroma interpolation and integer rounding.
- Composite exact HUD RGB565 words after video conversion.
- Use coded `(u,v)` → physical `(x=v,y=u+40)`, with correct black borders.
- Start with identity filtering; optional strong filtering remains display-only
  and must retain its original operator order and rounding.
- Switch an immutable video/HUD presentation descriptor at vblank only after
  old scanout readers drain. Handle memory/pixel clocks through qualified CDC.
- On decoder/transport failure, hold the last good frame while reporting the
  error; use the existing safe line behavior for an actual scanout underrun.

Exit gate: compare complete 480×800 RGB565 rasters against the native/layout
oracle, including all borders and HUD. Verify no mixed-generation frame,
mid-line descriptor switch or unauthorized read/write occurs.

If the first RGB565 path misses its memory budget, record the failure and
evaluate bounded tile/transpose caches with measured traffic. Do not silently
lower resolution, omit HUD or remove failed frames from the test window.

### 4. Hardware diagnostics and reproducible builds

Add features that reduce bring-up time:

- Versioned capability/status registers: implemented profiles, ABI version,
  active generation, accepted reference ID/tag and current display descriptor.
- Separate arrival, parse, decode, write-drained, committed and presented
  timestamps; report frame age and presentation counts distinctly.
- Sticky first-fault record with frame/generation, stage, address/tile index
  and reason. Include FIFO high-water, wait and underrun counters.
- Bounded diagnostic event ring, readable over the control interface; keep
  debug traffic out of the video payload and charge its bus traffic in tests.
- Built-in self-test sequence: color bars, moving pattern, checked memory
  roundtrip, one actual CU66 key and a dependent P packet, then abort/recovery.
- Source-pinned replay bundle and one-command smoke/full/implementation gates.
  Missing tools/device files return unavailable, not PASS.

Run functional assertions and seeded regressions in the existing simulators.
Add small formal properties for bank mutual exclusion, no commit on failure,
stable stalled data and no generation reuse before drain, if the formal
backend is available. Formal analysis is not a liveness claim without explicit
memory-service assumptions. Run CDC/reset checks and target-specific timing
separately from functional simulation.

The exact Artix-7 part remains an external tool-install gate. No DAP/JTAG is
needed to implement or simulate the above; attached hardware is required for
the final board measurements. General mapping cannot establish target Fmax.

### 5. Cadence and release evidence

Keep the exact 457-frame qualification as the regression baseline, then add
fixed input arrival times, packet fragmentation, jitter, dropped/truncated
packets, queue pressure, refresh/scanout phase sweeps and controller stalls.
Account for reference dependencies: dropping a predicted frame is not safe
unless subsequent packets reference the still-accepted state or a key restores
synchronization. Expose a precise recovery reason and key request/status path.

Report input, accepted, rejected, decoded, committed and presented IDs, missed
deadlines, frame-age p50/p95/p99/max and recovery time. Do not count bank flips,
duplicate refreshes or identical repeated packets as new captured frames.

A long repeated-content stress replay is useful but must be labeled as such.
The existing plan's 1,800-distinct-source-frame campaign and ten-minute physical
30 fps test require additional chronological source material and hardware.
They cannot be satisfied by looping the retained 457 frames or assuming a
100 MHz clock. Preserve failed arrivals and strict observation windows.

Exit gate: source-pinned functional/command-level results and explicit memory/
resource/timing budgets, followed by physical testing when the remote board
and exact-device build are available. Target 30 fps remains unproven until
unique complete presentations meet the measured system cadence.

## Scope and optional additions

Required first: transaction owner, real reference storage, command-level memory
tests, explicit HUD/global commit and minimal rotated RGB565 scanout.
Diagnostics and deterministic self-test belong in the same iteration.

Conditional additions after the complete path is correct:

1. Abort-safe burst writes and small line/tile caches, selected by measured
   service time and resource cost rather than nominal bus bandwidth.
2. Bounded prefetch/pipeline overlap where traces show stalls; preserve exact
   outputs and reference leases. Measure tails as well as averages.
3. Decoder capability negotiation and explicit JPEG fallback/control-plane
   recovery, without changing the frozen CU66 payload or enabling unsupported
   profiles accidentally. Cross-board fallback remains a measured integration.
4. ESP32 HUD endpoint feasibility probe: compile the bounded native endpoint,
   instrument peak live allocations including temporaries and coexistence with
   Wi-Fi/UI/QSPI, and measure service time. Do not infer fit from desktop timing
   or the 94,720-byte two-cache capacity figure alone.

Defer broader motion, a new entropy format, full HEVC/AV1 syntax, extra decoder
lanes, new display filters and second-chip support until profiling identifies
the bottleneck in the complete path. This iteration aims to make the existing
codec implementable and diagnosable on hardware with preserved image quality.

## Parallel ownership for implementation

Use isolated new v70 source/evidence directories; freeze v69 artifacts and
preserve unrelated work. Suggested allocation when implementation starts:

| Owner | Work | Boundary |
|---|---|---|
| Root/integrator | Transaction owner, HUD commit protocol and final system tests | Owns global generation/descriptor rules and merges verified modules |
| RTL agent | Memory map/adapters/controller integration and checked memory model | Owns memory ports, completion semantics and burst/abort tests |
| RTL agent | RGB565/HUD/portrait output and existing LCD integration | Owns color rounding, scanout descriptors and CDC interfaces |
| Luna agent | Fixture/evidence audit, diagnostics/register documentation and replay packaging | Independent count/hash/scope checks; no blind repinning of failures |

Agree memory and descriptor interfaces before parallel edits. Each result must
include commands, seeds, source/fixture hashes and genuine simulator PASS
markers. Integrate in the order above; a leaf PASS does not close a system gate.

## V70 completion record

See [the handoff and measurements](hardware-handoff.md), [reproduction](reproduction.md) and [verification matrix](verification-matrix.md). Implemented work includes full-packet owner/qmap/base/reference feedback, actual controller/tile adapters/checked32MiB map, exact portrait/HUD and optional8-row strip painters, LCD descriptor ownership, native encoded HUD endpoint, first-fault/timestamps/event-ring controls and bounded bank checks. The complete command-model system passes full framebuffer/readback checks but exposes a failed display/30fps budget. Live transport/ESP32 qualification, autonomous board self-test firmware, odd-byte/masked-write support, fixed-arrival1800-distinct-frame campaign and exact-device implementation/physical tests remain open. The next performance work is streaming LCD/burst access and bounded reader caching or direct transposed-YUV scanout, not another compression format.
