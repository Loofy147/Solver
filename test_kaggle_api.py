import os
import sys

# Ensure current directory is in path for relative imports
sys.path.append(os.getcwd())

from kaggle_evaluation.aimo_3_inference_server import AIMO3InferenceServer
import polars as pl

# Mocking Kaggle rerun environment
os.environ['KAGGLE_IS_COMPETITION_RERUN'] = '1'

def run_test():
    server = AIMO3InferenceServer()
    # Using local gateway for test
    # We need to point to a test file
    test_path = 'reference.csv'
    if not os.path.exists(test_path):
        print(f"Error: {test_path} not found.")
        return

    print("Starting local gateway test...")
    server.run_local_gateway(data_paths=(test_path,))
    print("Test finished.")

if __name__ == "__main__":
    run_test()
