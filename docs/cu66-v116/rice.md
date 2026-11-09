# V116 Rice successful payload and zero view

Prepared for Root dispatch; **no RTL compile or simulation has run** in this preparation. The selected backend remains the existing Verilator 5.020 image `sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`. Simulation evidence, synthesis structure, and routed timing remain unverified.

The authoritative [V115 routed diagnosis](../cu66-v115/final-routed-next.md) reports actual 125 MHz setup −2.974 ns from `base_kill_authorized_reg` to Rice `out_value_reg[12]/R`, with 11 LUT levels and high fanout. This candidate removes the 24-bit bank's source-level clear assignments; it does not claim measured timing improvement.

The original source is `fpga/experiments/cu66-v115-ingress/br88_rice_elastic.sv`, SHA256 `37c8f5bb79621117c0e9e05096b6edead446540b026b7240819bac39838660a3`. It has exactly three zero-assignment sites (`respond_error`, reset/start, parallel-prefix truncation) and one successful-data site. V116 changes these sites in place: each zero site sets `output_zero`; the successful site clears it and writes `successful_payload`. Public `out_value` selects zero or the payload combinationally. The private 24-bit payload has no reset/start/error assignment. All other assignments, acceptance priorities, and public cycle schedules are unchanged.

The non-obvious priorities are preserved: request acceptance precedes accepted input, accepted input precedes prefix/suffix progress, a malformed input in IDLE records failure without immediately changing public output, response consumption holds public data, and a legal new request holds previous public data until its response. Successful decoded zero clears the zero view exactly like any other successful value. Reset wins when reset and stream_start coincide.

`python3 scripts/cu66-v116/rice/emit.py --write` reproduces the candidate and faithful adapters. Without `--write`, it verifies source pins, forward and reverse substitutions, and original assertion-block retention. `edit-recipe.json` is reversible against the exact selected original. Original V115 and older files remain untouched.

The focused proof retains every original Rice SVA block, the exact original `verify` checker body, every equality term in the paired wrapper, and the byte-identical historical real-interface suite. The reference is the selected V115 parser, not an older optimization. Prepared-state fixtures initialize both parsers' original cached tuple and the new private view/checker tuple; this fixture extension does not claim protocol reachability. The additional independent checker reconstructs all old write priorities, predicts public old-value behavior, checks zero-view classification and payload-only-success writes, and rejects exposing a payload without success in the current owner.

The additive real-interface suite checks zero versus nonzero success, ordinary and escape zero, held responses, old data after consumption and new requests, consecutive errors, malformed padding, bad parameters, prefix/suffix/zero-length truncation, and reset/start/both in IDLE/PREFIX/SUFFIX/RESPONSE with request/input offers and both output-ready settings. It spans serial/parallel and 16/32-bit modes. The original suite retains its complete parameter sweep, maximum widths, prepared full32 boundaries, 1,520 corpus cases, 173,061 requests per configuration, eight configurations and 104 original directed checks.

The real-context ingress pair keeps the frozen final-ingress bench and all its existing public-output assertions. Its reference ingress is a faithful renamed copy of the same final-ingress production body, whose faithful renamed context instantiates old Rice. The candidate context instantiates V116 Rice. Additional assertions compare raw Rice output value, valid, and error even outside valid. Existing cancellation, malformed, owner/read-response, and clean retry gates remain strict.

Root dispatch commands are:

```bash
python3 scripts/cu66-v116/rice/qualify.py --run --suite parser
python3 scripts/cu66-v116/rice/qualify.py --run --suite ingress
```

`--suite all` runs them serially. Root alone grants heavy execution and maintains the global maximum of two heavy jobs. The runner uses Docker network none, 2 CPUs, 8 GiB memory and memory-swap, `-j 1`, Verilator `--assert -Wall`, and C++ `-std=c++17 -O2 -Wall -Wextra -Werror`. No warning downgrade or assertion suppression is configured. `-O2` is host execution optimization; it changes no simulated clock scheduling and implies no FPGA performance result.

Each command requires at least 8 GiB available, memory PSI full avg10 below 1 and combined used ratio below .85. It stops below 4 GiB available, at PSI full avg10 at least 5 for two samples, combined ratio at least .9, or a finite command watchdog. Compile caps are 900 seconds; simulations are capped at 600 seconds with finite testbench watchdogs. Attempts preserve source/recipe/fixture snapshots, expanded input bytes, commands, version, logs, memory samples, binary hashes, traces, and failure receipts. `actual_RTL_run` is persisted as true immediately before simulation launch, including failures. Source hashes are rechecked after completion.

Preparation checks performed: Python AST parsing, reversible emitter verification, faithful adapter pins, original assertion/checker-body retention, and runner preparation-only validation. These are source/recipe checks, not RTL functional proof. Native 2026.1 work, integrated parent validation, routed timing, and freeze/adoption decisions belong to Root.
