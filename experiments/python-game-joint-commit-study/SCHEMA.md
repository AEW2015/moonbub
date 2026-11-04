# V22 joint transaction API and laboratory bytes

## Pair and ACK grammar

The forward packet preserves the frozen CB21 serialized container. Its 53-byte
little-endian header is `<4sBIIII16s16s>`: magic/version, epoch, frame, AR03 length,
HC21 length, base digest and HUD digest. Valid patch-free AR03 and valid HC21
follow, then CRC32. The complete admitted pair is at most 49,152 bytes, including
57 bytes of CB21 binding. CB21's historical offline-format name does not imply
installed endpoint support; v22 adds only Python transaction semantics.

JA22 header `<4sBII16sHH>` fields are magic `JA22`, version1, epoch, frame,
SHA256[:16] of the complete forward pair, AF03 length43, HA21 length54. It is
followed by those exact complete ACK packets and a final CRC32. JA22 is134 bytes
before any IP/UDP/transport framing. CRC/hash consistency is not authentication.

`parse_ack` checks length, CRC, version, bounded identity and matching inner epoch/
frame. Sender acceptance additionally requires byte equality with the outstanding
pair's expected complete ACK before applying both permissions privately.

## Python owned records

`Candidate`: private owner token, frame ID, complete packet or `None`, JSON
diagnostics. A retained accepted candidate has a private record binding exact
object/packet/frame/config, base candidate/source lease, private HUD state and
pre-build semantic snapshot. It can be committed/discarded once. Failure consumes
actual work but no issued identity or cache publication.

`ReceiveCandidate`: owner, frame, packet, read-only private full display and YUV
planes, diagnostics. The private record binds state version and visible component
semantics, decoded endpoint forks, exact JA22, source lease, destination slots,
deadline and an initially false write-drained flag. Fence and vblank are explicit
caller-supplied model events. Presentation swaps only a completely validated
matching epoch after rechecking current readers. Abort drops all private work and
releases only this candidate's source lease.

`snapshot()` is JSON-compatible identity/ownership evidence, excluding accumulated
work counters and the speculative legacy memo cache. Receiver
`published_snapshot()` omits source-reader bookkeeping so that a live private
decode lease does not look like visible publication. Neither snapshot measures
actual bus traffic, memory fences, target heap, cycle timing or physical FPS.

The parent `results.json` schema and verifier document campaigns, source pins,
retained packets, quality controls and exact-array evidence separately.
