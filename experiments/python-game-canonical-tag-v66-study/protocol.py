"""Two EXPLICIT negotiated canonical-only SHA128 profiles, no old autoaccept."""
import hashlib,json,struct,zlib
import numpy as np
import helpers as h
OUTER=h.f.HEADER
INNER=struct.Struct('<4sBBIIIHHBB16sIIIII')
PROFILES={
    'CS66':dict(outer=b'CS66',inner=b'GS66',domain='geometry+planar little-endian int16',
        profile=hashlib.sha256(b'CS66:canonical-only-cached-ref-sha128-i16-v1:'+json.dumps(h.f.f.n.RECTS,separators=(',',':')).encode()).digest()[:16]),
    'CU66':dict(outer=b'CU66',inner=b'GU66',domain='geometry+planar validated uint8',
        profile=hashlib.sha256(b'CU66:canonical-only-cached-ref-sha128-u8-v1:'+json.dumps(h.f.f.n.RECTS,separators=(',',':')).encode()).digest()[:16])}
def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def tag_u8(planes):
    shapes=((480,720),(240,360),(240,360))
    if type(planes)not in(tuple,list)or len(planes)!=3:raise ValueError('three fixed canonical planes')
    for plane,shape in zip(planes,shapes,strict=True):
        if not isinstance(plane,np.ndarray)or plane.shape!=shape or plane.dtype.kind not in('i','u')or np.any(plane<0)or np.any(plane>255):
            raise ValueError('CU66 integer0..255 canonical domain; no truncation')
    digest=hashlib.sha256(struct.pack('<HH',720,480))
    for plane in planes:digest.update(plane.astype(np.uint8,copy=False).tobytes())
    return digest.digest()[:16]
def canonical_tag(planes,profile='CS66'):
    if profile=='CS66':return h.m.C.reference_tag(planes)
    if profile=='CU66':return tag_u8(planes)
    raise ValueError('explicit negotiated profile')

def convert(packet,profile='CS66',*,reference=None,normalized=None):
    """Offline adapter after frozen43 preflight validation; no receive fallback."""
    if profile not in PROFILES:raise ValueError('explicit profile')
    if type(packet)is not bytes or not h.oldrx.HEADER.size+8<=len(packet)<=49152:raise ValueError('bounded old CS38')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('old outer CRC')
    outer=list(OUTER.unpack_from(packet));nb,nh=outer[11:13]
    if outer[0]!=b'CS38'or outer[8]!=h.oldrx.PROFILE or len(packet)!=OUTER.size+nb+nh+4:raise ValueError('old explicitCS38profile/lengths')
    inner=packet[OUTER.size:OUTER.size+nb]
    if len(inner)<h.m.HEADER.size+7 or zlib.crc32(inner[:-4])!=struct.unpack('<I',inner[-4:])[0]:raise ValueError('old inner CRC')
    fields=list(h.m.HEADER.unpack_from(inner))
    if fields[0]!=b'GS38'or fields[4:8]!=outer[4:8]or fields[10]!=outer[9]:raise ValueError('old identities')
    evidence=dict(old_base_tag=fields[11].hex(),old_reference_tag=outer[9].hex(),old_output_tag=outer[10].hex())
    del fields[11];spec=PROFILES[profile];fields[0]=spec['inner']
    if profile=='CU66':
        if normalized is None or(bool(outer[2]&1))!=(reference is None):raise ValueError('CU66 requires verified canonical output/reference')
        outer[9]=bytes(16)if reference is None else tag_u8(reference);outer[10]=tag_u8(normalized);fields[10]=outer[9]
    newinner=seal(INNER.pack(*fields)+inner[h.m.HEADER.size:-4])
    outer[0]=spec['outer'];outer[8]=spec['profile'];outer[11]=len(newinner)
    result=seal(OUTER.pack(*outer)+newinner+packet[OUTER.size+nb:-4])
    assert len(result)==len(packet)-16
    return result,evidence

def hash_demand(sample_bytes=2,calls=1,clock_hz=100_000_000):
    if type(sample_bytes)is not int or sample_bytes not in(1,2)or type(calls)is not int or calls<1 or type(clock_hz)is not int or clock_hz<=0:raise ValueError('fixed hash budget assumptions')
    preimage=4+720*480*3//2*sample_bytes;blocks=(preimage+9+63)//64;rounds=blocks*64*calls
    return dict(sample_bytes=sample_bytes,calls=calls,preimage_bytes_per_tag=preimage,padded_SHA256_blocks_per_tag=blocks,
        rounds_per_block=64,assumed_rounds_per_cycle=1,total_round_cycles=rounds,assumed_clock_hz=clock_hz,
        assumed_serial_ms=1000*rounds/clock_hz,physical_timing_or_RTL_fit_proven=False)
