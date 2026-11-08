# V110 hardware-evidence checker audit

The offline checker and its recorded self-test are source-bound: both current source hashes match the receipt, and the root review pins that receipt by SHA-256. The transcript records 12 tests, 23 findings, zero failures, and zero errors. I reviewed the stored receipt and source without rerunning tests.

The checker requires explicit rational clock calibration, counter width, wrap count and reset epoch, and hashed provenance files. It validates the declared fixed 30-Hz release schedule, exact 60-second and 600-second windows, frame identity and order, supplied integrity flags, queue observations and health totals, and every packet-complete-to-validated-publication latency using an exact integer comparison. The synthetic test’s single 10 ms sample fails even with a 5 ms median; the reported outlier is frame `60s-source-17` on trace line 18. A self-declared `hardware_capture` fixture can pass the numerical gates while both hardware flags remain false.

The limits are material: queue peaks, health totals, calibration metadata, flags and provenance are supplied trace observations or claims. The checker can verify hashes and internal consistency, but cannot attest device execution, events missing from the trace, or whether the supplied health totals represent all device activity. The hardware gate still requires independent calibrated capture with real contention and production integration.

Machine-readable audit: [`hardware-evidence-final.json`](../../experiments/python-gamebub-v110/audit/hardware-evidence-final.json).
