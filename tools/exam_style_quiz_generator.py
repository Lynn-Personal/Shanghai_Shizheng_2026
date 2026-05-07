#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exam-style contextual quiz generator (single-theme first).
Produces Chinese contextual stems aligned with sample exam style.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BASE_PATH = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip("，。；：！？")


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"[。！？\n]+", text)
    out = []
    for p in parts:
        p = clean_text(p)
        if len(p) >= 12:
            out.append(p)
    return out


def load_kps(theme: str) -> list[str]:
    p = BASE_PATH / "knowledge_points" / f"{theme}_知识点标注.md"
    kps = []
    in_section_title_block = False
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("## "):
            in_section_title_block = "章节/栏目标题" in line
            continue
        if in_section_title_block and line.startswith("### "):
            continue
        if line.startswith("- ") and not line.startswith("- **"):
            if in_section_title_block:
                continue
            kp = clean_text(line[2:])
            if len(kp) >= 4:
                kps.append(kp)
    # de-dup keep order
    seen = set()
    uniq = []
    for k in kps:
        if k not in seen:
            uniq.append(k)
            seen.add(k)
    return uniq


def find_context_sentence(kp: str, sentences: list[str]) -> str:
    direct = [s for s in sentences if kp in s]
    if direct:
        return min(direct, key=len)

    tokens = [t for t in re.split(r"[，、：；（）()《》“”\-\s]+", kp) if len(t) >= 2]
    best = ""
    best_score = -1
    for s in sentences:
        score = sum(1 for t in tokens if t in s)
        if score > best_score:
            best_score = score
            best = s
    return best if best else kp


def normalize_question(text: str) -> str:
    text = clean_text(text)
    if not text.endswith("。"):
        text += "。"
    return text


def answer_type(answer: str) -> str:
    if re.fullmatch(r"\d{4}年(?:\d{1,2}月(?:\d{1,2}日)?)?(?:至\d{1,2}月\d{1,2}日)?", answer):
        return "date"
    if re.fullmatch(r"\d+(?:\.\d+)?%-\d+(?:\.\d+)?%", answer):
        return "number"
    if re.fullmatch(r"\d+(?:\.\d+)?%(?:以上)?", answer):
        return "number"
    if re.fullmatch(r"\d+(?:\.\d+)?(?:亿|万)?(?:千瓦|立方米|微克每立方米|人次|人|项|分|个|家|所|公里|天|条|亩|场比赛)(?:以上)?", answer):
        return "number"
    if re.fullmatch(r"\d+(?:\.\d+)?(?:%|亿|万)", answer):
        return "number"
    if answer.startswith("《") and answer.endswith("》"):
        return "title"
    if answer.startswith("“") and answer.endswith("”"):
        return "quote"
    return "term"


def split_number_and_unit(answer: str) -> tuple[str, str] | None:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)%-(\d+(?:\.\d+)?)%", answer)
    if m:
        return f"{m.group(1)}-{m.group(2)}", "%"

    m = re.fullmatch(r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)%", answer)
    if m:
        return f"{m.group(1)}-{m.group(2)}", "%"

    m = re.fullmatch(r"(\d+(?:\.\d+)?)%(以上)?", answer)
    if m:
        suffix = m.group(2) or ""
        return m.group(1), f"%{suffix}"

    m = re.fullmatch(
        r"(\d+(?:\.\d+)?)(亿|万)?(千瓦|立方米|微克每立方米|人次|人|项|分|个|家|所|公里|天|条|亩|场比赛)(以上)?",
        answer,
    )
    if m:
        scale = m.group(2) or ""
        unit = m.group(3)
        suffix = m.group(4) or ""
        return m.group(1), f"{scale}{unit}{suffix}"

    m = re.fullmatch(r"(\d+(?:\.\d+)?)(%|亿|万)", answer)
    if m:
        return m.group(1), m.group(2)

    return None


def answer_subtype(answer: str, kind: str) -> str:
    if kind == "date":
        if "至" in answer:
            return "date-range"
        if "日" in answer:
            return "date-day"
        if "月" in answer:
            return "date-month"
        return "date-year"
    if kind == "number":
        if "%" in answer:
            return "number-percent"
        if "千瓦" in answer:
            return "number-capacity"
        if "立方米" in answer:
            return "number-volume"
        if "万人" in answer or "人次" in answer or "人" in answer:
            return "number-population"
        if "条" in answer:
            return "number-article"
        if any(token in answer for token in ["个", "家", "项", "亩", "场"]):
            return "number-count"
    if kind == "title":
        return "title-doc"
    if kind == "quote":
        return "quote-slogan"
    if any(token in answer for token in ["法典", "条例", "白皮书", "法", "规则", "名录", "意见"]):
        return "term-doc"
    if any(token in answer for token in ["目标", "计划", "制度", "机制", "市场", "工程"]):
        return "term-policy"
    if any(token in answer for token in ["会议", "大会", "世博会", "全运会", "世运会"]):
        return "term-event"
    return "term-general"


def classify_domain(text: str) -> str:
    keyword_groups = {
        "law-policy": ["法典", "条例", "立法", "法治", "法", "规定"],
        "climate-carbon": ["碳", "温室气体", "非化石", "减排", "COP", "自主贡献", "双碳"],
        "ecology-biodiversity": ["湿地", "生物圈", "生物多样性", "保护区", "野生动物", "国家公园"],
        "desert-control": ["三北", "治沙", "沙漠", "锁边", "荒漠化"],
        "energy-transport": ["充电桩", "氢能", "光伏", "新能源", "千瓦", "能源"],
        "air-water": ["PM2.5", "水质", "海域"],
    }
    for domain, keywords in keyword_groups.items():
        if any(k in text for k in keywords):
            return domain
    return "general"


def distractor_match_score(target: dict, candidate: dict) -> int:
    score = 0
    if target["answer_type"] == candidate["answer_type"]:
        score += 50
    if target["answer_subtype"] == candidate["answer_subtype"]:
        score += 35
    if target["domain"] == candidate["domain"]:
        score += 25
    if target["answer_type"] == "number" and candidate["answer_type"] == "number":
        score += 10
    return score


def score_answer(answer: str, base_score: int) -> int:
    score = base_score
    kind = answer_type(answer)
    if kind == "date":
        score -= 40
    elif kind == "number":
        score -= 20
    elif kind == "title":
        score += 10
    elif kind == "quote":
        score += 5
    else:
        score += 20

    if any(token in answer for token in ["计划", "世博会", "全运会", "世运会", "西夏陵", "秦刻石", "中国馆", "研究所"]):
        score += 20
    if answer.startswith("第") and "届" in answer:
        score += 10
    if any(token in answer for token in ["宁夏", "上海", "广州", "成都", "青海"]) and kind == "term":
        score -= 10
    return score


def extract_entity_from_date_led_clause(kp: str) -> str | None:
    # Support comma-separated ("2025年1月1日，...") and colon-separated ("2025年10月20日至23日：...") formats.
    comma_match = re.match(r"^\d{4}年\d{1,2}月(?:\d{1,2}日)?，", kp)
    colon_match = re.match(r"^\d{4}年\d{1,2}月(?:\d{1,2}(?:日(?:至\d{1,2}日)?)?)?：", kp)
    if not comma_match and not colon_match:
        return None

    sep = "，" if comma_match else "："
    parts = kp.split(sep, 1)
    if len(parts) != 2:
        return None
    tail = clean_text(parts[1])
    if len(tail) < 4:
        return None

    patterns = [
        r"(?P<answer>“[^”]{2,20}”(?:联演|演训|演练|行动|时代|体系)?)",
        r"(?P<answer>[^，。；]{2,24}?(?:阅兵式|联演|演训|演练|行动|军旗面式样|军旗体系|联合指挥体系|全民征兵登记|四中全会|五中全会|六中全会|全会))",
        r"(?P<answer>[^，。；]{2,24}?)(?=于|在|由|是|为|首次|正式|成功|开始|进行|发起|组织|发动|宣布|举行|完成|入列|下水|参加|启动|派遣|部署|召开|通过|发布|出台|实施)",
    ]
    for pattern in patterns:
        match = re.search(pattern, tail)
        if not match:
            continue
        answer = clean_text(match.group("answer"))
        if len(answer) < 2 or len(answer) > 28:
            continue
        if any(ch in answer for ch in "，。；："):
            continue
        if answer in {"中国", "中方", "双方", "美国", "委内瑞拉", "印度", "巴基斯坦", "东部战区"}:
            continue
        if answer in kp:
            return answer
    return None


def extract_gap_spec(kp: str) -> dict | None:
    patterns = [
        # Military-specific patterns - preserve context with verb phrases
        (r'美国实施(?P<answer>午夜之锤)行动', 126),
        (r'以色列发动(?P<answer>崛起的雄狮)行动', 126),
        # General policy/event action patterns: ask only core keyword/object.
        (r'签署(?P<answer>[^，。；]{2,28}?(?:议定书|协议|合作文件|宣言|倡议|方案|机制))', 126),
        (r'发布(?P<answer>[^，。；]{2,28}?(?:白皮书|政策文件|意见|行动方案|倡议|机制|规则|名录|宣言))', 125),
        (r'推出(?P<answer>[^，。；]{2,24}?(?:机制|方案|倡议|计划|平台))', 124),
        (r'新军种的(?P<answer>军旗)', 125),
        (r'形成新时代人民军队(?P<answer>军旗体系)', 124),
        (r'中国第三艘航空母舰(?P<answer>福建舰)(?=下水)', 124),
        (r'派遣载有\d+名军人的(?P<answer>两栖中队)', 123),
        (r'(?P<answer>"六位一体"联合指挥)(?=：)', 123),
        (r'(?P<answer>"低慢小"目标打击)(?=：)', 123),
        # Naval exercises and operations - extract ship/entity name only
        (r'(?P<answer>福建舰)(?:出海开展首次航行试验)', 123),
        # Preserve important verbs and subjects
        (r'(?P<answer>委内瑞拉)启动全民征兵登记', 124),
        # Military joint exercises - extract exercise name only, keep context
        (r'中泰"(?P<answer>[^"]+)"海军联合训练', 122),
        (r'中柬"(?P<answer>[^"]+)"联演(?=开始|进行)', 122),
        (r'中国海军参加"(?P<answer>[^"]+)"多国海上联演', 122),
        (r'发起"(?P<answer>联合利剑-2025)"实战化演训', 122),
        (r'组织"(?P<answer>[^"]+)"演练', 122),
        (r'军方发动"(?P<answer>[^"]+)"对', 122),
        (r'中俄蒙举行"(?P<answer>[^"]+)"联合演练', 122),
        (r'(?P<answer>印度)和巴基斯坦宣布实现全面停火', 122),
        (r"^\d{4}年\d{1,2}月\d{1,2}日，[第首新三四五六七八九十两\d次修订的]*?(?P<answer>《[^》]+》)(?=首次提请|公布|发布|出台|审议)", 125),
        (r"宣布(?P<answer>中国2035年国家自主贡献目标)", 123),
        (r"发布(?P<answer>碳市场建设意见)", 122),
        (r"发布(?P<answer>《[^》]+》白皮书)", 122),
        (r"发布[^，。；]{0,120}?(?P<answer>四支新军种的军旗面式样)", 123),
        (r"派遣(?P<answer>[^，。；]{2,24}?两栖中队)", 118),
        (r"开始部署(?P<answer>反舰导弹)", 118),
        (r"同意新建(?P<answer>[^，。；]{2,20}?自然保护区)", 121),
        (r"发布(?P<answer>新版重点保护野生动物名录)", 120),
        (r"发布(?P<answer>十四五能源高质量发展成果)", 118),
        (r"列车(?P<answer>[^，。；]{2,12}号)(?=在)", 118),
        (r"发布(?P<answer>杭碳十条)", 118),
        (r"引入(?P<answer>实质性派生品种制度)", 118),
        (r"要求各方提交(?P<answer>新的国家自主贡献)", 112),
        # 十五五 and general policy/meeting-resolution patterns
        (r"审议通过(?P<answer>《[^》]+》)", 125),
        (r"实施(?P<answer>人工智能[+＋]行动)", 118),
        (r"前瞻布局(?P<answer>[^，。；]{2,30}?等(?:方向|领域))", 115),
        (r"首要任务是(?P<answer>[^，。；]{2,16})", 115),
        (r"首次对(?P<answer>[^，。；]{2,12}?)进行专章部署", 115),
        (r"发展具有(?P<answer>[^，。；]{4,40}?)的新时代中国特色社会主义文化", 112),
        (r"加快建设(?P<answer>[^，。；]{2,20}?(?:体系|格局|机制|市场|大市场))", 112),
        (r"把(?P<answer>[^，。；]{4,20}?)作为(?:独立原则|最大的政治|扩大内需和优化供给的重要抓手)", 112),
        (r"学好用活(?P<answer>[^，。；]{2,12}?经验)", 112),
        (r"体现(?P<answer>[^，。；]{4,40}?)的完整政策链条", 110),
        (r"破除(?P<answer>[^，。；]{2,12}?(?:竞争|壁垒))", 110),
        (r"民生导向聚焦(?P<answer>[^，。；]{2,12})", 110),
        (r"放在(?P<answer>[^，。；]{2,12}?)上(?=[，。])", 110),
        (r"坚持(?P<answer>[^，。；]{4,20}?(?:相结合|形势判断))", 108),
        (r"形成(?P<answer>[^，。；]{4,20}?(?:合力|格局|体系))", 108),
        (r"推进(?P<answer>[^，。；]{2,24}?(?:攻坚|碳中和|治军))", 108),
        (r"加快(?P<answer>[^，。；]{4,20}?融合)发展", 108),
        (r"捍卫(?P<answer>[^，。；]{4,24}?利益)", 108),
        (r"探索延长(?P<answer>[^，。；]{2,12})", 108),
        (r"促进(?P<answer>[^，。；]{4,20}?互动)", 105),
        (r"提升(?P<answer>[^，。；]{2,16}?(?:效率|效能|质效))", 105),
        (r"推动(?P<answer>[^，。；]{4,24}?(?:流动|振兴|转型))", 105),
        (r"提出(?P<answer>[^，。；]{2,16}?支柱)", 105),
        (r"(?P<answer>美丽中国)建设取得", 105),
        (r"(?P<answer>国家安全屏障)更加巩固", 105),
        (r"^(?P<answer>[^：]{2,24})(?=：)", 116),
        (r"表决通过(?P<answer>[^，。；]{2,16}?)(?=列入)", 120),
        (r"发现(?P<answer>[^，。]+?刻石)", 120),
        (r"^(?P<answer>\d{4}年[^，。；]{2,12}世博会)(?=于)", 115),
        (r"^(?P<answer>[^，。；\d]{2,16})(?=在第四十一个教师节来临之际)", 110),
        (r"^(?P<answer>[^，。；]{2,16}?全运会)(?=在|设置|共有|办赛理念)", 110),
        (r"^(?P<answer>[^，。；]{2,16}?世运会)(?=火炬|设|上中国代表团)", 110),
        (r"^(?P<answer>西夏陵)(?=是|列入)", 110),
        (r"^(?P<answer>特岗计划)(?=全称为)", 105),
        (r"坚守(?P<answer>[^，。；]+?)(?=、提升)", 100),
        (r"全称为(?P<answer>“[^”]+”)", 100),
        (r"以(?P<answer>“[^”]+”)(?=为主题)", 95),
        (r"主题(?:聚焦|为)(?P<answer>“[^”]+”(?:、“[^”]+”)*)", 90),
        (r"口号为(?P<answer>“[^”]+”)", 90),
        (r"列入(?P<answer>《[^》]+》)", 88),
        (r"位于(?P<answer>[^，。]+)", 85),
        (r"由(?P<answer>[^，。]+)(?=首次联合举办)", 85),
        (r"吉祥物选取(?P<answer>[^，。]+)", 95),
        (r"共分(?P<answer>[^，。]+?五编)", 92),
        (r"共(?P<answer>\d+条)", 92),
        (r"保护期由(?P<answer>\d+年延长至\d+年)", 92),
        (r"达到(?P<answer>\d+亿立方米)", 80),
        (r"达到(?P<answer>\d+亿千瓦)", 80),
        (r"比重达到(?P<answer>\d+%以上)", 80),
        (r"下降(?P<answer>\d+%-\d+%)", 80),
        (r"形成(?P<answer>“[^”]+”展区联动模式|“[^”]+”)", 90),
        (r"通过(?P<answer>“[^”]+”“[^”]+”产品)", 90),
        (r"是(?P<answer>国内现存唯一位于原址且海拔最高的秦代刻石)", 85),
        (r"包揽(?P<answer>[^，。]+冠亚军)", 85),
        (r"总数达到(?P<answer>\d+项)", 70),
        (r"公布新增(?P<answer>\d+家)", 70),
        (r"中国以(?P<answer>\d+(?:\.\d+)?分)", 70),
        (r"获得(?P<answer>\d+金\d+银\d+铜)", 70),
        (r"共进行(?P<answer>\d+场比赛)", 70),
        (r"吸引(?P<answer>约?\d+万人次观赛)", 70),
        (r"占比(?P<answer>约?\d+%)", 65),
        (r"覆盖(?P<answer>\d+个行政区)", 65),
        (r"带动(?P<answer>超?\d+(?:\.\d+)?亿元商圈消费)", 65),
        (r"设置竞赛项目(?P<answer>\d+个大项\d+个小项)", 70),
        (r"群众赛事(?P<answer>\d+个大项\d+个小项)", 70),
        (r"设(?P<answer>\d+个大项\d+个分项\d+个小项)", 70),
        (r"共(?P<answer>\d+名运动员参赛)", 65),
        (r"累计[^，。]*补充教师(?P<answer>\d+万人)", 65),
        (r"截至(?P<answer>\d{4}年\d{1,2}月)", 40),
        (r"当地时间(?P<answer>\d{4}年\d{1,2}月\d{1,2}日)", 40),
        (r"^(?P<answer>\d{4}年\d{1,2}月\d{1,2}日)(?=，)", 40),
        (r"^(?P<answer>\d{4}年\d{1,2}月)(?=，)", 35),
    ]

    candidates = []
    for pattern, base_score in patterns:
        match = re.search(pattern, kp)
        if not match:
            continue
        answer = clean_text(match.group("answer"))
        if len(answer) < 2 or len(answer) > 28 or any(ch in answer for ch in "，。；："):
            continue
        if answer not in kp:
            continue
        kind = answer_type(answer)
        score = score_answer(answer, base_score)
        # Avoid sentence-initial date blanks when there is another valid key fact.
        if kind == "date" and match.start("answer") == 0:
            score -= 60
        candidates.append((score, answer, kind, match.start("answer") == 0))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], -len(item[1])))
    best_score, raw_answer, kind, at_start = candidates[0]

    # Entity-first fallback: if best is a sentence-initial date, prefer a non-date candidate.
    if kind == "date" and at_start:
        for cand_score, cand_answer, cand_kind, _ in candidates:
            if cand_kind != "date" and cand_score >= best_score - 40:
                raw_answer = cand_answer
                kind = cand_kind
                break
        if kind == "date":
            fallback_entity = extract_entity_from_date_led_clause(kp)
            if fallback_entity:
                raw_answer = fallback_entity
                kind = answer_type(raw_answer)

    answer = raw_answer
    question = kp.replace(raw_answer, "____", 1)
    if kind == "number":
        split_result = split_number_and_unit(raw_answer)
        if split_result:
            number_part, unit_part = split_result
            question = kp.replace(raw_answer, f"____{unit_part}", 1)
            answer = number_part

    # For colon-format KPs ("X：描述"), flip to "描述，即____" so the blank is not at sentence start.
    if question.startswith("____："):
        tail = kp.split("：", 1)[1].rstrip("。").strip()
        if len(tail) >= 4:
            question = tail + "，即____。"

    if question == kp:
        return None

    return {
        "kp": kp,
        "question": normalize_question(question),
        "answer": answer,
        "answer_type": kind,
        "answer_subtype": answer_subtype(raw_answer, kind),
        "domain": classify_domain(kp),
    }


def simplify_answer(answer: str) -> str:
    """Extract core keyword from answer, removing subject/verb/modifiers."""
    if len(answer) <= 6:
        return answer

    # Keep exact phrasing when the stem relies on these suffixes.
    if answer in ['"六位一体"联合指挥', '"低慢小"目标打击']:
        return answer

    # Keep geopolitical compound names and ordinal document forms intact.
    if answer.startswith("中国-") or answer.startswith("中国－"):
        return answer
    if re.match(r'^第[一二三四五六七八九十百千万\d]+份', answer):
        return answer
    
    # Keep certain multi-word answers intact (they're already simplified at extraction stage)
    preserve_patterns = [
        "联合利剑-2025",
        "印度和巴基斯坦",
        "福建舰",
        "委内瑞拉",
    ]
    for pattern in preserve_patterns:
        if answer == pattern:
            return answer
    
    # Extract quoted content first (e.g., "联合利剑-2025")
    quoted = re.findall(r'"([^"]+)"', answer)
    if quoted:
        core = quoted[0]
        if len(core) >= 2:
            return core
    
    quoted_cn = re.findall(r'[\"\u201c]([^\"\u201d]+)[\"\u201d]', answer)
    if quoted_cn:
        core = quoted_cn[0]
        if len(core) >= 2:
            return core
    
    # Specific optimizations for military domain
    # "形成新时代人民军队军旗体系" -> "军旗体系"
    if "形成新时代人民军队军旗体系" in answer:
        return "军旗体系"
    if "形成新时代人民军队军旗" in answer:
        return "军旗体系"
    
    # "军方发动\"辛杜尔行动" -> "辛杜尔行动"
    if "军方发动" in answer:
        answer = answer.replace("军方发动", "").lstrip("\\\"").rstrip("\"")
    
    # Pattern 1: Remove leading subject + predicate
    m = re.search(r'^[^，。；]{2,20}?(?:签署命令)?(?:发布|组织|派遣|部署)(.+)$', answer)
    if m:
        rest = m.group(1)
        if len(rest) >= 3:
            answer = rest
    
    # Pattern 2: Special extractions
    if "新军种" in answer and "军旗" in answer:
        return "新军种军旗"
    
    if "福建舰" in answer:
        return "福建舰"
    
    # Pattern 3: Remove subject prefix
    for subject in ["委内瑞拉", "中国", "印度", "美国", "巴基斯坦"]:
        if answer.startswith(subject):
            # Keep geopolitical compound terms like "中国-东盟..." and "中国-中亚..." intact.
            if len(answer) > len(subject) and answer[len(subject)] in ["-", "－", "—", "—"]:
                continue
            # Only strip subject when followed by action-style predicate.
            rest = answer[len(subject):]
            if re.match(r'^(?:启动|宣布|发布|实施|组织|发起|开展|举行|会见|签署)', rest):
                stripped = re.sub(r'^(?:启动|宣布|发布|实施|组织|发起|开展|举行|会见|签署)', '', rest)
                stripped = stripped.lstrip("，的 ")
                if len(stripped) >= 2:
                    answer = stripped
                    break
    
    # Pattern 4: Extract from "载有" patterns
    if "载有" in answer:
        m = re.search(r'的(.+)$', answer)
        if m and len(m.group(1)) >= 2:
            return m.group(1)
    
    # Pattern 5: Remove trailing markers
    if "式样" in answer:
        answer = answer.replace("式样", "").strip("的")
    
    if "体系" in answer:
        m = re.search(r'(.+?)体系', answer)
        if m and len(m.group(1)) >= 2:
            answer = m.group(1) + "体系"
    
    # Pattern 6: Remove leading descriptors
    descriptors = [
        (r'^(中国(?![-－—])|中央|大型|新型|全新|第三|第五|跨|多|联合)', ""),
        (r'^(第\d+(?:艘|届|次|年|个月))?', ""),
    ]
    for pattern, _ in descriptors:
        m = re.match(pattern, answer)
        if m:
            rest = answer[len(m.group(0)):].lstrip("，的;；")
            if len(rest) >= 2 and len(rest) < len(answer) - 1:
                answer = rest
                break
    
    return answer if len(answer) >= 2 else answer


def make_fill(spec: dict) -> dict:
    simplified = simplify_answer(spec["answer"])
    return {
        "type": "fill",
        "question": spec["question"],
        "answer": [simplified],
        "explanation": f"材料对应表述：{spec['kp']}。",
    }


def build_distractors(spec: dict, specs: list[dict], needed: int) -> list[str]:
    candidates = [
        other
        for other in specs
        if other["kp"] != spec["kp"] and other["answer"] != spec["answer"]
    ]

    def pick_from(pool: list[dict], distractors: list[str], used: set[str]) -> None:
        for item in pool:
            ans = item["answer"]
            if ans in used:
                continue
            distractors.append(ans)
            used.add(ans)
            if len(distractors) >= needed:
                return

    tiers = [
        [x for x in candidates if x["answer_type"] == spec["answer_type"] and x["answer_subtype"] == spec["answer_subtype"] and x["domain"] == spec["domain"]],
        [x for x in candidates if x["answer_type"] == spec["answer_type"] and x["answer_subtype"] == spec["answer_subtype"]],
        [x for x in candidates if x["answer_type"] == spec["answer_type"] and x["domain"] == spec["domain"]],
        [x for x in candidates if x["answer_type"] == spec["answer_type"]],
        [x for x in candidates if x["domain"] == spec["domain"]],
        candidates,
    ]
    tiers = [sorted(t, key=lambda x: distractor_match_score(spec, x), reverse=True) for t in tiers]

    distractors: list[str] = []
    used = {spec["answer"]}
    for tier in tiers:
        if len(distractors) >= needed:
            break
        pick_from(tier, distractors, used)
    return distractors[:needed]


def make_single(spec: dict, specs: list[dict]) -> dict | None:
    distractors = build_distractors(spec, specs, 3)
    if len(distractors) < 3:
        return None
    stem = spec["question"].replace("____", "（  ）", 1)
    if not stem.endswith("。"):
        stem += "。"
    stem += " 横线处应填入的是（ ）。"
    options = [spec["answer"]] + distractors
    if len(set(options)) < 4:
        return None
    return {
        "type": "single",
        "question": stem,
        "options": options,
        "answer": [0],
        "explanation": f"正确项对应材料考点：{spec['kp']}。",
    }


def make_multiple(spec1: dict, spec2: dict, specs: list[dict]) -> dict | None:
    wrong_candidates = []
    excluded = {spec1["kp"], spec2["kp"]}
    excluded_answers = {spec1["answer"], spec2["answer"]}
    for item in specs:
        if item["kp"] in excluded:
            continue
        if item["answer"] in excluded_answers:
            continue
        score = max(distractor_match_score(spec1, item), distractor_match_score(spec2, item))
        wrong_candidates.append((score, item["answer"]))

    same_type_candidates = [
        item for item in wrong_candidates if item[0] >= 50
    ]
    ordered = sorted(same_type_candidates, key=lambda x: x[0], reverse=True)
    if len(ordered) < 2:
        ordered = sorted(wrong_candidates, key=lambda x: x[0], reverse=True)

    wrong_pool = []
    used = set(excluded_answers)
    for _, ans in ordered:
        if ans in used:
            continue
        wrong_pool.append(ans)
        used.add(ans)
        if len(wrong_pool) >= 2:
            break

    if len(wrong_pool) < 2:
        return None

    q1 = spec1["question"].rstrip("。")
    q2 = spec2["question"].rstrip("。")
    stem = f"{q1}；{q2}。可分别填入以上两处横线的选项有（ ）。"
    options = [spec1["answer"], spec2["answer"], wrong_pool[0], wrong_pool[1]]
    if len(set(options)) < 4:
        return None
    return {
        "type": "multiple",
        "question": stem,
        "options": options,
        "answer": [0, 1],
        "explanation": f"正确项对应材料考点：{spec1['kp']}；{spec2['kp']}。",
    }


def make_judge(kp: str, sent: str) -> dict:
    s = clean_text(sent)
    if len(s) < 10:
        s = kp
    return {
        "type": "judge",
        "question": f"{s}。（ ）",
        "answer": [1],
        "explanation": f"该表述与材料一致，依据考点：{kp}。",
    }


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def write_js(path: Path, fill_qs, single_qs, multiple_qs, judge_qs):
    lines = ["const quizData = ["]

    lines.append(f"  {{ type: 'info', info: '【填空题 共{len(fill_qs)}题，每题2分】' }},")
    for q in fill_qs:
        ans = json.dumps(q["answer"], ensure_ascii=False)
        lines.append(f"  {{ type: 'fill', question: '{esc(q['question'])}', answer: {ans}, explanation: '{esc(q['explanation'])}' }},")

    lines.append(f"  {{ type: 'info', info: '【单项选择题 共{len(single_qs)}题，每题2分】' }},")
    for q in single_qs:
        ans = json.dumps(q["answer"], ensure_ascii=False)
        opts = json.dumps(q["options"], ensure_ascii=False)
        lines.append(f"  {{ type: 'single', question: '{esc(q['question'])}', options: {opts}, answer: {ans}, explanation: '{esc(q['explanation'])}' }},")

    lines.append(f"  {{ type: 'info', info: '【多项选择题 共{len(multiple_qs)}题，每题3分】' }},")
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
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, title: str, js_name: str):
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
  <script src=\"{js_name}\"></script>
  <script src=\"main.js\"></script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def generate_theme(theme: str):
    kps = load_kps(theme)

    # Use knowledge-point full sentences as primary context to avoid material headers/noise.
    ctx = {kp: kp for kp in kps}
    gap_specs = [spec for kp in kps if (spec := extract_gap_spec(ctx[kp]))]
    if not gap_specs:
        raise RuntimeError(f"主题 {theme} 未提取到可命题的关键信息")

    non_date_specs = [s for s in gap_specs if s["answer_type"] != "date"]
    date_specs = [s for s in gap_specs if s["answer_type"] == "date"]

    leader_keywords = [
        "习近平", "特朗普", "拜登", "普京", "泽连斯基", "马克龙", "莫迪",
        "石破茂", "冯德莱恩", "内塔尼亚胡", "尹锡悦", "岸田文雄",
    ]

    def is_leader_value(v: str) -> bool:
        text = clean_text(str(v))
        if any(k in text for k in leader_keywords):
            return True
        # Generic leadership title-only answers should also be suppressed.
        return bool(re.fullmatch(r"[\u4e00-\u9fff]{2,6}(?:主席|总统|总理|首相)", text))

    non_leader_specs = [s for s in gap_specs if not is_leader_value(s["answer"])]
    non_date_non_leader_specs = [
        s for s in gap_specs if s["answer_type"] != "date" and not is_leader_value(s["answer"])
    ]

    # seed allocation for coverage
    fill_seed = kps[:20]
    single_seed = kps[20:40]
    judge_seed = kps[40:55]
    remain = kps[55:]

    multiple_seed_pairs = []
    i = 0
    while i + 1 < len(remain):
        multiple_seed_pairs.append((remain[i], remain[i + 1]))
        i += 2
    if i < len(remain):
        judge_seed.append(remain[i])

    spec_by_kp = {spec["kp"]: spec for spec in gap_specs}

    def fill_key(q: dict) -> tuple:
        return (q["question"], tuple(q["answer"]))

    def single_key(q: dict) -> tuple:
        return (q["question"], tuple(q["options"]), tuple(q["answer"]))

    def multiple_key(q: dict) -> tuple:
        return (q["question"], tuple(q["options"]), tuple(q["answer"]))

    def judge_key(q: dict) -> tuple:
        return (q["question"], tuple(q["answer"]))

    def dedupe_qs(qs: list[dict], key_func):
        seen = set()
        out = []
        for q in qs:
            k = key_func(q)
            if k in seen:
                continue
            seen.add(k)
            out.append(q)
        return out, seen

    # build initial
    fill_qs = [make_fill(spec_by_kp[k]) for k in fill_seed if k in spec_by_kp]

    single_qs = []
    for k in single_seed:
        if k not in spec_by_kp:
            continue
        q = make_single(spec_by_kp[k], gap_specs)
        if q:
            single_qs.append(q)

    multiple_qs = []
    for a, b in multiple_seed_pairs:
        if a not in spec_by_kp or b not in spec_by_kp:
            continue
        q = make_multiple(spec_by_kp[a], spec_by_kp[b], gap_specs)
        if q:
            multiple_qs.append(q)
    judge_qs = [make_judge(k, ctx[k]) for k in judge_seed]

    fill_qs, fill_seen = dedupe_qs(fill_qs, fill_key)
    single_qs, single_seen = dedupe_qs(single_qs, single_key)
    multiple_qs, multiple_seen = dedupe_qs(multiple_qs, multiple_key)
    judge_qs, judge_seen = dedupe_qs(judge_qs, judge_key)

    def is_date_value(v: str) -> bool:
        return answer_type(clean_text(str(v))) == "date"

    def is_2025_date_value(v: str) -> bool:
        text = clean_text(str(v))
        return bool(re.match(r"^2025年(?:\d{1,2}月(?:\d{1,2}日)?)?$", text))

    def fill_is_date(q: dict) -> bool:
        return bool(q.get("answer")) and is_date_value(q["answer"][0])

    def single_is_date(q: dict) -> bool:
        ans_idx = q.get("answer", [None])[0]
        if not isinstance(ans_idx, int):
            return False
        if ans_idx < 0 or ans_idx >= len(q.get("options", [])):
            return False
        return is_date_value(q["options"][ans_idx])

    def multiple_has_date(q: dict) -> bool:
        for ans_idx in q.get("answer", []):
            if isinstance(ans_idx, int) and 0 <= ans_idx < len(q.get("options", [])):
                if is_date_value(q["options"][ans_idx]):
                    return True
        return False

    def fill_is_2025_date(q: dict) -> bool:
        return bool(q.get("answer")) and is_2025_date_value(q["answer"][0])

    def single_is_2025_date(q: dict) -> bool:
        ans_idx = q.get("answer", [None])[0]
        if not isinstance(ans_idx, int):
            return False
        if ans_idx < 0 or ans_idx >= len(q.get("options", [])):
            return False
        return is_2025_date_value(q["options"][ans_idx])

    def multiple_has_2025_date(q: dict) -> bool:
        for ans_idx in q.get("answer", []):
            if isinstance(ans_idx, int) and 0 <= ans_idx < len(q.get("options", [])):
                if is_2025_date_value(q["options"][ans_idx]):
                    return True
        return False

    def fill_is_leader(q: dict) -> bool:
        return bool(q.get("answer")) and is_leader_value(q["answer"][0])

    def fill_is_colon_start(q: dict) -> bool:
        """True if the fill blank is at sentence start before a colon (e.g. '____：描述')."""
        return bool(re.match(r"^____[：:]\S", q.get("question", "")))

    def single_is_leader(q: dict) -> bool:
        ans_idx = q.get("answer", [None])[0]
        if not isinstance(ans_idx, int):
            return False
        if ans_idx < 0 or ans_idx >= len(q.get("options", [])):
            return False
        return is_leader_value(q["options"][ans_idx])

    def multiple_has_leader(q: dict) -> bool:
        for ans_idx in q.get("answer", []):
            if isinstance(ans_idx, int) and 0 <= ans_idx < len(q.get("options", [])):
                if is_leader_value(q["options"][ans_idx]):
                    return True
        return False

    def enforce_date_cap_fill(qs: list[dict], cap: int) -> list[dict]:
        if not non_date_specs:
            return qs
        date_count = sum(1 for q in qs if fill_is_date(q))
        if date_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if date_count <= cap:
                break
            if not fill_is_date(q):
                continue
            replacement = make_fill(non_date_specs[nd_idx % len(non_date_specs)])
            nd_idx += 1
            qs[i] = replacement
            date_count -= 1
        return qs

    def enforce_date_cap_single(qs: list[dict], cap: int) -> list[dict]:
        if not non_date_specs:
            return qs
        date_count = sum(1 for q in qs if single_is_date(q))
        if date_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if date_count <= cap:
                break
            if not single_is_date(q):
                continue
            attempts = 0
            replacement = None
            while attempts < len(non_date_specs):
                spec = non_date_specs[nd_idx % len(non_date_specs)]
                nd_idx += 1
                attempts += 1
                cand = make_single(spec, gap_specs)
                if cand and not single_is_date(cand):
                    replacement = cand
                    break
            if replacement:
                qs[i] = replacement
                date_count -= 1
        return qs

    def enforce_date_cap_multiple(qs: list[dict], cap: int) -> list[dict]:
        if len(non_date_specs) < 2:
            return qs
        date_count = sum(1 for q in qs if multiple_has_date(q))
        if date_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if date_count <= cap:
                break
            if not multiple_has_date(q):
                continue
            attempts = 0
            replacement = None
            while attempts < len(non_date_specs) * 2:
                spec1 = non_date_specs[nd_idx % len(non_date_specs)]
                spec2 = non_date_specs[(nd_idx + 1) % len(non_date_specs)]
                nd_idx += 2
                attempts += 2
                if spec1["kp"] == spec2["kp"]:
                    continue
                cand = make_multiple(spec1, spec2, gap_specs)
                if cand and not multiple_has_date(cand):
                    replacement = cand
                    break
            if replacement:
                qs[i] = replacement
                date_count -= 1
        return qs

    def enforce_2025_date_cap_fill(qs: list[dict], cap: int) -> list[dict]:
        pool = non_date_non_leader_specs or non_date_specs or non_leader_specs
        if not pool:
            return qs
        bad_count = sum(1 for q in qs if fill_is_2025_date(q))
        if bad_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if bad_count <= cap:
                break
            if not fill_is_2025_date(q):
                continue
            replacement = make_fill(pool[nd_idx % len(pool)])
            nd_idx += 1
            if not fill_is_2025_date(replacement):
                qs[i] = replacement
                bad_count -= 1
        return qs

    def enforce_2025_date_cap_single(qs: list[dict], cap: int) -> list[dict]:
        pool = non_date_non_leader_specs or non_date_specs or non_leader_specs
        if not pool:
            return qs
        bad_count = sum(1 for q in qs if single_is_2025_date(q))
        if bad_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if bad_count <= cap:
                break
            if not single_is_2025_date(q):
                continue
            attempts = 0
            replacement = None
            while attempts < len(pool):
                spec = pool[nd_idx % len(pool)]
                nd_idx += 1
                attempts += 1
                cand = make_single(spec, gap_specs)
                if cand and not single_is_2025_date(cand):
                    replacement = cand
                    break
            if replacement:
                qs[i] = replacement
                bad_count -= 1
        return qs

    def enforce_2025_date_cap_multiple(qs: list[dict], cap: int) -> list[dict]:
        pool = non_date_non_leader_specs or non_date_specs or non_leader_specs
        if len(pool) < 2:
            return qs
        bad_count = sum(1 for q in qs if multiple_has_2025_date(q))
        if bad_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if bad_count <= cap:
                break
            if not multiple_has_2025_date(q):
                continue
            attempts = 0
            replacement = None
            while attempts < len(pool) * 2:
                spec1 = pool[nd_idx % len(pool)]
                spec2 = pool[(nd_idx + 1) % len(pool)]
                nd_idx += 2
                attempts += 2
                if spec1["kp"] == spec2["kp"]:
                    continue
                cand = make_multiple(spec1, spec2, gap_specs)
                if cand and not multiple_has_2025_date(cand):
                    replacement = cand
                    break
            if replacement:
                qs[i] = replacement
                bad_count -= 1
        return qs

    def enforce_leader_cap_fill(qs: list[dict], cap: int) -> list[dict]:
        pool = non_date_non_leader_specs or non_leader_specs or non_date_specs
        if not pool:
            return qs
        leader_count = sum(1 for q in qs if fill_is_leader(q))
        if leader_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if leader_count <= cap:
                break
            if not fill_is_leader(q):
                continue
            replacement = make_fill(pool[nd_idx % len(pool)])
            nd_idx += 1
            if not fill_is_leader(replacement):
                qs[i] = replacement
                leader_count -= 1
        return qs

    def enforce_leader_cap_single(qs: list[dict], cap: int) -> list[dict]:
        pool = non_date_non_leader_specs or non_leader_specs or non_date_specs
        if not pool:
            return qs
        leader_count = sum(1 for q in qs if single_is_leader(q))
        if leader_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if leader_count <= cap:
                break
            if not single_is_leader(q):
                continue
            attempts = 0
            replacement = None
            while attempts < len(pool):
                spec = pool[nd_idx % len(pool)]
                nd_idx += 1
                attempts += 1
                cand = make_single(spec, gap_specs)
                if cand and not single_is_leader(cand):
                    replacement = cand
                    break
            if replacement:
                qs[i] = replacement
                leader_count -= 1
        return qs

    def enforce_leader_cap_multiple(qs: list[dict], cap: int) -> list[dict]:
        pool = non_date_non_leader_specs or non_leader_specs or non_date_specs
        if len(pool) < 2:
            return qs
        leader_count = sum(1 for q in qs if multiple_has_leader(q))
        if leader_count <= cap:
            return qs
        nd_idx = 0
        for i, q in enumerate(qs):
            if leader_count <= cap:
                break
            if not multiple_has_leader(q):
                continue
            attempts = 0
            replacement = None
            while attempts < len(pool) * 2:
                spec1 = pool[nd_idx % len(pool)]
                spec2 = pool[(nd_idx + 1) % len(pool)]
                nd_idx += 2
                attempts += 2
                if spec1["kp"] == spec2["kp"]:
                    continue
                cand = make_multiple(spec1, spec2, gap_specs)
                if cand and not multiple_has_leader(cand):
                    replacement = cand
                    break
            if replacement:
                qs[i] = replacement
                leader_count -= 1
        return qs

    # pad to 40/40/20/20 with contextual stems
    if theme in ("国际要闻", "探究性专题") and non_date_non_leader_specs:
        pad_specs = non_date_non_leader_specs + non_leader_specs + non_date_specs + date_specs
    elif theme in ("国际要闻", "探究性专题") and non_date_specs:
        pad_specs = non_date_specs + date_specs
    elif theme == "十五五" and non_date_specs:
        pad_specs = non_date_specs
    else:
        pad_specs = gap_specs

    idx = 0
    attempts = 0
    max_attempts = max(200, len(pad_specs) * 20)
    while len(fill_qs) < 40 and attempts < max_attempts:
        spec = pad_specs[idx % len(pad_specs)]
        q = make_fill(spec)
        k = fill_key(q)
        if k not in fill_seen:
            fill_qs.append(q)
            fill_seen.add(k)
        idx += 1
        attempts += 1

    idx = 0
    attempts = 0
    max_attempts = max(300, len(pad_specs) * 30)
    while len(single_qs) < 40 and attempts < max_attempts:
        spec = pad_specs[idx % len(pad_specs)]
        q = make_single(spec, gap_specs)
        if q:
            k = single_key(q)
            if k in single_seen:
                idx += 1
                attempts += 1
                continue
            single_qs.append(q)
            single_seen.add(k)
        idx += 1
        attempts += 1

    idx = 0
    attempts = 0
    max_attempts = max(400, len(pad_specs) * 40)
    while len(multiple_qs) < 20 and attempts < max_attempts:
        spec1 = pad_specs[idx % len(pad_specs)]
        spec2 = pad_specs[(idx + 1) % len(pad_specs)]
        if spec1["kp"] != spec2["kp"]:
            q = make_multiple(spec1, spec2, gap_specs)
            if q:
                k = multiple_key(q)
                if k in multiple_seen:
                    idx += 2
                    attempts += 1
                    continue
                multiple_qs.append(q)
                multiple_seen.add(k)
        idx += 2
        attempts += 1

    # Theme-specific balancing: reduce date-focused blanks/options for 国际要闻, 探究性专题, and 十五五.
    if theme in ("国际要闻", "探究性专题"):
        fill_qs = enforce_date_cap_fill(fill_qs, cap=8)
        single_qs = enforce_date_cap_single(single_qs, cap=8)
        multiple_qs = enforce_date_cap_multiple(multiple_qs, cap=4)
        # Hard constraint: do not ask by leader keywords or 2025-date keywords.
        fill_qs = enforce_2025_date_cap_fill(fill_qs, cap=0)
        single_qs = enforce_2025_date_cap_single(single_qs, cap=0)
        multiple_qs = enforce_2025_date_cap_multiple(multiple_qs, cap=0)
        fill_qs = enforce_leader_cap_fill(fill_qs, cap=0)
        single_qs = enforce_leader_cap_single(single_qs, cap=0)
        multiple_qs = enforce_leader_cap_multiple(multiple_qs, cap=0)
    elif theme == "十五五":
        # 十五五 should not ask about specific dates as answers, and should not
        # produce sentence-initial blanks (e.g. "____：描述") from X：描述 KPs.
        fill_qs = enforce_date_cap_fill(fill_qs, cap=0)
        single_qs = enforce_date_cap_single(single_qs, cap=0)
        multiple_qs = enforce_date_cap_multiple(multiple_qs, cap=0)
        # Remove any fill question with blank at sentence-start before colon.
        fill_qs = [q for q in fill_qs if not fill_is_colon_start(q)]

    # Final pass: de-duplicate again after all balancing rules, then refill uniquely.
    fill_qs, fill_seen = dedupe_qs(fill_qs, fill_key)
    single_qs, single_seen = dedupe_qs(single_qs, single_key)
    multiple_qs, multiple_seen = dedupe_qs(multiple_qs, multiple_key)

    idx = 0
    attempts = 0
    max_attempts = max(300, len(pad_specs) * 40)
    while len(fill_qs) < 40 and attempts < max_attempts:
        spec = pad_specs[idx % len(pad_specs)]
        q = make_fill(spec)
        k = fill_key(q)
        if k not in fill_seen:
            fill_qs.append(q)
            fill_seen.add(k)
        idx += 1
        attempts += 1

    idx = 0
    attempts = 0
    max_attempts = max(400, len(pad_specs) * 60)
    while len(single_qs) < 40 and attempts < max_attempts:
        spec = pad_specs[idx % len(pad_specs)]
        q = make_single(spec, gap_specs)
        if q:
            k = single_key(q)
            if k not in single_seen:
                single_qs.append(q)
                single_seen.add(k)
        idx += 1
        attempts += 1

    idx = 0
    attempts = 0
    max_attempts = max(500, len(pad_specs) * 80)
    while len(multiple_qs) < 20 and attempts < max_attempts:
        spec1 = pad_specs[idx % len(pad_specs)]
        spec2 = pad_specs[(idx + 1) % len(pad_specs)]
        if spec1["kp"] != spec2["kp"]:
            q = make_multiple(spec1, spec2, gap_specs)
            if q:
                k = multiple_key(q)
                if k not in multiple_seen:
                    multiple_qs.append(q)
                    multiple_seen.add(k)
        idx += 2
        attempts += 1

    idx = 0
    attempts = 0
    max_attempts = max(200, len(kps) * 20)
    while len(judge_qs) < 20 and attempts < max_attempts:
        k = kps[idx % len(kps)]
        q = make_judge(k, ctx[k])
        kq = judge_key(q)
        if kq not in judge_seen:
            judge_qs.append(q)
            judge_seen.add(kq)
        idx += 1
        attempts += 1

    # Second enforcement pass after final refill (captures newly added date/leader/colon-start questions).
    if theme in ("国际要闻", "探究性专题"):
        fill_qs = enforce_2025_date_cap_fill(fill_qs, cap=0)
        single_qs = enforce_2025_date_cap_single(single_qs, cap=0)
        multiple_qs = enforce_2025_date_cap_multiple(multiple_qs, cap=0)
        fill_qs = enforce_leader_cap_fill(fill_qs, cap=0)
        single_qs = enforce_leader_cap_single(single_qs, cap=0)
        multiple_qs = enforce_leader_cap_multiple(multiple_qs, cap=0)
    if theme == "十五五":
        fill_qs = enforce_date_cap_fill(fill_qs, cap=0)
        single_qs = enforce_date_cap_single(single_qs, cap=0)
        multiple_qs = enforce_date_cap_multiple(multiple_qs, cap=0)
        fill_qs = [q for q in fill_qs if not fill_is_colon_start(q)]

    js_name = f"{theme}模拟_新版_真题风格.js"
    html_name = f"{theme}模拟_新版_真题风格.html"

    js_path = BASE_PATH / "online_quiz" / js_name
    html_path = BASE_PATH / "online_quiz" / html_name

    write_js(js_path, fill_qs, single_qs, multiple_qs, judge_qs)
    write_html(html_path, f"{theme}模拟（新版·真题风格）", js_name)

    used_kps = set(fill_seed) | set(single_seed) | set(judge_seed)
    for a, b in multiple_seed_pairs:
        used_kps.add(a)
        used_kps.add(b)
    coverage = len(used_kps) / len(kps) * 100 if kps else 0.0

    print(f"主题: {theme}")
    print(f"知识点总数: {len(kps)}")
    print(f"覆盖率(种子覆盖): {len(used_kps)}/{len(kps)} = {coverage:.1f}%")
    print(f"输出JS: {js_name}")
    print(f"输出HTML: {html_name}")
    print(f"题量: 填空{len(fill_qs)} 单选{len(single_qs)} 多选{len(multiple_qs)} 判断{len(judge_qs)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate one exam-style validation quiz for a theme.")
    parser.add_argument("theme", nargs="?", default="文体", help="Theme name, for example 文体 or 环保")
    args = parser.parse_args()
    generate_theme(args.theme)
