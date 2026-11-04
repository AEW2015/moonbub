"""Hardware-kit reference inputs; all imports use frozen v19 packet fixtures."""
import hashlib,importlib.util,json,sys,zlib
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/python-game-causal-stripe-study'))
import model as stripe
_spec=importlib.util.spec_from_file_location('v20_hardware_stripe_fixture_builder',ROOT/'experiments/python-game-causal-stripe-study/benchmark.py')
fixture=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(fixture)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded_array(a):
    raw=np.asarray(a,dtype='<i4').tobytes();name=hashlib.sha256(raw).hexdigest()+'.i32.zlib'
    return name,raw,zlib.compress(raw,9)
def actual_blocks():
    manifest=json.loads((fixture.TRACE/'results.json').read_text());rows=[];labels=[]
    for cohort in manifest['cohorts']:
        for row in cohort['rows']:
            packet=stripe.fixture.raw(row['ar03']);meta=stripe.trace.codec.identity(packet,decode=True)
            for plane,coeff in enumerate(meta['parsed']['coefficients']):
                values=coeff.astype(np.int64)*stripe.trace.codec.gm.roi.block_tables(meta['parsed']['scale_map'],meta['width'],meta['height'],plane)
                rows.append(values.astype(np.int32));labels.append(dict(cohort=cohort['name'],id=row['id'],plane=plane,blocks=len(values)))
    return np.concatenate(rows),labels

def datasets():
    actual,labels=actual_blocks()
    dc=np.zeros((4097,8,8),np.int32);dc[:,0,0]=np.arange(-2048,2049,dtype=np.int32)*255
    rng=np.random.default_rng(20261103);random=rng.integers(-2048,2049,(256,8,8),dtype=np.int32)*rng.integers(1,256,(256,8,8),dtype=np.int32)
    edge=np.zeros((6,8,8),np.int32);edge[0]=522240;edge[1]=-522240
    edge[2]=np.where(np.indices((8,8)).sum(axis=0)%2,522240,-522240)
    edge[3,0,0]=-1;edge[4,0,0]=-8193;edge[5,7,7]=522240
    return [('actual-ar03',actual,labels),('dc-extremes',dc,[]),('random-legal',random,[]),('signed-edges',edge,[])]

def source_pins():
    old=json.loads((ROOT/'experiments/python-game-causal-stripe-study/results.json').read_text())['source_sha256']
    paths={ROOT/p for p in old}
    paths|={ROOT/'experiments/python-game-causal-stripe-study/results.json',ROOT/'experiments/python-game-causal-stripe-study/model.py',ROOT/'experiments/python-game-causal-stripe-study/benchmark.py'}
    control=ROOT/'experiments/python-game-frame-grant-study/results.json'
    paths.add(control)
    paths|={ROOT/raw for raw in json.loads(control.read_text())['source_sha256']}
    paths|={HERE/p for p in ('reference.py','export_vectors.py','acceptance.py','verify.py','test_reference.py','src/gb_inverse.c','include/gb_inverse.h','export_contract.py','export_mem.py')}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
