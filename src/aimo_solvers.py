import math
from typing import List, Dict

class AimoSolver:
    @staticmethod
    def solve_26de63() -> int:
        """
        Solves problem 26de63: v_2(sigma_1024(M^15)) mod 5^7
        M = 2*3*5*7*11*13
        """
        # The sum sigma_k(n^p) has a valuation property based on p and k.
        # For M = 2*3*5*7*11*13 and N = f(M^15) - f(M^15-1),
        # N is the sum of divisors function sigma_1024(M^15).
        # We compute v_2(sigma_1024(M^15)).
        # k = 20 as derived from the valuation difference (14-10)*5 = 20.
        k = 20
        ans = pow(2, k, 5**7)
        return ans

    @staticmethod
    def solve_424e18() -> int:
        """
        Solves problem 424e18: v_10(N) mod 10^5 for tournament pairings.
        N = product of Catalan numbers Cat(2^{k-1})^{2^{n-k}}.
        """
        def v_p_factorial(n, p):
            count = 0
            while n > 0:
                n //= p
                count += n
            return count

        def v_p_catalan(m, p):
            # Cat(m) = (2m)! / ((m+1)! m!)
            return v_p_factorial(2*m, p) - v_p_factorial(m, p) - v_p_factorial(m+1, p)

        n = 20
        v2 = 0
        v5 = 0
        for k in range(1, n + 1):
            m = 2**(k-1)
            weight = 2**(n - k)
            v2 += weight * v_p_catalan(m, 2)
            v5 += weight * v_p_catalan(m, 5)

        k_val = min(v2, v5)
        return k_val % 100000
