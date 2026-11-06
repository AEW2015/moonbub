# V91i1: bounded CS88 structural admission

This checkpoint adds the first outer-frame gate ahead of the frozen
[V91h coefficient endpoint](../cu66-v91h/README.md). It processes actual CS88
packets at the unchanged 720×480 geometry and 49,152-byte application cap.
It does not change encoding, quantization, wire bytes or image quality.

The supported subset is block size 32, chunk cap 65,536, key mode method 0,
delta grouped mode method 3, and QM87 methods 2/6. Other native-supported
profiles require explicit extensions and reject here. Known AB38 and BR88
chunk prefixes produce typed span descriptors; no entropy consumer is attached
to this admission component. Recognizing a prefix does not validate its payload.

The hardware-facing admission receipt is issued only after packet framing,
outer CRC, header/profile, reference eligibility, mode map, QM87 and directory
checks pass. A trusted external accepted-reference snapshot is latched at start;
this module cannot advance it. See the [exact contract](admission-contract.md)
for rejection order, supported syntax, ownership and cancellation semantics.

## Evidence and reproduction

**Result: PASS for the restricted structural-admission checkpoint.** The
[independent audit](../../experiments/python-gamebub-v91i/audit.json) and
[summary](../../experiments/python-gamebub-v91i/summary.json) retain the exact
source/vector/attempt hashes.

| Final seed | Vector rows | Structural receipts | Rejections | Interface/recovery checks | Plane-slot comparisons |
|---|---:|---:|---:|---:|---:|
| 911101 | 86 | 52 | 34 | 14 | 156 |
| 911102 | 86 | 52 | 34 | 14 | 156 |

The 52 admitted rows are 51 native packet variants and one synthetic all-COPY
case with no residual chunks. The native rows contain 25 distinct packet byte
strings, cover eight cohort/frame identities, and range from 13,440 to 47,960
bytes. They retain their original bytes. Negative vectors cover malformed
headers/directories, overflow, reference/cache eligibility, unsupported syntax,
CRC, QM runs/required cells and combined-fault rejection priority. The 14
directed checks include early/missing `in_last`, abort/reset/replacement at RAM
and held-receipt boundaries, external snapshot latching and backpressure.

The first strict lint attempt failed on unused width and unsupported array
reset syntax; both were fixed without warning waivers. Its source and log are
retained alongside the passing relint. An earlier passing simulation is also
retained but superseded after correcting a mutation-provenance flag; the two
final runs match the current source and vector hashes.

The [Python model](../../experiments/python-gamebub-v91i/admission-model.py)
builds deterministic vectors from retained native CS88 packets and labeled
synthetic boundary/malformed cases. Variants and repeated histories do not add
independent gameplay content coverage. The independent
[auditor](../../experiments/python-gamebub-v91i/verify_results.py) checks byte
parsing, descriptors, dispositions and retained seeded RTL receipts.

```sh
python3 experiments/python-gamebub-v91i/admission-model.py
python3 scripts/cu66-v91i/run_admission.py --seed 911101
python3 scripts/cu66-v91i/run_admission.py --seed 911102
python3 experiments/python-gamebub-v91i/verify_results.py
python3 scripts/cu66-v91i/summarize.py
```

The runner uses the existing `gamebub-cu66-v69-build` container, Verilator 5.020
and GCC 13.3.0, strict `--assert -Wall` and C++ `-Wall -Wextra -Werror`, with
two compiler jobs. Attempts retain commands, tool versions, source/vector
snapshots, exit codes and output hashes, including failed attempts. This is
Verilator simulation, not a Vivado implementation or hardware test.

## Next integration gates

V91i2 must connect admitted spans to entropy consumers and bind coefficients to
mode positions and quantizer cells. BR88 can use V91h; AB38 needs its own
consumer or an explicitly negotiated sender fallback. Modes/scales and packet
ownership must remain provisional while consumers run, with stale epochs
cancelled and accepted external memory requests drained safely.

V91i3 must integrate transaction ownership with reconstruction and final
validation. Inner chunk grammar/CRC, coefficient decoding, dequantization/IDCT,
accepted-reference pixels, HUD, content roots/seals and atomic validated
publication remain later consumers. Neither a structural receipt nor a chunk
scratch seal is a complete frame acceptance event.

This checkpoint does not prove a bitrate reduction, improved quality, routed
clock, memory fit, ESP32 throughput, sustained hardware 30 fps or complete
validated FPGA decoding under 10 ms. Those two product milestones remain open
in the [active roadmap](../gamebub-v91-v110-development-plan.md).
