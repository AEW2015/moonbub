# Offline cadence and observation-window analysis

Reproduce from this directory:

```sh
python3 test-analyze-cadence.py
python3 analyze-cadence.py results-1800-strict-failed/verified.jsonl
```

This script reads the already-verified JSONL; it does not validate simulation logs,
frame content, hashes, or provenance. Use `analyze-results.py` for the strict
verdict and the archived evidence for its limitations. It assumes the archived
100 MHz timebase and rational 30 Hz capture schedule. Gap percentiles use sorted
index floor((n−1)·p/100), and the span FPS is (N−1) divided by first-to-last
presentation time. Neither is a strict 60-second capture-window FPS.

For this archive the 1,800 presentations span 59.97648478 s, corresponding to
29.99509 fps over 1,799 intervals. Presentation gaps range from 30.73353 ms to
46.10030 ms (median 30.73353 ms, p95 46.10030 ms). All timestamps fit within
an observation window `(start, start + 60 s]` if its start is 2.38483 through
25.90004 ms after the first capture, inclusive at integer-cycle resolution.

That shifted-window observation does not change the strict result: only 1,799
presentations occurred in the 60 seconds following the first capture, and the
last was 2.38483 ms late. It does not show that a phase change is physically
implementable, eliminates per-frame lateness, or predicts the behavior of a new
RTL run or hardware.
