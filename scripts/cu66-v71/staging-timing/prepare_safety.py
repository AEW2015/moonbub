from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/staging-timing';d=p/'safety-v002';assert not d.exists();d.mkdir();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();parents={}
for name in ['cu71_packet_staging_credit','cu71_local_control_credit','dy71_local_control_credit']:
 f=p/(name+'.sv');parents[f.relative_to(r).as_posix()]=sha(f);s=f.read_text().replace(name,name.replace('_credit','_safe'))
 if name=='cu71_packet_staging_credit':
  assert 'assign begin_ready=state==EMPTY&&!rst;'in s;s=s.replace('assign begin_ready=state==EMPTY&&!rst;','assign begin_ready=state==EMPTY&&held_count==0&&!rst;')
  assert 'if((state==LOADING||state==SEALED)&&held_count==0)'in s;s=s.replace('if((state==LOADING||state==SEALED)&&held_count==0)','if((state==LOADING||state==SEALED)&&held_count==0&&!upload_valid)')
 else:
  s=s.replace('cu71_packet_staging_credit staging(','cu71_packet_staging_safe staging(')
  assert 'wire can_discard=!frame_active' in s;s=s.replace('wire can_discard=!frame_active','wire can_discard=!upload_pulse&&!frame_active')
 (d/(name.replace('_credit','_safe')+'.sv')).write_text(s,newline='\n')
(d/'derivation.json').write_text(json.dumps({'parents':parents,'changes':['Versioned module names only','Stager DISCARD additionally requires !upload_valid','CSR can_discard additionally requires !upload_pulse, so overlapping command ACK rejects','Stager begin_ready additionally requires held_count==0 defensively'],'normal_cycle_latency_changed':False,'general_input_equivalence_claimed':False,'selected_sources_modified':False,'hardware':False},indent=2)+'\n')
print(d)
