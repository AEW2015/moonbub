# Parser validation-stage board build preparation

This folder is prepared, not synthesized or routed. It copies the selected original `stb1-v001` 79-input source set and substitutes exactly two reviewed modules: the existing CE receiver factor and parser state19 validation split. All remaining 77 inputs are byte-identical. All XDC/Tcl constraint files, source order, top, part, clocks, pins and build scripts retain exact original bytes. No checkpoint is copied or reused.

`source-freeze.json`, `source-order.json`, `overlay-binding.json`, the two source diffs and `synth-review-request.json` bind the work. The latter is deliberately NOT an authorization receipt. Root must write `review-approval.json` bound to overlay/source hashes and `allow_synth=true` after functional review. The inherited runner requires that receipt and sets TEMP/TMP under C:/moon/tmp. No implementation or BIT authorization is requested here. No hardware or firmware operation occurred.

Prepared launch after root approval: `python run-phase.py synth`. Synthesis emits constraints/check-timing/CDC evidence; a later independent implementation gate is required for placement/routing/timing. Functional simulation and synthesis/timing are distinct gates. No timing success, hardware readiness or new image identity is claimed.
