import os
import sys

# Standard relative path detection
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from kaggle_evaluation.aimo_3_inference_server import AIMO3InferenceServer
from aimo_logic import predict

if __name__ == "__main__":
    server = AIMO3InferenceServer(predict)

    # KAGGLE_IS_COMPETITION_RERUN is set during the private rerun
    if os.getenv('KAGGLE_IS_COMPETITION_RERUN'):
        server.serve()
    else:
        # Commit phase: generate submission.parquet
        test_path = '/kaggle/input/ai-mathematical-olympiad-progress-prize-3/test.csv'
        if not os.path.exists(test_path):
            # For local verification or commit if path differs
            test_path = 'test.csv'

        server.run_local_gateway(data_paths=(test_path,))
