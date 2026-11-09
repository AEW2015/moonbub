# V114 native driver review

This is the earlier review snapshot, before the optimized resource-recovery
branch and final peer proof. Its recorded source hashes describe that snapshot.
The source-bound per-clock preflight and terminal audits govern later launches;
see [optimized qualification](optimized.md) for the completed recovery evidence.

Read-only refresh of both native drivers, both policies, the shared budget, six comparison controls, archived V113 source origins, and the current primary spatial proof. Machine-readable pins and findings are in [`native-driver-review.json`](../../experiments/python-gamebub-v114/audit/native-driver-review.json). No native preflight, build, or launch was performed.

Both drivers reparse all six timing controls from five pinned route reports apiece; receipt/report hashes and parsed clock, timing, and routing values match, and all six controls miss setup timing. The 18 archived V113 source snapshots are checked against both source-origin and retained-artifact hashes. The drivers bind a named auditor and the native source SHA, require all eight preflight checks, and enforce the shared limit of four initial measurements plus one positive fresh repeat across both studies. Fresh composition checks constrain the selected source-order replacement set, exclude the V111 header, bind focus proof sources to current candidate hashes, and preserve raw verdict/stdout and canonical data checks.

The fresh V114 bench API derivation pins the frozen V107 bench with 144 `need(` occurrences including the helper definition, and a derived bench with 145 occurrences after adding one pending-command eligibility assertion. The native spatial gate checks all original checks are retained and applies the recorded edits in reverse to recover the original bytes exactly. Both policies separately pin the V113 canonical reference SHA. Primary composition replaces one RTL body; optimized composition replaces two and also requires its extra `control-peer` focus proof.

The current selected primary spatial summary is `PASS_V114_SPATIAL_CANONICAL`: 44 candidate case profiles, 42 directed checks, and two transport seeds with 12 successful profiles and two abort/reset retries each. This meets the primary functional prerequisite only; no native preflight or launch is claimed. The optimized spatial summary and its required `control-peer` proof are absent at this audit snapshot, so optimized qualification remains unavailable.
