# Additional temporal qualification of frozen motion policy (v59)

**The frozen v53 policy again saves a small number of bytes and increases cumulative source error.** This is an additional temporal window, not a retuned policy or a project-wide unseen-media claim. No v53 model, threshold, proxy, quantizer or selection rule was changed.

| Cohort | Separate zero bytes | Selected bytes | Byte change | Separate zero active MSE | Selected active MSE | MSE change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mass-effect-10000 | 359,645 | 357,689 | -0.544% | 17.25033 | 17.73368 | +2.802% |
| mass-effect-4500 | 554,439 | 540,051 | -2.595% | 27.36174 | 29.83850 | +9.052% |
| mass-effect-1600 | 95,180 | 95,139 | -0.043% | 10.74909 | 10.77392 | +0.231% |
| mass-effect-combat | 776,074 | 769,377 | -0.863% | 30.30958 | 31.19250 | +2.913% |

The policy selects 38 zero, 41 score-proxy mixed and 17 local-Pareto mixed frames. All 96 inputs and selected frames are retained; all candidates fit the complete 49152-byte cap. There are 288 actual adaptive proposals with 1728 full/compact AB38 alternatives, plus 96 separately regenerated fixed-zero qualification packets with 576 additional AB38 alternatives. All 96 qualification packets are byte-identical to the existing binary-v40 zero packets. All 2,027,520 selected HUD words are exact.

## New caller, unchanged policy

`helpers.kernel` imports the frozen `python-game-quantized-motion-v53-study/model.py`, explicitly bound to its original helper. There is no new policy model in this directory and no frozen function/global patch. `adapter.py` selects original source IDs 24–47 from each of the four known v40 clips, preserves their actual global IDs/PTS, validates background 16 and consecutive HUD references, and starts a fresh receiver with key 24 and no previous reference. Frame 24 is not renamed frame 0.

The 24-frame window ends at 47. The earlier motion study used IDs 0–23; this is a predeclared additional temporal window for that fixed motion policy. The underlying source media and source-v40 corpus already existed in this repository, so this is not a claim of unseen media or a final broad generalization benchmark.

The unchanged v53 kernel pays shared zero/global-grid32 source analyses, exact pre-RDO quantized visible-YUV error and fine39 coefficient-bit proxies, 16 bits per nonzero macroblock, score4 and local-Pareto mixed maps, private Prepared construction and actual zero/mixedA/mixedB source encodes. All original global RDO/legacy-size reversion precedes hidden suppression. Actual full/compact AB38 options and stable legacy ties remain unchanged. Three fitting candidate receives use forks of the same selected state; only actual complete bytes and original-source RGB565 active SSE can admit a mixed frame. Only the selected fork advances.

## Separate zero qualification and future quality

A second owned trajectory independently regenerates fixed-zero source packets at its own pure-zero incoming references. Every packet must match its original binary40 packet byte-for-byte, then decode with exact canonical references, HUD and source quality. Its encodes, options and service time are archived separately in `zero_qualification`; they are not counted as the adaptive policy's three proposals.

Once a mixed frame changes the selected reference, the adaptive counterfactual zero proposal is no longer the separate pure-zero proposal. The local current-reference byte/SSE guard therefore does not guarantee future quality relative to that second trajectory. The cumulative increases in every cohort above reproduce that limitation on another temporal window. No quality-preserving or HEVC/AV1-superiority claim follows from the rate savings.

## Evidence and paid scope

Three producer tests pass: exact ID/key/reference slice boundaries and no input mutation, rejection of bad IDs/quantizers, and actual frozen-kernel key 24 encoding matching binary40 followed by a fresh receiver accepting frame24 first. Eight independent tests and the complete replay pass: 96 selected IDs24–47, 288 adaptive proposals/1728 AB38 alternatives plus 96 separate-zero reencodes/576 alternatives, 96 original zero byte goldens and 1329 source pins. The frozen53 kernel hash and every policy parameter are unchanged. The independent verifier separately rederives the frozen policy, source/proxy maps, actual mixed prediction/forward, original quantization/RDO/reversion, all entropy choices, current guards, owned future histories and the fixed-zero qualification.

Main `paid_sender_ms` and `paid_policy_with_receive_quality_ms` retain v53's scopes: all shared analyses, proxy/mix and three source encodes, with receives/quality checks included in the latter. Separate fixed-zero qualification work/time is reported independently. Source read/conversion, previously paid shared HX33 generation and archive I/O remain separate. All actual losing packets, arrays, costs, motion maps, source/HUD descriptors and metrics are retained. No physical 30 fps, FPGA/ESP32 cycle/fit, new native-codec frontier or hardware test is claimed here.

```sh
cd experiments/python-game-temporal-qual-v59-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_verify
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

All previous studies, including the v53 kernel, remain frozen.
