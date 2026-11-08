# Fault and parallel-prefix portable source exports

Both requested exports pass **source-preparation checks only**. The frozen [exporter](../../scripts/cu66-v110/export_replay.py), SHA-256 `46ac054ad093186a4ad1d7d7a313dfa062cb3c675055a1e5dececce8f25e42e0`, copied the exact qualified source closures and build/report/clock recipes into new external trees. No Vivado, RTL simulation, synthesis, placement, routing, DCP replay or hardware operation was performed.

| Variant | Preflight | New external source tree |
| --- | --- | --- |
| Fault | [v110-fault-initial-20261108T145006208611Z-77743f](../../experiments/python-gamebub-v110/prepared/v110-fault-initial-20261108T145006208611Z-77743f/preflight.json) | `/home/lori/gamebub-build/cu66-v69/v110-export-fault-check-20261108T145410795032Z` |
| Combined parallel prefix | [v110-combined-prefix-20261108T145130355355Z-bca7ac](../../experiments/python-gamebub-v110/prepared/v110-combined-prefix-20261108T145130355355Z-bca7ac/preflight.json) | `/home/lori/gamebub-build/cu66-v69/v110-export-prefix-check-20261108T145410795032Z` |

The fault preflight SHA-256 is `55a4d9554b8c6f7a2691436822b87ea80a3bf3103c77c303a2c5d1602c5e2374`; its exported replay-manifest SHA-256 is `49848153080fa4594ba3c7ba5b3adec4af6ac2488568f30d3bf06bb36e6526bf`. The prefix preflight SHA-256 is `277d8645665dc5fb205ae851d80197ca79d5422dc8c547d73465b72a47261dc4`; its replay-manifest SHA-256 is `45f7b26804ecc79aac481768ceb37d9bbee6b3965313164f11eb365e3adc9f70`.

For each export, independent checks verify:

- All **18 actual source bodies**—17 SV modules and one quantizer header—match the preflight input card, actual origin files and exported snapshot hashes. Historical aliases are resolved by the source card, not by reading an older similarly named body.
- The complete 17-file read order and include-directory list match exactly. The header exists under the declared exported include directory.
- `run.tcl`, `report.tcl` and the fixed 10-ns `component.xdc` match their exact preflight hashes. The original prepared `inputs.tcl` hash is checked separately; exported `inputs.tcl` is intentionally regenerated with build-relative source paths and a separately recorded hash.
- The only active XDC command is `create_clock -name component_clk -period 10.000 [get_ports clk]`. Source-order inspection confirms `read_xdc` precedes fresh `synth_design`; no tool execution is implied by that inspection.
- Every exported manifest file hash matches, and the source contract's canonical/focused proof pins still match their existing files.
- Plain `tclsh`, run from `/tmp`, evaluates **only `inputs.tcl`** into the correct absolute source/include/XDC paths under the actual exported root. A second evaluation substitutes an independent, uncreated root and produces the same relative layout there. These are path-construction checks, not simulation or native recipe execution.
- Exported inputs select `start_mode=rtl`, define no checkpoint variables and reference no original build/checkpoint paths. No DCP is exported. The unchanged `run.tcl` still contains its original checkpoint branch, but that branch is not selected by the exported inputs. Fresh RTL mode requires neither an original DCP nor the original build directory.

The common exact `run.tcl` SHA-256 is `3a5cb36dbb04681712ac5ee48146c73e88b95f5de818a4d9282ffdb503e59d47`, and XDC SHA-256 is `8620eb069e31e2bc5c90dce4c271fe55056abd7ec3024ea0bde0c2054e515106`. The fault report recipe SHA-256 is `06f6a30f7935142a356d3b4f8151ba5c464526afbae82298f591d5caa152f38c`; the prefix report recipe SHA-256 is `289c5a5ec2c9d5a8eb22ab772d915534def4661a414310e624131bbac9171c5e`. Each variant retains its own exact reporting recipe.

The complete [fault check](../../experiments/python-gamebub-v110/export-fault-check.json), SHA-256 `7f3b9711c555ff1924064e73cfefe2ff9b3765bcc0955b07344fede36f8a3c2f`, and [prefix check](../../experiments/python-gamebub-v110/export-prefix-check.json), SHA-256 `79dac7c4ba30c129d32bb983b12030a8ea735a8c1bb6617d15d034f4ebaae3fa`, retain exact exporter commands, preflight/manifest/source/recipe hashes, source order, include paths, proof pins and both plain-Tcl path tests.

These trees make the proposed implementations portable and reviewable. They do not supply an actual timing replay, clean repeated route, clock gain, full-parent signoff, sustained hardware 30 fps or validated complete decode below 10 ms. Existing source/proof/preflight/exporter files remain unchanged.
