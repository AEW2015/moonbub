"""Export deterministic synthetic HD21 controls, not gameplay/FPS measurements."""
from pathlib import Path
import hashlib
import json
import zlib

import numpy as np
import model

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    stored = zlib.compress(data, 9)
    name = sha(stored) + ".zlib"
    (HERE / "objects").mkdir(exist_ok=True)
    (HERE / "objects" / name).write_bytes(stored)
    return dict(path="objects/" + name, raw_bytes=len(data), raw_sha256=sha(data), stored_sha256=sha(stored))


def main():
    rng = np.random.default_rng(2104)
    base = rng.integers(0, 65536, (24, 160), dtype=np.uint16)
    sparse = base.copy()
    sparse[0, :3] ^= 1
    sparse[0, 5] ^= 65535
    sparse[23, 159] ^= 32768
    maximum = np.full((32, 660), 65535, dtype=np.uint16)
    cases = [("raw-random", base, None), ("copy-random", base, base),
             ("five-words-three-runs", sparse, base),
             ("all-words-changed-raw-fallback", base ^ np.uint16(1), base),
             ("maximum-words", maximum, None),
             ("single-word-extreme", np.zeros((1, 1), dtype=np.uint16), np.full((1, 1), 65535, dtype=np.uint16))]
    vectors = []
    for name, current, reference in cases:
        packet = model.encode(current, reference)
        np.testing.assert_array_equal(model.decode(packet, reference), current)
        vectors.append(dict(name=name, shape=list(current.shape), current=blob(current.astype("<u2").tobytes()),
                            reference=None if reference is None else blob(reference.astype("<u2").tobytes()),
                            packet=blob(packet), metadata=model.inspect(packet)))
    paths = ("model.py", "test_model.py", "benchmark.py", "verify.py", "README.md", "SCHEMA.md")
    result = dict(schema="gamebub-hud-delta-v21-1", source_sha256={p: sha((HERE / p).read_bytes()) for p in paths},
                  vectors=vectors, summary=dict(vectors=len(vectors), roundtrip_words=sum(a.size for _, a, _ in cases),
                  complete_packet_bytes=sum(v["metadata"]["packet_bytes"] for v in vectors)),
                  scope="Deterministic synthetic component controls; not native gameplay, target resource timing, or physical 30fps.")
    (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
