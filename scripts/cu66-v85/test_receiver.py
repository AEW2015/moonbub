#!/usr/bin/env python3
"""Exercise actual native receiver rejects/recovery/replay with real wire bytes."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time
import uuid
import zlib

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v85'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def reseal(value):
    out=bytes(value[:-4]);return out+struct.pack('>I',zlib.crc32(out))


def edited(packet,offset,value,width=1):
    out=bytearray(packet);out[offset:offset+width]=int(value).to_bytes(width,'big');return reseal(out)


class Client:
    def __init__(self,binary,log):
        self.process=subprocess.Popen(['docker','exec','-i','gamebub-cu66-v69-build',binary],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log)
    def send(self,packet,cohort=0):
        self.process.stdin.write(struct.pack('>II',cohort,len(packet))+packet);self.process.stdin.flush()
        line=self.process.stdout.readline();assert line,('receiver stopped',self.process.poll())
        return json.loads(line)
    def close(self):
        self.process.stdin.close();code=self.process.wait();assert code==0,code
    def kill(self):
        if self.process.poll() is None:self.process.terminate();self.process.wait()


def main():
    p=argparse.ArgumentParser();p.add_argument('--wire-report',type=Path,required=True);args=p.parse_args()
    path=args.wire_report.resolve();wire=json.loads(path.read_text());assert wire['status'] in ('PASS_SMOKE_ONLY','PASS_NATIVE_FULL_FRAME_PARITY')
    assert sha(AREA/'receiver.cpp')==wire['source_sha256']['experiments/python-gamebub-v85/receiver.cpp']
    key_path=path.parent/'c0-f0-cap65536.cs85';delta_path=path.parent/'c0-f1-cap65536.cs85'
    key=key_path.read_bytes();delta=delta_path.read_bytes();binary=wire['binary']
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'protocol-attempts'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True)
    (out/'test_receiver.py').write_bytes(Path(__file__).read_bytes())
    report=dict(schema='cu66-v85-native-protocol-tests-v1',status='FAIL',checks=[],
                source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
                               'experiments/python-gamebub-v85/receiver.cpp':sha(AREA/'receiver.cpp'),
                               str(path.relative_to(ROOT)):sha(path),str(key_path.relative_to(ROOT)):sha(key_path),str(delta_path.relative_to(ROOT)):sha(delta_path)},
                binary=binary,hardware_test=False)
    clients=[];started=time.monotonic()
    try:
        # Every malformed case is tried against an accepted key, then the exact
        # valid delta must still succeed. This reaches the real transform/HUD/C2
        # receiver path instead of a synthetic acceptance-state model.
        cases=[]
        cases.append(('outer_crc',bytes(delta[:-1])+bytes([delta[-1]^1]),'CS85 outer CRC'))
        for name,offset,value,width,reason in (
            ('profile_version',4,2,1,'explicit profile/version'),
            ('flags',5,2,1,'flags/group/reserved'),
            ('unsupported_cap',32,32,4,'chunk profile'),
            ('overflow_data_length',48,0xffffffff,4,'exact body length'),
            ('qmap_length',40,337,4,'component bounds'),
            ('stale_generation',16,1,8,'stale identity/generation'),
            ('wrong_reference',12,1,4,'accepted reference binding'),
            ('previous_root',52,delta[52]^1,1,'accepted reference binding'),
            ('content_root',84,delta[84]^1,1,'reconstructed content root'),
            ('content_seal',116,delta[116]^1,1,'reconstructed frame seal'),
            ('HUD_digest',148,delta[148]^1,1,'semantic HUD digest'),
            ('context_domain',180,delta[180]^1,1,'context/mask binding'),
            ('hidden_profile',212,delta[212]^1,1,'context/mask binding'),
            ('reserved_header',244,1,1,'reserved padding'),
        ):cases.append((name,edited(delta,offset,value,width),reason))
        map_len=struct.unpack_from('>I',delta,36)[0];qpos=256+map_len;data_pos=qpos+338
        cases.append(('qmap_code',edited(delta,qpos,delta[qpos]|0xc0),'quantizer code'))
        cases.append(('qmap_padding',edited(delta,qpos+337,delta[qpos+337]|1),'quantizer padding'))
        cases.append(('chunk_count',edited(delta,data_pos,0,4),'chunk count'))
        cases.append(('chunk_blocks',edited(delta,data_pos+4,0,4),'chunk lengths'))
        # Repair nested CRC so this validates AB38's own grammar check rather
        # than stopping at an unrelated outer-integrity check.
        ab_len=struct.unpack_from('>I',delta,data_pos+8)[0];ab_pos=data_pos+12
        changed=bytearray(delta);changed[ab_pos]^=1
        changed[ab_pos+ab_len-4:ab_pos+ab_len]=struct.pack('<I',zlib.crc32(changed[ab_pos:ab_pos+ab_len-4]))
        cases.append(('AB38_magic_resealed',reseal(changed),'AB profile'))
        changed=bytearray(delta);changed[256+5]=3
        changed[256+16:256+20]=struct.pack('>I',zlib.crc32(changed[256:256+16]+changed[256+20:256+map_len]))
        cases.append(('mode_method_resealed',reseal(changed),'CM84 method/key/group'))
        shortened=delta[:-5]+delta[-4:]
        cases.append(('truncated_body_resealed',reseal(shortened),'exact body length'))
        with (out/'native.stderr').open('wb') as log:
            for name,packet,reason in cases:
                client=Client(binary,log);clients.append(client)
                accepted=client.send(key);assert accepted['accepted'] and accepted['fid']==0
                rejected=client.send(packet)
                assert not rejected['accepted'] and rejected['retained_fid']==0,rejected
                assert reason in rejected['error'],(name,rejected)
                recovered=client.send(delta);assert recovered['accepted'] and recovered['fid']==1 and not recovered['replayed']
                replayed=client.send(delta);assert replayed['accepted'] and replayed['replayed']
                assert all(replayed[k]==recovered[k] for k in ('root','seal','canonical_sha256','hud_sha256','display_sha256','coefficient_sha256'))
                report['checks'].append(dict(name=name,result='PASS_REJECT_RETAIN_RECOVER_REPLAY',packet_sha256=hashlib.sha256(packet).hexdigest(),
                                             expected_error_contains=reason,rejected=rejected,recovered=recovered))
                client.close()
            client=Client(binary,log);clients.append(client)
            missing=client.send(delta);assert not missing['accepted'] and missing['retained_fid'] is None
            good=client.send(key);assert good['accepted']
            replay=client.send(key);assert replay['accepted'] and replay['replayed']
            accepted=client.send(delta);assert accepted['accepted'] and not accepted['replayed']
            stale=client.send(key);assert not stale['accepted'] and stale['retained_fid']==1 and 'stale' in stale['error']
            report['checks'].append(dict(name='missing_reference_key_recovery_and_stale_replay',result='PASS',missing=missing,stale=stale))
            client.close()
        report.update(status='PASS_ACTUAL_NATIVE_REJECT_RETAIN_RECOVER',count=len(report['checks']),
                      scope='Synchronous host-native receiver tests with actual decoded bytes. No mid-decode abort, transport fragmentation, FPGA drain, electrical timing or ESP32 proof.')
    except BaseException as exc:
        report['failure']=repr(exc)
        for client in clients:client.kill()
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={v.name:sha(v) for v in out.iterdir() if v.is_file() and v.name!='results.json'}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V85_PROTOCOL_REPORT',out/'results.json',report['status'],len(report['checks']),flush=True)


if __name__=='__main__':main()
