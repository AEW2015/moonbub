# `gamebub-recovery-v24`

RS24 header `<4sBBIQQ16s>` contains magic/version/kind, uint32 epoch, two uint64
boot nonces and profile SHA256[:16], followed by a uint32 little-endian CRC.
Messages are exactly 46 bytes. HELLO carries epoch0/target0; subsequent bound
messages require the target nonce and a positive epoch except HELLO_REPLY, which
can advertise an initially empty epoch ledger. All profile parameters are hashed.

`source_sha256` pins the executed scripts and conservative frozen dependencies.
`results.cases` stores every emitted control in hex, kind, direction and delivered
flag, totals including losses, terminal phases and optional actual CP23/JA23 probe
bytes. `reboot_sequence` stores three handshakes and key/full-HUD outputs at
epochs1/2/3. `scope` separates functional agreement from durable/physical/rekey work.
