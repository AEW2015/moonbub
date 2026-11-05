import unittest
import numpy as np
import helpers as h

class PlanTests(unittest.TestCase):
    def test_independent_frozen_parity_and_owned_copies(self):
        rng = np.random.default_rng(3601)
        for height,width in ((2,2),(16,16),(18,34),(50,66),(480,720)):
            planes = tuple(rng.integers(0,256,shape,dtype=np.int16) for shape in ((height,width),(height//2,width//2),(height//2,width//2)))
            rects = [(), ((0,0,width,height),), ((0,0,width//2,height),(width//2,0,width-width//2,height))]
            if width > 34 and height > 34:
                rects += [((15,15,9,18),(24,15,9,18),(0,0,8,8))]
            for rectangles in rects:
                plan = h.model.compile_plan((height,width),rectangles)
                saved = tuple(p.copy() for p in planes)
                old = h.old.mask.mask_source(planes,rectangles)
                actual = h.model.apply_plan(planes,plan)
                for before,after,expected,copy in zip(planes,actual,old,saved):
                    np.testing.assert_array_equal(after,expected)
                    np.testing.assert_array_equal(before,copy)
                    self.assertFalse(np.shares_memory(before,after))

    def test_random_union_holes_and_edge_support(self):
        rng = np.random.default_rng(3636)
        planes = tuple(np.zeros(s,np.uint8) for s in ((66,82),(33,41),(33,41)))
        for _ in range(36):
            rects=[]
            for _ in range(7):
                x,y=int(rng.integers(82)),int(rng.integers(66))
                rects.append((x,y,int(rng.integers(1,83-x)),int(rng.integers(1,67-y))))
            plan=h.model.compile_plan((66,82),rects)
            result=h.model.apply_plan(planes,plan)
            frozen=h.old.mask.mask_source(planes,rects)
            for a,b in zip(result,frozen): np.testing.assert_array_equal(a,b)
            for axis,runs in enumerate(plan.runs):
                self.assertEqual(sum(x1-x0 for _,x0,x1 in runs),plan.blocks[axis]*64)

    def test_invalid_inputs_no_mutation(self):
        planes=tuple(np.zeros(s,np.int16) for s in ((16,16),(8,8),(8,8)))
        for shape in ((1,2),(16,15),(True,16),(16.,16),None):
            with self.assertRaises(ValueError): h.model.compile_plan(shape,())
        for rectangles in (None, ((0,0,17,1),), ((True,0,1,1),), ((0,0,0,1),)):
            with self.assertRaises(ValueError): h.model.compile_plan((16,16),rectangles)
        plan=h.model.compile_plan((16,16),((0,0,16,16),))
        for bad in (planes[:2],(planes[0],planes[1],np.full((8,8),256)),(planes[0],planes[1],planes[2].astype(float))):
            with self.assertRaises(ValueError):h.model.apply_plan(bad,plan)
        self.assertTrue(all(not np.any(p) for p in planes))

if __name__=='__main__':unittest.main()
