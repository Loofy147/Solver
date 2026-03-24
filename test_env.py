import sys
try:
    import kaggle_evaluation
    print("kaggle_evaluation found in environment")
    print("Path:", kaggle_evaluation.__path__)
except ImportError:
    print("kaggle_evaluation NOT found in environment")

try:
    import polars as pl
    print("polars version:", pl.__version__)
except ImportError:
    print("polars NOT found")

try:
    import sympy
    print("sympy version:", sympy.__version__)
except ImportError:
    print("sympy NOT found")
