# V116 admission selected-plane preparation

Status: prepared, not yet RTL qualified. No compile or simulation was launched
by the admission worker before the Root heavy-slot grant. The source is an
isolated reversible candidate based on frozen V112 admission SHA256
`49f23fe56894012d1f647192bb030025eb79331fe24b173c11a2252bee4ff8b7`.

The authoritative V115 final routed 100 MHz report has −0.263 ns worst setup
from admission plane[0] to state[1]. Read-only extraction of the routed DCP's
compressed EDF records the actual named LUT/carry inputs in
`experiments/python-gamebub-v116/admission/mapped-path.json`. The first carry
S-input cone reaches every bit of each plane's block count, plane selection,
and word_value[2:0]; it has no cursor or residual-end sequential leaves. This
supports selected-count/zero preparation. Carry names alone do not establish
that a multiplier is on the critical path. No new timing result is claimed.

At existing PLANE_BEGIN, the candidate captures selected plane, receipt epoch,
32-bit count, and zero flag. At the subsequent existing FETCH_REQ it forms the
original 32-bit wrapped `46+128*selected_blocks`. CHUNK_NUMBER uses the zero
flag, CHUNK_BLOCKS the selected count, and CHUNK_LENGTH the prepared limit.
The independent 64-bit residual-end sum/bound and all original state/error
priority, read requests, response timing, public ports, raw held values,
counters, RAM interfaces, and original assertions remain unchanged. Reset,
start, abort, and PLANE_NEXT invalidate the preparation. Consume assertions
check validity, owner, plane, count, zero, literal original expression and
literal original predicates; fetch/word assertions check tuple stability.

`edit-recipe.json` reverses exactly to the frozen production source.
`packaging.json` retains the V112 keys and fragment filenames with this
candidate's byte offsets/hashes. Embedded scale and mode helpers remain exact
and are shared once only in the compile staging area. Adapters preserve each
complete main body. The exact frozen C++ file is saved as
`tb_admission.frozen.cpp`; the separately compiled legacy recipe translates
four physical hierarchy names and binds the newly required private tuple in
already existing forced-state fixtures. It removes no assertion, expected
value, corruption predicate, or packet golden.

The new focused C++ extension compares the inherited probe's complete public
output tuple before and after every edge, including invalid cycles. It adds
25,344 full32 count/word/cursor/residual-bound cases, uint64 counter wrap,
294 all-plane reset/start/abort preparation/fetch/word cases with retries,
and empty-plane successor transitions. Arbitrary consume fixtures bind the
completed-word poststate and never clock out-of-range reads. Accessed RAM
bytes are initialized through the original external RX write port. The
inherited full packet, malformed packet, header/quant/scale/mode, stalled
receipt, read-binding, cancellation and retry tests and independent replays
remain active for both seeds 116201 and 116202.

Preparation-only check:

```
python3 scripts/cu66-v116/admission/qualify.py
```

Root launch after granting one of the global maximum two heavy slots:

```
python3 scripts/cu66-v116/admission/qualify.py --run --root-grant ROOT_GRANTED_SLOT_2
```

The runner uses pinned Verilator 5.020 image
`sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`,
`--assert -Wall`, C++17 `-O2 -Wall -Wextra -Werror`, and build `-j 1`.
There is no warning suppression. C++ -O2 changes host speed only; it skips no
modeled cycles and makes no FPGA frequency claim. Each command runs in a new
2 CPU, 8 GiB container with memory+swap fixed to 8 GiB, network disabled and
finite inner/host watchdogs. Launch requires available RAM ≥8 GiB, memory
PSI full avg10 <1 and combined host memory+swap utilization <0.85. Stop
thresholds are available RAM <4 GiB, combined utilization ≥0.9, or PSI full
avg10 ≥5 on two samples. Root alone controls the global heavy-slot count.

Every attempt preserves exact commands, source/compile snapshots, logs,
resource samples, binary hash, traces, replay outcomes and failure status.
`actual_RTL_run` is persisted true before launching the first simulation,
including failing attempts. The selector uses selected_report and
selected_report_sha256; the raw report includes status, actual_RTL_run,
source_sha256, artifact_sha256, and commands. Behavioral simulation is not
formal equivalence, routed timing closure, CDC or hardware qualification.
