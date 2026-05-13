import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "kimi题库" / "国内新闻.txt"
OUT_DIR = ROOT / "online_quiz"


def clean_question_text(s: str) -> str:
    s = s.replace("\u3000", " ").strip()
    s = re.sub(r"[（(]\s*[）)]\s*$", "", s)
    return s.strip()


def normalize(s: str) -> str:
    return s.replace("\u3000", " ").strip()


def parse_question_blocks(lines):
    section = None
    fill_q = {}
    single_q = {}
    multiple_q = {}
    judge_q = {}

    i = 0
    while i < len(lines):
        s = lines[i].strip()

        if re.match(r"^一[、.]填空题", s):
            section = "fill"
            i += 1
            continue
        if re.match(r"^二[、.]单项选择题", s):
            section = "single"
            i += 1
            continue
        if re.match(r"^三[、.]多项选择题", s):
            section = "multiple"
            i += 1
            continue
        if re.match(r"^四[、.]判断题|^四[、.]是非判断题", s):
            section = "judge"
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s*(.+)$", s)
        if not m or section is None:
            i += 1
            continue

        q_no = int(m.group(1))
        q_text = clean_question_text(m.group(2))

        if section == "fill":
            fill_q[q_no] = q_text
            i += 1
            continue

        if section in ("single", "multiple"):
            options = []
            j = i + 1
            while j < len(lines):
                opt = lines[j].strip()
                mo = re.match(r"^([A-E])\.\s*(.+)$", opt)
                if mo:
                    options.append(normalize(mo.group(2)))
                    j += 1
                    continue
                break
            if options:
                item = {"question": q_text, "options": options}
                if section == "single":
                    single_q[q_no] = item
                else:
                    multiple_q[q_no] = item
                i = j
                continue

        if section == "judge":
            judge_q[q_no] = q_text
            i += 1
            continue

        i += 1

    return fill_q, single_q, multiple_q, judge_q


def parse_answers(lines):
    section = None
    fill_a = {}
    single_a = {}
    multiple_a = {}
    judge_a = {}

    for raw in lines:
        s = raw.strip()
        if not s:
            continue

        if re.match(r"^一[、.]填空题", s):
            section = "fill"
            continue
        if re.match(r"^二[、.]单项选择题", s):
            section = "single"
            continue
        if re.match(r"^三[、.]多项选择题", s):
            section = "multiple"
            continue
        if re.match(r"^四[、.]判断题|^四[、.]是非判断题", s):
            section = "judge"
            continue

        if section == "fill":
            m = re.match(r"^(\d+)\.\s*(.+)$", s)
            if m:
                fill_a[int(m.group(1))] = normalize(m.group(2))
            continue

        if section == "single":
            m_range = re.match(r"^(\d+)\s*-\s*(\d+)\s*:\s*(.+)$", s)
            if m_range:
                start = int(m_range.group(1))
                end = int(m_range.group(2))
                letters = re.findall(r"[A-D]", m_range.group(3))
                n = min(end - start + 1, len(letters))
                for idx in range(n):
                    single_a[start + idx] = letters[idx]
                continue
            m_one = re.match(r"^(\d+)\.\s*([A-D])$", s)
            if m_one:
                single_a[int(m_one.group(1))] = m_one.group(2)
            continue

        if section == "multiple":
            m = re.match(r"^(\d+)\.\s*([A-E]{2,5})$", s)
            if m:
                multiple_a[int(m.group(1))] = m.group(2)
            continue

        if section == "judge":
            m = re.match(r"^(\d+)\.\s*([√×AB])(?:[（(](.*?)[）)])?\s*$", s)
            if not m:
                continue
            no = int(m.group(1))
            tag = m.group(2)
            extra = normalize(m.group(3) or "")
            if tag in ("√", "A"):
                judge_a[no] = {"correct": True, "detail": ""}
            else:
                judge_a[no] = {"correct": False, "detail": extra}

    return fill_a, single_a, multiple_a, judge_a


def letter_to_index(ch: str) -> int:
    return ord(ch) - ord("A")


def build_data(fill_q, single_q, multiple_q, judge_q, fill_a, single_a, multiple_a, judge_a):
    data = [{"type": "info", "info": "【填空题】"}]

    for no in sorted(fill_q):
        data.append(
            {
                "type": "fill",
                "question": fill_q[no],
                "answer": [fill_a.get(no, "")],
                "explanation": "依据题库参考答案。",
            }
        )

    data.append({"type": "info", "info": "【单项选择题】"})
    for no in sorted(single_q):
        letter = single_a.get(no, "A")
        data.append(
            {
                "type": "single",
                "question": single_q[no]["question"],
                "options": single_q[no]["options"],
                "answer": [letter_to_index(letter)],
                "explanation": "依据题库参考答案。",
            }
        )

    data.append({"type": "info", "info": "【多项选择题】"})
    for no in sorted(multiple_q):
        letters = multiple_a.get(no, "AB")
        data.append(
            {
                "type": "multiple",
                "question": multiple_q[no]["question"],
                "options": multiple_q[no]["options"],
                "answer": [letter_to_index(ch) for ch in letters],
                "explanation": "依据题库参考答案。",
            }
        )

    data.append({"type": "info", "info": "【是非判断题】"})
    for no in sorted(judge_q):
        ans = judge_a.get(no, {"correct": True, "detail": ""})
        is_true = bool(ans.get("correct"))
        detail = normalize(ans.get("detail", ""))

        correct_answer_text = "正确"
        explanation = "依据题库参考答案。"
        if not is_true:
            if detail:
                correct_answer_text = f"错误（{detail}）"
                explanation = f"依据题库参考答案。{detail}"
            else:
                correct_answer_text = "错误"

        data.append(
            {
                "type": "judge",
                "question": judge_q[no],
                "options": ["正确", "错误"],
                "answer": [0 if is_true else 1],
                "correctAnswerText": correct_answer_text,
                "explanation": explanation,
            }
        )

    return data


def main():
    if not SRC.exists():
        raise SystemExit(f"Source not found: {SRC}")

    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()

    ans_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("参考答案"):
            ans_start = i
            break
    if ans_start is None:
        raise SystemExit("Cannot find answer block.")

    question_lines = lines[:ans_start]
    answer_lines = lines[ans_start + 1 :]

    fill_q, single_q, multiple_q, judge_q = parse_question_blocks(question_lines)
    fill_a, single_a, multiple_a, judge_a = parse_answers(answer_lines)

    data = build_data(fill_q, single_q, multiple_q, judge_q, fill_a, single_a, multiple_a, judge_a)

    js_name = "kimi_国内新闻_在线模拟.js"
    html_name = "kimi_国内新闻_在线模拟.html"

    js_path = OUT_DIR / js_name
    html_path = OUT_DIR / html_name

    js_content = "const quizData = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    js_path.write_text(js_content, encoding="utf-8")

    html = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>国内新闻 Kimi题库在线模拟</title>
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

    print(f"Generated {js_name} with {len(data)} items")


if __name__ == "__main__":
    main()
