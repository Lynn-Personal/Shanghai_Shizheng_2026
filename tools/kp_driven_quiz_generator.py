#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识点驱动题库生成器（中文版新版命名）

使用方法:
  python tools/kp_driven_quiz_generator.py

输出:
  online_quiz/[中文主题]模拟_新版.js
  online_quiz/[中文主题]模拟_新版.html
"""

import json
import re
from pathlib import Path

BASE_PATH = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")

NOISE_PATTERNS = [
    re.compile(r"page\s*\d+", re.IGNORECASE),
    re.compile(r"第\s*\d+\s*页"),
    re.compile(r"新闻现场"),
    re.compile(r"责任编辑[^\n]*"),
    re.compile(r"美术编辑[^\n]*"),
    re.compile(r"邮箱[^\n]*"),
    re.compile(r"一键复制|导出为PDF|Typora|Markdown编辑器"),
    re.compile(r"email:\S+"),
    re.compile(r"相关链接[：:]?"),
    re.compile(r"专家解读[：:]?"),
]


def clean_text(text: str) -> str:
    for p in NOISE_PATTERNS:
        text = p.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip("，。；：！？-_/")


def normalize_section(section: str) -> str:
    s = section or ""
    if "日期" in s or "时间锚" in s:
        return "📅 重要日期"
    if "数字" in s:
        return "📊 数字指标"
    if "组织" in s or "机构" in s:
        return "🏛️ 关键组织/机构"
    if "概念" in s:
        return "💡 关键概念"
    if "术语" in s or "定义" in s:
        return "📖 关键术语/定义"
    if "高频" in s or "核心高优" in s or "考点" in s:
        return "⭐ 参考样题高频考点"
    return "其他"


def load_knowledge_points(theme_name: str):
    kp_file = BASE_PATH / "knowledge_points" / f"{theme_name}_知识点标注.md"
    if not kp_file.exists():
        return []

    kps = []
    current_section = "其他"
    for line in kp_file.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if line.startswith("## "):
            current_section = normalize_section(line.replace("## ", "").strip())
        elif line.startswith("- ") and not line.startswith("- **"):
            kp = line[2:].strip()
            if len(kp) >= 2:
                kps.append((kp, current_section))
    return kps


def load_material(material_file: str) -> str:
    p = BASE_PATH / "materials" / material_file
    if not p.exists():
        return ""
    raw = p.read_text(encoding="utf-8")
    for pat in NOISE_PATTERNS:
        raw = pat.sub("", raw)
    return raw


def build_sentence_index(text: str):
    sentences = []
    for chunk in re.split(r"[。！？\n]+", text):
        chunk = clean_text(chunk)
        if len(chunk) >= 10:
            sentences.append(chunk)
    return sentences


def find_sentence_for_kp(kp: str, sentences):
    matches = [s for s in sentences if kp in s]
    if not matches:
        return ""
    return min(matches, key=len)


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def make_fill(kp: str, sent: str):
    if sent and kp in sent:
        q = clean_text(sent.replace(kp, "____", 1))
        if len(q) >= 6:
            return {
                "type": "fill",
                "question": q,
                "answer": [kp],
                "explanation": clean_text(sent),
            }
    return {
        "type": "fill",
        "question": "根据材料，补全下列知识点：____",
        "answer": [kp],
        "explanation": f"材料对应知识点：{kp}",
    }


def make_single(kp: str, distractors):
    if len(distractors) < 3:
        return None
    options = [kp] + distractors[:3]
    return {
        "type": "single",
        "question": "根据材料，下列说法正确的是哪一项？",
        "options": options,
        "answer": [0],
        "explanation": f"正确答案为：{kp}",
    }


def make_multiple(kp1: str, kp2: str):
    options = [kp1, kp2, f"未提及：{kp1[:10]}", f"未提及：{kp2[:10]}"]
    return {
        "type": "multiple",
        "question": "根据材料，下列说法正确的有（多选）？",
        "options": options,
        "answer": [0, 1],
        "explanation": f"材料涉及：{kp1}；{kp2}",
    }


def make_judge(kp: str):
    return {
        "type": "judge",
        "question": kp,
        "answer": [1],
        "explanation": "该表述在材料中出现，判断为正确。",
    }


def write_js(quiz_file: str, fill_qs, single_qs, multiple_qs, judge_qs):
    lines = ["const quizData = ["]
    lines.append(f"  {{ type: 'info', info: '【填空题 共{len(fill_qs)}题，每题1分】' }},")
    for q in fill_qs:
        ans = json.dumps(q["answer"], ensure_ascii=False)
        lines.append(f"  {{ type: 'fill', question: '{esc(q['question'])}', answer: {ans}, explanation: '{esc(q['explanation'])}' }},")

    lines.append(f"  {{ type: 'info', info: '【单选题 共{len(single_qs)}题，每题1分】' }},")
    for q in single_qs:
        ans = json.dumps(q["answer"], ensure_ascii=False)
        opts = json.dumps(q["options"], ensure_ascii=False)
        lines.append(f"  {{ type: 'single', question: '{esc(q['question'])}', options: {opts}, answer: {ans}, explanation: '{esc(q['explanation'])}' }},")

    lines.append(f"  {{ type: 'info', info: '【多选题 共{len(multiple_qs)}题，每题1分】' }},")
    for q in multiple_qs:
        ans = json.dumps(q["answer"], ensure_ascii=False)
        opts = json.dumps(q["options"], ensure_ascii=False)
        lines.append(f"  {{ type: 'multiple', question: '{esc(q['question'])}', options: {opts}, answer: {ans}, explanation: '{esc(q['explanation'])}' }},")

    lines.append(f"  {{ type: 'info', info: '【判断题 共{len(judge_qs)}题，每题1分】' }},")
    for q in judge_qs:
        ans = json.dumps(q["answer"], ensure_ascii=False)
        lines.append(f"  {{ type: 'judge', question: '{esc(q['question'])}', answer: {ans}, explanation: '{esc(q['explanation'])}' }},")

    lines[-1] = lines[-1].rstrip(",")
    lines.append("];\n")

    out_path = BASE_PATH / "online_quiz" / quiz_file
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_html(html_file: str, js_file: str, title: str):
    html = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"style.css\">
</head>
<body>
  <div id=\"quiz-container\"></div>
  <script src=\"{js_file}\"></script>
  <script src=\"main.js\"></script>
</body>
</html>
"""
    (BASE_PATH / "online_quiz" / html_file).write_text(html, encoding="utf-8")


def generate_kp_driven_quiz(theme_name: str, material_file: str, quiz_file: str):
    print("\n" + "=" * 70)
    print(f"  主题: {theme_name}  →  {quiz_file}")
    print("=" * 70)

    kps = load_knowledge_points(theme_name)
    material = load_material(material_file)
    sentences = build_sentence_index(material)

    if not kps:
        print("  ⚠️ 未读取到知识点")
        return 0.0

    kp_texts = [kp for kp, _ in kps]

    # 保证覆盖：先按顺序切片分配，剩余用判断题覆盖
    i = 0
    fill_slice = kp_texts[i:i+40]
    i += len(fill_slice)
    single_slice = kp_texts[i:i+40]
    i += len(single_slice)

    remain = kp_texts[i:]
    multiple_pairs = []
    j = 0
    while j + 1 < len(remain) and len(multiple_pairs) < 20:
        multiple_pairs.append((remain[j], remain[j+1]))
        j += 2
    used_in_multiple = {x for p in multiple_pairs for x in p}

    remain_after_multiple = [x for x in remain if x not in used_in_multiple]
    judge_slice = remain_after_multiple[:]
    if len(judge_slice) < 20:
        need = 20 - len(judge_slice)
        judge_slice += kp_texts[:need]

    fill_qs = [make_fill(kp, find_sentence_for_kp(kp, sentences)) for kp in fill_slice]

    single_qs = []
    for kp in single_slice:
        d = [x for x in kp_texts if x != kp][:3]
        q = make_single(kp, d)
        if q:
            single_qs.append(q)

    multiple_qs = [make_multiple(a, b) for a, b in multiple_pairs]
    judge_qs = [make_judge(kp) for kp in judge_slice]

    used = set(fill_slice) | set(single_slice) | used_in_multiple | set(judge_slice)
    coverage = len(used) / len(kp_texts) * 100

    print(f"  知识点总数: {len(kp_texts)}")
    print(f"  材料句子数: {len(sentences)}")
    print(f"\n  覆盖率: {len(used)}/{len(kp_texts)} = {coverage:.1f}%")
    print(f"  填空:{len(fill_qs)} 单选:{len(single_qs)} 多选:{len(multiple_qs)} 判断:{len(judge_qs)}")

    write_js(quiz_file, fill_qs, single_qs, multiple_qs, judge_qs)
    total = len(fill_qs) + len(single_qs) + len(multiple_qs) + len(judge_qs)
    print(f"  ✅ 输出: {quiz_file}  ({total} 题)")
    return coverage


def main():
    run_themes = [
        ("军事", "军事.txt", "军事模拟_新版.js", "军事模拟（新版）"),
        ("国际要闻", "国际要闻.txt", "国际要闻模拟_新版.js", "国际要闻模拟（新版）"),
        ("环保", "环保.txt", "环保模拟_新版.js", "环保模拟（新版）"),
        ("十五五", "十五五.txt", "十五五模拟_新版.js", "十五五模拟（新版）"),
        ("探究性专题", "探究性专题.txt", "探究性专题模拟_新版.js", "探究性专题模拟（新版）"),
        ("热点论坛", "热点论坛.txt", "热点论坛模拟_新版.js", "热点论坛模拟（新版）"),
        ("文体", "文体.txt", "文体模拟_新版.js", "文体模拟（新版）"),
        ("科技", "科技.txt", "科技模拟_新版.js", "科技模拟（新版）"),
    ]

    results = {}
    for theme, mat, js_file, title in run_themes:
        rate = generate_kp_driven_quiz(theme, mat, js_file)
        results[theme] = rate
        html_file = js_file.replace(".js", ".html")
        write_html(html_file, js_file, title)
        print(f"  ✅ 页面: {html_file}")

    print("\n" + "=" * 70)
    print("汇总")
    for theme, rate in results.items():
        flag = "✅" if rate >= 80 else "⚠️"
        print(f"  {flag} {theme}: {rate:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
