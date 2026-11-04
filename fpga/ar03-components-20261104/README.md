# AR03 component source export

This is a small, offline, source-only export of five frozen RTL modules and two bounded smoke benches. `source-snapshot.json` records exact original paths and SHA-256 hashes, plus the parent evidence-manifest digests. The files retain their repository-relative paths beneath `source/`.

Run the smoke checks with Python 3 and Icarus Verilog (`iverilog` and `vvp`) on `PATH`, or the known Windows MSYS2 UCRT64 location used by the original runs:

```powershell
python run_smoke.py
```

The runner verifies every copied source hash, compiles both benches, checks their exact summaries, and puts all generated binaries in a temporary directory. It does not modify this export.

The two smoke checks cover CP02 admission bounds/cancellation and AR03 envelope storage-parameter capacity. They do not reproduce the full 259-case CP02 corpus, six-plane KEY reconstruction, 56-case envelope replay, full protocol integration, or historical evidence runs. Those results remain bound to the separate manifests listed in `source-snapshot.json`.

This export is not a complete firmware distribution, bitstream, live AR03 backend, or hardware release. It contains no SDK, private dependency tree, executable, fixture corpus, or complete receiver. The envelope module issues only an outer-envelope certificate; inner AR03 validation, AF03 publication, memory integration, physical drain, and presentation are outside its scope.

The source-bound timing result for the parent CP02 variant reports 20 RAMB36, 1,909 LUTs, and an isolated clock-only OOC setup/hold estimate of +1.606 ns/+0.260 ns at 100 MHz. The separate ideal registered-neighbor diagnostic has +1.606 ns setup but −0.489 ns hold at 451 endpoints. Route, combined fit, board timing, and full-path throughput remain unestablished. These are retained evidence summaries, not measurements reproduced by the two smoke benches.

The retained variant-002 KEY component measurement in `fpga/experiments/ar03-entropy-20261104/measure-key-join-v002-20261104/result.json` (SHA-256 `0fe78dcd0302ee361c5858c4ddb223f7585f7244e5192ce72e0f593402f3dde`) reports 519,318 ordinary samples over six planes, with 519,471 comparisons including recovery; the three full-frame plane services span 3,042,828 simulated cycles (30.42828 ms at the nominal simulated 10 ns period). This is a component simulation result, not hardware FPS or complete-pipeline throughput.
