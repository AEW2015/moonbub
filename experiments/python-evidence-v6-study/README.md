# Python evidence v6 audit

This folder independently audits stored Python experiment JSON. It does not
rerun video, encoding, scheduling, or service benchmarks. `audit.py` reports
the v5 and v6 key/P preparation timing summaries recomputed from individual
records, checks source pins declared by result files and media manifests, and
summarizes native PTS and rendered-content diversity for the corpus and service
cases.

The combat primary/held-out comparison has 15 exact shared native PTS (100–114)
whose rendered hashes match. Repeated source content means matching hash values
alone cannot establish equivalent emitted IDs. The `overlap_by_id` helper
compares ID sets and hashes attached to each ID independently.

When new result JSON is available under `python-key-prepare-study`,
`python-measured-service-study`, `python-arithmetic-study`,
`python-token-entropy-study`, or a `python-*-v6-study` folder, the audit
includes it without changing or regenerating that result. Token entropy
metrics, 24 whole-key timing samples, 72 entropy-plane samples, and counts over
the 33.333 ms budget are recomputed from records. For measured service
cases, the audit recomputes KEY/P encode and decode medians and p95 from
per-packet records. It reports eventual presented IDs, IDs presented before
the capture-window end, and IDs in the diagnostic `[start,end)` window as
separate fields. It compares quality only for IDs presented by both cases.
NumPy-style summaries use linear
interpolation. The measured-service model's own p50/p95 also use its documented
lower-order-statistic and nearest-rank rules, which the audit reports alongside
linear values. These are offline Python service observations and modeled
delivery outcomes, not realtime or hardware qualification. Source files listed
in result JSON and media manifests are
verified before and after reading the available results. Missing pinned files
are recorded explicitly.

Run from this folder with:

```sh
python3 audit.py
python3 -m unittest -v test_audit.py
```
