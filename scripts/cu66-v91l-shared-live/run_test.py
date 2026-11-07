#!/usr/bin/env python3
"""Bounded native live key/delta -> real shared SDRAM writes -> validated RGB."""
import concurrent.futures
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v91l-shared-live';FABRIC=ROOT/'fpga/experiments/cu66-v91l-shared-service'
CONTAINER='gamebub-cu66-v69-build'
RGBSOURCE=ROOT/'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/rgb_goldens.tsv.gz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--seed',type=int,action='append',choices=(912801,912802));ap.add_argument('--tac',type=int,action='append',choices=(2,7));args=ap.parse_args();seeds=args.seed or [912801,912802];corners=args.tac or [2,7]
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8];out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 old=[ROOT/('fpga/experiments/'+n) for n in ('cu66-v91/br88_rice_elastic.sv','cu66-v91b/br88_context.sv','cu66-v91d/br88_packet_ingress.sv','cu66-v91g2/packed_scratch_v91g2.sv','cu66-v91h/br88_packet_ingress_v91h.sv','cu66-v91h/br88_packet_ingress_sync_v91h.sv','cu66-v91h/br88_pipeline_v91h.sv','cu66-v91i2/cs88_admission_v91i2a.sv','cu66-v91i2b/byte_refill_queue_v91i2b.sv','cu66-v91j/cu66_inverse_stream_v91j.sv','cu66-v69/inverse/cu66_dequant.sv','cu66-v69/inverse/cu66_idct8x8.sv','cu66-v69/inverse/cu66_reconstruct_tile.sv','cu66-v91k/cs88_coefficients_v91k.sv','cu66-v91k/cu66_reconstruct_stream_v91k.sv','cu66-v91k/cs88_pipeline_v91k.sv','cu66-v69/hash/cu66_sha256_bytes.sv','cu66-v69/banks/cu66_frame_bank_control.sv','cu66-v91l/cs88_validate_publish_v91l.sv','cu66-v91l-live/cu66_write_hash_join_v91l.sv','cu66-v91l-rows/cu66_row_write_hash_join_v91l.sv','cu66-v91l-rows/cs88_rows_v91l.sv','cu66-v91l-rowpair/tile_rowpair_reader.sv','cu66-v91l-readbridge/bl8_read_bridge.sv','cu66-v91l-tiled/row_to_sdram.sv','cu66-v91l-writepipe/controller/moonshine_sdram.sv','cu66-v91l-writepipe/sdram_pin_model.sv')]
 sv=old+[ROOT/'fpga/experiments/cu66-v91l-burst-converter'/n for n in ('canonical_rgb565_cached.sv','canonical_line_reader.sv','canonical_rgb565_lines.sv','canonical_rgb565_tiled.sv')]+[FABRIC/n for n in ('shared_sdram_service.sv','shared_sdram_timed.sv')]+[AREA/'shared_live.sv'];cpp=AREA/'tb_shared_live.cpp'
 sources=sv+[cpp,AREA/'make_wrapper.py',AREA/'make_bench.py',AREA/'bench_extension.inc',Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'fpga/experiments/cu66-v91l-rows/tb_compare.cpp',ROOT/'fpga/experiments/cu66-v91l-rows/make_bench.py']+[ROOT/'experiments/cu66-native-v69'/n for n in ('hud.hpp','bytes.hpp','generated_constants.hpp')]
 inputs=[ROOT/'experiments/python-gamebub-v91i2/vectors/cases.tsv',ROOT/'experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz',ROOT/'experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz',ROOT/'experiments/python-gamebub-v91l/vectors/validation.tsv.gz',RGBSOURCE]
 report=dict(schema='cu66-v91l-shared-live-v1',status='FAIL',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},commands=[],modes=[],seeds=seeds,t_ac_ns=corners,fixed_scratch_reference_profile=0,actual_live_canonical_producer=True,actual_physical_candidate_writes=True,actual_rgb_from_same_pin_memory=True,physical_preload=False,serial_live_commit_then_rgb=True,full_rtl_hud_decoder=False,full_rtl_hud_overlay=False,scratch_reference_service_rtl=False,full_live_physical_service_complete=False,hardware_30fps_proven=False,physical_hardware_tested=False,scope='Native BR88 key c0/f0 then delta c0/f1, frozen live reconstruction/write/hash/validation, actual tiled candidate writer plus retained burst converter through one unchanged controller and timed SDRAM pin model. C++ HUD decoded before each frame; finite frozen C++ scratch and ACK-backed accepted-reference endpoints. Original logical wrongACK/error/drain fault campaign remains separate frozen control.')
 began=time.monotonic();temporary=[]
 def cmd(argv,name,timeout):
  entry=dict(argv=argv,log=name,exit_code=None);report['commands'].append(entry)
  with (out/name).open('w') as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  entry['exit_code']=r.returncode
  if r.returncode:raise RuntimeError('command failed: '+str(out/name))
 try:
  for p in sources:
   target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  expanded=[];report['input_expansions']=[]
  for p in inputs:
   target=out/'inputs'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
   if p.suffix=='.gz':
    plain=out/p.stem;plain.write_bytes(gzip.decompress(target.read_bytes()));temporary.append(plain);expanded.append(plain);report['input_expansions'].append(dict(path=plain.name,compressed_path=str(target.relative_to(out)),compressed_sha256=sha(target),raw_sha256=sha(plain)))
   else:expanded.append(target)
  rgb={}
  for line in expanded[-1].read_text().splitlines():
   name,hx=line.split('\t')
   if name in ('actual_001','actual_006'):rgb[name]=hashlib.sha256(bytes.fromhex(hx)).hexdigest()
  report['rgb_goldens']=rgb
  cmd(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30);cmd(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
  snap=lambda p:str(out/'sources'/p.relative_to(ROOT))
  builds={}
  for tac in corners:
   build='/build/v91l-shared-live-'+stamp+'-tac'+str(tac);builds[tac]=build
   cmd(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','--timing','--assert','-Wall','--timescale','1ns/1ps','-DSIMULATION','-j','2','--top-module','shared_live','-GT_AC_NS='+str(tac)+'.0','--Mdir',build,'-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror -DROW_WRITES=1',*[snap(p) for p in sv],snap(cpp)],'compile-tac'+str(tac)+'.log',900)
  def run_mode(tac,seed):
   directory=out/('seed'+str(seed)+'-tac'+str(tac));directory.mkdir();mode=dict(seed=seed,t_ac_ns=tac,status='FAIL',directory=str(directory.relative_to(out)));report['modes'].append(mode)
   log_name='pins-seed'+str(seed)+'-tac'+str(tac)+'.jsonl'
   cmd(['docker','exec',CONTAINER,builds[tac]+'/Vshared_live',*[str(p) for p in expanded[:4]],str(seed),str(directory/'events.jsonl'),str(directory/'actual.tsv'),str(directory/'hashes.jsonl'),str(directory/'bus.bin'),str(expanded[-1]),str(directory/'physical-events.jsonl'),str(directory)],log_name,1800)
   verdict=[];live=[]
   with (out/log_name).open() as stream:
    for line in stream:
     event=json.loads(line)
     if event['type']=='verdict':verdict.append(event)
     elif event['type']=='live_case':live.append(event)
   assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS' and verdict[0]['cases']==2
   assert len(live)==2 and [e['id'] for e in live]==['c0_f0','c0_f1']
   for e in live:assert e['write_requests']==e['write_acks']==70080 and e['hash_deliveries']==e['physical_write_bytes']==560640 and e['hash_jobs']==1025
   frames=[];starts=[];commits=[];presentations=[]
   with (directory/'physical-events.jsonl').open() as stream:
    for line in stream:
     event=json.loads(line)
     if event['type']=='rgb_frame':frames.append(event)
     elif event['type']=='native_start':starts.append(event)
     elif event['type']=='native_commit':commits.append(event)
     elif event['type']=='native_presented':presentations.append(event)
   assert len(frames)==len(starts)==len(commits)==len(presentations)==2
   for start,commit,frame in zip(starts,commits,frames):
    assert start['bank']==commit['bank']==frame['bank'] and start['bank_active']==1 and commit['v_commit']==1
    for role in ('accepted_ref','front','pending'):
     if start[role+'_valid']:assert start['bank']!=start[role+'_bank']
    output=directory/frame['output'];frame['output_sha256']=sha(output);assert output.stat().st_size==frame['bytes']==691200 and frame['output_sha256']==rgb[frame['id']];assert frame['commit_cycle']<=frame['start_cycle']<frame['first_pixel_cycle']<=frame['last_pixel_cycle']<frame['closed_cycle'];assert frame['physical_reads']==frame['logical_reads']==32400
   mode.update(status='PASS_EXACT_LIVE_COMMIT_TO_SAME_MEMORY_RGB',verdict=verdict[0],live_cases=live,frames=frames,native_starts=starts,native_commits=commits,presentations=presentations)
   return mode
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   list(pool.map(lambda pair:run_mode(*pair),[(tac,seed) for tac in corners for seed in seeds]))
  report['modes'].sort(key=lambda mode:(mode['t_ac_ns'],mode['seed']))
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources};assert report['inputs_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
  report['status']='PASS_EXACT_LIVE_COMMIT_TO_SAME_TIMED_MEMORY_RGB'
 except BaseException as error:report.update(error_class=type(error).__name__,error=str(error));raise
 finally:
  for p in temporary:
   if p.exists():p.unlink()
  report['compressed_artifacts']={}
  for p in [*out.glob('pins-*.jsonl'),*out.glob('seed*/*.jsonl'),*out.glob('seed*/*.tsv'),*out.glob('seed*/*.bin')]:
   if p.name.endswith('.rgb565.bin'):continue
   raw=p.read_bytes();packed=p.with_suffix(p.suffix+'.gz');packed.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(packed.read_bytes())==raw
   receipt=dict(path=str(packed.relative_to(out)),gzip_sha256=sha(packed),raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw))
   if p.name=='bus.bin':assert len(raw)%32==0;receipt.update(record_bytes=32,records=len(raw)//32,format='<BBBBIIIIQI kind/profile/bank/bytes/fid/epoch/token/address/valueLE/cycle')
   else:receipt['rows']=len(raw.splitlines())
   report['compressed_artifacts'][str(p.relative_to(out))]=receipt;p.unlink()
  report['wall_seconds']=time.monotonic()-began;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('SHARED_LIVE',report['status'],out,flush=True)
if __name__=='__main__':main()
