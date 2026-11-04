# AR03 receiver-core source export

This is a source-only offline export of four dormant Rust production modules, two host test harnesses, and seven typed fixture files from sealed `v23-ar03-gateway-20261104`. It is not a full firmware distribution, a live endpoint, or a runnable receiver service. `source-snapshot.json` binds each copied source/fixture file to its original v23-relative path and SHA-256, and records source inventory digest `d904373e006126480d3de5c9d2711e459a614b0ed04de1dcc2b83b602243f36d`.

The module retains the v23 inactive gate: no live profile is advertised and authorization always denies activation. The known lab-profile gap remains: a delayed never-observed GF03 packet can rebind after frame ID/body/length reuse because TOKEN/GF03 carries no FG19 grant nonce. There is no real backend/FIFO/DMA implementation, AF03 publication, or production reset/rekey/unknown-outcome recovery. Do not enable it as a live receiver.

The export includes the FG19 retained history fixtures and typed GF03/PC18/QC18 examples plus the shared 10-case/51-step model transcript. Transcript drain events are scripted model inputs, not physical drain evidence. Host tests do not prove a full sender, network endpoint, or physical DMA behavior.

## Run the export checks

Python standard library and Rust stable are required. Binaries are placed in a temporary directory and removed after execution; no binary artifacts are written into this export.

```powershell
python run_tests.py --log-dir C:/path/to/evidence/ar03-receiver-core
```

The runner verifies the copied-file and fixture hashes, executes 22 gateway-core and 10 transcript tests, and checks that `Frames` and `Gateway` reject Copy/Clone use with the expected compiler diagnostics. No firmware dependencies, SDK, release image, or complete parent tree is included.
