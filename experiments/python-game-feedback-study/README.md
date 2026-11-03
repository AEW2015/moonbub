# GF02 chunks and GA01 decoded-frame feedback

This Python-only study connects frozen GM01 packets to real serialized chunk
and feedback bytes. It leaves the v8 GF01 sources and golden data unchanged.
Read [PROTOCOL.md](PROTOCOL.md) for fields and ownership rules, and the
[finite pipeline](../python-game-pipeline-study/README.md) for charged virtual
service and deadlines. No network socket, firmware, FPGA or live Sunshine mode
is installed here.

## Ownership correction and content binding

`regression_compare.py` reproduces a v8 GF01 bug: conflicting metadata after a
complete frame has been delivered deletes its logical pending slot. The immutable
Python bytes remain alive, but ownership is lost and the original completion
cannot commit. GF02 retains that delivered pin until its exact reader calls
`commit` or `reject`. Only an incomplete assembly may be discarded on conflict
or partial timeout. Reset refuses active delivered readers.

GA01 carries epoch, frame ID, ACK/NACK status and the GM01 body CRC. Its tag excludes
the GM01 footer: CRC32 of a complete CRC-appended valid GM01 packet has a constant
residue. All eight different golden packets share that whole-packet residue;
the eight body tags differ. The whole CRC still detects transport corruption;
it does not identify content for feedback. CRC is not authentication.

`delivery.py` checks ownership and GF02/GM01 identity, then calls the independent
GM01 receiver. ACK follows valid reconstruction and explicit ingress commit.
An inner failure returns NACK and releases the reader without advancing codec
state. The functional adapter has immediate completion; the finite pipeline
separately schedules reader lifetime, feedback serialization and expiration.

## Stored evidence

- Eight golden packets re-chunked as GF02, reverse-ordered and duplicated, all
  decode to the exact stored RGB565 output. All buffers drain.
- Three fault campaigns cover delivered metadata/duplicate conflict, missing
  chunk timeout, and valid outer transport containing a bad inner GM01 CRC.
- Six tests cover feedback CRC/identity/content tags, reorder/duplicate errors,
  two pinned slots, timeout/reset, and partial-versus-delivered ownership.
- Golden replay traffic is 40,843 nominal IPv4/UDP bytes forward, including
  duplicate datagrams, and 416 reverse bytes for eight 52-byte feedback messages.
  Fault campaigns are reported separately; these sums are not link throughput.

`results.json` and `regression.json` bind executed source hashes and golden
packet/manifest hashes. From this directory, using the study's pinned Python
and NumPy environment:

```sh
python -m unittest -v
python benchmark.py
python regression_compare.py
```

The payload pool is bounded to two 49,152-byte slots. Python allocation copies,
metadata, decoder workspaces and source arrays are extra. This is a logical
ownership proof; physical DMA drain, target memory fit, CPU service, real QSPI,
capability negotiation and authenticated peer control remain integration work.
