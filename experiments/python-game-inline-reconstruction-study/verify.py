#!/usr/bin/env python3
"""Read-only actual generated reconstruction, IT20 and service reconciliation."""
import hashlib,importlib.util,json,zlib
from pathlib import Path
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('v20_inline_own_benchmark',HERE/'benchmark.py');benchmark=importlib.util.module_from_spec(spec);spec.loader.exec_module(benchmark)
def raw(desc):
    path=Path(desc['path']);assert not path.is_absolute() and '..' not in path.parts
    stored=(HERE/path).read_bytes();assert hashlib.sha256(stored).hexdigest()==desc['stored_sha256']
    dec=zlib.decompressobj();data=dec.decompress(stored,desc['raw_bytes']+1)
    assert dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(data)==desc['raw_bytes']
    assert hashlib.sha256(data).hexdigest()==desc['raw_sha256'];return data

def main():
    d=json.loads((HERE/'results.json').read_text());assert d['schema']=='gamebub-inline-generated-reconstruction-v1'
    for p,h in d['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    c=d['counts'];assert (c['packets'],c['blocks'],c['residual_samples'],c['reconstructed_samples'],c['selected_ui_words'],c['profiles'])==(16,97308,6227712,6224472,253440,5)
    current=benchmark.run_vectors(False)
    assert len(current)==len(d['frames'])==16
    objects={f['tile_stream']['path'] for f in d['frames']}
    assert objects=={p.relative_to(HERE).as_posix() for p in (HERE/'objects').glob('*.it20.zlib')}
    assert len(objects)==c['tile_streams']==9
    assert sum(f['canonical_bytes_hashed'] for f in d['frames'])==c['canonical_bytes_hashed']==12449008
    for fresh,row in zip(current,d['frames']):
        assert fresh=={k:v for k,v in row.items() if k!='tile_stream'}
        data=raw(row['tile_stream']);assert hashlib.sha256(data).hexdigest()==row['tile_stream_sha256']
        tag,t=model.replay_stream(data,bytes.fromhex(row['private_tag_hex']),eligible=row['published'])
        assert tag.hex()==row['canonical_fixture_tag_hex'] and t.tiles==row['tiles']
        assert row['canonical_bytes_hashed']==4+2*row['reconstructed_samples']
        assert row['tagger_local_ndarray_bytes']==row['tagger_stripe_bytes']+row['canonical_row_bytes']
        assert row['selected_ui_word_errors']==0 and row['output_written_after_tag_push']
        assert (row['publication_tag_hex'] is not None)==row['published']
    frozen=json.loads((HERE.parent/'python-game-causal-stripe-study/results.json').read_text())['frames']
    assert len(d['cases'])==5
    for case in d['cases']:
        assert len(case['rows'])==len(frozen)==16
        for frame,r in zip(frozen,case['rows']):
            got=r['schedule'];b=model.v19.Budget(**got['config']);ib=model.InlineBudget(**got['inline_config'])
            assert model.schedule(frame,b,ib)==got
            assert got['tag_bank_reread_bytes']==0
            if not frame['published']:assert abs(got['frame_done_ms']-got['baseline_serial_frame_ms'])<1e-9
            else:assert got['reference_tag_ready_ms']<=got['bank_publication_earliest_ms']<=got['rgb_display_ready_ms']
            assert got['eliminated_physical_tag_bank_bytes']==(frame['samples'] if frame['published'] else 0)
            last={}
            for s in got['stripes']:
                assert s['entropy_done_ms']<=s['consumer_start_ms']<=s['prediction_done_ms']<=s['inverse_done_ms']<=s['compact_write_done_ms']<=s['done_ms']
                if s['hash_done_ms'] is not None:assert s['hash_start_ms']>=s['inverse_done_ms'] and s['hash_done_ms']<=s['done_ms']
                if s['coefficient_slot'] in last:assert s['entropy_start_ms']>=last[s['coefficient_slot']]
                last[s['coefficient_slot']]=s['done_ms']
    print(json.dumps(dict(packets=16,exact_blocks=97308,residual_samples=6227712,reconstructed_samples=6224472,exact_selected_ui_words=253440,
        tagger_local_arrays_720wide_bytes=7200,profiles=5,physical_or_native_30fps_proven=False),indent=2))
if __name__=='__main__':main()
