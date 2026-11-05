# Targeted native peak-rate controls (V61)

This follow-up measures 21 rate-control settings against the same 24 source frames (source IDs 24–47) used by the coarse V61 grid, decoding 504 actual access units. Three points each contain one access unit over the complete packet cap. Requested bitrate and VBV parameters are not treated as delivered rate; archived AUs and cap checks determine the result.

This is a targeted combat peak-rate experiment, not held-out calibration, a new source window, or a physical transport measurement. It uses the same common YUV, exact HX33 HUD, and 80-byte binding accounting as the temporal grid. No physical endpoint or FPGA 30 fps claim is supported.

Run `benchmark.py` and `verify.py`; the independent replay retains both passing and failing settings.
