# V91l C2 validation and publication partition

`cs88_validate_publish_v91l` implements the actual CS88 C2 content tree and
frame seal with the unchanged `cu66_sha256_bytes` RTL, then controls the
unchanged three-bank ownership module. It consumes tile-ordered canonical
bytes replayed from qualified candidate memories and semantic HUD bytes
produced by the frozen native C++ HUD decoder. This is a heterogeneous
validation partition; it is not a complete RTL HUD decoder, overlay engine,
canonical-producer join, external DMA controller or display implementation.

## Actual hash work

The fixed C2 context is SHA256 of the normative sorted profile JSON for
720×480, granularity 16 and `CU66-V82-CONTENT-SHA256-TREE-2`. The root has:

- 508 actual leaves over consecutive groups of at most 16 native 8×8 tiles,
  in Y/Cb/Cr plane order;
- four domain-separated empty leaves to fill a 512-leaf tree;
- 511 domain-separated internal hashes, with exact level and node index;
- a separate SHA256 of 42,240 actual decoded semantic HUD bytes;
- a 157-byte domain-separated seal binding frame/reference IDs, key flag,
  generation, prior accepted root, computed HUD digest and computed root.

All 1,025 messages run through the real frozen RTL SHA engine. Nominal work is
628,815 message bytes and 10,298 SHA blocks. Node storage is 1,024×256 bits,
32,768 logical bytes including unused node zero, plus SHA buffers, registered
child digests, metadata and control. This is not inferred RAM or routed fit.
Child digests are captured before parent-message consumption. Roots and seals
compare against the original CS88 header commitments at bytes 52–83 and 84–115.

The canonical stream checks epoch, plane, native tile, byte index, exact count
and final marker. The semantic HUD stream checks epoch, frame/reference IDs,
generation, count and final marker. A bound software-verified HUD receipt must
exist before HUD hashing. The actual transferred HUD digest must match that
receipt, and the frame seal independently binds the computed digest.

## Software HUD endpoint

The C++ bench invokes the unchanged `cu66::decode_hud` on actual extracted
HU25/HX32/HX33 bytes, with the previously accepted decoded HUD as prediction.
This performs original framing/CRC, identity, prior/output tags, component
syntax, range and patch reconstruction checks. The resulting words drive the
semantic byte stream and receipt. Independent expected HUD words are comparison
only; they do not replace decoding or synthesize a successful receipt.

Accepted software HUD state advances only after the RTL atomic commit. Invalid
HUD CRC is rejected before candidate preparation. Mutated receipt identity,
unverified receipt status, changed semantic bytes and wrong stream owners are
separate negative cases. The software decoder's CPU time is not modeled as
FPGA cycles or ESP32 performance.

## Atomic ownership and reset

The three-bank controller distinguishes candidate writer, accepted reference,
pending presentation and current front leases. New candidates cannot overwrite
accepted/front/pending banks. Commit requires all canonical/HUD bytes, matching
root and seal, matching producer completion, and the external write-drain fence.
The bench implements a finite one-byte pending-write service and commits bytes
to the candidate bank only on modeled ACK. A held drain fence blocks commit
although hashing is already complete. A late error never updates the accepted
root, generation, semantic HUD cache or reference-bank identity.

`power_on_reset` is a cold, externally quiescent reset. Local `reset` is warm:
it aborts provisional hash/candidate state while retaining accepted metadata
and retaining the writer lease until external writes drain. Abort behaves the
same way. Presentation additionally requires both vblank and scanout drain;
accepted reference commit and safe front presentation are distinct events.

The write-drain signal is an explicit trusted upstream authority, not a measured
physical DMA guarantee. No tagged physical write-response adapter is hidden in
this module. The testbench models actual data writes and ACK lifetime; hardware
memory errors must arrive through the upstream producer failure path or a
future qualified memory adapter.

## Test inputs and exclusions

The ten-column validation TSV supplies actual CS88 packets, canonical tile
bytes, independent HUD words and commitments. Four primary frames correspond
to qualified V91k candidate outputs. Three additional historical frames bootstrap
real accepted references: c0f2 and c3f48/f49. They use source-backed V82 canonical
bytes and byte-exact native selected CS88 packets, and are labeled historical
validation replays, not newly decoded BR88/FPGA output. Each cohort starts from
a real key and then commits causal references; there is no reference-restore
backdoor or golden trusted-root initialization.

The bench checks complete root/seal/HUD digests, every accepted bank byte,
all actual SHA work counts, immutable accepted metadata on late rejection and
warm reset, repeated retry, pending write drain, and negative vblank/scanout
gates. Start-only negative probes also reject a cold delta without an accepted
reference, zero epoch/generation, reserved or replayed frame IDs, stale accepted
generation, wrong delta reference, and a key with a non-sentinel reference.
These probes issue no HUD decode, data writes or hash jobs and preserve accepted
metadata and front/pending ownership before a clean valid retry. SHA framing/microarchitecture tests remain the unchanged component's
qualified scope. The complete entropy-to-hash producer join and full RTL HUD
semantics remain open, so this evidence does not complete V91l/V91m as an
all-RTL frame receiver or prove hardware 30 fps / validated sub-10-ms decoding.

Bench arguments are `validation.tsv seed events.jsonl`. Events include each
actual completed SHA message and digest; nominal rows identify primary versus
historical bootstrap fixtures. Root-owned runners retain source/input snapshots,
strict build commands, simulation output and compressed event artifacts.
