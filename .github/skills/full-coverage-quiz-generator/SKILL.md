---
name: full-coverage-quiz-generator
user-invocable: true
description: "Use when: generating online quiz sets from materials/*.txt into full-coverage Chinese policy/current-affairs mock exams with four question types and strict coverage accounting. Keywords: 模拟题, 全覆盖, 填空40, 单选40, 多选20, 判断20, 文体, 军事, 十五五"
---

# Full Coverage Quiz Generator

## Purpose

Generate theme-based mock quizzes from raw txt materials and output files compatible with the existing online quiz runner.

Target output format:
- Fill-in: 40
- Single-choice: 40
- Multiple-choice: 20
- True/False: 20
- Total default: 120 questions

If knowledge points exceed 120, expand question counts while preserving the 4:4:2:2 ratio as much as possible.

## Input And Output

Input:
- Source material txt under materials/, for example materials/文体.txt

Output:
- online_quiz/<主题>模拟.html
- online_quiz/<theme>_quiz_data.js

Compatibility requirement:
- Must match existing structure used by online_quiz/main.js and online_quiz/style.css.

## Workflow

### 0) Prepare And Clean Material (新增步骤)

Before extracting knowledge points, clean the source material to remove non-knowledge content:

Actions:
1. Remove headers and metadata lines containing:
   - 编辑信息 (editor names, emails)
   - 页码标记 (page numbers like "第38页")
   - 栏目标题 (section titles like "新闻现场", "背景资料")
   - 水印和说明文字 (watermarks and instructional text)

2. Filter keywords to exclude:
   - 专题、大赛、报刊名称 (column/competition names)
   - 导出、复制、PDF等说明 (export/download instructions)
   - "我已完整"、"无法直接"等第一人称说明

3. Consolidate multiline content:
   - Remove excessive line breaks
   - Normalize spacing to single spaces between sentences
   - Keep Chinese punctuation intact

Output: Cleaned material file ready for knowledge point extraction

Tool: `python tools/material_cleaner.py` (optional step before generation)

### 1) Build Knowledge Point Inventory

Read the source txt and extract atomic knowledge points as K001, K002, ...

Each atomic point should be one fact only, such as:
- time
- place
- person
- number
- concept definition
- policy expression
- list item
- comparison or distinction

Do not merge unrelated facts into one point.

### 2) De-duplicate And Normalize

Normalize variants of the same fact and keep one canonical expression.

Example normalization:
- numeric formats (118万人, 1.18 million) -> one canonical Chinese format
- date formats (2025年9月21日) -> keep full Chinese date

### 3) Coverage Matrix (Mandatory)

Create a coverage table before writing questions:
- every knowledge point Kxxx must appear at least once in the final set
- important points (time/place/number/core policy wording) should appear at least twice across different question types

Coverage target:
- 100 percent point coverage

### 4) Decide Question Counts

Default counts:
- Fill 40
- Single 40
- Multiple 20
- Judge 20

If point_count > 120:
1. extra = point_count - 120
2. Add by ratio 4:4:2:2
3. Use this increment rule:
   - fill_add = ceil(extra * 4 / 12)
   - single_add = ceil(extra * 4 / 12)
   - multiple_add = ceil(extra * 2 / 12)
   - judge_add = ceil(extra * 2 / 12)
4. Final counts:
   - fill = 40 + fill_add
   - single = 40 + single_add
   - multiple = 20 + multiple_add
   - judge = 20 + judge_add
5. If total expanded count is still below point_count, keep adding to single and fill first until total >= point_count.

### 5) Write Questions By Type

General constraints:
- Chinese language, concise and exam-ready
- no ambiguous correct answers
- explanations are short and factual
- no fabricated facts beyond source txt

Fill-in constraints:
- one to three blanks
- expected answers must be precise and short
- answers should be strings in answer array

Single-choice constraints:
- exactly four options
- exactly one correct option index in answer array
- distractors must be plausible but clearly wrong

Multiple-choice constraints:
- exactly four options
- at least two correct options
- answer indices sorted ascending

Judge constraints:
- statement must be clearly true or false per source
- avoid subjective wording

### 6) Output File Structure

The js file must define:
- const quizData = [ ... ]

Section headers must use info items:
- 【填空题 共X题，每题2分】
- 【单项选择题 共Y题，每题2分】
- 【多项选择题 共Z题，每题3分】
- 【判断题 共W题，每题1分】

Each question object must match existing schema:
- fill: type, question, answer, explanation
- single: type, question, options, answer, explanation
- multiple: type, question, options, answer, explanation
- judge: type, question, answer, explanation

### 7) HTML Page Generation

Create theme page based on existing simulator pages:
- include style.css
- include generated <theme>_quiz_data.js
- include main.js

### 8) Final Validation Checklist

Run all checks before completion:
- schema compatibility with main.js
- no duplicate const quizData declaration
- section counts match real counts
- all knowledge points covered in coverage table
- no syntax errors in generated js/html

## Quality Bar

A result is acceptable only if all are true:
- point coverage is 100 percent
- core points are repeated in at least two question types
- question quality is unambiguous
- files are directly runnable in online_quiz

## Quick Execution Prompt

When invoked, use this execution pattern:

"1. Clean materials/<主题>.txt by removing watermarks and metadata (using material_cleaner.py or manual filtering).
2. Read cleaned material, extract atomic knowledge points with IDs, build coverage matrix.
3. Generate online_quiz/<主题>模拟.html and online_quiz/<theme>_quiz_data.js with full coverage.
4. Use default 40/40/20/20 unless point count exceeds 120, then expand by 4:4:2:2 rule.
5. Validate schema/count/syntax before finishing."
