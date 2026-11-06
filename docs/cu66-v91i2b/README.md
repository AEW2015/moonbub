# V91i2b: final refill comparison before V91j

The bounded refill queue passes functional and ownership qualification. The
next implementation milestone is **V91j dequantization and IDCT integration**;
no further V91i subcheckpoint is required to start the supported BR88 path.

The new wrapper leaves admission, mode initialization, codec bytes, quantizers
and the V91h coefficient decoder unchanged. Compile-time `REFILL_OVERLAP=0`
retains the exact V91i2a request/wait/send control. Mode 1 uses two byte FIFO
entries and reserves capacity for each one-edge registered read response:
queued plus pending owners never exceed two. There is no response bypass.
See the [queue contract](queue-contract.md) and the
[RTL description](../../fpga/experiments/cu66-v91i2b/README.md).

## Measured results

Summed start-to-coefficient-completion cycles on the same four native golden
frames, with the same vector bytes and service rules:

| Seed | Service | Serial control | Queued refill | Reduction |
|---|---|---:|---:|---:|
| 911201 | FAST | 2,539,509 | 2,408,329 | 5.1656% |
| 911202 | FAST | 2,539,509 | 2,408,329 | 5.1656% |
| 911201 | SLOW | 3,119,367 | 2,986,950 | 4.2450% |
| 911202 | SLOW | 3,119,182 | 2,987,110 | 4.2342% |

FAST is deterministic: every native frame saves exactly
`2 × refill_bytes − 2 × nonempty_chunks` cycles. SLOW retains the same seeded
service rule, including address-based ACK delays, but scheduling changes alter
the later RNG draws and absolute ready-low trace. Its figures are measured
scenario results, not a replay of an identical cycle-by-cycle stall trace.

The enabled worst tested native count is 1,078,508 cycles from frame start and
1,006,531 cycles from the last accepted outer packet byte to coefficient
completion. QM6 preload remains a separately charged 1,350 cycles. These are
coefficient fences, not complete validated decoding, an achieved clock or a
hardware frame-rate result. Packet storage remains two 49,152-byte banks;
the FIFO does not eliminate that 98,304-byte staging budget.

Each seed compiles two separate static pipeline binaries and a standalone
queue test. Each pipeline binary passes 22 FAST/SLOW rows and 4,058,368 exact
coefficient/placement checks. Across both seeds/configurations that is
16,233,472 checks and 253,648 observed tile records. The same four related
native frames and synthetic variants are reused; this is not new content
coverage. Each disabled binary matches all 506 original case fields and
63,412 ordered original tile records exactly, including their timestamps.

The disabled pipeline passes its 10 existing directed groups; the enabled
pipeline adds abort/reset with both a queued byte and pending read, for 12.
The standalone helper passes 12 groups with legal read/child backpressure,
full-queue holds, simultaneous operations, cancellation, replacement and
malformed responses. Its separate ready input avoids forcing an internal
signal in the real decoder. Enabled qualification refills reconcile 187,140
requests/responses/pops per seed, with no final owners and at most two live
owners throughout. External accepted scratch requests still drain on real ACK.

The independent [audit](../../experiments/python-gamebub-v91i2b/audit.json)
and [summary](../../experiments/python-gamebub-v91i2b/summary.json) retain exact
sources, vector hashes, controls, logs, traces and results. One earlier attempt
passed functional checks but failed its final live-source hash guard because
the two integration cancellation tests were added while it ran. That attempt
remains recorded and is excluded from qualification; both final seeds use the
same frozen sources and vectors.

## Reproduction

Use the existing `gamebub-cu66-v69-build` container (Verilator 5.020, GCC
13.3.0). Runs use `--assert -Wall`, C++ `-Wall -Wextra -Werror` and two compiler
jobs. These are behavioral simulations; no device or new tool installation
is required.

```sh
python3 experiments/python-gamebub-v91i2b/queue_model.py
python3 scripts/cu66-v91i2b/run_pipeline.py --seed 911201
python3 scripts/cu66-v91i2b/run_pipeline.py --seed 911202
python3 scripts/cu66-v91i2b/check_v91j_reuse.py
python3 experiments/python-gamebub-v91i2b/verify_results.py
python3 scripts/cu66-v91i2b/summarize.py
```

## Direct next milestone: V91j

Existing [dequantizer](../../fpga/experiments/cu66-v69/inverse/cu66_dequant.sv)
and [Q14 IDCT](../../fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv) RTL are
available for reuse. The [readiness check](../../experiments/python-gamebub-v91i2b/v91j-reuse-readiness.json)
matches all 384 quantizer entries and 64 DCT constants to the current native
profile and records the common coefficient range −2048..2048. It also pins
the historical V69 regression evidence. This is source-data compatibility,
not a rerun or proof of the new integrated transform path.

V91j has three concrete pieces of work:

1. Assemble each 64-coefficient stream tile in bounded banks, retaining plane,
   tile, qscale and frame-epoch ownership while the inverse stages are busy.
2. Connect the existing inverse blocks and their opaque job IDs to the new
   metadata owner; preserve held output, cancellation and error propagation.
3. Compare exact signed dequantized values and unclipped residuals with an
   independent current-profile oracle. Cover zero/DC/AC, all scales and both
   plane types, signed rounding boundaries, limits, stalls and abort/retry.

AB38 fallback, reconstruction, accepted-reference/cache commit, COPY/CONST
pixels, HUD/content seals and validated publication remain explicit later
integration gates. They do not block starting V91j on the qualified BR88
subset. Sustained hardware 30 fps and complete validated FPGA decoding under
10 ms remain open; V100–V110 retain physical mapping/routing/timing work.
