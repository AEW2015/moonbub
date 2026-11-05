import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import cpl1_snapshot as c

P=Path(__file__).resolve().parent
E=json.loads((P/'frame0-expectation.json').read_text())

def words():
    w=[0]*40
    w[:4]=[0x1234,7,0x10000,0x7a7]
    w[4:11]=[0xffffffff,2,0x9abcdef0,0x12345678,1,0,1]
    w[11:16]=[17412,518400,21120,259200,259200]
    for start,tag in [(16,'b74b12e10009cfccbcb5363d13edc4ee'),(20,'1026aab8b7df606614f560a966806641')]:
        v=int(tag,16)
        w[start:start+4]=[(v>>(32*i))&0xffffffff for i in range(4)]
    w[24]=0x30000;w[25]=3;w[27:30]=[10,1,1]
    w[32:38]=[9,0x4c5725e5,345600,3,0,240]
    return w

def pages(w=None,cookie=None,gen=None):
    w=words() if w is None else w
    cookie=w[0] if cookie is None else cookie;gen=w[1] if gen is None else gen
    return [f'USB_TRACE cpl1 v=1 page={p} cookie={cookie:08x} gen={gen} off={0x500+16*p:03x} words='+','.join(f'{x:08x}'for x in w[4*p:4*p+4]) for p in range(10)]

def decode(lines):return c.select(c.parse('\n'.join(lines))[0])

class Tests(unittest.TestCase):
    def test_exact_numeric_limb_order(self):
        s=decode(pages());self.assertEqual(s.words,tuple(words()))
        f=s.fields();self.assertEqual(f['owner'],0x123456789abcdef0);self.assertEqual(f['core_cycle'],0x2ffffffff)
        self.assertEqual(f['base_tag_numeric'],E['exact_fields']['base_tag_numeric'])
        self.assertTrue(c.fixture_checks(s,E)['matches'])
    def test_log_prefix_ansi_states_and_reordered_pages(self):
        g,states=c.parse('unrelated\nUSB_TRACE cpl1 v=1 result=capturing\nUSB_TRACE cpl1 v=1 result=retained pages=10\n'+'\n'.join('2026 [INFO] \x1b[32m'+x+'\x1b[0m'for x in reversed(pages())))
        self.assertEqual(c.select(g).words,tuple(words()));self.assertEqual(len(states),2)
    def test_every_missing_page_rejected(self):
        for i in range(10):
            with self.subTest(page=i),self.assertRaises(ValueError):decode(pages()[:i]+pages()[i+1:])
    def test_duplicate_rejected_even_identical(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):decode(pages()+pages()[:1])
    def test_unsupported_truncated_malformed_page(self):
        for line in [pages()[0].replace('v=1','v=2'),pages()[0][:-2],pages()[0].replace('off=500','off=504'),pages()[0]+' garbage','USB_TRACE cpl1 v=1 page=10 cookie=00000001 gen=1 off=5a0 words=00000000,00000000,00000000,00000000']:
            with self.subTest(line=line),self.assertRaises(ValueError):decode([line]+pages()[1:])
    def test_envelope_and_embedded_pairs_must_agree(self):
        for lines in [pages(cookie=999),pages(gen=8),[pages()[0].replace('gen=7','gen=8')]+pages()[1:]]:
            with self.assertRaises(ValueError):decode(lines)
    def test_multiple_groups_require_explicit_selection(self):
        w=words();w[0]=22;w[1]=8
        g,_=c.parse('\n'.join(pages()+pages(w)))
        with self.assertRaises(ValueError):c.select(g)
        self.assertEqual(c.select(g,(22,8)).words,tuple(w))
        with self.assertRaises(ValueError):c.select(g,(22,9))
    def test_quarantine_exhaustion_locks_reserved(self):
        for i,v in [(0,0),(1,0xffffffff),(2,0),(3,8),(3,1<<11),(3,1<<12),(3,1<<31),(25,0),(25,1),(25,2),(25,128),(24,16),(35,16),(35,32),(38,1),(39,1)]:
            with self.subTest(i=i,v=v),self.assertRaises(ValueError):
                w=words();w[i]=v;decode(pages(w))
    def test_inconsistent_completed_canvas_rejected(self):
        for i,v in [(32,0),(34,345599),(35,5),(35,9),(36,1)]:
            with self.subTest(i=i,v=v),self.assertRaises(ValueError):
                w=words();w[i]=v;decode(pages(w))
    def test_actual_crc_never_replaced(self):
        w=words();w[33]=0x12345678;s=decode(pages(w));r=c.fixture_checks(s,E)
        self.assertFalse(r['matches']);self.assertEqual(r['checks']['canvas_crc32_hex']['actual'],'12345678')
        self.assertEqual(s.fields()['canvas_crc32_hex'],'12345678')
    def test_incomplete_locked_capture_valid_but_not_fixture(self):
        w=[0]*40;w[:3]=[1,1,0x10000];w[25]=3;s=decode(pages(w))
        self.assertFalse(c.fixture_checks(s,E)['matches'])
    def test_busy_new_capture_and_ignored_writes_do_not_fake_bank_release(self):
        w=words();w[31]=44
        r=c.fixture_checks(decode(pages(w)),E);self.assertTrue(r['matches']);self.assertIn('not chip ACKs',r['limits'])
        w[3]|=1<<4;self.assertFalse(c.fixture_checks(decode(pages(w)),E)['matches'])
    def test_wrong_fixture_or_unknown_schema_rejected_or_mismatch(self):
        w=words();w[9]=1;self.assertFalse(c.fixture_checks(decode(pages(w)),E)['matches'])
        with self.assertRaises(ValueError):c.fixture_checks(decode(pages()),dict(schema='future'))
        with self.assertRaises(ValueError):c.fixture_checks(decode(pages()),dict(schema=E['schema'],exact_fields={}))
    def test_no_records_or_long_invalid_record(self):
        for text in ['nothing','USB_TRACE cpl1 '+'x'*200]:
            with self.assertRaises(ValueError):c.select(c.parse(text)[0])
    def test_cli_new_output_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='cpl1-test-')as t:
            p=Path(t);(p/'input.log').write_text('\n'.join(pages()))
            cmd=[sys.executable,str(P/'cpl1_snapshot.py'),'--log',str(p/'input.log'),'--expectation',str(P/'frame0-expectation.json'),'--require-fixture','--output',str(p/'result.json')]
            r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
            result=json.loads((p/'result.json').read_text());self.assertTrue(result['fixture']['matches']);self.assertIn('Not attested',result['origin'])
            before=(p/'result.json').read_bytes();r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertEqual((p/'result.json').read_bytes(),before)
    def test_cli_requires_selector_pair_and_expectation_for_gate(self):
        for args in [['--cookie','1'],['--require-fixture']]:
            r=subprocess.run([sys.executable,str(P/'cpl1_snapshot.py'),'--log','not-opened',*args],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)

if __name__=='__main__':unittest.main()
