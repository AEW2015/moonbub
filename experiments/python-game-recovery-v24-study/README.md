# RS24 functional profile/reset agreement

This Python control-plane prototype agrees the exact CP23 profile, waits for old
owners to drain and establishes a new epoch after a one-sided reboot. It never implements
TLS/security rekey, real packet-credit drain, persistent storage or physical DMA.

Eight normal messages are HELLO/HELLO_REPLY, OFFER/READY, COMMIT/COMMITTED and
GO/GO_ACK. All bind a fixed profile digest, host/target boot nonce and reserved
monotonic epoch where applicable. Each is 46 application bytes including CRC;
nominal cost is 368 application /592 IPv4+UDP bytes. Retries use identical bytes,
and the campaign charges dropped messages too. CRC is not authentication.

Both sides require explicit transport-drained permission and no active source,
HUD-bank or decode owners before replacing state. Late reader acquisition is
rechecked at commit. Data remains blocked while reset agreement is incomplete.
The first new epoch requires an independent video key and full nonreferenced HUD.
Duplicate old COMMIT/GO packets cannot erase newly published banks. Epochs and
lease identities never wrap; exhausted state fails closed.

The campaign covers nominal plus one loss of each of eight message kinds, all
GO_ACK replies lost, and target/host reboot sequences. It replays actual CP23 and
JA23 packets from a static synthetic canvas. Nine nominal/single-loss sequences
recover; persistent GO_ACK loss leaves host SAFE_STOP and target RUNNING, with
the host still forbidden to emit data. No finite-loss recovery claim applies to
unbounded faults. The reboot sequence uses new epochs 1/2/3 and rejects stale data.

EpochLedger objects explicitly model durable monotonic storage retained across
reboot. Simultaneous loss of both ledgers, durable writes, real nonce generation,
network addressing, reordered data-plane FIFO/credit ownership and asynchronous
capture/display fences remain open. No native endpoint, elapsed recovery latency,
real network, memory mapping or physical frame-rate proof is supplied.

```sh
python -m unittest -v test_model.py
python verify.py
```

`benchmark.py` regenerates deterministic source-pinned traces. `verify.py` parses
all bytes and reruns the fault/data sequences without external footage.
