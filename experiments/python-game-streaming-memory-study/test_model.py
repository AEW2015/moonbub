from dataclasses import replace
import unittest
import model

def trace(publication=False,key=False):
    stripes=[]
    for p,w,h in [(0,720,480),(1,360,240),(2,360,240)]:
        for y in range(0,h,8):stripes.append(dict(plane=p,width=w,rows=8,y=y,blocks=w//8,general=0,dc=0,zero=w//8))
    return dict(width=720,height=480,key=key,publication=publication,packet_bytes=2048,plane_payload_bytes=1800,crc_validation_bytes=6000,ui_pixels=21120,stripes=stripes)

class MemoryTests(unittest.TestCase):
    def test_explicit_layout_window_and_local_scratch(self):
        a=model.allocation(model.Config());b=model.allocation(replace(model.Config(),mode='streaming'))
        self.assertEqual(a['external_address_end']-b['external_address_end'],1037312)
        self.assertFalse(model.allocation(replace(model.Config(),address_window_bytes=2*1024*1024))['window_sufficient'])
        self.assertEqual(b['local_bytes']['reconstructed_tag_stripe'],11520)
        ranges=sorted((r['address'],r['address']+r['padded_bytes']) for r in a['regions'].values())
        self.assertTrue(all(x[1]<=y[0] for x,y in zip(ranges,ranges[1:])))
    def test_streaming_retains_sha_work_avoids_coeff_scratch_and_tag_read(self):
        t=trace(publication=True);a=model.stages(t,model.Config(),100000,200000,1000000,0,3000000)
        b=model.stages(t,replace(model.Config(),mode='streaming'),100000,200000,1000000,0,0)
        total=lambda s:sum(x[2] for x in s if x[0]=='memory')
        self.assertEqual(total(a)-total(b),2*1036800+518400)
        # All real SHA compression work remains in both; only explicit stage order changes.
        cpu=lambda s:sum(x[1] for x in s if x[0]=='compute')
        self.assertLessEqual(abs(cpu(a)-cpu(b)),120)
    def test_capture_pools_references_and_drain_are_bounded(self):
        cfg=replace(model.Config(),frames=3,drain_ms=100,mode='streaming',read_cycles=8,write_cycles=8,mac_lanes=16,sample_positions_per_cycle=4)
        r=model.simulate([trace()],cfg)
        self.assertTrue(r['decoder_drained']);self.assertFalse(r['unresolved_ids'])
        self.assertLessEqual(r['peak_bounds']['input_slots'],2)
        self.assertLessEqual(r['peak_bounds']['reference_readers'],1)
        self.assertEqual(r['display_line_misses'],0)
        self.assertEqual(len({p['id'] for p in r['presented']}),len(r['presented']))
    def test_long_nonpreemptible_stall_can_fail_line_deadline(self):
        cfg=replace(model.Config(),frames=2,drain_ms=50,mode='streaming',stall_cycles=20000,stall_period=100000,stall_phase=20000,prefetch_lines=1)
        r=model.simulate([trace()],cfg)
        self.assertGreater(r['display_line_misses'],0)
        self.assertGreater(r['bus_counters']['stall_cycles'],0)
    def test_refresh_debt_and_turnaround_are_charged(self):
        cfg=replace(model.Config(),frames=1,drain_ms=50,mode='streaming')
        r=model.simulate([trace()],cfg)
        self.assertGreater(r['bus_counters']['refresh_cycles'],0)
        self.assertGreater(r['bus_counters']['row_changes'],0)
        self.assertGreater(r['bus_counters']['turnarounds'],0)
        self.assertGreater(r['bus_counters']['background_bursts'],0)
    def test_current_window_rejects_before_simulating(self):
        r=model.simulate([trace()],replace(model.Config(),address_window_bytes=2*1024*1024))
        self.assertEqual(r['status'],'address_window_rejected')
    def test_unaligned_reads_charge_head_and_tail_burst_overfetch(self):
        r=model.Request(15,2,False,lambda:None)
        self.assertEqual((r.address,r.bursts),(0,2))
    def test_logical_front_switches_are_not_clean_frames_after_underrun(self):
        cfg=replace(model.Config(),frames=2,drain_ms=100,mode='streaming',stall_cycles=20000,stall_period=100000,stall_phase=20000,prefetch_lines=1)
        r=model.simulate([trace()],cfg)
        self.assertGreater(r['display_line_misses'],0)
        self.assertLessEqual(r['clean_eventual_unique_ids'],r['eventual_presentations'])
    def test_invalid_limits(self):
        for cfg in [replace(model.Config(),prefetch_lines=0),replace(model.Config(),refresh_cycles=780),replace(model.Config(),stall_cycles=100000),replace(model.Config(),mode='free')]:
            with self.assertRaises(ValueError):model.simulate([trace()],cfg)

if __name__=='__main__':unittest.main()
