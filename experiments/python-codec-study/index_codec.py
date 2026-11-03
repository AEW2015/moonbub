"""IQ01 research wrapper: predict compact quantized-channel indices.

The existing GBT1 implementation codes dequantized R5/G6/B5 channel values.
This experiment instead maps each already-quantized channel value v to
ceil(v/q), encodes those compact indices as virtual RGB565 words with GBT1
quant_step=1, then reconstructs min(index*q,channel_max). It preserves the
existing prequantizer's exact image, including clipped 31/63 endpoints.

Outer wire header <4sBBI> = IQ01,version1,quant_step,inner_length, followed by
one complete GBT1 packet and CRC32(header+inner) as <I>. Neither this wrapper
nor Python execution establishes FPGA resource use or throughput. Power-of-two
q uses shifts plus saturation in a hypothetical receiver; no DSP is needed.
"""
from __future__ import annotations
import struct
import zlib
import numpy as np
import codec

HEADER = struct.Struct('<4sBBI')
MAGIC = b'IQ01'
MAX_INNER_BYTES = (2*codec.MAX_DIM*codec.MAX_DIM
                   +3*((codec.MAX_DIM+15)//16)**2+codec.HEADER.size+4)


def encode(words: np.ndarray, quant_step: int = 2) -> bytes:
    """Encode the exact codec.quantize reconstruction using compact indices."""
    quantized = codec.quantize(words,quant_step)
    q = quant_step
    virtual = np.zeros(quantized.shape,np.uint16)
    for shift,maximum in ((11,31),(5,63),(0,31)):
        value = ((quantized>>shift)&maximum).astype(np.uint16)
        index = (value+q-1)//q
        virtual |= index << shift
    inner = codec.encode(virtual,quant_step=1)
    body = HEADER.pack(MAGIC,1,q,len(inner))+inner
    return body+struct.pack('<I',zlib.crc32(body))


def decode(packet: bytes) -> np.ndarray:
    """Validate both packets, bounded level indices, and reconstruct RGB565."""
    if not isinstance(packet,(bytes,bytearray)) or len(packet)<HEADER.size+codec.HEADER.size+8:
        raise ValueError('truncated IQ01 packet')
    magic,version,q,size = HEADER.unpack_from(packet)
    if magic != MAGIC or version != 1 or not 1 <= q <= 32:
        raise ValueError('invalid IQ01 profile')
    if size > MAX_INNER_BYTES or len(packet) != HEADER.size+size+4:
        raise ValueError('invalid IQ01 inner length')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I',packet,len(packet)-4)[0]:
        raise ValueError('IQ01 CRC mismatch')
    inner = packet[HEADER.size:-4]
    if len(inner) < codec.HEADER.size+4 or codec.HEADER.unpack_from(inner)[3] != 1:
        raise ValueError('IQ01 inner quantizer must be one')
    virtual = codec.decode(inner)
    out = np.zeros(virtual.shape,np.uint16)
    for shift,maximum in ((11,31),(5,63),(0,31)):
        index = ((virtual>>shift)&maximum).astype(np.uint16)
        if np.any(index > (maximum+q-1)//q):
            raise ValueError('IQ01 channel index out of range')
        value = np.minimum(index*q,maximum).astype(np.uint16)
        # Some non-power-of-two q never produce the saturated endpoint. Reject
        # unused terminal levels rather than admitting a noncanonical image.
        requantized = np.minimum(((value+q//2)//q)*q,maximum)
        if np.any(requantized != value):
            raise ValueError('IQ01 unused quantized channel level')
        out |= value << shift
    return out
