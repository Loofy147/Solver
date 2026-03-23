import unittest
from src.aimo_solvers import AimoSolver
from src.real_world import MathSolver

class TestAimoSolvers(unittest.TestCase):
    def test_solve_26de63(self):
        # Known answer from reference.csv
        self.assertEqual(AimoSolver.solve_26de63(), 32951)

    def test_solve_424e18(self):
        # Known answer from reference.csv
        self.assertEqual(AimoSolver.solve_424e18(), 21818)

    def test_math_solver_valuation(self):
        # v_2(8!) = 4+2+1 = 7
        self.assertEqual(MathSolver.legendre_valuation(8, 2), 7)
        # v_5(25!) = 5+1 = 6
        self.assertEqual(MathSolver.legendre_valuation(25, 5), 6)

    def test_math_solver_catalan(self):
        # Cat(3) = 5. v_5(5) = 1.
        self.assertEqual(MathSolver.catalan_valuation(3, 5), 1)
        # Cat(4) = 14. v_2(14) = 1.
        self.assertEqual(MathSolver.catalan_valuation(4, 2), 1)

if __name__ == "__main__":
    unittest.main()
