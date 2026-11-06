#!/usr/bin/env python3
"""Strict live parser/reconstruction -> tagged byte ACK -> C2 validation campaign."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; AREA=ROOT/'fpga/experiments/cu66-v91l-rows'
CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--seed',type=int,choices=(912101,912102),default=912101);a=ap.parse_args()
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
 out=AREA/'comparison-attempts'/stamp;out.mkdir(parents=True);build='/build/v91l-rows-'+stamp
 old=[ROOT/('fpga/experiments/'+n) for n in ('cu66-v91/br88_rice_elastic.sv','cu66-v91b/br88_context.sv','cu66-v91d/br88_packet_ingress.sv','cu66-v91g2/packed_scratch_v91g2.sv','cu66-v91h/br88_packet_ingress_v91h.sv','cu66-v91h/br88_packet_ingress_sync_v91h.sv','cu66-v91h/br88_pipeline_v91h.sv','cu66-v91i2/cs88_admission_v91i2a.sv','cu66-v91i2b/byte_refill_queue_v91i2b.sv','cu66-v91j/cu66_inverse_stream_v91j.sv','cu66-v69/inverse/cu66_dequant.sv','cu66-v69/inverse/cu66_idct8x8.sv','cu66-v69/inverse/cu66_reconstruct_tile.sv','cu66-v91k/cs88_coefficients_v91k.sv','cu66-v91k/cu66_reconstruct_stream_v91k.sv','cu66-v91k/cs88_pipeline_v91k.sv','cu66-v69/hash/cu66_sha256_bytes.sv','cu66-v69/banks/cu66_frame_bank_control.sv','cu66-v91l/cs88_validate_publish_v91l.sv')]
 sv=old+[ROOT/'fpga/experiments/cu66-v91l-live/cu66_write_hash_join_v91l.sv',AREA/'cu66_row_write_hash_join_v91l.sv',AREA/'cs88_rows_v91l.sv'];cpp=AREA/'tb_compare.cpp'
 sources=sv+[cpp,AREA/'make_wrapper.py',AREA/'make_bench.py',Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh']+[ROOT/'experiments/cu66-native-v69'/n for n in ('hud.hpp','bytes.hpp','generated_constants.hpp')]
 inputs=[ROOT/'experiments/python-gamebub-v91i2/vectors/cases.tsv',ROOT/'experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz',ROOT/'experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz',ROOT/'experiments/python-gamebub-v91l/vectors/validation.tsv.gz']
 report=dict(schema='cu66-v91l-tile-row-write-comparison-v1',status='FAIL',seed=a.seed,source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},commands=[],input_expansions=[],modes=[],live_canonical_producer=True,full_rtl_hud_decoder=False,full_rtl_hud_overlay=False,physical_memory_controller=False,hardware_distinct_30fps_proven=False,full_frame_decode_under10ms_proven=False,monolithic_full_frame_rtl_proven=False,scope='Actual BR88 live canonical path, actual accepted-bank references and registered qcache, compared with static unchanged byte writer versus bounded eight-byte row writer; each logical response is priced at x16 payload beats plus identical response-overhead rules. C++ HUD remains before start, no physical controller/RGB/display/ESP32 claim.')
 began=time.monotonic();temporary=[]
 def cmd(argv,log,timeout):
  item=dict(argv=argv,log=log,exit_code=None);report['commands'].append(item)
  with (out/log).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=timeout,cwd=ROOT)
  item['exit_code']=r.returncode
  if r.returncode:raise RuntimeError('command failed: '+log)
 try:
  for p in sources:
   dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  (out/'inputs').mkdir()
  expanded=[]
  for p in inputs:
   dest=out/'inputs'/p.name;shutil.copyfile(p,dest)
   if p.suffix=='.gz':
    q=out/p.stem;q.write_bytes(gzip.decompress(dest.read_bytes()));temporary.append(q);expanded.append(q)
    report['input_expansions'].append(dict(path=q.name,compressed_path=str(dest.relative_to(out)),compressed_sha256=sha(dest),raw_sha256=sha(q),rows=len(q.read_bytes().splitlines())))
   else:expanded.append(dest)
  cmd(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30);cmd(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
  snapshot=lambda p:str(out/'sources'/p.relative_to(ROOT))
  for name,flag,width in (('control',0,1),('rows',1,8)):
   mode=dict(name=name,write_batch_bytes=width,status='FAIL');report['modes'].append(mode)
   cmd(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--top-module','cs88_rows_v91l','-GROW_WRITES='+str(flag),'--Mdir',build+'-'+name,'-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror -DROW_WRITES='+str(flag),*[snapshot(p) for p in sv],snapshot(cpp)],'compile-'+name+'.log',600)
   cmd(['docker','exec',CONTAINER,build+'-'+name+'/Vcs88_rows_v91l',*[str(p) for p in expanded],str(a.seed),str(out/('events-'+name+'.jsonl')),str(out/('actual-'+name+'.tsv')),str(out/('hashes-'+name+'.jsonl')),str(out/('bus-'+name+'.bin'))],'simulation-'+name+'.jsonl',1800)
   rows=[json.loads(x) for x in (out/('simulation-'+name+'.jsonl')).read_text().splitlines()];vs=[x for x in rows if x['type']=='verdict'];assert len(vs)==1 and vs[0]['status']=='TEST_PASS' and vs[0]['cases']==4
   mode['verdict']=vs[0];mode['live_rows']=[x for x in rows if x['type']=='live_case'];assert len(mode['live_rows'])==4
   for row in mode['live_rows']:
    assert row['write_batch_bytes']==width and row['write_requests']==row['write_acks']==560640//width
    assert row['x16_data_beats']==(560640 if width==1 else 280320)
    assert row['physical_write_bytes']==row['hash_deliveries']==560640
   mode['status']='PASS_EXACT_LIVE_PATH'
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources};assert report['inputs_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
  report['status']='PASS_EXACT_X16_PRICED_TILE_ROW_WRITES' 
 except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  for p in temporary:
   if p.exists():p.unlink()
  report['compressed_artifacts']={}
  for mode in report['modes']:
   name=mode['name'];mode['compressed_artifacts']={}
   for original in ('events-'+name+'.jsonl','hashes-'+name+'.jsonl','actual-'+name+'.tsv','bus-'+name+'.bin'):
    p=out/original
    if p.exists():
     raw=p.read_bytes();q=p.with_suffix(p.suffix+'.gz');q.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(q.read_bytes())==raw
     receipt=dict(path=q.name,gzip_sha256=sha(q),raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw))
     if p.suffix=='.bin':assert len(raw)%32==0;receipt.update(record_bytes=32,records=len(raw)//32,format='<BBBBIIIIQI; kind/profile/bank/bytes/fid/epoch/token/address/valueLE/cycle')
     else:receipt['rows']=len(raw.splitlines())
     mode['compressed_artifacts'][original]=receipt;p.unlink()
  report['compressed_artifacts']={mode['name']:mode['compressed_artifacts'] for mode in report['modes']}
  report['wall_seconds']=time.monotonic()-began;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'comparison-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('V91L_ROWS',report['status'],out,flush=True)
if __name__=='__main__':main()
