"""One-shot helper: remove all U+201C / U+201D from kp_driven_quiz_generator.py"""
import py_compile, pathlib

path = pathlib.Path(__file__).parent / "kp_driven_quiz_generator.py"
text = path.read_text(encoding="utf-8")
text = text.replace("\u201c", "").replace("\u201d", "")
path.write_text(text, encoding="utf-8")
print(f"Wrote {len(text)} chars")

try:
    py_compile.compile(str(path), doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print("Syntax ERROR:", e)
