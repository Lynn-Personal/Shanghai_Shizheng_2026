#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识点提取和标注工具
为每个主题材料提取知识点（可能考点），并生成标注文件
"""

import re
import json
from pathlib import Path
from collections import Counter

class KnowledgePointsExtractor:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.materials_dir = self.base_path / "materials"
        self.knowledge_dir = self.base_path / "knowledge_points"
        self.knowledge_dir.mkdir(exist_ok=True)
        
        # 过滤模式（同improved_quiz_generator_v3.py）
        self.filter_patterns = [
            r'^[第\d]+页.*',
            r'^新闻现场\s*$',
            r'^背景资料.*',
            r'^责任编辑.*',
            r'^邮箱.*',
            r'^美术编辑.*',
        ]

        # 参考样题中的常见考查形态，优先提取会议/文件/行动代号/政策术语
        self.exam_focus_keywords = [
            '全会', '峰会', '大会', '会议', '决定', '报告', '条例', '方案', '演习',
            '政府工作报告', '世界遗产', '中国式现代化', '新质生产力', '人工智能',
            '空间站', '神舟', '嫦娥', '载人', '月球', '领海基线', '主席国', '停火'
        ]

        self.noise_exact = {
            '全会', '会议', '首次', '第一', '相关链接', '新闻现场', '时间', '出席人员'
        }
        self.noise_contains = [
            '第1页', '第2页', '专题首页', '封面', '新闻现场', '相关链接', '责任编辑',
            '邮箱', '美术编辑', '写错别字', '每小题', '共40分', '共20分', '共10分'
        ]

    def _unique_clean(self, items, min_len=2, max_len=36, limit=None):
        """去重并清洗提取结果，保留原顺序。"""
        cleaned = []
        seen = set()

        for item in items:
            t = re.sub(r'\s+', ' ', item).strip().replace('"', '').replace('“', '').replace('”', '')
            t = t.strip('，。；：、()（）[]【】')
            if len(t) < min_len or len(t) > max_len:
                continue
            if t in self.noise_exact:
                continue
            if any(k in t for k in self.noise_contains):
                continue
            if '《' in t or '》' in t:
                continue
            if '•' in t or '：' in t or ':' in t:
                continue
            if re.search(r'第\d+页', t):
                continue
            if re.search(r'第[一二三四五六七八九十\d]+个$', t):
                continue
            if re.match(r'^[\-_/]+$', t):
                continue
            if t in seen:
                continue
            seen.add(t)
            cleaned.append(t)
            if limit and len(cleaned) >= limit:
                break

        return cleaned
    
    def should_filter(self, text):
        """检查是否应该过滤这一行"""
        text = text.strip()
        
        if len(text) < 5:
            return True
        
        for pattern in self.filter_patterns:
            if re.match(pattern, text):
                return True
        
        if re.match(r'^[-—_•·]+$', text):
            return True
        
        if re.match(r'^[\d\s]+$', text):
            return True
        
        explanation_keywords = [
            '一键复制', '导出为PDF', '导出为', 'Word', 'Typora', 'Markdown',
            'PDF文件', '内容整理', '所有内容', '电子版', 'Markdown编辑器',
            '我已完整', '当前对话', '网页搜索', '无法直接', '可下载',
            '图片附', '临时禁用', '我无法', '但我已'
        ]
        
        for keyword in explanation_keywords:
            if keyword in text:
                return True
        
        return False
    
    def clean_material(self, text):
        """清理材料"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if not self.should_filter(line):
                cleaned_lines.append(line.strip())
        
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = re.sub(r'\n\n+', '\n', cleaned_text)
        
        return cleaned_text
    
    def extract_knowledge_points(self, text):
        """
        从材料中提取知识点
        包括：日期、数字、关键组织、关键人物、关键概念
        """
        knowledge_points = {}
        
        # 1. 提取日期
        dates = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月|\d{4}年', text)
        if dates:
            knowledge_points['dates'] = self._unique_clean(dates, min_len=5, max_len=16)
        
        # 2. 提取数字和指标（优先保留带单位的量化信息）
        numbers = re.findall(r'(\d+(?:\.\d+)?(?:万亿元|亿元|万亿|万|亿|%|克|次|项|发|票|名|人))', text)
        if numbers:
            knowledge_points['numbers'] = self._unique_clean(numbers, min_len=2, max_len=16, limit=20)
        
        # 3. 提取组织名称（使用更严格的模式，减少截断短语）
        orgs = re.findall(
            r'((?:中共中央|国务院|中央军委|联合国安理会|联合国教科文组织|上海合作组织|中国人民解放军|中国政府|国家主席|生态环境部|新华社|香港特区立法会|中国共产党|人民大会堂)[^，。；：“”《》\n]{0,30})',
            text
        )
        if orgs:
            knowledge_points['organizations'] = self._unique_clean(orgs, min_len=3, max_len=24, limit=25)
        
        # 4. 提取关键概念（样题导向词 + 高频概念补充）
        concept_seed = [
            '中国式现代化', '进一步全面深化改革', '全面深化改革', '高质量发展', '新质生产力',
            '国家治理体系', '治理能力现代化', '社会主义市场经济体制', '现代化产业体系',
            '人工智能', '数字经济', '共同富裕', '国家安全', '绿色转型', '能源体系',
            '关键核心技术', '生态环境保护', '海洋生态环境', '新质战斗力', '两国方案'
        ]
        seed_hits = [c for c in concept_seed if c in text]

        raw_concepts = re.findall(r'[\u4e00-\u9fff]{4,10}', text)
        concept_freq = Counter(raw_concepts)
        stop_prefix = ('的', '和', '是', '在')
        stop_suffix = ('的', '和', '了', '在', '与', '及')
        freq_hits = [
            c for c, cnt in concept_freq.most_common(80)
            if cnt >= 2
            and not c.startswith(stop_prefix)
            and not c.endswith(stop_suffix)
        ]
        merged_concepts = self._unique_clean(seed_hits + freq_hits, min_len=4, max_len=14, limit=30)
        if merged_concepts:
            knowledge_points['key_concepts'] = merged_concepts
        
        # 5. 提取关键术语/文件名
        key_terms = []
        key_terms.extend(re.findall(r'《([^》]{3,40})》', text))
        key_terms.extend(re.findall(r'[“"]([^”"]{3,30})[”"]', text))
        key_terms.extend(re.findall(r'(?:提出|指出|强调|通过|发布|印发|举行|启动|发射|成立)([^，。；！？]{3,22})', text))
        if key_terms:
            filtered_terms = [
                t for t in key_terms
                if not re.search(r'第\d+页|封面|专题首页|新闻现场|出席人员|相关链接', t)
            ]
            knowledge_points['key_terms'] = self._unique_clean(filtered_terms, min_len=4, max_len=30, limit=25)

        # 6. 样题高频考点（会议/文件/行动代号/重点事件名）
        exam_focus_points = []
        exam_focus_points.extend(re.findall(r'《([^》]{4,50})》', text))
        exam_focus_points.extend(re.findall(r'[“"]([^”"]{2,36})[”"]', text))
        exam_focus_points.extend(
            re.findall(r'([\u4e00-\u9fffA-Za-z0-9\-]{2,24}(?:全会|峰会|大会|会议|条例|方案|决定|报告|演习|行动|开工典礼|世界遗产大会|空间站|载人飞船|月面着陆器|领海基线))', text)
        )
        exam_focus_points = self._unique_clean(exam_focus_points, min_len=3, max_len=40, limit=40)
        if exam_focus_points:
            knowledge_points['exam_focus_points'] = exam_focus_points
        
        # 7. 提取章节标题（以数字或特殊标记开头的行）
        sections = re.findall(r'^(?:\d+[\\.。]|【|●)\s*([^\n]{5,20})', text, re.MULTILINE)
        if sections:
            knowledge_points['sections'] = self._unique_clean(sections, min_len=4, max_len=26, limit=20)
        
        # 8. 计算唯一知识点总数
        total_points = sum(len(v) if isinstance(v, list) else 1 for v in knowledge_points.values())
        knowledge_points['total_unique_points'] = total_points
        
        return knowledge_points
    
    def extract_all_themes(self):
        """为所有主题提取知识点"""
        themes = [
            ('科技.txt', '科技'),
            ('十五五.txt', '十五五'),
            ('军事.txt', '军事'),
            ('国际要闻.txt', '国际要闻'),
            ('探究性专题.txt', '探究性专题'),
            ('文体.txt', '文体'),
            ('热点论坛.txt', '热点论坛'),
            ('环保.txt', '环保'),
        ]
        
        print("=" * 70)
        print("知识点提取和标注 - 8个主题")
        print("=" * 70)
        
        all_results = {}
        
        for filename, theme_name in themes:
            material_file = self.materials_dir / filename
            
            if not material_file.exists():
                print(f"\n✗ 文件不存在: {filename}")
                continue
            
            print(f"\n处理: {theme_name}")
            
            # 读取和清理材料
            with open(material_file, 'r', encoding='utf-8') as f:
                material = f.read()
            
            cleaned = self.clean_material(material)
            
            # 提取知识点
            kps = self.extract_knowledge_points(cleaned)
            
            # 保存结果
            all_results[theme_name] = kps
            
            # 生成标注文件
            self._save_knowledge_points_file(theme_name, kps, cleaned)
            
            # 输出统计
            print(f"  ✓ 材料大小: {len(cleaned):,} 字符")
            print(f"  ✓ 知识点类别: {len(kps)-1} 类")
            print(f"  ✓ 唯一知识点: {kps.get('total_unique_points', 0)} 个")
            
            # 详细输出
            if 'dates' in kps:
                print(f"    - 日期/年份: {len(kps['dates'])} 个")
            if 'numbers' in kps:
                print(f"    - 数字指标: {len(kps['numbers'])} 个")
            if 'organizations' in kps:
                print(f"    - 关键组织: {len(kps['organizations'])} 个")
            if 'key_concepts' in kps:
                print(f"    - 关键概念: {len(kps['key_concepts'])} 个 (Top: {', '.join(kps['key_concepts'][:3])})")
            if 'sections' in kps:
                print(f"    - 章节标题: {len(kps['sections'])} 个")
        
        # 生成综合报告
        self._generate_comprehensive_report(all_results)
        
        return all_results
    
    def _save_knowledge_points_file(self, theme_name, kps, material_text):
        """保存知识点标注文件"""
        filename = self.knowledge_dir / f"{theme_name}_知识点标注.md"
        
        content = f"# {theme_name} - 知识点标注\n\n"
        content += f"**材料统计**: {len(material_text):,} 字符\n"
        content += f"**唯一知识点**: {kps.get('total_unique_points', 0)} 个\n\n"
        
        # 日期
        if 'dates' in kps and kps['dates']:
            content += "## 📅 重要日期\n"
            for date in sorted(kps['dates']):
                content += f"- {date}\n"
            content += f"\n**小计**: {len(kps['dates'])} 个\n\n"

        # 样题高频考点
        if 'exam_focus_points' in kps and kps['exam_focus_points']:
            content += "## ⭐ 参考样题高频考点\n"
            for point in kps['exam_focus_points']:
                content += f"- {point}\n"
            content += f"\n**小计**: {len(kps['exam_focus_points'])} 个\n\n"
        
        # 数字指标
        if 'numbers' in kps and kps['numbers']:
            content += "## 📊 数字指标\n"
            for num in kps['numbers']:
                content += f"- {num}\n"
            content += f"\n**小计**: {len(kps['numbers'])} 个\n\n"
        
        # 关键组织
        if 'organizations' in kps and kps['organizations']:
            content += "## 🏛️ 关键组织/机构\n"
            for org in sorted(kps['organizations']):
                content += f"- {org}\n"
            content += f"\n**小计**: {len(kps['organizations'])} 个\n\n"
        
        # 关键概念
        if 'key_concepts' in kps and kps['key_concepts']:
            content += "## 💡 关键概念\n"
            for concept in kps['key_concepts']:
                content += f"- {concept}\n"
            content += f"\n**小计**: {len(kps['key_concepts'])} 个\n\n"
        
        # 关键术语
        if 'key_terms' in kps and kps['key_terms']:
            content += "## 📖 关键术语/定义\n"
            for term in kps['key_terms']:
                content += f"- {term}\n"
            content += f"\n**小计**: {len(kps['key_terms'])} 个\n\n"
        
        # 章节标题
        if 'sections' in kps and kps['sections']:
            content += "## 📑 章节/栏目标题\n"
            for section in sorted(kps['sections']):
                content += f"- {section}\n"
            content += f"\n**小计**: {len(kps['sections'])} 个\n\n"
        
        content += f"---\n\n**标注日期**: 2026年5月5日\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_comprehensive_report(self, all_results):
        """生成综合覆盖度报告"""
        report_file = self.base_path / "KNOWLEDGE_POINTS_COVERAGE_REPORT.md"
        
        content = "# 8个主题 - 知识点覆盖度综合评估\n\n"
        content += "**评估日期**: 2026年5月5日\n\n"
        
        # 总体统计表
        content += "## 📊 总体统计\n\n"
        content += "| 主题 | 材料大小 | 唯一知识点 | 日期 | 数字 | 组织 | 概念 | 术语 | 章节 |\n"
        content += "|------|--------|----------|------|------|------|------|------|------|\n"
        
        total_points = 0
        for theme, kps in all_results.items():
            material_chars = len(kps.get('_material', ''))
            unique = kps.get('total_unique_points', 0)
            total_points += unique
            
            dates = len(kps.get('dates', []))
            numbers = len(kps.get('numbers', []))
            orgs = len(kps.get('organizations', []))
            concepts = len(kps.get('key_concepts', []))
            terms = len(kps.get('key_terms', []))
            sections = len(kps.get('sections', []))
            
            content += f"| {theme} | {material_chars:,} | {unique} | {dates} | {numbers} | {orgs} | {concepts} | {terms} | {sections} |\n"
        
        content += f"\n**知识点总计**: {total_points} 个\n"
        content += f"**平均每个主题**: {total_points // len(all_results) if all_results else 0} 个\n\n"
        
        # 按类别统计
        content += "## 📈 按类别统计\n\n"
        
        type_stats = {
            'dates': 0,
            'exam_focus_points': 0,
            'numbers': 0,
            'organizations': 0,
            'key_concepts': 0,
            'key_terms': 0,
            'sections': 0,
        }
        
        for theme, kps in all_results.items():
            for key in type_stats:
                type_stats[key] += len(kps.get(key, []))
        
        content += "| 知识点类型 | 总数 | 比例 |\n"
        content += "|----------|------|------|\n"
        
        for key, count in type_stats.items():
            ratio = (count / total_points * 100) if total_points > 0 else 0
            label = {
                'dates': '日期/年份',
                'exam_focus_points': '样题高频考点',
                'numbers': '数字指标',
                'organizations': '关键组织',
                'key_concepts': '关键概念',
                'key_terms': '关键术语',
                'sections': '章节标题',
            }.get(key, key)
            content += f"| {label} | {count} | {ratio:.1f}% |\n"
        
        content += "\n"
        
        # 主题详细评级
        content += "## 🎯 主题详细评级\n\n"
        
        for theme, kps in sorted(all_results.items()):
            unique = kps.get('total_unique_points', 0)
            
            if unique >= 100:
                rating = "⭐⭐⭐ 优秀 (≥100)"
            elif unique >= 50:
                rating = "⭐⭐ 良好 (50-99)"
            elif unique >= 20:
                rating = "⭐ 一般 (20-49)"
            else:
                rating = "✗ 需改进 (<20)"
            
            content += f"### {theme} - {rating}\n"
            content += f"- 唯一知识点: {unique} 个\n"
            
            if 'dates' in kps:
                content += f"- 重要日期: {len(kps['dates'])} 个 {kps['dates'][:3]}\n"
            if 'key_concepts' in kps:
                content += f"- 关键概念: {len(kps['key_concepts'])} 个 (Top3: {', '.join(kps['key_concepts'][:3])})\n"
            if 'organizations' in kps:
                content += f"- 关键组织: {len(kps['organizations'])} 个\n"
            
            content += "\n"
        
        # 建议
        content += "## 💡 建议\n\n"
        content += "1. **优秀主题** (≥100知识点)：可直接用于题库生成\n"
        content += "2. **良好主题** (50-99知识点)：适合题库生成，可适当补充\n"
        content += "3. **一般主题** (20-49知识点)：需手工补充材料或提取\n"
        content += "4. **待改进主题** (<20知识点)：需重新整理材料或寻找补充资源\n\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n" + "=" * 70)
        print(f"✅ 综合报告已保存: {report_file}")
        print("=" * 70)

def main():
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    
    extractor = KnowledgePointsExtractor(base_path)
    results = extractor.extract_all_themes()
    
    print("\n✅ 所有主题的知识点标注已完成！")
    print(f"详见: {extractor.knowledge_dir}/")

if __name__ == "__main__":
    main()
