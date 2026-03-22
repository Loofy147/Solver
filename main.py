import sys
import argparse
from src.theorems import verify_all_theorems, print_cross_domain_table

from src.frontiers import solve_P2_equivariant
from src.engine import Engine, inject_domain
from src.export import write_lean_export
from src.frontiers import print_status, solve_P1, solve_P2, solve_P3, verify_m6_depth3_barrier
from src.benchmark import run_benchmark, print_summary, w4_benchmark

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

    parser.add_argument("--seeds", type=int, default=2, help="Number of seeds for SA")
    parser.add_argument("--max_iter", type=int, default=3000000, help="Max iterations for SA")
    parser.add_argument("--p2-equivariant", action="store_true", help="Run P2 solver with equivariant SA")
    parser.add_argument("--export-lean", action="store_true", help="Export results to Lean 4")
    parser.add_argument("--inject", action="store_true", help="Test domain injection")
    parser.add_argument("--m6-barrier", action="store_true", help="Verify m=6 depth-3 barrier")

    if len(sys.argv) == 1:
        print_status()
        return

    args = parser.parse_args()

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

    if args.benchmark:
        w4_benchmark()
        problems = [(3,3), (4,3), (5,3)]
        results = run_benchmark(problems)
        print_summary(results, problems)

    if args.p1:
        solve_P1(max_iter=1_500_000, seeds=range(3), verbose=True)

    if args.p2:
        solve_P2(max_iter=3_000_000, seeds=range(2), verbose=True)

    if args.p2_equivariant:
        solve_P2_equivariant(max_iter=args.max_iter, seeds=range(args.seeds), verbose=True)

    if args.inject:
        e = Engine()
        d1 = inject_domain({'name': 'Z_12 Crystal', 'group': 'Z_12', 'k': 3, 'action': 'projection to Z_6'})
        e.register(d1)
        r1 = e.analyse(d1.name, verbose=True)
        th1 = e.identify_theorem(r1)
        print(f'  {r1.one_line()} [{th1[0] if th1 else ""}]')

        d2 = inject_domain({'name': 'Z_11 Lie Orbit', 'group': 'Z_11', 'k': 3})
        e.register(d2)
        r2 = e.analyse(d2.name, verbose=True)
        th2 = e.identify_theorem(r2)
        print(f'  {r2.one_line()} [{th2[0] if th2 else ""}]')

        d3 = inject_domain({'name': 'k=4 m=4 Crystal', 'group': 'Z_4', 'k': 4, 'm': 4})
        e.register(d3)
        r3 = e.analyse(d3.name, verbose=True)
        th3 = e.identify_theorem(r3)
        print(f'  {r3.one_line()} [{th3[0] if th3 else ""}]')

    if args.export_lean:
        e = Engine()
        results = [e.run(3,3), e.run(4,3), e.run(4,4), e.run(5,3)]
        write_lean_export(results, 'proofs.lean')

    if args.p3:
        solve_P3(max_iter=2_000_000, seeds=range(2), verbose=True)

if __name__ == "__main__":
    main()
