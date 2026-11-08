# Separate capacity RTL activation contract

The capacity variant is a separate source experiment. It does not alter the six
frozen checkpoint implementation trials. It replaces only the four
`cu66-v107-count-threshold` production bodies with their same-named
`cu66-v108-capacity` bodies; every other RTL body and the include header stay
identical.

The [capacity native preparer](../../scripts/cu66-v108/native_capacity.py) requires
both actual RTL qualifications before it can create a build:

- `capacity/results.json`: `PASS`, `actual_RTL_run=true`, and current hashes of
  the four production bodies.
- `capacity-pipeline/results.json`: `PASS_EXACT_CAPACITY_CANONICAL`,
  `actual_RTL_run=true`, and exactly the complete eighteen-file RTL/header closure
  that native synthesis will consume.

Preparation freezes a distinct `capacity-native-contract.json`, source snapshot,
preflight and recipes. It preserves the exact parent seventeen-RTL read order
and include-directory order. The native run starts from fresh RTL with the
10.000 ns clock read before RuntimeOptimized synthesis. Default optimization,
placement and routing are the initial bounded comparison; no post-route physical
optimization, exception, board I/O timing guess or clock relaxation is added.

Dispatch requires root's separate activation and independent audit. All six
checkpoint matrix outcomes must be terminal first, unless root explicitly records
`allow_before_matrix_complete=true` and a concrete `measured_exception_reason`.
The activation binds the prepared preflight and contract hashes and allocates one
heavy slot under the global two-job cap. This script permits one capacity native
receipt, preserving a failed attempt rather than retrying silently.

The runner writes to `experiments/python-gamebub-v108/capacity-native/`, with a
separate receipt schema. The original checkpoint is mounted read-only as ancestry
evidence; the RTL branch never opens it. Native outputs include fresh synthesis,
placement and routing reports, the checkpoints' external paths/hashes, the fixed
clock, timing methodology and DRC, setup/hold/pulse results, complete routing
counts, source/recipe invariance and memory telemetry. Limits remain 2 CPUs,
2 Vivado threads, 8 GiB RAM without additional swap, and 2,400 seconds.

This flow is prepared infrastructure until both qualifications, activation and
independent gate exist. Passing isolated capacity tests alone does not qualify
the full decoder or its timing. Component timing does not prove board integration,
sustained hardware 30 fps or complete validated decoding below 10 ms.
