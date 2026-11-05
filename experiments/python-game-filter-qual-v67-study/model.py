"""Integer bookkeeping preserves per-frame regressions and source partitions."""
from fractions import Fraction

def summarize(rows):
    if not rows: raise ValueError('nonempty contiguous source window')
    ids=[r['id'] for r in rows]
    if ids!=list(range(ids[0],ids[0]+len(ids))): raise ValueError('contiguous ordered source IDs')
    identity=[r['identity']['active_squared_error'] for r in rows]
    strong=[r['strong']['active_squared_error'] for r in rows]
    samples=[r['identity']['active_channel_samples'] for r in rows]
    if any(type(x) is not int or x<0 for x in (*identity,*strong)): raise ValueError('integer SSE')
    if any(type(n)is not int or n<=0 or n!=r['strong']['active_channel_samples'] for r,n in zip(rows,samples,strict=True)): raise ValueError('same positive samples')
    ratios=[Fraction(b-a,a) if a else (Fraction(0) if b==0 else None) for a,b in zip(identity,strong,strict=True)]
    mse=lambda s:[Fraction(a,n) for a,n in zip(s,samples,strict=True)]
    return dict(frames=len(rows),first_id=ids[0],last_id=ids[-1],complete_bytes=sum(r['complete_bytes'] for r in rows),
                active_samples=sum(samples),identity_SSE=sum(identity),strong_SSE=sum(strong),
                identity_MSE=sum(identity)/sum(samples),strong_MSE=sum(strong)/sum(samples),
                improved_frames=sum(b<a for a,b in zip(identity,strong,strict=True)),
                regressed_frames=sum(b>a for a,b in zip(identity,strong,strict=True)),
                tied_frames=sum(b==a for a,b in zip(identity,strong,strict=True)),
                zero_identity_error_regressed_frames=sum(a==0 and b>0 for a,b in zip(identity,strong,strict=True)),
                maximum_positive_frame_SSE_delta=max(0,max(b-a for a,b in zip(identity,strong,strict=True))),
                worst_relative_SSE_increase=float(max([Fraction(0),*(r for r in ratios if r is not None)])),
                identity_peak_frame_MSE=float(max(mse(identity))),strong_peak_frame_MSE=float(max(mse(strong))))

def partitions(rows):
    return {name:summarize([r for r in rows if lo<=r['id']<hi])
            for name,lo,hi in [('calibration_0_23',0,24),('later_24_47',24,48),('remaining_48_plus',48,10**9)]}
