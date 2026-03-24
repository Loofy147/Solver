<<<<<<< SEARCH
from src.real_world import CryptoSolver, MusicSolver, ProteinSolver

G_="\033[92m";R_="\033[91m";Y_="\033[93m";B_="\033[94m"
=======
from src.real_world import CryptoSolver, MusicSolver, ProteinSolver, MathSolver
from src.aimo_solvers import AimoSolver

G_="\033[92m";R_="\033[91m";Y_="\033[93m";B_="\033[94m"
>>>>>>> REPLACE
<<<<<<< SEARCH
    parser.add_argument("--showcase-real", action="store_true", help="Showcase real-world data solvers")
    parser.add_argument("--crypto-check", type=int, help="Show crypto group hardness for prime p")
=======
    parser.add_argument("--showcase-real", action="store_true", help="Showcase real-world data solvers")
    parser.add_argument("--solve-aimo", action="store_true", help="Solve AIMO competition reference problems")
    parser.add_argument("--crypto-check", type=int, help="Show crypto group hardness for prime p")
>>>>>>> REPLACE
<<<<<<< SEARCH
    if args.showcase_real:
        print(f"\n{W_}REAL-WORLD SYMMETRY CHALLENGE SHOWCASE{Z_}")
=======
    if args.solve_aimo:
        print(f"\n{W_}AIMO COMPETITION REFERENCE SOLVER{Z_}")
        print("─"*72)
        print(f"{B_}[26de63]{Z_} Sum-of-divisors valuation: v_2(sigma_1024(M^15))")
        ans1 = AimoSolver.solve_26de63()
        print(f"  Result: {G_}{ans1}{Z_} (Correct: 32951)")
        print(f"\n{B_}[424e18]{Z_} Tournament order valuation: v_10(N) mod 10^5")
        ans2 = AimoSolver.solve_424e18()
        print(f"  Result: {G_}{ans2}{Z_} (Correct: 21818)")

    if args.showcase_real:
        print(f"\n{W_}REAL-WORLD SYMMETRY CHALLENGE SHOWCASE{Z_}")
>>>>>>> REPLACE
