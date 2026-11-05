# CP23 fixed ROM composite source export

This self-contained package captures the exact sealed `cp23-rom-composite-20261105` composition: its fixed CP23 ROM loader, local wrapper and core adapter, frozen full-v006 core/parents, testbench, original 17,412-byte frame, native gold assets, and compact recorded evidence for eight qualified simulation modes. It makes no claim of a complete CP23 decoder or public transport profile.

## Recorded native simulation coverage

| Mode | Preserved run label | Recorded result |
| ---: | --- | --- |
| 0 | `full-native-v001` | Full native oracle: 691,200 canvas pixels, 518,400 canonical samples, 21,120 HUD words, 259,200 physical words, 1,440 line latches; zero misses and underruns. |
| 1 | `load-held-cancel-v003` | Held LOAD cancel. |
| 2 | `physical-held-cancel-v001` | Actual physical burst held cancel. |
| 3 | `reset-load-v002` | Post-start logical reset quarantine with LOAD path. |
| 4 | `reset-physical-v001` | Post-start logical reset quarantine during physical traffic. |
| 5 | `pending-held-cancel-v001` | Pending post-good-retire held cancel. |
| 6 | `prestart-fetch-cancel-v002` | Pre-consumer START / FETCH cancel. |
| 7 | `load-pulse-cancel-v002` | Pulsed LOAD cancel. |

The frozen source also carries additive core-interface proof and parent-source integrity provenance. The supported control is an abstract local start/cancel interface. There is no CSR, network transport, firmware hook, or bitstream. Post-reset runs require reconfiguration; warm memory retention is unqualified. Synthesis/ROM resource gate, board timing, and hardware were not run. These source exports and recorded simulations do not establish board integration.

## Portable replay prerequisites and commands

Prerequisites: Python 3, Icarus Verilog with SystemVerilog 2012 support (`iverilog` and `vvp`), and a new writable evidence directory outside this package. Set `IVERILOG` and `VVP` to tool paths when needed. The helper adds the selected tool directories to the child `PATH` for Windows runtime DLL loading. It verifies the complete package before and after each replay and writes generated files only to the requested evidence directory.

Run these from the package directory, substituting a fresh absolute evidence path for each run:

```powershell
python verify_source.py
python run.py --mode 0 --evidence C:/cp23-rom-mode0
python run.py --mode 1 --evidence C:/cp23-rom-mode1
python run.py --mode 2 --evidence C:/cp23-rom-mode2
python run.py --mode 3 --evidence C:/cp23-rom-mode3
python run.py --mode 4 --evidence C:/cp23-rom-mode4
python run.py --mode 5 --evidence C:/cp23-rom-mode5
python run.py --mode 6 --evidence C:/cp23-rom-mode6
python run.py --mode 7 --evidence C:/cp23-rom-mode7
```

Recorded execution logs/results, commands, and source snapshots for the eight source-bound runs are under `evidence/`. They are retained as executed and may name their original experiment checkout in historical command records. The portable `run.py` compiles only files packaged here, copied into each external run's `inputs/` directory. It does not call the original experiment's helpers or read its checkout. `source-bindings.json`, `provenance/parent-manifest.json`, and `provenance/original-parent-bindings.json` retain the exact source ancestry and hashes.

## Fixture and gold files

`key.cp23.bin` is the exact 17,412-byte CP23 frame; `key.cp23.hex` decodes byte-for-byte to it. `fixture.hex`, `expected.hex`, `column.hex`, `composite.hex`, `hud.hex`, and `quantizers.hex` are the source-bound native simulation inputs and gold assets. The full native result and per-mode summaries remain in `evidence/`; duplicated per-run copies of those assets and simulator executables are excluded.

## Licensing and source notices

Both complete GameBub license texts are preserved byte-for-byte under `licenses/`, along with `licenses/ORIGINAL-NOTICES.md` and the sealed parent's `NOTICE.md`. Their presence does not apply a blanket license to the export. Each file remains governed by its original applicable copyright and license notices; no file is relicensed here.
