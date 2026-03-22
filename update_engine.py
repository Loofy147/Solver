import sys
import re

with open('src/engine.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'for m,sol,tags in [' in line and 'cycles' in line:
        # This was part of _load_defaults
        new_lines.append('        for m,sol,tags in [(3,PRECOMPUTED.get((3,3)),["cycles","odd"]),\n')
        new_lines.append('                           (4,PRECOMPUTED.get((4,3)),["cycles","even","sa"]),\n')
        new_lines.append('                           (5,PRECOMPUTED.get((5,3)),["cycles","odd"]),\n')
        new_lines.append('                           (7,None,["cycles","odd"])]:\n')
        continue
    if 'self.registry.register(Domain(' in line and 'Cycles m={m}' in line:
        new_lines.append('            self.registry.register(Domain(\n')
        continue
    if 'f"Cycles m={m} k=3", m**3, 3, m, f"(i+j+k) mod {m}",' in line:
        new_lines.append('                f"Cycles m={m} k=3", m**3, 3, m, f"(i+j+k) mod {m}",\n')
        continue
    new_lines.append(line)

# Let's just rewrite the whole _load_defaults to be safe
content = "".join(new_lines)
start_defaults = content.find('def _load_defaults(self):')
end_defaults = content.find('if __name__ == "__main__":')

new_defaults = """    def _load_defaults(self):
        # Advanced Domains
        self.registry.register(Domain(
            "Cubic Crystal Z_4^3", 64, 3, 4, "projection to Z_4",
            ["crystal", "3d"], G="Z_4^3", H="Z_4^2", X="Z_4"))
        self.registry.register(Domain(
            "Non-abelian S_3", 6, 2, 2, "parity map S_3 -> Z_2",
            ["non-abelian", "lie"], G="S_3", H="A_3", X="Z_2"))
        self.registry.register(Domain(
            "Hamming Code (7,4)", 128, 7, 8, "parity-check matrix",
            ["coding", "perfect"], G="Z_2^7", H="Z_2^4", X="Z_2^3"))

        for m,sol,tags in [(3,PRECOMPUTED.get((3,3)),["cycles","odd"]),
                           (4,PRECOMPUTED.get((4,3)),["cycles","even","sa"]),
                           (5,PRECOMPUTED.get((5,3)),["cycles","odd"]),
                           (7,None,["cycles","odd"])]:
            self.registry.register(Domain(
                f"Cycles m={m} k=3", m**3, 3, m, f"(i+j+k) mod {m}",
                tags, sol, f"G_{m}"))
        self.registry.register(Domain(
            "Cycles m=4 k=4 [OPEN]", 64, 4, 4, "(i+j+k) mod 4",
            ["cycles","even","k4","frontier"],
            notes="r-quad (1,1,1,1). Fiber-uniform impossible (331K checked). Open."))
        self.registry.register(Domain(
            "Hamming(7,4)", 128, 8, 2, "parity-check Z_2^7→Z_2^3",
            ["coding","perfect"], notes="Perfect code: ball×|C|=128"))
        self.registry.register(Domain(
            "Latin Square n=5", 5, 1, 5, "identity",
            ["latin"], notes="Cyclic L[i][j]=(i+j)%n"))

"""
final_content = content[:start_defaults] + new_defaults + content[end_defaults:]
with open('src/engine.py', 'w') as f:
    f.write(final_content)
