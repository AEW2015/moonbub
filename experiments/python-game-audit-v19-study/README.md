# Python Game v19 evidence audit

Read-only audit for the finalized v19 frame-grant and causal-stripe Python studies. It records the 720×480 coded canvas, 720×405 active image, and 30 scheduled frames/s target. Both final-readiness signals were received; all source pins, retained verifier replays, analysis replays, and semantic evidence checks pass.

The finalized stripe audit verifies 264 source/object pins, 16 packet decisions, 97,308 exact blocks, 6,227,712 residual samples, 6,224,472 reconstructed samples, 253,440 selected UI words, and ten conditional profiles. It checks coefficient-demand conservation, residual/YUV and packed-YUV8 canonical-tag round trips, 84.64% GENERAL MAC reduction against the existing bypass baseline, hash-bound matched analysis, and local-resource arithmetic. The retained verifier and analyzer checks pass. The modeled sparse service reduction is 4.27%; compact YUV8 adds 20.18% within the same conditional model. Every native case misses the 33.33 ms budget. These are not native or RTL timing results.

The frame-grant audit verifies 58 source pins, 12 cases/790 capture events, seven native profiles, fixed-service pairs, FINISH/FINISHED/RELEASE ownership transitions, five-token limits, and paid FG19 wire traffic (36-byte message plus 28-byte IPv4/UDP overhead). The primary pipelined grant case accounts for 10,496 forward and 15,744 reverse control bytes. Three intentional unknown-outcome cases retain owners at bounded safe stops; they are not counted as drained or recovered.

Selected RGB565 patch words match exactly with zero mismatches. The full requested-HUD gate is **unmet**: the 7200 baseline has 39 full and 24 partial decoded frames, and its grant profile has 37 full and 20 partial frames. Each partial frame selects 15,360 words exactly and omits 5,760 requested words from the fourth rectangle. Across both profiles, 44 decoded frames omit 253,440 requested words. Those omitted lossy base pixels are not described as protected. The primary 2600 profiles retain all 21,120 requested words in every decoded frame.

Timed benchmarks are never rerun by this audit. It replays only the retained deterministic verifiers and hash-bound analyzers.

The audit does not claim actual ESP32, RF, ISA, or FPGA fit. Scheduled cadence and accepted packets do not establish decoded-display FPS. Source pins are reported as checkout-relative paths, including pins copied from historical absolute paths containing `/moonbub-30fps-study/`.

Run the lightweight guards with `/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_audit.py`. Run `audit.py` to regenerate `audit.json`; pending evidence intentionally returns a nonzero exit status. `audit.py --check` recomputes without writing. Invocation logs are retained at the study root and mirrored in `logs/`.
