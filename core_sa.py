import random, math, time
from typing import Dict, List, Tuple, Optional
from core import _build_sa3, _sa_score, _ALL_P3, extract_weights, verify_sigma, PRECOMPUTED

def run_sa(m: int, seed: int=0, max_iter: int=5_000_000,
           T_init: float=3.0, T_min: float=0.003,
           verbose: bool=False, report_n: int=500_000,
           p_multi: float=0.05) -> Tuple[Optional[Dict], Dict]:
    """
    Full-3D SA for G_m (k=3) with coordinated multi-vertex flips.
    Returns (sigma_map | None, stats).
    """
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
            if d < 0 or rng.random() < math.exp(-d / max(T, 1e-9)):
                cs = ns
                if cs < bs: bs = cs; best = sigma[:]; stall = 0
                else: stall += 1
            else:
                for i, v in enumerate(v_indices): sigma[v] = old_vals[i]
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
            print(f"    it={it+1:>8,} T={T:.5f} s={cs} best={bs} reh={reheats} {el:.1f}s")

    elapsed = time.perf_counter() - t0
    sol = None
    if bs == 0:
        sol = {}
        for idx, pi in enumerate(best):
            i, rem = divmod(idx, m * m); j, k = divmod(rem, m)
            sol[(i, j, k)] = tuple(_ALL_P3[pi])
    return sol, {"best": bs, "iters": it + 1, "elapsed": elapsed, "reheats": reheats}
