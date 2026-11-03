# GF02 / GA01 laboratory contract

Experimental profile only. GF01, installed JPEG peers and GM01-only adapters do
not negotiate or accept this profile. GM01 coefficient/map arithmetic remains
unchanged. No capability negotiation or authentication is implemented.

## Forward GF02

All fields are network byte order. Python layout is `!4sBIIIHHHII`, 31 bytes.

| Field | Bytes | Rule |
| --- | ---: | --- |
| Magic | 4 | `GF02` |
| Version | 1 | 2 |
| Epoch | 4 | Current session, below `0xffffffff` |
| Frame | 4 | Capture ID, below `0xffffffff`, newer than committed ID |
| Total payload | 4 | 1 through 49,152 bytes |
| Chunk index | 2 | Zero based |
| Chunk count | 2 | `ceil(total / 1024)` |
| Chunk payload length | 2 | Canonical 1,024 bytes except final chunk |
| Whole CRC | 4 | CRC32 of complete GM01 bytes, including its footer |
| Body tag | 4 | CRC32 of GM01 bytes excluding the final four-byte footer |

A chunk consists of that header followed by exactly its declared bytes. All
chunks for an identity must agree on total, count, whole CRC and body tag.
Complete assembly checks both CRC values; the decoder adapter also validates
GM01 and matches its epoch/frame to the outer identity. GF02 alone does not
parse the codec. Nominal IPv4/UDP adds 28 bytes, so each chunk costs payload+59
bytes before lower-layer framing. At most 48 chunks describe a maximum frame.

There are at most two reassembly slots. Identical repeats are harmless. Conflicts
abort incomplete assemblies, but must preserve a delivered reader's ownership.
Partial timeout applies only before delivery. Delivery does not commit the
codec or release a slot. `commit(complete)` requires the exact owned completion
and valid newer decoded frame; `reject(complete)` signals a finished failed or
obsolete reader. Advancing commit may remove older partial rows but leaves older
delivered readers pinned. Reset requires every delivered reader to drain.

## Reverse GA01

Layout is `!4sBBHIII` (20 bytes), followed by a network-order four-byte CRC32 over
those 20 bytes. Total 24 bytes; nominal IPv4/UDP wire cost is 52 bytes.

| Field | Bytes | Rule |
| --- | ---: | --- |
| Magic | 4 | `GA01` |
| Version | 1 | 1 |
| Status | 1 | 0 ACK, 1 NACK |
| Reason | 2 | ACK requires 0; NACK requires 1 through 7 |
| Epoch | 4 | Session binding |
| Frame | 4 | Exact transaction binding |
| Body tag | 4 | GF02/GM01 content checksum binding |
| Feedback CRC | 4 | CRC32 of preceding 20 bytes |

Reason numbers are advisory in these prototypes, with no frozen shared reason
mapping between the immediate functional helper and pipeline. A target peer
contract must freeze that enum before deployment. Sender decisions use status
plus exact epoch/frame/body-tag matching. Invalid CRC/fields or stale/foreign
feedback must never create a reference. Accepted key ACK installs the immutable
reference; P ACK releases credit without changing it.

Feedback success follows valid decode completion, not chunk arrival. A NACK or
timeout requests expiration; it does not cancel an active reader or permit slot,
reference or credit reuse until every encode/wire/QSPI/decode owner drains.
There is no retransmission/authentication/replay-window policy beyond the stated
laboratory identity and monotonic-commit checks. Whole-packet CRC residues must
not be substituted for the body tag.
