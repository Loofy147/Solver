import kaggle_evaluation.core.templates
from src.real_world import AimoIntegration
import polars as pl
import os

def predict(id: pl.Series, problem: pl.Series, *args) -> int:
    problem_id = id.item()
    problem_text = problem.item()
    return AimoIntegration.classify_and_solve(problem_id, problem_text)

class AIMO3InferenceServer(kaggle_evaluation.core.templates.InferenceServer):
    def __init__(self):
        super().__init__(predict)

    def _get_gateway_for_test(self, data_paths=None, *args, **kwargs):
        import aimo_3_gateway
        return aimo_3_gateway.AIMO3Gateway(data_paths)

if __name__ == "__main__":
    server = AIMO3InferenceServer()
    server.serve()
