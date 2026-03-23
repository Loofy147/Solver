import torch
import sys
import os
import time

# Add src to path
sys.path.append('src')

from gpu_core import GPUSolver
from core import verify_sigma

def solve_m6():
    m = 6
    solver = GPUSolver(m)

    # Define orbits for equivariant moves
    orbits = []
    def enc(i, j, k): return i*m*m + j*m + k

    # Z_2 and Z_3 coordinate orbits
    for j in range(m):
        for k in range(m):
            orbits.append([enc(i, j, k) for i in [0, 3]])
            orbits.append([enc(i, j, k) for i in [1, 4]])
            orbits.append([enc(i, j, k) for i in [2, 5]])
            orbits.append([enc(i, j, k) for i in [0, 2, 4]])
            orbits.append([enc(i, j, k) for i in [1, 3, 5]])

    print(f"\nStarting GPU SA for m=6, k=3")
    best_sigma, best_score = solver.solve(
        num_chains=2048,
        max_iter=500000,
        T_init=3.0,
        T_min=0.001,
        orbits=orbits,
        p_equivariant=0.2,
        verbose=True
    )

    if best_score == 0:
        print("SOLVED m=6!")
        sol_dict = solver.sigma_to_dict(best_sigma)
        print(f"Verified: {verify_sigma(sol_dict, m)}")
        return sol_dict
    else:
        print(f"Failed to solve m=6. Best score: {best_score}")
        return None

def solve_m8():
    m = 8
    solver = GPUSolver(m)
    print(f"\nStarting GPU SA for m=8, k=3")
    best_sigma, best_score = solver.solve(
        num_chains=1024,
        max_iter=800000,
        T_init=3.0,
        T_min=0.001,
        verbose=True
    )

    if best_score == 0:
        print("SOLVED m=8!")
        sol_dict = solver.sigma_to_dict(best_sigma)
        print(f"Verified: {verify_sigma(sol_dict, m)}")
        return sol_dict
    else:
        print(f"Failed to solve m=8. Best score: {best_score}")
        return None

if __name__ == "__main__":
    print(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

    s6 = solve_m6()
    s8 = solve_m8()

    if s6: torch.save(s6, 'sol_m6.pt')
    if s8: torch.save(s8, 'sol_m8.pt')
