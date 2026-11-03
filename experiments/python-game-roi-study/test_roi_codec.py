import struct
import unittest
import zlib
import numpy as np
import roi_codec as rc


def repair(body):return body+struct.pack('<I',zlib.crc32(body))


class RoiTests(unittest.TestCase):
    def test_uniform_maps_match_frozen_pixels(self):
        rng=np.random.default_rng(701)
        for h,w in ((2,2),(18,34),(48,64)):
            rgb=rng.integers(0,256,(h,w,3),dtype=np.uint8)
            mw,mh=rc.geometry(w,h)
            for scale in rc.SCALES:
                packet=rc.encode(rgb,np.full((mh,mw),scale,np.uint8))
                np.testing.assert_array_equal(rc.decode(packet),rc.ft.reconstruct(rgb,scale))
                self.assertLessEqual(len(packet),rc.info(packet)['raw_bound_bytes'])

    def test_nonuniform_golden_reconstruction(self):
        rng=np.random.default_rng(702);rgb=rng.integers(0,256,(34,50,3),dtype=np.uint8)
        scale_map=rc.declared_map(50,34,[(1,1,17,17)],8,32)
        packet=rc.encode(rgb,scale_map);w,h,m,coeff=rc.parse(packet)
        np.testing.assert_array_equal(m,scale_map)
        golden=rc.ft.planes_to_rgb(rc.reconstruct_planes(rc.quantized(rgb,scale_map),scale_map,w,h))
        np.testing.assert_array_equal(rc.decode(packet),golden)

    def test_crc_lengths_profile_and_map_rejections(self):
        rgb=np.full((18,34,3),90,np.uint8);mw,mh=rc.geometry(34,18)
        packet=rc.encode(rgb,np.full((mh,mw),8,np.uint8))
        for malformed in (packet[:-1],packet+b'\0',packet[:-1]+bytes([packet[-1]^1]),b'BAD!'+packet[4:]):
            with self.assertRaises(ValueError):rc.decode(malformed)
        body=bytearray(packet[:-4]);body[rc.HEADER.size]|=0xc0
        with self.assertRaises(ValueError):rc.decode(repair(bytes(body)))
        body=bytearray(packet[:-4]);nmap=(mw*mh+3)//4;body[rc.HEADER.size+nmap-1]|=1
        with self.assertRaises(ValueError):rc.decode(repair(bytes(body)))
        fields=list(rc.HEADER.unpack_from(packet));fields[7]+=1
        body=rc.HEADER.pack(*fields)+packet[rc.HEADER.size:-4]
        with self.assertRaises(ValueError):rc.decode(repair(body))
        fields=list(rc.HEADER.unpack_from(packet));fields[8]=0xffffffff
        body=rc.HEADER.pack(*fields)+packet[rc.HEADER.size:-4]
        with self.assertRaises(ValueError):rc.decode(repair(body))

    def test_nested_coefficient_crc_is_checked(self):
        rgb=np.full((32,32,3),110,np.uint8);packet=rc.encode(rgb,np.full((2,2),16,np.uint8))
        body=bytearray(packet[:-4]);pos=rc.HEADER.size+1;body[pos+rc.cc.COEFF.size]^=1
        with self.assertRaises(ValueError):rc.decode(repair(bytes(body)))

    def test_map_and_roi_domain(self):
        rgb=np.zeros((16,16,3),np.uint8)
        for m in (np.ones((1,1),np.uint8),np.full((1,1),8,np.int16),np.full((2,2),8,np.uint8)):
            with self.assertRaises(ValueError):rc.encode(rgb,m)
        for rect in ((-1,0,1,1),(0,0,17,1),(0,0,0,1)):
            with self.assertRaises(ValueError):rc.declared_map(16,16,[rect])


if __name__=='__main__':unittest.main()
