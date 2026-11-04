# Native AR03 gateway contract building block

Experimental offline C port, not installed receiver firmware. Source contract is
MoonBub `27a4dde6a7e2ea4fab09d892551ef542f05c8965`; paired Sunshine
`3d49c6fe87753eb5b35d693991fdff0365e4bbbf` has byte-identical wire and development
JSON (recorded under `evidence/ar03-v20-20261104/paired-contracts.json`).

`gb_gateway.c` decodes FG19 and TOKEN/GF03 byte fields without packed casts,
allocation or output mutation on invalid input. It checks bounded fragment
geometry and binds a route to a GRANT identity. It has no socket, DMA, credit
ledger, FIFO reader, frame assembly or entropy decoder. A successful parse or
`gb_route_matches` is **not** permission to forward data or acknowledge a frame.
The caller must still validate its exact frame owner, packet-token lease, real
FIFO space and whole assembled packet/body CRC. Individual GF03 payloads do not
carry an independent payload CRC; the returned token/header CRC covers only the
first 47 bytes, as prescribed by the current contract.

`gb_write_fg19` serializes a grammatical control into exactly 36 bytes with the
specified network byte order and CRC. It validates into local scratch before
touching caller output, rejects insufficient capacity, and does not authorize
sending a control. All 1,725 retained controls round-trip byte-for-byte. Native
frame-reservation work is separate in `gb_ownership.c`; see its own limits and
tests before use. Neither helper implements production reset negotiation.

The caller supplies the accepted epoch. Current golden vectors use epoch1; this
does not implement production negotiation/reset/rekey. FG19 slot syntax matches
the frozen parser, including NO_SLOT for some control kinds. Endpoint state and
direction policy must reject controls without the exact real owner. Packet slot
numbers 0..5 are grammatical; a separate ledger limits simultaneous DATA permits
to five while reserving the sixth mailbox position for control.

Run on Linux/WSL with GCC and Python standard library:

```sh
python3 test_gateway.py --source /path/to/pinned/moonbub \
  --result /path/to/evidence/gateway-native-result.json
```

The test compiles a temporary shared C library with UBSan and replays all 1,725
retained FG19 controls, exact fields and hashes, all single-bit corruptions of one
control, truncated/oversized and valid-CRC illegal controls, actual GF03/header
CRC, fragment-boundary geometry up to 49,152 bytes, wrong-owner binding, control
serialization and NULL inputs. This is Linux host correctness evidence, not ESP32 ISA/CPU/heap/QSPI/RF
calibration or complete protocol ownership evidence.
