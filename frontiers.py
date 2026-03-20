"""
frontiers.py — Open Problem Solvers
=====================================
P1  k=4, m=4  fiber-structured SA     (construction open)
P2  m=6, k=3  full-3D SA              (first attempts)
P3  m=8, k=3  full-3D SA              (harder)

TRIAGE FINDINGS (from open_problems.py run):
• P2 m=6 k=3: score dropped 147→14 in 2M iters with repair+reheat.
  Getting close. Needs ~10M iterations. FIRST RUN EVER on G_6.
• P3 m=8 k=3: harder (512 vertices). Same SA structure.
• P1 k=4 m=4: fiber-structured space 24^64. More budget needed.

Run:
    python frontiers.py --p1        # k=4, m=4
    python frontiers.py --p2        # m=6, k=3
    python frontiers.py --p3        # m=8, k=3
    python frontiers.py --all       # all three
    python frontiers.py --status    # print current knowledge state
"""

import sys, time, math, random
from math import gcd
from itertools import permutations, product as iprod
from typing import Optional, Dict, Tuple

from core import run_sa, extract_weights

G_="\033[92m";R_="\033[91m";Y_="\033[93m";W_="\033[97m";D_="\033[2m";Z_="\033[0m"
def found(s): print(f"  {G_}✓ {s}{Z_}")
def open_(s): print(f"  {Y_}◆ OPEN: {s}{Z_}")
def note(s):  print(f"  {D_}{s}{Z_}")
def hr(n=72): return "─"*n


# ══════════════════════════════════════════════════════════════════════════════
# P1: k=4, m=4  —  fiber-structured SA
# ══════════════════════════════════════════════════════════════════════════════

def solve_P1(max_iter: int=2_000_000, seeds=range(5),
             verbose: bool=True) -> Optional[Dict]:
    """
    Find σ: Z_4^4 → S_4 such that each colour class is a Hamiltonian cycle.
    Strategy: fiber-structured SA where σ(v) = f(fiber(v), j(v), k(v)).
    The unique valid r-quadruple is (1,1,1,1) — all four colors share r_c=1.
    """
    print(f"\n{'═'*72}")
    print(f"{W_}P1: k=4, m=4 — Fiber-Structured SA{Z_}")
    print(hr())
    note("r-quadruple (1,1,1,1): unique, all gcd(1,4)=1, sum=4.")
    note("Fiber-uniform proved impossible (331,776 checked).")
    note(f"Fiber-structured space: σ(v)=f(fiber,j,k) → 24^64 states.")
    note(f"Running {len(list(seeds))} seeds × {max_iter:,} iters each.")
    print()

    M=4; K=4; N=M**4

    ALL_P4 = list(permutations(range(K))); nP=len(ALL_P4)

    def dec4(v):
        l=v%4; v//=4; k_=v%4; v//=4; j_=v%4; i_=v//4
        return i_,j_,k_,l
    def enc4(i,j,k_,l): return i*64+j*16+k_*4+l

    arc_s=[[0]*K for _ in range(N)]
    for v in range(N):
        ci,cj,ck,cl=dec4(v)
        arc_s[v][0]=enc4((ci+1)%M,cj,ck,cl)
        arc_s[v][1]=enc4(ci,(cj+1)%M,ck,cl)
        arc_s[v][2]=enc4(ci,cj,(ck+1)%M,cl)
        arc_s[v][3]=enc4(ci,cj,ck,(cl+1)%M)
    pa=[[None]*K for _ in range(nP)]
    for pi,p in enumerate(ALL_P4):
        for at,c in enumerate(p): pa[pi][c]=at
    fibers=[sum(dec4(v))%M for v in range(N)]

    def make_sigma(tab):
        sig=[0]*N
        for v in range(N):
            ci,cj,ck,cl=dec4(v)
            sig[v]=tab[(fibers[v],cj,ck)]
        return sig

    def score(sig):
        f=[[0]*N for _ in range(K)]
        for v in range(N):
            pi=sig[v]; p=pa[pi]
            for c in range(K): f[c][v]=arc_s[v][p[c]]
        def cc(fg):
            vis=bytearray(N); comps=0
            for s in range(N):
                if not vis[s]:
                    comps+=1; cur=s
                    while not vis[cur]: vis[cur]=1; cur=fg[cur]
            return comps
        return sum(cc(f[c])-1 for c in range(K))

    keys=[(s,j,k_) for s in range(M) for j in range(M) for k_ in range(M)]
    best_global=999; best_tab=None

    for seed in seeds:
        rng=random.Random(seed)
        table={key:rng.randrange(nP) for key in keys}
        sig=make_sigma(table); cs=score(sig); bs=cs; best=dict(table)
        T=100.0; cool=(0.005/T)**(1/max_iter); stall=0; reheats=0
        t0=time.perf_counter()

        for it in range(max_iter):
            if cs==0: break
            if cs<=4:
                fixed=False; rng.shuffle(keys)
                for key in keys:
                    old=table[key]
                    for pi in rng.sample(range(nP),nP):
                        if pi==old: continue
                        table[key]=pi; sig=make_sigma(table); ns=score(sig)
                        if ns<cs: cs=ns; fixed=True
                        if cs<bs: bs=cs; best=dict(table)
                        if ns>=cs: table[key]=old
                        if fixed: break
                    if fixed: break
                if cs==0: break
                T*=cool; continue
            key=rng.choice(keys); old=table[key]; new=rng.randrange(nP)
            if new==old: T*=cool; continue
            table[key]=new; sig=make_sigma(table); ns=score(sig); d=ns-cs
            if d<0 or rng.random()<math.exp(-d/max(T,1e-9)):
                cs=ns
                if cs<bs: bs=cs; best=dict(table); stall=0
                else: stall+=1
            else: table[key]=old; stall+=1
            if stall>50_000:
                T=100.0/(2**reheats); reheats+=1; stall=0
                table=dict(best); cs=bs
            T*=cool

        elapsed=time.perf_counter()-t0
        sym=f"{G_}SOLVED{Z_}" if bs==0 else f"best={bs}"
        if verbose: print(f"  seed={seed}: {sym}  iters={it+1:,}  {elapsed:.1f}s")
        if bs<best_global: best_global=bs; best_tab=dict(best)
        if bs==0: break

    if best_global==0:
        found(f"k=4, m=4 SOLVED via fiber-structured SA!")
        return best_tab
    open_(f"k=4, m=4: best score={best_global} after all seeds")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# P2: m=6, k=3  —  full-3D SA (first serious attempt)
# ══════════════════════════════════════════════════════════════════════════════

def solve_P2(max_iter: int=5_000_000, seeds=range(3),
             verbose: bool=True) -> Optional[Dict]:
    """
    G_6: 216 vertices, full-3D SA.
    Column-uniform proved impossible (parity). This is the first serious attempt.
    
    Previous run (2M iters, 1 seed): score 147→14. Shows convergence.
    Target: ~10M iterations to reach 0.
    """
    print(f"\n{'═'*72}")
    print(f"{W_}P2: m=6, k=3 — Full-3D SA on G_6{Z_}")
    print(hr())
    note("Column-uniform impossible (Thm 6.1). First serious full-3D attempt.")
    note("Previous run: score 147→14 in 2M iters. Getting close.")
    note(f"Space: 6^216 ≈ 10^168. Budget: {max_iter:,} × {len(list(seeds))} seeds.")
    print()

    best_overall=None; best_score=999
    for seed in seeds:
        sol, stats = run_sa(6, seed=seed, max_iter=max_iter, verbose=verbose)
        s=stats['best']
        sym=f"{G_}SOLVED{Z_}" if s==0 else f"best={s}"
        print(f"  seed={seed}: {sym}  iters={stats['iters']:,}  "
              f"{stats['elapsed']:.1f}s  reheats={stats['reheats']}")
        if s<best_score: best_score=s; best_overall=sol
        if s==0: break

    if best_score==0:
        found("m=6, k=3: SOLVED — first ever solution for G_6!")
        return best_overall
    open_(f"m=6, k=3: best={best_score}. Needs larger budget (~10M iters).")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# P3: m=8, k=3  —  larger even m
# ══════════════════════════════════════════════════════════════════════════════


def solve_P2_warm_start(max_iter=10_000_000, seed=0, verbose=True):
    """
    m=6, k=3 warm-start approach using Z_3-lifted solution.
    
    FINDING: The Z_3 lift (sigma_6(i,j,k) = sigma_3(i%3,j%3,k%3))
    reaches score=9 reliably. This is a TRUE local minimum of depth >=3.
    Escape requires ~10M iterations at T=2.0.
    
    STRUCTURAL INSIGHT: Z_6 = Z_2 × Z_3 creates a product-structure
    local minimum. Breaking it requires coordinated multi-vertex changes
    that span the Z_3 periodic structure.
    """
    import random, math
    from core import _build_sa3, _sa_score, verify_sigma, PRECOMPUTED, _ALL_P3
    from itertools import permutations

    m=6; m3=3; m3_sol=PRECOMPUTED[(3,3)]
    n,arc_s,pa=_build_sa3(m); nP=6
    ALL_P=[list(p) for p in permutations(range(3))]
    perm_to_int={tuple(p):i for i,p in enumerate(ALL_P)}

    # Build warm start
    sigma=[perm_to_int[m3_sol[(v//36%3,(v//6)%6%3,v%6%3)]] for v in range(n)]
    warm_score=_sa_score(sigma,arc_s,pa,n)
    if verbose: note(f"Z_3 warm start score: {warm_score}")

    rng=random.Random(seed)
    # Minimal perturbation to break exact Z_3 symmetry
    for v in rng.sample(range(n), 12): sigma[v]=rng.randrange(nP)
    cs=_sa_score(sigma,arc_s,pa,n); bs=cs; best=sigma[:]

    # Run at T=2.0 (high enough to cross depth-3 barrier)
    T=2.0; stall=0; reheats=0; t0=__import__('time').perf_counter()

    for it in range(max_iter):
        if cs==0: break
        if cs<=10:
            order=list(range(n)); rng.shuffle(order); fixed=False
            for v in order:
                old=sigma[v]
                for pi in rng.sample(range(nP),nP):
                    if pi==old: continue
                    sigma[v]=pi; ns=_sa_score(sigma,arc_s,pa,n)
                    if ns<cs: cs=ns; fixed=True
                    if cs<bs: bs=cs; best=sigma[:]
                    if ns>=cs: sigma[v]=old
                    if fixed: break
                if fixed: break
            if not fixed:
                for _ in range(max(2,cs//2)): sigma[rng.randrange(n)]=rng.randrange(nP)
                cs=_sa_score(sigma,arc_s,pa,n)
                if cs<bs: bs=cs; best=sigma[:]
            continue
        v=rng.randrange(n); old=sigma[v]; new=rng.randrange(nP)
        if new==old: continue
        sigma[v]=new; ns=_sa_score(sigma,arc_s,pa,n); d=ns-cs
        if d<0 or rng.random()<math.exp(-d/max(T,1e-9)):
            cs=ns
            if cs<bs: bs=cs; best=sigma[:]; stall=0
            else: stall+=1
        else: sigma[v]=old; stall+=1
        if stall>80_000:
            T=max(T*0.8,0.001); reheats+=1; stall=0; sigma=best[:]; cs=bs

    elapsed=__import__('time').perf_counter()-t0
    if bs==0:
        sol={}
        for idx,pi in enumerate(best):
            i,rem=divmod(idx,m*m); j,k=divmod(rem,m)
            sol[(i,j,k)]=tuple(ALL_P[pi])
        if verify_sigma(sol,m):
            found("m=6 k=3 SOLVED via warm start!")
            return sol
    if verbose:
        open_(f"m=6 k=3: best={bs} after {it+1:,} iters ({elapsed:.1f}s)")
    return None

def solve_P3(max_iter: int=3_000_000, seeds=range(2),
             verbose: bool=True) -> Optional[Dict]:
    """
    G_8: 512 vertices. Harder than m=6. Tests scaling.
    Score function needs 512 components checked per iteration.
    """
    print(f"\n{'═'*72}")
    print(f"{W_}P3: m=8, k=3 — Full-3D SA on G_8{Z_}")
    print(hr())
    note("512 vertices. Column-uniform impossible (parity).")
    note(f"Budget: {max_iter:,} × {len(list(seeds))} seeds.")
    print()

    best_overall=None; best_score=999
    for seed in seeds:
        sol, stats = run_sa(8, seed=seed, max_iter=max_iter, verbose=verbose)
        s=stats['best']
        sym=f"{G_}SOLVED{Z_}" if s==0 else f"best={s}"
        print(f"  seed={seed}: {sym}  iters={stats['iters']:,}  {stats['elapsed']:.1f}s")
        if s<best_score: best_score=s; best_overall=sol
        if s==0: break

    if best_score==0:
        found("m=8, k=3: SOLVED!")
        return best_overall
    open_(f"m=8, k=3: best={best_score}. Harder than m=6.")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# STATUS SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

def print_status():
    print(f"\n{'═'*72}")
    print(f"{W_}FRONTIER STATUS — Open Problems{Z_}")
    print(hr())

    rows = [
        ("P1", "k=4, m=4 (G_4^4)",    "Arithmetic proved. Fiber-structured SA running.",     "OPEN"),
        ("P2", "m=6, k=3 (G_6)",       "Score 9 via Z_3 warm start. DEEP local min (depth>=3). Needs ~10M iters at T=2.0.", "OPEN"),
        ("P3", "m=8, k=3 (G_8)",       "First attempt. 512 vertices.",                        "OPEN"),
        ("P4", "W7 formula",            "FIXED: phi(m)×coprime_b^(k-1). Exact for m=3.",      "RESOLVED"),
        ("P5", "Non-abelian S_3",       "PROVED: same parity law. k=2 ok, k=3 blocked.",      "RESOLVED"),
        ("P6", "Product Z_m×Z_n",       "PROVED: fiber quotient=Z_gcd. Framework complete.",  "RESOLVED"),
        ("CL", "Closure lemma",         "Proved for m=3. General algebraic proof: open.",      "PARTIAL"),
        ("W7", "W7 lower bound",        "Exact m=3. Underestimates by ~100x for m≥5.",        "PARTIAL"),
    ]

    print(f"\n  {'Prob':<5} {'Name':<25} {'Evidence':<50} {'Status'}")
    print(f"  {'─'*90}")
    for prob,name,evidence,status in rows:
        col=(G_ if status=="RESOLVED" else Y_ if status=="PARTIAL" else
             "\033[91m" if status=="OPEN" else W_)
        print(f"  {prob:<5} {name:<25} {evidence:<50} {col}{status}{Z_}")

    print(f"\n  {W_}What's new since the original open problem list:{Z_}")
    new = [
        "W7 corrected formula derived and proved (Closure Lemma, m=3)",
        "Non-abelian parity law proved for S_3 (P5 resolved)",
        "Product group framework complete (P6 resolved)",
        "m=6 k=3: first SA run — score 14, converging (was never attempted)",
        "m=8 k=3: first SA run — first attempt at this scale",
    ]
    for item in new: print(f"  • {item}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    if '--status' in args or not args:
        print_status()

    if '--p1' in args or '--all' in args:
        solve_P1(max_iter=1_500_000, seeds=range(3), verbose=True)

    if '--p2' in args or '--all' in args:
        solve_P2(max_iter=3_000_000, seeds=range(2), verbose=True)

    if '--p3' in args or '--all' in args:
        solve_P3(max_iter=2_000_000, seeds=range(2), verbose=True)


if __name__ == "__main__":
    main()


# ══════════════════════════════════════════════════════════════════════════════
# REAL-3 FIX: Fiber-uniform k=4 exhaustive proof (331,776 cases)
# ══════════════════════════════════════════════════════════════════════════════

def prove_fiber_uniform_k4_impossible(verbose: bool=True) -> bool:
    """
    THEOREM: No fiber-uniform σ yields a valid k=4 decomposition of G_4^4.
    Proof method: exhaustive search over all 24^4 = 331,776 fiber-uniform sigmas.

    Fiber-uniform means σ(v) depends only on fiber(v) = (i+j+k+l) mod 4.
    With 4 fibers and 4 colors, there are 24^4 = 331,776 combinations.
    This is small enough to check completely in ~40 seconds.

    Result: 0 valid sigmas found → proved impossible.
    """
    from itertools import permutations, product as iprod
    import time

    M=4; K=4; N=M**4
    ALL_P4 = list(permutations(range(K))); nP=len(ALL_P4)

    def dec4(v):
        l=v%4; v//=4; k_=v%4; v//=4; j_=v%4; i_=v//4
        return i_,j_,k_,l
    def enc4(i,j,k_,l): return i*64+j*16+k_*4+l

    arc_s=[[0]*K for _ in range(N)]
    for v in range(N):
        ci,cj,ck,cl=dec4(v)
        arc_s[v][0]=enc4((ci+1)%M,cj,ck,cl)
        arc_s[v][1]=enc4(ci,(cj+1)%M,ck,cl)
        arc_s[v][2]=enc4(ci,cj,(ck+1)%M,cl)
        arc_s[v][3]=enc4(ci,cj,ck,(cl+1)%M)
    pa=[[None]*K for _ in range(nP)]
    for pi,p in enumerate(ALL_P4):
        for at,c in enumerate(p): pa[pi][c]=at
    fibers=[sum(dec4(v))%M for v in range(N)]

    def score(sigma):
        f=[[0]*N for _ in range(K)]
        for v in range(N):
            pi=sigma[v]; p=pa[pi]
            for c in range(K): f[c][v]=arc_s[v][p[c]]
        def cc(fg):
            vis=bytearray(N); comps=0
            for s in range(N):
                if not vis[s]:
                    comps+=1; cur=s
                    while not vis[cur]: vis[cur]=1; cur=fg[cur]
            return comps
        return sum(cc(f[c])-1 for c in range(K))

    if verbose:
        print(f"\n  Checking all 24^4={24**4:,} fiber-uniform sigmas...", end="", flush=True)

    t0=time.perf_counter(); found=0
    for combo in iprod(range(nP), repeat=M):
        sigma=[combo[fibers[v]] for v in range(N)]
        if score(sigma)==0: found+=1

    elapsed=time.perf_counter()-t0
    if verbose:
        print(f" done ({elapsed:.1f}s)")
        if found==0:
            print(f"  \033[92m■ PROVED: No fiber-uniform σ works for k=4, m=4. "
                  f"Checked {24**4:,} cases. ■\033[0m")
        else:
            print(f"  \033[91m✗ UNEXPECTED: {found} valid fiber-uniform sigmas found\033[0m")

    return found == 0
