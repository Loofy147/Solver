"""
engine.py — The Global Structure Engine
=========================================
Pipeline · DomainRegistry · BranchTree · ClassifyingSpace

Usage:
    from src.engine import Engine
    e = Engine()
    result = e.run(m=5, k=3)
    e.print_tree()
    e.print_space()

Adding a new domain:
    from src.engine import Engine, Domain
    e = Engine()
    e.register(Domain("My System", group_order=729, k=3, m=9,
                       phi_desc="sum mod 9"))
    e.analyse("My System")
"""

from __future__ import annotations
import time
import re
from math import gcd
from itertools import product as iprod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from src.core import extract_weights, Weights, verify_sigma, solve, PRECOMPUTED

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
    status:   Status
    proof:    Dict
    elapsed:  float
    instance_solution: Any = None

    def one_line(self) -> str:
        col = _STATUS_COL[self.status]
        sym = _STATUS_SYM[self.status]
        return (f"({self.m},{self.k}) {col}{sym:<22}{Z_} "
                f"W4={self.weights.h1_exact} W6={self.weights.compression:.4f} {self.elapsed*1000:.1f}ms")


class BranchNode:
    def __init__(self, domain, status, question, evidence):
        self.domain   = domain
        self.status   = status
        self.question = question
        self.evidence = evidence
        self.children: List[BranchNode] = []

class BranchTree:
    def __init__(self):
        self._roots: List[BranchNode] = []

    def add(self, r: Result) -> None:
        # Simple tree: top level is the problem (m,k)
        node = BranchNode(r.domain, r.status, r.proof["theorem"], r.proof["proof"][0])
        self._roots.append(node)

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
# INVARIANT LEARNING REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

THEOREM_FINGERPRINTS = {
    "Parity Law": {"obstruction": "H2", "condition": "Even m, Odd k"},
    "Existence Law": {"obstruction": "None", "condition": "Odd m"},
    "Fiber-Uniform Obstruction": {"obstruction": "W9", "condition": "m=4, k=4"},
    "Product Law": {"obstruction": "None", "condition": "gcd(m,n)=1"},
    "Equivariance Law": {"obstruction": "None", "condition": "Group Action G on X"},
    "State Collapse": {"obstruction": "None", "condition": "X/G reduction"},
    "Algebraic Hardness": {"obstruction": "None", "condition": "Exp in Z_p^*"},
    "Stabilizer Principle": {"obstruction": "None", "condition": "Quantum Error Correction"},
}


class DomainParser:
    """Infers SES properties from a mathematical description."""
    def parse(self, desc: Dict) -> Domain:
        name = desc.get('name', 'Anonymous Domain')
        G_str = desc.get('group', 'Z_m^3')
        H_str = desc.get('subgroup', 'Z_m^2')
        X_str = desc.get('set', 'G/H')
        k = desc.get('k', 3)

        m = desc.get('m')
        if m is None:
            if G_str.startswith('Z_'):
                try:
                    match = re.search(r'\d+', G_str)
                    g_val = int(match.group()) if match else 5
                    if '/' in X_str or H_str.startswith('Z_'):
                        match_h = re.search(r'\d+', H_str)
                        h_val = int(match_h.group()) if match_h else 1
                        m = g_val // h_val
                    else:
                        m = g_val
                except: m = 5
            else: m = 5

        n = desc.get('n', m**3)
        phi = desc.get('action', f'projection {G_str} -> Z_{m}')

        tags = desc.get('tags', ['injected'])
        if 'Lie' in G_str or 'crystal' in name.lower():
            tags.append('advanced')

        return Domain(name=name, group_order=n, k=k, m=m, phi_desc=phi, G=G_str, H=H_str, X=X_str, tags=tags)


def inject_domain(desc: Dict) -> Domain:
    parser = DomainParser()
    return parser.parse(desc)


class Engine:
    def classify_latex(self, text: str) -> List[str]:
        """Identify system domains relevant to the LaTeX problem."""
        tags = []
        if "tournament" in text.lower(): tags.append("combinatorics")
        if "triangle" in text.lower() or "circle" in text.lower(): tags.append("geometry")
        if "divisor" in text.lower() or "sigma" in text.lower(): tags.append("number_theory")
        if "f(m) + f(n)" in text: tags.append("algebra")
        return tags

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

    def run(self, m: int, k: int=3, verbose: bool=False, instance_data: Any=None) -> Result:
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
        r.instance_solution = instance_data
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
        for r in self._cache.values():
            th = self.identify_theorem(r)
            th_str = f" [{G_}{' + '.join(th)}{Z_}]" if th else ""
            print(f"  {r.one_line()}{th_str}")

    def identify_theorem(self, r: Result) -> List[str]:
        """
        Given a result, identify which known theorems it instantiates.
        """
        matches = []
        w = r.weights
        if w.h2_blocks:
            matches.append("Parity Law")
        if w.h3_blocks:
            matches.append("Fiber-Uniform Obstruction")
        if not w.h2_blocks and not w.h3_blocks and w.m % 2 == 1:
            matches.append("Existence Law")

        # AI/RL Laws
        if any(tag in r.domain.lower() for tag in ['cnn', 'gnn', 'rotation']):
            matches.append("Equivariance Law")
        if 'robot' in r.domain.lower() or 'state' in r.domain.lower():
            matches.append("State Collapse")

        # Advanced Domain Laws
        if "Modular Exp" in r.domain:
            matches.append("Algebraic Hardness")
        if "quantum" in r.domain.lower():
            matches.append("Stabilizer Principle")
        return matches

    # ── default domains ────────────────────────────────────────────────────

    def _load_defaults(self):
        # AI / Machine Learning Domains
        self.registry.register(Domain(
            name="Rotational CNN", group_order=4, k=1, m=1, phi_desc="C4 rotation",
            tags=["ai", "equivariance"], G="C4", H="e", X="Grid"))
        self.registry.register(Domain(
            name="Permutation GNN", group_order=720, k=1, m=1, phi_desc="S6 permutation",
            tags=["ai", "invariance"], G="S6", H="e", X="Graph"))

        # RL / Robotics Domains
        self.registry.register(Domain(
            name="Symmetric Robot Arm", group_order=8, k=2, m=2, phi_desc="Z2 reflection",
            tags=["rl", "robotics"], G="D4", H="Z2", X="StateSpace"))

        # Cryptography / Security Domains
        self.registry.register(Domain(
            name="Modular Exp (RSA)", group_order=1024, k=1, m=1024, phi_desc="x^e mod n",
            tags=["crypto", "hardness"], G="Z_n^*", H="e", X="Z_n"))

        # Quantum Computing Domains
        self.registry.register(Domain(
            name="Quantum Stabilizer", group_order=16, k=2, m=4, phi_desc="error syndrome",
            tags=["quantum", "stabilizer"], G="PauliGroup", H="StabilizerSubgroup", X="Syndromes"))

        # Computational Biology Domains
        self.registry.register(Domain(
            name="Protein Folding Lattice", group_order=24, k=3, m=6, phi_desc="icosahedral symmetry",
            tags=["biology", "lattice"], G="I_h", H="I", X="Foldings"))

        # Music Theory Domains
        self.registry.register(Domain(
            name='Chromatic Scale Z_12', group_order=12, k=1, m=4, phi_desc='augmented triads',
            tags=['music', 'theory'], G='Z_12', H='Z_3', X='Z_4'))

        # Physics & Linguistics Domains
        self.registry.register(Domain(
            name='Lattice Gauge QCD', group_order=192, k=4, m=24, phi_desc='plaquette action',
            tags=['physics', 'lattice'], G='SU(3)_discretized', H='Z_3', X='GluonField'))
        self.registry.register(Domain(
            name='Morphological Syncretism', group_order=8, k=1, m=2, phi_desc='person/number merge',
            tags=['linguistics', 'symmetry'], G='FeatureGroup', H='Z_4', X='Paradigm'))




        # Advanced Domains
        self.registry.register(Domain(
            name="Cubic Crystal Z_4^3", group_order=64, k=3, m=4, phi_desc="projection to Z_4",
            tags=["crystal", "3d"], G="Z_4^3", H="Z_4^2", X="Z_4"))
        self.registry.register(Domain(
            name="Non-abelian S_3", group_order=6, k=2, m=2, phi_desc="parity map S_3 -> Z_2",
            tags=["non-abelian", "lie"], G="S_3", H="A_3", X="Z_2"))
        self.registry.register(Domain(
            name="Hamming Code (7,4)", group_order=128, k=7, m=8, phi_desc="parity-check matrix",
            tags=["coding", "perfect"], G="Z_2^7", H="Z_2^4", X="Z_2^3"))

        for m,sol,tags in [(3,PRECOMPUTED.get((3,3)),["cycles","odd"]),
                           (4,PRECOMPUTED.get((4,3)),["cycles","even","sa"]),
                           (5,PRECOMPUTED.get((5,3)),["cycles","odd"]),
                           (7,None,["cycles","odd"])]:
            self.registry.register(Domain(
                name=f"Cycles m={m} k=3", group_order=m**3, k=3, m=m, phi_desc=f"(i+j+k) mod {m}",
                tags=tags, precomputed=sol, notes=f"G_{m}"))
        self.registry.register(Domain(
            name="Cycles m=4 k=4 [OPEN]", group_order=64, k=4, m=4, phi_desc="(i+j+k) mod 4",
            tags=["cycles","even","k4","frontier"],
            notes="r-quad (1,1,1,1). Fiber-uniform impossible (331K checked). Open."))
        self.registry.register(Domain(
            name="Hamming(7,4)", group_order=128, k=8, m=2, phi_desc="parity-check Z_2^7→Z_2^3",
            tags=["coding","perfect"], notes="Perfect code: ball×|C|=128"))
        self.registry.register(Domain(
            name="Latin Square n=5", group_order=5, k=1, m=5, phi_desc="identity",
            tags=["latin"], notes="Cyclic L[i][j]=(i+j)%n"))


if __name__ == "__main__":
    e = Engine()
    for m,k in [(3,3),(4,3),(4,4),(5,3),(7,3)]:
        r = e.run(m,k)
        print(f"  {r.one_line()}")
    e.print_tree()
    e.print_space(12,7)
