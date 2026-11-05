import unittest
from unittest.mock import patch
import numpy as np
import helpers as h
model=h.module('hudfast42_test_model',h.HERE/'model.py')

class FastHUDTests(unittest.TestCase):
    def test_huffman_constant_random_and_bounded_domain_byte_parity(self):
        rng=np.random.default_rng(4201)
        samples=[np.full(100,13,np.uint16),np.arange(253,dtype=np.uint16),rng.integers(0,253,2048,dtype=np.uint16)]
        for values in samples:
            expected,stats=h.hud32._huff_encode(values)
            with patch('builtins.format',side_effect=AssertionError('per-symbol format forbidden')):
                actual,info=model.huff_encode(values)
            self.assertEqual(actual,expected);self.assertEqual(info,stats)
        for values in(np.array([],np.uint16),np.array([253],np.uint16),np.zeros(h.h.MAX_WORDS+1,np.uint16)):
            with self.assertRaises(ValueError):model.huff_encode(values)
    def test_explicit_legal_depth16_codebook_and_depth_rejection(self):
        lengths={s:s+1 for s in range(15)};lengths.update({15:16,16:16});values=np.tile(np.arange(17,dtype=np.uint16),3)
        codes=h.hud32._codes(lengths);expected=''.join(format(codes[int(v)][0],f'0{codes[int(v)][1]}b')for v in values)
        stream,bits=model._pack_codes(values,lengths);self.assertEqual(bits,len(expected))
        self.assertEqual(stream,(int(expected,2)<<((-len(expected))%8)).to_bytes((len(expected)+7)//8,'big'))
        frequencies=[1,1]
        while len(frequencies)<18:frequencies.append(sum(frequencies[-2:]))
        source=np.repeat(np.arange(18,dtype=np.uint16),frequencies)
        self.assertLessEqual(len(source),h.h.MAX_WORDS)
        with self.assertRaisesRegex(ValueError,'bounded Huffman code depth'):model.huff_encode(source)
        with self.assertRaisesRegex(ValueError,'bounded Huffman code depth'):h.hud32._huff_encode(source)
    def test_rice_empty_boundaries_runs_and_no_format(self):
        rng=np.random.default_rng(4202)
        samples=[np.array([],np.int64),np.zeros(12,np.int64),np.array([0,1,2,15,16,127,128]),np.array([h.h.MAX_WORDS]),rng.integers(0,200,20)]
        for values in samples:
            expected=h.hud33._rice_encode(values)
            with patch('builtins.format',side_effect=AssertionError('Rice format forbidden')):actual=model.rice_encode(values)
            self.assertEqual(actual,expected)
        for values in(np.array([-1]),np.array([h.h.MAX_WORDS+1]),np.array([[1]])):
            with self.assertRaises(ValueError):model.rice_encode(values)
    def test_channel_zero_runs_and_random_exact_selected_schemes(self):
        rng=np.random.default_rng(4203)
        for values in(np.zeros(400,np.uint16),np.repeat(np.array([0,6,0,17,4],np.uint16),70),rng.integers(0,253,500,dtype=np.uint16)):
            expected,old=h.hud33._channel_encode(values);actual,info=model.channel_encode(values)
            self.assertEqual(actual,expected);self.assertEqual(info,old)
        with self.assertRaises(ValueError):model.channel_encode(np.array([],np.uint16))
    def test_real_key_pipeline_no_global_mutation_and_baseline_validation(self):
        qual=h.load(h.QUAL/'results.json');old=qual['cases'][0]['rows'][0];baseline=h.raw(old['hud_packets']['HU25'],h.QUAL)
        snapshots=(h.hud32._huff_encode,h.hud33._rice_encode,h.hud33._channel_encode)
        p32,w32=model.encode_hud32(baseline);p33,w33=model.encode_hud33(baseline,p32)
        self.assertEqual(p32,h.raw(old['hud_packets']['HX32'],h.QUAL));self.assertEqual(p33,h.raw(old['hud_packets']['HX33_selected'],h.QUAL))
        self.assertEqual(snapshots,(h.hud32._huff_encode,h.hud33._rice_encode,h.hud33._channel_encode))
        self.assertTrue(w33['baseline_HU25_and_HX32_decode_validation_paid']);self.assertFalse(w33['cache_used'])
        wrong=bytearray(p32);wrong[-1]^=1
        with self.assertRaises(ValueError):model.encode_hud33(baseline,bytes(wrong))
        self.assertLessEqual(w32['work']['patch_materializations'],4);self.assertLessEqual(w33['work']['patch_materializations'],4)
    def test_private_huffman_plan_owns_input_until_emit(self):
        values=np.arange(50,dtype=np.uint16);plan=model._huff_plan(values);expected=model._huff_emit(plan)
        values[:]=0;self.assertEqual(model._huff_emit(plan),expected);self.assertFalse(np.shares_memory(plan['values'],values))

if __name__=='__main__':unittest.main()
