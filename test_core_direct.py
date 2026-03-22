import sys
import os
sys.path.append(os.path.abspath('src'))
from core import solve, verify_sigma, extract_weights

for m in [3, 5, 7]:
    w = extract_weights(m, 3)
    sol = solve(m, 3)
    if sol and verify_sigma(sol, m):
        print(f"m={m}: Success")
    else:
        print(f"m={m}: Failure")
