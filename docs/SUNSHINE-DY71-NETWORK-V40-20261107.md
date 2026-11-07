# Sunshine / DY71 next integration gate

V40 implements an explicit two-frame CU66 network lab endpoint for the color-verified V023 FPGA. It is built and tested offline, not installed. No live Windows CU66 encoder or production network agreement is established.

[Complete DYN1 v1 contract, port5535, credits, integrity, presentation and recovery](../firmware/experiments/v40-dy71-network-lab-20261107/docs/SUNSHINE-DY71-NETWORK-LAB-v1.md).

[Reference uploader](../firmware/experiments/v40-dy71-network-lab-20261107/tools/dy71_fixture_sender.py) and [golden vectors](../firmware/experiments/v40-dy71-network-lab-20261107/docs/golden-vectors/).

Windows branch `gamebub/cu66-v70-windows-20261105`, commit `15ca3422`, was reported to qualify the exact retained key/P fixtures offline. First adapt/test the uploader against this lab contract, wait for installed-app and heap/identity readiness, then transmit the exact original pair on request. Do not send JPEG/MSV1 to5535 or start a sustained stream. No network run has been started by this handoff.

Next after KEY/P: bulk HUD service and continuous ownership, live host encoder, stage timing and sustained-rate tests; audio/controller coexistence follows video. V023 scalar diagnostics took about54seconds for two frames, so this is correctness bring-up, not interactive or30fps readiness.
