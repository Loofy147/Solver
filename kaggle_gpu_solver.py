import os
import subprocess
import sys

# Aggressively fix the environment for P100 (sm_60) compatibility
def fix_environment():
    print("Checking for GPU and compatibility...")
    try:
        import torch
        if torch.cuda.is_available():
            major, minor = torch.cuda.get_device_capability(0)
            print(f"Detected GPU: {torch.cuda.get_device_name(0)} (Capability {major}.{minor})")
            if major < 7:
                print("Architecture sm_60 (P100) detected. Standard Kaggle torch may be incompatible.")
                print("Re-installing torch with sm_60 support (cu118)...")
                # Uninstall existing torch components to avoid TORCH_LIBRARY conflicts
                subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio", "triton"])
                # Install a version known to support sm_60
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.4.0+cu118", "--index-url", "https://download.pytorch.org/whl/cu118"])
                print("Installation complete. Restarting process logic...")
                return True
        else:
            print("No GPU detected.")
    except Exception as e:
        print(f"Environment check/fix failed: {e}")
    return False

# If we re-installed, we might need to be careful about the current process state.
# However, in a Kaggle script, we can just proceed and hope the dynamic loader picks up the new libs.
# If not, we'd need to os.execv, but let's try direct import first.
fix_environment()

import torch
import math
import time
import random
from itertools import permutations

class GPUSolver:
    def __init__(self, m, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.m = m
        self.n = m**3
        self.device = device
        print(f"Initializing GPUSolver on {device}")

        # Test basic allocation
        try:
            test = torch.zeros(1, device=device)
            print("Basic GPU allocation successful.")
        except Exception as e:
            print(f"GPU allocation failed: {e}")
            self.device = 'cpu'
            device = 'cpu'

        self.arc_s = torch.zeros((self.n, 3), dtype=torch.long, device=device)
        for idx in range(self.n):
            i, rem = divmod(idx, m*m); j, k = divmod(rem, m)
            self.arc_s[idx, 0] = ((i + 1) % m) * m * m + j * m + k
            self.arc_s[idx, 1] = i * m * m + ((j + 1) % m) * m + k
            self.arc_s[idx, 2] = i * m * m + j * m + (k + 1) % m

        self._ALL_P3 = list(permutations(range(3)))
        pa = torch.zeros((6, 3), dtype=torch.long, device=device)
        for pi, p in enumerate(self._ALL_P3):
            for at, c in enumerate(p):
                pa[pi, c] = at
        self.pa = pa

    def _sa_score_gpu(self, sigma):
        num_chains = sigma.shape[0]
        total_score = torch.zeros(num_chains, device=self.device)
        arc_s_exp = self.arc_s.unsqueeze(0).expand(num_chains, -1, -1)
        base_labels = torch.arange(self.n, device=self.device).unsqueeze(0).expand(num_chains, -1)

        for c in range(3):
            at = self.pa[sigma, c]
            f = torch.gather(arc_s_exp, 2, at.unsqueeze(2)).squeeze(2)
            labels = base_labels.clone()
            jump = f
            for _ in range(math.ceil(math.log2(self.n)) + 1):
                # Use amin for min-label propagation
                labels = labels.scatter_reduce(1, jump, labels, reduce='amin', include_self=True)
                jump = torch.gather(jump, 1, jump)
            starts = (labels == base_labels)
            total_score += (starts.sum(dim=1).to(torch.float) - 1)
        return total_score

    def sigma_to_dict(self, sigma_tensor):
        sol = {}
        sigma_list = sigma_tensor.tolist()
        for idx, pi in enumerate(sigma_list):
            i, rem = divmod(idx, self.m*self.m); j, k = divmod(rem, self.m)
            sol[(i,j,k)] = tuple(self._ALL_P3[int(pi)])
        return sol

    def solve(self, num_chains=1024, max_iter=100000, T_init=2.0, T_min=0.01, orbits=None, p_equivariant=0.0, verbose=True, seed=42):
        torch.manual_seed(seed); random.seed(seed)
        sigma = torch.randint(0, 6, (num_chains, self.n), device=self.device)
        cs = self._sa_score_gpu(sigma); best_scores = cs.clone(); best_sigmas = sigma.clone()
        T = T_init; cool = (T_min / T_init)**(1.0 / max_iter)
        if orbits:
            max_len = max(len(o) for o in orbits); orbit_tensor = torch.full((len(orbits), max_len), -1, dtype=torch.long, device=self.device)
            for i, o in enumerate(orbits): orbit_tensor[i, :len(o)] = torch.tensor(o, dtype=torch.long, device=self.device)
            orbit_masks = (orbit_tensor != -1)
        else: orbit_tensor = None
        t0 = time.perf_counter()
        for i in range(max_iter):
            if (best_scores == 0).any(): break
            old_sigma = sigma.clone(); move_type = torch.rand(num_chains, device=self.device)
            is_equivariant = (move_type < p_equivariant) & (orbit_tensor is not None)
            v_std = torch.randint(0, self.n, (num_chains,), device=self.device); new_val_std = torch.randint(0, 6, (num_chains,), device=self.device)
            sigma[~is_equivariant, v_std[~is_equivariant]] = new_val_std[~is_equivariant]
            if is_equivariant.any():
                eq_indices = torch.where(is_equivariant)[0]; orbit_ids = torch.randint(0, orbit_tensor.shape[0], (len(eq_indices),), device=self.device)
                new_vals_eq = torch.randint(0, 6, (len(eq_indices),), device=self.device)
                for idx, (batch_idx, o_id) in enumerate(zip(eq_indices, orbit_ids)):
                    o = orbit_tensor[o_id]; mask = orbit_masks[o_id]; sigma[batch_idx, o[mask]] = new_vals_eq[idx]
            ns = self._sa_score_gpu(sigma); delta = ns - cs; accept = (delta <= 0) | (torch.rand(num_chains, device=self.device) < torch.exp(-delta / T))
            sigma[~accept] = old_sigma[~accept]; cs[accept] = ns[accept]
            mask = cs < best_scores
            if mask.any(): best_scores[mask] = cs[mask]; best_sigmas[mask] = sigma[mask]
            T *= cool
            if verbose and i % 5000 == 0:
                print(f"Iter {i:6d} | T: {T:.4f} | Best: {best_scores.min().item():4.1f} | Avg: {cs.mean().item():4.1f} | {time.perf_counter()-t0:.1f}s")
        idx = best_scores.argmin().item(); return best_sigmas[idx], best_scores[idx].item()

def solve_m6():
    m = 6; solver = GPUSolver(m); orbits = []
    def enc(i, j, k): return i*m*m + j*m + k
    for j in range(m):
        for k in range(m):
            orbits.append([enc(i, j, k) for i in [0, 3]]); orbits.append([enc(i, j, k) for i in [1, 4]]); orbits.append([enc(i, j, k) for i in [2, 5]])
            orbits.append([enc(i, j, k) for i in [0, 2, 4]]); orbits.append([enc(i, j, k) for i in [1, 3, 5]])
    print("\nStarting GPU SA for m=6, k=3")
    best_sigma, best_score = solver.solve(num_chains=1024, max_iter=200000, T_init=3.0, T_min=0.001, orbits=orbits, p_equivariant=0.2, verbose=True)
    if best_score == 0: print("SOLVED m=6!")
    else: print(f"Failed to solve m=6. Best score: {best_score}")

def solve_m8():
    m = 8; solver = GPUSolver(m)
    print("\nStarting GPU SA for m=8, k=3")
    best_sigma, best_score = solver.solve(num_chains=512, max_iter=300000, T_init=3.0, T_min=0.001, verbose=True)
    if best_score == 0: print("SOLVED m=8!")
    else: print(f"Failed to solve m=8. Best score: {best_score}")

if __name__ == "__main__":
    solve_m6()
    solve_m8()
