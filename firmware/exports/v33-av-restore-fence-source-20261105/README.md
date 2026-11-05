# Portable v33 AV restore fence source

This self-contained export contains all 574 inputs declared by the sealed v33 source snapshot, including binary fixtures, assets, fonts, Cargo/ESP-IDF locks and nested files. It also carries the candidate's exact `LICENSE-GPL-V3` and `upstream-README.md` notices under `licenses/`; the README preserves the upstream licensing boundary. No blanket license is asserted for fonts or assets. No application ELF, BIN or UF2 is bundled. The sealed candidate manifest and v32 parent provenance are retained under `provenance/`; they record the original check/release and UF2 validation and are not evidence of a relocated v33 build.

Candidate manifest SHA-256: `9ff2b452aa948dd5e89c4bbe7facb00e6b9bf25236fa36b481f2c6601cb40874`. Selected source snapshot SHA-256: `8e91bc9c2bd063ee1c2e1163dd40e6d3f6baa4250ce7af22cff5796da6655b1c`. Candidate check/release, host SDK suite (83 cases) and production UF2 parser passed. Static shared SRAM is 130812 bytes, unchanged from v32. Physical gates were not run.

The v33 fix intentionally makes the AV worker exit and quarantine after an error restoring radio power-save. Normal NoPS behavior, radio behavior, transport, queue, pacing, and defaults are unchanged. v31 remains the first legacy physical comparison candidate. This does not establish that power-save caused retained sequence losses.

## Dependencies and replay

See `DEPENDENCIES.md` for pinned Rust/ESP-IDF/toolchain and host prerequisites. The export assumes no second GameBub checkout. `verify_source.py` validates every package file and all 574 selected source hashes. `validate_copy.py` makes a fresh isolated copy and runs host-only checks; its evidence must be a new directory outside the export. The optional `build_rev4.ps1` supports preflight/check/build with overlap checks, a short target path, external tool paths, and Git fallback handling. It never runs a device flasher or hardware action.

The copied replay retains the inherited 97 Rust suite tests, 39 model cases, and 24 expected compiler rejections, and updates SDK-host expectation to v33's 83 cases. A relocated target build is not implied by original candidate metadata.

```powershell
python verify_source.py
python validate_copy.py --evidence C:/new-v33-host-replay
./build_rev4.ps1 -PreflightOnly -EvidenceDirectory C:/new-v33-preflight -TargetDirectory C:/mv33src01
```
