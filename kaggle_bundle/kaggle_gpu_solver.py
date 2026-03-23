import os
import sys

# Ensure kaggle_bundle is in the path so we can import src and kaggle_evaluation
sys.path.append(os.getcwd())

import kaggle_evaluation.aimo_3_inference_server

if __name__ == "__main__":
    # In Kaggle environment, we just start the server
    server = kaggle_evaluation.aimo_3_inference_server.AIMO3InferenceServer()
    server.serve()
