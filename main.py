import sys
import argparse
from src.theorems import verify_all_theorems, print_cross_domain_table
from src.frontiers import print_status, solve_P1, solve_P2, solve_P3, verify_m6_depth3_barrier
from src.benchmark import run_benchmark, print_summary, w4_benchmark

def main():
    parser = argparse.ArgumentParser(description="Highly Symmetric Systems Explorer")
    parser.add_argument("--theorems", action="store_true", help="Run theorem verification")
    parser.add_argument("--status", action="store_true", help="Check open problem status")
    parser.add_argument("--benchmark", action="store_true", help="Run quick benchmark")
    parser.add_argument("--p1", action="store_true", help="Run P1 solver (k=4, m=4)")
    parser.add_argument("--p2", action="store_true", help="Run P2 solver (m=6, k=3)")
    parser.add_argument("--p3", action="store_true", help="Run P3 solver (m=8, k=3)")
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

    if args.p3:
        solve_P3(max_iter=2_000_000, seeds=range(2), verbose=True)

if __name__ == "__main__":
    main()
