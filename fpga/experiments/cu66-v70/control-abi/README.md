# CU66 v70 HUD control ABI prototype

This folder defines and self-tests a Python standard-library framing codec for
the proposed HUD processor control link. It does not implement an FPGA or
processor endpoint, transport, transaction state machine, CRC over the original
HU format, or physical link. The original CU66/HU payload is carried unchanged
inside PREPARE. This is codec proof only; it is not RTL, integration, or board
evidence.

## Frame format

Every frame is exactly a 32-byte little-endian header, the declared payload,
and a 4-byte little-endian CRC32 trailer. CRC32 is IEEE/zlib CRC-32 over all
32 header bytes followed by the declared payload, protecting generation and
other header fields as well as payload. No trailing bytes are accepted by the single-frame
decoder. The incremental decoder accepts fragmentation and concatenated
frames, then rejects an incomplete frame when `finish()` signals EOF.

| Offset | Type | Field |
|---:|---|---|
| 0 | 4 bytes | `HC70` request or `HR70` response |
| 4 | u8 | ABI version, currently 1 |
| 5 | u8 | Opcode: PREPARE=1, STATUS=2, READ_CANDIDATE=3, ACK_EXTERNAL_WRITE_DRAIN=4, COMMIT=5, ABORT=6, RESET=7 |
| 6 | u16 | Reserved, must be zero |
| 8 | u32 | Payload byte length, at most 49,152 |
| 12 | u64 | Generation |
| 20 | u32 | Frame ID |
| 24 | u32 | Reference ID |
| 28 | u32 | Argument |

All integer fields are unsigned and little-endian. PREPARE carries the original
HU bytes, unchanged, with no codec-added prefix. READ_CANDIDATE request payload is
`offset:u32,count:u32`. ACK_EXTERNAL_WRITE_DRAIN request payload is `word_count:u32,tag[16]`.
COMMIT, ABORT, STATUS and RESET request payloads are empty. For responses,
`argument` carries the status code; response payload is opcode-specific and
this prototype leaves its interpretation to the endpoint contract. The codec
does not determine whether a generation is stale or authorized.

RESET request `argument` must equal 1, defined as the caller's assertion that
the endpoint has reached the protocol's quiescent state before reset. The
codec checks that field policy only. It does not execute or verify quiescence
or reset behavior.

## Self-check

Run `python3 -B -m unittest -v test_hud_control.py` from this directory.
Retained test output and SHA-256 pins are in `results/`. The test only exercises
the Python codec and its stream framing behavior.
