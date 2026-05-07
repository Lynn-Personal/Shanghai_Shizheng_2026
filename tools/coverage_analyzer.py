#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识点覆盖度分析工具
检查所有题库文件的知识点覆盖情况
"""

import os
import json
import re
from collections import defaultdict
from pathlib import Path

class CoverageAnalyzer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.materials_dir = self.base_path / "materials"
        self.quiz_dir = self.base_path / "online_quiz"
        
    def extract_knowledge_points(self, text):
        """提取文本中的关键知识点"""
        points = {
            'dates': set(),      # 日期
            'numbers': set(),    # 数字
            'names': set(),      # 人名、机构名
            'places': set(),     # 地点
            'concepts': set(),   # 概念
        }
        
        # 提取日期 (YYYY年MM月DD日格式)
        dates = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日', text)
        points['dates'].update(dates)
        
        # 提取日期 (YYYY年MM月格式)
        dates_ym = re.findall(r'\d{4}年\d{1,2}月', text)
        points['dates'].update(dates_ym)
        
        # 提取中文数字和百分比
        numbers = re.findall(r'\d+[万亿年个%\s]*(?:人|次|倍|岁|年|个|件|个百分点|个百分比)', text)
        points['numbers'].update(numbers)
        
        # 提取"《...》"中的标题、计划名
        titles = re.findall(r'《([^》]+)》', text)
        points['concepts'].update(titles)
        
        # 提取"...计划/工程/倡议"等
        concepts = re.findall(r'([^\s。，\n]{2,15}(?:计划|工程|倡议|法|制|报告|方案|中心|基地|区域|城市))', text)
        points['concepts'].update(concepts[:20])  # 限制数量
        
        return points
    
    def load_quiz_data(self, quiz_file):
        """从JS文件中提取题库数据"""
        with open(quiz_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取 const quizData = [...]
        match = re.search(r'const quizData = \[(.*)\];', content, re.DOTALL)
        if not match:
            return []
        
        try:
            # 简单的JSON-like解析（不完全的JSON）
            quiz_text = match.group(1)
            # 计算题目数量和问题文本
            return quiz_text
        except:
            return ""
    
    def analyze_theme(self, theme_name, material_file, quiz_file):
        """分析单个主题的覆盖度"""
        result = {
            'theme': theme_name,
            'material_file': material_file.name,
            'quiz_file': quiz_file.name,
            'coverage_score': 0,
            'details': {}
        }
        
        # 读取源材料
        with open(material_file, 'r', encoding='utf-8') as f:
            material_text = f.read()
        
        # 提取源材料中的知识点
        source_points = self.extract_knowledge_points(material_text)
        
        # 读取题库
        quiz_text = self.load_quiz_data(quiz_file)
        
        # 计算覆盖率
        coverage_stats = {
            'dates': 0,
            'numbers': 0,
            'names': 0,
            'concepts': 0
        }
        
        total_points = sum(len(v) for v in source_points.values())
        found_points = 0
        
        # 检查每个知识点是否在题库中
        for category, points in source_points.items():
            for point in points:
                if point in quiz_text:
                    found_points += 1
                    coverage_stats[category] += 1
        
        if total_points > 0:
            coverage_pct = (found_points / total_points) * 100
        else:
            coverage_pct = 0
        
        result['coverage_score'] = round(coverage_pct, 1)
        result['coverage_details'] = {
            'total_points': total_points,
            'found_points': found_points,
            'coverage_rate': f"{coverage_pct:.1f}%",
            'by_category': coverage_stats
        }
        result['source_points_sample'] = {
            'dates': list(sorted(source_points['dates']))[:5],
            'numbers': list(source_points['numbers'])[:5],
            'concepts': list(source_points['concepts'])[:5]
        }
        
        return result
    
    def run_analysis(self):
        """运行完整分析"""
        # 主题映射
        theme_mappings = {
            '科技': ('科技.txt', 'technology_quiz_data.js'),
            '国际要闻': ('国际要闻.txt', 'international_quiz_data.js'),
            '探究性专题': ('探究性专题.txt', 'research_quiz_data.js'),
            '热点论坛': ('热点论坛.txt', 'hotspot_quiz_data.js'),
            '环保': ('环保.txt', 'environment_quiz_data.js'),
            '十五五': ('十五五.txt', 'wenti_quiz_data.js'),
            '军事': ('军事.txt', 'military_quiz_data.js'),
            '文体': ('文体.txt', None),  # 可能没有对应的自动生成版本
        }
        
        results = []
        
        for theme, (material_name, quiz_name) in theme_mappings.items():
            material_path = self.materials_dir / material_name
            quiz_path = self.quiz_dir / quiz_name if quiz_name else None
            
            if material_path.exists() and quiz_path and quiz_path.exists():
                print(f"分析中: {theme}...", end=" ")
                result = self.analyze_theme(theme, material_path, quiz_path)
                results.append(result)
                print(f"✓ 覆盖度: {result['coverage_score']}%")
            else:
                print(f"跳过: {theme} (文件缺失)")
        
        return results

def main():
    base_path = r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026"
    
    print("="*60)
    print("知识点覆盖度分析")
    print("="*60)
    print()
    
    analyzer = CoverageAnalyzer(base_path)
    results = analyzer.run_analysis()
    
    print("\n" + "="*60)
    print("分析结果汇总")
    print("="*60)
    print()
    
    # 汇总统计
    for result in sorted(results, key=lambda x: x['coverage_score'], reverse=True):
        theme = result['theme']
        score = result['coverage_score']
        details = result['coverage_details']
        
        # 根据覆盖度给出评级
        if score >= 90:
            rating = "✅ 优秀"
        elif score >= 75:
            rating = "✓ 良好"
        elif score >= 60:
            rating = "△ 中等"
        else:
            rating = "✗ 需改进"
        
        print(f"{theme:15} | 覆盖度: {score:5.1f}% | {rating:8} | "
              f"知识点: {details['found_points']}/{details['total_points']}")
        
        # 显示各类别覆盖情况
        cat_stats = details['by_category']
        print(f"{'':15} | 日期: {cat_stats.get('dates',0)}, "
              f"数字: {cat_stats.get('numbers',0)}, "
              f"概念: {cat_stats.get('concepts',0)}")
        print()
    
    # 计算总体统计
    avg_score = sum(r['coverage_score'] for r in results) / len(results) if results else 0
    print("-"*60)
    print(f"平均覆盖度: {avg_score:.1f}%")
    print()
    
    # 生成详细报告
    print("="*60)
    print("详细知识点样本")
    print("="*60)
    print()
    
    for result in results:
        print(f"\n【{result['theme']}】")
        sample = result['source_points_sample']
        print(f"  核心日期: {', '.join(sample['dates'][:3])}")
        print(f"  关键数字: {', '.join(sample['numbers'][:3])}")
        print(f"  重要概念: {', '.join(sample['concepts'][:3])}")

if __name__ == '__main__':
    main()
