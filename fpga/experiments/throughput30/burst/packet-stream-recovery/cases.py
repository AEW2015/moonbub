#!/usr/bin/env python3
"""Fixed corner cases plus seeded middle single-packet positions."""
import random
cases=[(0,1),(5,1),(25,1),(0,3),(5,3),(23,3)]
choices=[x for x in range(1,25) if x!=5]
cases.extend((x,1) for x in random.Random(42).sample(choices,3))
for a,b in cases:print(a,b)
