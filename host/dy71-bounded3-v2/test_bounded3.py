"""Pure fake-transport tests: no socket created, no datagram transmitted."""
import io
import json
from pathlib import Path
import struct
import unittest
import zlib
import bounded3_sender as sender

HERE=Path(__file__).resolve().parent
PEER=('192.168.0.157',5535)

class Fake:
    def __init__(self,fail_frame=None):self.frames=[];self.reply=None;self.fail_frame=fail_frame;self.sent=[]
    def sendto(self,b,peer):
        assert peer==PEER
        h=list(sender.core.HEADER.unpack(b[:48]));assert h[:4]==[b'DYN1',2,0,48]
        assert zlib.crc32(b[:-4])==struct.unpack_from('<I',b,len(b)-4)[0]
        self.sent.append((h[5],h[8]))
        h[0]=b'DYA1';h[2]=3 if h[5]==self.fail_frame else (2 if h[8]+h[11]==h[7]else 0)
        h[8]+=h[11];h[11]=0
        wire=sender.core.HEADER.pack(*h);self.reply=wire+struct.pack('<I',zlib.crc32(wire))
        return len(b)
    def recvfrom(self,n):return self.reply,PEER

class Tests(unittest.TestCase):
    def test_three_actual_frames_present_in_dependency_order(self):
        b=sender.load_sequence(HERE/'manifest.json',sender.PROFILE);fake=Fake();log=io.StringIO()
        results=sender.upload(fake,PEER,b,7,log,1)
        self.assertEqual([r['frame']for r in results],[0,1,2])
        self.assertEqual(len(fake.sent),58)
        self.assertEqual([json.loads(row)['status']for row in log.getvalue().splitlines()],['presented']*3)
    def test_failure_stops_before_next_dependent_frame(self):
        b=sender.load_sequence(HERE/'manifest.json',sender.PROFILE);fake=Fake(fail_frame=1)
        with self.assertRaisesRegex(RuntimeError,'failed/retained'):
            sender.upload(fake,PEER,b,7,io.StringIO(),1)
        self.assertNotIn(2,[frame for frame,offset in fake.sent])
    def test_explicit_profile_and_count(self):
        with self.assertRaisesRegex(ValueError,'explicit'):
            sender.load_sequence(HERE/'manifest.json','dyn1-pair')
        with self.assertRaises(ValueError):sender.upload(Fake(),PEER,[],7,io.StringIO(),1)
    def test_v1_reply_rejected(self):
        b=sender.load_sequence(HERE/'manifest.json',sender.PROFILE)[0]
        fake=Fake();fake.sendto(sender.core.datagram(b,7,11,0),PEER)
        reply=bytearray(fake.reply);reply[4]=1;reply[-4:]=struct.pack('<I',zlib.crc32(reply[:-4]))
        with self.assertRaisesRegex(ValueError,'header'):sender.core.decode_reply(bytes(reply))
    def test_published_vectors(self):
        vectors=json.loads((HERE/'golden-vectors.json').read_text())
        import hashlib
        for row in vectors['vectors']:
            wire=(HERE/row['file']).read_bytes()
            self.assertEqual(hashlib.sha256(wire).hexdigest(),row['sha256'])
            self.assertEqual(len(wire),row['bytes'])
            self.assertEqual(wire[4],2)
            self.assertEqual(zlib.crc32(wire[:-4]),struct.unpack_from('<I',wire,len(wire)-4)[0])
            if row['kind']=='reply':self.assertEqual(sender.core.decode_reply(wire)[2],row['status'])

if __name__=='__main__':unittest.main(verbosity=2)
