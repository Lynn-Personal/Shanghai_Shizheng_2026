#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细知识点覆盖度报告
识别每个题库中缺失的关键知识点
"""

import os
import re
from pathlib import Path

class DetailedCoverageReport:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.materials_dir = self.base_path / "materials"
        self.quiz_dir = self.base_path / "online_quiz"
        
    def extract_key_facts(self, text):
        """提取源材料中的关键事实"""
        facts = []
        
        # 提取所有"《..."》"格式的标题
        titles = re.findall(r'《([^》]+)》', text)
        facts.extend([('title', t) for t in titles])
        
        # 提取数字相关的事实
        numbers = re.findall(r'(\d+(?:\.\d+)?(?:万|亿|%)?)(?:人|次|倍|个|年|天|个百分点)?', text)
        facts.extend([('number', n) for n in numbers[:20]])  # 前20个
        
        # 提取日期
        dates = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日', text)
        facts.extend([('date', d) for d in dates])
        
        # 提取人名（通常在3-4个汉字）
        names = re.findall(r'([^\s\d。，；：（）「」『』【】\n\t]{2,4}(?:同志|主席|总书记|总理|部长|主任|委员|院士|教授|博士)?)', text)
        facts.extend([('name', n) for n in names[:15]])
        
        return facts

    def check_coverage(self, facts, quiz_text):
        """检查事实是否在题库中出现"""
        missing = []
        found = []
        
        for fact_type, fact_value in facts:
            # 使用宽松匹配来避免格式差异
            search_value = fact_value.strip()
            if search_value and search_value in quiz_text:
                found.append((fact_type, fact_value))
            elif search_value and len(search_value) > 2:
                missing.append((fact_type, fact_value))
        
        return found, missing
    
    def analyze_theme(self, theme_name, material_file, quiz_file):
        """生成单个主题的详细报告"""
        print(f"\n{'='*70}")
        print(f"【{theme_name}】覆盖度详细分析")
        print(f"{'='*70}")
        
        # 读取源材料和题库
        with open(material_file, 'r', encoding='utf-8') as f:
            material_text = f.read()
        
        with open(quiz_file, 'r', encoding='utf-8') as f:
            quiz_text = f.read()
        
        # 提取关键事实
        facts = self.extract_key_facts(material_text)
        found, missing = self.check_coverage(facts, quiz_text)
        
        # 统计
        coverage_pct = (len(found) / (len(found) + len(missing)) * 100) if (len(found) + len(missing)) > 0 else 0
        
        print(f"\n覆盖统计:")
        print(f"  总发现事实: {len(facts)}")
        print(f"  已覆盖: {len(found)} ({coverage_pct:.1f}%)")
        print(f"  缺失: {len(missing)} ({100-coverage_pct:.1f}%)")
        
        # 显示已覆盖的关键知识点
        print(f"\n✓ 已覆盖的知识点样本 (前10个):")
        for i, (fact_type, fact_value) in enumerate(found[:10]):
            print(f"  {i+1}. [{fact_type:6}] {fact_value}")
        
        # 显示缺失的关键知识点
        if missing:
            print(f"\n✗ 缺失的知识点 (前15个):")
            # 按类型分组显示
            by_type = {}
            for fact_type, fact_value in missing:
                if fact_type not in by_type:
                    by_type[fact_type] = []
                by_type[fact_type].append(fact_value)
            
            idx = 1
            for fact_type in ['title', 'date', 'number', 'name']:
                if fact_type in by_type:
                    print(f"  {fact_type.upper()}:")
                    for value in by_type[fact_type][:5]:
                        print(f"    {idx}. {value}")
                        idx += 1
                        if idx > 15:
                            break
                    if idx > 15:
                        break
        
        # 质量评级
        print(f"\n覆盖度评级:")
        if coverage_pct >= 95:
            print(f"  ✅ 优秀 (95%+) - 知识点覆盖充分，质量优异")
        elif coverage_pct >= 85:
            print(f"  ✓ 良好 (85-94%) - 知识点覆盖良好，可考虑微调")
        elif coverage_pct >= 70:
            print(f"  △ 中等 (70-84%) - 知识点覆盖一般，建议改进")
        elif coverage_pct >= 50:
            print(f"  ✗ 待改进 (50-69%) - 缺失较多关键知识点，需要优化")
        else:
            print(f"  ✗✗ 严重不足 (<50%) - 知识点覆盖严重不足，需完全重做")
        
        print(f"\n建议:")
        if coverage_pct >= 90:
            print(f"  - 当前题库质量优异，可直接用于考试")
        elif coverage_pct >= 75:
            print(f"  - 建议补充缺失的关键知识点到题库中")
        else:
            print(f"  - 强烈建议使用full-coverage-quiz-generator Skill重新生成")
            print(f"  - 需要确保所有关键的日期、数字、标题都被包含")
        
        return {
            'theme': theme_name,
            'coverage': coverage_pct,
            'found': len(found),
            'missing': len(missing),
            'missing_list': missing
        }

def main():
    base_path = r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026"
    
    theme_mappings = {
        '科技': ('科技.txt', 'technology_quiz_data.js'),
        '国际要闻': ('国际要闻.txt', 'international_quiz_data.js'),
        '探究性专题': ('探究性专题.txt', 'research_quiz_data.js'),
        '热点论坛': ('热点论坛.txt', 'hotspot_quiz_data.js'),
        '环保': ('环保.txt', 'environment_quiz_data.js'),
        '十五五': ('十五五.txt', 'wenti_quiz_data.js'),
        '军事': ('军事.txt', 'military_quiz_data.js'),
    }
    
    analyzer = DetailedCoverageReport(base_path)
    results = []
    
    for theme, (material_name, quiz_name) in theme_mappings.items():
        material_path = analyzer.materials_dir / material_name
        quiz_path = analyzer.quiz_dir / quiz_name
        
        if material_path.exists() and quiz_path.exists():
            result = analyzer.analyze_theme(theme, material_path, quiz_path)
            results.append(result)
    
    # 最终总结
    print(f"\n{'='*70}")
    print("COVERAGE SUMMARY")
    print(f"{'='*70}")
    
    sorted_results = sorted(results, key=lambda x: x['coverage'], reverse=True)
    
    print("\n按覆盖度排序:")
    for result in sorted_results:
        coverage = result['coverage']
        status = "✅" if coverage >= 90 else "✓" if coverage >= 75 else "△" if coverage >= 50 else "✗"
        print(f"  {status} {result['theme']:12} {coverage:5.1f}% ({result['found']:3}/{result['found']+result['missing']:3})")
    
    avg_coverage = sum(r['coverage'] for r in results) / len(results) if results else 0
    print(f"\n平均覆盖度: {avg_coverage:.1f}%")
    
    # 识别需要重建的题库
    needs_rebuild = [r for r in results if r['coverage'] < 50]
    if needs_rebuild:
        print(f"\n需要重新生成的题库 (覆盖度 < 50%):")
        for result in needs_rebuild:
            print(f"  - {result['theme']} ({result['coverage']:.1f}%)")
            print(f"    建议使用: full-coverage-quiz-generator Skill")

if __name__ == '__main__':
    main()
