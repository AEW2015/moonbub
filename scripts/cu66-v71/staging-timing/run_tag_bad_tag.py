"""Real full KEY decode/hash with wrong expected-tag input and actual HUD abort."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/tag-equality-v001';p=d/'evidence/keyp01';a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert json.loads((p/'result.json').read_text())['frames']==2
for f in(p/'inputs').rglob('*'):
 if f.is_file():
  dest=o/Path(str(f.relative_to(p)).replace('keyp01',o.name));dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
receiver=o/'inputs/fpga/experiments/cu66-v71/direct-system/board-math-v001/cu71_receiver_direct_math.sv';text=receiver.read_text();assert text.count('.expected_tag(canonical_expected)')==1;receiver.write_text(text.replace('.expected_tag(canonical_expected)',".expected_tag(canonical_expected^128'd1)"),newline='\n')
cpp=(p/'tb.cpp').read_text();start=cpp.index(' void run(cu66::Bytes bytes,');end=cpp.index('\n};',start)
cpp=cpp[:start]+''' void run(cu66::Bytes bytes,std::shared_ptr<const cu66::Frame>gold,bool lost_ack=false){
  while(!d.start_ready)tick();generation++;packet=std::move(bytes);golds[generation]=gold;prepared=result_sent=drain_sent=false;aux_pending=false;candidate=nullptr;word_cursor=read_cursor=0;soft_calls=0;drop_ack=false;did_drop_ack=false;
  uint64_t begin=cycles,first_error=0;unsigned old=d.accepted_count;d.start_generation=generation;d.start_packet_bytes=packet.size();d.start_valid=1;while(!tick().start){}d.start_valid=0;
  while(!d.aborted){need(cycles-begin<20000000,"badtag drain timeout");tick();if(d.error){need(d.error_code==0x50,"wrong badtag reason");if(!first_error)first_error=cycles;}need(!d.lcd_error&&!d.cache_prepare_fault,"unrelated display fault");}
  need(first_error&&d.error&&d.error_code==0x50,"real tag mismatch missing");need(d.accepted_count==old&&d.rejected_count==1,"failed tag committed or not rejected");need(!d.reference_valid&&!d.front_valid&&!d.lcd_front_valid&&!hud.accepted(),"failed tag published reference/front/HUD");need(soft_calls==1&&!software_pending,"actual HUD abort not drained");need(d.rgb_completed_writes==0,"RGB activity");
  std::cout<<"TAG_EQ_BAD_TAG_ACTUAL_NATIVE_PASS error=0x50 first_error_cycle="<<first_error<<" completion_cycle="<<cycles<<" native_ABORT_calls="<<soft_calls<<" accepted="<<d.accepted_count<<" rejected="<<d.rejected_count<<" canonical_physical_words="<<d.model_writes<<std::endl;
 }
'''+cpp[end:]
old='need(e.opcode==5,"unexpected abort in positive full system run");software_success=hud.commit(e.generation,e.fid);need(software_success,"root commit disagrees with processor state");'
new='need(e.opcode==6,"expected actual native abort only");software_success=hud.abort(e.generation,e.fid);need(software_success,"actual native abort failed");';assert old in cpp;cpp=cpp.replace(old,new)
start=cpp.index(' uint64_t begin=s.cycles;while(s.cycles-begin<3500000)');end=cpp.index(' return 0;}catch',start);cpp=cpp[:start]+cpp[end:];(o/'tb.cpp').write_text(cpp,newline='\n')
parents={str(f):sha(f)for f in[p/'source-freeze.json',p/'result.json',p/'tb.cpp',p/'execution.json',r/'fpga/experiments/cu66-v71/direct-system/board-math-v001/cu71_receiver_direct_math.sv',Path(__file__).resolve()]};(o/'source-freeze.json').write_text(json.dumps({'parents':parents,'compiled':{str(f.relative_to(o)):sha(f)for f in o.rglob('*')if f.is_file()},'fault':'Only verification receiver-to-base expected_tag input XOR1; exact base/decoder/SHA/HUD/memory/owner sources unchanged. Native endpoint processes real ABORT and drains; no success fabricated.'},indent=2)+'\n')
executions=json.loads((p/'execution.json').read_text());steps=[]
for label in['build','frames']:
 cmd=next(x['command']for x in executions if x['label']==label);cmd=[x.replace('keyp01',o.name)for x in cmd]
 if label=='frames':cmd[-1]=cmd[-1].rsplit(' ',1)[0]+' 1'
 start=time.monotonic()
 with(o/(label+'.log')).open('w')as log:q=subprocess.run(cmd,cwd=o,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 steps.append({'label':label,'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start});(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,label
assert 'TAG_EQ_BAD_TAG_ACTUAL_NATIVE_PASS'in(o/'frames.log').read_text()
(o/'result.json').write_text(json.dumps({'status':'PASS_ACTUAL_FULL_KEY_HASH_TAG_MISMATCH_REAL_NATIVE_ABORT_NO_PUBLICATION','expected_error':'0x50','injection':'Wrong expected_tag at actual base input only; immutable packet/native oracle unchanged','actual_native_ABORT':True,'accepted':0,'rejected':1,'reference_front_HUD_published':False,'exact_candidate_base':'6d9e57bd55da26b83ccf8027bb2e4c704329d670b1a73201b0dc40c9ed185433','hardware':False,'source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n')
