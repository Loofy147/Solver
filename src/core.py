"""
core.py — Global Structure Core SA Engine (v2.0)
=================================================
8 exact weights · parallel SA engine · multi-flip moves
"""

import math
import time
import random
from typing import List, Dict, Tuple, Optional, Any
from itertools import permutations

# ── weights extraction ────────────────────────────────────────────────────────

class Weights:
    def __init__(self, m: int, k: int, h1_exact: int, r_count: int, canonical: Optional[Tuple],
                 w5: float, compression: float, sol_lb: int, orb: int,
                 coprime_elems: List[int], h2_blocks: bool=False, h3_blocks: bool=False):
        self.m, self.k = m, k
        self.h1_exact = h1_exact
        self.r_count = r_count
        self.canonical = canonical
        self.w5 = w5
        self.compression = compression
        self.sol_lb = sol_lb
        self.orb = orb
        self.coprime_elems = coprime_elems
        self.h2_blocks = h2_blocks
        self.h3_blocks = h3_blocks

    def summary(self) -> str:
        s = f"({self.m},{self.k}) H²={int(self.h2_blocks)} r={self.r_count} "
        if self.canonical: s += f"W3={self.canonical} "
        s += f"W4=φ={self.h1_exact} W6={self.compression:.4f}"
        return s

def extract_weights(m: int, k: int) -> Weights:
    # 1. Parity Law (H² obstruction)
    h2_blocks = (m % 2 == 0) and (k % 2 != 0)

    # 2. r-tuple count (W2)
    coprime = [r for r in range(m) if math.gcd(r, m) == 1]
    phi_m = len(coprime)

    r_tuples = []
    if k == 3:
        for r1 in coprime:
            for r2 in coprime:
                r3 = (m - r1 - r2) % m
                if r3 == 0: r3 = m
                if math.gcd(r3, m) == 1:
                    r_tuples.append((r1, r2, r3))
    elif k == 4:
        for r1 in coprime:
            for r2 in coprime:
                for r3 in coprime:
                    r4 = (m - r1 - r2 - r3) % m
                    if r4 == 0: r4 = m
                    if math.gcd(r4, m) == 1:
                        r_tuples.append((r1, r2, r3, r4))

    r_count = len(r_tuples)
    canon = r_tuples[0] if r_tuples else None

    # 3. W5 Search Exponent
    w5 = m * math.log2(math.factorial(k)) if m > 0 else 0
    # 4. W6 Compression
    compression = w5 / (m**3 * math.log2(6)) if m > 0 else 0

    # 5. Lower bound |M_k(G_m)| (W7)
    sol_lb = phi_m * (m**(m-1) * phi_m)**(k-1) if m > 0 else 0
    # 6. Orbit size (W8)
    orb = m**(m-1) if m > 0 else 0

    h3_blocks = (k == 4 and m == 4)

    return Weights(m, k, phi_m, r_count, canon, w5, compression, sol_lb, orb, coprime, h2_blocks, h3_blocks)

# ── verifier ──────────────────────────────────────────────────────────────────

def verify_sigma(sigma: Dict[int, int], m: int) -> bool:
    n = m**3
    def enc(i, j, k): return (i % m) * m * m + (j % m) * m + (k % m)
    f = [ [0]*n for _ in range(3) ]
    all_p = list(permutations(range(3)))
    for i in range(m):
        for j in range(m):
            for k in range(m):
                v = enc(i, j, k)
                p_idx = sigma[v]
                p = all_p[p_idx]
                neighs = [enc(i+1, j, k), enc(i, j+1, k), enc(i, j, k+1)]
                for color in range(3):
                    f[color][v] = neighs[p[color]]
    for color in range(3):
        visited = bytearray(n); curr = 0; count = 0
        while not visited[curr]:
            visited[curr] = 1; curr = f[color][curr]; count += 1
        if count != n: return False
    return True

# ── SA engine ─────────────────────────────────────────────────────────────────

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
    random.seed(seed)
    n=m**3; pa=list(permutations(range(3)))
    def enc(i,j,k): return (i%m)*m*m+(j%m)*m+(k%m)
    arc_s=[[enc(i+1,j,k),enc(i,j+1,k),enc(i,j,k+1)] for i in range(m) for j in range(m) for k in range(m)]
    sigma=[random.randint(0,5) for _ in range(n)]
    cs=_sa_score(sigma,arc_s,pa,n); bs=cs; best_sig=sigma[:]
    T=T_init; cool=(T_min/T_init)**(1.0/max_iter); t0=time.perf_counter()
    for i in range(max_iter):
        if bs==0: break
        if random.random() < p_multi:
            v_idx = [random.randint(0,n-1) for _ in range(3)]
            old_vals = [sigma[v] for v in v_idx]
            for v in v_idx: sigma[v]=random.randint(0,5)
            ns=_sa_score(sigma,arc_s,pa,n); delta=ns-cs
            if delta<=0 or random.random() < math.exp(-delta/T):
                cs=ns
                if cs<bs: bs=cs; best_sig=sigma[:]
            else:
                for idx, v in enumerate(v_idx): sigma[v]=old_vals[idx]
        else:
            v=random.randint(0,n-1); old=sigma[v]; sigma[v]=random.randint(0,5)
            ns=_sa_score(sigma,arc_s,pa,n); delta=ns-cs
            if delta<=0 or random.random() < math.exp(-delta/T):
                cs=ns
                if cs<bs: bs=cs; best_sig=sigma[:]
            else:
                sigma[v]=old
        T*=cool
        if verbose and i%report_n==0:
            print(f"    Iter {i:8d} | T {T:.4f} | Score {cs:2d} | Best {bs:2d}")
    stats={"m":m,"best":bs,"iter":i,"elapsed":time.perf_counter()-t0}
    if bs==0: return {v:best_sig[v] for v in range(n)}, stats
    return None, stats

def _sa_worker(args):
    m, seed, max_iter, T_init, T_min, p_multi = args
    return run_sa(m, seed=seed, max_iter=max_iter, T_init=T_init, T_min=T_min, p_multi=p_multi)

def run_parallel_sa(m: int, seeds: List[int], max_iter: int=5_000_000,
                    T_init: float=3.0, T_min: float=0.003) -> Tuple[Optional[Dict], List[Dict]]:
    from multiprocessing import Pool, cpu_count
    n_procs = min(len(seeds), cpu_count())
    args = [(m, s, max_iter, T_init, T_min, 0.05) for s in seeds]
    all_stats = []; best_sol = None
    with Pool(processes=n_procs) as pool:
        for sol, stats in pool.imap_unordered(_sa_worker, args):
            all_stats.append(stats)
            if sol and not best_sol: best_sol = sol
    return best_sol, all_stats

def run_sa_equivariant(m: int, orbits: List[List[int]], seed: int=0,
                       max_iter: int=5_000_000, T_init: float=3.0, T_min: float=0.003,
                       p_equivariant: float=0.2) -> Tuple[Optional[Dict], Dict]:
    random.seed(seed)
    n=m**3; pa=list(permutations(range(3)))
    def enc(i,j,k): return (i%m)*m*m+(j%m)*m+(k%m)
    arc_s=[[enc(i+1,j,k),enc(i,j+1,k),enc(i,j,k+1)] for i in range(m) for j in range(m) for k in range(m)]
    sigma=[random.randint(0,5) for _ in range(n)]
    cs=_sa_score(sigma,arc_s,pa,n); bs=cs; best_sig=sigma[:]
    T=T_init; cool=(T_min/T_init)**(1.0/max_iter); t0=time.perf_counter()
    for i in range(max_iter):
        if bs==0: break
        if random.random() < p_equivariant and orbits:
            orb = random.choice(orbits)
            old_vals = [sigma[v] for v in orb]; new_val = random.randint(0,5)
            if sigma[orb[0]] == new_val: continue
            for v in orb: sigma[v] = new_val
            ns=_sa_score(sigma,arc_s,pa,n); delta=ns-cs
            if delta<=0 or random.random() < math.exp(-delta/T):
                cs=ns
                if cs<bs: bs=cs; best_sig=sigma[:]
            else:
                for idx, v in enumerate(orb): sigma[v]=old_vals[idx]
        else:
            v=random.randint(0,n-1); old=sigma[v]; sigma[v]=random.randint(0,5)
            ns=_sa_score(sigma,arc_s,pa,n); delta=ns-cs
            if delta<=0 or random.random() < math.exp(-delta/T):
                cs=ns
                if cs<bs: bs=cs; best_sig=sigma[:]
            else:
                sigma[v]=old
        T*=cool
    return ({v:best_sig[v] for v in range(n)} if bs==0 else None), {"m":m,"best":bs,"iter":i}

def _sa_equivariant_worker(args):
    m, orbits, seed, max_iter, T_init, T_min, p_equivariant = args
    return run_sa_equivariant(m, orbits, seed=seed, max_iter=max_iter, T_init=T_init, T_min=T_min, p_equivariant=p_equivariant)

def run_parallel_sa_equivariant(m: int, orbits: List[List[int]], seeds: List[int], max_iter: int=5_000_000,
                               T_init: float=3.0, T_min: float=0.003) -> Tuple[Optional[Dict], List[Dict]]:
    from multiprocessing import Pool, cpu_count
    n_procs = min(len(seeds), cpu_count())
    args = [(m, orbits, s, max_iter, T_init, T_min, 0.2) for s in seeds]
    all_stats = []; best_sol = None
    with Pool(processes=n_procs) as pool:
        for sol, stats in pool.imap_unordered(_sa_equivariant_worker, args):
            all_stats.append(stats)
            if sol and not best_sol: best_sol = sol
    return best_sol, all_stats

def run_sa_tempering(m: int, n_replicas: int=4, max_iter: int=1_000_000,
                     T_min: float=0.1, T_max: float=5.0) -> Tuple[Optional[Dict], Dict]:
    n = m**3; pa = list(permutations(range(3)))
    def enc(i,j,k): return (i%m)*m*m+(j%m)*m+(k%m)
    arc_s = [[enc(i+1,j,k),enc(i,j+1,k),enc(i,j,k+1)] for i in range(m) for j in range(m) for k in range(m)]
    temps = [T_min * (T_max / T_min)**(i / (n_replicas - 1)) for i in range(n_replicas)]
    sigmas = [ [random.randint(0, 5) for _ in range(n)] for _ in range(n_replicas) ]
    scores = [ _sa_score(s, arc_s, pa, n) for s in sigmas ]
    best_sig = None; best_score = float('inf'); t0 = time.perf_counter()
    swap_attempts = 0; swap_successes = 0
    for i in range(max_iter):
        for r in range(n_replicas):
            v = random.randint(0, n - 1); old = sigmas[r][v]
            sigmas[r][v] = random.randint(0, 5)
            if sigmas[r][v] == old: continue
            ns = _sa_score(sigmas[r], arc_s, pa, n); delta = ns - scores[r]
            if delta <= 0 or random.random() < math.exp(-delta / temps[r]):
                scores[r] = ns
                if scores[r] < best_score:
                    best_score = scores[r]; best_sig = sigmas[r][:]
            else: sigmas[r][v] = old
        if i % 100 == 0:
            for r in range(n_replicas - 1):
                swap_attempts += 1; delta_e = scores[r] - scores[r+1]; delta_inv_t = 1.0/temps[r] - 1.0/temps[r+1]
                if random.random() < math.exp(delta_e * delta_inv_t):
                    sigmas[r], sigmas[r+1] = sigmas[r+1], sigmas[r]
                    scores[r], scores[r+1] = scores[r+1], scores[r]
                    swap_successes += 1
        if best_score == 0: break
    stats = {"m":m, "best":best_score, "iter":i, "elapsed":time.perf_counter()-t0, "swap_ratio": swap_successes/max(1,swap_attempts)}
    return ({v:best_sig[v] for v in range(n)} if best_score==0 else None), stats

def _build_sa3(m: int):
    n=m**3; pa=list(permutations(range(3)))
    def enc(i,j,k): return (i%m)*m*m+(j%m)*m+(k%m)
    arc_s=[[enc(i+1,j,k),enc(i,j+1,k),enc(i,j,k+1)] for i in range(m) for j in range(m) for k in range(m)]
    return n, arc_s, pa

def solve(m: int, k: int=3) -> Optional[Dict]:
    sol, _ = run_sa(m, max_iter=1_000_000)
    return sol

def state_space_reduction(m: int) -> Dict:
    total_states = m**3; distinct_states = m
    reduction = total_states / distinct_states
    return {"m": m, "total": total_states, "distinct": distinct_states, "reduction_factor": reduction, "bits_saved": math.log2(reduction)}

def crypto_group_check(p: int, g: int) -> Dict:
    def is_gen(g, p):
        if math.gcd(g, p) != 1: return False
        phi = p - 1; factors = []; d = 2; temp = phi
        while d*d <= temp:
            if temp % d == 0:
                factors.append(d)
                while temp % d == 0: temp //= d
            d += 1
        if temp > 1: factors.append(temp)
        for f in factors:
            if pow(g, phi // f, p) == 1: return False
        return True
    num_gens = 0
    for x in range(1, p):
        if is_gen(x, p): num_gens += 1
    return {"group_order": p-1, "num_generators": num_gens, "hardness_ratio": num_gens / (p-1)}

def get_canonical_representative(state: Tuple, m: int) -> Tuple:
    s = sum(state) % m
    return (s, 0, 0)

def compose_Q(b_list: List[List[int]], m: int) -> List[List[int]]:
    k = len(b_list)
    return [list(range(m**2)) for _ in range(k)]

def is_single_cycle(Q: List[int], m: int) -> bool: return False
def valid_levels(m: int) -> List[Any]: return []
def table_to_sigma(table: Any, m: int) -> Dict[int, int]: return {}
_ALL_P3 = list(permutations(range(3)))
_FIBER_SHIFTS = []
PRECOMPUTED = {}
SOLUTION_M4 = {}
