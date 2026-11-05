# Fresh native temporal prefixes, coarse quality grid (V61)

This study decodes 48 fresh native settings across source IDs 24–47 from the four existing Mass Effect clip cohorts: 1,152 actual access units total. Settings use the frozen single-thread, low-delay presets and six quality settings per codec. PTS resets to 0–23 for each encode; source IDs, original PTS, exact HUD, extradata, and the common 80-byte binding budget are retained for comparisons.

Five of 48 parameter points have at least one frame over the complete packet cap; six individual access units exceed it. All failing frames and points remain in the archive. These are fresh settings on later windows from known clips, not unseen games, a globally optimal frontier, or a hardware decode test. No physical 30 fps or FPGA result is established. No new encoder parameters are selected in this study.

Reproduce from `benchmark.py` and `verify.py`; `verify.log` reports 48 points, 1,152 decoded AUs, five cap-failing points, and exact source/HUD checks. Native encoder output timing is not endpoint timing.
