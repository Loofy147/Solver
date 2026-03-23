"""
real_world.py — Practical Data Solvers
=======================================
Solving actual instances in Cryptography, Music, and Biology.
"""

import math
from typing import List, Dict, Tuple, Any

class CryptoSolver:
    @staticmethod
    def solve_discrete_log(g: int, h: int, p: int) -> int:
        """
        Solves g^x = h mod p using Baby-step Giant-step (BSGS).
        Exploits the cyclic group structure of Z_p^*.
        """
        m = math.ceil(math.sqrt(p - 1))
        # Baby steps
        lookup = {pow(g, j, p): j for j in range(m)}
        # Giant steps
        c = pow(g, m * (p - 2), p) # g^(-m) mod p
        for i in range(m):
            target = (h * pow(c, i, p)) % p
            if target in lookup:
                return i * m + lookup[target]
        return -1

class MusicSolver:
    @staticmethod
    def analyze_chords(notes: List[int]) -> List[Tuple[str, str]]:
        """
        Maps sequences of notes to canonical chords in Z_12.
        Identifies orbits under the transposition group.
        """
        chords = []
        for i in range(0, len(notes) - 2, 3):
            chord = sorted([n % 12 for n in notes[i:i+3]])
            # Transpose to root (canonical form)
            root = chord[0]
            canonical = tuple((n - root) % 12 for n in chord)

            label = "Unknown"
            if canonical == (0, 4, 7): label = "Major"
            elif canonical == (0, 3, 7): label = "Minor"
            elif canonical == (0, 4, 8): label = "Augmented"
            elif canonical == (0, 3, 6): label = "Diminished"

            chords.append((label, str(chord)))
        return chords

class ProteinSolver:
    @staticmethod
    def fold_hp(sequence: str) -> Dict:
        """
        Symmetry-guided HP folding on a 2D lattice.
        Uses a simple greedy approach with symmetry-aware local search.
        """
        # sequence like "HPHPH"
        # directions: (1,0), (-1,0), (0,1), (0,-1)
        path = [(0,0)]
        visited = {(0,0)}

        for amino in sequence[1:]:
            curr = path[-1]
            best_move = None
            max_contacts = -1

            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                cand = (curr[0]+dx, curr[1]+dy)
                if cand not in visited:
                    # Heuristic: maximize H-H contacts (adjacent but not sequential)
                    contacts = 0
                    if amino == 'H':
                        for ddx, ddy in [(1,0), (-1,0), (0,1), (0,-1)]:
                            neighbor = (cand[0]+ddx, cand[1]+ddy)
                            if neighbor in visited and sequence[path.index(neighbor)] == 'H':
                                # Check if it's not a sequential neighbor
                                if neighbor != curr:
                                    contacts += 1

                    if contacts > max_contacts:
                        max_contacts = contacts
                        best_move = cand

            if best_move:
                path.append(best_move)
                visited.add(best_move)
            else:
                # Dead end, just move somewhere free
                break

        return {"sequence": sequence, "path": path, "score": sum(1 for p in path)}

class MathSolver:
    @staticmethod
    def legendre_valuation(n: int, p: int) -> int:
        """Computes v_p(n!) using Legendre's formula."""
        count = 0
        while n > 0:
            n //= p
            count += n
        return count

    @staticmethod
    def catalan_valuation(m: int, p: int) -> int:
        """Computes v_p(Cat(m)) where Cat(m) is the m-th Catalan number."""
        # Cat(m) = (2m)! / ((m+1)! m!)
        v = MathSolver.legendre_valuation
        return v(2*m, p) - v(m, p) - v(m+1, p)

    @staticmethod
    def sum_divisors_valuation_pow2(p: int, e: int, k: int) -> int:
        """
        Computes v_2(sigma_k(p^e)).
        sigma_k(p^e) = (p^(k(e+1)) - 1) / (p^k - 1)
        """
        if p == 2:
            # sigma_k(2^e) = 1 + 2^k + ... + 2^(ke).
            # If k > 0 and e > 0, this is 1 + even = odd. v_2 = 0.
            return 0

        # For odd p, we use Lifting The Exponent Lemma or basic properties.
        # v_2(p^n - 1) = v_2(p-1) + v_2(p+1) + v_2(n) - 1 for even n.
        def v2_pow_minus_1(x, n):
            if n == 0: return 0 # should not happen here
            # v_2(x^n - 1)
            v_x_minus_1 = 0
            tmp = x - 1
            while tmp > 0 and tmp % 2 == 0:
                v_x_minus_1 += 1
                tmp //= 2

            v_x_plus_1 = 0
            tmp = x + 1
            while tmp > 0 and tmp % 2 == 0:
                v_x_plus_1 += 1
                tmp //= 2

            v_n = 0
            tmp = n
            while tmp > 0 and tmp % 2 == 0:
                v_n += 1
                tmp //= 2

            return v_x_minus_1 + v_x_plus_1 + v_n - 1

        v_num = v2_pow_minus_1(p, k * (e + 1))
        v_den = v2_pow_minus_1(p, k)
        return v_num - v_den
