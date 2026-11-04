from dataclasses import replace
import unittest
import facts,gateway
class GatewayTests(unittest.TestCase):
    def test_source_extraction(self):
        f=facts.extract()
        self.assertEqual((f['cpu_hz'],f['header_bytes'],f['payload_bytes'],f['dma_buffer_bytes']),(240000000,40,1024,1065))
        self.assertEqual((f['udp_mailbox_packets'],f['wifi_static_rx'],f['wifi_dynamic_rx']),(6,10,32))
        self.assertFalse(f['external_psram_enabled']);self.assertFalse(f['ar02_gf02_implemented'])
    def test_one_working_packet_plus_six_mailbox(self):
        r=gateway.simulate([dict(id=0,bytes=8*1024)],replace(gateway.Config(),burst_packets=8,burst_spacing_us=0))
        self.assertEqual(r['counters']['mailbox_full'],1)
        self.assertEqual((r['peak_mailbox'],r['peak_dma_working_packets']),(6,1))
        self.assertEqual(r['completed_frames'],0);self.assertTrue(r['queue_drained'])
    def test_sequential_recovery_after_lost_packet(self):
        r=gateway.simulate([dict(id=0,bytes=8*1024),dict(id=1,bytes=1024)],replace(gateway.Config(),burst_packets=8,burst_spacing_us=0))
        self.assertEqual([c['id'] for c in r['completed']],[1])
    def test_monotone_cpu_cost_and_bus_service(self):
        cfg=gateway.Config();frames=[dict(id=i,bytes=16000) for i in range(10)]
        a=gateway.simulate(frames,cfg);b=gateway.simulate(frames,replace(cfg,cpu_fraction=.3))
        self.assertGreater(b['service_total_us'],a['service_total_us'])
        self.assertGreater(b['maximum_completed_age_ms'],a['maximum_completed_age_ms'])
        self.assertLess(gateway.packet_service_us(1024,0,replace(cfg,qspi_write_hz=80_000_000))['dma_blocking_us'],gateway.packet_service_us(1024,0,cfg)['dma_blocking_us'])
    def test_fifo_credit_failure_and_hypothetical_wait(self):
        cfg=replace(gateway.Config(),fifo_bytes=1024,fpga_drain_bytes_per_second=100000);frames=[dict(id=0,bytes=4096)]
        a=gateway.simulate(frames,cfg);b=gateway.simulate(frames,replace(cfg,fifo_policy='bounded_fifo_wait',maximum_fifo_wait_ms=20))
        self.assertGreater(a['counters'].get('fifo_overflow',0),0)
        self.assertEqual(b['completed_frames'],1);self.assertTrue(b['fifo_waits_us'])
    def test_lock_busy_drops_frame(self):
        r=gateway.simulate([dict(id=0,bytes=1024)],replace(gateway.Config(),lock_busy_ms=16.6666667))
        self.assertEqual(r['counters']['begin_device_lock_busy'],1);self.assertEqual(r['completed_frames'],0)
        self.assertEqual(r['counters'].get('abort_calls',0),0)
    def test_ram_not_free_512k_or_psram(self):
        r=gateway.ram_budget(facts.extract(),available_internal_bytes=256*1024,largest_dma_block_bytes=1024)
        self.assertFalse(r['fit_proven']);self.assertFalse(r['psram_assumed']);self.assertFalse(r['contiguous_requirement_met_by_assumption'])
        self.assertEqual(r['reserve_bytes']['working_dma'],1065)
    def test_raw_rate_not_goodput(self):
        cfg=gateway.Config();s=gateway.packet_service_us(1024,0,cfg)
        self.assertGreater(s['cpu_us']+s['poll_us']+s['dma_blocking_us'],1024*8/160)
        self.assertEqual(s['cpu_cycles'],1024*(8*5+2*2)+2000)
    def test_abort_recovery_can_overflow_mailbox(self):
        frames=[dict(id=i,bytes=16000) for i in range(10)]
        cfg=replace(gateway.Config(),lock_period_ms=1000,lock_busy_ms=1,lock_phase_ms=3.5)
        a=gateway.simulate(frames,cfg);b=gateway.simulate(frames,replace(cfg,abort_recovery_ms=100))
        self.assertGreater(a['counters'].get('device_lock_busy',0),0)
        self.assertGreater(b['abort_service_us'],a['abort_service_us'])
        self.assertGreater(b['counters'].get('mailbox_full',0),a['counters'].get('mailbox_full',0))
    def test_maximum_frame_30fps_wire_requirement(self):
        r=gateway.simulate([dict(id=i,bytes=49152) for i in range(60)])
        self.assertAlmostEqual(r['required_ipv4_udp_mbps'],12.57984)
        self.assertEqual(r['capture_id_denominator'],60)
        self.assertGreater(r['drain_end_ms'],r['capture_window_ms'])
    def test_invalid_limits(self):
        for cfg in [replace(gateway.Config(),mailbox_packets=0),replace(gateway.Config(),cpu_fraction=2),replace(gateway.Config(),fifo_policy='free')]:
            with self.assertRaises(ValueError):gateway.simulate([dict(id=0,bytes=1024)],cfg)
if __name__=='__main__':unittest.main()
