# v20 development work packages

Use the paired `handoff/gamebub-app-codec-v20-20261103` branches and pin their
commits in your task notes. All prompts below are scoped to implementation work;
no board flashing, boot-device changes or replacement of an installed service is
needed to start. Coordinate source ownership before merging implementations.

## FPGA inverse-transform agent

> Implement the AR03 Q14 inverse module against hardware/gamebub-v20/src/gb_inverse.c
> and its golden-index.json. Keep ZERO/DC bypass and exact sparse GENERAL products,
> both biased-floor rounding boundaries, legal widths and prediction/clipping order.
> Add a valid/ready block interface with block identity, bounded storage and explicit
> abort/reset. Export selected int32 .mem vectors with export_mem.py. Verify all
> retained block classes plus randomized stalls and legal extremes in RTL simulation.
> Report exact vector matches separately from synthesis DSP/LUT/BRAM and timing.
> Preserve the existing JPEG implementation while the AR03 endpoint is developed.

## FPGA entropy, compact-bank and tag agents

> Implement bounded AR03/GM01/SR01/CP02 parsing using the complete packet and
> generated-tile fixtures. Honor every length, CRC, geometry, source-bank/tag and
> stream-finalization check before atomic publication. Reconstructed samples become
> uint8 only after addition/clipping. Feed canonical Y/Cb/Cr raster stripes into
> SHA256, expanding each sample to little-endian int16 and prefixing width/height.
> Test partial tiles, edge padding, stalls, reorder/duplicate/truncate/abort and
> expected-tag mismatch. UI overlays affect display RGB565 only. Map reference and
> display banks explicitly and measure actual arbitration/cache service; include
> parser/control/hash state in resource reports. The Python full-cache planning
> footprint is not an existing mapped implementation.

## ESP32 gateway and control agent

> Add an explicitly negotiated experimental AR03 endpoint. Use wire-contract.json
> and generated gb_wire.h offsets; preserve byte order and total bounds. Implement
> five data permits plus one control mailbox position, true FIFO availability,
> complete-frame grants and exact nonce/slot/body ownership. Keep PC18, FINISHED,
> RELEASE and AF03 meanings separate. Replay the exported FG19 byte sequences and
> negative controller tests. Specify reset/rekey, reconnect and unknown-outcome
> recovery before enabling continuous use. Measure real CRC/copy/DMA/heap/QSPI/RF
> costs; do not substitute remaining-frame allowance for FIFO space.

## Sunshine/native host agent

> Port the mandatory-HUD component and actual candidate/build/admit/commit/discard
> lifecycle using the Python model and 20 isolated packet fixtures. Prepare all
> requested exact RGB565 patch packets first, reserve complete framed bytes, then
> search the bounded declared quantization maps. Never silently omit a mandatory
> patch; reject the whole frame if no profile fits. Preserve candidate source leases
> and body/reference identity until commit or discard. Pay and report losing work,
> quality loss and all wire bytes. Compare decoded outputs against fixture bank
> preconditions. Existing software byte caching does not authorize unsignaled
> receiver HUD-cache reuse. Keep native negotiation and server changes isolated
> until the peer can validate the new profile.

## Integration and performance agent

> Assemble the verified modules through explicit interfaces and run ACCEPTANCE.md
> gates. Start with offline golden packets, then local patterned frames, then a
> calibrated transport, then fresh gameplay. Keep geometry at720×480 coded with
> 720×405 active content. Record unique captures/decodes/presentations, gaps/age,
> full requested HUD coverage, quality, all control costs and fault state. Treat
> 11.376Mb/s as the complex-scene forward-data projection, not measured radio
> capacity. Investigate inline tagging, smaller refill caches and overlap using
> actual packet/stripe traces. Pre-granted capacity leases or receiver HUD reuse
> require new generation/loss/reset proofs; they are not v20 implemented features.
