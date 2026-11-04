# Portable GM01 section/map simulation export

This source-only export contains the exact RTL, testbench and vector preparation inputs bound by the sealed experiment. `source-snapshot.json` records each original path and SHA-256, the parent sealed manifest digest, and the sealed `vectors.hex` digest expected from regeneration.

The runner stages only the four bound inputs in a temporary directory, applies a guarded one-literal replacement to the staged `prepare_vectors.py` so it uses the explicit native checkout, asks the pinned Python oracle to create vectors there, verifies their SHA-256 against the sealed result, runs Icarus Verilog in that same temporary workspace, checks the actual final pass marker, and removes generated vectors and simulator binaries on exit. The original exported generator remains byte-identical. Logs and `result.json` are written only to the required external `--log-dir`.

## Requirements

- Python with `requirements-oracle.txt` installed (`numpy`, `Pillow`, `av`). The project does not include a Python environment or fixture data.
- The frozen MoonBub oracle checkout at commit `27a4dde6a7e2ea4fab09d892551ef542f05c8965` and a native review checkout containing commit `c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`. Neither checkout is bundled or assumed to be present. The runner requires explicit `--source` and `--native-source` paths, verifies the MoonBub HEAD, and verifies the pinned native Git commit object is available; the native checkout HEAD may differ because the generator reads sources with `git show` at the pinned commit.
- Icarus Verilog `iverilog` and `vvp` on `PATH`, or in a recognized MSYS2 UCRT64/MINGW64 `bin` directory. The runner prepends the selected simulator directory to `PATH` so its DLLs can load.

Example on Windows PowerShell:

```powershell
python .\run_tests.py `
  --source C:\path\to\moonbub-ar03-v20-20261104 `
  --native-source C:\path\to\sunshine-gamebub-dxgi-work `
  --oracle-python C:\path\to\python.exe `
  --log-dir C:\path\to\evidence\gm01-export
```

Omit `--oracle-python` to use the Python running the standard-library harness. The harness passes `-B` and an initially absent temporary `pycache_prefix` to vector preparation. Only the staged generator's single native-repository path literal is overridden; its source-bound behavior and pinned Git object checks remain unchanged. Generated files are temporary and are not part of this export.

## Scope

A pass proves only the recorded GM01 section/header/map/CRC/section-size certificate and map descriptor simulation. CP02 header, coefficient syntax, CP02 CRC, entropy, reconstruction, reference-bank semantics, tags, patches and publication remain downstream. The harness does not synthesize the design or establish resource use, timing closure, hardware readiness, or full-path throughput.
