# DY71 direct YUV integration profile

Root approved this isolated profile on 2026-11-06: magic/USERID/USR_ACCESS `0x44593731` (`DY71`), ABI `0x00010000`, local capabilities `0x0f`. No board image, CSR mapping, network offer or ESP32 compatibility is implied. Existing v35 must reject its different identity. Any firmware adapter needs a separate review.

The canonical physical layout is tile-major64: one 8x8 tile is 64 row-major bytes in four full BL8 commands. Logical plane/bank/index APIs, entropy bytes and canonical SHA row order stay unchanged. Two display slots mean cache contexts, never RGB framebuffer allocations. No RGB write/read traffic is part of this profile.

The isolated receiver derives from the frozen timing-v001 owner and preserves its packet/base/tag checks, canonical reference/front leases, software COMMIT retry and irreversible COMMIT point. Painter readiness is replaced by an explicitly named cache PREPARE contract.

```text
packet/base decode + canonical tag + actual canonical writes
processor HUD tag + 21120 completed HUD writes
                  |
             non-LCD drain
                  |
PREPARE(generation, frame, canonical bank, HUD bank, free cache slot)
                  |
3600 initial BL8 reads + cache writes + owned DMA drain
                  |
matching prepared result -> COMMIT_READY
                  |
irreversible root COMMIT + retriable software COMMIT acknowledgment
                  |
matching READY descriptor -> display PENDING (not cancellable)
                  |
vblank + line/pixel/memory scanout drain
                  |
identity-qualified presented pulse -> new FRONT, old FRONT lease release
```

Pre-COMMIT abort retains generation/frame/slot identity and waits for the direct owner's real cancellation/drain acknowledgment before reporting the cache worker drained. A successful PREPARE is not presentation and does not release memory. After irreversible COMMIT, missing software ACK cannot roll back the cache or canonical/HUD state. Runtime FRONT refill DMA belongs to the display lease and is excluded from per-frame non-LCD drain.

The BL8 physical response has no generation echo. The selected memory and DMA contract must prevent a late successful response after acknowledged abort drain. Reset recovery coordinates receiver, memory, owner and pixel domains. Pixel-only reset is unsupported.

The frozen direct owner uses a 32-bit internal DMA cookie and deliberately fails closed before wrap. At approximately 2.1 million commands/s it could exhaust in roughly half an hour. Short native fixtures do not qualify an overnight or unbounded session. A separately verified wider-cookie successor or a coordinated owner/backend/pixel reset policy is required before long-duration release.

Initial integration uses `direct-display/frozen-port-contract-v001.json` unchanged. That component has functional native/pin-model evidence but its full-owner 100 MHz synthesis setup is negative; no DY71 board build is ready. Complete KEY/P canonical/HUD verification, actual LCD pixel scoring, concurrency/failure tests, fit, routed setup/hold and bundled CDC checks remain required.
