---
name: exam-style-kp-annotation
user-invocable: true
description: "Use when: rebuilding knowledge points from sample papers and materials so points are contextual (not isolated keywords), exam-ready, and priority-aware (pre-2025 date/event low priority). Keywords: 考点整理, 样题, 真题, 文体, 上下文"
---

# Exam-Style Knowledge Point Annotation

## Purpose

Convert raw material text into exam-ready knowledge points that match real paper style.

Core fix target:
- Reject isolated keywords.
- Use contextual point sentences with clear exam value.

## Sample-Derived Principles

From 2015真题 + 样题 + 样题2, real points and questions follow these patterns:

1. Point granularity:
- One point = one complete fact unit.
- Preferred structure: event + subject + action/result + key qualifier (time/place/number/significance).

2. Questionability:
- Every point should be directly testable by at least one common type:
  - fill blank (exact term/date/number)
  - single choice (唯一正确事实)
  - multiple choice (并列事实组)
  - judge (事实真伪)
- If a sentence contains both date and event subject, keep the event subject explicit so later question generation can choose the central tested keyword.

3. Distractor-friendly formatting:
- Keep entity type explicit to support plausible distractors:
  - 人名, 地名, 机构名, 时间, 数值, 政策表述, 主题口号, 历史意义
- For numeric points, keep number and unit clearly separable to support numeric-only answers in later question generation.
  - Preferred: "达到36亿千瓦" (not ambiguous writing that hides unit boundary)
  - Preferred: "下降7%-10%" / "达到30%以上"

4. Anti-fragment rule:
- Forbidden as standalone points:
  - truncated titles
  - broken phrases
  - meaningless nouns without predicate
  - page metadata or editorial strings

5. Extraction-friendly writing rule:
- A good point should expose one or more complete exam-usable key items:
  - 主体 / 机构 / 事件名称
  - 制度名称 / 主题口号 / 规范标题
  - 完整时间 / 数值 / 地点
- Prefer sentences where the core object is explicit, so later blanks can ask for "西夏陵" rather than only the accompanying date.
- For numeric expressions, ensure the phrase can be transformed into "____ + 固定单位" style stems.

## Priority Rule (Mandatory)

- Non-date conceptual points: High priority by default.
- Date/event points with explicit year:
  - year < 2025 => low priority
  - year >= 2025 => high priority
- If a point includes both concept and old date, split into two points:
  - conceptual statement => high
  - old-date occurrence => low

## Output Schema For Knowledge Point Files

Recommended markdown sections:

1. 核心高优先级考点（事件-主体-动作-意义）
2. 高频数字与时间锚点（2025+）
3. 术语与制度性表述
4. 上海地方文体融合考点
5. 低优先级日期/事件（2025年前）

Point writing style:
- Use full Chinese sentence fragments with context.
- Keep each point concise, usually 18-60 Chinese chars.
- Each point should stand alone without relying on previous bullet.

## Question Construction Templates

Fill blank:
- 联合国教科文组织国际STEM教育研究所于2025年9月21日在____正式成立。
- 第十五届全运会由____首次联合举办。
- 当地时间2025年7月11日，第47届世界遗产大会表决通过____列入《世界遗产名录》。
- 中国提出到2035年风电和太阳能发电总装机容量力争达到____亿千瓦。
- 中国提出到2035年非化石能源消费占比达到____%以上。

Single choice:
- 下列关于西夏陵列入《世界遗产名录》的表述，正确的是（ ）。

Multiple choice:
- 关于2025年上海“体育+文旅”实践，下列说法正确的有（ ）。

Judge:
- 2025年成都世运会是中国大陆首次承办的非奥运项目国际综合性赛事。（ ）

## Workflow

1. Read all sample papers and current theme material.
2. Extract candidate facts as full context units (not words).
3. Remove noise and de-duplicate by semantic meaning.
4. Apply priority rule (pre-2025 date/event low; others high).
5. Organize by exam-usable sections.
6. Quick self-check:
- no isolated keyword points
- no page/editor metadata
- each point questionable
- priority labels consistent
- core object/entity is explicit when present in the source fact
- numeric point text supports "unit in stem, number-only answer" conversion
