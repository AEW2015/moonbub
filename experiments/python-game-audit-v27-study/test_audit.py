import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import audit


def seal(data):
    return data + struct.pack('<I', zlib.crc32(data))


def sample_pair():
    rects=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
    hud_head=audit.HU25.pack(b'HU25',1,4,1,0,audit.NO_REF,720,480,bytes(16),b'h'*16,
                             1,1,1,1,1,1,1,1,*(v for r in rects for v in r))
    hud=seal(hud_head+b'WXYZ')
    gm_head=audit.GM27.pack(b'GM27',1,1,1,0,audit.NO_REF,720,480,32,18,bytes(16),b'g'*16,
                            1,0,1,1,1)
    gm=seal(gm_head+b'Q'+b'YCB')
    head=audit.CP27.pack(b'CP27',1,3,1,0,255,0,len(gm),len(hud),
                         hashlib.sha256(gm).digest()[:16],hashlib.sha256(hud).digest()[:16])
    return seal(head+gm+hud)


class V27AuditPrimitiveTests(unittest.TestCase):
    def test_nominal_rate_uses_complete_bytes_and_separates_id_rate(self):
        self.assertEqual(audit.projected_mbps(100_000,48),0.5)
        self.assertEqual(audit.projected_mbps(100_000,48,60),1.0)
        with self.assertRaises(ValueError): audit.projected_mbps(100_000,0)

    def test_complete_cp27_body_includes_base_hud_and_exact_binding(self):
        self.assertEqual(audit.complete_body_bytes(10_000,8_245,60),18_305)
        with self.assertRaises(ValueError): audit.complete_body_bytes(10_000,-1,60)
        with self.assertRaises(ValueError): audit.complete_body_bytes(True,1,60)

    def test_complete_cap_accepts_exact_boundary_and_rejects_one_over(self):
        self.assertTrue(audit.under_cap(49_152))
        self.assertFalse(audit.under_cap(49_153))
        with self.assertRaises(ValueError): audit.under_cap(-1)

    def test_quality_uses_integer_sse_and_exact_sample_denominator(self):
        self.assertEqual(audit.quality_stats(dict(active_squared_error=14_383_660,
                                                  active_channel_samples=1_000_000)),
                         (14_383_660,1_000_000,14.38366))
        with self.assertRaises(ValueError):
            audit.quality_stats(dict(active_squared_error=1,active_channel_samples=0))
        with self.assertRaises(ValueError):
            audit.quality_stats(dict(active_squared_error=2,active_channel_samples=1,active_mse=1.9))

    def test_same_reference_sse_guard_and_complete_cap_both_gate_candidate(self):
        self.assertTrue(audit.candidate_eligible(49_152,100,100))
        self.assertFalse(audit.candidate_eligible(49_153,1,100))
        self.assertFalse(audit.candidate_eligible(10_000,101,100))
        with self.assertRaises(ValueError): audit.candidate_eligible(-1,0,0)

    def test_cp27_actual_inner_lengths_crc_and_component_sha_bindings(self):
        packet=sample_pair(); parsed=audit.parse_cp27(packet)
        self.assertEqual((parsed['epoch'],parsed['frame'],parsed['flags'],parsed['bytes']),(1,0,3,len(packet)))
        self.assertEqual(parsed['hud_meta']['patch_words'],audit.HUD_WORDS)
        damaged=bytearray(packet);damaged[-5]^=1
        with self.assertRaises(ValueError): audit.parse_cp27(bytes(damaged))

    def test_ja27_is_65_bytes_and_binds_pair_and_both_reconstruction_tags(self):
        pair=audit.parse_cp27(sample_pair())
        body=audit.JA27.pack(b'JA27',1,pair['epoch'],pair['frame'],pair['pair_tag'],
                             pair['base_meta']['reconstructed_tag'],pair['hud_meta']['out_tag'])
        self.assertEqual(audit.parse_ja27(seal(body),pair)['bytes'],65)
        broken=bytearray(seal(body));broken[20]^=1
        with self.assertRaises(ValueError): audit.parse_ja27(bytes(broken),pair)

    def test_gm27_parser_accepts_bounded_syntax_without_encoder_optimality(self):
        parsed=audit.parse_cp27(sample_pair())
        self.assertEqual(parsed['base_meta']['bytes'],audit.GM27.size+8)
        self.assertTrue(parsed['base_meta']['key'])

    def test_lineage_requires_same_ids_source_hashes_and_reference_ids(self):
        left=[dict(id=i,source_common_yuv_sha256=f's{i}',reference_id=i-1) for i in range(2)]
        right=[dict(row) for row in left]
        audit.lineage(left,right)
        right[1]['reference_id']=7
        with self.assertRaises(ValueError): audit.lineage(left,right)
        right[1]['reference_id']=0;right[0]['source_common_yuv_sha256']='wrong'
        with self.assertRaises(ValueError): audit.lineage(left,right)

    def test_archive_verifier_checks_stored_raw_hash_bounds_and_safe_paths(self):
        raw=b'actual retained object';stored=zlib.compress(raw,9)
        desc=dict(path='objects/blob.zlib',raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),
                  stored_sha256=hashlib.sha256(stored).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);(base/'objects').mkdir();(base/'objects/blob.zlib').write_bytes(stored)
            self.assertEqual(audit.read_object(desc,base,enforce_repo_root=False),raw)
            bad=dict(desc,raw_bytes=1)
            with self.assertRaises(ValueError): audit.read_object(bad,base,enforce_repo_root=False)
            with self.assertRaises(ValueError): audit.read_object(dict(desc,path='../escape'),base,enforce_repo_root=False)


if __name__ == '__main__':
    unittest.main()
