import glob
import json
import os

for p in sorted(glob.glob("online_quiz/kimi_*_在线模拟.js")):
    with open(p, "r", encoding="utf-8") as f:
        txt = f.read()
    data = json.loads(txt[len("const quizData = "):-2])
    counts = {}
    for q in data:
        counts[q["type"]] = counts.get(q["type"], 0) + 1
    print(os.path.basename(p), counts)
