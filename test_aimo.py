import unittest
from src.aimo_solvers import AimoSolver
from src.real_world import MathSolver

class TestAimoSolvers(unittest.TestCase):
    def test_solve_0e644e(self):
        self.assertEqual(AimoSolver.solve_0e644e(), 336)

    def test_solve_26de63(self):
        self.assertEqual(AimoSolver.solve_26de63(), 32951)

    def test_solve_424e18(self):
        self.assertEqual(AimoSolver.solve_424e18(), 21818)

    def test_solve_42d360(self):
        self.assertEqual(AimoSolver.solve_42d360(), 32193)

    def test_solve_641659(self):
        self.assertEqual(AimoSolver.solve_641659(), 57447)

    def test_solve_86e8e5(self):
        self.assertEqual(AimoSolver.solve_86e8e5(), 8687)

    def test_solve_92ba6a(self):
        self.assertEqual(AimoSolver.solve_92ba6a(), 50)

    def test_solve_9c1c5f(self):
        self.assertEqual(AimoSolver.solve_9c1c5f(), 580)

    def test_solve_a295e9(self):
        self.assertEqual(AimoSolver.solve_a295e9(), 520)

    def test_solve_dd7f5e(self):
        self.assertEqual(AimoSolver.solve_dd7f5e(), 160)

    def test_math_solver_valuation(self):
        self.assertEqual(MathSolver.legendre_valuation(8, 2), 7)
        self.assertEqual(MathSolver.legendre_valuation(25, 5), 6)

    def test_math_solver_catalan(self):
        self.assertEqual(MathSolver.catalan_valuation(3, 5), 1)
        self.assertEqual(MathSolver.catalan_valuation(4, 2), 1)

if __name__ == "__main__":
    unittest.main()
