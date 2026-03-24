import kaggle_evaluation.core.templates
import polars as pl
import os
import sys

# Ensure root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.real_world import AimoIntegration

def predict(id: pl.Series, problem: pl.Series, *args) -> int:
    try:
        problem_id = str(id.item())
        problem_text = str(problem.item())
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
