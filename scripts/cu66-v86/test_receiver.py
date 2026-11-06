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
AREA=ROOT/'experiments/python-gamebub-v86'


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
    assert sha(AREA/'receiver.cpp')==wire['source_sha256']['experiments/python-gamebub-v86/receiver.cpp']
    key_path=path.parent/'c0-f0-copy_group_cap65536.cs86';delta_path=path.parent/'c0-f1-copy_group_cap65536.cs86'
    key=key_path.read_bytes();delta=delta_path.read_bytes();binary=wire['binary']
    foreign_key_path=path.parent/'c3-f0-copy_group_cap65536.cs86';foreign_delta_path=path.parent/'c3-f1-copy_group_cap65536.cs86'
    foreign_key=foreign_key_path.read_bytes();foreign_delta=foreign_delta_path.read_bytes()
    legacy_path=ROOT/'experiments/python-gamebub-v85/wire-attempts/20261106T130658877580Z-53860fda/c0-f1-cap65536.cs85'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'protocol-attempts'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True)
    (out/'test_receiver.py').write_bytes(Path(__file__).read_bytes())
    report=dict(schema='cu66-v86-native-protocol-tests-v1',status='FAIL',checks=[],
                source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
                               'experiments/python-gamebub-v86/receiver.cpp':sha(AREA/'receiver.cpp'),
                               str(path.relative_to(ROOT)):sha(path),str(key_path.relative_to(ROOT)):sha(key_path),str(delta_path.relative_to(ROOT)):sha(delta_path),
                               str(foreign_key_path.relative_to(ROOT)):sha(foreign_key_path),str(foreign_delta_path.relative_to(ROOT)):sha(foreign_delta_path)},
                binary=binary,hardware_test=False)
    clients=[];started=time.monotonic()
    try:
        # Every malformed case is tried against an accepted key, then the exact
        # valid delta must still succeed. This reaches the real transform/HUD/C2
        # receiver path instead of a synthetic acceptance-state model.
        cases=[]
        report['source_sha256'][str(legacy_path.relative_to(ROOT))]=sha(legacy_path)
        cases.append(('valid_legacy_profile_rejected',legacy_path.read_bytes(),'explicit profile/version'))
        cases.append(('outer_crc',bytes(delta[:-1])+bytes([delta[-1]^1]),'CS86 outer CRC'))
        for name,offset,value,width,reason in (
            ('profile_version',4,2,1,'explicit profile/version'),
            ('flags',5,2,1,'flags/group'),
            ('group_size',6,8,1,'flags/group'),
            ('unknown_map_method',7,4,1,'mode method'),
            ('unsupported_cap',32,16,4,'chunk profile'),
            ('overflow_data_length',48,0xffffffff,4,'exact body length'),
            ('qmap_length',40,337,4,'component bounds'),
            ('stale_generation',16,1,8,'stale identity/generation'),
            ('wrong_reference',12,1,4,'accepted reference binding'),
            ('content_root',52,delta[52]^1,1,'reconstructed content root'),
            ('content_seal',84,delta[84]^1,1,'reconstructed frame seal'),
            ('reserved_header',116,1,1,'reserved padding'),
            ('wrong_geometry',24,512,2,'geometry'),
            ('block_reserved',30,1,2,'block geometry/reserved'),
        ):cases.append((name,edited(delta,offset,value,width),reason))
        map_len=struct.unpack_from('>I',delta,36)[0];qpos=128+map_len;data_pos=qpos+338
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
        # Locate a real nonempty grouped token and reseal after replacing its
        # tag with3. Geometry and fixed hidden positions define the token count.
        assert delta[7]==3
        import importlib.util
        native_path=ROOT/'experiments/python-gamebub-v82/native/data.py'
        spec=importlib.util.spec_from_file_location('cs86_negative_native',native_path)
        native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
        hidden=next(native.iter_frames())['hidden_mask']
        bitpos=0;offset=0;tag_at=None
        def readbit():
            nonlocal bitpos
            value=(delta[128+bitpos//8]>>(7-bitpos%8))&1;bitpos+=1;return value
        for plane,count in enumerate((5400,1350,1350)):
            for start in range(0,count,16):
                tag_start=bitpos;tag=readbit()*2+readbit()
                visible=sum(not hidden[offset+i] for i in range(start,min(start+16,count)))
                if visible and tag_at is None:tag_at=tag_start
                if tag==2:bitpos+=visible
            offset+=count
        assert tag_at is not None
        changed=bytearray(delta)
        for position in (tag_at,tag_at+1):changed[128+position//8]|=1<<(7-position%8)
        cases.append(('group_tag_resealed',reseal(changed),'grouped invalid tag'))
        # V2-style raw bitset spelling is independently valid in CS86. Its low
        # two pad bits must still be zero, even when group3 is normally shorter.
        def body_replaced(packet,new_body,method):
            old_len=struct.unpack_from('>I',packet,36)[0]
            value=bytearray(packet[:128]);value[7]=method;struct.pack_into('>I',value,36,len(new_body))
            raw=bytes(value)+new_body+packet[128+old_len:-4]
            return raw+struct.pack('>I',zlib.crc32(raw))
        bits=bytearray(976);visible_index=0
        # Derive original delta modes from its known source, not by calling the
        # new map encoder under test.
        iterator=native.iter_frames();next(iterator);delta_native=next(iterator)
        for h,copy in zip(hidden,delta_native['copy_ref_mask']):
            if not h:
                bits[visible_index//8]|=(not copy)<<(7-visible_index%8);visible_index+=1
        assert visible_index==7806
        raw_spelling=body_replaced(delta,bytes(bits),1)
        malformed_bits=bytearray(bits);malformed_bits[-1]|=1
        cases.append(('bitset_padding_resealed',body_replaced(delta,bytes(malformed_bits),1),'bitset padding'))
        cases.append(('implicit_map_on_delta',body_replaced(delta,b'',0),'implicit map on delta'))
        cases.append(('run_underrun_resealed',body_replaced(delta,b'\x80',2),'run underrun'))
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
            # Valid method1 encoding must give the same pixels/seal as method3.
            client=Client(binary,log);clients.append(client);assert client.send(key)['accepted']
            raw_result=client.send(raw_spelling);assert raw_result['accepted'] and raw_result['fid']==1
            report['checks'].append(dict(name='alternative_bitset_spelling',result='PASS',recovered=raw_result))
            client.close()
            # The cached frame ID is identical but its accepted pixels/HUD/root
            # are from a different native key. Implicit reference/HUD binding
            # must reject this branch, then recover using the matching delta.
            client=Client(binary,log);clients.append(client);assert client.send(foreign_key)['accepted']
            mismatch=client.send(delta);assert not mismatch['accepted'] and mismatch['retained_fid']==0
            recovered_foreign=client.send(foreign_delta);assert recovered_foreign['accepted'] and recovered_foreign['fid']==1
            report['checks'].append(dict(name='same_fid_wrong_cached_branch',result='PASS',rejected=mismatch,recovered_foreign=recovered_foreign))
            client.close()
            # Substitute another fully valid, independent HUD key, re-ID and
            # reseal its own envelope, while preserving the expected original
            # semantic HUD in the C2 seal. Only C2 semantic binding should fail.
            def hud_payload(packet):
                pos=128+struct.unpack_from('>I',packet,36)[0]+338+struct.unpack_from('>I',packet,48)[0]
                return pos,packet[pos:-4]
            key_hud_pos,original_hud=hud_payload(key);_,foreign_hud=hud_payload(foreign_key)
            assert hashlib.sha256(original_hud).digest()!=hashlib.sha256(foreign_hud).digest()
            altered_hud=bytearray(foreign_hud);struct.pack_into('<I',altered_hud,10,2)
            altered_hud[-4:]=struct.pack('<I',zlib.crc32(altered_hud[:-4]))
            value=bytearray(key[:key_hud_pos]);struct.pack_into('>I',value,8,2);struct.pack_into('>Q',value,16,3)
            struct.pack_into('>I',value,44,len(altered_hud))
            from_control=next(r for r in json.loads((ROOT/'experiments/python-gamebub-v82/native/index.json').read_text())['frames'] if r['cohort']==0 and r['fid']==0)
            context=hashlib.sha256(b'{"geometry":[720,480,5400,1350,1350],"granularity":16,"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"}').digest()
            message=b'CU66V82C2\x00S\x00'+context+struct.pack('>IIBQ',2,0xffffffff,1,3)+bytes(32)+bytes.fromhex(from_control['hud_sha256'])+key[52:84]
            value[84:116]=hashlib.sha256(message).digest()
            # A positive companion proves this re-ID/seal construction is
            # otherwise valid. The foreign-HUD rejection below must be caused
            # by the changed semantic HUD, not a malformed generated seal.
            correct_hud=bytearray(original_hud);struct.pack_into('<I',correct_hud,10,2)
            correct_hud[-4:]=struct.pack('<I',zlib.crc32(correct_hud[:-4]))
            control_prefix=bytearray(value);struct.pack_into('>I',control_prefix,44,len(correct_hud))
            control_body=bytes(control_prefix)+bytes(correct_hud)
            good_reidentified=control_body+struct.pack('>I',zlib.crc32(control_body))
            companion_client=Client(binary,log);clients.append(companion_client);assert companion_client.send(key)['accepted']
            companion=companion_client.send(good_reidentified)
            assert companion['accepted'] and companion['fid']==2 and companion['generation']==3,companion
            assert companion['root']==key[52:84].hex() and companion['hud_sha256']==from_control['hud_sha256']
            companion_client.close()
            body=bytes(value)+bytes(altered_hud);bad_hud=body+struct.pack('>I',zlib.crc32(body))
            client=Client(binary,log);clients.append(client);assert client.send(key)['accepted']
            late=client.send(bad_hud);assert not late['accepted'] and late['retained_fid']==0 and 'reconstructed frame seal' in late['error'],late
            after=client.send(delta);assert after['accepted'] and after['fid']==1
            report['checks'].append(dict(name='valid_other_HUD_rejected_by_semantic_seal',result='PASS',packet_sha256=hashlib.sha256(bad_hud).hexdigest(),
                                        positive_companion_packet_sha256=hashlib.sha256(good_reidentified).hexdigest(),positive_companion=companion,rejected=late,recovered=after))
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
        print('V86_PROTOCOL_REPORT',out/'results.json',report['status'],len(report['checks']),flush=True)


if __name__=='__main__':main()
