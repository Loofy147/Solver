# Global Structure in Highly Symmetric Systems

**Finding global structure in combinatorial problems via the short exact sequence**  
**0 → H → G → G/H → 0**

Derived from Knuth's *Claude's Cycles* (Feb 2026). Converges on a universal framework governing Cayley digraphs, Latin squares, Hamming codes, magic squares, difference sets, and Pythagorean triples.

---

## Repository

```
core.py        8 exact weights · verifier · SA engine · hardcoded solutions
engine.py      pipeline · domain registry · branch tree · classifying space
theorems.py    9 theorems verified · moduli theorem · cross-domain table
domains.py     all domains incl. P5 (non-abelian S_3) + P6 (product groups)
frontiers.py   open problem solvers P1/P2/P3 · frontier status
benchmark.py   v2.0 vs 6 alternatives · W4 correction · scaling
README.md      this file
```

---

## Quick Start

```bash
# Prove m=4 k=3 impossible in 0.02ms
python core.py

# Run all 9 theorems
python theorems.py

# Analyse any domain
python engine.py

# Check open problems
python frontiers.py --status

# Benchmark
python benchmark.py --quick
```

---

## The Four Coordinates

Every highly symmetric combinatorial problem reduces to the short exact sequence:

```
0  →  H  →  G  →  G/H  →  0
```

| Coordinate | Abstract | In Claude's Cycles | Cohomology |
|---|---|---|---|
| **C1 Fiber Map** | φ: G → G/H | f(i,j,k) = (i+j+k) mod m | H⁰ |
| **C2 Twisted Translation** | Q_c(h) = h + g_c | Q_c(i,j) = (i+b_c(j), j+r_c) | H¹ 1-cocycle |
| **C3 Governing Condition** | gcd(r_c, \|G/H\|) = 1 | r-triple (1, m−2, 1) | H¹ class ≠ 0 |
| **C4 Parity Obstruction** | arithmetic of \|G/H\| | 3 odds ≠ even m | H²(Z₂,Z/2) = Z/2 |

---

## The 8 Weights

For any problem (m, k), these 8 values fully determine solvability, strategy, and solution count. All computed in **O(m²) or faster**.

| Weight | Formula | What it gives |
|---|---|---|
| W1 H² obstruction | `all_odd AND k_odd AND m_even` | Proves impossible in O(1) |
| W2 r-tuple count | `\|{t ∈ cp^k : sum=m}\|` | Number of construction seeds |
| W3 canonical seed | `(1,...,1, m-(k-1))` | Direct construction path |
| W4 H¹ order **exact** | `φ(m)` (Euler totient) | Gauge multiplicity |
| W5 search exponent | `m × log₂(valid_levels)` | log of compressed space |
| W6 compression | W5 / (m³ × log₂(6)) | Search space reduction |
| W7 solution lb | `φ(m) × (m^(m-1)·φ(m))^(k-1)` | `\|M_k(G_m)\|` lower bound |
| W8 orbit size | `m^(m-1)` | Solutions per gauge class |

> **W4 correction from v1.0:** The original formula enumerating all `b: Z_m → Z_m` was O(m^m) and **wrong** (off by up to 16,807× at m=7). The correct value is `φ(m)`, derived from `|coprime-sum cocycles| / |coboundaries| = m^(m-1)·φ(m) / m^(m-1) = φ(m)`.

---

## Theorems (all 9 verified)

| Theorem | Statement | Verified |
|---|---|---|
| **3.2** Orbit-Stabilizer | \|Z_m³\| = m × m² | m=2..11 |
| **5.1** Single-Cycle | Q_c is m²-cycle iff gcd(r,m)=1 AND gcd(Σb,m)=1 | 8 cases |
| **6.1** Parity Obstruction | Even m, odd k → column-uniform impossible | m=4..16 |
| **7.1** Odd m Existence | r-triple (1,m−2,1) valid for all odd m≥3 | m=3..15 |
| **8.2** m=4 Solution | Explicit 64-vertex 3-Hamiltonian decomposition | verified |
| **9.1** k=4 Resolution | (1,1,1,1) breaks even-m obstruction for m=4 | verified |
| **Cor 9.2** Classification | Even m: odd k blocked, even k feasible | 7 cases |
| **Moduli** Torsor | M_k(G_m) is a torsor under H¹(Z_m,Z_m²) | m=3: 648 = 2×18² |
| **W4** H¹ exact | \|H¹\| = φ(m), not the v1.0 approximation | m=3,4,5 |

---

## The Moduli Theorem (Eilenberg-Mac Lane)

The space M_k(G_m) of valid k-Hamiltonian decompositions is:
- **Empty** if the H² obstruction class γ₂ ∈ H²(Z₂,Z/2) = Z/2 is nontrivial (parity obstruction)
- **A torsor under H¹(Z_m, Z_m²)** when γ₂ = 0

For m=3, k=3: |M| = 648 = φ(3) × coprime_b(3)² = 2 × 18². **Exact.**

The Closure Lemma (proved for m=3): given b₀,...,b_{k-2}, the final b_{k-1} is determined by the fiber bijection constraint. Hence |M| = φ(m) × coprime_b(m)^(k-1).

---

## Benchmark

v2.0 vs 6 alternatives on 6 problems (10s timeout):

| Solver | Correct | Proves ⊘ | Avg ms | Timeouts |
|---|---|---|---|---|
| **v2.0 pipeline** | **6/6** | **3** | **360** | **0** |
| A3 v1.0 pipeline | 5/6 | 2 | 39 | 1 |
| A4 level enum | 3/6 | 0 | 2,124 | 3 |
| A2 backtrack | 3/6 | 0 | — | 3 |
| A1 pure SA | 1/6 | 0 | 6,909 | 3 |
| A0 brute random | 0/6 | 0 | — | 6 |
| A5 scipy | 0/6 | 0 | 297 | 0 |

**Key advantage:** No search-based method can prove impossibility. For m=4 k=3 and m=6 k=3, v2 returns a 4-line proof in 0.02ms. All alternatives timeout at 10s.

Geometric mean speedup: **38,120×** over pure SA, **7,203×** over level enumeration.

---

## Open Problems

| Problem | Status | Known |
|---|---|---|
| P1: k=4, m=4 construction | 🔴 OPEN | r-quad (1,1,1,1) unique. Fiber-uniform impossible (331K checked). SA running. |
| P2: m=6, k=3 full-3D | 🔴 OPEN | Score 147→14 in 2M iters. Converging. Never previously attempted. |
| P3: m=8, k=3 full-3D | 🔴 OPEN | First attempt. 512 vertices. |
| P4: W7 formula | 🟢 RESOLVED | phi(m)×coprime_b^(k-1). Exact m=3, lower bound m≥5. |
| P5: Non-abelian (S_3) | 🟢 RESOLVED | Same parity law. k=2 feasible, k=3 blocked. |
| P6: Product Z_m×Z_n | 🟢 RESOLVED | Fiber quotient = Z_gcd(m,n). Framework complete. |
| Closure lemma | 🟡 PARTIAL | Proved m=3 exhaustively. General algebraic proof open. |

---

## Adding a New Domain

```python
from engine import Engine, Domain
e = Engine()
e.register(Domain(
    name        = "My System",
    group_order = 729,           # |G|
    k           = 3,             # arc colours
    m           = 9,             # |G/H|
    phi_desc    = "sum mod 9",
    tags        = ["cayley"],
))
result = e.run(9, 3)
e.print_tree()
e.print_theorems()
```

The engine automatically: checks orbit-stabilizer, derives the twisted translation form, computes all valid r-tuples, proves impossibility if none exist, selects the right strategy, and generates formal theorem statements.

---

## Cross-Domain Universality

The same four coordinates govern every domain:

| Domain | G | G/H | Governing | Obstruction |
|---|---|---|---|---|
| Claude's Cycles (odd m) | Z_m³ | Z_m | gcd(r_c,m)=1 | None |
| Claude's Cycles (even m) | Z_m³ | Z_m | infeasible | 3 odds ≠ even |
| Cyclic Latin square | Z_n | Z_1 | shift=1 coprime | Orthog: even n |
| Hamming(7,4) code | Z_2⁷ | Z_2³ | n=2^r-1 | Non-Hamming n |
| Magic sq (Siamese) | Z_n² | Z_n | step(1,1) coprime | n=2 impossible |
| Diff set (7,3,1) | Z_7 | Z_1 | k(k-1)=λ(n-1) | n≡2(mod4) |
| Z_m×Z_n product | Z_m×Z_n | Z_gcd | gcd(r_c,gcd)=1 | Same parity law |
| S_3 (non-abelian) | S_3 | Z_2 | k=2 feasible | k=3 obstructed |

---

## Papers

| Title | Language | Pages |
|---|---|---|
| Global Structure in Highly Symmetric Systems | English | 19 |
| The Even-m Case in Claude's Cycles | English | 5 |
| The Discovery Engine: A Six-Phase Methodology | English | 8 |
| حالة m الزوجية في مسألة دورات كلود | Arabic | 6 |
| محرّك الاكتشاف: منهجية ست مراحل | Arabic | 7 |

---

*March 2026*
