"""HR01 row-reset lossless RGB565 patch candidate; no temporal patch state.

The PC chooses complete encoded bytes. A bounded decoder needs only a row's
remaining-pixel counter, literal/run counter and optional256-entry palette.
This is a software contract, not target timing/resource evidence.
"""
from pathlib import Path
import struct
import sys
import time
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-game-hud-study'))
import hud_codec as hp

HEADER = struct.Struct('<4sBBHHHHHII')
U16 = struct.Struct('<H')
RAW, WORD_RUNS, INDEX_RUNS = 0, 1, 2


def _seal(body):
    return body + struct.pack('<I', zlib.crc32(body))


def _tokens(values, unit):
    """Greedy runs>=3, literals<=128, and no token crosses a row boundary."""
    out = bytearray()
    values = [int(v) for v in values]
    def run_at(i):
        end = i + 1
        while end < len(values) and end - i < 128 and values[end] == values[i]:
            end += 1
        return end - i
    def symbol(value):
        return bytes((value,)) if unit == 1 else U16.pack(value)
    i = 0
    while i < len(values):
        count = run_at(i)
        if count >= 3:
            out.append(0x80 | (count - 1))
            out.extend(symbol(values[i]))
            i += count
        else:
            begin = i
            i += count
            while i < len(values) and i - begin < 128:
                count = run_at(i)
                if count >= 3:
                    break
                i += min(count, 128 - (i - begin))
            out.append(i - begin - 1)
            for value in values[begin:i]:
                out.extend(symbol(value))
    return bytes(out)


def _decode_row(data, width, unit):
    values = []
    cursor = 0
    while cursor < len(data):
        tag = data[cursor]
        cursor += 1
        count = (tag & 127) + 1
        if len(values) + count > width:
            raise ValueError('HR01 row output overflow')
        repeat = bool(tag & 128)
        need = unit if repeat else count * unit
        if cursor + need > len(data):
            raise ValueError('HR01 truncated row token')
        raw = data[cursor:cursor + need]
        cursor += need
        symbols = list(raw) if unit == 1 else list(struct.unpack('<' + 'H' * (need // 2), raw))
        values.extend(symbols * count if repeat else symbols)
    if len(values) != width:
        raise ValueError('HR01 row output underflow')
    return values


def encode_modes(rgb, rect):
    """Encode bounded candidates from current pixels; pay all attempted work."""
    started = time.perf_counter_ns()
    a = hp.gm.ft._check_rgb(rgb)
    h, w = a.shape[:2]
    x, y, rw, rh = hp._rect(rect, w, h)
    words = hp.corpus.rgb565(a[y:y+rh, x:x+rw])
    modes = {}
    def frame(mode, palette, payload):
        count = len(palette) // 2
        return _seal(HEADER.pack(b'HR01', 1, mode, x, y, rw, rh, count, rw*rh, len(payload)) + palette + payload)
    modes[RAW] = frame(RAW, b'', words.astype('<u2').tobytes())
    payload = bytearray()
    for row in words:
        tokens = _tokens(row, 2)
        payload.extend(U16.pack(len(tokens)))
        payload.extend(tokens)
    modes[WORD_RUNS] = frame(WORD_RUNS, b'', bytes(payload))
    palette, indices = np.unique(words, return_inverse=True)
    if len(palette) <= 256:
        indices = indices.reshape(rh, rw)
        payload = bytearray()
        for row in indices:
            tokens = _tokens(row, 1)
            payload.extend(U16.pack(len(tokens)))
            payload.extend(tokens)
        modes[INDEX_RUNS] = frame(INDEX_RUNS, palette.astype('<u2').tobytes(), bytes(payload))
    mode = min(modes, key=lambda k: (len(modes[k]), k))
    return modes[mode], {
        'selected_mode': mode,
        'colors': len(palette),
        'attempts': [{'mode': k, 'bytes': len(packet)} for k, packet in modes.items()],
        'candidate_count': len(modes),
        'all_candidate_service_ms': (time.perf_counter_ns()-started)/1e6,
        'source_pixels': rw*rh,
    }


def decode(packet, width, height):
    hp.gm.roi.geometry(width, height)
    if type(packet) is not bytes or len(packet) < HEADER.size + 4:
        raise ValueError('HR01 patch type/truncation')
    magic, version, mode, x, y, w, h, colors, pixels, length = HEADER.unpack_from(packet)
    hp._rect((x,y,w,h), width, height)
    if magic != b'HR01' or version != 1 or mode not in (RAW, WORD_RUNS, INDEX_RUNS) or pixels != w*h:
        raise ValueError('HR01 patch fields')
    if len(packet) != HEADER.size + colors*2 + length + 4:
        raise ValueError('HR01 exact patch length')
    if colors > min(256, pixels) or length > h*(2+3*w):
        raise ValueError('HR01 allocation/payload bound')
    if zlib.crc32(packet[:-4]) != struct.unpack('<I',packet[-4:])[0]:
        raise ValueError('HR01 CRC')
    start = HEADER.size
    palette = np.frombuffer(packet[start:start+colors*2], '<u2')
    payload = packet[start+colors*2:-4]
    if mode == RAW:
        if colors or length != pixels*2:
            raise ValueError('HR01 raw geometry/palette')
        words = np.frombuffer(payload, '<u2').reshape(h,w).copy()
    else:
        if mode == WORD_RUNS and colors:
            raise ValueError('HR01 word-run palette')
        if mode == INDEX_RUNS and (not colors or (colors>1 and np.any(palette[1:] <= palette[:-1]))):
            raise ValueError('HR01 sorted unique palette')
        cursor = 0
        rows = []
        for _ in range(h):
            if cursor+2 > len(payload):
                raise ValueError('HR01 missing row length')
            n = U16.unpack_from(payload,cursor)[0]
            cursor += 2
            if n == 0 or n > 3*w or cursor+n > len(payload):
                raise ValueError('HR01 row byte bounds')
            rows.append(_decode_row(payload[cursor:cursor+n],w,1 if mode == INDEX_RUNS else 2))
            cursor += n
        if cursor != len(payload):
            raise ValueError('HR01 trailing rows')
        codes = np.asarray(rows,np.uint16)
        if mode == INDEX_RUNS:
            if np.any(codes >= colors) or not np.array_equal(np.unique(codes),np.arange(colors)):
                raise ValueError('HR01 invalid/unused palette index')
            words = palette[codes].copy()
        else:
            words = codes
    words.setflags(write=False)
    return {'rect':(x,y,w,h), 'mode':mode, 'colors':colors, 'words':words, 'bytes':len(packet)}


def choose_patch(rgb, rect):
    """Actual-byte choice across frozen HP01 and all HR01 candidates."""
    started = time.perf_counter_ns()
    legacy = hp.encode_patch(rgb,rect)
    row, info = encode_modes(rgb,rect)
    chosen = row if len(row) < len(legacy) else legacy
    return chosen, {**info, 'hp01_bytes':len(legacy), 'hr01_bytes':len(row),
                    'chosen_format':chosen[:4].decode(), 'chosen_bytes':len(chosen),
                    'complete_search_ms':(time.perf_counter_ns()-started)/1e6}


def decode_any(packet,width,height):
    if type(packet) is bytes and packet[:4] == b'HP01':
        return hp.decode_patch(packet,width,height)
    return decode(packet,width,height)


FRAME = struct.Struct('<4sBBIHHI')


def wrap(base, patches, width, height):
    """HG01 wrapper, emitted from trusted encoder outputs; receiver validates all."""
    hp.gm.roi.geometry(width,height)
    if type(base) is not bytes or len(base) < hp.gm.HEADER.size+4:
        raise ValueError('HG01 base type/length')
    if type(patches) not in (tuple,list) or len(patches)>4:
        raise ValueError('HG01 patch count')
    rects=[]
    for packet in patches:
        if type(packet) is not bytes or len(packet)<HEADER.size+4 or packet[:4] not in (b'HP01',b'HR01'):
            raise ValueError('HG01 patch type/profile')
        fields=HEADER.unpack_from(packet)
        rects.append(hp._rect(fields[3:7],width,height))
    hp._disjoint(rects)
    section=b''.join(struct.pack('<I',len(p))+p for p in patches)
    return _seal(FRAME.pack(b'HG01',1,len(patches),len(base),width,height,len(section))+base+section)


def parse_frame(packet,epoch):
    if type(packet) is not bytes or len(packet)<FRAME.size+4:
        raise ValueError('HG01 frame type/length')
    magic,version,count,nbase,w,h,npatch=FRAME.unpack_from(packet)
    hp.gm.roi.geometry(w,h)
    if (magic!=b'HG01' or version!=1 or count>4 or not hp.gm.HEADER.size+4<=nbase<=hp._base_bound(w,h)
        or len(packet)!=FRAME.size+4+nbase+npatch
        or npatch>3*w*h+4*(4+HEADER.size+4+512+2*h)):
        raise ValueError('HG01 geometry/length/profile')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:
        raise ValueError('HG01 CRC')
    base=packet[FRAME.size:FRAME.size+nbase]
    fields=hp.gm.HEADER.unpack_from(base)
    if fields[3]!=epoch or fields[6:8]!=(w,h):
        raise ValueError('HG01 base geometry/session')
    # Patch validation must finish first. The atomic stateful GM01 receiver
    # then validates/decodes its base exactly once, before committing state.
    # This preflight does not claim that coefficient bytes are valid yet.
    meta={'frame_id':fields[4],'width':w,'height':h,'epoch':epoch}
    pos=FRAME.size+nbase;raw=[];rects=[]
    for _ in range(count):
        if pos+4>len(packet)-4:
            raise ValueError('HG01 missing patch length')
        length=struct.unpack_from('<I',packet,pos)[0];pos+=4
        if length<HEADER.size+4 or pos+length>len(packet)-4:
            raise ValueError('HG01 patch byte bounds')
        p=packet[pos:pos+length];pos+=length
        if p[:4] not in (b'HP01',b'HR01'):
            raise ValueError('HG01 patch profile')
        rects.append(hp._rect(HEADER.unpack_from(p)[3:7],w,h));raw.append(p)
    if pos!=len(packet)-4:
        raise ValueError('HG01 trailing patch bytes')
    # Bound total decoded patch area before allocating any patch words.
    hp._disjoint(rects)
    patches=[decode_any(p,w,h) for p in raw]
    return base,patches,meta


class Receiver:
    def __init__(self,epoch=1):
        self.epoch=epoch
        self.base=hp.gm.Receiver(epoch)

    def receive(self,packet):
        base,patches,meta=parse_frame(packet,self.epoch)
        rgb,info=self.base.receive(base)
        words=hp.corpus.rgb565(rgb)
        for p in patches:
            x,y,w,h=p['rect'];words[y:y+h,x:x+w]=p['words']
        return hp.corpus.expand565(words), {**info,'wrapper_bytes':len(packet),
            'patches':[{k:v for k,v in p.items() if k!='words'} for p in patches],
            'base_frame_id':meta['frame_id']}
