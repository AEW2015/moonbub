#!/usr/bin/env python3
"""Independent retained-data checks for actual re-encoded context observations."""
from array import array
import gzip,hashlib,importlib.util,json,struct,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
FIELDS=('decisions','renorm','stream_bytes','rice_values','events','raw_bytes','header_bytes','crc_bytes','emits','raw_bits','prob_init')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def main():
    index=json.loads((AREA/'index.json').read_text());assert index['record_count']==914 and index['native_sources']==457
    for name,digest in index['source_sha256'].items():assert sha(ROOT/name)==digest,('source',name)
    path=AREA/index['data']['path'];assert sha(path)==index['data']['gzip_sha256']
    residual=load('cu86_verify_residual',ROOT/'experiments/python-gamebub-v85/residual/data.py')
    native=load('cu86_verify_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    raw=hashlib.sha256();records=chunks=0;totals={str(c):[[0]*11 for _ in range(5)] for c in (256,65536)}
    with gzip.open(path,'rb') as stream:
        for original,picture in zip(residual.iter_frames(),native.iter_frames(),strict=True):
            for cap in (256,65536):
                prefix=stream.read(4);n,=struct.unpack('<I',prefix);assert 1<=n<=262144
                head=stream.read(n);payload=stream.read(8100*55*4);assert len(head)==n and len(payload)==8100*55*4
                raw.update(prefix);raw.update(head);raw.update(payload);meta=json.loads(head)
                for key in ('cohort','fid','ordinal','key','canonical_coefficients_sha256','canonical_sha256','hud_sha256','display_sha256'):assert meta[key]==original[key],key
                assert meta['cap']==cap and hashlib.sha256(payload).hexdigest()==meta['work_sha256']
                expected=index['frames'][records];assert meta==expected
                words=array('I');words.frombytes(payload)
                if sys.byteorder!='little':words.byteswap()
                frame_totals=[[sum(words[part*11+i::55]) for i in range(11)] for part in range(5)]
                assert dict(zip(FIELDS,frame_totals[0]))==meta['shared_totals']
                assert [dict(zip(FIELDS,row)) for row in frame_totals[1:]]==meta['context_totals']
                assert frame_totals[0][8]==8100 and all(row[8]==0 for row in frame_totals[1:])
                stats=original['variant_stats'][str(cap)]
                assert [row[0] for row in frame_totals[1:]]==stats['attempted_encoder_decisions']
                assert [row[1] for row in frame_totals[1:]]==stats['attempted_encoder_renorm']
                expected_chunks=[];offset=0;stream_bytes=[0]*4;stream_bits=[0]*4;event_counts=[0]*3;encoded_tiles=0
                for axis,total in enumerate((5400,1350,1350)):
                    indices=[offset+t for t in range(total) if not picture['hidden_mask'][offset+t] and (original['key'] or original['zero_mask'][offset+t]=='0')]
                    cursor=0
                    for chunk in original['variants'][str(cap)][axis]:
                        blocks=chunk['blocks'];packet=chunk['data'];chunks+=1;encoded_tiles+=blocks
                        assert zlib.crc32(packet[:-4])==struct.unpack('<I',packet[-4:])[0]
                        values=struct.unpack_from('<4sBBIHH4I3I',packet)
                        assert values[:6]==(b'AB38',1,0,blocks,1,0)
                        lengths=values[6:10];event_counts=[x+y for x,y in zip(event_counts,values[10:13])]
                        pos=42
                        for context,size in enumerate(lengths):
                            bits=struct.unpack_from('<I',packet,pos+2)[0]
                            assert size==6+(bits+7)//8
                            stream_bytes[context]+=(bits+7)//8;stream_bits[context]+=bits;pos+=size
                        assert pos==len(packet)-4
                        first=indices[cursor]
                        assert words[first*55+7]==len(packet) and words[first*55+6]==28
                        for context in range(4):assert words[first*55+11+context*11+10]==88
                        cursor+=blocks
                        expected_chunks.append(dict(axis=axis,blocks=blocks,bytes=len(packet),sha256=hashlib.sha256(packet).hexdigest()))
                    assert cursor==len(indices)
                    offset+=total
                assert meta['chunks']==expected_chunks
                assert frame_totals[0][7]==sum(c['bytes'] for c in expected_chunks)==stats['AB38_bytes']
                assert frame_totals[0][6]==28*len(expected_chunks)
                assert all(row[10]==88*len(expected_chunks) for row in frame_totals[1:])
                assert [row[2] for row in frame_totals[1:]]==stream_bytes
                assert [row[9] for row in frame_totals[1:]]==stream_bits
                assert frame_totals[1][3]==encoded_tiles and frame_totals[1][4]==0
                for c in range(3):assert frame_totals[c+2][4]==event_counts[c] and frame_totals[c+2][3]==2*event_counts[c]
                for tile in range(8100):
                    hidden=bool(picture['hidden_mask'][tile]);copy=not original['key'] and original['zero_mask'][tile]=='1' and not hidden
                    if hidden or copy:
                        assert list(words[tile*55:tile*55+55])==[0]*8+[1]+[0]*46
                for part in range(5):
                    for i in range(11):totals[str(cap)][part][i]+=frame_totals[part][i]
                records+=1
        assert not stream.read(1)
    assert records==914 and chunks==7432 and raw.hexdigest()==index['data']['raw_sha256']
    expected_totals={cap:dict(shared=dict(zip(FIELDS,v[0])),contexts=[dict(zip(FIELDS,row)) for row in v[1:]]) for cap,v in totals.items()}
    assert index['totals']==expected_totals
    result=dict(schema='cu66-v86-context-data-verification-v1',status='PASS',variant_records=records,native_sources=457,chunks=chunks,
                index_sha256=sha(AREA/'index.json'),data_sha256=sha(path),verifier_sha256=sha(Path(__file__)),
                validation=['Every source/chunk identity and compressed/raw/count hash checked.',
                            'Per-context decoded decisions/renorm exactly equal actual selected encoder counters.',
                            'Native AB38 lengths/CRCs/bit lengths/events and context initialization/fetch/termination totals match.',
                            'COPY/CONST entropy zero, one emit per canonical tile; full coefficient SHA is bound to native bridge parity.'],
                scope='Retained primitive observations, not measured FPGA cycles or a complete codec/display model.')
    (AREA/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('V86_REENCODED_CONTEXT_DATA_PASS records=914 chunks=7432 native_sources=457')


if __name__=='__main__':main()
