import sys
import argparse
import os

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from src.theorems import verify_all_theorems, print_cross_domain_table
from src.engine import Engine, inject_domain
from src.export import write_lean_export
from src.frontiers import print_status, solve_P1, solve_P2, solve_P3, verify_m6_depth3_barrier, solve_P2_equivariant
from src.benchmark import run_benchmark, print_summary, w4_benchmark
from src.core import state_space_reduction, get_canonical_representative, crypto_group_check
from src.real_world import CryptoSolver, MusicSolver, ProteinSolver

G_="\033[92m";R_="\033[91m";Y_="\033[93m";B_="\033[94m"
C_="\033[96m";W_="\033[97m";D_="\033[2m";Z_="\033[0m"

def main():
    parser = argparse.ArgumentParser(description="Highly Symmetric Systems Explorer")
    parser.add_argument("--theorems", action="store_true", help="Run theorem verification")
    parser.add_argument("--status", action="store_true", help="Check open problem status")
    parser.add_argument("--benchmark", action="store_true", help="Run quick benchmark")
    parser.add_argument("--p1", action="store_true", help="Run P1 solver (k=4, m=4)")
    parser.add_argument("--p2", action="store_true", help="Run P2 solver (m=6, k=3)")
    parser.add_argument("--p3", action="store_true", help="Run P3 solver (m=8, k=3)")
    parser.add_argument("--gpu", action="store_true", help="Use GPU-accelerated SA engine")
    parser.add_argument("--chains", type=int, default=1024, help="Number of parallel SA chains for GPU")
    parser.add_argument("--seeds", type=int, default=2, help="Number of seeds for CPU SA")
    parser.add_argument("--max_iter", type=int, default=3000000, help="Max iterations for SA")
    parser.add_argument("--p2-equivariant", action="store_true", help="Run P2 solver with equivariant SA")
    parser.add_argument("--export-lean", action="store_true", help="Export results to Lean 4")
    parser.add_argument("--inject", action="store_true", help="Test domain injection")
    parser.add_argument("--m6-barrier", action="store_true", help="Verify m=6 depth-3 barrier")
    parser.add_argument("--rl-reduction", type=int, help="Show state-space reduction for m")
    parser.add_argument("--showcase-real", action="store_true", help="Showcase real-world data solvers")
    parser.add_argument("--crypto-check", type=int, help="Show crypto group hardness for prime p")

    if len(sys.argv) == 1:
        print_status()
        return

    args = parser.parse_args()

    if args.gpu:
        if not HAS_TORCH:
            print(f"{R_}Error: PyTorch not found. GPU engine requires torch.{Z_}")
            sys.exit(1)
        from src.gpu_core import GPUSolver

    if args.theorems:
        verify_all_theorems(verbose=True)
        print_cross_domain_table()

    if args.status:
        print_status()
        e = Engine()
        print(f"\n{W_}DOMAIN REGISTRY SUMMARY{Z_}")
        for d in e.registry.all():
            r = e.analyse(d.name)
            th = e.identify_theorem(r)
            th_str = f" [{G_}{' + '.join(th)}{Z_}]" if th else ""
            print(f"  {d.name:<30} {r.one_line()}{th_str}")

    if args.m6_barrier:
        verify_m6_depth3_barrier(verbose=True)

    if args.showcase_real:
        print(f"\n{W_}REAL-WORLD SYMMETRY CHALLENGE SHOWCASE{Z_}")
        print("─"*72)
        p = 65537; g = 3; x = 12345; h = pow(g, x, p)
        print(f"{B_}[Crypto]{Z_} Solving Discrete Log: {g}^x = {h} mod {p}")
        sol_x = CryptoSolver.solve_discrete_log(g, h, p)
        print(f"  Result: x = {sol_x} (Expected {x}) {'✓' if sol_x == x else '✗'}")
        notes = [60, 64, 67, 62, 65, 69]
        print(f"\n{B_}[Music]{Z_} Analyzing Chord Sequence: {notes}")
        chords = MusicSolver.analyze_chords(notes)
        for label, original in chords:
            print(f"  Notes {original} -> {G_}{label}{Z_} (Transposition Orbit)")
        seq = "HPHPPHPHPH"
        print(f"\n{B_}[Biology]{Z_} HP Protein Folding: {seq}")
        res = ProteinSolver.fold_hp(seq)
        print(f"  Fold Path: {res['path']}")
        print(f"  {G_}Stability Score: {res['score']}{Z_} (Contacts preserved)")

    if args.crypto_check:
        p = args.crypto_check
        res = crypto_group_check(p, 2)
        print(f"\n{W_}CRYPTOGRAPHIC GROUP HARDNESS (Z_p^*) for p={p}{Z_}")
        print(f"  Group order:       {res['group_order']}")
        print(f"  Number of gens:    {res['num_generators']}")
        print(f"  {G_}Hardness ratio:     {res['hardness_ratio']:.4f}{Z_}")

    if args.rl_reduction:
        m = args.rl_reduction
        res = state_space_reduction(m)
        print(f"\n{W_}RL STATE-SPACE REDUCTION for m={m}{Z_}")
        print(f"  Total states (G):    {res['total']}")
        print(f"  Distinct states (G/H): {res['distinct']}")
        print(f"  {G_}Reduction factor:     {res['reduction_factor']}x{Z_}")

    if args.benchmark:
        w4_benchmark()
        problems = [(3,3), (4,3), (5,3)]
        results = run_benchmark(problems)
        print_summary(results, problems)

    if args.p1:
        solve_P1(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)

    if args.p2:
        if args.gpu:
            m = 6; solver = GPUSolver(m)
            print(f"\n{W_}Running GPU Breakthrough Search for m=6...{Z_}")
            solver.solve(num_chains=args.chains, max_iter=args.max_iter)
        else:
            solve_P2(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)

    if args.p2_equivariant:
        solve_P2_equivariant(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)

    if args.p3:
        if args.gpu:
            m = 8; solver = GPUSolver(m)
            print(f"\n{W_}Running GPU Breakthrough Search for m=8...{Z_}")
            solver.solve(num_chains=args.chains, max_iter=args.max_iter)
        else:
            solve_P3(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)

    if args.inject:
        e = Engine()
        for d_spec in [{'name': 'Z_12 Crystal', 'group': 'Z_12', 'k': 3, 'action': 'projection to Z_6'},
                       {'name': 'Z_11 Lie Orbit', 'group': 'Z_11', 'k': 3},
                       {'name': 'k=4 m=4 Crystal', 'group': 'Z_4', 'k': 4, 'm': 4}]:
            d = inject_domain(d_spec); e.register(d)
            r = e.analyse(d.name, verbose=True)
            print(f'  {r.one_line()}')

    if args.export_lean:
        e = Engine()
        results = [e.run(3,3), e.run(4,3), e.run(4,4), e.run(5,3)]
        write_lean_export(results, 'proofs.lean')

if __name__ == "__main__":
    main()
