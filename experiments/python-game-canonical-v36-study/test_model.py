"""Focused ownership, coefficient omission and publication tests for CN36."""
import unittest,struct,zlib
import numpy as np
import helpers as h
m=h.module('canonical36_unit_model',h.HERE/'model.py')
class CanonicalTests(unittest.TestCase):
    def test_geometry_and_ownership(self):
        self.assertEqual([int(v.sum()) for v in m.HIDDEN],[256,19,19])
        source=tuple(np.full(s,42,np.int16) for s in ((480,720),(240,360),(240,360)))
        out=m.normalize(source)
        for a,b in zip(source,out):
            self.assertFalse(np.shares_memory(a,b));self.assertTrue(np.all(a==42))
        with self.assertRaises(ValueError):m.zero_hidden((np.zeros((1,8,8),np.int16),)*3)
    def test_coefficients_preserved_outside(self):
        rng=np.random.default_rng(36);source=tuple(rng.integers(-12,13,(len(v),8,8),dtype=np.int16) for v in m.HIDDEN)
        result=m.zero_hidden(source)
        for a,b,hidden in zip(source,result,m.HIDDEN,strict=True):
            np.testing.assert_array_equal(a[~hidden],b[~hidden]);self.assertFalse(np.any(b[hidden]));self.assertFalse(np.shares_memory(a,b))
    def test_malformed_no_publish(self):
        rx=m.Receiver();before=(rx.ref,rx.rid,rx.hud,rx.last)
        for packet in (b'',b'CN36'+bytes(200),bytearray(300)):
            with self.assertRaises(ValueError):rx.receive(packet)
            self.assertEqual(before,(rx.ref,rx.rid,rx.hud,rx.last))
if __name__=='__main__':unittest.main()
