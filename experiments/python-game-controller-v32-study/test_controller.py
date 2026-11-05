import unittest
from controller import select_tier
def c(kind,size,error):return dict(kind=kind,complete_bytes=size,hybrid=dict(active_squared_error=error))
class ShadowTests(unittest.TestCase):
    def test_shadow_is_v30_band_winner_not_legacy_zero(self):
        a,b,d,e=c('zero',400,100),c('half32',300,80),c('half32_band',290,70),c('zero_shrink',200,75)
        winner,shadow=select_tier([a,b,d,e],'shrink_strict');self.assertIs(winner,d);self.assertIs(shadow,d)
    def test_budget_tie_and_capacity(self):
        a,b=c('zero',100,100),c('zero_shrink',90,101)
        self.assertIs(select_tier([a,b],'shrink_budget')[0],b)
        self.assertIs(select_tier([a,b],'shrink_strict')[0],a)
        b['complete_bytes']=100;b['hybrid']['active_squared_error']=99
        self.assertIs(select_tier([a,b],'shrink_strict')[0],a)
        b['complete_bytes']=49153
        self.assertIs(select_tier([a,b],'shrink_strict')[0],a)
    def test_no_shadow_rescue_and_zero_error_budget(self):
        self.assertIsNone(select_tier([c('zero',49153,100),c('zero_shrink',90,0)],'shrink_budget')[0])
        a=c('zero',100,0)
        self.assertIs(select_tier([a,c('zero_shrink',90,1)],'shrink_budget')[0],a)
    def test_invalid_inputs(self):
        for args in (([],'band_control'),([c('zero',1,0),c('zero_shrink',1,0)],'band_control'),([c('zero',1,0),c('zero',2,0)],'shrink_strict')):
            with self.assertRaises(ValueError):select_tier(*args)
if __name__=='__main__':unittest.main()
