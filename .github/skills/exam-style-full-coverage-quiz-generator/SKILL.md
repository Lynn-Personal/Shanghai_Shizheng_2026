---
name: exam-style-full-coverage-quiz-generator
user-invocable: true
description: "Use when: generating mock current-affairs quiz sets with real-exam phrasing style from question_examples/2015年真题.txt, 样题.txt, 样题2.txt; enforce contextual stems (no generic blank prompts), four question types, and full knowledge-point coverage. Keywords: 模拟题, 真题问法, 上下文题干, 四种题型, 全覆盖"
---

# Exam-Style Full Coverage Quiz Generator

## Purpose

Generate quiz sets that look and feel like real exam questions, not template-only prompts.

Core quality target:
- Every question stem must include enough context to be answerable.
- Stem wording must be aligned with:
  - question_examples/2015年真题.txt
  - question_examples/样题.txt
  - question_examples/样题2.txt

## Mandatory Input Sources

1. Theme source:
- materials/<主题>.txt

2. Style source (must read before writing questions):
- question_examples/2015年真题.txt
- question_examples/样题.txt
- question_examples/样题2.txt

3. Knowledge-point source:
- knowledge_points/<主题>_知识点标注.md

## Non-Negotiable Rules

1. Contextual stem required
- Every question must include event context (who/what/when/where/policy scene).
- A student should be able to infer what fact is being asked without seeing the answer options.

2. Forbidden low-context stems
- Do NOT produce stems like:
  - "材料中出现的重要日期是____"
  - "材料中的关键词是____"
  - "材料提到的机构是____"
  - "根据材料，下列说法正确的是（ ）" (without topic context)
  - "根据材料，____" / "材料指出，____" when that lead-in is not part of the fact itself

3. Answer content must be complete key information
- The blank or correct option must be a complete keyword / key fact unit, not a broken clause.
- Preferred answer categories:
  - event subject / core object
  - policy / institution / meeting name
  - theme / slogan / quoted formulation
  - complete date / number / title when those are the real exam point
- Forbidden answer forms:
  - arbitrary truncations such as "教育初" or "填补近2"
  - descriptive long clauses when a shorter complete keyword exists

3.2 Core-keyword extraction rule (mandatory)
- Ask only the core keyword/number when the sentence supports it, while keeping sufficient context in stem.
- Typical mandatory patterns:
  - 发布/推出/签署 + X方案/机制/倡议/议定书/宣言 -> ask X core term
  - 发现了X/发现X -> ask X core object
  - 是第X届/第X次 -> ask the ordinal keyword (届次/轮次/次数) when it is the test point
- Keep action structure in stem, do not remove key verb context.
- Example:
  - Good: "2025年6月21日，美国实施____行动，对伊朗核设施实施空袭。" -> answer: "午夜之锤"
  - Bad: "2025年6月21日，____，对伊朗核设施实施空袭。" -> answer: "实施午夜之锤行动"

3.3 Leader-name restriction (mandatory)
- Do not use country leaders' names as primary asked blank/option target.
- Prefer asking location/event/theme/mechanism/significance/number instead.
- If a sentence contains both leader name and event keyword, ask the event keyword.

3.1 Numeric-answer formatting (mandatory)
- For numeric facts, keep the unit in the stem and ask/answer only the numeric part.
- Examples:
  - Preferred: "力争达到____亿千瓦" -> answer: "36"
  - Preferred: "下降____%" -> answer: "7-10"
  - Preferred: "达到____%以上" -> answer: "30"
- Avoid asking with full numeric+unit as answer when unit can be fixed in the stem.

4. Entity-first extraction rule
- When one sentence contains both a date and a core event/entity, prefer the core event/entity as the tested blank when it is the more central knowledge point.
- Example:
  - Better: "当地时间2025年7月11日，第47届世界遗产大会表决通过____列入《世界遗产名录》。"
  - Answer: "西夏陵"
  - Less preferred default: asking only for "2025年7月11日"

4.1 Colon-format KP flipping rule (mandatory)
- KPs in "X：描述" format (term or date before colon, description after) must NOT produce "____：描述" fill questions with a blank at sentence start.
- Instead, flip the question direction using the description as the stem: "描述，即____。" with the term as the answer.
- Examples:
  - KP: "新质生产力：以科技创新和产业升级驱动高质量发展的新型生产力形态。"
    - Bad stem: "____：以科技创新和产业升级驱动高质量发展的新型生产力形态。"
    - Good stem: "以科技创新和产业升级驱动高质量发展的新型生产力形态，即____。"
  - KP: "2025年10月20日至23日：二十届四中全会召开。"
    - Bad stem: "____：二十届四中全会召开。"
    - Good stem (entity-first): "党的____召开并审议通过十五五规划建议。" / rephrase with event context.
- This applies regardless of whether the answer before the colon is a date, number, term, or proper name.

4.2 Date-cap rule for policy/planning themes
- For themes whose KPs are mostly policy text (e.g. 十五五, 环保, 科技), do not let date-answers dominate fill/single/multiple questions.
- Recommended cap: 0 date-answers for fill and single; 0 for multiple.
- Non-date specs must be prioritised in padding/refill loops so that date specs never re-enter after enforcement.

5. Four question types required
- fill
- single
- multiple
- judge

6. Full coverage required
- Every knowledge point must appear at least once in final questions.
- Core time/number/policy points should appear in at least two question types when possible.

7. Distractor quality rule (single/multiple)
- Distractors must prioritize same answer type and close semantic domain.
- Preferred order for distractor selection:
  1) same type + same subtype + same domain
  2) same type + same subtype
  3) same type + same domain
  4) same type
- Enforce option uniqueness (no duplicate options in one question).

8. Reconstruction consistency rule (mandatory)
- For each fill/single/multiple item, the reconstructed statement must match the source fact:
  - fill: question(with blank replaced by answer) == explanation source sentence
  - single: question(with correct option filled) == explanation source sentence
  - multiple: question(with each correct option filled in order) == explanation source sentence
- If reconstruction loses key words (for example missing verb phrase, subject, qualifier, or quoted formulation), revise extraction/stem so the loss is eliminated.
- This rule is strict: do not ship quiz output with reconstruction mismatches.

9. Intra-type de-duplication rule (mandatory)
- No duplicate simulated questions within the same type.
- fill questions must be unique within fill set; single within single; multiple within multiple; judge within judge.
- If balancing/padding introduces duplicates, run final dedupe-and-refill before output.

## Question Style Constraints (Exam-like)

### Fill-in
- Stem must include scene sentence and target slot.
- Do not prepend generic wrappers like "根据材料" unless they are semantically necessary.
- Prefer asking for the event subject / policy name / complete key phrase before asking for a date.
- For numeric points, write the stem as "____ + unit" and keep answers numeric-only.
- Good pattern:
  - "当地时间2025年7月11日，第47届世界遗产大会表决通过____列入《世界遗产名录》。"
  - "2035年我国非化石能源消费占能源消费总量比重达到____%以上。"
  - "到2035年风电和太阳能总装机容量力争达到____亿千瓦。"

### Single-choice
- Must contain topic anchor in stem.
- Good pattern:
  - "关于中国-东盟自贸区3.0版升级议定书，下列说法正确的是（ ）。"

### Multiple-choice
- Use grouped comparison or parallel facts.
- Good pattern:
  - "关于2025年我国生态治理进展，下列说法正确的有（ ）。"

### Judge
- Statement must be specific and verifiable.
- Good pattern:
  - "2025年10月9日，中国发布了针对14种稀土及相关技术的出口管制公告。（ ）"

## Output Contract

Generate:
- online_quiz/<中文主题>模拟_新版.js
- online_quiz/<中文主题>模拟_新版.html

JS schema must remain compatible with online_quiz/main.js:
- fill: type, question, answer, explanation
- single: type, question, options, answer, explanation
- multiple: type, question, options, answer, explanation
- judge: type, question, answer, explanation

## Workflow

1. Read style files first (2015年真题 + 样题 + 样题2).
2. Read and clean material text.
3. Read knowledge points and build coverage checklist.
4. Draft stems using exam-like contextual phrasing.
5. Build four-type question set.
6. Run coverage pass: ensure all points covered.
7. Run per-item stem audit: check each question one by one for missing context or broken key phrase.
8. Run colon-format check: any stem starting with "____：" must be flipped to description-first per Rule 4.1.
9. Run date-cap enforcement: remove/replace date-answer questions per Rule 4.2 for policy themes.
10. Run reconstruction pass: verify "题干 + 正确答案 = 解释中的原始表述" for fill/single/multiple.
11. Run intra-type dedupe pass and refill to required counts (using non-date specs for policy themes).
12. Validate syntax/schema and output files.

## Validation Checklist

- No forbidden generic stems.
- All stems have contextual clues.
- Blanks/options are complete key information, not broken phrases.
- No stem begins with "____：" (colon-format blank at sentence start) — must be flipped per Rule 4.1.
- When date and entity coexist, the chosen blank is the more central tested fact when appropriate.
- Numeric items use stem-with-unit and numeric-only answers/options.
- For policy/planning themes, date-answer questions are removed/replaced before output (Rule 4.2).
- Single/multiple options are unique and distractors are type-consistent.
- Four types all present.
- 100% knowledge-point coverage.
- For fill/single/multiple, stem + correct answer(s) can reconstruct the explanation source sentence exactly (allowing only punctuation/whitespace normalization).
- All questions are checked one by one for stem omissions before final output.
- No duplicate question items within each type (fill/single/multiple/judge).
- Asked blank/answer focuses on core keyword/number (including patterns like 发布/推出/签署+X方案/机制/倡议), not long clauses.
- No leader-name-focused asked blank/option as the primary test point.
- Question text is factual and answerable.
- Output files can run directly with online_quiz/main.js.

## Quick Invocation Prompt

"Use exam-style-full-coverage-quiz-generator for materials/<主题>.txt and knowledge_points/<主题>_知识点标注.md. Read question_examples/2015年真题.txt, 样题.txt, 样题2.txt first. Generate online_quiz/<中文主题>模拟_新版.js and .html with fill/single/multiple/judge, enforce full knowledge-point coverage, one-by-one stem omission audit, no duplicates within each question type, and core-keyword extraction (e.g., 发布/推出/签署+X方案/机制/倡议). Do not use leader names as primary asked blanks."
