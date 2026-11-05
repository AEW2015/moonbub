"""Independent resealed semantic-corruption checks, no encoder import."""
import unittest
import verify as v

class WireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=v.f.frozen.load(v.HERE/'results.json');rows=data['cases'][0]['rows']
        cls.key=v.f.frozen.raw(rows[0]['packet'],v.HERE)
        cls.predicted=v.f.frozen.raw(rows[1]['packet'],v.HERE)

    def rewrite(self,packet,change):
        outer=list(v.HEADER.unpack_from(packet));inner=packet[v.HEADER.size:v.HEADER.size+outer[11]]
        fields=list(v.m.HEADER.unpack_from(inner));tail=bytearray(inner[v.m.HEADER.size:-4])
        change(outer,fields,tail)
        inner=v.seal(v.m.HEADER.pack(*fields)+tail)
        return v.seal(v.HEADER.pack(*outer)+inner+packet[v.HEADER.size+outer[11]:-4])

    def test_unknown_plane_dispatch_rejected_without_publication(self):
        def mutate(outer,fields,tail):tail[fields[12]+fields[13]]=255
        bad=self.rewrite(self.key,mutate);rx=v.Receiver()
        with self.assertRaises(ValueError):rx.receive(bad)
        self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_wrong_inner_reconstruction_tag_rejected_without_publication(self):
        def mutate(outer,fields,tail):fields[11]=bytes([1])*16
        bad=self.rewrite(self.key,mutate);rx=v.Receiver()
        with self.assertRaises(ValueError):rx.receive(bad)
        self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

    def test_wrong_prior_reference_cannot_replace_accepted_key(self):
        def mutate(outer,fields,tail):outer[9]=fields[10]=bytes([1])*16
        bad=self.rewrite(self.predicted,mutate);rx=v.Receiver();rx.receive(self.key)
        saved=(rx.ref,rx.hud,rx.rid,rx.last)
        with self.assertRaises(ValueError):rx.receive(bad)
        self.assertIs(rx.ref,saved[0]);self.assertIs(rx.hud,saved[1]);self.assertEqual((rx.rid,rx.last),saved[2:])

if __name__=='__main__':unittest.main()
