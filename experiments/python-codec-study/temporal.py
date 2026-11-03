"""Experimental immutable-reference tile delta wrapper; not a device protocol.

Only exact differences in a prequantized RGB565 image are omitted. Changed
tiles are packed into an intra-coded mosaic. Complete packets are CRC checked
before a copied reference can be published. Whole-frame reference copies are
deliberate and counted, rather than treating SKIP as free SDRAM traffic.
"""
import struct
import zlib

import numpy as np

import codec

HEADER = struct.Struct('<4sIIIIHHII')
NO_REF = 0xffffffff
MAX_PIXELS = 720 * 480


def encode(words, reference=None, *, epoch=1, frame_id=0, reference_id=NO_REF,
           use_dpcm=True):
    """Encode a full independent frame or a delta against an exact reference."""
    a = np.asarray(words)
    if a.dtype != np.uint16 or a.ndim != 2:
        raise ValueError('expected uint16 image')
    h, w = a.shape
    if not h or not w or h % 16 or w % 16 or h * w > MAX_PIXELS:
        raise ValueError('temporal dimensions must be bounded multiples of 16')
    if not 0 <= epoch < NO_REF or not 0 <= frame_id < NO_REF:
        raise ValueError('identity exhausted; start a fresh epoch')
    independent = reference is None
    if independent:
        reference_id = NO_REF
    elif reference.dtype != np.uint16 or reference.shape != a.shape or not 0 <= reference_id < frame_id:
        raise ValueError('invalid reference identity/image')
    tiles = a.reshape(h//16, 16, w//16, 16).transpose(0, 2, 1, 3).reshape(-1, 16, 16)
    if independent:
        indices = np.arange(len(tiles), dtype=np.uint16)
    else:
        previous = reference.reshape(h//16, 16, w//16, 16).transpose(0, 2, 1, 3).reshape(-1, 16, 16)
        indices = np.flatnonzero(np.any(tiles != previous, axis=(1, 2))).astype(np.uint16)
    payload = b''
    if len(indices):
        columns = w // 16
        rows = (len(indices) + columns - 1) // columns
        mosaic = np.zeros((rows * columns, 16, 16), dtype=np.uint16)
        mosaic[:len(indices)] = tiles[indices]
        mosaic = mosaic.reshape(rows, columns, 16, 16).transpose(0, 2, 1, 3).reshape(rows * 16, w)
        payload = codec.encode(mosaic, quant_step=1, use_dpcm=use_dpcm)
    body = HEADER.pack(b'TD01', epoch, frame_id, reference_id, int(independent),
                       w, h, len(indices), len(payload)) + indices.astype('<u2').tobytes() + payload
    return body + struct.pack('<I', zlib.crc32(body))


def decode(packet, reference=None, *, epoch=1, reference_id=NO_REF):
    """Stateless reconstruction; never mutate the supplied reference.

    Caller must bind reference image+ID to this epoch and enforce monotonic
    commit IDs. Use Receiver for that stateful publication contract. Successful
    reconstruction alone does not publish a framebuffer or prove memory drain.
    """
    if not isinstance(epoch, int) or not 0 <= epoch < NO_REF:
        raise ValueError('reserved/invalid expected epoch')
    if len(packet) < HEADER.size + 4:
        raise ValueError('truncated temporal packet')
    body, crc = packet[:-4], struct.unpack('<I', packet[-4:])[0]
    if zlib.crc32(body) != crc:
        raise ValueError('temporal CRC')
    magic, session, frame_id, ref_id, independent, w, h, count, size = HEADER.unpack_from(body)
    if magic != b'TD01' or session != epoch or independent not in (0, 1):
        raise ValueError('unsupported profile/epoch')
    if not w or not h or w % 16 or h % 16 or w * h > MAX_PIXELS or frame_id == NO_REF:
        raise ValueError('invalid dimensions/identity')
    total = w * h // 256
    if count > total or len(body) != HEADER.size + count * 2 + size:
        raise ValueError('invalid tile count/length')
    indices = np.frombuffer(body, '<u2', count, HEADER.size)
    if count and (int(indices[-1]) >= total or np.any(indices[1:] <= indices[:-1])):
        raise ValueError('tile indices must be bounded and strictly increasing')
    if independent:
        if ref_id != NO_REF or count != total:
            raise ValueError('incomplete independent frame')
        out = np.zeros((h, w), dtype=np.uint16)
    else:
        if (ref_id != reference_id or ref_id >= frame_id or reference is None
                or reference.shape != (h, w) or reference.dtype != np.uint16):
            raise ValueError('missing or stale reconstructed reference')
        out = reference.copy()
    if bool(count) != bool(size):
        raise ValueError('missing/unexpected mosaic')
    if count:
        mosaic = codec.decode(body[HEADER.size + count * 2:])
        columns = w // 16
        rows = (count + columns - 1) // columns
        if mosaic.shape != (rows * 16, w):
            raise ValueError('mosaic shape mismatch')
        tiles = mosaic.reshape(rows, 16, columns, 16).transpose(0, 2, 1, 3).reshape(-1, 16, 16)
        for index, tile in zip(indices, tiles):
            y, x = divmod(int(index), columns)
            out[y*16:(y+1)*16, x*16:(x+1)*16] = tile
        if np.any(tiles[count:]):
            raise ValueError('noncanonical mosaic padding')
    return out, {'frame_id': frame_id, 'changed_tiles': count, 'total_tiles': total,
                 'reference_copy_bytes': 0 if independent else w*h*4,
                 'changed_pixel_write_bytes': count*512,
                 'independent': bool(independent)}


class Receiver:
    """Single-session, monotonic, atomic reference owner for the Python model.

    A failed packet leaves all committed state unchanged. Returned images are
    separate arrays: consumers may mutate them without changing the owned
    reference. This class is not thread-safe and implements no ACK, physical
    memory-drain, presentation, or network retry protocol. Start a new Receiver
    with a fresh epoch after reset; epoch allocation is an external contract.
    """
    def __init__(self, epoch=1):
        if not isinstance(epoch, int) or not 0 <= epoch < NO_REF:
            raise ValueError('reserved/invalid receiver epoch')
        self._epoch = epoch
        self._last_frame_id = None
        self._reference = None

    @property
    def epoch(self):
        return self._epoch

    @property
    def last_frame_id(self):
        return self._last_frame_id

    def receive(self, packet):
        image, info = decode(packet, self._reference, epoch=self._epoch,
                             reference_id=NO_REF if self._last_frame_id is None else self._last_frame_id)
        frame_id = info['frame_id']
        if self._last_frame_id is not None and frame_id <= self._last_frame_id:
            raise ValueError('replayed/regressing committed frame')
        owned = image.copy()
        owned.setflags(write=False)
        # No state is changed until the complete packet is validated/copied.
        self._reference = owned
        self._last_frame_id = frame_id
        info['python_ownership_snapshot_bytes'] = image.nbytes
        return image, info
