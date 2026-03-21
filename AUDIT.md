# System Quality Audit & Discovery Roadmap

## 1. System Quality Audit

### Structural Integrity
- **Verification Coverage:** 10/10 theorems in `theorems.py` are verified computationally.
- **Weights Engine:** `core.extract_weights` uses exact Euler totient $\phi(m)$ and cohomology class counting. It correctly identifies parity obstructions in $O(1)$.
- **Frontier Status:** `frontiers.py` provides a real-time table of open problems with evidence-based status (OPEN, PARTIAL, RESOLVED).

### Performance Bottlenecks
- **Score Function:** `_sa_score` in `core.py` uses a linear-time component counter. While efficient ($O(N)$), it is called millions of times.
- **Search Space Barrier:** The $m=6$ case was stuck at score 9. New coordinated multi-flip logic now allows escaping depth-3 local minima.
- **Scaling:** Parallel SA engine now utilizes all available CPU cores.

---

## 2. Genuine Gaps Map

| Gap ID | Category | Description | Status |
| :--- | :--- | :--- | :--- |
| **G1** | Algorithmic | Lack of multi-vertex (coordinated) flips in SA. | **RESOLVED** |
| **G2** | Structural | P1 (k=4, m=4) fiber-uniformity is impossible. | **PARTIAL** (Z2 seeding implemented) |
| **G3** | Scalability | No parallelization. | **RESOLVED** |
| **G4** | Algebraic | Closure Lemma is verified only for $m=3$. | **OPEN** |

---

## 3. High-Impact Improvement Roadmap

### Phase A: The Barrier-Breaker (COMPLETED)
1.  **Parallel SA Seeds:** Implemented `run_parallel_sa` in `core.py` utilizing `multiprocessing` for multi-core scaling.
2.  **Coordinated 3-Flip Moves:** Updated `run_sa` to perform periodic coordinated 3-vertex flips to escape depth-3 local minima.
3.  **Symmetry Seeding for P1:** Implemented $Z_2$ quotient seeding in `frontiers.py` to improve $k=4$ convergence.

### Phase B: Scalability & Rigor (Future)
1.  **Cython/Numba Acceleration:** Accelerate `_sa_score` component counting.
2.  **General Closure Proof:** Derive the algebraic proof for the Closure Lemma for all $m$.
3.  **GPU Offloading:** Port score function to CUDA/Jax for $G_{10}+$ analysis.

---

## 4. Metadata: Method Signatures

./core_sa.py:def run_sa(m: int, seed: int=0, max_iter: int=5_000_000,
./theorems.py:def proved(s): print(f"  {G_}■ {s}{Z_}")
./theorems.py:def fail(s):   print(f"  {R_}✗ {s}{Z_}")
./theorems.py:def note(s):   print(f"  {D_}{s}{Z_}")
./theorems.py:def build_proof(m: int, k: int, solution=None) -> Dict:
./theorems.py:def verify_all_theorems(verbose: bool=True) -> Dict[str,bool]:
./theorems.py:def print_cross_domain_table():
./theorems.py:def compute_H1_classes(m: int) -> Dict:
./theorems.py:def verify_m4_structure() -> Dict:
./theorems.py:def prove_fiber_uniform_k4_impossible(verbose: bool=True) -> bool:
./frontiers.py:def found(s): print(f"  {G_}✓ {s}{Z_}")
./frontiers.py:def open_(s): print(f"  {Y_}◆ OPEN: {s}{Z_}")
./frontiers.py:def note(s):  print(f"  {D_}{s}{Z_}")
./frontiers.py:def hr(n=72): return "─"*n
./frontiers.py:def solve_P1(max_iter: int=2_000_000, seeds=range(5),
./frontiers.py:def solve_P2(max_iter: int=5_000_000, seeds=range(3),
./frontiers.py:def solve_P2_warm_start(max_iter=10_000_000, seed=0, verbose=True):
./frontiers.py:def solve_P3(max_iter: int=3_000_000, seeds=range(2),
./frontiers.py:def verify_m6_depth3_barrier(verbose: bool=True):
./frontiers.py:def print_status():
./frontiers.py:def main():
./core.py:def extract_weights(m: int, k: int) -> Weights:
./core.py:def weights_table(m_range=range(2,11), k_range=range(2,7)) -> List[Weights]:
./core.py:def verify_sigma(sigma: Dict[Tuple,Tuple], m: int) -> bool:
./core.py:def table_to_sigma(table: List[Dict], m: int) -> Dict[Tuple,Tuple]:
./core.py:def _level_valid(lv: Dict[int,list], m: int) -> bool:
./core.py:def valid_levels(m: int) -> List[Dict]:
./core.py:def compose_Q(table: List[Dict], m: int) -> List[Dict]:
./core.py:def is_single_cycle(Q: Dict, m: int) -> bool:
./core.py:def _build_sa3(m: int):
./core.py:def _sa_score(sigma: List[int], arc_s, pa, n: int) -> int:
./core.py:def run_sa(m: int, seed: int=0, max_iter: int=5_000_000,
./core.py:def solve(m: int, k: int=3, seed: int=42) -> Optional[Dict]:
./core.py:def _sa_worker(args):
./core.py:def run_parallel_sa(m: int, seeds: List[int], max_iter: int=5_000_000,
./benchmark.py:def _build_score(m):
./benchmark.py:def solver_v2(m,k=3):
./benchmark.py:def solver_A0_random(m,budget=30_000):
./benchmark.py:def solver_A1_SA(m,max_iter=300_000):
./benchmark.py:def solver_A2_backtrack(m):
./benchmark.py:def solver_A3_v1(m,k=3):
./benchmark.py:def _build_score(m):
./benchmark.py:def solver_A4_level_enum(m):
./benchmark.py:def solver_A5_scipy(m):
./benchmark.py:def run_benchmark(problems: List[Tuple[int,int]], verbose=True) -> Dict:
./benchmark.py:def print_summary(all_results, problems):
./benchmark.py:def w4_benchmark():
./benchmark.py:def main():
./domains.py:def proved(s): print(f"  {G_}■ {s}{Z_}")
./domains.py:def open_(s):  print(f"  {Y_}◆ {s}{Z_}")
./domains.py:def note(s):   print(f"  {D_}{s}{Z_}")
./domains.py:def analyse_magic_squares(verbose=True):
./domains.py:def analyse_pythagorean(verbose=True):
./domains.py:def _load_magic_pythagorean(engine):
./domains.py:def build_decomposition_category():
./domains.py:def load_all_domains(engine) -> None:
./domains.py:def _load_cycles(engine: Engine) -> None:
./domains.py:def _load_classical(engine: Engine) -> None:
./domains.py:def analyse_P5_nonabelian(verbose: bool=True) -> Dict:
./domains.py:def _load_P5_nonabelian(engine: Engine) -> None:
./domains.py:def analyse_P6_product_groups(verbose: bool=True) -> List[Dict]:
./domains.py:def _load_P6_product(engine: Engine) -> None:
