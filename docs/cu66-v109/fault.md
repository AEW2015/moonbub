# V109 same-edge owned fault predicates

This candidate removes repeated wide error-status reductions from operational control without adding a public cycle. It starts from the actual qualified V108 composite source map in `experiments/python-gamebub-v108/outtile-native/20261108T101802940240Z/receipt.json`, rather than historical alias filenames. V108's reported 100 MHz route has WNS −2.020 ns; its worst transform-error to Rice-reservoir enable path has fourteen LUT levels and 81.315% routing delay. This candidate requires new native timing measurement.

The selected bodies are:

| Native alias | Actual V108 origin | V109 candidate |
| --- | --- | --- |
| `cu66-v91j/cu66_inverse_stream_v91j.sv` | `cu66-v107-meta-flags/cu66_inverse_stream_v91j.sv` (`afc0ebb4…`) | `cu66-v109-fault/cu66_inverse_stream_v91j.sv` |
| `cu66-v91k/cu66_reconstruct_stream_v91k.sv` | `cu66-v104-control/cu66_reconstruct_stream_v91k.sv` (`445e1b96…`) | `cu66-v109-fault/cu66_reconstruct_stream_v91k.sv` |
| `cu66-v91k/cs88_coefficients_v91k.sv` | `cu66-v106-producer-cache/cs88_coefficients_v91k.sv` (`396b0d9a…`) | `cu66-v109-fault/cs88_coefficients_v91k.sv` |
| `cu66-v91k/cs88_pipeline_v91k.sv` | `cu66-v107-meta-flags/cs88_pipeline_v91k.sv` (`582e6cf1…`) | `cu66-v109-fault/cs88_pipeline_v91k.sv` |

All paths above have prefix `fpga/experiments/`. The [reversible edit recipe](../../fpga/experiments/cu66-v109-fault/edit-recipe.json) contains complete hashes, exact replacements, and the full 18-file native source map. Fourteen entries remain byte-identical to the V108 composite, including all four V108 capacity bodies and the V108 output-tile body behind the historical `cu66-v69/inverse/cu66_idct8x8.sv` alias.

Each error producer adds a one-bit `fault_o`. Every original `error <= next_value` assignment has an adjacent `fault_o <= (next_value != 0)` in its original procedural block or failure task. There are twelve producer assignments and two assignments each in inverse and reconstruction. The implicit hold behavior and original last-assignment priority remain exact. A registered error is never sampled to derive a fault one cycle later.

The full top connects those three bits through its existing private child interfaces. Its public port list is unchanged. Cancellation, one-shot base abort with the original acknowledgement registers, status priority, done, and coefficient-stage cancellation use the exact fault bits. The inverse and reconstruction kill, private producer abort, input-storage fence, and running guards also use their local bit. Original reported status codes and their priority remain unchanged. No timing exception, clock change, added flush stage, altered drain ownership, or acknowledgement timing is introduced.

Every modified producer asserts `fault_o == (error != 0)` on every edge, including reset, abort, sticky failure, and replacement start; the top asserts all three connections. These new assertions supplement all original assertions.

Preparation is reversible and does not run RTL:

```sh
python3 scripts/cu66-v109/fault/prepare.py
python3 scripts/cu66-v109/fault/model.py
python3 scripts/cu66-v109/fault/qualify.py
```

The structural model checks all error assignments, source substitutions and reverse edits; it exhausts all 128 relevant top control combinations and all 16,777,216 combinations of the three eight-bit status codes. Its result is explicitly distinct from RTL qualification.

The focused run command is:

```sh
python3 scripts/cu66-v109/fault/qualify.py --run
```

This compiles complete original/new inverse bodies with the actual selected V108 dequantizer, IDCT and quantization header. It retains the existing independent input/store/metadata/fault-priority oracles, complete public and intermediate-state comparisons, both bank stores, historical boundary goldens, resets/cancels/retries, and 51 concurrent arithmetic/input-failure cases. Seeds are 109101 and 109102. Prepared internal response cases are declared verification-only additions and do not claim full packet reachability. The inherited prepared response accessor is adapted to V108's generated IDCT child class; its stimulus and all original checks remain the same.

The complete original/new reconstruction pair retains the existing independent coordinate/pixel oracle, every public output including invalid values and counters, two full canonical frames, and 51 reset/cancel/start/malformed checks. Producer/top structural induction is supplemented by the root's required full canonical pipeline qualification. Focused PASS alone does not qualify complete pipeline behavior or physical timing.

Each focused Docker invocation has a 4 GiB memory and memory+swap limit, two CPUs, one compile job, network disabled and a finite timeout. Attempts retain logs, source snapshots, hashes, compressed traces and failure receipts. The first attempt (`20261108T105815152642Z`) failed at C++ compilation because the inherited prepared-response bench assumed flattened pre-V108 IDCT member names; this is retained as a verification binding failure, not an RTL mismatch. The production source hashes were unchanged by the accessor repair.

Focused result: **PASS**, actual RTL executed, retained at [the selected focused receipt](../../experiments/python-gamebub-v109/fault/results.json), attempt `20261108T105940262100Z`. Both inverse seeds passed 9,467 prepared edges, 51 concurrent-failure cases, two late same-edge write/fail cases, and the unchanged 48-case/15-directed historical suite. Reconstruction passed 2,445,067 clock edges and 7,335,201 half-cycle public comparisons across two frames and 51 directed checks. The first compile failure remains retained separately. Generated child/parent binding headers and their hashes are in the passing receipt. No timing or full-pipeline qualification is inferred from this focused result.
