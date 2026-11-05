"""Exact local guard and immutable incoming-reference fork semantics."""
import json,unittest
import verify as v

class GuardProofTests(unittest.TestCase):
    def test_full_ties_keep_zero(self):self.assertEqual(v.choose(b'aa',10,b'bb',10),'zero')
    def test_either_strict_improvement_requires_other_nonworse(self):
        self.assertEqual(v.choose(b'aaa',10,b'bb',10),'global_grid')
        self.assertEqual(v.choose(b'aa',10,b'bb',9),'global_grid')
        self.assertEqual(v.choose(b'aaa',10,b'bb',9),'global_grid')
        self.assertEqual(v.choose(b'aaa',10,b'bb',11),'zero')
        self.assertEqual(v.choose(b'aa',10,b'bbb',9),'zero')
    def test_final_cap_and_no_selectable_proposal(self):
        self.assertEqual(v.choose(b'z'*49153,10,b'g'*49152,10),'global_grid')
        self.assertIsNone(v.choose(b'z'*49153,10,b'g'*49152,11))
        self.assertIsNone(v.choose(b'z'*49154,10,b'g'*49153,9))
        self.assertEqual(v.choose(b'z'*49152,10,b'g'*49153,9),'zero')
    def test_actual_bytes_and_integer_SSE_domains(self):
        for packets in((bytearray(b'z'),b'g'),(b'z',b'')):
            with self.subTest(packets=packets),self.assertRaises(ValueError):v.choose(packets[0],0,packets[1],0)
        for error in(-1,True,1.,float('nan')):
            with self.subTest(error=error),self.assertRaises(ValueError):v.choose(b'z',error,b'g',0)
    def test_integer_error_difference_is_not_rounded_MSE(self):
        # A one-unit source-error increase cannot be traded for saved bytes.
        self.assertEqual(v.choose(b'zz',2**35,b'g',2**35+1),'zero')
    def test_losing_receive_fork_cannot_publish_selected_history(self):
        folder=v.proof.BINARY;rows=json.loads((folder/'results.json').read_text())['cases'][0]['rows']
        rx=v.direct.Receiver();rx.receive(v.raw(rows[0]['packet'],folder));before=v.proof.rxproof.snapshot(rx)
        losing=v.fork(rx);self.assertIs(losing.ref,rx.ref);self.assertIs(losing.hud,rx.hud)
        with v.proof.rxproof.no_reencode():losing.receive(v.raw(rows[1]['packet'],folder))
        v.proof.rxproof.unchanged(rx,before);self.assertEqual(losing.last,1);self.assertEqual(rx.last,0)
    def test_failed_candidate_fork_preserves_incoming_state(self):
        folder=v.proof.BINARY;rows=json.loads((folder/'results.json').read_text())['cases'][0]['rows']
        rx=v.direct.Receiver();rx.receive(v.raw(rows[0]['packet'],folder));before=v.proof.rxproof.snapshot(rx)
        bad=v.proof.rxproof.outer_edit(v.raw(rows[1]['packet'],folder),10,b'X'*16)
        with self.assertRaises(ValueError),v.proof.rxproof.no_reencode():v.fork(rx).receive(bad)
        v.proof.rxproof.unchanged(rx,before)

if __name__=='__main__':unittest.main()
