# CE-factor KEY/P replay with witnessed SDRAM poison

This is a separate, approved functional gate and has passed; see REPORT.md and result.json. The zero-initialized CE control is unchanged and already passed. Exact V55 Rust/native, original KEY/P packets and independent known-front canonical/raster/HUD goldens are the same as that control. The selected production RTL remains the same pinned CE-factor receiver; the only additional change is an initial fill in the test SDRAM model array.

For each word address, the model computes m=((address*0x045D9F3B) modulo 2^32) xor 0xD14C5EED, then word=(lo16(m) xor hi16(m)) or 0x0101. Both bytes are nonzero. This is address-dependent deterministic poison, not a four-state unknown-memory model. It executes before the first clock without changing control registers, real SDRAM init commands, reset, clocks or timing parameters.

The same initial block asserts evaluated MEM_WORDS=16,777,216 and actual memory samples first=8fa1, second=15c7, last=d9c7, then prints STB1_POISON_FILLED. The final end gate requires exactly that runtime witness. The Verilator stdout stream is redirected away from binary RPC; buffered display text may only be flushed at process completion. Actual sample assertions must pass before any model transaction proceeds. No marker is accepted merely from the source text.

Model SHA-256 is 5af3451e4ab30cc8c3a81e8d1054eb922b27fa8fbdcf6a93ae642cc133ae3468. proposal-before-runtime-witness.json preserves the earlier reviewed version; proposal.json, model-only.diff and prelaunch-binding.json bind the final witness-qualified version. Root explicitly approved this exact initial-only extension. No Vivado or hardware operation is performed.

The comparison ignores unowned banks and checks only independently known presented front data. It does not force bank 2 selection. The old pair is HX33 only; no new-video12/HU25, stale/error injection, recovery or app failure-hook coverage is inherited. Every other uninitialized two-state model array retains its original behavior; only SDRAM contents are poisoned.

Timing remains deliberately modeled: eight 100 MHz cycles per direct CSR access, 100 us per modeled yield and 200 ms explicit Prepare service. Native callback CPU virtual time is zero. Accelerated powerup 20 and refresh 750, AC/OH 2.223 ns and clock flight 0.757 ns remain unchanged. No physical QSPI/CPU/FPS, target heap/reserve/stack, SDK/radio/DMA or SDF claim follows from this run. The runtime/source/golden end checks passed.
