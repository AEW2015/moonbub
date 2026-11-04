# Python Game v13 evidence audit

This is a lightweight, stdlib-only audit for the v13 cache-admission,
causal-motion-gate, actual-wall execution, and bounded UI-cache studies. It
reads each study's `results.json` when present and emits `audit.json`. Inputs
being regenerated are explicitly marked as awaiting finalization; no result is
inferred from absent fields.

Target scope is a 720x480 canvas (720x405 active image) at 30 fps. The audit
keeps source-frame identities, unique RGB content hashes, synthetic/real cohorts,
complete packet sizes, cache bytes and pins, rejected work cost, causal gate
evidence, oracle comparisons, exact UI-region reuse, strict/eventual
presentation, charged service, actual host wall time, and hardware timing as
distinct evidence categories. Source pins are hashed twice for stability and
checked separately per available study.

Run with the project interpreter or any Python 3 interpreter:

```sh
python audit.py
python -m unittest -v test_audit.py
```

This is evidence accounting only. It does not benchmark codecs, claim hardware
timing, or turn an oracle result into a live policy guarantee.

## Frozen audit summary

The five result files currently audit as follows:

- Cache admission: 172 paired rows, 163 admitted and 9 rejected; all compared
  whole-packet hashes match, and all 49 exact-cache-hit attempts are counted.
- Motion gate: 616 profile decisions and 775 candidate attempts; 136 real-source
  gated rows avoided BM attempts, while 5 synthetic translation rows ran them.
  All 154 same-reference control and gated packet comparisons match.
- Finite execution: 16 cases and 1,104 capture events; strict presentations
  rederived from timestamps with no mismatches and no unresolved work. Measured
  CPU, resize, encode, and decode wall durations match their charged durations
  for every recorded observation.
- UI cache: 160 paired rows, 292 exact region-payload hits (176 despite changed
  whole-source RGB), at most four entries and 51,286 reported persistent bytes.
  All full-frame packet hashes match; this standalone study is not included in
  the finite-execution results.
- Credit window: 7 cases and 780 capture events; 661 prepared and decoded,
  647 strict and 661 eventual presentations, no strict timestamp mismatch or
  unresolved work. Sender/credit windows agree with their factories; ingress
  remains at two slots and framebuffer roles at three. Regression tests cover
  the expiry-versus-deferred-ACK edge and the positive ACK-after-drain control.

Every available study's source pins match and remain stable during the audit.
The finite runs measure Python execution costs; none proves sustained physical
30 fps or qualifies a three-credit window as a hardware default. The credit
study combines cache admission, UI reuse, and the fast receiver, so its run
counts are not a window-only comparison with the earlier finite-execution
study.
