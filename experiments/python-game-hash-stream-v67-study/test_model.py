import unittest
import numpy as np
import model

class Checks(unittest.TestCase):
    def test_order_failure_poison_and_no_accept_after(self):
        s=model.TileHash('CU66_u8')
        with self.assertRaises(ValueError):s.feed(0,0,8,np.zeros((8,8),np.uint8))
        with self.assertRaises(ValueError):s.feed(0,0,0,np.zeros((8,8),np.uint8))
        self.assertEqual(s.tiles,0)
    def test_no_lossy_cast(self):
        for dtype in (np.int16,np.float32):
            s=model.TileHash('CU66_u8')
            with self.assertRaises(ValueError):s.feed(0,0,0,np.full((8,8),256,dtype))
            self.assertTrue(s.failed)
    def test_copied_input_and_early_finish(self):
        s=model.TileHash('CS66_i16');a=np.full((8,8),7,np.uint8);s.feed(0,0,0,a);a[:]=8
        np.testing.assert_array_equal(s.strip[:,:8],7)
        self.assertEqual(s.work()['serialized_bytes'],4)
        with self.assertRaises(ValueError):s.finish()
        self.assertTrue(s.failed)

if __name__=='__main__':unittest.main()
