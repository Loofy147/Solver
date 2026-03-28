import os
import subprocess
import sys

def fix_environment():
    if os.environ.get('ENV_FIXED') == '1':
        return

    print("Checking for GPU compatibility...")
    try:
        import torch
        if torch.cuda.is_available():
            major, _ = torch.cuda.get_device_capability(0)
            if major < 7: # sm_60 (P100) or older
                print(f"Architecture sm_{major}0 (P100) detected. Fixing environment...")
                subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio", "triton"])
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.3.1+cu118", "--index-url", "https://download.pytorch.org/whl/cu118"])
                print("Environment fixed. Restarting process...")
                os.environ['ENV_FIXED'] = '1'
                os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"Setup warning: {e}")

fix_environment()

import torch
import math
import time
import random
from itertools import permutations

class GPUSolver:
    def __init__(self, m, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.m = m; self.n = m**3; self.device = device
        print(f"Initializing GPUSolver(m={m}) on {device}")

        # Precompute successor table
        arc_s = torch.zeros((self.n, 3), dtype=torch.long, device=device)
        for idx in range(self.n):
            i, rem = divmod(idx, m*m); j, k = divmod(rem, m)
            arc_s[idx, 0] = ((i + 1) % m) * m * m + j * m + k
            arc_s[idx, 1] = i * m * m + ((j + 1) % m) * m + k
            arc_s[idx, 2] = i * m * m + j * m + (k + 1) % m
        self.arc_s = arc_s

        # Precompute permutation table
        self._ALL_P3 = list(permutations(range(3)))
        pa = torch.zeros((6, 3), dtype=torch.long, device=device)
        for pi, p in enumerate(self._ALL_P3):
            for at, c in enumerate(p): pa[pi, c] = at
        self.pa = pa

    def _sa_score_gpu(self, sigma):
        num_chains = sigma.shape[0]
        total_score = torch.zeros(num_chains, device=self.device)
        arc_s_exp = self.arc_s.unsqueeze(0).expand(num_chains, -1, -1)
        base_labels = torch.arange(self.n, device=self.device).unsqueeze(0).expand(num_chains, -1)

        for c in range(3):
            at = self.pa[sigma, c]
            f = torch.gather(arc_s_exp, 2, at.unsqueeze(2)).squeeze(2)
            labels = base_labels.clone(); jump = f
            for _ in range(math.ceil(math.log2(self.n)) + 1):
                labels = labels.scatter_reduce(1, jump, labels, reduce='amin', include_self=True)
                jump = torch.gather(jump, 1, jump)
            starts = (labels == base_labels)
            total_score += (starts.sum(dim=1).to(torch.float) - 1)
        return total_score

    def solve(self, num_chains=1024, max_iter=200000, T_init=3.0, T_min=0.001, orbits=None, p_equivariant=0.0, verbose=True):
        sigma = torch.randint(0, 6, (num_chains, self.n), device=self.device)
        cs = self._sa_score_gpu(sigma); bs = cs.clone(); best_sigmas = sigma.clone()
        T = T_init; cool = (T_min / T_init)**(1.0 / max_iter); t0 = time.perf_counter()

        if orbits:
            max_len = max(len(o) for o in orbits); orb_t = torch.full((len(orbits), max_len), -1, dtype=torch.long, device=self.device)
            for i, o in enumerate(orbits): orb_t[i, :len(o)] = torch.tensor(o, dtype=torch.long, device=self.device)
            orb_m = (orb_t != -1)
        else: orb_t = None

        for i in range(max_iter):
            if (bs == 0).any(): break
            old_sigma = sigma.clone(); move_type = torch.rand(num_chains, device=self.device)
            is_eq = (move_type < p_equivariant) & (orb_t is not None)
            v_std = torch.randint(0, self.n, (num_chains,), device=self.device)
            sigma[~is_eq, v_std[~is_eq]] = torch.randint(0, 6, (num_chains,), device=self.device)[~is_eq]
            if is_eq.any():
                eq_idx = torch.where(is_eq)[0]; orb_ids = torch.randint(0, orb_t.shape[0], (len(eq_idx),), device=self.device)
                vals = torch.randint(0, 6, (len(eq_idx),), device=self.device)
                for idx, (b_idx, o_id) in enumerate(zip(eq_idx, orb_ids)):
                    o = orb_t[o_id]; msk = orb_m[o_id]; sigma[b_idx, o[msk]] = vals[idx]
            ns = self._sa_score_gpu(sigma); delta = ns - cs
            accept = (delta <= 0) | (torch.rand(num_chains, device=self.device) < torch.exp(-delta / T))
            sigma[~accept] = old_sigma[~accept]; cs[accept] = ns[accept]
            mask = cs < bs; bs[mask] = cs[mask]; best_sigmas[mask] = sigma[mask]
            T *= cool
            if verbose and i % 5000 == 0:
                print(f"Iter {i:6d} | T: {T:.4f} | Best: {bs.min().item():4.1f} | Avg: {cs.mean().item():4.1f} | {time.perf_counter()-t0:.1f}s")
        idx = bs.argmin().item(); return best_sigmas[idx], bs[idx].item()

def solve_m6():
    m = 6; solver = GPUSolver(m); orbits = []
    def enc(i,j,k): return i*36+j*6+k
    for j in range(m):
        for k in range(m):
            orbits.append([enc(i,j,k) for i in [0,3]]); orbits.append([enc(i,j,k) for i in [1,4]]); orbits.append([enc(i,j,k) for i in [2,5]])
    print("\nStarting m=6 breakthrough search...")
    best_sigma, best_score = solver.solve(num_chains=1024, max_iter=10000000, p_equivariant=0.2)
    if best_score == 0: print("SOLVED m=6!")
    else: print(f"Best score for m=6: {best_score}")

if __name__ == "__main__":
    solve_m6()
