"""Exact arithmetic envelope, not a CPU/ISA/RF execution or FPS simulation."""
from fractions import Fraction
HEADER=40;CHUNK=1024;MAX_FRAME=256*1024;FPS=30
IPV4_UDP_BYTES=28;CLOCKS=(40_000_000,20_000_000,16_000_000,10_000_000)
UNKNOWN_US=(25,100,500,1000);RESERVES_US=(0,5000,10000)
PERIOD_US=Fraction(1_000_000,FPS)

def integer(value,name,minimum=0,maximum=None):
    if type(value)is not int or value<minimum or(maximum is not None and value>maximum):raise ValueError(name)
    return value

def fragment_lengths(length,chunk=CHUNK):
    integer(length,'bounded nonempty payload',1,MAX_FRAME);integer(chunk,'bounded fragment payload',1,CHUNK)
    count=(length+chunk-1)//chunk;return (chunk,)*(count-1)+(length-(count-1)*chunk,)

def fraction(value):
    value=Fraction(value);return dict(numerator=value.numerator,denominator=value.denominator,value=float(value))

def frame(length,header=HEADER,chunk=CHUNK):
    integer(header,'nonnegative illustrative header')
    parts=fragment_lengths(length,chunk);n=len(parts)
    payload_clocks=2*length;command_address_clocks=16*n;total=payload_clocks+command_address_clocks
    udp_payload=length+header*n;l3=udp_payload+IPV4_UDP_BYTES*n
    return dict(payload_bytes=length,fragment_payload_limit=chunk,fragments=n,tail_payload_bytes=parts[-1],
        header_bytes=header,udp_payload_bytes=udp_payload,ipv4_udp_header_bytes=IPV4_UDP_BYTES*n,L3_IPv4_UDP_bytes=l3,
        nominal_payload_bits_per_second_at30=length*8*FPS,nominal_L3_bits_per_second_at30=l3*8*FPS,
        source_level_crc_bit_rounds=8*length,payload_QSPI_clocks=payload_clocks,command_address_QSPI_clocks=command_address_clocks,total_QSPI_clocks=total)

def qspi_us(length,clock_hz,chunk=CHUNK):
    integer(clock_hz,'positive assumed clock',1);parts=fragment_lengths(length,chunk)
    return Fraction((2*length+16*len(parts))*1_000_000,clock_hz)

def residual(length,clock_hz=40_000_000,reserve_us=0,chunk=CHUNK):
    integer(reserve_us,'assumed other-stage reserve')
    parts=fragment_lengths(length,chunk);left=PERIOD_US-qspi_us(length,clock_hz,chunk)-reserve_us
    return left,left/len(parts)

def scenario(length,clock_hz,unknown_us_per_fragment,reserve_us=0,chunk=CHUNK):
    integer(unknown_us_per_fragment,'assumed combined unknown work')
    integer(reserve_us,'assumed other-stage reserve')
    n=len(fragment_lengths(length,chunk));elapsed=qspi_us(length,clock_hz,chunk)+n*unknown_us_per_fragment+reserve_us
    margin=PERIOD_US-elapsed
    return elapsed,margin,margin>=0
