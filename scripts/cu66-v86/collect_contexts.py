#!/usr/bin/env python3
"""Observe actual residual-only AB38 chunks and canonical-scatter their work."""
from array import array
import datetime,gzip,hashlib,importlib.util,json,struct,subprocess,sys,tarfile,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v86/contexts'
FIELDS=('decisions','renorm','stream_bytes','rice_values','events','raw_bytes','header_bytes','crc_bytes','emits','raw_bits','prob_init')
CAPS=(256,65536);CONTAINER='gamebub-cu66-v69-build'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def exact(stream,n):
    data=stream.read(n)
    if len(data)!=n:raise ValueError(('native bridge output truncated',n,len(data)))
    return data


def main():
    if (AREA/'index.json').exists():raise FileExistsError('retained context index exists')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True);binary='/build/v86-contexts-'+stamp
    residual_index=ROOT/'experiments/python-gamebub-v85/residual/index.json'
    ri=json.loads(residual_index.read_text())
    sources=[Path(__file__).resolve(),AREA/'trace.hpp',AREA/'bridge.cpp',AREA/'data.py',residual_index,
             ROOT/'experiments/python-gamebub-v85/residual/data.py',
             ROOT/'experiments/python-gamebub-v85/residual'/ri['data']['path'],
             ROOT/'experiments/python-gamebub-v82/native/data.py',ROOT/'experiments/python-gamebub-v82/native/index.json']
    sources+=sorted((ROOT/'experiments/cu66-native-v69').glob('*.hpp'))
    sources+=sorted((ROOT/'experiments/python-gamebub-v82/native/data').glob('*.gz'))
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(out/'sources.tar.gz','w:gz') as tar:
        for p in sources:
            if p.suffix!='.gz':tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    commands=[];report=dict(schema='cu66-v86-reencoded-contexts-v1',status='FAIL',source_sha256=pins)
    started=time.monotonic();process=None
    def run(command,name):
        commands.append(command);r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        (out/name).write_text(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError((command,r.returncode))
    try:
        run(['docker','exec',CONTAINER,'g++','--version'],'compiler.txt')
        run(['docker','exec',CONTAINER,'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(AREA/'bridge.cpp'),'-o',binary],'compile.log')
        run(['docker','cp',CONTAINER+':'+binary,str(out/'bridge.bin')],'copy.log')
        residual=load('cu86_context_residual',ROOT/'experiments/python-gamebub-v85/residual/data.py')
        native=load('cu86_context_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
        command=['docker','exec','-i',CONTAINER,binary];commands.append(command)
        frames=[];raw=hashlib.sha256();global_totals={str(cap):[[0]*11 for _ in range(5)] for cap in CAPS};chunk_count=0
        with (out/'native.log').open('wb') as log:
            process=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log)
            with gzip.open(out/'data.bin.gz','wb') as output:
                for frame,original in zip(residual.iter_frames(),native.iter_frames(),strict=True):
                    for key in ('cohort','fid','ordinal','key','canonical_sha256','hud_sha256','display_sha256'):
                        assert frame[key]==original[key]
                    assert frame['zero_mask']==''.join(str(v) for v in original['zero_coeff_mask'])
                    for cap in CAPS:
                        # Native words per tile: shared11 then four contexts11.
                        words=array('I',[0])*(8100*55)
                        for tile in range(8100):words[tile*55+8]=1
                        coefficient_hash=hashlib.sha256();totals=[[0]*11 for _ in range(5)];chunks=[];offset=0
                        for axis,total in enumerate((5400,1350,1350)):
                            indices=[offset+t for t in range(total) if not original['hidden_mask'][offset+t] and (frame['key'] or frame['zero_mask'][offset+t]=='0')]
                            tile_coeff={};cursor=0
                            for chunk in frame['variants'][str(cap)][axis]:
                                blocks=chunk['blocks'];packet=chunk['data'];chunk_count+=1
                                process.stdin.write(struct.pack('<II',blocks,len(packet))+packet);process.stdin.flush()
                                got,=struct.unpack('<I',exact(process.stdout,4));assert got==blocks
                                coefficients=exact(process.stdout,blocks*128)
                                observed=array('I');observed.frombytes(exact(process.stdout,blocks*55*4))
                                if sys.byteorder!='little':observed.byteswap()
                                for block in range(blocks):
                                    tile=indices[cursor];cursor+=1
                                    tile_coeff[tile]=coefficients[block*128:(block+1)*128]
                                    for i in range(55):words[tile*55+i]+=observed[block*55+i]
                                chunks.append(dict(axis=axis,blocks=blocks,bytes=len(packet),sha256=hashlib.sha256(packet).hexdigest()))
                            assert cursor==len(indices)
                            for tile in range(offset,offset+total):coefficient_hash.update(tile_coeff.get(tile,bytes(128)))
                            offset+=total
                        assert coefficient_hash.hexdigest()==frame['canonical_coefficients_sha256']
                        for tile in range(8100):
                            for part in range(5):
                                for i in range(11):totals[part][i]+=words[tile*55+part*11+i]
                        assert totals[0][8]==8100 and all(t[8]==0 for t in totals[1:])
                        assert totals[0][7]==sum(c['bytes'] for c in chunks)
                        assert all(t[10]==88*len(chunks) for t in totals[1:])
                        for context in totals[1:]:assert context[9]==context[1]+18*len(chunks)
                        for part in range(5):
                            for i in range(11):global_totals[str(cap)][part][i]+=totals[part][i]
                        if sys.byteorder!='little':words.byteswap()
                        payload=words.tobytes()
                        meta={k:frame[k] for k in ('cohort','ordinal','fid','refid','key','canonical_coefficients_sha256','canonical_sha256','hud_sha256','display_sha256')}
                        meta.update(cap=cap,work_sha256=hashlib.sha256(payload).hexdigest(),chunks=chunks,
                                    shared_totals=dict(zip(FIELDS,totals[0])),context_totals=[dict(zip(FIELDS,t)) for t in totals[1:]])
                        encoded=json.dumps(meta,separators=(',',':')).encode();record=struct.pack('<I',len(encoded))+encoded+payload
                        output.write(record);raw.update(record);frames.append(meta)
                    if len(frames)%50==0:print('V86_REENCODED_CONTEXT_PROGRESS',len(frames)//2,flush=True)
            process.stdin.close();code=process.wait();assert code==0,code
        assert len(frames)==914 and chunk_count==7432
        assert pins=={name:sha(ROOT/name) for name in pins},'source mutation'
        index=dict(schema='cu66-v86-native-reencoded-contexts-v1',record_count=914,native_sources=457,caps=CAPS,fields=FIELDS,
                   data=dict(path=str((out/'data.bin.gz').relative_to(AREA)),gzip_sha256=sha(out/'data.bin.gz'),raw_sha256=raw.hexdigest()),
                   source_sha256=pins,frames=frames,totals={cap:dict(shared=dict(zip(FIELDS,rows[0])),contexts=[dict(zip(FIELDS,t)) for t in rows[1:]]) for cap,rows in global_totals.items()},
                   validation='Every observed AB38 chunk equals frozen coefficient decoder; canonical scattered coefficient SHA equals V85 for both caps.',
                   scope='Actual new-stream primitive observations only. Mode-map/outer/HUD parsing, dequant/reconstruction and target timing excluded.')
        (AREA/'index.json').write_text(json.dumps(index,indent=2)+'\n')
        report.update(status='PASS',records=914,native_sources=457,chunks=chunk_count,index_sha256=sha(AREA/'index.json'),source_archive_sha256=sha(out/'sources.tar.gz'))
    except BaseException as exc:
        report['failure']=repr(exc)
        if process is not None and process.poll() is None:process.terminate();process.wait()
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V86_REENCODED_CONTEXT_REPORT',out/'results.json',report['status'],flush=True)


if __name__=='__main__':main()
