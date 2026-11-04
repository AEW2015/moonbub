#!/usr/bin/env python3
"""Actual generated-tile inline canonical tags and conditional service campaign."""
from dataclasses import replace
from pathlib import Path
import hashlib,json,time,zlib
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
TRACE=HERE.parent/'python-game-ar03-trace-study';V19=HERE.parent/'python-game-causal-stripe-study'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def store(data):
    path=HERE/'objects'/(hashlib.sha256(data).hexdigest()+'.it20.zlib');packed=zlib.compress(data,9)
    path.parent.mkdir(exist_ok=True);path.write_bytes(packed)
    return dict(path=path.relative_to(HERE).as_posix(),encoding='zlib',raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=sha(path))
def dependencies():
    d=json.loads((V19/'results.json').read_text());paths={ROOT/p for p in d['source_sha256']}
    paths|={V19/'results.json',V19/'benchmark.py',V19/'model.py',HERE/'model.py',HERE/'benchmark.py',HERE/'verify.py',HERE/'test_model.py'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def run_vectors(write_objects=False):
    d=json.loads((TRACE/'results.json').read_text());proofs=[]
    for cohort in d['cohorts']:
        for row in cohort['rows']:
            proof,data=model.reconstruct(row,cohort['name'])
            if write_objects:proof['tile_stream']=store(data)
            proofs.append(proof)
    return proofs

def main():
    before=dependencies();started=time.perf_counter();proofs=run_vectors(True)
    frozen=json.loads((V19/'results.json').read_text());frames=frozen['frames'];cases=[]
    profiles=[('compact_inline_hash100',model.v19.Budget(bytes_per_sample=1),model.InlineBudget()),
        ('compact_inline_hash25',model.v19.Budget(bytes_per_sample=1),model.InlineBudget(hash_MBps=25)),
        ('compact_inline_hash400',model.v19.Budget(bytes_per_sample=1),model.InlineBudget(hash_MBps=400)),
        ('compact_inline_mem240',model.v19.Budget(bytes_per_sample=1,effective_sdram_MBps=240),model.InlineBudget()),
        ('compact_inline_onebuffer',model.v19.Budget(bytes_per_sample=1,stripe_buffers=1),model.InlineBudget())]
    for label,budget,inline in profiles:
        rows=[dict(cohort=f['cohort'],id=f['id'],schedule=model.schedule(f,budget,inline)) for f in frames]
        native=[r['schedule'] for r in rows if r['cohort'].startswith('native')]
        summary=dict(profile=label,native_decisions=len(native),native_mean_serial_ms=sum(r['baseline_serial_frame_ms'] for r in native)/len(native),
            native_mean_inline_ms=sum(r['frame_done_ms'] for r in native)/len(native),native_budget_misses=sum(r['missed_frame_budget'] for r in native),
            eliminated_physical_tag_bank_bytes=sum(r['eliminated_physical_tag_bank_bytes'] for r in native),
            max_additional_tagger_ndarray_bytes=max(r['additional_tagger_ndarray_bytes'] for r in native),max_local_planning_bytes=max(r['local_planning_bytes'] for r in native),
            maximum_hash_backpressure_ms=max(r['hash_backpressure_ms'] for r in native))
        print(json.dumps(summary),flush=True);cases.append(dict(profile=label,rows=rows,summary=summary))
    assert before==dependencies()
    counts=dict(packets=len(proofs),native_decisions=12,unique_native_acquisitions=6,flat_controls=4,
        blocks=sum(p['blocks'] for p in proofs),residual_samples=sum(p['residual_samples'] for p in proofs),reconstructed_samples=sum(p['reconstructed_samples'] for p in proofs),
        canonical_bytes_hashed=sum(p['canonical_bytes_hashed'] for p in proofs),selected_ui_words=sum(p['selected_ui_words'] for p in proofs),
        tile_streams=len(list((HERE/'objects').glob('*.it20.zlib'))),profiles=len(profiles))
    out=dict(schema='gamebub-inline-generated-reconstruction-v1',source_sha256=before,counts=counts,frames=proofs,cases=cases,
        python_wall_seconds=time.perf_counter()-started,
        arithmetic_scope='Actual validated AR03 coefficient stripes pass through the exact sparse Q14 inverse, prediction and clipping. Each generated compact tile is tagged before external output-bank write; no completed reconstructed plane is reread as tag input. Canonical int16 geometry/Y/Cb/Cr bytes and all expected reference/display/UI vectors match.',
        publication_scope='Private tag sealed only at complete explicit finish with validated packet and expected hash. Only KEY/PROMOTE eligible frames expose publication_tag. Ordinary P hashes are correctness probes, not bank publication. Abort/order/duplicate/truncation/CRC failures expose no new publication. Existing committed receiver bank management is outside this standalone prototype.',
        memory_scope='Tagger owns one <=8-row compact uint8 stripe plus one canonical int16 row (7200B at720width). Full packet/parsed coefficients, coefficient-stripe NumPy inverse temporaries, external prediction/output/fixture arrays and export bytearray are excluded. Hashlib/Python control heap is not measured; conditional SHA/control state128+64B is planning only. Local footprint conservatively adds tagger storage to frozen v19 decoder buffers instead of claiming alias reuse.',
        timing_scope='Conditional compact-YUV8 v19 service with exact actual stripe demands; copy/expand/hash work paid, stripes retained until compact write AND inline hash drain. Hash path overlaps external writes but can backpressure inverse/entropy. No optimistic future-bank release or free hash throughput. Serial baseline retains all same declared costs plus post-frame tag-bank read/hash. Physical bytes and canonical hash bytes are separate.',
        excluded_scope='No ISA/RF/native clock calibration, fitted DSP/BRAM/resource/SDRAM arbitration, physical480x800 scanline or joint end-to-end/hardware30fps proof. Ten v19 decoder assumptions remain conditional, including full49152Bcompressedcache and4preflightpasses. Native12decisions reuse6sourceacquisitions;4flatcontrols notgameplayFPS.')
    (HERE/'results.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
