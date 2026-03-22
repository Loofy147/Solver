from src.real_world import CryptoSolver, MusicSolver, ProteinSolver

# 1. BSGS Test
p = 101; g = 2; x = 37; h = pow(g, x, p)
assert CryptoSolver.solve_discrete_log(g, h, p) == x
print("BSGS solver verified.")

# 2. Chord Test
notes = [60, 64, 67] # C Maj
chords = MusicSolver.analyze_chords(notes)
assert chords[0][0] == "Major"
print("Music solver verified.")

# 3. HP Fold Test
seq = "HPHP"
res = ProteinSolver.fold_hp(seq)
assert len(res['path']) == 4
print("Protein solver verified.")
