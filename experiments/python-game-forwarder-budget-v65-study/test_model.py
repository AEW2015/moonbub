"""Fragment boundaries, exact phase timing and declared allocation scopes."""
from fractions import Fraction
import unittest
import helpers as h
import model as m
import benchmark as b

class ForwardBudgetTests(unittest.TestCase):
    def test_fragment_boundaries_and_exact_ceil_including_MAX(self):
        for size,n,tail in((1,1,1),(1023,1,1023),(1024,1,1024),(1025,2,1),(m.MAX_FRAME-1,256,1023),(m.MAX_FRAME,256,1024)):
            parts=m.fragment_lengths(size);self.assertEqual((len(parts),parts[-1]),(n,tail));self.assertEqual(sum(parts),size)
        for bad in(0,-1,m.MAX_FRAME+1,True,1.0):
            with self.assertRaises(ValueError):m.fragment_lengths(bad)
        self.assertEqual(len(m.fragment_lengths(1024,512)),2)
    def test_header_is_network_only_and_phase_boundary_exact(self):
        current=m.frame(1025);small=m.frame(1025,header=8)
        self.assertEqual(current['L3_IPv4_UDP_bytes'],1025+2*68);self.assertEqual(current['total_QSPI_clocks'],2*1025+16*2)
        self.assertEqual(current['total_QSPI_clocks'],small['total_QSPI_clocks']);self.assertEqual(current['L3_IPv4_UDP_bytes']-small['L3_IPv4_UDP_bytes'],64)
        self.assertEqual(m.qspi_us(1024,40_000_000),Fraction(258,5))
        used,margin,passes=m.scenario(m.MAX_FRAME,10_000_000,0,0)
        self.assertLess(margin,0);self.assertFalse(passes)
        left,each=m.residual(1025,40_000_000,10000);self.assertEqual(each*2,left)
        self.assertEqual(left,m.PERIOD_US-m.qspi_us(1025,40_000_000)-10000)
    def test_rust_allocation_scope_and_backend_constraints_are_not_memory_FPS_claims(self):
        audit=b.evidence();self.assertEqual(audit['runtime_internal_DMA_buffer_bytes'],m.HEADER+m.CHUNK+1)
        self.assertEqual(audit['runtime_internal_DMA_buffer_bytes'],1065);self.assertEqual(audit['boot_programming_DMA_scratch_bytes'],16384)
        self.assertEqual(audit['streaming_thread_stack_declared_bytes'],16384);self.assertFalse(audit['current_CS38_deployable'])
        self.assertIn('before session',audit['boot_scratch_scope']);self.assertIn('Not total',audit['memory_scope'])

if __name__=='__main__':unittest.main()
