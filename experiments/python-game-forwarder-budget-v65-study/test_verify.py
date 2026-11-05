"""Exact boundary/time/source-domain tests; no execution/RF performance claims."""
from fractions import Fraction
import json,unittest
import verify as v
subject=v.module('forward65_budget_subject',v.HERE/'model.py')

class ForwarderProofTests(unittest.TestCase):
    def test_fragment_ceil_tail_and_protocol_MAX(self):
        for size in(1,1023,1024,1025,44032,49152,262143,262144):
            expected=v.frame(size);self.assertEqual(subject.frame(size),expected)
            self.assertEqual(len(v.parts(size)),(size+1023)//1024);self.assertEqual(sum(v.parts(size)),size)
        for value in(0,-1,True,1.,262145):
            with self.subTest(value=value),self.assertRaises(ValueError):v.parts(value)
    def test_unknown_work_is_one_combined_amortized_allowance(self):
        elapsed,margin=v.budget(44032,40_000_000,10000,500)
        self.assertEqual(elapsed,Fraction(168594,5));self.assertEqual(margin,Fraction(-5782,15))
        actual=subject.scenario(44032,40_000_000,500,10000);self.assertEqual(actual,(elapsed,margin,False))
        self.assertEqual(v.qspi(1024,40_000_000),Fraction(258,5))
    def test_exact_zero_deadline_is_inclusive_and_negative_not_clamped(self):
        # Protocol-legal artificial boundary, not an actual retained CS38 frame.
        elapsed,margin=v.budget(49608,3_000_000,0,0)
        self.assertEqual(elapsed,v.PERIOD);self.assertEqual(margin,0)
        self.assertEqual(subject.scenario(49608,3_000_000,0,0),(elapsed,margin,True))
        elapsed,margin=v.budget(262144,10_000_000,0,0);self.assertLess(margin,0)
        self.assertEqual(subject.residual(262144,10_000_000)[0],margin)
    def test_header_changes_are_hypothetical_network_only(self):
        baseline=v.frame(1025);small=v.frame(1025,8)
        self.assertEqual(baseline['total_QSPI_clocks'],small['total_QSPI_clocks']);self.assertEqual(baseline['source_level_crc_bit_rounds'],small['source_level_crc_bit_rounds'])
        self.assertEqual(baseline['L3_IPv4_UDP_bytes']-small['L3_IPv4_UDP_bytes'],64)
    def test_current_codec_field_and_opaque_payload_are_different_constraints(self):
        packet=next(v.host.packets(b'CS38-not-a-JPEG',7,0));parsed=v.host.parse_packet(packet)
        self.assertEqual(parsed.payload,b'CS38-not-a-JPEG') # transport parse does not make the JPEG core decode it
        unknown=bytearray(packet);unknown[5]=2
        with self.assertRaises(ValueError):v.host.parse_packet(bytes(unknown))
    def test_readonly_source_evidence_and_requested_allocation_scopes(self):
        data=json.loads((v.HERE/'results.json').read_text());v.source_audit(data['audit'])
        self.assertFalse(data['audit']['current_CS38_deployable']);self.assertEqual(data['audit']['runtime_internal_DMA_buffer_bytes'],1065)
        self.assertEqual(data['audit']['boot_programming_DMA_scratch_bytes'],16384);self.assertEqual(data['audit']['streaming_thread_stack_declared_bytes'],16384)

if __name__=='__main__':unittest.main()
