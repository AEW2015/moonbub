# V29 current-source quiet-block adaptive search

This experiment retains full720×480 coded /720×405 active geometry and frozen
GM27 prediction, vector syntax, quantization and reconstruction. The host first
scores zero motion on stride4 samples from the current source and the accepted
reconstructed reference. For each block, weighted SAD is divided by its actual
weighted sample count. Blocks with sampled MAE≤2 (`adaptive_zero2`) or≤4
(`adaptive_zero4`) keep zero vectors. Other blocks use the same81 stride4 coarse
and25 stride2 half-pixel refinement candidates as v28 mixed search. Constants
were fixed before running the corpus; threshold2 is the conservative experiment.

Search gathers compact active sample coordinates. Counters include the quiet
screen and every actual active candidate sample. Full-resolution prediction,
transform, quantization, entropy coding, reference reconstruction and packet
serialization remain paid. The gate is an encoder heuristic: sampled quietness
is not a full-resolution quality guarantee, so output/error must be measured.
No frozen module globals are altered and no source image substitutes for a
reconstructed decoder reference.

`analyze_with(gm27,...,search_policy='adaptive_zero2')` creates a preparation owned
by the supplied frozen GM27 implementation. `analyze_planes` uses its own frozen
GM27 owner. `work['search']` records quiet/active block counts, screen samples,
all scored sample differences and actual logical reference gathers. Addresses
clamp each bilinear tap separately, preserving negative-edge semantics.

The matched-reference benchmark uses first12 retained frames from each of two
Mass Effect scenes; candidate outputs never become later references. The parent
experiment separately regenerates full causal controller histories. These are
Python models, not ESP32/RF/QSPI measurements or an FPGA/native30fps proof.
