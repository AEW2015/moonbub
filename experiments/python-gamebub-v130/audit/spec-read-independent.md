# Independent V130 speculative admission review

The selected focused [receipt](../spec-read/attempts/20261111T023724210252Z/receipt.json)
has SHA-256 `9ce96bcf9488ea7e17a0e9434490c6af69c200e20972a816fcbeba8561708655`.
All 12 source hashes were checked against both live files and source
snapshots, and every receipt-listed artifact was rehashed. The two seed logs
record 621,950 edges each, 4,001 accepted replay responses, six stage
cancellation cases, six replay cancellation cases, all 65,536 low-16-bit
replay addresses plus upper values, and a successful final same-epoch retry.
The final retry occurs specifically after the last pending-response **abort**;
it does not demonstrate same-epoch retry for all reset/start/abort combinations.

The selected candidate is byte-identical to the V128-selected admission source
after exactly the declared read-enable and address-block replacement. The
renamed original and candidate module splits reconstruct the full sources and
use byte-identical helper modules. The candidate physically reads in FETCH_REQ
and FINISHED, with a simulation-only RAM-bound assertion and no changes to
logical response valid, acceptance, tags or writes. The generated paired wrapper
compares all declared non-data outputs and qualifies replay/stage data on their
respective valid signals. Invalid data buses may legitimately differ and
consumers must not use them unqualified.

Actual recorded commands use Verilator with `--assert -Wall` and host
`-Werror`, no `-Wno-fatal`, and two successful simulations. The
[first attempt](../spec-read/attempts/20261111T023320199962Z/receipt.json)
failed before simulation because of fatal C++ misleading-indentation warnings;
the passing attempts retained that history.

The separate [negative-control receipt](../spec-read/negative/attempts/20261111T023831069806Z/receipt.json)
actually compiled and ran both mutants. Removing the clamp was caught by the
RAM bounds assertion, while removing the abort mask caused a public-output
mismatch. Those controls exercise only those faults. All negative-control
source, mutant, log and artifact hashes were rechecked.

This finite, two-state paired admission test uses a shared helper implementation
and one valid packet fixture. It is not formal equivalence, a full-parent
integration or proof of cancellation with external physical write/ACK debt.
No new implementation, routing, board timing, throughput or decoding-latency
result follows from it.
