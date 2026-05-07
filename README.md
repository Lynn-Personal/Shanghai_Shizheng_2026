# 在线竞赛模拟问答工具

## 项目目标

本项目用于在线竞赛备赛，核心用途包括：
- 竞赛复习
- 知识点检查
- 知识巩固

## 目录结构（当前）

```text
Shanghai_Shizheng_2026/
├─ materials/                      # 原始素材（8个主题）
├─ question_examples/              # 样题与题型参考
├─ knowledge_points/               # 主题知识点标注（最新维护）
│  ├─ 军事_知识点标注.md
│  ├─ 十五五_知识点标注.md
│  ├─ 国际要闻_知识点标注.md
│  ├─ 探究性专题_知识点标注.md
│  ├─ 文体_知识点标注.md
│  ├─ 热点论坛_知识点标注.md
│  ├─ 环保_知识点标注.md
│  └─ 科技_知识点标注.md
├─ online_quiz/                    # 在线答题页面与题库
│  ├─ index.html
│  ├─ main.js
│  ├─ style.css
│  ├─ *_模拟.html                  # 中文主题入口页
│  ├─ *_quiz_data.js               # 基础题库
│  ├─ *_quiz_priority.js           # 优先级版本题库
│  ├─ *_quiz_priority_regen80.js   # regen80版本题库
│  ├─ *_quiz_kpdriven.js           # 知识点驱动版本题库（当前主用）
│  └─ *_quiz_kpdriven.html         # 知识点驱动版本页面
├─ tools/                          # 题库生成、评估、清洗脚本
├─ .github/skills/                 # 可复用技能定义
├─ README.md
└─ 各类评估/报告 .md
```

说明：
- 当前推荐使用 `knowledge_points/` + `online_quiz/*_quiz_kpdriven.js` 作为主流程。
- `*_quiz_data.js`、`*_quiz_priority.js`、`*_quiz_priority_regen80.js` 为历史或对照版本，可并行保留。

## 题型与规则

每套模拟试题包含四种题型：
- 单选题（Single Choice）
- 多选题（Multiple Choice，至少两个正确答案）
- 判断题（True/False）
- 填空题（Fill-in-the-Blank）

每套试题总计 100 题，题量结构固定为：
- 20 道单选题
- 20 道多选题
- 20 道判断题
- 40 道填空题

## 出题依据

### 1) 题目形式参考
题型呈现形式参考 `question_examples/`：
- `question_examples/单选.png`
- `question_examples/多选.png`
- `question_examples/判断.png`
- `question_examples/填空.png`

### 2) 出题深度与考点参考
出题方式、难度深度和考察点参考：
- `question_examples/2025时政大赛样题.pdf`

### 3) 知识素材来源
竞赛素材在 `materials/`，共 8 个主题：
- `materials/十五五.txt`
- `materials/军事.txt`
- `materials/国际要闻.txt`
- `materials/探究性专题.txt`
- `materials/文体.txt`
- `materials/热点论坛.txt`
- `materials/环保.txt`
- `materials/科技.txt`

## 生成要求

需要为以上 8 个主题分别生成一套模拟试题，并满足：
- 每个主题 1 套
- 每套 100 题
- 题型数量满足 20/20/20/40（单选/多选/判断/填空）
- 考点尽可能覆盖主题材料中的全部核心知识点

## 运行方式

当前在线答题页面位于 `online_quiz/`。
可直接在浏览器打开对应 HTML 文件开始作答，例如：
- `online_quiz/十五五模拟.html`
- `online_quiz/军事模拟.html`
- `online_quiz/文体模拟.html`

如需使用知识点驱动版本，可直接打开对应页面，例如：
- `online_quiz/wenti_quiz_kpdriven.html`
- `online_quiz/environment_quiz_kpdriven.html`
- `online_quiz/international_quiz_kpdriven.html`

页面会自动加载对应题库数据与答题逻辑：
- `online_quiz/main.js`
- `online_quiz/style.css`

## 实现方式

本应用采用“静态页面 + 题库数据文件”的实现方式，便于快速扩展主题与维护。

### 1) 页面与渲染逻辑分离
- 每个主题一个 HTML 页面（例如 `online_quiz/十五五模拟.html`、`online_quiz/军事模拟.html`）。
- 页面只负责加载公共样式和脚本，不硬编码题目。
- 公共交互逻辑统一在 `online_quiz/main.js`：
	- 题目渲染
	- 提交判分
	- 正确答案与解析展示
	- 错题收集与重做

### 2) 题库数据驱动
- 每个主题对应一个题库 JS 文件（如 `quiz_data.js`、`military_quiz_data.js`、`wenti_quiz_data.js`）。
- 题库统一导出 `const quizData = [...]`。
- 支持四种题型：
	- `fill` 填空题
	- `single` 单选题
	- `multiple` 多选题
	- `judge` 判断题

### 3) 统一数据结构
- 填空题：`type`、`question`、`answer`、`explanation`
- 单选题：`type`、`question`、`options`、`answer`、`explanation`
- 多选题：`type`、`question`、`options`、`answer`、`explanation`
- 判断题：`type`、`question`、`answer`、`explanation`

## Skills 与用法

为便于后续批量扩题，项目已内置一个可复用 Skill：
- `.github/skills/full-coverage-quiz-generator/SKILL.md`

### Skill 作用
- 从 `materials/*.txt` 自动抽取考点并生成在线题库。
- 默认采用“全覆盖”策略：
	- 40 填空
	- 40 单选
	- 20 多选
	- 20 判断
	- 共 120 题
- 当考点超过 120 时，按 4:4:2:2 比例继续扩展题量。

### 与本项目初始 requirement 的关系
- 初始 requirement 为每套 100 题（20/20/20/40）。
- 当前 Skill 偏向“满覆盖优先”并默认 120 题。
- 如需严格按 100 题执行，请在使用时明确指定 20/20/20/40。

### 推荐提示词模板

1) 严格 100 题模式（符合初始 requirement）

`请读取 materials/环保.txt，参考 question_examples/2025时政大赛样题.pdf 和四类题型图片，生成 online_quiz/环保模拟.html 与 online_quiz/environment_quiz_data.js。题量严格为：填空40、单选20、多选20、判断20，总计100题，并尽可能覆盖全部核心考点。`

2) 满覆盖扩展模式（Skill 默认风格）

`请使用 full-coverage-quiz-generator 处理 materials/科技.txt：先抽取原子考点并建立覆盖矩阵，再生成 online_quiz/科技模拟.html 与 online_quiz/tech_quiz_data.js。默认40/40/20/20，若考点超过120按4:4:2:2扩展。`

### 生成后的自检清单
- 题量是否与目标一致（100 题或扩展题量）。
- 四种题型是否齐全。
- `info` 分段标题题量是否和真实题数一致。
- 是否只有一个 `const quizData` 定义。
- 页面脚本引用是否正确（题库 JS + `main.js`）。
- 题目是否覆盖材料核心时间、人物、地点、数字、政策表述。

## 维护建议

- 新增主题时，优先复用现有页面骨架与题库 schema，避免改动 `main.js`。
- 保持题库文件命名稳定（建议 `*_quiz_data.js`），便于批量管理。
- 若后续统一为“严格 100 题”，可再新增一个 standard skill（20/20/20/40 固定）与 full-coverage skill 并行。

## 后续扩展建议

- 按统一规则补齐其余 5 个主题的题库与页面。
- 增加题库校验脚本（检查题量、题型比例、答案合法性、重复题）。
- 增加“错题导出/打印”“按题型训练”“随机组卷”等功能。
