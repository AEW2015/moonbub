# V31 ESP32 trace candidate for coordinated testing

Installed control remains **v30 / build50 / overlap / 32 slots**. Nothing in this handoff installs an image or starts a sender. V31 changes diagnostic work only; it is not a confirmed packet-loss fix or a 30fps result.

## Candidate and portable sources

The self-contained package is `firmware/exports/v31-trace-lock-scope-source-20261105`. Its manifest SHA-256 is `5aac54272fcfd15f7d440dc58c669620626d37243da46d2d2b6d162960ce0607`:602 included files, all568 selected source/test/tool inputs, original app-only UF2, assets, locks and licenses. No other GameBub repository is assumed present. External esp193/ESP-IDF5.4.3, Cargo caches and managed component prerequisites are specified in its DEPENDENCIES.md.

| Artifact | SHA-256 |
|---|---|
| Candidate source snapshot | `5cc486e7d90188bb2c6400b03cf65e716da94a3e5d6164957740c6aa844137de` |
| Full local candidate manifest | `850f8a31e5e597e6e9e4b69d30d1d776f5f076c9bab2556ec8782dbe05515942` |
| Original ELF, retained locally | `7c76ae8fa4e8e3fef2e79f53f58b88416ae2f2e8aa49d7399ca540a192ebaa4f` |
| Original application BIN, retained locally | `29dcd8e213888e0e4fd3f6c06d15a9ebef7aea893ff645ccc87982a49e571970` |
| Included app-only UF2 | `380bf1c894744cc38e3b7988c8d1aaa4c10faefd499cca937eb27548a639024b` |

## Change and evidence

Packet recording no longer collects/copies the16 full64-bit phase maxima inside its mutex. It reads ten context words plus version checks; summaries/manual seal still collect full maxima. Eight per-kind rejected diagnostic-call counters add32 bytes. These count lost diagnostic calls, not network packets or identities.

USB trace schema is v2:33 summary pages (the original25 shapes plus eight loss-kind pages), with versioned event/failure pages. The included collector accepts preserved v1 exports and rejects mixed/unknown schemas, missing pages and inconsistent valid loss totals. Use the matching collector after STOP, not the old v30 collector against v31.

Executed original target check/release passed with locked/offline rev4 inputs. A review-stopped first source attempt and a later external Python-version-probe failure are retained; the corrected successful retry and release bind identical inputs. SDKconfig/generated bindings match v30. Production UF2 parser checks all12,538 blocks and application-only addresses.

Actual static shared SRAM130,436 bytes (+32); Trace object8,272 bytes (+32). Individual Trace.record frame320 to192 bytes; summary page816 to896 bytes. These are ELF observations, not a whole-call-chain stack bound or measured physical latency. Stacks, queues, radio/AV behavior, streaming wire and FPGA remain unchanged.

Portable regressions: core31, USB6, protocol22, budget5, collector16, model39, SDK-host66 and24 expected rejections passed. Three saved v1 exports validate with the new collector. Fresh-copy replay verifies all files,125 embedded asset references and four locked metadata/path checks. Portable target rebuild is a separate gate; consult later replay evidence rather than inferring it from host tests. Physical v31 testing is **NOT_RUN**.

## Proposed next hardware gate

After coordinated installation and fresh identity verification, repeat only the retained unchanged-pacing Xonotic baseline:720x480,20fps,4Mbps,Q25,offsetzero, input-only AV, audio/injectionoff, build50/overlap/32 slots unchanged. Reserve new frame IDs2014200 or higher. Keep Windows baseline waiting behavior; do not combine the first v31 measurement with the host spin-tail candidate.

Capture outbound UDP for the whole run through STOP and report capture point/drop counts. Independently verify camera coverage, starting/final receiver counters, v2 trace/loss-kind counts, heap/stack minima, core counters and power-save restoration. Compare observed trace loss and delivery; do not assume the smaller recording path fixes the unlocalized Sequence failures. No run is scheduled by this document.

Custom CP23/HC22/HD22 remains a separate offline development path. V31/build50 do not implement a custom network decoder or allocate a custom port.
