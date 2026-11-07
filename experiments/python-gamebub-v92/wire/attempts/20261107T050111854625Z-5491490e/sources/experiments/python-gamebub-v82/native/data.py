"""Verified V82 decoded tiles. Pure standard library, one frame retained by loader.

iter_frames() yields dictionaries with 8100 actual 64-byte tiles (Y5400/U1350/V1350)
and four masks, each bytes(8100) of 0/1 values. `same_mask` compares byte equality
with the prior accepted frame, even for keys; an initial frame has no equal tiles.
`copy_ref_mask` is only visible delta tiles with all 64 quantized coefficients zero.
Hidden tiles use CONST128. Keys always use the full-write baseline.
"""
from pathlib import Path
import gzip
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parent
TILE_COUNTS = (5400, 1350, 1350)
TILE_COUNT = 8100
TILE_BYTES = 64
MASK_NAMES = ("same_mask", "zero_coeff_mask", "hidden_mask", "copy_ref_mask")

def iter_frames(root=None, *, verify=True):
    """Yield frames in cohort/ordinal order, verifying chunk digests by default.

    Metadata includes key/fid/refid/cohort, encoded sizes, packet/canonical/HUD/
    display digests, and encoded base/HUD digests. Masks include all hidden tiles;
    callers must distinguish `hidden_mask` (CONST128) from visible COPY_REF.
    """
    root = Path(root) if root is not None else ROOT
    index = json.loads((root / "index.json").read_text())
    total = 0
    for chunk in index["chunks"]:
        path = root / chunk["path"]
        if verify and hashlib.sha256(path.read_bytes()).hexdigest() != chunk["gzip_sha256"]:
            raise ValueError(f"gzip digest mismatch: {path}")
        raw_hash = hashlib.sha256()
        raw_length = 0
        with gzip.open(path, "rb") as stream:
            for _ in range(chunk["record_count"]):
                head = stream.read(4)
                if len(head) != 4:
                    raise ValueError("truncated frame length")
                n, = struct.unpack("<I", head)
                if not 1 <= n <= 16384:
                    raise ValueError("metadata bound")
                payload = stream.read(n + TILE_COUNT * (TILE_BYTES + len(MASK_NAMES)))
                if len(payload) != n + TILE_COUNT * (TILE_BYTES + len(MASK_NAMES)):
                    raise ValueError("truncated frame payload")
                raw_hash.update(head); raw_hash.update(payload)
                raw_length += 4 + len(payload)
                frame = json.loads(payload[:n])
                tile_data = payload[n:n + TILE_COUNT*TILE_BYTES]
                frame["tiles"] = [tile_data[i:i+64] for i in range(0, len(tile_data), 64)]
                at = n + TILE_COUNT*TILE_BYTES
                for name in MASK_NAMES:
                    frame[name] = payload[at:at+TILE_COUNT]
                    at += TILE_COUNT
                frame["planes"] = [frame["tiles"][:5400], frame["tiles"][5400:6750], frame["tiles"][6750:]]
                frame["copy_mask"] = [frame["copy_ref_mask"][:5400], frame["copy_ref_mask"][5400:6750], frame["copy_ref_mask"][6750:]]
                total += 1
                yield frame
            if stream.read(1):
                raise ValueError("extra chunk payload")
        if verify and (raw_hash.hexdigest() != chunk["raw_sha256"] or raw_length != chunk["raw_bytes"]):
            raise ValueError(f"raw digest/size mismatch: {path}")
    if total != index["record_count"]:
        raise ValueError("corpus record count mismatch")
