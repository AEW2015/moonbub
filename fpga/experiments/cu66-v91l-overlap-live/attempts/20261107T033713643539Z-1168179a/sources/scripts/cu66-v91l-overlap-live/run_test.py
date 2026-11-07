#!/usr/bin/env python3
"""Bounded native live key/delta -> real shared SDRAM writes -> validated RGB."""
import concurrent.futures
import os,selectors
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v91l-overlap-live';FABRIC=ROOT/'fpga/experiments/cu66-v91l-shared-service'
CONTAINER='gamebub-cu66-v69-build'
RGBSOURCE=ROOT/'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/rgb_goldens.tsv.gz'
def file_stats(p):
 digest=hashlib.sha256();size=rows=0
 with p.open('rb') as stream:
  while block:=stream.read(1024*1024):digest.update(block);size+=len(block);rows+=block.count(b'\n')
 return digest.hexdigest(),size,rows
def sha(p):return file_stats(p)[0]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--seed',type=int,action='append',choices=(912901,912902));ap.add_argument('--no-guard',action='store_true');ap.add_argument('--only-guard',action='store_true');ap.add_argument('--tac',type=int,action='append',choices=(2,7));args=ap.parse_args();seeds=args.seed or [912901,912902];corners=args.tac or [2,7]
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8];out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 old=[ROOT/('fpga/experiments/'+n) for n in ('cu66-v91/br88_rice_elastic.sv','cu66-v91b/br88_context.sv','cu66-v91d/br88_packet_ingress.sv','cu66-v91g2/packed_scratch_v91g2.sv','cu66-v91h/br88_packet_ingress_v91h.sv','cu66-v91h/br88_packet_ingress_sync_v91h.sv','cu66-v91h/br88_pipeline_v91h.sv','cu66-v91i2/cs88_admission_v91i2a.sv','cu66-v91i2b/byte_refill_queue_v91i2b.sv','cu66-v91j/cu66_inverse_stream_v91j.sv','cu66-v69/inverse/cu66_dequant.sv','cu66-v69/inverse/cu66_idct8x8.sv','cu66-v69/inverse/cu66_reconstruct_tile.sv','cu66-v91k/cs88_coefficients_v91k.sv','cu66-v91k/cu66_reconstruct_stream_v91k.sv','cu66-v91k/cs88_pipeline_v91k.sv','cu66-v69/hash/cu66_sha256_bytes.sv','cu66-v69/banks/cu66_frame_bank_control.sv','cu66-v91l/cs88_validate_publish_v91l.sv','cu66-v91l-live/cu66_write_hash_join_v91l.sv','cu66-v91l-rows/cu66_row_write_hash_join_v91l.sv','cu66-v91l-rows/cs88_rows_v91l.sv','cu66-v91l-rowpair/tile_rowpair_reader.sv','cu66-v91l-readbridge/bl8_read_bridge.sv','cu66-v91l-tiled/row_to_sdram.sv','cu66-v91l-writepipe/controller/moonshine_sdram.sv','cu66-v91l-writepipe/sdram_pin_model.sv')]
 sv=old+[ROOT/'fpga/experiments/cu66-v91l-burst-converter'/n for n in ('canonical_rgb565_cached.sv','canonical_line_reader.sv','canonical_rgb565_lines.sv','canonical_rgb565_tiled.sv')]+[FABRIC/n for n in ('shared_sdram_service.sv','shared_sdram_timed.sv')]+[ROOT/'fpga/experiments/cu66-v91l-reference-reader'/n for n in ('reference_tile_reader.sv','reader_client_mux.sv','reference_shared_timed.sv')]+[ROOT/'fpga/experiments/cu66-v91l-scratch-service'/n for n in ('scratch_line_bridge.sv','scratch_sdram_timed.sv','scratch_shared_timed.sv')]+[ROOT/'fpga/experiments/cu66-v91l-overlap-lease/display_overlap_lease.sv',AREA/'overlap_live.sv'];cpp=AREA/'tb_overlap_live.cpp'
 sources=sv+[cpp,AREA/'interface.json',AREA/'make_wrapper.py',AREA/'make_bench.py',AREA/'overlap_extension.inc',Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'fpga/experiments/cu66-v91l-rows/tb_compare.cpp',ROOT/'fpga/experiments/cu66-v91l-rows/make_bench.py',ROOT/'fpga/experiments/cu66-v91l-reference-live/tb_reference_live.cpp',ROOT/'fpga/experiments/cu66-v91l-scratch-live/tb_scratch_live.cpp']+[ROOT/'experiments/cu66-native-v69'/n for n in ('hud.hpp','bytes.hpp','generated_constants.hpp')]
 inputs=[ROOT/'experiments/python-gamebub-v91i2/vectors/cases.tsv',ROOT/'experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz',ROOT/'experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz',ROOT/'experiments/python-gamebub-v91l/vectors/validation.tsv.gz',RGBSOURCE]
 report=dict(schema='cu66-v91l-overlap-live-v1',status='FAIL',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},commands=[],modes=[],seeds=seeds,t_ac_ns=corners,fixed_scratch_profile=0,actual_live_canonical_producer=True,actual_physical_candidate_writes=True,actual_rgb_from_same_pin_memory=True,physical_preload=False,serial_live_commit_then_rgb=False,native_decode_display_overlap=True,hardware_overlap_qualified=False,full_rtl_hud_decoder=False,full_rtl_hud_overlay=False,scratch_service_rtl=True,physical_scratch_service=True,all_external_memory_endpoints_rtl=True,accepted_reference_service_rtl=True,physical_reference_service=True,full_live_physical_service_complete=False,scratch_memory_actors=False,hardware_30fps_proven=False,physical_hardware_tested=False,scope='Native BR88 key c0/f0 then delta c0/f1, frozen live reconstruction/write/hash/validation, actual tiled candidate writer plus retained burst converter through one unchanged controller and timed SDRAM pin model. C++ HUD decoded before each frame; bounded 128-bit scratch read/write endpoint now real RTL through bank3 of the same controller; accepted-reference tiles read by real RTL through the same physical SDRAM service. Actual key display overlaps the next native delta decode; immutable display leases gate bank aliasing and real presentation drain. Four natural modes retain seeded80percent outputready; one separate directed native guard holds the final pixel through deltaCOMMIT+17cycles. No measured30fps or hardware claim. Original logical wrongACK/error/drain fault campaign remains separate frozen control.')
 began=time.monotonic();temporary=[];streamed_artifacts={}
 def cmd(argv,name,timeout):
  entry=dict(argv=argv,log=name,exit_code=None);report['commands'].append(entry)
  if name.startswith('pins-'):
   digest=hashlib.sha256();size=rows=0;started=time.monotonic();chunks=[];entry['log_chunks']=[];carry=b''
   process=subprocess.Popen(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
   destination=compressed=None;chunk_bytes=chunk_rows=0;chunk_digest=None;packed=None
   def close_chunk():
    nonlocal destination,compressed,chunk_bytes,chunk_rows,chunk_digest,packed
    if compressed is None:return
    compressed.close();destination.close();chunks.append(dict(path=packed.name,gzip_sha256=sha(packed),raw_sha256=chunk_digest.hexdigest(),raw_bytes=chunk_bytes,rows=chunk_rows));entry['log_chunks'].append(packed.name);destination=compressed=None
   def write_chunk(raw):
    nonlocal destination,compressed,chunk_bytes,chunk_rows,chunk_digest,packed
    if not raw:return
    if compressed is None:
     packed=out/(name+'.part'+str(len(chunks)).zfill(3)+'.gz');destination=packed.open('wb');compressed=gzip.GzipFile(fileobj=destination,mode='wb',mtime=0,compresslevel=6);chunk_bytes=chunk_rows=0;chunk_digest=hashlib.sha256()
    compressed.write(raw);chunk_digest.update(raw);chunk_bytes+=len(raw);chunk_rows+=raw.count(b'\n')
    if chunk_bytes>=128*1024*1024:close_chunk()
   try:
    while selector.get_map():
     if time.monotonic()-started>timeout:process.kill();raise subprocess.TimeoutExpired(argv,timeout)
     for key,_ in selector.select(timeout=1):
      block=os.read(key.fileobj.fileno(),1048576)
      if block:
       digest.update(block);size+=len(block);rows+=block.count(b'\n');raw=carry+block;at=raw.rfind(b'\n')
       if at>=0:write_chunk(raw[:at+1]);carry=raw[at+1:]
       else:carry=raw
      else:selector.unregister(key.fileobj)
    write_chunk(carry);process.wait(timeout=10);entry['exit_code']=process.returncode
   finally:
    close_chunk();selector.close();process.stdout.close()
    if process.poll() is None:process.kill();process.wait()
    streamed_artifacts[name]=dict(chunks=chunks,raw_sha256=digest.hexdigest(),raw_bytes=size,rows=rows)
  else:
   with (out/name).open('w') as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
   entry['exit_code']=r.returncode
  if entry['exit_code']:raise RuntimeError('command failed: '+str(out/name))
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
   build='/build/v91l-scratch-live-'+stamp+'-tac'+str(tac);builds[tac]=build
   cmd(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','--timing','--assert','-Wall','--timescale','1ns/1ps','-DSIMULATION','-j','2','--top-module','overlap_live','-GT_AC_NS='+str(tac)+'.0','--Mdir',build,'-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror -DROW_WRITES=1',*[snap(p) for p in sv],snap(cpp)],'compile-tac'+str(tac)+'.log',900)
  def run_mode(tac,seed,guard):
   directory=out/('seed'+str(seed)+'-tac'+str(tac)+('-guard' if guard else ''));directory.mkdir();mode=dict(seed=seed,t_ac_ns=tac,guard_mode=guard,pin_logs=[],status='FAIL',directory=str(directory.relative_to(out)));report['modes'].append(mode)
   log_name='pins-seed'+str(seed)+'-tac'+str(tac)+('-guard' if guard else '')+'.jsonl'
   cmd(['docker','exec',CONTAINER,builds[tac]+'/Voverlap_live',*[str(p) for p in expanded[:4]],str(seed),str(directory/'events.jsonl'),str(directory/'actual.tsv'),str(directory/'hashes.jsonl'),str(directory/'bus.bin'),str(expanded[-1]),str(directory/'physical-events.jsonl'),str(directory),str(int(guard))],log_name,1800)
   verdict=[];live=[]
   mode['pin_logs']=[c['path'] for c in streamed_artifacts[log_name]['chunks']]
   for pin_log in mode['pin_logs']:
    with gzip.open(out/pin_log,'rt') as stream:
     for line in stream:
      event=json.loads(line)
      if event['type']=='verdict':verdict.append(event)
      elif event['type']=='live_case':live.append(event)
   assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS' and verdict[0]['cases']==2
   assert len(live)==2 and [e['id'] for e in live]==['c0_f0','c0_f1']
   for e in live:assert e['write_requests']==e['write_acks']==70080 and e['hash_deliveries']==e['physical_write_bytes']==560640 and e['hash_jobs']==1025
   frames=[];starts=[];commits=[];presentations=[];references=[];services=[];scratches=[];overlap=[];guards=[];scratch_requests=scratch_responses=scratch_writes=scratch_reads=0;ref_requests=ref_responses=ref_line_requests=ref_line_responses=0
   with (directory/'physical-events.jsonl').open() as stream:
    for line in stream:
     event=json.loads(line);kind=event['type']
     if kind=='rgb_frame':frames.append(event)
     elif kind=='reference_frame':references.append(event)
     elif kind=='service_counts':services.append(event)
     elif kind=='scratch_frame':scratches.append(event)
     elif kind=='overlap_summary':overlap.append(event)
     elif kind=='publication_wait_actual_display':guards.append(event)
     elif kind=='scratch_live_req':scratch_requests+=1;scratch_writes+=int(event['write']);scratch_reads+=int(not event['write'])
     elif kind=='scratch_live_rsp':scratch_responses+=1
     elif kind=='reference_req':ref_requests+=1
     elif kind=='reference_rsp':ref_responses+=1
     elif kind=='reference_line_req':ref_line_requests+=1
     elif kind=='reference_line_rsp':ref_line_responses+=1
     elif kind=='native_start':starts.append(event)
     elif kind=='native_commit':commits.append(event)
     elif kind=='native_presented':presentations.append(event)
   assert len(frames)==len(starts)==len(commits)==len(presentations)==len(references)==len(scratches)==2 and len(services)==len(overlap)==1
   assert scratch_requests==scratch_responses==sum(c['requests'] for c in scratches)==14058
   assert scratch_writes==sum(c['write_requests'] for c in scratches)==7029 and scratch_reads==sum(c['read_requests'] for c in scratches)==7029
   for c in scratches:
    assert c['requests']==c['responses']==c['read_requests']+c['write_requests'] and c['write_requests']==c['write_responses'] and c['read_requests']==c['read_responses']
    assert c['max_address']%16==0 and c['max_address']<=262128
   assert ref_requests==ref_responses==7806 and ref_line_requests==ref_line_responses==31224
   assert [r['tile_requests'] for r in references]==[0,7806] and [r['line_responses'] for r in references]==[0,31224]
   counts=services[0];assert counts['writer_grants']==counts['wr_rows']==140160
   assert counts['writer_commands']==counts['wr_words_accepted']==counts['wr_words_retired']==560640
   assert counts['writes']==616872 and counts['readwords']==824424
   assert counts['reader_grants']==counts['reader_commands']==counts['rd_requests']==counts['rd_responses']==96024 and counts['rd_count_beats']==768192
   for stages in references:assert stages['start_cycle']<stages['input_complete_cycle']<=stages['stage_first_cycle']<=stages['stage_last_cycle']<=stages['last_canonical_pixel_cycle']<stages['commit_cycle']
   for start,commit,frame in zip(starts,commits,frames):
    assert start['bank']==commit['bank']==frame['bank'] and start['bank_active']==1 and commit['v_commit']==1
    for role in ('accepted_ref','front','pending'):
     if start[role+'_valid']:assert start['bank']!=start[role+'_bank']
    output=directory/frame['output'];frame['output_sha256']=sha(output);assert output.stat().st_size==frame['bytes']==691200 and frame['output_sha256']==rgb[frame['id']]
    assert frame['commit_cycle']<=frame['start_cycle']<frame['first_pixel_cycle']<=frame['last_pixel_cycle']<=frame['engine_done_cycle']<frame['closed_cycle']
    assert frame['physical_reads']==frame['logical_reads']==32400
   o=overlap[0];assert o['key_rgb_start_cycle']<o['delta_start_cycle']<o['key_rgb_closed_cycle'] and o['last_rgb_closed_cycle']==frames[-1]['closed_cycle']
   assert all(o[k]>0 for k in ('engine_bank_active_cycles','contended_offer_cycles','candidate_requests_while_rgb','reference_requests_while_rgb','scratch_requests_while_rgb'))
   assert bool(o['guard_mode'])==guard and len(guards)==int(guard)
   if guard:
    g=guards[0];assert g['display_active'] and not g['scanout_drained'] and g['external_drained_hint'] and g['vblank'] and g['front_fid']==0 and g['pending_fid']==1 and g['accepted_fid']==1 and o['key_rgb_closed_cycle']>o['delta_commit_cycle']+17
   mode.update(status='PASS_EXACT_NATIVE_DECODE_DISPLAY_OVERLAP',verdict=verdict[0],live_cases=live,frames=frames,native_starts=starts,native_commits=commits,presentations=presentations,references=references,service_counts=services,scratch_frames=scratches,overlap=overlap[0],guard_receipts=guards,scratch_requests=scratch_requests,scratch_responses=scratch_responses,scratch_write_requests=scratch_writes,scratch_read_requests=scratch_reads,reference_tile_requests=ref_requests,reference_tile_responses=ref_responses,reference_bl8_requests=ref_line_requests,reference_bl8_responses=ref_line_responses)
   return mode
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   jobs=[] if args.only_guard else [(tac,seed,False) for tac in corners for seed in seeds]
   if not args.no_guard:jobs.append((2,912901,True))
   list(pool.map(lambda pair:run_mode(*pair),jobs))
  report['modes'].sort(key=lambda mode:(mode['guard_mode'],mode['t_ac_ns'],mode['seed']))
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources};assert report['inputs_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
  report['status']='PASS_EXACT_NATIVE_DECODE_DISPLAY_OVERLAP_SAME_TIMED_MEMORY'
 except BaseException as error:report.update(error_class=type(error).__name__,error=str(error));raise
 finally:
  for p in temporary:
   if p.exists():p.unlink()
  report['compressed_artifacts']=dict(streamed_artifacts)
  for p in [*out.glob('pins-*.jsonl'),*out.glob('seed*/*.jsonl'),*out.glob('seed*/*.tsv'),*out.glob('seed*/*.bin')]:
   if p.name.endswith('.rgb565.bin'):continue
   raw_hash,raw_bytes,raw_rows=file_stats(p);packed=p.with_suffix(p.suffix+'.gz')
   with p.open('rb') as source,packed.open('wb') as destination:
    with gzip.GzipFile(fileobj=destination,mode='wb',mtime=0) as compressed:shutil.copyfileobj(source,compressed,1024*1024)
   digest=hashlib.sha256()
   with gzip.open(packed,'rb') as source:
    while block:=source.read(1024*1024):digest.update(block)
   assert digest.hexdigest()==raw_hash
   receipt=dict(path=str(packed.relative_to(out)),gzip_sha256=sha(packed),raw_sha256=raw_hash,raw_bytes=raw_bytes)
   if p.name=='bus.bin':assert raw_bytes%32==0;receipt.update(record_bytes=32,records=raw_bytes//32,format='<BBBBIIIIQI kind/profile/bank/bytes/fid/epoch/token/address/valueLE/cycle')
   else:receipt['rows']=raw_rows
   report['compressed_artifacts'][str(p.relative_to(out))]=receipt;p.unlink()
  report['wall_seconds']=time.monotonic()-began;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('OVERLAP_LIVE',report['status'],out,flush=True)
if __name__=='__main__':main()
