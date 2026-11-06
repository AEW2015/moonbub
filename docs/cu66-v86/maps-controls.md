# V86 grouped operation bodies and actual all-visible controls

These are two component experiments for the compact CS86 study. Neither their
metadata-byte reductions nor the AB38 component sizes alone establish complete
wire savings, hardware latency or a fitted decoder.

## Bit-packed binary group map

The fixed profile retains 8,100 canonical tiles with 294 hidden CONST128 tiles.
Its hidden-mask SHA-256 is
`e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5`.
Only the remaining 7,806 visible positions need COPY_REF/RESIDUAL choices.
Hidden mask, geometry and the explicit profile must agree before parsing.

`scripts/cu66-v86/prototype_maps.py` provides:

```python
method, body = encode_body(modes, hidden, key=key)
modes = decode_body(method, body, hidden, key=key)
```

Method 0 is an implicit key map with an empty body. Delta maps select the
shortest actual body among the inherited visible bitset (method 1), inherited
128-position visible RLE (method 2), and new grouped representation (method 3).
Ties select the lower method number. The bitset fallback limits every selected
body to 976 bytes. This is a body codec; the CS86 outer envelope must bind its
method and protect the bytes, replacing CM84's nested 20-byte header.

Method 3 visits 16-tile groups separately in Y, U and V canonical order:
5400/1350/1350 tiles yield 338/85/85 groups, or 508 total. Every group has a
two-bit MSB-first tag, with no per-group byte padding:

| Tag | Meaning |
|---|---|
| `00` | All visible positions in this group COPY_REF |
| `01` | All visible positions in this group RESIDUAL |
| `10` | Mixed group, followed by one bit per visible position: 0 COPY, 1 RESIDUAL |
| `11` | Empty visible group, legal only when every position is fixed hidden CONST |

Mixed groups must contain both bit values; uniform mixed encodings reject.
Empty groups require tag `11`; visible groups reject that tag. Only the final
body byte may have fewer than eight zero padding bits. Extra bytes, nonzero
padding, truncation and coverage mismatches reject. The independent parser
does not call the encoder or group-body builder.

All **457 native operation arrays** round-trip. The 20 keys select method 0 and
all 437 deltas select method 3. Selected body size is **0 / 712 / 950 bytes**
(minimum/median/maximum), totaling **301,684 bytes**. The previous V2 selected
bodies total 374,962 bytes, so grouping saves **73,278 metadata-body bytes**.
These totals exclude both old and new outer framing.

There are 27 directed malformed/pattern checks. Four retained vectors cover
the implicit key, a real inherited bitset, a real inherited RLE, and a selected
group body. An earlier passing two-vector snapshot is retained as unselected
history; adding inherited vectors changed evidence coverage, not coding rules.

## Actual all-visible coefficient controls

The control collector is a new local fork of V85's actual encoder. It retains
the same quantized coefficients, DC reset rule (`bw=1`), minimum-uncoded-Rice
parameter selection, raw fallback and native independent AB38 decoder. Unlike
the COPY candidates, it encodes every visible tile on both keys and deltas;
hidden CONST tiles remain omitted. Counts are 5,144 / 1,331 / 1,331 blocks per
plane on every source, including zero-coefficient visible tiles.

It produces actual AB38 bytes for chunk caps 256 and 65,536 (the latter means
whole residual plane). Every generated chunk is independently decoded during
native collection and compared coefficient-for-coefficient. Original complete
native packet/picture/HUD/display checks and every zero-mask bit also match.
The full canonical coefficient SHA-256 is unchanged from V85.

| Control chunk cap | Actual AB38 bytes | Chunks | Raw chunks |
|---|---:|---:|---:|
| 256 | 5,879,176 | 15,081 | 0 |
| 65,536 | 4,618,536 | 1,371 | 0 |

The whole-plane control reproduces V85's matched-control bytes on every source
and in aggregate. These retained bytes now allow the parent experiment to
construct and actually receive complete all-visible control packets, rather
than relying on a projected envelope size. Native source coverage is 457
sources / 1,371 original planes across four reset histories from one walkthrough
family. No unseen content or physical throughput qualification follows.

`experiments/python-gamebub-v86/controls/data.py` exposes the V85-compatible
`iter_frames()` API with variant keys `'256'` and `'65536'`, native identities,
quantizer/HUD bytes, original zero mask and actual chunks. Residual-count
metadata refers here to all visible blocks. The independent retained-data audit
checks record/raw/compressed SHA, native metadata, chunk coverage, exact AB38
headers/CRC/lengths and matched-control byte equality without invoking an
encoder. Host collection uses the existing C++17 build container; exact commands,
compiler, binary and source snapshots are retained.

## Reproduction

The following create new metadata evidence or collect controls and refuse to
overwrite their selected result/index:

```sh
python3 scripts/cu66-v86/prototype_maps.py
python3 scripts/cu66-v86/collect_controls.py
```

To audit the retained all-visible controls without re-encoding:

```sh
python3 experiments/python-gamebub-v86/controls/verify.py
```

The host collector and Python parser use complete records and arrays. They are
not bounded streaming FPGA/ESP32 implementations. Complete packet-size and
native receiver qualification remain separate from these component records.
