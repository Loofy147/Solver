import math
from math import gcd

G_="\033[92m";R_="\033[91m";Y_="\033[93m";W_="\033[97m";Z_="\033[0m"

class UniversalityChecker:
    def __init__(self, registry):
        self.registry = registry

    def check_all(self):
        results = []
        for d in self.registry.all():
            m, k = d.m, d.k
            coprime = [r for r in range(1, m+1) if gcd(r, m) == 1]
            phi_m = len(coprime)

            # Simplified r-count for the table
            r_tuples = []
            if k == 1: r_tuples = [(1,)] if gcd(1,m)==1 else []
            elif k == 2: r_tuples = [(r1, (m-r1)%m or m) for r1 in coprime if gcd((m-r1)%m or m, m)==1]
            elif k == 3:
                for r1 in coprime:
                    for r2 in coprime:
                        r3 = (m - r1 - r2) % m or m
                        if gcd(r3, m) == 1: r_tuples.append((r1, r2, r3))
            elif k == 4:
                for r1 in coprime:
                    for r2 in coprime:
                        for r3 in coprime:
                            r4 = (m - r1 - r2 - r3) % m or m
                            if gcd(r4, m) == 1: r_tuples.append((r1, r2, r3, r4))

            r_count = len(r_tuples) if k <= 4 else 0
            h2_obstructed = (m % 2 == 0) and (k % 2 != 0)

            status = "OBSTRUCTED" if h2_obstructed else ("FEASIBLE" if r_count > 0 or k > 4 else "OPEN")
            results.append({
                "domain": d.name, "m": m, "k": k, "phi_m": phi_m,
                "r_count": r_count, "status": status
            })
        return results

    def print_table(self):
        print(f"\n{'═'*84}")
        print(f"{W_}CROSS-DOMAIN UNIVERSALITY — Governing Structure{Z_}")
        print(f"{'─'*84}")
        print(f"{W_}{'Domain':<30} {'m':>3} {'k':>3} {'φ(m)':>5} {'r-count':>8} {'Status':<12}{Z_}")
        print(f"  {'─'*80}")
        for res in self.check_all():
            status_col = R_ if res['status'] == 'OBSTRUCTED' else (G_ if res['status'] == 'FEASIBLE' else Y_)
            print(f"  {res['domain']:<30} {res['m']:>3} {res['k']:>3} {res['phi_m']:>5} {res['r_count']:>8} {status_col}{res['status']:<12}{Z_}")
        print(f"{'═'*84}")
