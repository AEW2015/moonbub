# Portable v31 trace lock-scope source

This package contains all568 selected source/test/tool paths, complete handheld assets, Cargo locks, SDK defaults, licenses, meaningful host harnesses and the original unprogrammed v31 app-only UF2. There is no requirement for another GameBub checkout. External compiler/IDF/Cargo/component prerequisites are listed in DEPENDENCIES.md. No SDK cache, target directory, ELF, application BIN, local_credentials file or firmware flashing tool is bundled. The declared handheld/bootloader.bin source input remains because espflash.toml references it; the provided build/packaging helpers never flash it.

Selected candidate: `v31-trace-lock-scope-20261105`. Parent candidate manifest SHA256850f8a31e5e597e6e9e4b69d30d1d776f5f076c9bab2556ec8782dbe05515942; selected source snapshot5cc486e7d90188bb2c6400b03cf65e716da94a3e5d6164957740c6aa844137de. These are retained under provenance. The package's own manifest verifies ONLY included files plus every selected source path; it does not require omitted candidate artifacts to exist. Nested manifest.json and empty files are included and individually bound. Only the top-level self-manifest is excluded from its own file table.

## Behavior and inherited executed evidence

The trace's packet-context snapshot excludes the16 full64 phase maxima. Packet recording reads ten payload words/two version checks rather than additionally reading32 maximum words/copying128B under the mutex. Full64 maxima remain collected for summaries/manual seal. Eight bounded per-Kind loss counters add32B; these identify rejected diagnostic call kinds, not lost network packets or a specific missing Complete. No loss journal or capture timestamp extension is added. Sequence-only first-trigger96-record ring/16postevents, failure tails, manual seal/arm fences, protocol/wire/queues, power-save, SDK defaults and other behavior remain v30-equivalent.

USB trace schema v2 uses33 summary pages: existing25 shapes plus pages25..32(kind,lost,loss_valid). Event/failure page shapes remain unchanged, versioned v2. `tools/collect_gamebub_trace.py` accepts v1/v2 and rejects unknown/mixed versions, missing pages and inconsistent valid loss totals. It uses the existing recorder's query interface only when deliberately run against hardware by its owner. This export's validation imports parser functions without calling its live main. The published v30 collector/installed firmware are untouched.

The candidate's executed target check/release used esp193/IDF5.4.3 and locked/offline rev4 sources. Check passed6m07s through a named tool-only retry; release passed1m31s. A prior source-review stop and an external Python-version-probe failure are explicitly preserved in provenance; no PASS is inherited from those failed stages. The corrected application inputs remained identical throughout successful check/release. Generated SDKconfig/bindings matched sealedv30. The package's new portable build launcher has NOT executed another target build; it is a clean rebuild path for these same sources, not a claim of an executed relocated target build. Future builds may embed new SDK dates/times and need not reproduce image hashes byte-for-byte.

Inherited measurements: actual ESP Trace object8,272B(+32), whole static shared SRAM130,436B(+32vs v30); task stacks USB6144, KeyDiag6144, AV8192 unchanged. Actual entry frames: Trace::record320?192B, new context_snapshot80B versus old combined352B, maxima_snapshot176B(summary-only); USB summary_page816?896B. Individual frames/inlining changes do not establish closed stack bounds or reduced physical latency. Host/fake SDK tests are not ESP ABI/performance evidence. No v31 physical stack/heap/trace-loss/delivery measurement exists.

Original images: supplied UF2 SHA256380bf1c894744cc38e3b7988c8d1aaa4c10faefd499cca937eb27548a639024b (12,538 blocks); omitted ELF7c76ae8fa4e8e3fef2e79f53f58b88416ae2f2e8aa49d7399ca540a192ebaa4f; omitted application BIN29dcd8e213888e0e4fd3f6c06d15a9ebef7aea893ff645ccc87982a49e571970. Full originals remain local in the sealed candidate. Production updater parser verified every supplied UF2 block/application address/Rev4 identity and binary round trip. This package has not been programmed. Installedv30/build50 and receiver/device settings remain unchanged.

## Verify and replay safely

```
python verify_source.py
python validate_copy.py --evidence C:/v31-replay-new
```

Use a NEW external evidence directory. validate_copy copies the entire package first, verifies all568 inputs/all included files, then runs core31/USB6/protocol22/budget5/collector16 plus model39/SDK-host66/24 expected rejections, local embedded-asset checks and four locked/offline metadata/path checks. Outputs remain outside both packages. It does not build a target, open a device or invoke collector main. Both original/copy manifests must remain valid afterward. Do not write test outputs into the bound package. All zero-byte and duplicate-content paths count separately.

## Authoritative clean rebuild path (not executed here)

```
./build_rev4.ps1 -EvidenceDirectory C:/v31-preflight-new -TargetDirectory C:/v31src01 -PreflightOnly
./build_rev4.ps1 -Action build -EvidenceDirectory C:/v31-build-new -TargetDirectory C:/v31src01
```

Paths must be fresh, short, external and user-owned. Preflight does not create a target. The helper verifies the complete source package, exact compiler/IDF versions and selected unchanged build.rs Git fallback via a repository-discovery ceiling. It invokes only cargo check/build, never cargo run or the configured espflash runner. Outputs live under the chosen target/evidence directories. Rust esp193, IDF5.4.3, tools, Cargo registry/Git caches and Espressif managed components are external prerequisites; no silent repository path dependency is assumed. Initial cache installation may need network access. The helper deliberately uses offline/locked dependencies once installed. See DEPENDENCIES.md for exact selected versions/hashes.

No publication, image selection or physical regression is performed by these helpers. The hardware owner must separately review identity, source/stack/SRAM and matching collector, then authorize any installation and controlled same-source comparison. No FPGA or radio/queue change is part of this candidate.
