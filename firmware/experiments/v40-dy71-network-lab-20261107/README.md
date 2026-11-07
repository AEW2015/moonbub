# V40 DY71 network lab

Development receiver and reference uploader for the custom CU66/DY71 path. This is the first two-frame network bring-up gate, not an interactive streaming release.

- [Sender contract and hardware procedure](docs/SUNSHINE-DY71-NETWORK-LAB-v1.md)
- [Offline qualification](evidence/QUALIFICATION.json)
- [Reference uploader](tools/dy71_fixture_sender.py)

The isolated application compiles for Game Bub Rev4 / ESP32-S3 with the exact effective V39 SDK configuration. Production DFU parser and static SRAM guard pass. The V40 ELF SHA-256 is `925c4c026242336e9dd5a3bce501fe8ba216ff08c7cc4b6d06ec537aad4d3f59`; app-only UF2 SHA-256 is `46870990aac9f0e37dd0729329171d416cc315cf82e0ee70f08d6b9c1f191739`. Neither is installed. Executable artifacts are kept in the local release folder, not this source handoff.

Tests: preserved local native-endpoint suite 18; network driver suite 13; UDP/native integration suite 19; wire suite 6; Python sender suite 3. Suites overlap; these counts are not additive distinct-case coverage. Actual localhost UDP and actual native C++ HU decode are exercised against a software CSR model, not physical FPGA/network results. Runtime Wi-Fi/heap/stack admission remains unmeasured.

The original fixture bytes are unchanged from the Windows-qualified KEY/P pair. No live CU66 encoder exists in the reported Windows commit `15ca3422`; the sender can first use these retained fixtures. DYN1 is a proposed lab contract, separate from production negotiation and the prior JPEG/MSV1 path.

Reproducible local commands are in `run-host.py`, `build-local.py` and `package-local.py`; these use the recorded Windows installation paths and short target cache, so inspect/adapt those paths before running elsewhere. Build and packaging scripts never flash or program hardware.

The current V023 scalar HUD transfer/readback is intentionally preserved. Two diagnostic frames previously took about 54 seconds including scalar service. Interactive video next needs measured bulk HUD transport and continuous session/owner handling, plus a live host encoder; passing the network fixture is not a 30fps result.
