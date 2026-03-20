"""
engine.py — The Global Structure Engine
=========================================
Pipeline · DomainRegistry · BranchTree · ClassifyingSpace

Usage:
    from engine import Engine
    e = Engine()
    result = e.run(m=5, k=3)
    e.print_tree()
    e.print_space()

Adding a new domain:
    from engine import Engine, Domain
    e = Engine()
    e.register(Domain("My System", group_order=729, k=3, m=9,
                       phi_desc="sum mod 9"))
    e.analyse("My System")
"""

from __future__ import annotations
import time
from math import gcd
from itertools import product as iprod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from core import extract_weights, Weights, verify_sigma, solve, PRECOMPUTED

G_="\033[92m";R_="\033[91m";Y_="\033[93m";B_="\033[94m"
C_="\033[96m";W_="\033[97m";D_="\033[2m";Z_="\033[0m"


# ── status ────────────────────────────────────────────────────────────────────
class Status(Enum):
    PROVED_POSSIBLE   = auto()
    PROVED_IMPOSSIBLE = auto()
    OPEN_PROMISING    = auto()
    OPEN_UNKNOWN      = auto()

_STATUS_COL = {
    Status.PROVED_POSSIBLE:   G_,
    Status.PROVED_IMPOSSIBLE: R_,
    Status.OPEN_PROMISING:    Y_,
    Status.OPEN_UNKNOWN:      D_,
}
_STATUS_SYM = {
    Status.PROVED_POSSIBLE:   "■ PROVED POSSIBLE",
    Status.PROVED_IMPOSSIBLE: "■ PROVED IMPOSSIBLE",
    Status.OPEN_PROMISING:    "◆ OPEN (promising)",
    Status.OPEN_UNKNOWN:      "○ OPEN (unknown)",
}


# ══════════════════════════════════════════════════════════════════════════════
# DOMAIN REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Domain:
    name:        str
    group_order: int
    k:           int
    m:           int            # |G/H|, the fiber quotient modulus
    phi_desc:    str            # description of the fiber map φ
    tags:        List[str]      = field(default_factory=list)
    precomputed: Any            = None   # solution if known
    notes:       str            = ""


class DomainRegistry:
    def __init__(self): self._d: Dict[str,Domain] = {}
    def register(self, d: Domain) -> None: self._d[d.name] = d
    def get(self, name: str) -> Optional[Domain]: return self._d.get(name)
    def all(self) -> List[Domain]: return list(self._d.values())
    def by_tag(self, tag: str) -> List[Domain]:
        return [d for d in self._d.values() if tag in d.tags]
    def __len__(self): return len(self._d)


# ══════════════════════════════════════════════════════════════════════════════
# RESULT + BRANCH TREE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Result:
    domain:   str
    m:        int
    k:        int
    weights:  Weights
    solution: Any
    status:   Status
    proof:    Dict
    elapsed:  float

    def one_line(self) -> str:
        col = _STATUS_COL[self.status]
        sym = _STATUS_SYM[self.status]
        return (f"({self.m},{self.k}) {col}{sym:<22}{Z_} "
                f"W4={self.weights.h1_exact} W6={self.weights.compression:.4f} "
                f"{self.elapsed*1000:.1f}ms")


@dataclass
class BranchNode:
    domain:   str
    question: str
    status:   Status
    evidence: str
    children: List[BranchNode] = field(default_factory=list)


class BranchTree:
    def __init__(self): self._roots: List[BranchNode] = []

    def add(self, result: Result) -> None:
        root = BranchNode(
            domain=result.domain,
            question=f"Does a k={result.k}-Hamiltonian decomposition exist for {result.domain}?",
            status=result.status,
            evidence=result.proof.get("theorem",""),
        )
        for c_label, c_evidence in [
            (f"C1 Fiber Map", f"|G|={result.m**3}={result.m}×{result.m**2}"),
            (f"C2 Twisted Translation", f"Q_c(i,j)=(i+b_c(j),j+r_c)"),
            (f"C3 Governing Condition", f"W3={result.weights.canonical}"),
            (f"C4 Parity Obstruction", f"W1={result.weights.h2_blocks}"),
        ]:
            root.children.append(BranchNode(result.domain, c_label, result.status, c_evidence))
        self._roots.append(root)

    def print(self, indent: int=0, nodes: Optional[List]=None) -> None:
        if nodes is None: nodes = self._roots
        for node in nodes:
            pad = "  "*indent
            col = _STATUS_COL[node.status]
            print(f"{pad}{col}{_STATUS_SYM[node.status]}{Z_}  {W_}{node.domain}{Z_}")
            print(f"{pad}    {D_}Q: {node.question[:70]}{Z_}")
            print(f"{pad}    {D_}E: {node.evidence[:70]}{Z_}")
            if node.children: self.print(indent+1, node.children)

    def by_status(self, s: Status) -> List[BranchNode]:
        out = []
        def collect(nodes):
            for n in nodes:
                if n.status==s: out.append(n)
                collect(n.children)
        collect(self._roots); return out


# ══════════════════════════════════════════════════════════════════════════════
# PROOF BUILDER
# ══════════════════════════════════════════════════════════════════════════════

class ProofBuilder:
    def build(self, w: Weights, solution: Any=None) -> Dict:
        if w.h2_blocks:
            return {
                "theorem": f"No column-uniform σ for G_{w.m} (k={w.k}).",
                "proof": [
                    f"(1) Need r₀+…+r_{{k-1}}={w.m}, each gcd(rᵢ,{w.m})=1.",
                    f"(2) Coprime-to-{w.m}={list(w.coprime_elems)} — all odd.",
                    f"(3) Sum of k={w.k} odds is odd ≠ m={w.m} (even). □",
                ],
                "corollary": "Holds for ALL even m, ALL odd k. γ₂∈H²(Z_2,Z/2)=Z/2 nontrivial.",
            }
        if solution is not None:
            return {
                "theorem": f"Valid k={w.k}-Hamiltonian decomp of G_{w.m} exists.",
                "proof": [
                    f"(1) r-tuple {w.canonical} valid. [W3]",
                    f"(2) b-functions found, gcd(Σbᵢ,{w.m})=1. [Thm 5.1]",
                    f"(3) σ verified: {w.m**3} arcs, in-degree 1, 1 component. □",
                ],
                "gauge":  f"|H¹|=phi({w.m})={w.h1_exact}. [W4]",
                "sol_lb": f"|M|≥{w.sol_lb:,}. [W7]",
            }
        return {
            "theorem": f"H² absent for m={w.m}, k={w.k}. Solution search required.",
            "proof":   [f"(1) r-tuple {w.canonical} valid.",
                        f"(2) Explicit σ: open."],
        }


# ══════════════════════════════════════════════════════════════════════════════
# CLASSIFYING SPACE
# ══════════════════════════════════════════════════════════════════════════════

class ClassifyingSpace:
    """The full (m,k) grid as a computable mathematical object."""

    def __init__(self, m_max: int=16, k_max: int=8):
        self.m_max=m_max; self.k_max=k_max
        self.grid = {(m,k): extract_weights(m,k)
                     for m in range(2,m_max+1) for k in range(2,k_max+1)}

    def obstruction_grid(self) -> str:
        lines=[f"  m\\k  "+"   ".join(f"k={k}" for k in range(2,self.k_max+1))]
        lines.append("  "+"─"*70)
        for m in range(2,self.m_max+1):
            row=f"  {m:>3}  "
            for k in range(2,self.k_max+1):
                w=self.grid[(m,k)]
                row+=f"  {R_}✗{Z_}" if w.h2_blocks else f"  {G_}✓{Z_}" if w.solvable else f"  {Y_}?{Z_}"
            lines.append(row)
        return "\n".join(lines)

    def compression_grid(self, m_max=12, k_max=7) -> str:
        lines=[f"  m\\k  "+"  ".join(f" k={k}" for k in range(2,min(k_max,self.k_max)+1))]
        lines.append("  "+"─"*65)
        for m in range(2,min(m_max,self.m_max)+1):
            row=f"  {m:>3}  "
            for k in range(2,min(k_max,self.k_max)+1):
                r=self.grid[(m,k)].compression
                col=G_ if r<0.05 else (Y_ if r<0.15 else "\033[91m")
                row+=f" {col}{r:.4f}{Z_}"
            lines.append(row)
        return "\n".join(lines)

    def summary(self) -> Dict:
        counts={"obstructed":0,"constructible":0,"frontier":0}
        for w in self.grid.values():
            if w.h2_blocks:   counts["obstructed"]    +=1
            elif w.solvable:  counts["constructible"] +=1
            else:             counts["frontier"]      +=1
        return counts

    def richest(self, n=8) -> List:
        return sorted([(m,k,w.r_count) for (m,k),w in self.grid.items()
                       if w.solvable], key=lambda x:-x[2])[:n]


# ══════════════════════════════════════════════════════════════════════════════
# THE ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class Engine:
    """
    The Global Structure Engine.

    e = Engine()          # loads all default domains
    e.run(5, 3)           # solve G_5 k=3
    e.analyse("Cycles m=5 k=3")  # by domain name
    e.print_tree()        # print knowledge state
    e.print_space()       # print classifying space
    e.print_theorems()    # print generated theorems
    e.register(Domain(...))  # add new domain
    """

    def __init__(self):
        self.registry = DomainRegistry()
        self.tree     = BranchTree()
        self.pb       = ProofBuilder()
        self._cache:  Dict[Tuple,Result] = {}
        self._load_defaults()

    # ── public API ─────────────────────────────────────────────────────────

    def register(self, d: Domain) -> "Engine":
        self.registry.register(d); return self

    def run(self, m: int, k: int=3, verbose: bool=False) -> Result:
        key = (m,k)
        if key in self._cache: return self._cache[key]
        t0 = time.perf_counter()
        w  = extract_weights(m, k)
        if verbose: print(f"  {D_}Weights: {w.summary()}{Z_}")

        sol = None
        if not w.h2_blocks:
            pre = PRECOMPUTED.get((m,k))
            if pre is not None:
                sol = pre
            elif w.r_count > 0:
                sol = solve(m, k)

        verified = bool(sol and isinstance(sol,dict) and verify_sigma(sol,m))
        if not verified: sol = None

        proof = self.pb.build(w, sol if verified else None)
        status = (Status.PROVED_POSSIBLE   if verified else
                  Status.PROVED_IMPOSSIBLE if w.h2_blocks else
                  Status.OPEN_PROMISING)

        r = Result(domain=f"({m},{k})", m=m, k=k, weights=w,
                   solution=sol, status=status, proof=proof,
                   elapsed=time.perf_counter()-t0)
        self._cache[key] = r
        self.tree.add(r)
        return r

    def analyse(self, name: str, verbose: bool=False) -> Result:
        d = self.registry.get(name)
        if d is None: raise KeyError(f"Unknown domain: {name}")
        r = self.run(d.m, d.k, verbose)
        r.domain = name; return r

    def batch(self, problems: List[Tuple[int,int]]) -> List[Result]:
        return [self.run(m,k) for m,k in problems]

    # ── output ─────────────────────────────────────────────────────────────

    def print_tree(self) -> None:
        print(f"\n{'═'*72}\n{W_}BRANCH TREE — Knowledge State{Z_}\n{'─'*72}")
        self.tree.print()
        print()
        for s in Status:
            nodes = self.tree.by_status(s)
            if nodes:
                col = _STATUS_COL[s]
                print(f"  {col}{s.name}: {len(nodes)}{Z_}")

    def print_space(self, m_max=14, k_max=8) -> None:
        sp = ClassifyingSpace(m_max, k_max)
        print(f"\n{'═'*72}\n{W_}CLASSIFYING SPACE m=2..{m_max}, k=2..{k_max}{Z_}\n{'─'*72}")
        print(f"\n{W_}Feasibility (✓=constructible, ✗=H²-blocked, ?=frontier):{Z_}")
        print(sp.obstruction_grid())
        print(f"\n{W_}Compression ratio W6:{Z_}")
        print(sp.compression_grid(m_max, k_max))
        counts=sp.summary(); total=sum(counts.values())
        print(f"\n{W_}Space ({total} problems):{Z_}")
        for name,(cnt) in counts.items():
            pct=100*cnt/total
            col=G_ if "const" in name else (R_ if "obstr" in name else Y_)
            print(f"  {col}{name:<16}{Z_}  {cnt:>4}  {pct:5.1f}%")
        print(f"\n{W_}8 Richest (most r-tuples):{Z_}")
        for m,k,cnt in sp.richest():
            w=extract_weights(m,k)
            print(f"  m={m} k={k}: {cnt} r-tuples, canon={w.canonical}")

    def print_theorems(self) -> None:
        print(f"\n{'═'*72}\n{W_}GENERATED THEOREMS{Z_}\n{'─'*72}")
        n=1
        for r in self._cache.values():
            if "theorem" in r.proof:
                print(f"\n  {B_}Theorem {n}.{Z_}  {r.proof['theorem']}")
                for step in r.proof.get("proof",[]): print(f"    {step}")
                if "corollary" in r.proof: print(f"    {D_}{r.proof['corollary']}{Z_}")
                n+=1

    def print_results(self) -> None:
        print(f"\n{'═'*72}\n{W_}RESULTS{Z_}\n{'─'*72}")
        for r in self._cache.values(): print(f"  {r.one_line()}")

    # ── default domains ────────────────────────────────────────────────────

    def _load_defaults(self):
        for m,sol,tags in [(3,PRECOMPUTED.get((3,3)),["cycles","odd"]),
                           (4,PRECOMPUTED.get((4,3)),["cycles","even","sa"]),
                           (5,PRECOMPUTED.get((5,3)),["cycles","odd"]),
                           (7,None,["cycles","odd"])]:
            self.registry.register(Domain(
                f"Cycles m={m} k=3", m**3, 3, m, f"(i+j+k) mod {m}",
                tags, sol, f"G_{m}"))
        self.registry.register(Domain(
            "Cycles m=4 k=4 [OPEN]", 64, 4, 4, "(i+j+k) mod 4",
            ["cycles","even","k4","frontier"],
            notes="r-quad (1,1,1,1). Fiber-uniform impossible (331K checked). Open."))
        self.registry.register(Domain(
            "Hamming(7,4)", 128, 8, 2, "parity-check Z_2^7→Z_2^3",
            ["coding","perfect"], notes="Perfect code: ball×|C|=128"))
        self.registry.register(Domain(
            "Latin Square n=5", 5, 1, 5, "identity",
            ["latin"], notes="Cyclic L[i][j]=(i+j)%n"))


if __name__ == "__main__":
    e = Engine()
    for m,k in [(3,3),(4,3),(4,4),(5,3),(7,3)]:
        r = e.run(m,k)
        print(f"  {r.one_line()}")
    e.print_tree()
    e.print_space(12,7)
