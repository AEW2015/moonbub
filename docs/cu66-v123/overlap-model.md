# V123 causal spatial overlap prototype

This standard-library event model uses six retained canonical vectors. It is a synthetic scheduling hypothesis, not an RTL, C2/HUD/seal, FPGA timing, or hardware model. Its cycle values must not be read as frame latency or FPS evidence.

## Inputs and byte checks

Input: `experiments/python-gamebub-v122/integrated-study/spatial/attempts/20261110T004249476141Z/sources/experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz`. Each of six rows contains `id`, `refhex`, and `targetcanonicalhex`; the target payload is 518,400 bytes (8,100 chunks of 64 bytes). The first reference field is `-`; the other five reference fields are retained and SHA-256 hashed. Reference bytes are not assumed to equal target canonical bytes. Every target payload is sent through the event schedule, written to modeled memory on ACK, read back from that memory in order by the digest consumer, and compared by full-vector SHA-256 with the digest of the retained target bytes. This verifies transfer/scheduling byte preservation; the target digest is derived from the same retained payload and is not an independent oracle. The compressed input hash and per-vector target/reference hashes are recorded in `overlap-model/results.json`.

## Causal schedule and resource accounting

For each 64-byte result chunk, the model allocates an available slot and compute lane, computes the chunk, queues it until the memory bus is free, accepts one physical write, waits for its ACK, and commits the actual payload bytes into modeled memory. One ordered hash consumer reads only ACK-committed bytes, in allocation order, from an assumed local ACK-committed mirror. That local read is instantaneous in the model: storage and digest-port cost are unbudgeted, and this does not claim an additional physical read port. The modeled 16-bit bus charges writes only; it has no readback traffic, scanout, or refresh, so it is not a full memory-bandwidth lower bound. If the actual design needs external readback, that traffic and its service cost must be added in a future model. A slot is released only after its matching token is ACKed and hashed. The integrated runtime ledger enforces globally unique tokens, slot ownership, maximum outstanding write credit of one, matching ACKs, ACK-before-hash, strict hash order, no duplicate hash, matching release, zero debt, and all chunks hashed before the abstract batch drain.

Each vector's `synthetic_compute_start_cycle` is when its first chunk is allocated for compute. Its `digest_complete_cycle` follows hashing of the last chunk, full-vector digest comparison, and a synthetic four-cycle finalization step. The result records each vector's compute-start-to-digest interval. It does not represent final-outer-byte-to-validated-commit time and cannot be compared directly with the retained row fixture's 1.55-million-cycle interval. These digest completion points are not immutable-bank publication. Only the final batch ledger check asserts zero debt, all ACKs/hashes, and no owned slots; that abstract batch drain is not a C2/HUD/seal publication model.

## Synthetic profiles and limits

The modeled bus is 16 bits wide, so 64 bytes require at least 32 data edges. Profiles use exactly 32 synthetic data edges plus either 2 or 16 synthetic overhead edges per 64-byte write (34 or 48 total). Profiles below the 32-edge data floor are rejected. The compute cost is 32 synthetic cycles per chunk. The ordered digest service is an abstract 12-cycle cost per chunk; it does not model the SHA-256 core's full computation. A separate four-cycle synthetic per-vector finalization cost is included. These costs are not calibrated from aggregate counters or measured from hardware.

The six configurations are `(1 slot, 1 lane)`, `(2 slots, 1 lane)`, and `(2 slots, 2 lanes)` under both profiles. A faster model total does not establish that such compute overlap is feasible in RTL or that a real memory service can meet those assumptions.

Run:

```sh
python3 scripts/cu66-v123/overlap_model.py --self-test
```

The bounded self-tests cover valid abstract batch drain and failures for wrong/stale tokens, early batch drain, unpaid debt, slot reuse, hash before ACK, out-of-order hashing, corrupted ACK-committed data, a bus cost below the physical data-edge floor, and nonpositive/noninteger compute, hash, finalization, and overhead parameters. The command writes `experiments/python-gamebub-v123/overlap-model/results.json` with input/script hashes, schedule hashes, per-vector compute-start-to-digest intervals and aggregate abstract batch-drain cycles, queue/slot/ACK statistics, and digests. The original prototype output is preserved at `overlap-model/attempts/initial-prototype-results.json`, bound by hash in the revised results; it used an impossible eight-edge service assumption and a disconnected test ledger. No aggregate V122 event count is expanded into a trace. No RTL, C2/HUD/seal, native route, validated-decode, 125 MHz, or FPS gate is closed.
