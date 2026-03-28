from src.universality import UniversalityChecker
import sys
import argparse
import os
import torch

try:
    HAS_TORCH = True
    from src.gpu_core import GPUSolver
except ImportError:
    HAS_TORCH = False

from src.theorems import verify_all_theorems, print_cross_domain_table
from src.engine import Engine, inject_domain
from src.export import write_lean_export
from src.frontiers import print_status, solve_P1, solve_P2, solve_P3, verify_m6_depth3_barrier, solve_P2_equivariant
from src.benchmark import run_benchmark, print_summary, w4_benchmark
from src.core import state_space_reduction, get_canonical_representative, crypto_group_check
from src.real_world import CryptoSolver, MusicSolver, ProteinSolver, MathSolver
from src.aimo_solvers import AimoSolver

G_="\033[92m";R_="\033[91m";Y_="\033[93m";B_="\033[94m"
C_="\033[96m";W_="\033[97m";D_="\033[2m";Z_="\033[0m"

def main():
    parser = argparse.ArgumentParser(description="Highly Symmetric Systems Explorer")
    parser.add_argument("--theorems", action="store_true", help="Run theorem verification")
    parser.add_argument("--universality", action="store_true", help="Show cross-domain universality table")
    parser.add_argument("--status", action="store_true", help="Check open problem status")
    parser.add_argument("--benchmark", action="store_true", help="Run quick benchmark")
    parser.add_argument("--p1", action="store_true", help="Run P1 solver (k=4, m=4)")
    parser.add_argument("--p2", action="store_true", help="Run P2 solver (m=6, k=3)")
    parser.add_argument("--p3", action="store_true", help="Run P3 solver (m=8, k=3)")
    parser.add_argument("--gpu", action="store_true", help="Use GPU acceleration")
    parser.add_argument("--gpu-equivariant", action="store_true", help="Use GPU with equivariant moves")
    parser.add_argument("--chains", type=int, default=1024, help="Number of GPU chains")
    parser.add_argument("--seeds", type=int, default=4, help="Number of CPU seeds/parallel chains")
    parser.add_argument("--max_iter", type=int, default=1_000_000, help="Max iterations")
    parser.add_argument("--p2-equivariant", action="store_true", help="Run P2 solver with equivariant SA")
    parser.add_argument("--export-lean", action="store_true", help="Export results to Lean 4")
    parser.add_argument("--inject", action="store_true", help="Test domain injection")
    parser.add_argument("--m6-barrier", action="store_true", help="Verify m=6 depth-3 barrier")
    parser.add_argument("--rl-reduction", type=int, help="Run RL state reduction for G_m")
    parser.add_argument("--showcase-real", action="store_true", help="Showcase real-world solvers")
    parser.add_argument("--solve-aimo", action="store_true", help="Run AIMO competition verification")
    parser.add_argument("--crypto-check", type=int, help="Check symmetry hardness for Z_p")

    args = parser.parse_args()

    if args.solve_aimo:
        print(f"\n{W_}AIMO 3 Reference Problem Verification{Z_}")
        import unittest
        from test_aimo import TestAimoSolvers
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAimoSolvers)
        unittest.TextTestRunner(verbosity=1).run(suite)
        return

    if args.gpu_equivariant:
        if not HAS_TORCH:
            print(f"{R_}Error: PyTorch not found. Cannot run GPU solver.{Z_}")
            return
        m = 6
        print(f"{W_}Starting GPU Equivariant SA for m={m}, k=3{Z_}")
        # Define m=6 orbits for equivariant moves
        def enc(i, j, k): return i*m*m + j*m + k
        orbits = []
        for j in range(m):
            for k in range(m):
                orbits.append([enc(i, j, k) for i in [0, 3]])
                orbits.append([enc(i, j, k) for i in [1, 4]])
                orbits.append([enc(i, j, k) for i in [2, 5]])
                orbits.append([enc(i, j, k) for i in [0, 2, 4]])
                orbits.append([enc(i, j, k) for i in [1, 3, 5]])

        solver = GPUSolver(m)
        best_sig, score = solver.solve(num_chains=args.chains, max_iter=args.max_iter, orbits=orbits)
        print(f"{G_}Best score found: {score}{Z_}")
        return

    if args.gpu:
        if not HAS_TORCH:
            print(f"{R_}Error: PyTorch not found. Cannot run GPU solver.{Z_}")
            return
        m = 6
        print(f"{W_}Starting GPU SA for m={m}, k=3{Z_}")
        solver = GPUSolver(m)
        best_sig, score = solver.solve(num_chains=args.chains, max_iter=args.max_iter)
        print(f"{G_}Best score found: {score}{Z_}")
        return

    if args.universality:
        e = Engine()
        checker = UniversalityChecker(e.registry)
        checker.print_table()

    if args.status:
        print_status()

    if args.p1:
        solve_P1(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)

    if args.p2:
        if args.p2_equivariant:
            solve_P2_equivariant(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)
        else:
            solve_P2(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)

    if args.p3:
        solve_P3(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)

    if args.theorems:
        print(f"\n{W_}1. Formal Theorem Verification{Z_}")
        verify_all_theorems()
        print(f"\n{W_}2. Cross-Domain Governing Structure{Z_}")
        print_cross_domain_table()

    if args.m6_barrier:
        verify_m6_depth3_barrier()

    if args.rl_reduction:
        m = args.rl_reduction
        state = [0] * (m**3)
        red = state_space_reduction(state, m)
        print(f"G_{m} state space reduction: {len(state)} -> {len(red)}")

    if args.showcase_real:
        print(f"\n{W_}Real-World Symmetry Solvers Showcase{Z_}")
        print(f"{B_}Crypto:{Z_} Discrete Log g=2, h=pow(2,123,1000003), p=1000003 ->", CryptoSolver.solve_discrete_log(2, pow(2,123,1000003), 1000003))
        print(f"{B_}Music:{Z_} Chords (0,4,7,2,5,9) ->", MusicSolver.analyze_chords([0,4,7,2,5,9]))
        print(f"{B_}Math:{Z_} v2(sigma_3(5^2)) ->", MathSolver.sum_divisors_valuation_pow2(5, 2, 3))

    if args.export_lean:
        write_lean_export("proofs.lean")

    if args.inject:
        d_spec = {"name": "Injected Domain", "group": "Z_8", "subgroup": "Z_2", "k": 3}
        e = Engine()
        d = inject_domain(d_spec); e.register(d)
        e.analyse("Injected Domain", verbose=True)

    if args.crypto_check:
        p = args.crypto_check
        hardness = crypto_group_check(p, 2)
        print(f"Z_{p} symmetry hardness (generators count): {hardness}")

if __name__ == "__main__":
    main()
