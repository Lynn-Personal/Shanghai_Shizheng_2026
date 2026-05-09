import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIMI_DIR = ROOT / "kimi题库"
ONLINE_DIR = ROOT / "online_quiz"


def parse_options_line(line: str):
    line = line.strip()
    # Match: A. xxx  B. xxx  C. xxx  D. xxx
    parts = re.findall(r"([A-D])\.\s*(.*?)(?=\s+[A-D]\.|$)", line)
    if len(parts) == 4:
        return [p[1].strip() for p in parts]
    return []


def normalize_text(s: str) -> str:
    return s.replace("\u3000", " ").strip()


def parse_answers_block(lines):
    answer_maps = {
        "fill": {},
        "single": {},
        "multiple": {},
        "judge": {},
    }

    section = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if "### 一、填空题" in line:
            section = "fill"
            continue
        if "### 二、单项选择题" in line:
            section = "single"
            continue
        if "### 三、多项选择题" in line:
            section = "multiple"
            continue
        if "### 四、是非判断题" in line:
            section = "judge"
            continue

        if section is None:
            continue

        # Keep digits inside answers (e.g., 2025, 85.46, 118), only split on next question number marker.
        pairs = re.findall(r"(\d+)\.\s*(.+?)(?=\s+\d+\.|$)", line)
        for idx, ans in pairs:
            idx_i = int(idx)
            a = ans.strip()
            if section == "single":
                m = re.search(r"([ABCD])", a)
                if m:
                    answer_maps[section][idx_i] = m.group(1)
            elif section == "multiple":
                m = re.search(r"([ABCD]{2,4})", a)
                if m:
                    answer_maps[section][idx_i] = m.group(1)
            elif section == "judge":
                m = re.search(r"([AB])", a)
                if m:
                    answer_maps[section][idx_i] = m.group(1)
            else:
                answer_maps[section][idx_i] = a

    return answer_maps


def letter_to_index(ch: str) -> int:
    return ord(ch) - ord("A")


def parse_file(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title = "在线模拟题"
    topic = path.stem.replace("kimi", "").replace("题库", "")

    for line in lines:
        if line.strip().startswith("###") and "主题" in line:
            title = line.strip("# ")
            break

    # Locate answer section
    ans_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## 参考答案"):
            ans_start = i
            break
    if ans_start is None:
        raise ValueError(f"No answer section in {path}")

    answer_maps = parse_answers_block(lines[ans_start:])

    data = []
    section = None
    q_index = 0
    current_q = None

    def flush_current():
        nonlocal current_q, q_index
        if not current_q:
            return
        q_index += 1
        current_q["no"] = q_index
        data.append(current_q)
        current_q = None

    i = 0
    while i < len(lines[:ans_start]):
        line = lines[i].rstrip()
        s = line.strip()

        if s.startswith("## 一、填空题"):
            flush_current()
            section = "fill"
            q_index = 0
            data.append({"type": "info", "info": "【填空题】"})
            i += 1
            continue
        if s.startswith("## 二、单项选择题"):
            flush_current()
            section = "single"
            q_index = 0
            data.append({"type": "info", "info": "【单项选择题】"})
            i += 1
            continue
        if s.startswith("## 三、多项选择题"):
            flush_current()
            section = "multiple"
            q_index = 0
            data.append({"type": "info", "info": "【多项选择题】"})
            i += 1
            continue
        if s.startswith("## 四、是非判断题"):
            flush_current()
            section = "judge"
            q_index = 0
            data.append({"type": "info", "info": "【是非判断题】"})
            i += 1
            continue

        q_match = re.match(r"^(\d+)\.\s*(.+)$", s)
        if section and q_match:
            flush_current()
            q_no = int(q_match.group(1))
            q_text = normalize_text(q_match.group(2))

            if section == "fill":
                ans_text = answer_maps["fill"].get(q_no, "")
                ans_list = [normalize_text(ans_text)] if ans_text else [""]
                current_q = {
                    "type": "fill",
                    "question": q_text,
                    "answer": ans_list,
                    "explanation": "依据题库参考答案。",
                }
            elif section in ("single", "multiple"):
                opts = []
                j = i + 1
                while j < ans_start and len(opts) < 4:
                    opt_line = lines[j].strip()
                    if not opt_line:
                        j += 1
                        continue
                    parsed = parse_options_line(opt_line)
                    if parsed:
                        opts = parsed
                        break
                    j += 1

                if len(opts) != 4:
                    opts = ["选项A", "选项B", "选项C", "选项D"]

                if section == "single":
                    letter = answer_maps["single"].get(q_no, "A")
                    answer = [letter_to_index(letter)]
                else:
                    letters = answer_maps["multiple"].get(q_no, "AB")
                    answer = [letter_to_index(c) for c in letters]

                current_q = {
                    "type": section,
                    "question": q_text,
                    "options": opts,
                    "answer": answer,
                    "explanation": "依据题库参考答案。",
                }
            elif section == "judge":
                letter = answer_maps["judge"].get(q_no, "A")
                answer = [0 if letter == "A" else 1]
                current_q = {
                    "type": "judge",
                    "question": q_text,
                    "options": ["正确", "错误"],
                    "answer": answer,
                    "explanation": "依据题库参考答案。",
                }

        i += 1

    flush_current()

    for item in data:
        if "no" in item:
            del item["no"]

    return topic, title, data


def write_outputs(topic: str, title: str, data):
    js_name = f"kimi_{topic}_在线模拟.js"
    html_name = f"kimi_{topic}_在线模拟.html"

    js_path = ONLINE_DIR / js_name
    html_path = ONLINE_DIR / html_name

    js_content = "const quizData = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    js_path.write_text(js_content, encoding="utf-8")

    html = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>{topic} Kimi题库在线模拟</title>
  <link rel=\"stylesheet\" href=\"style.css\">
</head>
<body>
  <div id=\"quiz-container\"></div>
  <script src=\"{js_name}\"></script>
  <script src=\"main.js\"></script>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")


def main():
    txt_files = sorted(KIMI_DIR.glob("kimi*题库.txt"))
    if not txt_files:
        raise SystemExit("No kimi quiz txt files found")

    for f in txt_files:
        topic, title, data = parse_file(f)
        write_outputs(topic, title, data)
        print(f"Converted: {f.name} -> kimi_{topic}_在线模拟.html/js ({len(data)} items)")


if __name__ == "__main__":
    main()
