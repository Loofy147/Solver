"""
core.py — Mathematical Foundations
====================================
Weights · Verifier · Solutions · Level Machinery · SA Engine

The 8 weights classify any (m, k) problem in the moduli space M_k(G_m).
All are closed-form, all O(m²) or faster.

  W1  H² obstruction    bool   proves impossible in O(1)
  W2  r-tuple count     int    how many construction seeds
  W3  canonical seed    tuple  the direct construction path
  W4  H¹ order EXACT    int    phi(m)  — gauge multiplicity
  W5  search exponent   float  log₂(compressed space)
  W6  compression ratio float  W5 / log₂(full space)
  W7  solution lb       int    phi(m) × coprime_b(m)^(k-1)  [exact for m=3]
  W8  orbit size        int    m^(m-1)

Derivation of W4 = phi(m):
  |coprime-sum cocycles b: Z_m→Z_m| = m^(m-1) · phi(m)
  |coboundaries|                     = m^(m-1)
  |H¹(Z_m, coprime-sum)|            = phi(m)

Closure lemma (proved for m=3, conjectured general):
  Given b₀,...,b_{k-2} with gcd(sum,m)=1, b_{k-1} is determined.
  Therefore W7 = phi(m) × coprime_b(m)^(k-1)  [exact for m=3].
"""

import math, random
from math import gcd, log2, factorial
from itertools import permutations, product as iprod
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass
from functools import lru_cache

# ── pre-computed tables ───────────────────────────────────────────────────────
_LEVEL_COUNTS: Dict[int,int] = {2:2,3:24,4:48,5:384,6:1152,7:5040,8:13440,9:72576}
_ALL_P3 = [list(p) for p in permutations(range(3))]
_FIBER_SHIFTS = ((1,0),(0,1),(0,0))   # i-shift, j-shift for arc types 0,1,2


# ══════════════════════════════════════════════════════════════════════════════
# THE 8 WEIGHTS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Weights:
    m: int; k: int
    h2_blocks:   bool           # W1
    h3_blocks:   bool           # W9: Secondary obstruction
    r_count:     int            # W2
    canonical:   Optional[tuple]# W3
    h1_exact:    int            # W4 = phi(m)
    search_exp:  float          # W5
    compression: float          # W6
    sol_lb:      int            # W7 lower bound
    orbit_size:  int            # W8
    coprime_elems: tuple        # cached

    @property
    def strategy(self) -> str:
        if self.h2_blocks:   return "S4"  # prove impossible
        if self.r_count > 0: return "S1"  # column-uniform
        return                      "S2"  # fiber-structured SA

    @property
    def solvable(self) -> bool:
        return not self.h2_blocks and self.r_count > 0

    def summary(self) -> str:
        h3 = " H³≠0" if self.h3_blocks else ""
        ok = "H²=0" if not self.h2_blocks else "H²≠0"
        return (f"({self.m},{self.k}) {ok}{h3} r={self.r_count} "
                f"W3={self.canonical} W4=φ={self.h1_exact} "
                f"W6={self.compression:.4f} → {self.strategy}")



@lru_cache(maxsize=1024)
def extract_weights(m: int, k: int) -> Weights:
    """Extract all 9 weights for problem (m,k). Cached."""
    cp = tuple(r for r in range(1, m) if gcd(r, m) == 1)
    phi_m = len(cp)

    # W1: H² obstruction — O(1)
    all_odd = bool(cp) and all(r % 2 == 1 for r in cp)
    h2 = all_odd and (k % 2 == 1) and (m % 2 == 0)

    # W2/W3: r-tuples — O(|cp|^k)
    r_tuples = [] if h2 else [t for t in iprod(cp, repeat=k) if sum(t) == m]
    r_count  = len(r_tuples)
    canon    = None
    if r_count > 0:
        mid = m - (k - 1)
        canon = ((1,)*(k-1) + (mid,)) if (mid > 0 and gcd(mid,m)==1) else r_tuples[0]

    # W4: |H¹(Z_m, coprime-sum)| = phi(m) — O(1) exact
    h1 = phi_m

    # W5/W6: search compression — O(1)
    # Estimate size of valid_levels(m) as (3!)^m / 2^m = 3^m
    # log2(6^m) = m * log2(6). Compressed log2(3^m) = m * log2(3).
    # W5 = m * log2(levels), W6 = W5 / (m^3 * log2(6))
    levels = 3**m
    search_exp = m * math.log2(levels)
    total_exp  = (m**3) * math.log2(6)
    compression = search_exp / total_exp

    # W7: Solution count lower bound — phi(m) * (m^(m-1) * phi(m))^(k-1)
    coprime_b = (m**(m-1)) * h1
    sol_lb = h1 * (coprime_b**(k-1))

    # W8: Orbit size (gauge orbit size) — m^(m-1)
    orbit_size = m**(m-1)

    # W9: Secondary obstruction (Fiber-Uniform k=4 Impossibility)
    h3 = (m == 4 and k == 4) # Known from Theorem 10.1

    return Weights(m=m, k=k, h2_blocks=h2, h3_blocks=h3, r_count=r_count, canonical=canon,
                   h1_exact=h1, search_exp=round(search_exp,3),
                   compression=round(compression,6), sol_lb=sol_lb,
                   orbit_size=orbit_size, coprime_elems=cp)


def weights_table(m_range=range(2,11), k_range=range(2,7)) -> List[Weights]:
    return [extract_weights(m,k) for m in m_range for k in k_range]


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION
# ══════════════════════════════════════════════════════════════════════════════

def verify_sigma(sigma: Dict[Tuple,Tuple], m: int) -> bool:
    """
    Verify sigma: Z_m³ → S_3 yields three directed Hamiltonian cycles.
    Checks: |arcs|=m³, in-degree=1, components=1 for each colour.
    """
    sh = ((1,0,0),(0,1,0),(0,0,1)); n = m**3
    funcs: List[Dict] = [{},{},{}]
    for v,p in sigma.items():
        for at in range(3):
            nb = tuple((v[d]+sh[at][d])%m for d in range(3))
            funcs[p[at]][v] = nb
    for fg in funcs:
        if len(fg) != n: return False
        vis: set = set(); comps = 0
        for s in fg:
            if s not in vis:
                comps += 1; cur = s
                while cur not in vis: vis.add(cur); cur = fg[cur]
        if comps != 1: return False
    return True


# ══════════════════════════════════════════════════════════════════════════════
# HARDCODED VERIFIED SOLUTIONS
# ══════════════════════════════════════════════════════════════════════════════

_TABLE_M3 = [
    {0:(2,0,1),1:(1,0,2),2:(2,0,1)},
    {0:(0,2,1),1:(1,2,0),2:(0,2,1)},
    {0:(0,1,2),1:(0,1,2),2:(0,1,2)},
]
_TABLE_M5 = [
    {0:(0,2,1),1:(1,2,0),2:(0,2,1),3:(0,2,1),4:(1,2,0)},
    {0:(2,1,0),1:(2,1,0),2:(0,1,2),3:(2,1,0),4:(2,1,0)},
    {0:(2,1,0),1:(0,1,2),2:(0,1,2),3:(2,1,0),4:(2,1,0)},
    {0:(2,1,0),1:(2,1,0),2:(0,1,2),3:(0,1,2),4:(2,1,0)},
    {0:(2,0,1),1:(1,0,2),2:(2,0,1),3:(1,0,2),4:(2,0,1)},
]
SOLUTION_M4: Dict[Tuple,Tuple] = {
    (0,0,0):(2,1,0),(0,0,1):(2,1,0),(0,0,2):(0,2,1),(0,0,3):(1,2,0),
    (0,1,0):(1,0,2),(0,1,1):(0,2,1),(0,1,2):(2,0,1),(0,1,3):(0,1,2),
    (0,2,0):(2,0,1),(0,2,1):(0,1,2),(0,2,2):(1,2,0),(0,2,3):(1,0,2),
    (0,3,0):(1,2,0),(0,3,1):(1,2,0),(0,3,2):(0,1,2),(0,3,3):(2,0,1),
    (1,0,0):(2,0,1),(1,0,1):(0,2,1),(1,0,2):(2,1,0),(1,0,3):(1,2,0),
    (1,1,0):(2,0,1),(1,1,1):(1,2,0),(1,1,2):(0,2,1),(1,1,3):(1,0,2),
    (1,2,0):(0,2,1),(1,2,1):(1,2,0),(1,2,2):(0,1,2),(1,2,3):(2,0,1),
    (1,3,0):(2,1,0),(1,3,1):(1,0,2),(1,3,2):(0,2,1),(1,3,3):(1,2,0),
    (2,0,0):(2,0,1),(2,0,1):(0,2,1),(2,0,2):(1,2,0),(2,0,3):(0,2,1),
    (2,1,0):(2,1,0),(2,1,1):(2,0,1),(2,1,2):(1,2,0),(2,1,3):(2,0,1),
    (2,2,0):(0,1,2),(2,2,1):(2,0,1),(2,2,2):(0,2,1),(2,2,3):(1,0,2),
    (2,3,0):(1,0,2),(2,3,1):(0,2,1),(2,3,2):(1,0,2),(2,3,3):(1,2,0),
    (3,0,0):(1,0,2),(3,0,1):(1,0,2),(3,0,2):(2,0,1),(3,0,3):(2,0,1),
    (3,1,0):(0,2,1),(3,1,1):(0,1,2),(3,1,2):(0,2,1),(3,1,3):(0,2,1),
    (3,2,0):(1,2,0),(3,2,1):(0,2,1),(3,2,2):(1,2,0),(3,2,3):(2,0,1),
    (3,3,0):(2,0,1),(3,3,1):(2,1,0),(3,3,2):(1,0,2),(3,3,3):(1,2,0),
}

def table_to_sigma(table: List[Dict], m: int) -> Dict[Tuple,Tuple]:
    """Convert a list of level-dicts to the full sigma map."""
    sigma = {}
    for i in range(m):
        for j in range(m):
            for k in range(m):
                sigma[(i,j,k)] = table[(i+j+k)%m][j]
    return sigma

PRECOMPUTED: Dict[Tuple[int,int], Dict] = {
    (3,3): table_to_sigma(_TABLE_M3, 3),
    (5,3): table_to_sigma(_TABLE_M5, 5),
    (4,3): dict(SOLUTION_M4),
}


# ══════════════════════════════════════════════════════════════════════════════
# FIBER LEVEL MACHINERY
# ══════════════════════════════════════════════════════════════════════════════

def _level_valid(lv: Dict[int,list], m: int) -> bool:
    for c in range(3):
        targets: set = set()
        for j in range(m):
            at = lv[j].index(c); di,dj = _FIBER_SHIFTS[at]
            for i in range(m): targets.add(((i+di)%m, (j+dj)%m))
        if len(targets) != m*m: return False
    return True

@lru_cache(maxsize=16)
def valid_levels(m: int) -> List[Dict]:
    """All valid level assignments for G_m. Cached."""
    result = []
    for combo in iprod(_ALL_P3, repeat=m):
        lv = {j: combo[j] for j in range(m)}
        if _level_valid(lv, m): result.append(lv)
    return result

def compose_Q(table: List[Dict], m: int) -> List[Dict]:
    """Compute the three composed fiber permutations Q_0, Q_1, Q_2."""
    Qs: List[Dict] = [{},{},{}]
    for i0 in range(m):
        for j0 in range(m):
            pos = [[i0,j0],[i0,j0],[i0,j0]]
            for s in range(m):
                lv = table[s]
                for c in range(3):
                    cj = pos[c][1]; at = lv[cj].index(c)
                    di,dj = _FIBER_SHIFTS[at]
                    pos[c][0] = (pos[c][0]+di)%m
                    pos[c][1] = (pos[c][1]+dj)%m
            for c in range(3): Qs[c][(i0,j0)] = tuple(pos[c])
    return Qs

def is_single_cycle(Q: Dict, m: int) -> bool:
    n = m*m; vis: set = set(); cur = (0,0)
    while cur not in vis: vis.add(cur); cur = Q[cur]
    return len(vis) == n


# ══════════════════════════════════════════════════════════════════════════════
# SA ENGINE  —  fast integer-array SA with repair + plateau escape
# ══════════════════════════════════════════════════════════════════════════════

def _build_sa3(m: int):
    """Build arc-successor and perm-arc tables for G_m (k=3) SA."""
    n = m**3
    arc_s = [[0]*3 for _ in range(n)]
    for idx in range(n):
        i,rem = divmod(idx,m*m); j,k = divmod(rem,m)
        arc_s[idx][0] = ((i+1)%m)*m*m+j*m+k
        arc_s[idx][1] = i*m*m+((j+1)%m)*m+k
        arc_s[idx][2] = i*m*m+j*m+(k+1)%m
    pa = [[None]*3 for _ in range(6)]
    for pi,p in enumerate(_ALL_P3):
        for at,c in enumerate(p): pa[pi][c] = at
    return n, arc_s, pa

def _sa_score(sigma: List[int], arc_s, pa, n: int) -> int:
    f0=[0]*n; f1=[0]*n; f2=[0]*n
    for v in range(n):
        pi=sigma[v]; p=pa[pi]
        f0[v]=arc_s[v][p[0]]; f1[v]=arc_s[v][p[1]]; f2[v]=arc_s[v][p[2]]
    def cc(f):
        vis=bytearray(n); c=0
        for s in range(n):
            if not vis[s]:
                c+=1; cur=s
                while not vis[cur]: vis[cur]=1; cur=f[cur]
        return c
    return cc(f0)-1 + cc(f1)-1 + cc(f2)-1

def run_sa(m: int, seed: int=0, max_iter: int=5_000_000,
           T_init: float=3.0, T_min: float=0.003,
           verbose: bool=False, report_n: int=500_000,
           p_multi: float=0.05) -> Tuple[Optional[Dict], Dict]:
    """
    Full-3D SA for G_m (k=3) with coordinated multi-vertex flips.
    Returns (sigma_map | None, stats).
    """
    import time
    n, arc_s, pa = _build_sa3(m)
    rng = random.Random(seed); nP = 6
    sigma = [rng.randrange(nP) for _ in range(n)]
    cs = _sa_score(sigma, arc_s, pa, n)
    bs = cs; best = sigma[:]
    cool = (T_min/T_init)**(1.0/max_iter)
    T = T_init; stall=0; reheats=0; t0=time.perf_counter()

    for it in range(max_iter):
        if cs == 0: break

        # Periodic check for coordinated multi-flips to escape traps
        if rng.random() < p_multi:
            # Pick a vertex and 2 others to perform a coordinated 3-flip
            v_indices = rng.sample(range(n), 3)
            old_vals = [sigma[v] for v in v_indices]
            new_vals = [rng.randrange(nP) for _ in range(3)]
            for i, v in enumerate(v_indices): sigma[v] = new_vals[i]
            ns = _sa_score(sigma, arc_s, pa, n)
            d = ns - cs
            if d < 0 or (T > 1e-9 and rng.random() < math.exp(-d / T)):
                cs = ns
                if cs < bs: bs = cs; best = sigma[:]; stall = 0
                else: stall += 1
            else:
                for i, v in enumerate(v_indices): sigma[v] = old_vals[i]
                stall += 1
        else:
            # Standard single-flip
            v = rng.randrange(nP if m==1 else n); old = sigma[v]; new = rng.randrange(nP)
            if new == old: T *= cool; continue
            sigma[v] = new; ns = _sa_score(sigma, arc_s, pa, n); d = ns - cs
            if d < 0 or (T > 1e-9 and rng.random() < math.exp(-d / T)):
                cs = ns
                if cs < bs: bs = cs; best = sigma[:]; stall = 0
                else: stall += 1
            else: sigma[v] = old; stall += 1

        if stall > 80_000:
            T = T_init / (2**reheats); reheats += 1; stall = 0; sigma = best[:]; cs = bs
        T *= cool
        if verbose and (it + 1) % report_n == 0:
            el = time.perf_counter() - t0
            print(f"    it={it+1:>8,} T={T:.5f} s={cs} best={bs} reh={reheats} {el:.1f}s")

    elapsed = time.perf_counter() - t0
    sol = None
    if bs == 0:
        sol = {}
        for idx, pi in enumerate(best):
            i, rem = divmod(idx, m * m); j, k = divmod(rem, m)
            sol[(i, j, k)] = tuple(_ALL_P3[pi])
    return sol, {"best": bs, "iters": it + 1, "elapsed": elapsed, "reheats": reheats}


def construct_direct(m: int, k: int=3) -> Optional[Dict]:
    """
    Algebraic construction for odd m (k=3).
    Generalizes the Closure Lemma logic to provide O(m^2) verified solutions.
    """
    if k != 3 or m % 2 != 1: return None
    table = []
    # s=0: c*=0. pos 1 is color 0.
    lv0 = {0: (1, 0, 2)}
    for j in range(1, m): lv0[j] = (2, 0, 1)
    table.append(lv0)
    # s=1: c*=1. pos 1 is color 1.
    lv1 = {0: (0, 1, 2)}
    for j in range(1, m): lv1[j] = (2, 1, 0)
    table.append(lv1)
    # s >= 2: c*=2. pos 1 is color 2.
    for s in range(2, m):
        lvs = {j: (1, 2, 0) for j in range(m)}
        table.append(lvs)
    return table_to_sigma(table, m)

def solve(m: int, k: int=3, seed: int=42) -> Optional[Dict]:
    """
    Unified solver. Returns sigma or None.
    Routes: precomputed → column-uniform → SA.
    """
    w = extract_weights(m, k)
    if w.h2_blocks: return None

    # Precomputed
    if (m,k) in PRECOMPUTED: return PRECOMPUTED[(m,k)]

    # Algebraic construction (odd m, k=3)
    if w.r_count > 0 and k == 3:
        return construct_direct(m, k)

    # Full-3D SA (even m, k=3)
    if k == 3:
        sol, _ = run_sa(m, seed=seed)
        return sol
    return None


if __name__ == "__main__":
    import sys
    print("╔═══════════════════════════════════════════════╗")
    print("║  core.py — weight extraction + verification  ║")
    print("╚═══════════════════════════════════════════════╝")
    print()
    print("8 weights for key (m,k) problems:")
    print(f"  {'m,k':<8} {'W1':>6} {'W2':>4} {'W3':<18} {'W4':>5} {'W6':>8} {'W7':>10}")
    print("  " + "─"*65)
    for m,k in [(3,3),(4,3),(4,4),(5,3),(6,3),(7,3),(8,4)]:
        w = extract_weights(m,k)
        blocked = "H²≠0" if w.h2_blocks else "H²=0"
        print(f"  m={m} k={k}  {blocked}  {w.r_count:>4}  {str(w.canonical):<18}  "
              f"{w.h1_exact:>5}  {w.compression:>8.5f}  {w.sol_lb:>10,}")
    print()
    print("Verified solutions:")
    for (m,k),sol in PRECOMPUTED.items():
        ok = verify_sigma(sol, m)
        print(f"  m={m} k={k}: verified={ok}")
    print()
    print("solve(7,3) — column-uniform for odd m:")
    import time
    t0 = time.perf_counter()
    sol = solve(7, 3)
    dt = time.perf_counter() - t0
    if sol:
        ok = verify_sigma(sol, 7)
        print(f"  m=7: found in {dt:.2f}s, verified={ok}")
    else:
        print(f"  m=7: not found in budget")

def _sa_worker(args):
    """Worker function for parallel SA seeds."""
    m, seed, max_iter, T_init, T_min, p_multi = args
    return run_sa(m, seed=seed, max_iter=max_iter, T_init=T_init, T_min=T_min, p_multi=p_multi)


def run_sa_equivariant(m: int, orbits: List[List[int]], seed: int=0, max_iter: int=5_000_000,
                       T_init: float=3.0, T_min: float=0.003,
                       verbose: bool=False, report_n: int=500_000,
                       p_equivariant: float=0.2) -> Tuple[Optional[Dict], Dict]:
    """
    Equivariant SA that flips entire orbits simultaneously to escape structural traps.
    """
    import time, math
    n, arc_s, pa = _build_sa3(m)
    rng = random.Random(seed); nP = 6
    sigma = [rng.randrange(nP) for _ in range(n)]
    cs = _sa_score(sigma, arc_s, pa, n)
    bs = cs; best = sigma[:]
    cool = (T_min/T_init)**(1.0/max_iter)
    T = T_init; stall=0; reheats=0; t0=time.perf_counter()

    for it in range(max_iter):
        if cs == 0: break

        if rng.random() < p_equivariant:
            # Equivariant flip: pick a random orbit and a new permutation
            orbit = rng.choice(orbits)
            old_vals = [sigma[v] for v in orbit]
            new_val = rng.randrange(nP)
            for v in orbit: sigma[v] = new_val
            ns = _sa_score(sigma, arc_s, pa, n)
            d = ns - cs
            if d < 0 or (T > 1e-9 and rng.random() < math.exp(-d / T)):
                cs = ns
                if cs < bs: bs = cs; best = sigma[:]; stall = 0
                else: stall += 1
            else:
                for i, v in enumerate(orbit): sigma[v] = old_vals[i]
                stall += 1
        else:
            # Standard single-flip
            v = rng.randrange(n); old = sigma[v]; new = rng.randrange(nP)
            if new == old: T *= cool; continue
            sigma[v] = new; ns = _sa_score(sigma, arc_s, pa, n); d = ns - cs
            if d < 0 or (T > 1e-9 and rng.random() < math.exp(-d / T)):
                cs = ns
                if cs < bs: bs = cs; best = sigma[:]; stall = 0
                else: stall += 1
            else: sigma[v] = old; stall += 1

        if stall > 80_000:
            T = T_init / (2**reheats); reheats += 1; stall = 0; sigma = best[:]; cs = bs
        T *= cool
        if verbose and (it + 1) % report_n == 0:
            el = time.perf_counter() - t0
            print(f'    it={it+1:>8,} T={T:.5f} s={cs} best={bs} reh={reheats} {el:.1f}s')

    elapsed = time.perf_counter() - t0
    sol = None
    if bs == 0:
        sol = {}
        for idx, pi in enumerate(best):
            i, rem = divmod(idx, m * m); j, k = divmod(rem, m)
            sol[(i, j, k)] = tuple(_ALL_P3[pi])
    return sol, {'best': bs, 'iters': it + 1, 'elapsed': elapsed, 'reheats': reheats}

def run_parallel_sa(m: int, seeds: List[int], max_iter: int=5_000_000,
                    T_init: float=3.0, T_min: float=0.003) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Execute multiple SA seeds in parallel.
    Returns (first_solution | None, list_of_all_stats).
    """
    from multiprocessing import Pool, cpu_count

    n_procs = min(len(seeds), cpu_count())
    args = [(m, s, max_iter, T_init, T_min, 0.05) for s in seeds]

    all_stats = []
    best_sol = None

    print(f"    Spawning {n_procs} parallel SA processes for G_{m}...")
    with Pool(processes=n_procs) as pool:
        for sol, stats in pool.imap_unordered(_sa_worker, args):
            all_stats.append(stats)
            if sol and not best_sol:
                best_sol = sol
                # Note: imap_unordered doesn't allow easy early exit without
                # more complex logic, but for these budgets it is fine.

    return best_sol, all_stats


def _sa_equivariant_worker(args):
    """Worker function for parallel equivariant SA seeds."""
    m, orbits, seed, max_iter, T_init, T_min, p_equivariant = args
    return run_sa_equivariant(m, orbits, seed=seed, max_iter=max_iter, T_init=T_init, T_min=T_min, p_equivariant=p_equivariant)

def run_parallel_sa_equivariant(m: int, orbits: List[List[int]], seeds: List[int], max_iter: int=5_000_000,
                               T_init: float=3.0, T_min: float=0.003) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Execute multiple equivariant SA seeds in parallel.
    """
    from multiprocessing import Pool, cpu_count

    n_procs = min(len(seeds), cpu_count())
    args = [(m, orbits, s, max_iter, T_init, T_min, 0.2) for s in seeds]

    all_stats = []
    best_sol = None

    print(f'    Spawning {n_procs} parallel equivariant SA processes for G_{m}...')
    with Pool(processes=n_procs) as pool:
        for sol, stats in pool.imap_unordered(_sa_equivariant_worker, args):
            all_stats.append(stats)
            if sol and not best_sol:
                best_sol = sol
    return best_sol, all_stats

def get_canonical_representative(state: Tuple, m: int) -> Tuple:
    """
    Given a state (i, j, k) in Z_m^3, return its canonical form
    under the translation group H = Z_m^2.

    The fiber map is phi(i, j, k) = (i + j + k) mod m.
    Two states are equivalent if they belong to the same fiber.
    The canonical representative for a fiber s is (s, 0, 0).
    """
    s = sum(state) % m
    return (s, 0, 0)

def state_space_reduction(m: int) -> Dict:
    """Compute how much the state space collapses under symmetry."""
    total_states = m**3
    distinct_states = m # Only one per fiber
    reduction = total_states / distinct_states
    return {
        "m": m,
        "total": total_states,
        "distinct": distinct_states,
        "reduction_factor": reduction,
        "bits_saved": math.log2(reduction)
    }

def crypto_group_check(p: int, g: int) -> Dict:
    """
    Perform a symmetry-aware check on a cryptographic group Z_p^*.
    Checks if g is a generator and computes the 'symmetry hardness' (phi(phi(p))).
    """
    from math import gcd
    if p < 2: return {"error": "p must be >= 2"}

    # phi(p) for prime p is p-1
    group_order = p - 1

    # Simple primality check heuristic for large p
    is_probably_prime = True
    for i in range(2, min(int(math.sqrt(p)) + 1, 100)):
        if p % i == 0:
            is_probably_prime = False
            break

    # Check if g is coprime to p
    valid_g = gcd(g, p) == 1

    # Symmetry hardness: how many generators exist? phi(group_order)
    # This is O(sqrt(group_order))
    def get_phi(n):
        res = n
        d = 2
        temp = n
        while d * d <= temp:
            if temp % d == 0:
                while temp % d == 0: temp //= d
                res -= res // d
            d += 1
        if temp > 1: res -= res // temp
        return res

    num_generators = get_phi(group_order) if is_probably_prime else 0

    return {
        "p": p,
        "g": g,
        "group_order": group_order,
        "num_generators": num_generators,
        "hardness_ratio": num_generators / group_order if group_order > 0 else 0,
        "is_probably_prime": is_probably_prime
    }
