# Exploratory header fetch-index factoring

This is a separate candidate for a future timing study. It is **not selected
for the V129 implementation run** and has not been routed or measured for
timing. The V129 post-placement worst path ran from `command_pending_reg`
through frame and refill control to an ingress `fetch_index` enable. Placement
is an estimate; this observation does not establish which of V129's jointly
changed sources caused the path or whether this candidate improves it.

In the [V128-selected ingress](../../fpga/experiments/cu66-v128-raw/br88_packet_ingress_sync_v91h.sv),
`start` initializes `fetch_index` to zero and is the only entry to `RECEIVE`.
The `F_HEADER` call to `begin_fetch` occurs at the valid final received byte,
where it redundantly writes that index to zero. The [candidate](../../fpga/experiments/cu66-v129-header-index/br88_packet_ingress_sync_v91h.sv)
omits that write only for `F_HEADER`; descriptor, replay and raw fetches retain
it. A simulation assertion checks `state == RECEIVE` implies a zero index when
not cancelled. The change adds no intended public cycle or state changes.
Synthesis may still choose to retain the control path; only a new matched
implementation run can establish its physical effect.

The [source-bound paired test](../../fpga/experiments/cu66-v129-header-index/tb_pair.cpp)
instantiates both actual ingress modules with the selected V129 parser and
context sources. The generated [wrapper](../../fpga/experiments/cu66-v129-header-index/header_index_pair.sv)
compares all 67 public outputs on each evaluation with Verilator assertions and
warnings enabled. The [passing receipt](../../experiments/python-gamebub-v129/header-index/attempts/20261111T010410691169Z/receipt.json),
SHA-256 `bf11ec9c006380b99de50d16c7526a739b98ed33a591cd6611aee57f043bf8c5`,
records 1,704 clocks and 6,793 comparisons; four valid coded packets and one
valid raw packet exercised all four fetch purposes: header, descriptor, replay
and raw. Four directed cases applied reset, abort, start, and all three together
while input was valid, followed by a coded-packet recovery. Source and generated
wrapper snapshots, tool command, binary and logs are retained in the attempt.

The [first attempt](../../experiments/python-gamebub-v129/header-index/attempts/20261111T010320704422Z/receipt.json)
failed at compile because the generated wrapper and renamed baseline filenames
did not match their module names. No RTL simulation ran in that attempt. The
second attempt corrected the filenames, made a new pre-run source freeze, and
kept warnings fatal; it did not suppress the warnings.

This finite direct-ingress comparison is not formal equivalence, does not
exercise every error or interleaving, and is not the complete V129 composition.
Before any promotion, add directed malformed-final-byte and stall/cancellation
coverage, run the retained focused and full spatial, peer and parent exact-cycle
checks against a pinned baseline, and independently audit source and artifact
closure. Then run fresh constrained implementation and inspect routed timing and
methodology. It does not establish hardware operation, sustained 30 fps, or
under-10-ms decode latency.
# Portable build artifacts

The two local `obj/` directories are generated compiler outputs and are ignored
by Git. Each attempt includes an `obj.tar.zst` archive instead; the
[archive verifier](../../scripts/cu66-v129/header-index/verify_archives.py)
streams both archives without extracting, rejects unsafe members, and checks
every archived object against the unchanged original receipt. Its recorded
[archive hashes](../../experiments/python-gamebub-v129/header-index/attempts/object-archives.json)
cover both the failed and passing attempts. Run the verifier from the repository
root with `python3 scripts/cu66-v129/header-index/verify_archives.py`; it requires
the `zstd` executable. To run a tool that expects the original object paths,
first verify the trusted archives and extract each `obj.tar.zst` into its own
attempt directory with `tar --zstd -xf obj.tar.zst`. The original receipt is
unchanged; a clone without rehydration does not have the individual objects.
