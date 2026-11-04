# Owned packet storage for the dormant AR03 gateway

This isolated software prerequisite implements the existing gateway `Backend`
trait using five bounded owned datagram buffers. It imports the byte-identical
published receiver core from `host/ar03-receiver-core-20261104`; neither that
export nor sealed v23 firmware is modified. No runtime instance, listener,
production capability, FPGA register map or wire format is added.

The adapter copies all received bytes before returning an owned lease and keeps
the 16-byte TOKEN separate from the GF03 bytes reserved for FIFO ingress. A
reservation also requires a nonzero, unique active ticket from the private
`Fifo` trait. **No real implementation of that trait exists.** Its eventual
hardware implementation must reserve actual FIFO capacity and prove consumer
completion; software free slots, SPI submission success, JPEG credits and
diagnostic snapshots cannot supply those proofs.

Completion binds frame identity, packet identity, opaque buffer ID, lengths and
hardware ticket. `poll_one` derives the gateway's consumed/rejected status from
the matched proof. Retirement must succeed before storage is recycled. Unknown
reservation, completion or retirement retains ownership and stops. Late proofs
never free another owner. There is no force-free/reset/rekey interface.

A private per-lease call budget bounds repeated pending/foreign completion
polls: the default is 64 adapter calls, or an explicit nonzero bound through
`cold_bounded`. Exhaustion stops and retains bytes; it does not fabricate a
receipt. This is **not** a production timeout, a wire-contract addition, or a
wall-clock liveness proof. The future service worker still needs measured
scheduling and a real bounded deadline/recovery policy.

`bytes` exposes only an ordinary immutable Rust borrow. No asynchronous DMA
pointer is given out. A future SPI implementation must finish reading before
that borrow ends or introduce separately reviewed pinned-buffer lifetimes.
The compile-time <=8 KiB storage bound excludes the hardware adapter. This
host-only check is not an ESP32 stack, heap, SRAM or DMA qualification; no
device allocation or application rebuild was performed.

Run with Python and Rust stable:

```powershell
python host/experiments/ar03-owned-backend-20261104/run_tests.py --log-dir path/to/new-evidence
```

The runner checks the frozen receiver-core hashes, runs 20 host tests and three
expected compiler rejections: mutable manager copy, clone and dropping a manager
while packet bytes remain borrowed. Binaries are temporary. Tests use a fake
FIFO contract, not real hardware. The existing GF03-without-grant-nonce replay
counterexample and inactive live gate remain unresolved and unchanged.
