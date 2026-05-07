#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖度驱动的题库重生成工具
1) 评估当前8个主题模拟题对知识点覆盖度
2) 覆盖度<80%的主题，生成新的题库文件（不覆盖旧文件）
3) 对新题库逐题清洗，移除 page1 等无效文字并增强可读性
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

from priority_aware_quiz_generator import PriorityAwareQuizGenerator


THEMES = [
    ("科技", "科技.txt", "technology_quiz_data.js", "technology_quiz_priority.js"),
    ("十五五", "十五五.txt", "wenti_quiz_data.js", "wenti_quiz_priority.js"),
    ("军事", "军事.txt", "military_quiz_data.js", "military_quiz_priority.js"),
    ("国际要闻", "国际要闻.txt", "international_quiz_data.js", "international_quiz_priority.js"),
    ("探究性专题", "探究性专题.txt", "inquiry_quiz_data.js", "inquiry_quiz_priority.js"),
    ("文体", "文体.txt", "culture_quiz_data.js", "culture_quiz_priority.js"),
    ("热点论坛", "热点论坛.txt", "forum_quiz_data.js", "forum_quiz_priority.js"),
    ("环保", "环保.txt", "environment_quiz_data.js", "environment_quiz_priority.js"),
]


class CoverageDrivenRegenerator:
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.quiz_dir = self.base_path / "online_quiz"
        self.knowledge_dir = self.base_path / "knowledge_points"
        self.materials_dir = self.base_path / "materials"
        self.threshold = 80.0

        self.invalid_patterns = [
            re.compile(r"page\s*\d+", re.IGNORECASE),
            re.compile(r"第\s*\d+\s*页"),
            re.compile(r"新闻现场", re.IGNORECASE),
            re.compile(r"责任编辑", re.IGNORECASE),
            re.compile(r"美术编辑", re.IGNORECASE),
            re.compile(r"邮箱", re.IGNORECASE),
            re.compile(r"一键复制|导出为PDF|Typora|Markdown编辑器", re.IGNORECASE),
        ]

    def choose_current_quiz(self, normal_file: str, priority_file: str) -> Path:
        """优先使用当前常用的 priority 题库，其次标准题库。"""
        priority_path = self.quiz_dir / priority_file
        normal_path = self.quiz_dir / normal_file
        if priority_path.exists():
            return priority_path
        return normal_path

    def load_knowledge_points(self, theme_name: str) -> List[str]:
        kp_file = self.knowledge_dir / f"{theme_name}_知识点标注.md"
        if not kp_file.exists():
            return []

        points = []
        with open(kp_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- ") and not line.startswith("- **"):
                    point = line[2:].strip()
                    if len(point) >= 2:
                        points.append(point)
        return points

    def extract_question_texts(self, quiz_path: Path) -> List[str]:
        if not quiz_path.exists():
            return []

        content = quiz_path.read_text(encoding="utf-8")

        # question 字段
        questions = re.findall(r"question:\s*'((?:\\'|[^'])*)'", content)
        texts = [q.replace("\\'", "'") for q in questions if len(q.strip()) > 0]

        # options 字段
        options_blocks = re.findall(r"options:\s*\[(.*?)\],\s*answer:", content, re.DOTALL)
        for block in options_blocks:
            opts = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', block)
            for opt in opts:
                if opt.strip():
                    texts.append(opt)

        # explanation 字段
        exps = re.findall(r"explanation:\s*'((?:\\'|[^'])*)'", content)
        texts.extend([e.replace("\\'", "'") for e in exps if len(e.strip()) > 0])

        return texts

    def calculate_coverage(self, texts: List[str], knowledge_points: List[str]) -> Tuple[int, int, float]:
        if not knowledge_points:
            return 0, 0, 0.0

        covered = 0
        for kp in knowledge_points:
            kp = kp.strip()
            if not kp:
                continue
            if any(kp in t for t in texts):
                covered += 1

        total = len(knowledge_points)
        rate = covered / total * 100 if total else 0.0
        return covered, total, rate

    def sanitize_text(self, text: str) -> str:
        s = text
        for p in self.invalid_patterns:
            s = p.sub("", s)

        # 清理多余空白和标点
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"([，。；：！？])\1+", r"\1", s)
        s = re.sub(r"^[，。；：！？\-_/\s]+", "", s)
        s = re.sub(r"[，。；：！？\-_/\s]+$", "", s)
        return s

    def sanitize_js_quiz_file(self, quiz_path: Path) -> Dict[str, int]:
        content = quiz_path.read_text(encoding="utf-8")

        counters = {
            "question_cleaned": 0,
            "option_cleaned": 0,
            "explanation_cleaned": 0,
            "invalid_token_found_after_clean": 0,
        }

        def replace_question(match):
            old = match.group(1)
            new = self.sanitize_text(old)
            if new != old:
                counters["question_cleaned"] += 1
            if not new:
                new = "请根据材料选择正确表述。"
            return f"question: '{new}'"

        def replace_explanation(match):
            old = match.group(1)
            new = self.sanitize_text(old)
            if new != old:
                counters["explanation_cleaned"] += 1
            if not new:
                new = "该题依据材料内容判断。"
            return f"explanation: '{new}'"

        def replace_options_block(match):
            block = match.group(1)
            opts = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', block)
            new_opts = []
            changed = False
            for opt in opts:
                cleaned = self.sanitize_text(opt)
                if cleaned != opt:
                    changed = True
                    counters["option_cleaned"] += 1
                if not cleaned:
                    cleaned = "与材料一致的表述"
                new_opts.append(cleaned)

            if changed:
                quoted = ", ".join([f'"{o}"' for o in new_opts])
                return f"options: [{quoted}], answer:"
            return match.group(0)

        content = re.sub(r"question:\s*'((?:\\'|[^'])*)'", replace_question, content)
        content = re.sub(r"explanation:\s*'((?:\\'|[^'])*)'", replace_explanation, content)
        content = re.sub(r"options:\s*\[(.*?)\],\s*answer:", replace_options_block, content, flags=re.DOTALL)

        # 最终扫描是否还有无效词
        for p in self.invalid_patterns:
            if p.search(content):
                counters["invalid_token_found_after_clean"] += 1

        quiz_path.write_text(content, encoding="utf-8")
        return counters

    def run(self):
        print("=" * 88)
        print("覆盖度驱动重生成 - 阈值80%（不覆盖旧题库）")
        print("=" * 88)

        generator = PriorityAwareQuizGenerator(self.base_path)
        report_lines = []
        report_lines.append("# 覆盖度驱动重生成报告\n")
        report_lines.append("- 规则: 覆盖度 < 80% 时生成新题库文件，不覆盖原文件")
        report_lines.append("- 质量要求: 清洗 page1/第X页 等无效文字并复检\n")
        report_lines.append("| 主题 | 当前题库 | 当前覆盖率 | 是否重生成 | 新题库 | 新覆盖率 | 清洗结果 |")
        report_lines.append("|------|---------|-----------:|-----------|--------|----------:|----------|")

        total_regenerated = 0

        for theme_name, material_name, normal_js, priority_js in THEMES:
            current_quiz = self.choose_current_quiz(normal_js, priority_js)
            knowledge_points = self.load_knowledge_points(theme_name)
            current_texts = self.extract_question_texts(current_quiz)
            _, _, current_rate = self.calculate_coverage(current_texts, knowledge_points)

            regenerate = current_rate < self.threshold
            new_file = "-"
            new_rate = current_rate
            clean_msg = "-"

            if regenerate:
                material_path = self.materials_dir / material_name
                stem = current_quiz.stem
                new_file = f"{stem}_regen80.js"

                # 生成新题库（不会覆盖旧题库）
                generator.generate_js_quiz(material_path, new_file, theme_name, target_questions=120)
                new_quiz_path = self.quiz_dir / new_file

                # 清洗并复检
                clean_stats = self.sanitize_js_quiz_file(new_quiz_path)
                new_texts = self.extract_question_texts(new_quiz_path)
                _, _, new_rate = self.calculate_coverage(new_texts, knowledge_points)

                clean_msg = (
                    f"Q{clean_stats['question_cleaned']}/"
                    f"O{clean_stats['option_cleaned']}/"
                    f"E{clean_stats['explanation_cleaned']}/"
                    f"残留{clean_stats['invalid_token_found_after_clean']}"
                )
                total_regenerated += 1

            report_lines.append(
                f"| {theme_name} | {current_quiz.name} | {current_rate:.1f}% | "
                f"{'是' if regenerate else '否'} | {new_file} | {new_rate:.1f}% | {clean_msg} |"
            )

            print(
                f"[{theme_name}] 当前{current_rate:.1f}% -> "
                f"{'已重生成' if regenerate else '无需重生成'}"
            )

        report_lines.append("")
        report_lines.append(f"- 本次重生成主题数: {total_regenerated}")
        report_lines.append("- 新文件命名: *_regen80.js")

        report_path = self.base_path / "REGEN80_COVERAGE_REPORT.md"
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        print("\n" + "=" * 88)
        print(f"✅ 报告已生成: {report_path}")
        print("=" * 88)


def main():
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    CoverageDrivenRegenerator(base_path).run()


if __name__ == "__main__":
    main()
