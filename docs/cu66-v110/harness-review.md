# V110 canonical and native harness review

The canonical harness binds its baseline to the actual V109 FETCH native
receipt and canonical proof, checks all 18 selected source origins and every
focused candidate source against recorded hashes, and retains the V107 bench,
packaging and admission dependencies. It runs the candidate with assertions
active, rejects warnings, then compares each candidate seed's output, events,
cycles and canonical artifacts byte-for-byte with the frozen V109 control.
Control RTL is reused and not recounted. At review time the busy and combined
canonical runs were still in progress; neither had a final receipt.

The native preparation path requires a passing canonical receipt plus all
applicable focused proof pins, then verifies source, tooling, recipe and policy
hashes before a separately audited dispatch. The frozen 10 ns clock, part,
trial limits, resource guards, no-silent-retry rule and clean repeat requirement
are explicit. The report script records local predicate mapping in TSV without
preservation constraints. The root reported a parser self-test matching all
four actual V109 report sets; the launcher additionally checks the selected
FETCH report set against its pinned receipt.

This flow measures an out-of-context component. It cannot qualify the complete
production parent, board I/O or hardware frame/latency gates. Machine-readable
review: [harness-review.json](../../experiments/python-gamebub-v110/audit/harness-review.json).
