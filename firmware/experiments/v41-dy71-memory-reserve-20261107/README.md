# V41 DY71 physical memory reserve

V40 installed successfully, connected to192.168.0.157, then refused its140000-byte startup guard with118116free/largest37888. No FPGA writes or network payload transmission occurred. V023 remains unchanged.

V41 keeps the exact DYN1 lab wire, original KEY/P fixtures, port5535,16KiB worker stack and scalar checked HUD transfer. The Windows uploader at5e4013ec remains compatible. It replaces the unmeasured140000-byte threshold with114688 and a98304-byte native arena, plus real internal-free-heap checks before every native allocation against8192reserve. Allocation failures return through the existing semantic exception handler and prevent successful drain/commit. The arena peak for the actual pair was92235bytes in the physical CPU probe; allocator overhead and concurrent Wi-Fi are separately subject to the physical reserve check, not assumed covered by logical accounting.

Host tests pass the exact smaller arena and a forced insufficient-physical-heap negative case. Runtime memory/stack and network fixtures remain pending installation. V41 now has its own human-readable diagnostic variant label; exact ELF identity remains authoritative.

See[the unchanged lab transport](docs/SUNSHINE-DY71-NETWORK-LAB-v1.md). This is a two-frame correctness test, not interactive/30fps streaming. No FPGA rebuild, JPEG/AV tuning or persistent settings changes accompany this app update.

The initial target build failed with `Undefined temporary symbol` after introducing an atomic minimum diagnostic. The retry uses exclusive-worker load/store sampling and preserves the failed build evidence. Runtime reserve behavior and wire semantics are unchanged by that diagnostic adjustment.
