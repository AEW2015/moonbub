"""CP25 atomic laboratory composition of frozen GM25 and exact HU25/HD25.

Two logical reconstructed base banks, one last-accepted HUD, synchronous write
drain/vblank gates and real CRC/tag-bound ACK bytes. This is a host model only.
"""
from pathlib import Path
from dataclasses import dataclass
import hashlib
import importlib.util
import struct
import sys
import time
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = _load('cp25_frozen_gm25', HERE.parent / 'python-game-base-motion-v25-study/model.py')
hud_codec = _load('cp25_frozen_hd25', HERE.parent / 'python-game-hud-motion-v25-study/model.py')
ui = base.C._ui()
CAP = 49152
NO_REF = base.NO_REF
ZERO = bytes(16)
PAIR = struct.Struct('<4sBBIIBBII16s16s')
HUD = struct.Struct('<4sBBIIIHH16s16s4I4B16H')
ACK = struct.Struct('<4sBII16s16s16s')
KEY, PUBLISH, NO_SLOT = 1, 2, 255


def seal(body):
    return body + struct.pack('<I', zlib.crc32(body))


def digest(data):
    return hashlib.sha256(data).digest()[:16]


def _checked(data, minimum, maximum, label):
    if type(data) is not bytes or not minimum <= len(data) <= maximum:
        raise ValueError(label + ' bounded bytes')
    if zlib.crc32(data[:-4]) != struct.unpack('<I', data[-4:])[0]:
        raise ValueError(label + ' CRC')


def _identity(epoch, frame):
    if not base._id(epoch) or not base._id(frame):
        raise ValueError('bounded epoch/frame identity')


def _validated_hud(patches, width, height):
    if type(patches) not in (tuple, list) or len(patches) > 4:
        raise ValueError('bounded HUD tuples')
    result, rects = [], []
    for item in patches:
        if type(item) is not dict or 'rect' not in item or 'words' not in item:
            raise ValueError('decoded HUD shape')
        rect = ui.hp._rect(tuple(item['rect']), width, height)
        words = item['words']
        if not isinstance(words, np.ndarray) or words.dtype != np.uint16 or words.shape != (rect[3], rect[2]):
            raise ValueError('decoded HUD word bounds')
        frozen = words.copy(); frozen.setflags(write=False)
        result.append(dict(rect=rect, words=frozen))
        rects.append(rect)
    ui.hp._disjoint(rects)
    return tuple(result)


def hud_tag(patches, width=720, height=480):
    patches = _validated_hud(patches, width, height)
    body = bytearray(struct.pack('<HHB', width, height, len(patches)))
    for patch in patches:
        body.extend(struct.pack('<4H', *patch['rect']))
        body.extend(patch['words'].astype('<u2', copy=False).tobytes())
    return digest(bytes(body))


def _parse_hud(packet):
    _checked(packet, HUD.size + 4, CAP, 'HU25')
    v = HUD.unpack_from(packet)
    magic, version, count, epoch, frame, refid, width, height, ref_tag, out_tag = v[:10]
    lengths, types, rectangle_values = v[10:14], v[14:18], v[18:]
    _identity(epoch, frame); base.roi.geometry(width, height)
    if magic != b'HU25' or version != 1 or count > 4 or out_tag == ZERO:
        raise ValueError('HU25 profile')
    if refid == NO_REF:
        if ref_tag != ZERO:
            raise ValueError('HU25 independent reference tag')
    elif not base._id(refid) or refid >= frame or ref_tag == ZERO:
        raise ValueError('HU25 past reference identity')
    if len(packet) != HUD.size + 4 + sum(lengths):
        raise ValueError('HU25 exact payload lengths')
    rectangles, payloads = [], []
    pos = HUD.size
    for index, (length, kind) in enumerate(zip(lengths, types)):
        rect = tuple(rectangle_values[4 * index:4 * index + 4])
        if index >= count:
            if length or kind or any(rect):
                raise ValueError('HU25 unused slot padding')
            continue
        if kind not in (1, 2) or not 1 <= length <= CAP:
            raise ValueError('HU25 patch type/length')
        rect = ui.hp._rect(rect, width, height)
        rectangles.append(rect)
        payloads.append(packet[pos:pos + length]); pos += length
    ui.hp._disjoint(rectangles)
    return dict(epoch=epoch, frame_id=frame, reference_id=refid, width=width, height=height,
                reference_tag=ref_tag, reconstructed_tag=out_tag, rectangles=tuple(rectangles),
                types=tuple(types[:count]), payloads=tuple(payloads))


def encode_hud(patches, reference=None, *, epoch=1, frame_id=0, reference_id=NO_REF,
               motion=False, width=720, height=480):
    started = time.perf_counter_ns()
    _identity(epoch, frame_id); base.roi.geometry(width, height)
    if type(motion) is not bool:
        raise ValueError('HUD declared motion policy')
    current = ui.validate_patches(patches, width, height)
    if reference is None:
        if type(reference_id) is not int or reference_id != NO_REF:
            raise ValueError('HUD independent reference identity')
        ref, ref_tag = (), ZERO
    else:
        if not base._id(reference_id) or reference_id >= frame_id:
            raise ValueError('HUD past reference identity')
        ref = _validated_hud(reference, width, height)
        ref_tag = hud_tag(ref, width, height)
    by_rect = {p['rect']: p['words'] for p in ref}
    payloads, types, details = [], [], []
    for full, item in zip(patches, current):
        hh, ww = item['words'].shape
        eligible = (ww <= hud_codec.old.MAX_WIDTH and hh <= hud_codec.old.MAX_HEIGHT
                    and hh * ww <= hud_codec.MAX_WORDS)
        if eligible:
            hd, info = hud_codec.encode_with_info(item['words'], by_rect.get(tuple(item['rect'])), motion=motion)
        else:
            hd, info = None, dict(not_attempted='outside-HD25-bounded-patch-domain', encode_ms=0.)
        use_hd = hd is not None and len(hd) < len(full)
        payloads.append(hd if use_hd else full); types.append(2 if use_hd else 1)
        details.append(dict(rect=tuple(item['rect']), selected='HD25' if use_hd else full[:4].decode(),
                            full_bytes=len(full), hd25_bytes=len(hd) if hd is not None else None, hd25_work=info))
    count = len(payloads)
    lengths = [len(v) for v in payloads] + [0] * (4 - count)
    rectangle_values = [v for patch in current for v in patch['rect']] + [0] * (16 - 4 * count)
    out_tag = hud_tag(current, width, height)
    body = HUD.pack(b'HU25', 1, count, epoch, frame_id, reference_id, width, height, ref_tag,
                    out_tag, *lengths, *(types + [0] * (4 - count)), *rectangle_values) + b''.join(payloads)
    packet = seal(body)
    if len(packet) > CAP:
        raise ValueError('HU25 complete cap')
    return packet, dict(packet_bytes=len(packet), fixed_bytes=HUD.size + 4, patches=details,
                        reference_tag=ref_tag.hex(), reconstructed_tag=out_tag.hex(),
                        encode_wall_ms=(time.perf_counter_ns() - started) / 1e6)


def decode_hud(packet, reference=None, *, expected_epoch=None, expected_reference_id=None):
    meta = _parse_hud(packet)
    width, height = meta['width'], meta['height']
    if expected_epoch is not None and meta['epoch'] != expected_epoch:
        raise ValueError('HU25 wrong epoch')
    if meta['reference_id'] == NO_REF:
        ref = ()
    else:
        if expected_reference_id != meta['reference_id'] or reference is None:
            raise ValueError('HU25 exact reference ID required')
        ref = _validated_hud(reference, width, height)
        if hud_tag(ref, width, height) != meta['reference_tag']:
            raise ValueError('HU25 exact reference content')
    by_rect = {p['rect']: p['words'] for p in ref}
    decoded = []
    for rect, kind, payload in zip(meta['rectangles'], meta['types'], meta['payloads']):
        if kind == 1:
            item = ui.validate_patches((payload,), width, height)[0]
            if tuple(item['rect']) != rect:
                raise ValueError('HU25 full-patch rectangle binding')
            words = item['words']
        else:
            words = hud_codec.decode(payload, by_rect.get(rect))
            if words.shape != (rect[3], rect[2]):
                raise ValueError('HU25 HD25 rectangle shape')
        decoded.append(dict(rect=rect, words=words))
    result = _validated_hud(decoded, width, height)
    if hud_tag(result, width, height) != meta['reconstructed_tag']:
        raise ValueError('HU25 reconstructed content tag')
    return result, meta


def parse_pair(packet):
    _checked(packet, PAIR.size + HUD.size + base.HEADER.size + 12, CAP, 'CP25')
    magic, version, flags, epoch, frame, source, destination, nb, nh, bt, ht = PAIR.unpack_from(packet)
    _identity(epoch, frame)
    if magic != b'CP25' or version != 1 or flags not in (0, KEY | PUBLISH, PUBLISH):
        raise ValueError('CP25 profile')
    key, publish = bool(flags & KEY), bool(flags & PUBLISH)
    if key:
        if source != NO_SLOT or destination != 0:
            raise ValueError('CP25 key bank rule')
    elif source not in (0, 1) or destination != (1 - source if publish else NO_SLOT):
        raise ValueError('CP25 P bank rule')
    if nb < base.HEADER.size + 7 or nh < HUD.size + 4 or len(packet) != PAIR.size + nb + nh + 4:
        raise ValueError('CP25 exact inner lengths')
    b = packet[PAIR.size:PAIR.size + nb]; h = packet[PAIR.size + nb:-4]
    if digest(b) != bt or digest(h) != ht:
        raise ValueError('CP25 inner SHA binding')
    bm, hm = base.parse(b, expected_epoch=epoch), _parse_hud(h)
    if (bm['frame_id'] != frame or hm['frame_id'] != frame or hm['epoch'] != epoch
            or bm['key'] != key or (bm['width'], bm['height']) != (hm['width'], hm['height'])
            or key and hm['reference_id'] != NO_REF):
        raise ValueError('CP25 coherent inner identities')
    return dict(epoch=epoch, frame_id=frame, source_slot=source, destination_slot=destination,
                key=key, publish=publish, base=b, hud=h, base_meta=bm, hud_meta=hm,
                pair_tag=digest(packet))


def encode_pair(base_packet, hud_packet, *, epoch, frame_id, source_slot=NO_SLOT,
                destination_slot=0, publish=True, key=True):
    if type(publish) is not bool or type(key) is not bool:
        raise ValueError('CP25 declared key/publish flags')
    _identity(epoch, frame_id)
    if type(base_packet) is not bytes or type(hud_packet) is not bytes:
        raise ValueError('CP25 immutable inner bytes')
    if type(source_slot) is not int or type(destination_slot) is not int or not 0 <= source_slot <= 255 or not 0 <= destination_slot <= 255:
        raise ValueError('CP25 bounded slots')
    packet = seal(PAIR.pack(b'CP25', 1, (KEY if key else 0) | (PUBLISH if publish else 0), epoch,
                            frame_id, source_slot, destination_slot, len(base_packet), len(hud_packet),
                            digest(base_packet), digest(hud_packet)) + base_packet + hud_packet)
    parse_pair(packet)
    return packet


def validate_ack(ack, pair):
    _checked(ack, ACK.size + 4, ACK.size + 4, 'JA25')
    meta = parse_pair(pair)
    magic, version, epoch, frame, pt, bt, ht = ACK.unpack_from(ack)
    if (magic != b'JA25' or version != 1 or epoch != meta['epoch'] or frame != meta['frame_id']
            or pt != meta['pair_tag'] or bt != meta['base_meta']['reconstructed_tag']
            or ht != meta['hud_meta']['reconstructed_tag']):
        raise ValueError('JA25 exact pair/output binding')
    return dict(epoch=epoch, frame_id=frame, source_slot=meta['source_slot'],
                destination_slot=meta['destination_slot'], published=meta['publish'],
                pair_tag=pt.hex(), base_tag=bt.hex(), hud_tag=ht.hex())


@dataclass(frozen=True)
class Bank:
    frame_id: int
    tag: bytes
    planes: tuple


class Receiver:
    def __init__(self, epoch=1, width=720, height=480):
        _identity(epoch, 0); base.roi.geometry(width, height)
        self.epoch, self.width, self.height = epoch, width, height
        self.banks = (None, None)
        self.hud, self.hud_id, self.hud_tag = (), NO_REF, ZERO
        self.last_frame_id, self.last_ack = -1, None

    def receive(self, pair, write_drained=True, vblank=True):
        if type(write_drained) is not bool or type(vblank) is not bool or not write_drained or not vblank:
            raise ValueError('CP25 modeled write-drain/vblank gate')
        meta = parse_pair(pair)
        bm = meta['base_meta']
        if meta['epoch'] != self.epoch or meta['frame_id'] <= self.last_frame_id:
            raise ValueError('CP25 epoch/monotonic presentation')
        if (bm['width'], bm['height']) != (self.width, self.height):
            raise ValueError('CP25 fixed receiver canvas')
        if meta['key']:
            rebuilt, _ = base.decode(meta['base'], expected_epoch=self.epoch)
            decoded_hud, hm = decode_hud(meta['hud'], expected_epoch=self.epoch)
        else:
            source = self.banks[meta['source_slot']]
            if source is None or source.frame_id != bm['reference_id'] or source.tag != bm['reference_tag']:
                raise ValueError('CP25 actual source-bank identity')
            rebuilt, _ = base.decode(meta['base'], source.planes, expected_epoch=self.epoch,
                                     expected_reference_id=source.frame_id)
            decoded_hud, hm = decode_hud(meta['hud'], self.hud, expected_epoch=self.epoch,
                                         expected_reference_id=self.hud_id)
        # Everything above is private validation. Construct ACK before the one
        # modeled atomic publication; no failure path changes receiver state.
        ack = seal(ACK.pack(b'JA25', 1, self.epoch, meta['frame_id'], meta['pair_tag'],
                            bm['reconstructed_tag'], hm['reconstructed_tag']))
        banks = list(self.banks)
        if meta['key']:
            banks = [Bank(meta['frame_id'], bm['reconstructed_tag'], rebuilt), None]
        elif meta['publish']:
            banks[meta['destination_slot']] = Bank(meta['frame_id'], bm['reconstructed_tag'], rebuilt)
        self.banks = tuple(banks)
        self.hud, self.hud_id, self.hud_tag = decoded_hud, meta['frame_id'], hm['reconstructed_tag']
        self.last_frame_id, self.last_ack = meta['frame_id'], ack
        return rebuilt, decoded_hud, ack


def overlay(base_rgb, decoded_hud):
    return ui.apply_patches(base_rgb, decoded_hud)
