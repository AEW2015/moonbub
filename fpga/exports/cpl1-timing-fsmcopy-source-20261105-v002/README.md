# CPL1 timing-cleanup source and evidence

Restricted independent KEY CP23/HC22 fixed-ROM diagnostic, CAPS=0. No custom network port; no full-profile, P-frame, audio or 30 unique fps claim. Existing installed v30/build50 has not been changed.

Run `python reproduce.py verify`, then `python replay.py --full --output NEW_EXTERNAL_DIRECTORY`. Icarus/vvp and Python are external dependencies. Simulation uses actual pad branches and custom digital models, not physical hardware or vendor timing simulation.

Run `python reproduce.py build NEW_EXTERNAL_DIRECTORY` with Vivado 2025.2 for XC7A100T-CSG324-1. Set VIVADO to its executable if needed. When present, implementation-repair.tcl and implementation-chain.json are part of the canonical implementation: reproduce the baseline source build and all recorded physical optimization steps. Source files in inputs/ and sim-inputs/ are selected exact copies; runtime assets are mandatory. No external GameBub checkout is needed. A routed checkpoint remains locally at the path and SHA in LOCAL-CHECKPOINT.json; regenerate it with this build recipe.

reports/timing-gate.json records routed setup/hold/pulse, four bus-skew checks and routing. Read coverage gaps and DRC/CDC reports separately: unbudgeted/asynchronous I/O and external QSPI hold are not board signoff. digital-board-evidence/ records functional model and independent CRC evidence. image/ contains the candidate BIT, exact routed-checkpoint binding, unchanged-source proof, uncapped DRC and final register-copy function proof. Add `image` after the build output-directory argument to regenerate a BIT after the rebuild timing gate passes. Hardware programming/playback has not been performed for this candidate. A complete second P&R reproduction has not been executed as part of packaging; the exact build recipe and selected route evidence are provided.

Retain upstream source notices and licenses/. An image, if separately generated, must be bound to the final routed checkpoint and is not permission to program hardware.
