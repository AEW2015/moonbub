# Local MoonBub lab controller v1

One finite12-frame trial using the pinned `dy71-sequence-v3` sender. This is a control-plane tool, not a six-hour blind loop. No hardware or network execution has been performed while developing this package.

The controller owns the USB serial port and raw log, requires exact USB serial `802C0E7A` and a full64-character installed SDK ELF hash, verifies a nonce-correlated PING before querying `?`, and requires the query's exact ELF match. It configures the local host with a nonce-correlated HOST33 ACK. DTR/RTS are set inactive before opening and never toggled for reset.

Before sending `@` once, it requires fresh reviewed FPGA/camera receipts, a live camera PID, sufficient future coverage, and a live child sender whose printed JSON binds `.33` to `.157:5535`, profile/count12, nonzero session, manifest hash, fresh local timestamps and at least30seconds remaining initial wait. It launches only the caller-pinned local sender/core/manifest. It never talks to `.47`.

The sender begins its existing bounded initial-packet wait while the controller verifies readiness. The tool does not change that sender's wire behavior. After a complete DY45 END, it runs the pinned validator, requires exactly one fresh checksum-valid export and successful12-frame receiver/sender counts. Failure preserves evidence, stops only its own sender child, closes serial and exits. It does not reset, retry or kill unrelated processes. An interrupted/failed export cannot authorize an automatic reboot.

## Install and pure tests

Use a Python environment with `pyserial` installed. The code otherwise uses the standard library.

```powershell
python -m unittest -v test_controller
```

15 pure tests cover one valid arm, refusal of a second arm, stale/expired/dead sender, bad ELF/serial, wrong nonce/action/ACK, missing prerequisite, wrong source/destination/count/profile, source pins and camera freshness/liveness/coverage. These do not establish physical serial/reset behavior.

## Reviewed prerequisites

Create receipts only after independently checking the real hardware/image and camera. Do not generate these blindly from the desired settings.

Program receipt:

```json
{"schema":"moonbub-program-receipt-v1","created_unix_us":0,"verified":true,"device_serial":"802C0E7A","fpga_sha256":"FULL_64_LOWERCASE_SHA256"}
```

Camera marker:

```json
{"schema":"moonbub-camera-ready-v1","created_unix_us":0,"pid":12345,"full_panel_verified":true,"coverage_until_unix_us":0}
```

Both timestamps must be no more than120seconds old by default and cannot be in the future. Camera coverage must extend through the configured run timeout (default180seconds); its local PID must be live. On Windows, liveness uses OpenProcess/GetExitCodeProcess, never `os.kill`. A marker is an operator/reviewer assertion about actual full-panel coverage; PID liveness alone does not prove valid video or successful camera writes. Program receipts are likewise explicit reviewed evidence, not a substitute for root's JTAG verification.

## One explicit local trial

Example argument shape; substitute actual hashes, paths and reviewed fresh receipts. The full sender file, its adjacent `dyn1_sequence_core.py`, manifest and validator are pinned separately. SHA values can be obtained with `Get-FileHash` after checking the intended source commit.

```powershell
python lab_controller.py run `
  --expected-elf FULL_INSTALLED_SDK_ELF_SHA256 `
  --output C:/moon/dev/evidence/UNIQUE-v48-local-trial `
  --sender C:/moon/publish/host/dy71-sequence-v3/sequence_sender.py `
  --sender-sha256 FULL_SENDER_SHA256 --core-sha256 FULL_CORE_SHA256 `
  --manifest C:/moon/publish/host/dy71-sequence-v3/manifest.json `
  --manifest-sha256 FULL_MANIFEST_SHA256 `
  --validator C:/moon/publish/firmware/experiments/V48_PATH/tools/validate_telemetry.py `
  --validator-sha256 FULL_VALIDATOR_SHA256 `
  --program-receipt C:/moon/dev/evidence/fresh-program.json `
  --expected-fpga-sha256 FULL_VERIFIED_BIT_SHA256 `
  --camera-ready C:/moon/dev/evidence/fresh-camera.json
```

Only count12, receiver `.157:5535` and source `.33` are supported. Existing source/fixture validation inside the sender still applies. Outputs must be new unique directories under C:/moon. Source paths are read-only. No firmware installation, FPGA programming, camera start or image inference is hidden in this command; root owns those prerequisites.

Evidence includes serial.raw, argv and exact sender command, stdout/stderr, sender packet log, child PID/start time, arm/session receipt, isolated export.raw, validator output and result/failure. `quiescence.json` is written after the child has stopped, even on a negative completed export. Raw serial is authoritative; export.raw is the ASCII DY45-oriented decoded line subset after arming.

## Explicit separate control actions

Wire commands are `!MBLAB1 <16lowerhexnonce> ACTION\n`. Only a matching `MBLAB1 nonce=... action=... result=OK` authorizes progress. A matching nonce with a refusal/wrong action aborts; unrelated nonces are ignored. ACK means firmware accepted/queued the action, not proof of its later completion.

`ping` is read-only. `reboot` and `dfu` additionally require `--completed-run PATH/TO/quiescence.json` with the same ELF/serial, sender stopped and complete validated export. Their control actions are never called by `run`, including failure paths.

```powershell
python lab_controller.py reboot --expected-elf FULL_SHA `
  --completed-run C:/moon/dev/evidence/PRIOR/quiescence.json `
  --output C:/moon/dev/evidence/UNIQUE-explicit-reboot
```

For reboot, the controller must observe USB disappearance, reenumeration of the same exact serial, a new nonce PING ACK and exact ELF identity. Failure to observe the brief disappearance leaves reboot unverified and stops; no second reset is issued. A software reboot is explicitly not a true rail power cycle and does not prove all peripheral power domains reset. DFU records its ACK and closes; it cannot claim updater accessibility or successful installation. Root must review the one-final-UF2 recovery path before relying on these controls.

There are no automatic whole-run retries, repeated resets or overnight scheduling in this package. Root should reconcile each bounded outcome before deciding the next trial.
