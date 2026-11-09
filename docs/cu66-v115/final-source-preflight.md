# V115 final source and focused-recipe preflight review

The owner and final-ingress candidates pass this independent **static source and
recipe review**. The detailed current hashes and reversible checks are recorded
in [final-source-preflight.json](../../experiments/python-gamebub-v115/audit/final-source-preflight.json).
This review did not run a build, test, RTL simulation, native flow, or hardware.

Both recipes recreate their candidate bytes from the pinned original and reverse
exactly back to the original: seven owner edits and two final-ingress edits. The
combined source map keeps the selected refined 18-origin composition and changes
exactly two paths: the V91k top to the owner candidate and synchronous ingress
to the final-ingress candidate. Current source hashes match those recipes and
origin pins.

The owner change adds one held authorization bit at existing registered real
kill births, clearing it on reset and new command. The raw valid/tag signals and
kill edge remain in place. The additive assertions guard birth provenance,
ownership, reset/command revocation, delivery, and stale private-pulse
suppression. The recipe makes no arbitrary private-state recovery claim.

The final-ingress change captures the unchanged 32-bit next-address formula on
the existing `stage_read_req` edge, then uses that captured value for bounds
preparation during the existing `FETCH_WAIT`. It retains the six-bit index,
leaves the payload unreset, and declares zero public-cycle delta. The focused
qualifier keeps assertions enabled with Verilator `--assert -Wall`, uses owned
C++ `-Wall -Wextra -Werror`, rejects Verilator warnings, and has no warning
suppression. The final-ingress pair compares the candidate with a frozen
reference on every public clock edge. The owner focus likewise retains strict
flags, 78 original directed checks, four real physical-drain checks, and the
stale-private fixture before its additive checks. These are recipe requirements,
not results of this audit.

**Runtime remains pending for the complete final composition.** The owner-focus and final-ingress selectors now point to PASS receipts, and
their selector hashes match those receipt files. I recorded the receipt IDs and
hashes but did not independently audit their source snapshots or artifacts in
this static review. Full-composition qualification therefore remains pending.
No third-composition native preflight card is present, so this report provides
no launch authorization.

The existing owner `source-review.json` is author-produced and was not counted
as independent evidence. I independently recalculated current hashes and
forward/reverse recipe bytes. This audit was limited to static provenance and
runner configuration; it does not establish functional or timing qualification.
