"""
engine.py — The Global Structure Engine
=========================================
Pipeline · DomainRegistry · BranchTree · ClassifyingSpace
"""

from __future__ import annotations
import time
import re
import math
from math import gcd
from itertools import product as iprod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from src.core import extract_weights, Weights, verify_sigma, solve, PRECOMPUTED

G_="\033[92m"; R_="\033[91m"; Y_="\033[93m"; B_="\033[94m"
C_="\033[96m"; W_="\033[97m"; D_="\033[2m"; Z_="\033[0m"

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
    Status.PROVED_IMPOSSIBLE: "✘ PROVED IMPOSSIBLE",
    Status.OPEN_PROMISING:    "◆ OPEN PROMISING",
    Status.OPEN_UNKNOWN:      "◇ OPEN UNKNOWN",
}

# ── domain ────────────────────────────────────────────────────────────────────
@dataclass
class Domain:
    name:        str
    group_order: int
    k:           int
    m:           int            # |G/H|, the fiber quotient modulus
    phi_desc:    str            # description of the fiber map φ
    G:           str            = 'Z_m^3'
    H:           str            = 'Z_m^2'
    X:           str            = 'G/H'
    tags:        List[str]      = field(default_factory=list)
    precomputed: Any            = None   # solution if known
    notes:       str            = ''

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
    status:   Status = Status.OPEN_UNKNOWN
    proof:    Dict   = field(default_factory=dict)
    elapsed:  float  = 0.0
    instance_solution: Any = None

    def summary(self) -> str:
        col = _STATUS_COL[self.status]
        return f"Domain {W_}{self.domain}{Z_}: {col}{_STATUS_SYM[self.status]}{Z_} ({self.elapsed*1000:.1f}ms)"

    def one_line(self) -> str:
        col = _STATUS_COL[self.status]
        sym = "✓" if self.status == Status.PROVED_POSSIBLE else ("✗" if self.status == Status.PROVED_IMPOSSIBLE else "?")
        return f"{col}{sym} {W_}{self.domain:<20}{Z_} m={self.m:<2} k={self.k:<2} {self.weights.summary()}"

class BranchTree:
    def __init__(self): self.nodes: List[Result] = []
    def add(self, r: Result): self.nodes.append(r)
    def by_status(self, s: Status) -> List[Result]: return [n for n in self.nodes if n.status == s]
    def print(self):
        for r in self.nodes: print(f"  {r.one_line()}")

class ClassifyingSpace:
    def __init__(self, m_max=12, k_max=6):
        self.m_max = m_max; self.k_max = k_max
    def obstruction_grid(self) -> str:
        out = f"   {' '.join(f'{k:2}' for k in range(2, self.k_max+1))}\n"
        for m in range(2, self.m_max+1):
            row = f"{m:2} "
            for k in range(2, self.k_max+1):
                w = extract_weights(m, k)
                if w.h2_blocks: row += f"{R_} ✗{Z_}"
                elif w.r_count > 0: row += f"{G_} ✓{Z_}"
                else: row += f"{Y_} ?{Z_}"
            out += row + "\n"
        return out
    def compression_grid(self, m_max, k_max) -> str:
        out = f"   {' '.join(f'{k:2}' for k in range(2, k_max+1))}\n"
        for m in range(2, m_max+1):
            row = f"{m:2} "
            for k in range(2, k_max+1):
                w = extract_weights(m, k)
                c = w.compression
                col = G_ if c > 0.9 else (Y_ if c > 0.5 else R_)
                row += f"{col} {int(c*10):1}{Z_}"
            out += row + "\n"
        return out
    def summary(self) -> Dict:
        feasible, obstructed, unknown = 0, 0, 0
        for m in range(2, self.m_max+1):
            for k in range(2, self.k_max+1):
                w = extract_weights(m, k)
                if w.h2_blocks: obstructed += 1
                elif w.r_count > 0: feasible += 1
                else: unknown += 1
        return {"feasible": feasible, "obstructed": obstructed, "unknown": unknown}
    def richest(self, top=8) -> List:
        data = []
        for m in range(2, 20):
            for k in range(2, 6):
                w = extract_weights(m, k)
                data.append((m, k, w.r_count))
        return sorted(data, key=lambda x: x[2], reverse=True)[:top]

class ProofBuilder:
    def build(self, w: Weights, sol: Any) -> Dict:
        if w.h2_blocks:
            return {"theorem": "Parity Law Obstruction", "proof": [f"m={w.m} is even", f"k={w.k} is odd", "H² cohomology class is non-trivial"]}
        if sol:
            return {"theorem": "Existence Law", "proof": [f"r-count {w.r_count} > 0", "Explicit construction verified"]}
        return {"theorem": "Status Unknown", "proof": ["No parity obstruction found", "Search depth insufficient"]}

class DomainParser:
    def parse(self, desc: Dict) -> Domain:
        name = desc.get('name', 'Anonymous Domain')
        G_str = desc.get('group', 'Z_m^3'); H_str = desc.get('subgroup', 'Z_m^2')
        X_str = desc.get('set', 'G/H'); k = desc.get('k', 3); m = desc.get('m')
        if m is None:
            try:
                g_val = int(re.search(r'\d+', G_str).group())
                h_val = int(re.search(r'\d+', H_str).group()) if 'Z' in H_str else 1
                m = g_val // h_val
            except: m = 5
        return Domain(name, 0, k, m, f"SES {G_str} -> {X_str}")

def inject_domain(desc: Dict) -> Domain: return DomainParser().parse(desc)

class Engine:
    def __init__(self):
        self.registry = DomainRegistry(); self.tree = BranchTree()
        self.pb = ProofBuilder(); self._cache: Dict[Tuple,Result] = {}
        self._load_defaults()

    def classify_latex(self, text: str) -> List[str]:
        tags = []
        if "tournament" in text.lower(): tags.append("combinatorics")
        if "triangle" in text.lower() or "circle" in text.lower(): tags.append("geometry")
        if "f(m) + f(n)" in text: tags.append("algebra")
        return tags

    def register(self, d: Domain) -> "Engine":
        self.registry.register(d); return self

    def run(self, m: int, k: int=3, verbose: bool=False, instance_data: Any=None) -> Result:
        key = (m,k)
        if key in self._cache: return self._cache[key]
        t0 = time.perf_counter(); w = extract_weights(m, k)
        sol = None
        if not w.h2_blocks:
            pre = PRECOMPUTED.get((m,k))
            if pre is not None: sol = pre
            elif w.r_count > 0: sol = solve(m, k)
        verified = bool(sol and isinstance(sol,dict) and verify_sigma(sol,m))
        if not verified: sol = None
        proof = self.pb.build(w, sol if verified else None)
        status = (Status.PROVED_POSSIBLE if verified else Status.PROVED_IMPOSSIBLE if w.h2_blocks else Status.OPEN_PROMISING)
        r = Result(domain=f"({m},{k})", m=m, k=k, weights=w, solution=sol, status=status, proof=proof, elapsed=time.perf_counter()-t0)
        self._cache[key] = r; self.tree.add(r); return r

    def analyse(self, name: str, verbose: bool=False) -> Result:
        d = self.registry.get(name)
        if d is None: raise KeyError(f"Unknown domain: {name}")
        r = self.run(d.m, d.k, verbose); r.domain = name; return r

    def print_tree(self) -> None:
        print(f"\n{'═'*72}\n{W_}BRANCH TREE — Knowledge State{Z_}\n{'─'*72}")
        self.tree.print()
    def print_space(self, m_max=14, k_max=8) -> None:
        sp = ClassifyingSpace(m_max, k_max)
        print(f"\n{'═'*72}\n{W_}CLASSIFYING SPACE{Z_}\n{'─'*72}")
        print(sp.obstruction_grid())
    def print_universality(self) -> None:
        from src.universality import UniversalityChecker
        UniversalityChecker(self.registry).print_table()

    def print_theorems(self) -> None:
        print(f"\n{'═'*72}\n{W_}GENERATED THEOREMS{Z_}\n{'─'*72}")
        n=1
        for r in self._cache.values():
            if "theorem" in r.proof:
                print(f"  {B_}Theorem {n}.{Z_} {r.proof['theorem']}")
                for step in r.proof.get("proof", []): print(f"    {step}")
                n+=1

    def _load_defaults(self):
        # Multi-domain catalog
        self.registry.register(Domain("G-CNN Equivariance", 72, 3, 6, "rotation orbit", tags=["ai", "equivariance"], G="D_36", H="C_6", X="Z_6"))
        self.registry.register(Domain("State Space Reduction", 500, 4, 10, "symmetry quotient", tags=["rl", "robotics"], G="Z_500", H="Z_50", X="Z_10"))
        self.registry.register(Domain("Discrete Log Hardness", 1024, 2, 2, "parity map", tags=["crypto", "hardness"], G="Z_1024", H="Z_512", X="Z_2"))
        self.registry.register(Domain("Lattice Gauge Theory", 64, 3, 4, "gauge orbit", tags=["physics", "lattice"], G="Z_4^3", H="Z_4^2", X="Z_4"))
        self.registry.register(Domain("Chordal Symmetries", 12, 3, 12, "transposition", tags=["music", "orbits"], G="Z_12", H="0", X="Z_12"))
        for m,sol,tags in [(3,PRECOMPUTED.get((3,3)),["cycles","odd"]),(4,None,["cycles","even","sa"]),(5,PRECOMPUTED.get((5,3)),["cycles","odd"])]:
            self.registry.register(Domain(f"Cycles m={m} k=3", m**3, 3, m, f"sum mod {m}", tags=tags, precomputed=sol))
        self.registry.register(Domain("Cycles m=4 k=4 [OPEN]", 64, 4, 4, "(i+j+k) mod 4", tags=["cycles","even","k4"], notes="r-quad (1,1,1,1)."))
        self.registry.register(Domain("Hamming(7,4)", 128, 8, 2, "parity-check", tags=["coding","perfect"]))
        self.registry.register(Domain("Latin Square n=5", 5, 1, 5, "identity", tags=["latin"]))

if __name__ == "__main__":
    e = Engine(); e.run(3,3); e.run(4,3); e.print_tree(); e.print_theorems()
