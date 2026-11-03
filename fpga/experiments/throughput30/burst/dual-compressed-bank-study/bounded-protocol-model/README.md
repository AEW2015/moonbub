# Bounded stop-and-wait replay specification

This isolated Python experiment wraps the adjacent tagged bank model with a
single-request replay cache. A request must carry the current epoch and the
next sequential request ID. An exact retry of the immediately preceding
request returns its historical ACK without repeating the operation; a changed
retry is rejected, and any other old or future ID is rejected. Success and
failure both consume an ID. Only one last request/ACK is retained by the
wrapper; the underlying model's history is cleared after each operation.

The caller must have at most one request outstanding and must not send the next
request until it has received the previous response. A client that violates
this rule may lose the ability to replay an older result. In particular this
is not a pipelined QSPI protocol, a throughput estimate, a physical drain or
CDC design, nor an implementation for the real firmware. A single retained
request includes its payload, so memory is bounded by the maximum command size
only if a future wire format imposes one. Python request IDs and epochs do not
wrap. A real implementation needs finite-width wrap handling, a persistent or
fresh non-reused session epoch, reboot reconciliation, and authenticated ACKs
as appropriate. Reset explicitly discards the replay cache and all ownership;
it must follow an actual independently verified quiesce/drain sequence.

Run `python3 -m unittest -v` in this directory. The tests cover lost ACK retry,
conflicting retries, out-of-order requests, bank reuse, stale tokens, reset,
and caching of rejected operations. The underlying bank model allows two
concurrent receives even though the current experimental RTL does not.
