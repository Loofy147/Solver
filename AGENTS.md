# Agent Instructions for Highly Symmetric Systems

## Competition Mode (AIMO 3)
The system is equipped with specialized solvers for the AI Mathematical Olympiad.
- **Entry Point:** Use `python3 main.py --solve-aimo` to verify the 10 reference problems.
- **Evaluation API:** The Kaggle evaluation framework is in `kaggle_evaluation/`.
- **Inference Server:** `kaggle_evaluation/aimo_3_inference_server.py` handles gRPC requests.
- **Solvers:** `src/aimo_solvers.py` contains specialized logic for number theory, geometry, and combinatorics.
- **Symbolic Fallback:** `AimoSolver.solve_symbolic` uses `sympy` to solve basic algebra and arithmetic.

## Performance & Optimization
- **Parallel Tempering:** Use `src.core.run_sa_tempering` for complex combinatorial landscapes (e.g., m=6).
- **GPU Acceleration:** `src.gpu_core.GPUSolver` provides high-speed SA using PyTorch.
- **Path Doubling:** The score function in GPU mode uses O(log N) path-doubling for cycle detection.

## Verification
- Always run `python3 -m unittest test_aimo.py` after modifying solvers.
- Use `python3 run_aimo_eval.py` to verify the full reference set (10/10 expected).
- Run `python3 main.py --theorems` to ensure core symmetry properties are preserved.

## Deployment
- The `kaggle_bundle/` directory contains the synchronized submission package.
- Push to Kaggle using: `kaggle kernels push -p kaggle_bundle`.
