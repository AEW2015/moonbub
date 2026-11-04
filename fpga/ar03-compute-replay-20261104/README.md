# AR03 offline compute replay export

This source export is derived from the sealed parent manifest SHA-256 `93b61cc6fb05f157554aefa7fa5770a34934e38ab28469d476a5214a858947f6`. `source-snapshot.json` records the full parent manifest, hashes of copied source files, and the selected qualifying timing report metadata.

The scope is the private pre-HUD KEY tag/compute path and its fixture/controller: full decoded YUV sample comparison, final tag, ingress count, result timing, busy rejection, abort recovery, and controller CSR behavior. It covers no HUD, P stage, banks, AF, scanout, network, physical 30 fps, board shell, routing, bitstream, or hardware. The parent OOC setup/hold/internal timing result is not board timing.

## Requirements

- Python 3 standard library only. No virtual environment or Python package installation is needed.
- Icarus Verilog (`iverilog` and `vvp`), including its runtime DLLs. Defaults target `C:\msys64\ucrt64\bin`; override with `--iverilog` and `--vvp` when needed. The runner prepends both binary directories to `PATH`.
- External fixture directory containing `fixture.raw` (raw packet bytes) and `expected.hex` (ASCII byte hex, with LF or CRLF line endings accepted; whitespace is ignored). The runner verifies the raw fixture is 48,203 bytes with SHA-256 `5a39857f436fc50daaa46fc518ab13f9c168fbdadabbe95ef8bf6eeff02c0518`, and expected YUV decodes to 518,400 bytes with logical SHA-256 `cdb3d93c247a8210e32bfa131151b91cf4ad973ed3954f51edbd1dfbd3fda836`. It records the expected file's raw byte count and SHA as well. Fixture and expected data are intentionally absent from this export.

## Replay

```powershell
python .\run_replay.py --fixtures C:\path\to\external-fixtures --evidence-dir C:\path\to\evidence
```

The runner copies the bound RTL/test sources and validated external fixture/expected bytes into a `TemporaryDirectory`, writes Icarus-compatible `fixture.hex` and `expected.hex` there, compiles the full testbench with `-g2012 -s tb_diagnostic`, then runs it. It also compiles `ar03_fixture_diagnostic.sv` plus `tb_controls.sv` (with a temporary `ar03_key_tagged` output stub) under `-g2012 -s tb_controls` for the 20 controller-only checks; that suite does not verify compute functionality. Temporary `.vvp` executables and input files are removed when the runner exits.

`--reuse-diagnostic-evidence DIR` is an optional recovery path for an already executed full replay. It requires the prior compile and simulation logs and checks the exact 518,400-sample PASS marker before reusing them, while rerunning the controller suite. A normal replay omits this option and executes both simulations.

Default evidence output is `replay-evidence/` under this directory. Supply `--evidence-dir` to keep executed logs and `run.json` elsewhere. The source export itself contains no simulation executable, private fixture/expected image, Python environment, or vendor library.

Recreating the original encoded/native fixture from source requires the MoonBub kit at `27a4dde6a7e2ea4fab09d892551ef542f05c8965`, Sunshine at `c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`, and their oracle dependencies. Those repositories are not assumed present. This runner deliberately does not generate the fixture or access the network.
