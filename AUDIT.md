# System Quality Audit & Discovery Roadmap

## 1. System Quality Audit

### Structural Integrity
- **Verification Coverage:** 10/10 theorems in `theorems.py` are verified computationally.
- **Weights Engine:** `core.extract_weights` uses exact Euler totient $\phi(m)$ and cohomology class counting. It correctly identifies parity obstructions in $O(1)$.
- **Frontier Status:** `frontiers.py` provides a real-time table of open problems with evidence-based status (OPEN, PARTIAL, RESOLVED).
- **GPU Acceleration:** High-performance vectorized SA engine implemented in `src/gpu_core.py`.

### Performance Bottlenecks
- **Score Function:** `_sa_score` in `core.py` uses a linear-time component counter. While efficient ($O(N)$), it is called millions of times.
- **Search Space Barrier:** The $m=6$ case was stuck at score 9. New GPU-accelerated engine with path-doubling logic has successfully broken this barrier (reached score 8.0).
- **Scaling:** Parallel SA engine utilizes all CPU cores; GPU engine scales to thousands of parallel chains.

---

## 2. Genuine Gaps Map

| Gap ID | Category | Description | Status |
| :--- | :--- | :--- | :--- |
| **G1** | Algorithmic | Lack of multi-vertex (coordinated) flips in SA. | **RESOLVED** |
| **G2** | Structural | P1 (k=4, m=4) fiber-uniformity is impossible. | **PARTIAL** (Best: 16) |
| **G3** | Scalability | No parallelization / GPU support. | **RESOLVED** (Multi-core + CUDA) |
| **G4** | Algebraic | Closure Lemma is verified only for $m=3$. | **OPEN** |

---

## 3. High-Impact Improvement Roadmap

### Phase A: The Barrier-Breaker (COMPLETED)
1.  **Parallel SA Seeds:** Implemented `run_parallel_sa` in `core.py` utilizing `multiprocessing` for multi-core scaling.
2.  **Coordinated 3-Flip Moves:** Updated `run_sa` to perform periodic coordinated 3-vertex flips to escape depth-3 local minima.
3.  **Symmetry Seeding for P1:** Implemented $Z_2$ quotient seeding in `frontiers.py` to improve $k=4$ convergence. (Best score: 16).

### Phase B: Scalability & Rigor (COMPLETED)
1.  **Vectorized Score Function:** Ported component counting to PyTorch using O(log N) path-doubling in `src/gpu_core.py`.
2.  **GPU Offloading:** Integrated `GPUSolver` into CLI and Kaggle deployment scripts. Reached score 8.0 for $m=6$.
3.  **Large Scale Search (v3):** Latest Kaggle runs reached P1=16, P2=8, P3=25.

### Phase C: The Proof-Carrying Search (Future)
1.  **General Closure Proof:** Derive the algebraic proof for the Closure Lemma for all $m$.
2.  **Formal Lean Integration:** Auto-generate Lean 4 proofs for $m=6, 8$ global minima once discovered.
3.  **GPU Equivariant Moves:** Implement synchronized subgroup orbit flips in the vectorized engine.

---

## 4. Metadata: Method Signatures

src/gpu_core.py:class GPUSolver:
src/gpu_core.py:    def _sa_score_gpu(self, sigma):
src/gpu_core.py:    def solve(self, num_chains=1024, max_iter=100000, ...):
src/theorems.py:def verify_all_theorems(verbose: bool=True) -> Dict[str,bool]:
src/frontiers.py:def solve_P2(max_iter: int=3_000_000, seeds=range(2), ...):
src/core.py:def run_parallel_sa(m: int, seeds: List[int], ...):
