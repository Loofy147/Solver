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

        # Precompute tables
        arc_s = torch.zeros((self.n, 3), dtype=torch.long, device=device)
        for idx in range(self.n):
            i, rem = divmod(idx, m*m); j, k = divmod(rem, m)
            arc_s[idx, 0] = ((i + 1) % m) * m * m + j * m + k
            arc_s[idx, 1] = i * m * m + ((j + 1) % m) * m + k
            arc_s[idx, 2] = i * m * m + j * m + (k + 1) % m
        self.arc_s = arc_s

        self._ALL_P3 = list(permutations(range(3)))
        pa = torch.zeros((6, 3), dtype=torch.long, device=device)
        for pi, p in enumerate(self._ALL_P3):
            for at, c in enumerate(p):
                pa[pi, c] = at
        self.pa = pa

    def _sa_score_gpu(self, sigma):
        """
        Vectorized score function matching core.py's cc(f) exactly.
        Counts number of components in a functional graph (out-degree 1).
        """
        num_chains = sigma.shape[0]
        total_score = torch.zeros(num_chains, device=self.device)
        arc_s_exp = self.arc_s.unsqueeze(0).expand(num_chains, -1, -1)

        base_labels = torch.arange(self.n, device=self.device).unsqueeze(0).expand(num_chains, -1)

        for c in range(3):
            at = self.pa[sigma, c]
            f = torch.gather(arc_s_exp, 2, at.unsqueeze(2)).squeeze(2)

            # Use label propagation: labels[v] = min { s : s reaches v }
            # After path doubling, labels will store the min index of the component's root or cycle.
            labels = base_labels.clone()
            jump = f

            for _ in range(math.ceil(math.log2(self.n)) + 1):
                # Pull labels from predecessors: labels[jump[v]] = min(labels[jump[v]], labels[v])
                labels = labels.scatter_reduce(1, jump, labels, reduce='amin', include_self=True)
                # jump[v] = jump[jump[v]]
                jump = torch.gather(jump, 1, jump)

            # Node v is a 'start' in cc(f) iff it was never reachable from any s < v.
            # This is equivalent to labels[v] == v.
            starts = (labels == base_labels)
            counts = starts.sum(dim=1).to(torch.float)
            total_score += (counts - 1)

        return total_score

    def sigma_to_dict(self, sigma_tensor):
        sol = {}
        sigma_list = sigma_tensor.tolist()
        for idx, pi in enumerate(sigma_list):
            i, rem = divmod(idx, self.m*self.m); j, k = divmod(rem, self.m)
            sol[(i,j,k)] = tuple(self._ALL_P3[int(pi)])
        return sol

    def solve(self, num_chains=1024, max_iter=100000, T_init=2.0, T_min=0.01,
              orbits=None, p_equivariant=0.0, verbose=True, seed=42):
        torch.manual_seed(seed); random.seed(seed)
        sigma = torch.randint(0, 6, (num_chains, self.n), device=self.device)
        cs = self._sa_score_gpu(sigma)
        best_scores = cs.clone(); best_sigmas = sigma.clone()
        T = T_init; cool = (T_min / T_init)**(1.0 / max_iter)
        if orbits:
            max_len = max(len(o) for o in orbits)
            orbit_tensor = torch.full((len(orbits), max_len), -1, dtype=torch.long, device=self.device)
            for i, o in enumerate(orbits):
                orbit_tensor[i, :len(o)] = torch.tensor(o, dtype=torch.long, device=self.device)
            orbit_masks = (orbit_tensor != -1)
        else:
            orbit_tensor = None
        t0 = time.perf_counter()
        for i in range(max_iter):
            if (best_scores == 0).any(): break
            old_sigma = sigma.clone()
            move_type = torch.rand(num_chains, device=self.device)
            is_equivariant = (move_type < p_equivariant) & (orbit_tensor is not None)
            v_std = torch.randint(0, self.n, (num_chains,), device=self.device)
            new_val_std = torch.randint(0, 6, (num_chains,), device=self.device)
            sigma[~is_equivariant, v_std[~is_equivariant]] = new_val_std[~is_equivariant]
            if is_equivariant.any():
                eq_indices = torch.where(is_equivariant)[0]
                orbit_ids = torch.randint(0, orbit_tensor.shape[0], (len(eq_indices),), device=self.device)
                new_vals_eq = torch.randint(0, 6, (len(eq_indices),), device=self.device)
                for idx, (batch_idx, o_id) in enumerate(zip(eq_indices, orbit_ids)):
                    o = orbit_tensor[o_id]; mask = orbit_masks[o_id]
                    sigma[batch_idx, o[mask]] = new_vals_eq[idx]
            ns = self._sa_score_gpu(sigma); delta = ns - cs
            accept = (delta <= 0) | (torch.rand(num_chains, device=self.device) < torch.exp(-delta / T))
            sigma[~accept] = old_sigma[~accept]; cs[accept] = ns[accept]
            mask = cs < best_scores
            if mask.any(): best_scores[mask] = cs[mask]; best_sigmas[mask] = sigma[mask]
            T *= cool
            if verbose and i % 5000 == 0:
                elapsed = time.perf_counter() - t0
                print(f"Iter {i:6d} | T: {T:.4f} | Best: {best_scores.min().item():4.1f} | Avg: {cs.mean().item():4.1f} | {elapsed:.1f}s")
        idx = best_scores.argmin().item()
        return best_sigmas[idx], best_scores[idx].item()
