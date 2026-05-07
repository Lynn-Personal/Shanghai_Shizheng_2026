#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合覆盖度评估报告
评估改进后题库的有效知识点覆盖度
包括：知识点类型分析、答案完整性、材料匹配度
"""

import os
import re
import json
from pathlib import Path
from collections import Counter

class ComprehensiveCoverageAssessment:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.quiz_dir = self.base_path / "online_quiz"
        self.materials_dir = self.base_path / "materials"
    
    def extract_quiz_data(self, quiz_file):
        """从JS文件中提取题库数据"""
        with open(quiz_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取quizData数组
        match = re.search(r'const quizData = \[(.*)\];', content, re.DOTALL)
        if not match:
            return []
        
        questions = []
        
        # 提取填空题答案
        fills = re.findall(r"{ type: 'fill'.*?answer:\s*\[(.*?)\]", content, re.DOTALL)
        for fill in fills:
            answers = re.findall(r'"([^"]*)"', fill)
            if answers:
                questions.extend(answers)
        
        # 提取单选题选项
        singles = re.findall(r"{ type: 'single'.*?options:\s*\[(.*?)\]", content, re.DOTALL)
        for single in singles:
            options = re.findall(r'"([^"]*)"', single)
            questions.extend(options)
        
        # 提取多选题选项
        multiples = re.findall(r"{ type: 'multiple'.*?options:\s*\[(.*?)\]", content, re.DOTALL)
        for multiple in multiples:
            options = re.findall(r'"([^"]*)"', multiple)
            questions.extend(options)
        
        # 提取判断题内容
        judges = re.findall(r"{ type: 'judge'.*?question:\s*'([^']*)'", content)
        questions.extend(judges)
        
        return questions
    
    def extract_material_keywords(self, material_file):
        """从材料中提取关键词"""
        with open(material_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取时间、数字、名词等关键信息
        keywords = set()
        
        # 时间
        dates = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月', content)
        keywords.update(dates)
        
        # 大数字
        numbers = re.findall(r'(\d{2,})', content)
        keywords.update(numbers)
        
        # 关键组织名称
        orgs = re.findall(r'[中国|中共|中央|人大|政府|部][\w。]+', content)
        keywords.update(orgs)
        
        return keywords
    
    def calculate_coverage(self, quiz_questions, material_keywords):
        """计算覆盖度"""
        # 将题库中的内容与材料关键词进行匹配
        quiz_text = '\n'.join(quiz_questions)
        
        matched = 0
        for keyword in material_keywords:
            if keyword in quiz_text:
                matched += 1
        
        coverage = (matched / len(material_keywords) * 100) if material_keywords else 0
        return coverage, matched, len(material_keywords)
    
    def assess_all_themes(self):
        """评估所有主题"""
        themes = [
            ('科技', 'technology_quiz_data.js', 'materials/科技.txt'),
            ('十五五', 'wenti_quiz_data.js', 'materials/十五五.txt'),
            ('军事', 'military_quiz_data.js', 'materials/军事.txt'),
        ]
        
        print("\n" + "="*75)
        print("改进后题库的综合覆盖度评估报告")
        print("="*75 + "\n")
        
        total_coverage = 0
        total_matched = 0
        total_keywords = 0
        
        for theme_name, quiz_file, material_file in themes:
            quiz_path = self.quiz_dir / quiz_file
            material_path = self.base_path / material_file
            
            # 提取题库内容
            quiz_questions = self.extract_quiz_data(quiz_path)
            
            # 提取材料关键词
            material_keywords = self.extract_material_keywords(material_path)
            
            # 计算覆盖度
            coverage, matched, total = self.calculate_coverage(quiz_questions, material_keywords)
            
            # 统计题目结构
            with open(quiz_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fill_count = content.count("{ type: 'fill'")
            single_count = content.count("{ type: 'single'")
            multi_count = content.count("{ type: 'multiple'")
            judge_count = content.count("{ type: 'judge'")
            total_count = fill_count + single_count + multi_count + judge_count
            
            # 获取文件大小
            file_size = os.path.getsize(material_path) / 1024
            quiz_size = os.path.getsize(quiz_path) / 1024
            
            print(f"【{theme_name}题库】")
            print(f"  题目结构: {fill_count}填空 + {single_count}单选 + {multi_count}多选 + {judge_count}判断")
            print(f"  总计:    {total_count} 题目")
            print(f"  知识点覆盖: {matched}/{total} = {coverage:.1f}%")
            print(f"  材料大小:   {file_size:.1f} KB  →  题库大小: {quiz_size:.1f} KB")
            
            # 质量等级
            if coverage >= 75:
                level = "✅ 优秀 (≥75%)"
            elif coverage >= 60:
                level = "✓ 良好 (≥60%)"
            elif coverage >= 45:
                level = "△ 中等 (≥45%)"
            else:
                level = "✗ 需改进 (<45%)"
            
            print(f"  评级:    {level}\n")
            
            total_coverage += coverage
            total_matched += matched
            total_keywords += total
        
        # 平均统计
        avg_coverage = total_coverage / 3
        
        print("="*75)
        print(f"平均覆盖度: {avg_coverage:.1f}%")
        print(f"知识点总匹配: {total_matched}/{total_keywords}")
        
        if avg_coverage >= 75:
            overall = "✅ 优秀"
        elif avg_coverage >= 60:
            overall = "✓ 良好"
        elif avg_coverage >= 45:
            overall = "△ 中等"
        else:
            overall = "✗ 需改进"
        
        print(f"综合评级: {overall}")
        print("="*75 + "\n")

def main():
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    
    assessor = ComprehensiveCoverageAssessment(base_path)
    assessor.assess_all_themes()

if __name__ == '__main__':
    main()
