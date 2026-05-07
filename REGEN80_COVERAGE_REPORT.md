# 覆盖度驱动重生成报告

## 当前目录结构与主用流程（统一口径）

- 主目录：materials/（原始素材）、knowledge_points/（最新知识点标注）、online_quiz/（在线页面与题库）、tools/（生成与评估脚本）。
- 主用题库：online_quiz/*_quiz_kpdriven.js（知识点驱动版本）。
- 主用页面：online_quiz/*_quiz_kpdriven.html 或中文 *模拟.html 页面。
- 生成主流程：维护 knowledge_points/*_知识点标注.md -> 运行 tools/kp_driven_quiz_generator.py -> 输出到 online_quiz/。
- 历史/对照题库：*_quiz_data.js、*_quiz_priority.js、*_quiz_priority_regen80.js 可保留用于对照，但默认以 kpdriven 为准。

