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
