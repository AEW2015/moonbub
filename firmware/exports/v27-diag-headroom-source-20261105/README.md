# v27 diagnostic headroom: portable source export

This package contains all **558 active inputs**, byte-for-byte, from the sealed
`v27-diag-headroom-20261105` candidate. It includes the complete handheld source,
assets, Cargo locks, SDK defaults/component lock, host harnesses, production UF2
parser and licenses. No existing GameBub checkout is required. Every packaged
file is listed in the top-level manifest, including zero-byte files, duplicate
content at distinct paths and every nested manifest. Only the top-level
manifest itself is excluded from its file list.

The candidate manifest SHA256 is
`eff2da64de4fcf8757530d663bfad224cc6f3f8631944d5bc25aef5468de1b0e`.
Source changes remain the two 6144-byte diagnostic stack declarations, v27
diagnostic identity and corresponding test expectations. Receiver, device,
LCD/settings defaults, ports, queues, priorities, AV and wire sources are copied
unchanged. There is no export-specific firmware patch.

## Check a fresh copy

From the repository or extracted package, use a new external evidence directory:

```powershell
python ./verify_source.py
python ./validate_copy.py --evidence C:/v27-export-review-01
```

`validate_copy.py` verifies the original, copies it into
`C:/v27-export-review-01/source-copy`, and runs integrity, embedded-file/path,
39-model/66-SDK/24-expected-rejection host and four locked Cargo metadata checks.
All output goes **outside** that copied source, under the evidence directory.
Both original and copy remain manifest-valid. Optional `--cargo`/`--rustc`
arguments select host tools. A failure is retained; use a new evidence directory
for a retry. The existing fake-device test has a two-second wall-clock wait;
the candidate's initial failure and unchanged successful retry are recorded in
its full local evidence, not changed or hidden by this export.

Each individual checker also requires `--evidence` pointing to a new external
directory. Do not put output, caches, `.git`, or additional files inside the
source export. Integrity verification rejects unbound files. These checks use
fake SDK/host layouts and do not establish ESP ABI, stack margin or delivery.

## Rebuild without programming

Install the exact external tools/caches listed in [DEPENDENCIES.md](DEPENDENCIES.md).
The portable Windows launcher checks source integrity, the esp193 compiler
revision and IDF5.4.3 before compilation. Git must be installed; the unchanged
build.rs runs Git and uses its selected snapshot fallback when discovery fails.
The launcher limits discovery at this package root and verifies that behavior.

```powershell
./build_rev4.ps1 -PreflightOnly -EvidenceDirectory C:/v27-preflight-01 -TargetDirectory C:/v27src01
./build_rev4.ps1 -Action build -EvidenceDirectory C:/v27-build-01 -TargetDirectory C:/v27src01
```

Use fresh paths; preflight does not create the target or perform compilation.
The build command uses `cargo +esp193 build --offline --locked --release
--features rev4`. All targets/logs stay external. `-Action check` is also
supported with its own new paths. A future rebuild may embed a new SDK date/time
and is not assumed to reproduce the supplied image hash. Source `espflash.toml`
is preserved, but this launcher never invokes a device runner or flashing tool.

## Supplied image and inherited evidence

`images/moonshine-rev4.uf2` is the original application-only Rev4 image, not
regenerated during export:

| Image | SHA256 | Included |
| --- | --- | --- |
| UF2 | `9c96bdbbb0b1e7e9157ed6b951765615d4747277d37f73f4016422cdba5b04a3` | Yes |
| ELF | `5cdf81d4e853172a8f7d610f035438675c1d7b65687b0ccea41adb8cdb5ffdd2` | No |
| Application BIN | `9b93ece6c768f1191fbaa9e762b477c47b37500cd21bd0bfcf74159e14e57834` | No |

ELF/BIN, SDK/target caches and redundant build output remain in the original
candidate. Small `.bin` files within the 558 selected inputs (the declared
bootloader source input and test fixtures) are required source/test assets,
not the omitted application BIN. They remain byte-identical.

`provenance/` contains compact **inherited** executed target-check/release,
SDK/ABI/memory, host, parser, image identity and frame-review records. The copied
candidate build manifest references its original full artifact set; it is
historical provenance, not this package's integrity manifest. This export's
own manifest binds only files actually included. Original target check/build
passed with esp193/IDF5.4.3, static SRAM122124 bytes, both stacks6144 and production
parser12419-block validation. Dynamic stack increase is2048 persistent USB bytes
plus2048 while KeyDiag lives; ELF static SRAM excludes those allocations and
runtime overhead. No target build or image conversion was rerun for packaging.

Physical results and installation decisions belong to the root hardware report,
not the inherited offline NOT_RUN fields. Larger stacks do not close the loaded
diagnostic-delivery gate. Selected diagnostic byte captures are not complete
UART capture; external hold, actual heap/stack margins, network loss and genuine
mid-compute cancellation retain their existing limits. Preparing or validating
this source package does not access hardware or change device/settings state.
