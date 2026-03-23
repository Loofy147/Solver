import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.real_world import AimoIntegration

def evaluate():
    if not os.path.exists('reference.csv'):
        print("Error: reference.csv not found.")
        return

    df = pd.read_csv('reference.csv')
    correct = 0
    total = len(df)

    print(f"Evaluating AIMO solvers on {total} reference problems...")
    print("-" * 60)

    for _, row in df.iterrows():
        pid = row['id']
        problem = row['problem']
        expected = row['answer']

        try:
            actual = AimoIntegration.classify_and_solve(pid, problem)
            is_correct = (actual == expected)
            if is_correct:
                correct += 1

            status = "PASS" if is_correct else "FAIL"
            print(f"[{pid}] {status:4} | Expected: {expected:5} | Actual: {actual:5}")
        except Exception as e:
            print(f"[{pid}] ERROR | {e}")

    print("-" * 60)
    score = correct / total
    print(f"Final Score: {correct}/{total} ({score*100:.1f}%)")

if __name__ == "__main__":
    evaluate()
