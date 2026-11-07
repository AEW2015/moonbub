#!/usr/bin/env python3
"""Independent tile geometry, source-derived prefill order and line-level cache model."""
from array import array
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def mapping():
    forward=array('I',[0])*518400
    inverse=array('I',[0])*518400
    used=bytearray(518400)
    for base,width,height in ((0,720,480),(345600,360,240),(432000,360,240)):
        # Tile-major enumeration is independent of the RTL's quotient formula.
        physical=base
        for tile_y in range(0,height,8):
            for tile_x in range(0,width,8):
                for y in range(8):
                    for x in range(8):
                        logical=base+(tile_y+y)*width+tile_x+x
                        assert not used[logical]
                        used[logical]=1
                        forward[logical]=physical;inverse[physical]=logical
                        physical+=1
        assert physical==base+width*height
    assert all(used) and len(set(forward))==518400
    return forward,inverse

def schedule():
    # Direct interval model: prefill rows0/1 before Y0, one extra chroma row
    # before each later even output row, then consume the whole luma row.
    byte_order=[]
    last_line=[-1,-1,-1]
    addresses=[]
    for y in range(480):
        chroma_rows=(0,1) if y==0 else (y//2+1,) if y%2==0 and y<478 else ()
        intervals=[]
        for cy in chroma_rows:
            intervals.extend(((1,345600+360*cy,360),(2,432000+360*cy,360)))
        intervals.append((0,y*720,720))
        for plane,start,count in intervals:
            for a in range(start,start+count):
                byte_order.append(a)
                line=a&~15
                if last_line[plane]!=line:
                    addresses.append(line);last_line[plane]=line
    assert len(byte_order)==518400 and len(addresses)==32400
    assert len(set(byte_order))==518400 and set(addresses)==set(range(0,518400,16))
    return addresses,byte_order

def cache(frame,addresses,forward,inverse,retain):
    physical=bytes(frame[i] for i in inverse)
    tags=[None,None,None]
    fragments=[{}, {}, {}]
    scratch=None
    reads=row_hits=scratch_hits=0
    max_valid=0
    for a in addresses:
        if not retain:scratch=None
        result=bytearray()
        for logical in (a,a+8):
            plane=0 if logical<345600 else 1 if logical<432000 else 2
            base,width=((0,720),(345600,360),(432000,360))[plane]
            y,x=divmod(logical-base,width)
            tileburst=forward[logical]&~15
            if retain and tags[plane]==y and x in fragments[plane]:
                value=fragments[plane][x];row_hits+=1
            else:
                if scratch!=tileburst:
                    reads+=1;scratch=tileburst
                    if retain and y%2==0:
                        if tags[plane]!=y+1:
                            fragments[plane]={};tags[plane]=y+1
                        fragments[plane][x]=physical[tileburst+8:tileburst+16]
                else:scratch_hits+=1
                offset=forward[logical]-tileburst
                value=physical[tileburst+offset:tileburst+offset+8]
            assert value==frame[logical:logical+8]
            result.extend(value)
            max_valid=max(max_valid,sum(map(len,fragments)))
            assert max_valid<=180
        assert result==frame[a:a+16]
    assert reads==(32400 if retain else 64800)
    return dict(physical_reads=reads,row_hits=row_hits,scratch_hits=scratch_hits,
                valid_fragment_high_water=max_valid,data_storage_bytes=1472 if retain else 32)

def main():
    model=json.loads((AREA/'prefill-results.json').read_text())
    assert model['generator_sha256']==sha(AREA/'prefill_model.py')
    for name,h in model['source_sha256'].items():assert sha(ROOT/name)==h,name
    vector=ROOT/model['vector']['path']
    assert sha(vector)==model['vector']['gzip_sha256']
    raw=gzip.decompress(vector.read_bytes())
    assert hashlib.sha256(raw).hexdigest()==model['vector']['raw_sha256']
    expected,order=schedule()
    actual=[int(v,16) for v in raw.splitlines()]
    assert actual==expected
    forward,inverse=mapping()
    frames={}
    inp=ROOT/'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz'
    assert sha(inp)==model['input_sha256']
    with gzip.open(inp,'rt') as stream:
        for line in stream:
            name,profile,hx=line.rstrip().split('\t')
            if name in ('actual_001','actual_006') and profile=='0':frames[name]=bytes.fromhex(hx)
    checks={}
    for name,frame in frames.items():
        assert hashlib.sha256(bytes(frame[i] for i in order)).hexdigest()==model['frames'][name]['consumer_response_sha256']
        checks[name]={str(retain):cache(frame,actual,forward,inverse,retain) for retain in (0,1)}
    assert len(checks)==2
    result=dict(status='PASS_INDEPENDENT_PREFILL_GEOMETRY_AND_LINE_CACHE_MODEL',
                verifier_sha256=sha(Path(__file__)),prefill_report_sha256=sha(AREA/'prefill-results.json'),
                exact_source_byte_schedule_size=len(order),logical_line_requests=len(actual),
                mapped_canonical_bytes=518400,frames=checks,
                scope='Source-derived client order, exact native canonical bytes and fixed-size cache semantics; no controller arbitration or hardware performance result.')
    (AREA/'audit-models.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
if __name__=='__main__':main()
