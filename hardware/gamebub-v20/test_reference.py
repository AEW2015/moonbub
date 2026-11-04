import ctypes,json,tempfile,unittest
from pathlib import Path
import numpy as np
import acceptance as a,reference as ref,export_contract as ec
class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.lib,cls.fn,cls.toolchain=a.compile_library(cls.temp.name)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_native_rejects_outside_contract_without_output_mutation(self):self.assertEqual(a.check_errors(self.fn),4)
    def test_basis_and_negative_rounding_sparse_matches_frozen(self):
        rng=np.random.default_rng(7);cases=rng.integers(-2048,2049,(128,8,8),dtype=np.int32)*255
        for values,expected in zip(cases,ref.stripe.ft.inverse(cases)):
            out=np.full((8,8),-999,np.int32);w=a.Work();self.assertEqual(self.fn(values.ctypes.data_as(a.PTR),out.ctypes.data_as(a.PTR),ctypes.byref(w)),0);np.testing.assert_array_equal(out,expected)
    def test_inplace_and_optional_work_follow_same_arithmetic(self):
        values=np.zeros((8,8),np.int32);values[0,0]=-8193;expected=ref.stripe.ft.inverse(values)
        self.assertEqual(self.fn(values.ctypes.data_as(a.PTR),values.ctypes.data_as(a.PTR),None),0);np.testing.assert_array_equal(values,expected)
    def test_wire_offsets_match_frozen_formats_and_crc_rejects(self):
        d=ec.build();self.assertEqual(d['layouts']['AR03']['field_bytes'],61);self.assertEqual(d['layouts']['FG19']['total_header_or_message_bytes'],36)
        packet=ec.fc.seal(ec.fc.REQUEST,0,1,1,1200,123)
        with self.assertRaises(ValueError):ec.fc.parse(packet[:-1]+bytes([packet[-1]^1]))
    def test_readmemh_export_matches_selected_signed_vector(self):
        from export_mem import export
        if not (ref.HERE/'golden-index.json').is_file():self.skipTest('generate golden-index first')
        with tempfile.TemporaryDirectory() as folder:
            m=export('signed-edges',0,2,folder);self.assertEqual(m['blocks'],2)
            words=(Path(folder)/'dequantized.mem').read_text().splitlines();self.assertEqual(len(words),128);self.assertEqual(int(words[64],16),(-522240)&0xffffffff)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):export('signed-edges',0,257,folder)
if __name__=='__main__':unittest.main()
