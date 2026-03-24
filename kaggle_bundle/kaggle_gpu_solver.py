import os
import sys

# Ensure current directory is in path
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKING_DIR not in sys.path:
    sys.path.append(WORKING_DIR)

import kaggle_evaluation.aimo_3_inference_server

if __name__ == "__main__":
    server = kaggle_evaluation.aimo_3_inference_server.AIMO3InferenceServer()
    server.serve()
