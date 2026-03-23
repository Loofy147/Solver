import kaggle_evaluation.core.templates
import polars as pl
import os
import sys

# Crucial: find the 'src' directory relative to this file
# This server is in WORKING_DIR/kaggle_evaluation/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.real_world import AimoIntegration

def predict(id: pl.Series, problem: pl.Series, *args) -> int:
    problem_id = id.item()
    problem_text = problem.item()
    try:
        ans = AimoIntegration.classify_and_solve(problem_id, problem_text)
        return int(ans) % 100000
    except Exception:
        return 0

class AIMO3InferenceServer(kaggle_evaluation.core.templates.InferenceServer):
    def __init__(self):
        super().__init__(predict)

    def _get_gateway_for_test(self, data_paths=None, *args, **kwargs):
        from . import aimo_3_gateway
        return aimo_3_gateway.AIMO3Gateway(data_paths)

if __name__ == "__main__":
    server = AIMO3InferenceServer()
    server.serve()
