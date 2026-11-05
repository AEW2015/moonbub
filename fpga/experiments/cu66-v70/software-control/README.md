# Encoded HC70/HR70 native HUD endpoint

`hud_endpoint.hpp` is a transport-neutral C++17 framing codec and stateful HUD
endpoint around the **unchanged** v69 `HudGate`. It uses the v70 Python
`control-abi/hud_control.py` frame format: 32-byte little-endian header,
0–49,152 payload bytes, and CRC32 over the complete header plus payload.
The maximum complete control frame is49,188 bytes. This limit is separate
from the original CU66 video packet's complete-frame cap.

There are no C/C++ struct layout casts. Exact size, magic, version, opcode,
reserved bits, payload shape and header+payload CRC are validated before
dispatch can mutate the gate. The endpoint accepts one complete HC70 request
at a time; partial/concatenated frames require an external bounded assembler.
Malformed framing throws `hc70::ProtocolError` without changing accepted or
candidate state. A valid request returns one encoded HR70 response.

## Request policy

Every response echoes request opcode/generation/frame/reference header fields.
The response header's `argument` is a result code. Gate-mutating requests and
candidate reads bind generation, frame ID **and reference ID**. STATUS is a
read-only query whose response body explicitly identifies current gate state.

| Opcode | Request argument / payload | Meaning |
|---:|---|---|
| 1 PREPARE | argument0=predicted or1=key; unchanged original HU bytes | Decode original compressed HUD and verify its reference/output semantics |
| 2 STATUS | argument0, empty payload | Return current status; request identity need not name the current candidate |
| 3 READ_CANDIDATE | argument0; `offset:u32,count:u32` | Read actual owned candidate words in rectangle order as little-endian u16; check bounds without wrapping |
| 4 ACK_EXTERNAL_WRITE_DRAIN | argument1; `word_count:u32,readback_tag[16]` | Caller asserts external writes drained; require count21120 and exact candidate tag |
| 5 COMMIT | argument0, empty payload | Advance accepted HUD only after matching transfer ACK; root whole-frame authority must qualify this call |
| 6 ABORT | argument0, empty payload | Discard the matching candidate/failed preparation and preserve accepted HUD |
| 7 RESET | argument1, empty payload, fresh generation | Caller asserts all relevant external masters quiescent; clear caches using the frozen gate's reset policy |

READ success has exactly `2*count` payload bytes, with no extra prefix. Word
order is the existing four rectangle arrays, each row-major. Error replies and
all other opcode replies carry the fixed72-byte status payload below. Clients
must check the result code before interpreting READ bytes.

COMMIT retries for the **currently accepted** generation/frame/reference are
idempotent. ABORT retains one last-successful identity so a lost ABORT reply
can be retried idempotently, even after a newer candidate is prepared, without
discarding that new candidate. A successful RESET invalidates the abort cache.
This is not an unbounded historical reply log. PREPARE retries while a
candidate exists report Busy; STATUS can determine the current transaction.

## Result codes and fixed response status payload

Result codes:0=Ok,1=Busy,2=Stale,3=InvalidIdentity,4=DecodeRejected,
5=Rejected (policy, missing candidate, invalid range, transfer or commit gate).
Malformed framing produces no trustworthy encoded reply; the caller receives
`ProtocolError`. The test executable's codec-only mode returns exit2 and an
explicit `CODEC_REJECT` marker for those expected negative cases.

| Payload offset | Type | Field |
|---:|---|---|
| 0 | u8 | Phase: Idle0, Ready1, Transferred2, Committed3, Aborted4, Failed5 |
| 1 | u8 | Flags described below |
| 2 | u16 | Reserved zero |
| 4 | u32 | Current status word count |
| 8 | u64 | Current status generation |
| 16 | u32 | Current status frame ID |
| 20 | u32 | Current status reference ID |
| 24 | 16 bytes | Current status HUD tag |
| 40 | u64 | Accepted HUD generation, or0 when absent |
| 48 | u32 | Accepted frame ID, or0xffffffff when absent |
| 52 | u32 | Accepted reference ID, or0xffffffff when absent |
| 56 | 16 bytes | Accepted HUD tag, or all zero when absent |

Flag bits:0=historical semantic decode verified,1=historical external-drain ACK,
2=live candidate ready,3=live candidate transferred,4=accepted cache exists.
After COMMIT the historical decode/drain flags may remain set, but live
candidate flags2/3 are clear. A historical success is not a new ready token.
An old ABORT retry may return Ok with a body describing a newer current
candidate; correlate the echoed request identity and inspect status-body IDs.

## Qualification and reproducibility

```sh
python3 fpga/experiments/cu66-v70/software-control/run_endpoint.py
python3 fpga/experiments/cu66-v70/software-control/verify_endpoint.py
```

The dedicated tools container builds with GCC13/C++17 and fatal
`-Wall -Wextra -Wconversion -Werror`, then runs release and ASAN/UBSAN builds.
Both builds pass **457 actual HUD histories /20 keys** using **2,811 encoded
commands per build**. Each actual frame executes encoded PREPARE, STATUS,
complete READ, readback-tag ACK and COMMIT, including an idempotent COMMIT
retry. The READ bytes match frozen source HUD hashes and the actual original
HU output tag after reconstructing rectangle geometry. Candidate words remain
valid after overwriting the input wire buffer.

Thirteen malformed header/opcode/length/CRC/direction/reset-policy cases leave
both accepted state and encoded STATUS unchanged. Directed tests additionally
cover early commit, Busy/Stale generation behavior, incorrect ACK authority
or reference identity, invalid READ ranges/overflow, nested HU corruption,
stale reset, lost COMMIT/ABORT reply retries, delayed old ABORT during a new
candidate, and recovery with original key/P packets.

The Python cross-check round-trips17 valid frames through Python→C++→Python,
including all seven opcodes, both magics, maximum payload and high u64 values;
15 malformed cases are rejected by both codecs. It also independently decodes
five actual native endpoint request/response pairs and reconstructs the full
HUD tag from the native READ response using Python `hashlib`. No Python ABI
source was changed. First-key request/response artifacts are in `examples/`.

## Integration boundary

The header library has no OS calls and can be a starting point for a firmware
port, but uses the frozen decoder's C++ heap/exception-based containers. Peak
live allocations, timing and coexistence with Wi-Fi/UI/QSPI have **not** been
qualified on ESP32. The test executable's filesystem operations are tooling,
not endpoint requirements. No server, link transport, MMIO adapter or ESP32
firmware image was added.

The complete-system simulation still uses its separately tested typed HUD
peer; this encoded endpoint is not claimed to be on that system's live path.
ACK/RESET arguments are **caller assertions**, not measured DMA completion,
cache coherency or physical reset/flush. CRC provides framing integrity, not
authentication. Root generation/whole-frame commit authority remains external.
