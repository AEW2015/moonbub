import struct
import unittest
import zlib

import numpy as np

import pacing
import temporal


class TemporalTests(unittest.TestCase):
    def test_exact_immutable_chain_and_nochange(self):
        a = np.arange(32*32, dtype=np.uint16).reshape(32, 32)
        p = temporal.encode(a)
        ref, info = temporal.decode(p)
        self.assertTrue(np.array_equal(a, ref))
        b = a.copy()
        b[0:16, 0:16] = 42
        p = temporal.encode(b, ref, frame_id=1, reference_id=0)
        out, info = temporal.decode(p, ref, reference_id=0)
        self.assertEqual(info['changed_tiles'], 1)
        self.assertEqual(info['reference_copy_bytes'], 4096)
        self.assertTrue(np.array_equal(ref, a))
        self.assertTrue(np.array_equal(out, b))
        p = temporal.encode(b, out, frame_id=2, reference_id=1)
        again, info = temporal.decode(p, out, reference_id=1)
        self.assertEqual(info['changed_tiles'], 0)
        self.assertTrue(np.array_equal(again, b))

    def test_loss_rejects_dependents_and_keyframe_recovers(self):
        a = np.zeros((16, 32), np.uint16)
        p = temporal.encode(a, a, frame_id=2, reference_id=1)
        with self.assertRaises(ValueError):
            temporal.decode(p, a, reference_id=0)
        key = temporal.encode(a+1, frame_id=3)
        out, _ = temporal.decode(key)
        self.assertTrue(np.all(out == 1))
        with self.assertRaises(ValueError):
            temporal.decode(key, epoch=2)

    def test_receiver_monotonic_epoch_and_owned_reference(self):
        receiver = temporal.Receiver(epoch=7)
        source = np.zeros((16,32),np.uint16)
        packet = temporal.encode(source,epoch=7,frame_id=9)
        image, _ = receiver.receive(packet)
        image[:] = 12345  # Caller mutation must not corrupt the owned reference.
        delta = temporal.encode(source,source,epoch=7,frame_id=10,reference_id=9)
        recovered, _ = receiver.receive(delta)
        self.assertTrue(np.array_equal(recovered,source))
        for bad in (packet,temporal.encode(source+1,epoch=7,frame_id=1),
                    temporal.encode(source+1,epoch=8,frame_id=11)):
            with self.assertRaises(ValueError): receiver.receive(bad)
            self.assertEqual(receiver.last_frame_id,10)
        self.assertFalse(receiver._reference.flags.writeable)
        self.assertEqual(receiver.epoch,7)

    def test_receiver_loss_then_refresh_recovers_atomically(self):
        receiver = temporal.Receiver()
        source = np.zeros((16,32),np.uint16)
        receiver.receive(temporal.encode(source,frame_id=0))
        # Frame1 never arrives; frame2 refers to its unavailable reconstruction.
        dependent = temporal.encode(source+2,source+1,frame_id=2,reference_id=1)
        with self.assertRaises(ValueError): receiver.receive(dependent)
        self.assertEqual(receiver.last_frame_id,0)
        key = bytearray(temporal.encode(source+3,frame_id=3));key[-1]^=1
        with self.assertRaises(ValueError): receiver.receive(key)
        self.assertEqual(receiver.last_frame_id,0)
        image,_ = receiver.receive(temporal.encode(source+4,frame_id=4))
        self.assertTrue(np.all(image==4))
        image,_ = receiver.receive(temporal.encode(source+5,source+4,frame_id=5,reference_id=4))
        self.assertTrue(np.all(image==5))

    def test_reserved_epochs_and_reset_do_not_accept_old_session(self):
        source=np.zeros((16,16),np.uint16)
        packet=bytearray(temporal.encode(source))
        struct.pack_into('<I',packet,4,temporal.NO_REF)
        packet[-4:]=struct.pack('<I',zlib.crc32(packet[:-4]))
        with self.assertRaises(ValueError): temporal.Receiver(temporal.NO_REF)
        with self.assertRaises(ValueError): temporal.decode(packet,epoch=temporal.NO_REF)
        old=temporal.encode(source,epoch=1,frame_id=0)
        with self.assertRaises(ValueError): temporal.Receiver(2).receive(old)

    def test_semantic_corruption_with_recomputed_crc(self):
        a = np.zeros((16, 32), np.uint16)
        body = bytearray(temporal.encode(a)[:-4])
        body[temporal.HEADER.size:temporal.HEADER.size+4] = b'\x00\x00\x00\x00'
        with self.assertRaises(ValueError):
            temporal.decode(bytes(body)+struct.pack('<I', zlib.crc32(body)))
        p = bytearray(temporal.encode(a))
        p[-1] ^= 1
        with self.assertRaises(ValueError):
            temporal.decode(bytes(p))


class PacingTests(unittest.TestCase):
    def test_wire_and_bounds(self):
        self.assertEqual(pacing.wire_bytes(1025), 1161)
        with self.assertRaises(ValueError):
            pacing.simulate([1], link_mbps=0)

    def test_latest_bounds_backlog_and_fifo_grows(self):
        kwargs = dict(link_mbps=4, cap=262144)
        latest = pacing.simulate([40000]*90, policy='latest', **kwargs)
        fifo = pacing.simulate([40000]*90, policy='fifo', **kwargs)
        self.assertTrue(latest['dropped'])
        self.assertGreater(fifo['max_age_ms'], latest['max_age_ms']*5)
        self.assertEqual(fifo['transmitted'], 90)

    def test_strict_window_not_eventual(self):
        result = pacing.simulate([1000]*30, phase_ms=32)
        self.assertEqual(result['presented_eventual'], 30)
        self.assertLess(result['presented_strict_window'], 30)
        self.assertEqual(pacing.simulate([50000], cap=49152)['transmitted'], 0)


    def test_cap_drop_rejects_dependent_until_refresh(self):
        result=pacing.simulate([1000,50000,1000,1000,1000],
                               references=[None,0,1,None,3],cap=49152)
        self.assertEqual(result['transmitted'],4)
        self.assertEqual(result['decoded'],3)
        self.assertEqual(result['reference_rejected'],1)
        self.assertEqual(result['rejected'][0]['id'],2)
        self.assertEqual([x['id'] for x in result['records']],[0,3,4])
        self.assertGreater(result['rejected'][0]['qspi_end_ms'],
                           result['rejected'][0]['network_start_ms'])
        self.assertEqual(result['input_count'],result['transmitted']+len(result['dropped']))

    def test_latest_drop_rejects_dependents_then_refresh_chain_recovers(self):
        references=[None]+[i-1 for i in range(1,32)]
        references[30]=None
        result=pacing.simulate([20000]*32,link_mbps=1,cap=49152,references=references)
        self.assertTrue(any(x['reason']=='replaced' for x in result['dropped']))
        self.assertGreater(result['reference_rejected'],0)
        self.assertEqual([x['id'] for x in result['records']],[0,30,31])
        self.assertEqual(result['transmitted'],result['decoded']+result['reference_rejected'])
        self.assertEqual(result['decoded'],result['presented_eventual']+result['superseded_at_vblank'])

    def test_shared_vblank_winner_and_exact_window_boundary(self):
        result=pacing.simulate([1]*10,fps=10000,decode_ms=0,link_mbps=10000,qspi_mbps=10000)
        self.assertEqual(result['decoded'],10)
        self.assertEqual(result['presented_eventual'],1)
        self.assertEqual(result['superseded_at_vblank'],9)
        # One frame becomes eligible exactly at the excluded 1000ms endpoint.
        result=pacing.simulate([1],fps=1,link_mbps=10000,qspi_mbps=10000,
                               decode_ms=999,refresh_hz=1)
        self.assertEqual(result['records'][0]['eligible_vblank_ms'],1000)
        self.assertEqual(result['presented_eventual'],1)
        self.assertEqual(result['presented_strict_window'],0)

    def test_invalid_references_and_nonfinite_parameters(self):
        for refs in ([0],[None,2],[None,-1],[None,True],[]):
            with self.assertRaises(ValueError): pacing.simulate([1,1],references=refs)
        for kwargs in ({'decode_ms':float('nan')},{'fps':float('inf')}):
            with self.assertRaises(ValueError): pacing.simulate([1],**kwargs)


if __name__ == '__main__':
    unittest.main()
