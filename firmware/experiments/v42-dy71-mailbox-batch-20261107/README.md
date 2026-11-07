# V42 DY71 mailbox batching candidate

V41/V023 completed the original network KEY/P pair with matching Windows presentation replies. Its scalar total was58.043306s; HUD writes/readback consumed49.982510s. V42 is the next controlled firmware-only comparison, not a new FPGA or bulk HUD endpoint.

## Change

- Consecutive changed mailbox metadata fields share a bounded incrementing QSPI write (at most12words).
- Sequence and opcode are submitted in one ordered2-word QSPI write.
- ACK sequence, status and data are retrieved in one3-word QSPI read. Status/data are interpreted only after matching the submitted sequence; old ACK snapshots are ignored and future ACKs fail closed.
- Existing command-idle check, deadlines, full generation/frame/tag identities, per-word completed HUD writes, actual SDRAM readback equality, native semantic ACK and actual presentation checks remain. Unknown/partial I/O errors are not retried as successful commands and retain/quarantine ownership.
- Target adapter records actual QSPI transaction attempts separately from register-word read/write counts.

V023 BIT5535056e... stays unchanged. No FPGA rebuild, clock change, network format, native allocation budget, worker stack, source fixture or Windows uploader change. This is mailbox batching; each HUD memory word still has its own checked command.

## Offline gates

Host suites exercise actual native HU decode with scalar fallback and batched bus adapters, plus full KEY/P readback and failure cases. Exact selected V023 QSPI endpoint and CDC RTL pass12-word metadata,2-word submission and3-word reply bursts:32commands/448writes per run, two relative phases and8/16MHz. A changed-wire-data negative control fails as expected. The pin backend is a synthetic ordered CSR mailbox, not a complete decoder/SDRAM simulation. Source bindings and executed commands are in evidence/pin-sim. No physical V42 result is established by those tests.

## Next physical test

1. Preserve exact V41 rollback; app-only V42 update after the operator enters usable USB update mode. Confirm ELF, variant and CPU-only HU probe after boot. Preserve SD/settings/partitions.
2. Reload the same verified V023 via volatile JTAG only after the old lease has been cleared by the power cycle. Keep its routed source/image gates unchanged.
3. Start the same cbbd85fda Windows uploader with the original KEY/P and `--initial-wait-seconds 600` before arming. Confirm its printed live source/session. Only then arm USB~ and verify .157:5535/.47 and physical SRAM admission. Retain USB evidence and capture the final held image.
4. Require2actual accepted/presented,0rejects/underruns,42240written/verified HUD words, both matching status2 replies, no reboot/panic and retained endpoint/lease. Preserve all errors; no automatic whole-run retry or force release.
5. Compare measured HUD write/readback intervals and actual transaction count against V41; report source-wait/network time separately. V41 scalar reads381957+writes296074 correspond to678031 single-register QSPI attempts. Do not infer an isolated bus bandwidth or FPS from command counts.

Even a successful batching improvement is not an interactive/30fps result. Native HU CPU in V41 was303841/210627us per frame, already above a30fps frame budget. Further work includes true bulk HUD streaming/readback and native HU service optimization, continuous ownership/session handling and a live host encoder. Keep these gates separate from this pair test.
