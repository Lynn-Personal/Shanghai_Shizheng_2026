#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

BASE_PATH = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
GEN_PATH = BASE_PATH / "tools" / "exam_style_quiz_generator.py"


def load_gen_module():
    spec = importlib.util.spec_from_file_location("exam_gen", str(GEN_PATH))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def is_2025_date_value(gen, v: str) -> bool:
    text = gen.clean_text(str(v))
    if gen.answer_type(text) != "date":
        return False
    return bool(re.match(r"^2025年(?:\d{1,2}月(?:\d{1,2}日)?)?$", text))


def is_leader_value(gen, v: str) -> bool:
    text = gen.clean_text(str(v))
    leader_keywords = [
        "习近平", "特朗普", "拜登", "普京", "泽连斯基", "马克龙", "莫迪",
        "石破茂", "冯德莱恩", "内塔尼亚胡", "尹锡悦", "岸田文雄",
    ]
    if any(k in text for k in leader_keywords):
        return True
    return bool(re.fullmatch(r"[\u4e00-\u9fff]{2,6}(?:主席|总统|总理|首相)", text))


def filter_specs(gen, theme: str, specs: list[dict]) -> list[dict]:
    pool = specs[:]
    if theme in ("国际要闻", "探究性专题"):
        pool = [s for s in pool if not is_leader_value(gen, s["answer"]) and not is_2025_date_value(gen, s["answer"]) ]
    elif theme == "十五五":
        pool = [s for s in pool if s["answer_type"] != "date"]
    return pool if pool else specs


def fill_key(q: dict) -> tuple:
    return (q["question"], tuple(q["answer"]))


def single_key(q: dict) -> tuple:
    return (q["question"], tuple(q["options"]), tuple(q["answer"]))


def multiple_key(q: dict) -> tuple:
    return (q["question"], tuple(q["options"]), tuple(q["answer"]))


def judge_key(q: dict) -> tuple:
    return (q["question"], tuple(q["answer"]))


def dedupe(qs: list[dict], key_fn):
    out = []
    seen = set()
    for q in qs:
        k = key_fn(q)
        if k in seen:
            continue
        seen.add(k)
        out.append(q)
    return out


def generate_theme_v2(gen, theme: str):
    kps = gen.load_kps(theme)
    ctx = {kp: kp for kp in kps}
    gap_specs = [spec for kp in kps if (spec := gen.extract_gap_spec(ctx[kp]))]
    if not gap_specs:
        raise RuntimeError(f"主题 {theme} 未提取到可命题的关键信息")

    preferred_specs = filter_specs(gen, theme, gap_specs)

    # Phase 1: build fill questions from all suitable specs (no fixed 40 cap).
    fill_qs: list[dict] = []
    used_fill = set()
    used_kps = set()
    for spec in preferred_specs + gap_specs:
        q = gen.make_fill(spec)
        if not q:
            continue
        k = fill_key(q)
        if k in used_fill:
            continue
        fill_qs.append(q)
        used_fill.add(k)
        used_kps.add(spec["kp"])

    # Phase 2: build single-choice questions from all specs with new KPs first.
    single_qs: list[dict] = []
    used_single = set()
    ordered_single_specs = sorted(preferred_specs + gap_specs, key=lambda s: (s["kp"] in used_kps,))
    for spec in ordered_single_specs:
        cand = gen.make_single(spec, gap_specs)
        if cand:
            k = single_key(cand)
            if k not in used_single:
                single_qs.append(cand)
                used_single.add(k)
                used_kps.add(spec["kp"])

    # Phase 3: build multiple-choice questions (covers two KPs each), not capped at 20.
    multiple_qs: list[dict] = []
    used_multiple = set()
    ordered_multi_specs = sorted(preferred_specs + gap_specs, key=lambda s: (s["kp"] in used_kps,))
    for idx in range(0, len(ordered_multi_specs) - 1, 2):
        a = ordered_multi_specs[idx]
        b = ordered_multi_specs[idx + 1]
        if a["kp"] == b["kp"]:
            continue
        cand = gen.make_multiple(a, b, gap_specs)
        if not cand:
            continue
        k = multiple_key(cand)
        if k in used_multiple:
            continue
        multiple_qs.append(cand)
        used_multiple.add(k)
        used_kps.add(a["kp"])
        used_kps.add(b["kp"])

    # A second pass with shifted pairs adds variety when possible.
    for idx in range(1, len(ordered_multi_specs) - 1, 2):
        a = ordered_multi_specs[idx]
        b = ordered_multi_specs[idx + 1]
        if a["kp"] == b["kp"]:
            continue
        cand = gen.make_multiple(a, b, gap_specs)
        if not cand:
            continue
        k = multiple_key(cand)
        if k in used_multiple:
            continue
        multiple_qs.append(cand)
        used_multiple.add(k)
        used_kps.add(a["kp"])
        used_kps.add(b["kp"])

    # Phase 4: judge questions.
    # Keep at least 20 for exam shape; then append uncovered KPs to push coverage near 100%.
    judge_qs: list[dict] = []
    used_judge = set()
    for kp in kps:
        q = gen.make_judge(kp, ctx[kp])
        k = judge_key(q)
        if k in used_judge:
            continue
        judge_qs.append(q)
        used_judge.add(k)
        if len(judge_qs) >= 20:
            break

    # Mark currently covered KPs from explanations we intentionally built.
    covered = set(used_kps)
    for i in range(min(20, len(kps))):
        covered.add(kps[i])

    # Append uncovered KPs as extra judge questions (v2 high-coverage mode).
    missing = [kp for kp in kps if kp not in covered]
    for kp in missing:
        q = gen.make_judge(kp, ctx[kp])
        k = judge_key(q)
        if k in used_judge:
            continue
        judge_qs.append(q)
        used_judge.add(k)
        covered.add(kp)

    fill_qs = dedupe(fill_qs, fill_key)
    single_qs = dedupe(single_qs, single_key)
    multiple_qs = dedupe(multiple_qs, multiple_key)
    judge_qs = dedupe(judge_qs, judge_key)

    js_name = f"{theme}模拟_第2版_真题风格.js"
    html_name = f"{theme}模拟_第2版_真题风格.html"
    js_path = BASE_PATH / "online_quiz" / js_name
    html_path = BASE_PATH / "online_quiz" / html_name

    gen.write_js(js_path, fill_qs, single_qs, multiple_qs, judge_qs)
    gen.write_html(html_path, f"{theme}模拟（第2版·真题风格·高覆盖）", js_name)

    # strict output coverage from explanations
    js_text = js_path.read_text(encoding="utf-8")
    refs = {gen.clean_text(x) for x in re.findall(r"(?:材料对应表述|正确项对应材料考点|依据考点)：([^。']+)", js_text)}
    kp_set = set(kps)
    hit = len(kp_set & refs)
    cov = hit / len(kps) * 100 if kps else 0

    print(f"主题: {theme}")
    print(f"知识点总数: {len(kps)}")
    print(f"输出JS: {js_name}")
    print(f"输出HTML: {html_name}")
    print(f"题量: 填空{len(fill_qs)} 单选{len(single_qs)} 多选{len(multiple_qs)} 判断{len(judge_qs)}")
    print(f"覆盖率(解释命中): {hit}/{len(kps)} = {cov:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Generate v2 high-coverage exam-style quizzes.")
    parser.add_argument("themes", nargs="+", help="Theme names, e.g. 探究性专题 科技 环保")
    args = parser.parse_args()

    gen = load_gen_module()
    for t in args.themes:
        generate_theme_v2(gen, t)


if __name__ == "__main__":
    main()
