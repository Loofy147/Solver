import torch
import math
import time
from itertools import permutations

class GPUSolver:
    def __init__(self, m, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.m = m; self.n = m**3; self.device = device
        arc_s = torch.zeros((self.n, 3), dtype=torch.long, device=device)
        for idx in range(self.n):
            i, rem = divmod(idx, m*m); j, k = divmod(rem, m)
            arc_s[idx, 0] = ((i + 1) % m) * m * m + j * m + k
            arc_s[idx, 1] = i * m * m + ((j + 1) % m) * m + k
            arc_s[idx, 2] = i * m * m + j * m + (k + 1) % m
        self.arc_s = arc_s
        self.pa = torch.tensor([[p.index(c) for c in range(3)] for p in permutations(range(3))],
                              dtype=torch.long, device=device)

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
            total_score += (labels == base_labels).sum(dim=1).to(torch.float) - 1
        return total_score

    def solve(self, num_chains=1024, max_iter=200000, T_init=3.0, T_min=0.001):
        sigma = torch.randint(0, 6, (num_chains, self.n), device=self.device)
        cs = self._sa_score_gpu(sigma); bs = cs.clone(); best_sigmas = sigma.clone()
        T = T_init; cool = (T_min / T_init)**(1.0 / max_iter)
        for i in range(max_iter):
            if (bs == 0).any(): break
            old_sigma = sigma.clone(); v = torch.randint(0, self.n, (num_chains,), device=self.device)
            sigma[torch.arange(num_chains), v] = torch.randint(0, 6, (num_chains,), device=self.device)
            ns = self._sa_score_gpu(sigma); delta = ns - cs
            accept = (delta <= 0) | (torch.rand(num_chains, device=self.device) < torch.exp(-delta / T))
            sigma[~accept] = old_sigma[~accept]; cs[accept] = ns[accept]
            mask = cs < bs; bs[mask] = cs[mask]; best_sigmas[mask] = sigma[mask]
            T *= cool
        idx = bs.argmin().item(); return best_sigmas[idx], bs[idx].item()
