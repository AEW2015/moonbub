# CS86 compact packet layout

CS86 is the compact host research packet assembled by
`scripts/cu66-v86/run_wire.py` and parsed by
`experiments/python-gamebub-v86/receiver.cpp`. All multibyte integers are
unsigned big-endian. The fixed header is 128 bytes: the 52-byte `PREFIX`
structure, two 32-byte C2 digests, and 12 zero reserved bytes
(52 + 64 + 12 = 128). Offsets below are byte offsets from packet start.

| Offset | Size | Field | Meaning and validation |
|---:|---:|---|---|
| 0 | 4 | Magic | ASCII `CS86` |
| 4 | 1 | Version | `1` |
| 5 | 1 | Flags | `0` delta, `1` key; other bits are not accepted |
| 6 | 1 | Group size | `16` tiles |
| 7 | 1 | Map method | `0` through `3`; see [maps and controls](maps-controls.md) |
| 8 | 4 | Frame ID | `u32` |
| 12 | 4 | Reference ID | `u32`; key uses `0xffffffff`, delta binds accepted frame |
| 16 | 8 | Generation | `u64`, nonzero and newer than accepted state |
| 24 | 2 | Width | `720` |
| 26 | 2 | Height | `480` |
| 28 | 2 | Block size | `16` or `32` |
| 30 | 2 | Reserved | Must be zero |
| 32 | 4 | Chunk cap | Exactly `256` or `65536` |
| 36 | 4 | Map body length | At most `976` bytes |
| 40 | 4 | Quantizer map length | Exactly `338` bytes |
| 44 | 4 | HUD length | `110` through `49152` bytes |
| 48 | 4 | Residual data length | Exact number of bytes in all plane chunk records |
| 52 | 32 | Expected content root | C2 root over reconstructed canonical planes |
| 84 | 32 | Expected content seal | C2 seal over profile, identity, previous root, semantic HUD hash, and root |
| 116 | 12 | Reserved padding | Must be all zero |

The header is followed by the declared map body, 338-byte quantizer map,
residual data, HUD payload, and a four-byte big-endian CRC-32. CRC covers every
preceding packet byte, including the complete header. The packet length must
equal `128 + map_length + 338 + data_length + hud_length + 4` exactly; trailing
bytes reject.

The map is embedded as its raw body. CS86 does not include the 20-byte CM84
map wrapper. Method 0 is the empty implicit key map. Delta methods 1 and 2 are
the inherited visible-position bitset and RLE bodies. Method 3 encodes 16-tile
groups in Y, U, V order with two-bit group tags and optional mixed-group bits;
the fixed hidden mask and group details are documented in
[maps and controls](maps-controls.md). There are 5,400 Y and 1,350 each U/V
tiles (8,100 total); 294 fixed hidden tiles leave 7,806 encoded visible
positions. The receiver reconstructs the fixed profile mask and accepts only
the fixed profile's 16-tile grouping. Map method 3 is a distinct CS86 map
body, not a changed interpretation of a CS85 field.

The quantizer map contains 1,352 two-bit slots: 1,350 active scale codes and
two required zero padding codes. The residual section is in Y, U, V plane
order. Each plane starts with a big-endian `u32` chunk count. Each chunk is a
big-endian `u32` block count, a big-endian `u32` AB38 byte length, then the
AB38 payload. The receiver checks counts against the declared cap, validates
chunk bounds and decodes each payload. The `data_length` covers all three
plane count words and chunk records.

The content profile and hidden mask are fixed in the receiver and therefore
are not transmitted as per-packet fields. A delta's previous root comes from
accepted receiver state, not a packet field. The receiver reconstructs the
semantic HUD digest and C2 root, then recomputes and checks the C2 seal against
the header's expected seal before publishing state. These implicit values are
validated through the resulting map, state binding, root, and seal checks;
they are not omitted checks. Packet replay is accepted only for the same full
packet digest, and rejected packets must leave accepted state unchanged.

The native receiver currently bounds a research packet to 2 MiB. That parser
limit is not an FPGA or ESP32 receive-memory limit. The 49,152-byte
compatibility budget is reported separately by the experiment; it is not a
formal negotiated transport cap. Formal profile negotiation, bounded
streaming hardware, and FPGA/ESP32 integration are not implemented. The selected
full-wire run verifies all 457 sources across six configurations (2,742 native
packets), with all six receiver processes exiting 0. See [evidence-scope.md](evidence-scope.md)
for the complete proof and its bounds. The earlier
[`wire-layout-audit.json`](../../experiments/python-gamebub-v86/wire-layout-audit.json)
records the initial two-source smoke extent and manual layout arithmetic only.
