"""Independent seeded differential checks of valid-header malformed payloads."""
import struct
import unittest
import zlib
import numpy as np
import word_coeff as wc


class DifferentialFuzzTests(unittest.TestCase):
    def test_two_thousand_valid_crc_payloads_match_acceptance_and_values(self):
        rng=np.random.default_rng(719)
        old=wc.frozen_codec
        accepted=rejected=0
        for case in range(2000):
            blocks=(case%4)+1
            ndc=int(rng.integers(1,12));nac=int(rng.integers(3,40))
            dc=bytes([int(rng.integers(0,14))])+rng.integers(0,256,ndc-1,dtype=np.uint8).tobytes()
            ac=rng.integers(0,12,3,dtype=np.uint8).tobytes()+rng.integers(0,256,nac-3,dtype=np.uint8).tobytes()
            body=old.COEFF.pack(b'CP02',1,1,blocks,1,0,len(dc),len(ac))+dc+ac
            packet=body+struct.pack('<I',zlib.crc32(body))
            answers=[]
            for decode in (old.decode_coefficients,wc.decode_coefficients):
                try:answers.append(('ok',decode(packet,blocks,1)))
                except ValueError:answers.append(('reject',None))
            self.assertEqual(answers[0][0],answers[1][0],case)
            if answers[0][0]=='ok':
                accepted+=1
                np.testing.assert_array_equal(answers[0][1],answers[1][1])
            else:rejected+=1
        self.assertGreater(rejected,0)
        # This campaign need not produce valid frames: deterministic valid
        # families and canonical-edge fixtures are checked by the other suite.


if __name__=='__main__':unittest.main()
