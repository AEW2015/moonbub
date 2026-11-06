"""New DY71 owner, preserving the frozen timing-v001 transaction state machine."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';p=r/'fpga/experiments/cu66-v71/codec/timing-v001/cu71_receiver_timing.sv';s=p.read_text();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=s.replace('module cu71_receiver_timing #(','module cu71_receiver_direct #(')
# Explicit profile semantics: display slots refer to cache contexts, not RGB RAM.
s=s.replace('painter_drained','cache_worker_drained').replace('painted_at','prepared_at')
s=s.replace('paint_','cache_prepare_').replace('PAINT_','CACHE_PREPARE_').replace('WAIT_RGB','WAIT_CACHE').replace('rgb','cache')
s=s.replace('    input logic cache_prepare_result_success,input logic cache_worker_drained,','    input logic cache_prepare_result_success,input logic cache_prepare_result_slot,input logic cache_worker_drained,')
old='cache_prepare_match=cache_prepare_result_generation==active_generation&&cache_prepare_result_frame_id==fid;';assert old in s
s=s.replace(old,'cache_prepare_match=cache_prepare_result_generation==active_generation&&cache_prepare_result_frame_id==fid&&cache_prepare_result_slot==cache_slot;')
s='// DY71 ABI1 direct tile-major profile: cache PREPARE replaces RGB painting.\n'+s
out=d/'cu71_receiver_direct.sv';assert not out.exists();out.write_text(s,newline='\n')
(d/'receiver-derivation.json').write_text(json.dumps({'parent':p.relative_to(r).as_posix(),'parent_sha256':sha(p),'candidate':out.relative_to(r).as_posix(),'candidate_sha256':sha(out),'changes':'Module/semanticnames; preparedresponse additionallymatchescache_slot. Parser/base/hash/banklease/irreversibleCOMMIT/lostACKretry state transitions retained.','profile_magic':'0x44593731','profile_abi':'0x00010000','capabilities':'0x0f','wire_or_csr_compatibility':False,'hardware':False},indent=2)+'\n');print(sha(out))
