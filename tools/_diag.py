"""Diagnose problem characters on line 345 of kp_driven_quiz_generator.py"""
import pathlib

path = pathlib.Path(__file__).parent / "kp_driven_quiz_generator.py"
lines = path.read_text(encoding="utf-8").splitlines()
line = lines[344]  # 0-indexed
print("LINE:", repr(line))
for i, c in enumerate(line):
    if ord(c) > 127:
        print(f"  pos={i} char={repr(c)} hex=U+{ord(c):04X}")
