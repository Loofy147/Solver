import os
import sys

# Standard Kaggle paths
WORKING_DIR = '/kaggle/working'
if WORKING_DIR not in sys.path:
    sys.path.append(WORKING_DIR)

import kaggle_evaluation.aimo_3_inference_server

if __name__ == "__main__":
    server = kaggle_evaluation.aimo_3_inference_server.AIMO3InferenceServer()
    server.serve()
