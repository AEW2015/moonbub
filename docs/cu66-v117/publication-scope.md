# V117 final publication scope audit

Result: **PASS for the final precommit scope inventory; Root must recheck the staged index**. All five native trials have terminated. This auditor performed no staging, commit, push, deletion, pinned-source change or heavy job.

The current machine-readable review is [publication-scope-final.json](../../experiments/python-gamebub-v117/audit/publication-scope-final.json), SHA-256 `0ff0649c4237f586505577685757072d206110f1b0fd2d2c2806d044393fc8ce`. The earlier [initial](../../experiments/python-gamebub-v117/audit/publication-scope-preliminary.json) and [corrected preliminary](../../experiments/python-gamebub-v117/audit/publication-scope-preliminary-corrected.json) reports remain unchanged historical snapshots.

## Scope and inventory

Publication is limited to `docs/cu66-v117/`, `scripts/cu66-v117/`, `experiments/python-gamebub-v117/` and the existing `fpga/experiments/cu66-v117*` directories. The non-ignored Git inventory contained **2,385 files totaling 502,842,564 bytes** before writing the final audit and refreshing this document. The largest file is a packet-vector fixture at **10,111,467 bytes**, below the conservative 95,000,000-byte threshold. Intentional source snapshots, compressed event/canonical traces and retained failed attempts account for duplication; this audit did not prune evidence.

Both `git diff --name-only` and `git diff --cached --name-only` were empty. Older tracked files remain unchanged and the index is empty. The protected `fpga/experiments/throughput30/burst/marker-recovery/` remains entirely untracked and unstaged: two files outside the publication roots.

The original global `docs/wordbank.md` was authored by the V117 reconstruction agent. Root legitimately relocated it into [wordbank.md](wordbank.md) under `docs/cu66-v117/` and refreshed its unpinned status header. The old global path is absent, and the selected reconstruction proof has no documentation source pin. This documentation-only relocation requires no RTL rebuild. The initial inventory's mistaken description of the document as unrelated is historical and does not define the current scope.

No `.lic`, `.pairing.json`, private-key filename, compiled object/executable, bitstream or DCP filename occurs in the proposed scope. No ELF/PE/Mach-O signatures, symlinks, private-key header within the first 4,096 bytes, or file above 95 decimal MB were found. Expanded gzip starts were also checked for ELF/PE signatures. These are targeted checks, not a comprehensive secret-content scan.

## Provenance and selected evidence

All **27** current orchestration entries reproduce their complete unified diffs exactly from the pinned current original/candidate bytes, including empty diffs for identical files. Their source and diff hashes match. Every entry identifies `current_file_structural_diff`; the manifest explicitly disclaims a historical ancestry claim for evolved Root prototypes. Immutable per-component reversible recipes and actual executed source snapshots remain separate historical provenance.

All **50** path/hash pins in the current results aggregate match. Its **21** selected receipts were checked against current source files and retained artifacts: **812 source-hash checks and 1,558 artifact-hash checks** passed. This includes the preserved failed LIVE evidence as well as successful selected campaigns; the scope audit does not promote a failed test to PASS. Native source origins/snapshots, proof pins, tooling and fixed recipes also match. Relocated documentation is outside those immutable source contracts.

All five native receipts are terminal and retain negative routed setup results:

| Composition | Target | Routed WNS |
| --- | ---: | ---: |
| A | 125 MHz | −1.925 ns |
| B | 125 MHz | −2.202 ns |
| C | 125 MHz | −1.679 ns |
| C | 100 MHz | −0.317 ns |
| B | 100 MHz | −0.100 ns |

Native build directories, DCPs and compiled build objects remain external under `/home/lori/gamebub-build/cu66-v69/`. The publication contains retained text/JSON reports, logs, recipes and source snapshots. There is no clock-qualified positive run or fresh-repeat qualification. Sustained hardware 30 fps, validated hardware decoding under 10 ms, production Sunshine/ESP32 endpoint integration and full-parent routed-clock qualification remain open. Timing evidence comes from actual routing; placement estimates are not signoff.

## Final staging check

The inventory is a precommit snapshot, not a circular self-hash guarantee: this audit, its document refresh and later final audit files legitimately add or update eligible evidence. Root alone stages the explicit V117 roots, checks the final staged names and sizes again, verifies that protected or older unrelated paths are absent, then commits and pushes. No further build is implied by this publication audit.
