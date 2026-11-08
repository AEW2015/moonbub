"""Explicit dy71-bounded3-v2 diagnostic. NOT a live encoder or negotiated stream."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import socket
import struct
import time
import dyn1_pair_core as core

PROFILE='dy71-bounded3-v2'

def load_sequence(manifest_path, profile):
    if profile != PROFILE:
        raise ValueError('requires explicit dy71-bounded3-v2 profile')
    manifest_path=Path(manifest_path)
    manifest=json.loads(manifest_path.read_text())
    if manifest['status']!='PASS_FRESH_SOFTWARE_REFERENCE_AND_FAULTS' or len(manifest['frames'])!=3:
        raise ValueError('requires qualified exact three-frame manifest')
    bodies=[]
    for index,record in enumerate(manifest['frames']):
        item=record['files']['cu66'];path=(manifest_path.parent/item['path']).resolve()
        if path.parent!=manifest_path.parent.resolve():
            raise ValueError('packet path must be adjacent to manifest')
        body=path.read_bytes();core.validate(body)
        if len(body)!=item['bytes'] or hashlib.sha256(body).hexdigest()!=item['sha256']:
            raise ValueError('packet manifest length/hash')
        frame,reference=struct.unpack_from('<II',body,8)
        if frame!=record['id'] or reference!=record['reference_id'] or bool(body[5]&1)!=record['key']:
            raise ValueError('packet manifest identity')
        if frame!=index or reference!=(0xffffffff if index==0 else index-1) or bool(body[5]&1)!=(index==0):
            raise ValueError('requires exact chronological KEY0/P1/P2 chain')
        bodies.append(body)
    return bodies

def upload(sock, receiver, bodies, session, log, initial_wait_seconds):
    if len(bodies)!=3 or session==0:
        raise ValueError('three bodies and nonzero session required')
    results=[]
    for index,body in enumerate(bodies):
        result=core.send_frame(sock,receiver,body,session,log,
            initial_wait_seconds if index==0 else 10)
        if result['status']!='presented':
            raise RuntimeError('must observe actual presentation before next dependent frame')
        results.append(result)
    return results

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',required=True,choices=[PROFILE])
    p.add_argument('--manifest',type=Path,default=Path(__file__).with_name('manifest.json'))
    p.add_argument('--receiver',required=True)
    p.add_argument('--bind',required=True)
    p.add_argument('--port',type=int,default=5535)
    p.add_argument('--initial-wait-seconds',type=float,default=600)
    p.add_argument('--log',type=Path,required=True)
    a=p.parse_args()
    if not 1<=a.initial_wait_seconds<=1800:p.error('initial wait must be1..1800seconds')
    if a.port!=5535:p.error('bounded3 profile is explicitly port5535')
    bodies=load_sequence(a.manifest,a.profile)
    session=secrets.randbits(64)or 1
    receiver=(socket.gethostbyname(a.receiver),a.port)
    with a.log.open('x')as log,socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as sock:
        sock.bind((a.bind,0));sock.settimeout(0.1)
        row={'event':'session','profile':PROFILE,'wire':'DYN1/DYA1 v2; explicit selection, no negotiation',
             'frames':3,'session':session,'source':sock.getsockname(),'destination':receiver,
             'manifest_sha256':hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
             'initial_wait_seconds':a.initial_wait_seconds,'started_unix_us':time.time_ns()//1000}
        log.write(json.dumps(row)+'\n');log.flush();print(json.dumps(row),flush=True)
        try:
            results=upload(sock,receiver,bodies,session,log,a.initial_wait_seconds)
        except Exception as exc:
            failure={'event':'failed','error':str(exc),'whole_run_retry':False,'receiver_state':'unknown_or_retained; do not auto-reset'}
            log.write(json.dumps(failure)+'\n');log.flush();raise
        result={'event':'complete','profile':PROFILE,'presented':len(results),'whole_run_retry':False}
        log.write(json.dumps(result)+'\n');log.flush();print(json.dumps(result),flush=True)

if __name__=='__main__':main()
