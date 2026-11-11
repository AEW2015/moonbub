# V130 admission speculative read experiment

**Unselected candidate; not a timing or full-parent result.** The V129 routed
worst path passes from cancellation control into admission RAM's read enable.
The isolated [candidate](../../fpga/experiments/cu66-v130-spec-read/cs88_admission_v91i2a.sv)
changes only the physical read enable and replay address: it reads in FETCH_REQ
and FINISHED, clamping replay addresses outside the 49,152-byte RAM to zero.
The logical read request, acceptance, tag, response-valid, counters, and write
enable remain unchanged. An unaccepted speculative read does not create a
logical response. The candidate may change the data bus on invalid cycles;
this is not exact all-public-signal equivalence, and downstream ownership must
still be verified before it can be promoted. Its RAM activity and power cost
are not measured.

[Source composition and packaging](../../experiments/python-gamebub-v130/spec-read/composition.json)
identifies the exact single admission alias substitution on the 18-origin V129
composition. It provides three byte-exact compile fragments whose concatenation
reconstructs the production source. The selector is PREPARED_NOT_INTEGRATED;
no functional or physical signoff is implied.

The paired [actual-RTL focused receipt](../../experiments/python-gamebub-v130/spec-read/attempts/20261111T023724210252Z/receipt.json)
records strict Verilator builds and two 621,950-edge simulations. Each compared
all non-data public outputs at every evaluation, and stage/replay data only when
response-valid. Each admitted 13 copies of one valid 25,495-byte fixture,
verified 4,001 accepted replay responses against packet data/address/epoch, and
covered six reset/start/abort cases at FETCH_REQ/FETCH_WAIT and six at replay
offer/pending-response. All 65,536 low-16-bit speculative replay addresses and
several high-bit values were exercised under an in-RTL bounds assertion. This is
finite two-state simulation of the admission pair, not a formal invariant.
The final clean retry reuses the aborted epoch without an intervening global
reset. Two separately compiled [negative controls](../../experiments/python-gamebub-v130/spec-read/negative/results.json)
removed the address clamp and the abort mask respectively; each was detected
by the bound assertion or public-output comparator. Wider malformed fixtures,
invalid-bus consumer safety and external physical write/ACK debt remain open.
A full-parent regression and new 125 MHz route are required.

The [first attempt](../../experiments/python-gamebub-v130/spec-read/attempts/20261111T023320199962Z/receipt.json)
failed at host compilation because two C++ statements triggered fatal
misleading-indentation warnings. The [second attempt](../../experiments/python-gamebub-v130/spec-read/attempts/20261111T023341481877Z/receipt.json)
passed after braces-only repair; the expanded run above used the same strict
warning and assertion policy. The binary hash is recorded, but the binary itself
is in a local build directory rather than the retained receipt tree.
