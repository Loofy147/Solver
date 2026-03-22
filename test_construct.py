import sys
import os
from math import gcd
from itertools import permutations, product as iprod
sys.path.append(os.path.abspath('src'))
from core import verify_sigma, table_to_sigma

def construct_algebraic_odd_m(m: int):
    if m % 2 == 0: return None
    table = []
    # s=0: c*=0. pos 1 is color 0.
    lv0 = {}
    lv0[0] = (1, 0, 2)  # pos 0 is color 1. b1=1.
    for j in range(1, m): lv0[j] = (2, 0, 1)  # pos 0 is color 2. b2=1.
    table.append(lv0)

    # s=1: c*=1. pos 1 is color 1.
    lv1 = {}
    lv1[0] = (0, 1, 2)  # pos 0 is color 0. b0=1.
    for j in range(1, m): lv1[j] = (2, 1, 0)  # pos 0 is color 2. b2=1.
    table.append(lv1)

    # s >= 2: c*=2. pos 1 is color 2.
    for s in range(2, m):
        lvs = {}
        for j in range(m): lvs[j] = (1, 2, 0)  # pos 0 is color 1. b1=1.
        table.append(lvs)

    return table_to_sigma(table, m)

for m in [3, 5, 7, 9, 11, 13, 15]:
    sol = construct_algebraic_odd_m(m)
    if sol and verify_sigma(sol, m):
        print(f"m={m}: Success")
    else:
        print(f"m={m}: Failure")
