"""CP02 decoder with bounded (<=64 bit) lookahead and exact frozen syntax."""
from pathlib import Path
import struct
import sys
import zlib

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'python-coefficient-study'))
import coeff_codec as frozen_codec

COEFF=frozen_codec.COEFF
MAX_BLOCKS=frozen_codec.MAX_BLOCKS
MAX_COEFF=frozen_codec.MAX_COEFF
PAYLOAD_OVERHEAD=frozen_codec.PAYLOAD_OVERHEAD
frozen=frozen_codec.frozen
_band=frozen_codec._band
_unmap=frozen_codec._unmap


class _Bits:
    """At most64 reservoir bits;15-bit unary lookahead with canonical escapes."""
    def __init__(self,data):
        self.data=data
        self.position=0
        self.offset=0
        self.value=0
        self.bits=0
        self.peak_bits=0

    def _fill(self,count):
        while self.bits<count:
            take=min((64-self.bits)//8,len(self.data)-self.offset)
            if not take:
                raise ValueError('truncated coefficient bits')
            chunk=self.data[self.offset:self.offset+take]
            self.offset+=take
            self.value=(self.value<<(take*8))|int.from_bytes(chunk,'big')
            self.bits+=take*8
            self.peak_bits=max(self.peak_bits,self.bits)

    def get(self,count):
        if count<0 or self.position+count>len(self.data)*8:
            raise ValueError('truncated coefficient bits')
        if not count:return 0
        if count>32:raise ValueError('internal bit-read exceeds bounded window')
        self._fill(count)
        self.bits-=count
        answer=self.value>>self.bits
        self.value&=(1<<self.bits)-1
        self.position+=count
        return answer

    def rice(self,k,escape):
        available=min(15,len(self.data)*8-self.position)
        if not available:raise ValueError('truncated coefficient bits')
        self._fill(available)
        word=self.value>>(self.bits-available)
        zeros=available-word.bit_length()
        if zeros<available:
            self.get(zeros+1)
            return (zeros<<k)|self.get(k)
        if available<15:raise ValueError('truncated coefficient bits')
        self.get(15)
        value=self.get(escape)
        if value>>k<15:raise ValueError('noncanonical coefficient escape')
        return value

    def finish(self):
        left=len(self.data)*8-self.position
        if left>=8 or self.get(left):
            raise ValueError('extra/nonzero coefficient padding')


def decode_coefficients(packet, blocks, blocks_w):
    if (type(blocks) is not int or not 1 <= blocks <= MAX_BLOCKS
            or type(blocks_w) is not int or not 1 <= blocks_w <= 256 or blocks % blocks_w):
        raise ValueError('invalid expected coefficient geometry')
    if (not isinstance(packet, (bytes, bytearray)) or not PAYLOAD_OVERHEAD <= len(packet) <= 128*blocks+PAYLOAD_OVERHEAD):
        raise ValueError('coefficient payload bound')
    magic, version, mode, count, width, reserved, ndc, nac = COEFF.unpack_from(packet)
    if ((magic, version, count, width, reserved) != (b'CP02', 1, blocks, blocks_w, 0)
            or mode not in (0, 1) or len(packet) != PAYLOAD_OVERHEAD+ndc+nac):
        raise ValueError('coefficient header/length')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I', packet, len(packet)-4)[0]:
        raise ValueError('coefficient CRC')
    dc_data = packet[COEFF.size:COEFF.size+ndc]
    ac_data = packet[COEFF.size+ndc:-4]
    if mode == 0:
        if ndc != blocks*128 or nac:
            raise ValueError('RAW coefficient lengths')
        out = np.frombuffer(dc_data, '<i2').copy().reshape(blocks, 8, 8)
        if np.any(np.abs(out.astype(np.int32)) > MAX_COEFF):
            raise ValueError('RAW coefficient range')
        return out
    if not dc_data or dc_data[0] > 13 or len(ac_data) < 3 or any(k > 11 for k in ac_data[:3]):
        raise ValueError('coefficient Rice parameters')
    dcbits, acbits = _Bits(dc_data[1:]), _Bits(ac_data[3:])
    zig = np.zeros((blocks, 64), np.int16)
    previous = 0
    for i in range(blocks):
        if i % blocks_w == 0:
            previous = 0
        difference = _unmap(dcbits.rice(dc_data[0], 14))
        value = previous+difference
        if not -MAX_COEFF <= value <= MAX_COEFF:
            raise ValueError('reconstructed DC range')
        zig[i, 0] = previous = value
        position = 1
        while position < 64:
            # Consume EOB/ZRL together. A nonzero prefix also supplies
            # the top run bit, leaving only its lower three bits to fetch.
            tag = acbits.get(2)
            if tag == 0:
                break
            if tag == 1:
                if position+16 > 64:
                    raise ValueError('AC ZRL overrun')
                position += 16
            else:
                target = position+((tag & 1) << 3)+acbits.get(3)
                if target >= 64:
                    raise ValueError('AC run overrun')
                mapped = acbits.rice(ac_data[_band(target)], 12)+1
                value = _unmap(mapped)
                if value == 0 or not -MAX_COEFF <= value <= MAX_COEFF:
                    raise ValueError('AC coefficient range')
                zig[i, target] = value
                position = target+1
    dcbits.finish()
    acbits.finish()
    out = np.empty((blocks, 64), np.int16)
    out[:, frozen.ZIGZAG] = zig
    return out.reshape(blocks, 8, 8)

