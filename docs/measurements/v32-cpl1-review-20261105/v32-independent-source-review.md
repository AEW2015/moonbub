# V32 independent source review

Reviewer: root; 2026-11-05. Scope: offline read-only CPL1 observer and the frozen CSR draft, not device identity or electrical validation.

Reviewed `handheld/src/cpl1.rs` and `cpl1_usb.rs` against `fpga/candidates/cp23-local-rom-20261105/CSR-DRAFT.md` after the candidate was sealed. No candidate source was changed.

- Identification requires CPL1/schema/CAPS=0/image, with no fallback to JPEG or AKD1 semantics.
- The single capture write is `0xe0000500`; it does not address decoder START, reset, cancellation or timing controls. Reads use the existing read profile; capture explicitly requests that same bounded clock.
- Fresh nonzero cookies are allocated for the ESP32 boot lifetime, independently of FPGA reset. Generation must advance; exhaustion, changed identities, cookies, generations and program epoch reject the query. Cross-ESP32-boot continuity is explicitly unsupported.
- Every four-word read group checks identity and cookie/generation before and after. The complete40-word group is validated for reserved bits, quarantine, both PLL locks and digest/count consistency. Flag12 in the current draft is included in the rejected exhaustion mask; reserved words598/59c must be zero.
- SDK adapter checks elapsed deadline after blocking I/O as well as before a step. A single driver transaction still lacks a proved worst-case execution bound; this is not a hard real-time SPI proof.
- Cached pages retain cookie/generation and raw numeric values. The expected CRC is documentation only; it is not substituted into actual status. Repeated canvases do not establish unique frame rate.
- Coordinator permission is released on success, error, timeout and quiet-state loss. Page formatting occurs after the state lock is dropped. Existing streaming settings and transport behavior are unchanged.

Source review outcome: no additional blocker found in this scope. Target build, host cases, UF2 validation and SRAM evidence are recorded separately in the sealed candidate. Whole-task stack/heap safety, live CPL1 query, real QSPI read integrity, LCD behavior, routed board gates and any physical throughput remain unverified. The current board shell is a separate, unfinished candidate.
