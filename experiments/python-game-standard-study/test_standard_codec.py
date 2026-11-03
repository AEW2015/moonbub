import unittest
import numpy as np
import standard_codec as sc


class ReferenceTests(unittest.TestCase):
    def frames(self):
        a=np.zeros((480,720,3),np.uint8);a[120:180,180:240]=[180,160,140]
        return [a,np.roll(a,4,axis=1)]

    def verify(self,name):
        outputs,info=sc.run(self.frames(),name,35)
        self.assertEqual(sorted(outputs),[0,1]);self.assertEqual(info['output_pts'],[0,1])
        self.assertFalse(info['unconsumed_options'])
        self.assertEqual(info['coded_bytes'],sum(p['bytes'] for p in info['packets'])+info['extradata_bytes'])
        self.assertTrue(all(a.shape==(480,720,3) and a.dtype==np.uint8 for a in outputs.values()))
        self.assertTrue(all(p['pts']==p['dts'] for p in info['packets']))
        self.assertEqual(info['packets_returned_only_at_flush'],len(info['packets'])-sum(len(c['emitted_pts']) for c in info['frame_calls']))

    def test_hevc_native_roundtrip_pts_and_byte_accounting(self):self.verify('libx265')
    def test_av1_native_roundtrip_pts_and_byte_accounting(self):self.verify('libsvtav1')
    def test_reject_missing_input_and_unknown_encoder(self):
        with self.assertRaises(ValueError):sc.run([],'libx265',32)
        with self.assertRaises(ValueError):sc.options('generic',32)


if __name__=='__main__':unittest.main()
