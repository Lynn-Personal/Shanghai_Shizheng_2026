#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进后的覆盖度评估工具
评估最新生成的题库的知识点覆盖效果
"""

import os
import re
from pathlib import Path

def count_knowledge_points(quiz_file):
    """统计题库中出现的知识点数量"""
    with open(quiz_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有answer字段中的值
    # 匹配 answer: [xxx] 格式，其中xxx可以是数字或字符串
    answers = re.findall(r'answer:\s*\[(.*?)\]', content)
    
    # 统计唯一的知识点
    knowledge_points = set()
    for answer_str in answers:
        # 提取引号内的内容（答案文本）或数字（答案索引）
        # 格式1: ["2025年11月1日"] 
        # 格式2: [0] 
        text_answers = re.findall(r'"([^"]*)"', answer_str)
        if text_answers:
            knowledge_points.update(text_answers)
        else:
            # 如果没有引号，可能是数字选项索引
            if answer_str.strip():
                knowledge_points.add(answer_str.strip())
    
    return len(knowledge_points)

def evaluate_coverage():
    """评估覆盖度"""
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    quiz_dir = base_path / "online_quiz"
    materials_dir = base_path / "materials"
    
    themes = [
        ('科技', 'technology_quiz_data.js', 'materials/科技.txt'),
        ('十五五', 'wenti_quiz_data.js', 'materials/十五五.txt'),
        ('军事', 'military_quiz_data.js', 'materials/军事.txt'),
    ]
    
    print("\n" + "="*70)
    print("改进后题库的有效知识点覆盖度评估")
    print("="*70 + "\n")
    
    total_stats = {
        'quiz_knowledge_points': 0,
        'material_chars': 0,
        'quiz_questions': 0
    }
    
    for theme_name, quiz_file, material_file in themes:
        quiz_path = quiz_dir / quiz_file
        material_path = base_path / material_file
        
        # 统计题库中的知识点
        with open(quiz_path, 'r', encoding='utf-8') as f:
            quiz_content = f.read()
        
        knowledge_points = count_knowledge_points(quiz_path)
        
        # 统计题目数量
        q_count = quiz_content.count("{ type: 'fill'") + \
                 quiz_content.count("{ type: 'single'") + \
                 quiz_content.count("{ type: 'multiple'") + \
                 quiz_content.count("{ type: 'judge'")
        
        # 统计材料字数
        with open(material_path, 'r', encoding='utf-8') as f:
            material_content = f.read()
        
        material_chars = len(material_content)
        
        # 统计填空题、单选题、多选题、判断题
        fill_count = quiz_content.count("{ type: 'fill'")
        single_count = quiz_content.count("{ type: 'single'")
        multiple_count = quiz_content.count("{ type: 'multiple'")
        judge_count = quiz_content.count("{ type: 'judge'")
        
        # 计算覆盖率
        coverage = (knowledge_points / max(1, material_chars)) * 100 if material_chars > 0 else 0
        
        print(f"【{theme_name}题库】")
        print(f"  知识点数: {knowledge_points}")
        print(f"  题目构成: {fill_count}填+{single_count}单+{multiple_count}多+{judge_count}判 = {q_count}题")
        print(f"  材料字数: {material_chars}")
        print(f"  题库大小: {os.path.getsize(quiz_path) / 1024:.1f} KB")
        print(f"  覆盖率:   {coverage:.1f}%")
        
        # 质量评价
        if coverage >= 80:
            level = "✅ 优秀"
        elif coverage >= 60:
            level = "✓ 良好"
        elif coverage >= 40:
            level = "△ 中等"
        else:
            level = "✗ 需改进"
        
        print(f"  评级:    {level}\n")
        
        total_stats['quiz_knowledge_points'] += knowledge_points
        total_stats['material_chars'] += material_chars
        total_stats['quiz_questions'] += q_count
    
    # 平均覆盖率
    avg_coverage = (total_stats['quiz_knowledge_points'] / max(1, total_stats['material_chars'] // 3)) * 100
    
    print("="*70)
    print(f"平均覆盖率: {avg_coverage:.1f}%")
    print(f"总题库规模: {total_stats['quiz_questions']}题")
    print(f"知识点总数: {total_stats['quiz_knowledge_points']}")
    print("="*70 + "\n")

if __name__ == '__main__':
    evaluate_coverage()
