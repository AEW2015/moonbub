# Qualified forty-frame DYN1v3 fixture

This package replays oneKEY+39dependentP frames using the unchanged count-bound v3 sender. Source metadata and geometry/quantization are in manifest.json. It is a20second rendering-clip interval sampled2fps with RGB444 prepared colors and uniformq32, notMassEffect/live/FPS evidence. Original source MP4 is not duplicated. Independent canonical/HUD/RGB565/HC70 oracles are compressed losslessly in oracles; index.json binds uncompressed and compressed hashes.

Offline full-frame/reference/rollback and exact-native HUD checks passed. Physical V56 failed atframe8; V57 failed atframe17 due to ESP32 contiguous-allocation failure. The package is not a passed40-frame hardware sequence. Coordinate exact firmware/count40, fresh FPGA, sourcefilter, capture and readiness before transmitting; no auto-retry or reset. Keep the final lease retained on error. Source/qualification scripts remain at the historical C:/moon paths pinned in the manifests.
