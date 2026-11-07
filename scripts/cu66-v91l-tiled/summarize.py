#!/usr/bin/env python3
"""Bind independently audited tiled writes, retention reader and derived source model."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91l-tiled'
SHARED=['docs/gamebub-application-specific-codec-plan.md','docs/gamebub-v91-v110-development-plan.md','docs/literature-review-2026-11-06/README.md']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())

def pins(report,path):
    for name,h in report['source_sha256'].items():
        assert sha(ROOT/name)==sha(path.parent/'sources'/name)==h,name
    for name,h in report['artifacts_sha256'].items():assert sha(path.parent/name)==h,name
    for name,h in report['inputs_sha256'].items():
        assert sha(ROOT/name)==sha(path.parent/'inputs'/Path(name).name)==h,name
    assert all(c['exit_code']==0 for c in report['commands'])

def main():
    a=read(AREA/'audit-tiled.json')
    assert a['status']=='PASS_INDEPENDENT_TWO_SEED_TILED_PIN_AUDIT'
    assert a['verifier_sha256']==sha(AREA/'verify_tiled.py')
    tiledpath=ROOT/a['selected_report'];tiled=read(tiledpath)
    assert a['report_sha256']==sha(tiledpath)
    pins(tiled,tiledpath)
    assert len(a['modes'])==8 and len(a['checker_negative_controls'])==32
    assert all(x['rejected'] for x in a['checker_negative_controls'])
    assert sum(m['verdict']['checks'] for m in a['modes'])==220
    assert sum(m['verdict']['read_words'] for m in a['modes'])==320
    assert sum(m['native_rows'] for m in a['modes'])==560640
    assert sum(len(m['native_frames']) for m in a['modes'])==8
    comparisons=[]
    for c,runner in zip(a['comparisons'],tiled['comparisons']):
        for key in ('seed','raster_cycles','tile8x8_cycles','raster_activates','tile8x8_activates'):
            assert c[key]==runner[key],key
        comparisons.append(dict(c,raster_ms_at100mhz=c['raster_cycles']/100000,
                                tile8x8_ms_at100mhz=c['tile8x8_cycles']/100000,
                                speedup=c['raster_cycles']/c['tile8x8_cycles']))
    # Reader receipt schema and bindings are verified by its independently run checker.
    r=read(AREA/'audit-rowpair.json')
    assert r['status']=='PASS_INDEPENDENT_TWO_SEED_ROWPAIR_AUDIT'
    assert r['verifier_sha256']==sha(AREA/'verify_rowpair.py')
    rowpath=ROOT/r['selected_report'];rowreport=read(rowpath)
    assert r['report_sha256']==sha(rowpath)
    pins(rowreport,rowpath)
    assert len(r['modes'])==4 and len(r['comparisons'])==4
    assert sum(m['verdict']['checks'] for m in r['modes'])==68
    assert sum(len(m['frames']) for m in r['modes'])==8
    assert len(r['checker_negative_controls'])==32 and all(x['rejected'] for x in r['checker_negative_controls'])
    for checked,measured in zip(r['comparisons'],rowreport['comparisons']):
        for key in ('seed','frame','independent_bl8','retained_bl8','independent_cycles','retained_cycles','component_cycle_reduction_percent'):
            assert checked[key]==measured[key],key
    models=read(AREA/'audit-models.json')
    assert models['status']=='PASS_INDEPENDENT_PREFILL_GEOMETRY_AND_LINE_CACHE_MODEL'
    assert models['verifier_sha256']==sha(AREA/'verify_models.py')
    assert models['prefill_report_sha256']==sha(AREA/'prefill-results.json')
    p=read(AREA/'prefill-results.json')
    assert p['generator_sha256']==sha(AREA/'prefill_model.py')
    for name,h in p['source_sha256'].items():assert sha(ROOT/name)==h
    assert sha(ROOT/p['vector']['path'])==p['vector']['gzip_sha256']
    result=dict(schema='cu66-v91l-tiled-and-retention-summary-v1',status='PASS_TILED_WRITES_AND_DERIVED_PREFILL_RETENTION_COMPONENTS',
                tiled_run=dict(path=str(tiledpath.relative_to(ROOT)),sha256=sha(tiledpath)),
                tiled_comparisons=comparisons,
                rowpair_run=dict(path=str(rowpath.relative_to(ROOT)),sha256=sha(rowpath)),
                rowpair_comparisons=r['comparisons'],rowpair_check_entries=68,rowpair_exact_native_outputs=8,
                rowpair_cycle_scope=rowreport['service'],
                integrity={name:sha(AREA/name) for name in ('audit-tiled.json','audit-rowpair.json','audit-models.json','verify_tiled.py','verify_rowpair.py','verify_models.py','prefill_model.py','prefill-results.json')},
                tiled_native_row_requests=560640,tiled_native_word_writes=2242560,tiled_native_bank_images=8,
                tiled_check_entries=220,tiled_read_word_comparisons=320,
                logical_converter_requests_per_frame=32400,
                reader_independent_bl8_per_frame=64800,reader_retained_bl8_per_frame=32400,
                retained_data_storage_bytes=1472,retained_metadata_included=False,
                address_order='DERIVED_FROM_SOURCE actual converter chroma-prefill/luma byteorder reduced through three plane line tags; not captured addresses.',
                timed_tiled_write_controller=True,retention_reader_real_sdram_join=False,
                existing_rgb565_converter_join=False,live_codec_shared_controller_join=False,
                physical_hardware_tested=False,sustained_hardware_30fps_proven=False,validated_complete_decode_under10ms=False,
                next='Join bounded retained reader and tile-mapped writer with live codec/validation and all clients on one finite physical SDRAM service, preserve controls and actual RGB565 oracle, then cadence/physical gates.')
    (AREA/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    paths=[]
    for directory in (AREA,ROOT/'fpga/experiments/cu66-v91l-tiled',ROOT/'fpga/experiments/cu66-v91l-rowpair',ROOT/'scripts/cu66-v91l-tiled',ROOT/'scripts/cu66-v91l-rowpair',ROOT/'docs/cu66-v91l-tiled'):
        paths.extend(x for x in directory.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x.name!='bundle-manifest.json')
    paths.extend(ROOT/name for name in SHARED)
    manifest=dict(schema='cu66-v91l-tiled-bundle-v1',files={str(x.relative_to(ROOT)):sha(x) for x in sorted(paths)})
    (AREA/'bundle-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(result['status'],len(paths),'manifest files')
if __name__=='__main__':main()
