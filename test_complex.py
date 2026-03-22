from src.engine import Engine, inject_domain
import sys

e = Engine()

# 1. Non-abelian Lie Group discretized (G=S_3)
print("Testing Non-abelian S_3...")
d1 = inject_domain({'name': 'Lie Algebra S_3', 'group': 'S_3', 'k': 2, 'm': 2, 'action': 'projection to Z_2'})
e.register(d1)
r1 = e.analyse(d1.name, verbose=True)
th1 = e.identify_theorem(r1)
print(f"  Result: {r1.one_line()} {th1}")

# 2. Crystal system with large group order
print("\nTesting Large Crystal Z_60...")
d2 = inject_domain({'name': 'Z_60 Crystal', 'group': 'Z_60', 'k': 3, 'action': 'projection to best divisor'})
e.register(d2)
r2 = e.analyse(d2.name, verbose=True)
th2 = e.identify_theorem(r2)
print(f"  Result: {r2.one_line()} {th2}")

# 3. Hamming Code instance
print("\nTesting Hamming Code Z_2^7 -> Z_2^3...")
d3 = inject_domain({'name': 'Hamming(7,4)', 'group': 'Z_128', 'm': 8, 'k': 2})
e.register(d3)
r3 = e.analyse(d3.name, verbose=True)
th3 = e.identify_theorem(r3)
print(f"  Result: {r3.one_line()} {th3}")
