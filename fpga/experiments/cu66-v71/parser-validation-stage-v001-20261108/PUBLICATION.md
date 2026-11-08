# Preserved parser-stage review evidence

All files copied from the original experiment remain byte-identical; receipt paths and commands are historical and intentionally not rewritten. The publication manifest binds each preserved file to its original path/hash. Generated VVP binaries and caches are excluded; source, compile commands, logs, all57 actual packet case hex files, fixtures and expected outcomes are retained. No original receipt was edited, no repository commit/push occurred, and this publication does not claim synthesis/route/hardware completion.

The original frozen test manifest SHA is3f354b59f41de07850a505e2789a618c6a3e000b826d2f886e3f9758d240c7dd. Original source-control/parser-candidate hashes and active focused03/packets02/watchdog01 gates are preserved in frozen-tests.json. Earlier startup/less-complete test attempts remain labeled history. See README.md for semantics/limits, especially provisional diagnostics and the demonstrated watchdog cutoff difference.

## Restoring the exact production input set

Use the sibling stb1-release-v028-20261108/inputs tree as the immutable79-file baseline. Copy it into a NEW C:/moon working directory; never modify the release. Replace exactly these two files in the new copy:

1. metadata-baseline-v022/cu71_receiver_final_v022.sv using support/cu71_receiver_final_v022.sv (the independently reviewed CE factor, SHA316123fb...).
2. packet-rx-staging-v001/cu71_packet_rxstage_v001.sv using candidate/cu71_packet_rxstage_v001.sv (staged validation, SHA39197a68...).

Preserve each full fpga/experiments/cu66-v71/... relative path. Compare all79 resulting hashes with candidate-production-source-freeze.json. RESTORATION.json binds both replacements and the baseline; the other77files were verified against the sibling release. This package is a source/test experiment, not a newly selected board image. Selected V028 remains independent.

## Replaying parser checks after relocation

run-focused.py and run-packets.py use their own directory for parser sources/tests/fixtures and accept a new --out name. Restore local Icarus binaries at C:/msys64/ucrt64/bin, or change a COPY of a runner to the local installation and preserve that changed command/hash. Child-only PATH/TMP setup is explicit. New replay receipts must go under a fresh evidence name, keeping the published receipts intact.

run-watchdog.py intentionally binds the original exact CE receiver path under C:/moon/builds/stb1-ce-v001/inputs/... . If that build cache is pruned, restore that exact receiver file from support after verifying its SHA, or update a COPY of the runner to use this support file and record the path-only adaptation. The receiver test uses actual receiver/parser control and explicit inert unrelated datapaths; it is not full-system simulation. Source-bindings.json also records the original CE base path, whereas RESTORATION.json provides the standalone restoration recipe.

Reader-audit receipts likewise preserve original firmware paths. Exact inspected V54/V55 source files are copied under support/readers/ so the audit can be independently reproduced even if old workspace copies disappear. Fixture CU66 files are original immutable KEY/P/P goldens; per-case mutations/CRC repair are reconstructed by run-packets.py and all actual57case bytes are retained in evidence/packets02.

No FPGA programming, firmware flashing, Windows driver change or network transmission was performed to publish this evidence. Root owns the separately running synthesis and any later selection.
