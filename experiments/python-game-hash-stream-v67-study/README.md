# Ordered tile → canonical hash stream (v67)

The model accepts normalized **uint8 8×8 tiles** in exact planar tile-raster order and produces the same canonical SHA256[:16] as full row-major serialization. It reuses one fixed **8×720 uint8 strip (5,760 B logical data)** across Y/U/V. Chroma serializes only the first 360 columns. It owns no full-frame reconstruction array.

Two explicit domains are checked: `CS66_i16` serializes each canonical sample as little-endian two-byte data, matching legacy canonical tags; `CU66_u8` serializes validated eight-bit samples. Both start with little-endian 720×480 geometry. The input API rejects other dtypes rather than casting or truncating. The producer verifies that the original canonical samples are integers in 0–255 before making its uint8 input views.

The 457-frame causal campaign checks **914 domain results**, **3,701,700 tiles / 236,908,800 canonical samples per domain** and 190,569 deterministic consumer-pause checks. Every legacy tag matches the stored canonical tag; every packed-u8 tag matches independent full-plane serialization. Neither canonical input nor encoded data changes.

Per frame, 8,100 tiles become 960 planar rows. The i16/u8 domains serialize 1,036,804 / 518,404 bytes including geometry. The largest transient serialized row is **1,440 / 720 B** respectively, additional to the strip. SHA context/block padding, Python objects/temporary allocations, ports, control and CDC are excluded from the strip-data bound. This is not a total BRAM/SRAM or allocated-memory measurement.

Malformed identity/order, duplicate/extra tiles, wrong dtypes and incomplete finalization poison or close a frame context. Input tiles are copied into owned strip storage before returning. The final tag is idempotent, and input after finalization is rejected. A caller must compare the expected tag and complete HUD/integrity validation before publishing a reconstruction bank; the hash component does not implement bank ownership, epoch/replay checks or panel recovery.

This supplies the tile-order conversion contract needed before mapping a streaming hash engine alongside inverse reconstruction. It does not execute SHA RTL, model ready/valid clocks or prove FPGA fit/throughput. Canonical full planes in the replay are external input/oracle models. The display-filter rows and this decode-side strip cannot automatically share storage during concurrent decode and scanout.

```sh
cd experiments/python-game-hash-stream-v67-study
python -m unittest -v test_model
python benchmark.py
python verify.py
```

The independent full 457-frame replay and five directed tests pass for both domains, including full-frame hashlib parity, input ownership/pauses, immutable domain selection, malformed order/duplicate/early finalization and dtype rejection. No native codec, firmware or bitstream is changed by this experiment.
