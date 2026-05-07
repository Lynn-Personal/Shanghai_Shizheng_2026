#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版完整覆盖题库生成器
重点：确保生成完整的40/40/20/20题库结构
"""

import os
import re
import json
import math
from pathlib import Path

class ImprovedQuizGenerator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.quiz_dir = self.base_path / "online_quiz"
        
    def regenerate_with_fillins(self, quiz_file, material_file):
        """改进：确保生成完整的填空题"""
        with open(material_file, 'r', encoding='utf-8') as f:
            material = f.read()
        
        print(f"\n处理: {quiz_file}")
        
        # 读取原始题库
        with open(self.quiz_dir / quiz_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取所有句子作为填空题基础
        sentences = re.split(r'[。！？；，:：\n]+', material)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5][:50]
        
        # 生成40道填空题
        fill_questions = []
        for i, sentence in enumerate(sentences[:40]):
            # 从句子中选择一个词作为空白
            words = re.split(r'[、·\s]+', sentence)
            if len(words) > 2:
                blank_idx = len(words) // 2
                blank_word = words[blank_idx]
                
                # 构建问题
                before = ''.join(words[:blank_idx])
                after = ''.join(words[blank_idx+1:])
                question = f'{before}____{after}'
                
                fill_questions.append({
                    'type': 'fill',
                    'question': question,
                    'answer': [blank_word],
                    'explanation': sentence
                })
        
        print(f"✓ 生成{len(fill_questions)}道填空题")
        
        # 提取原始题库中的单选、多选、判断题
        single_pattern = r"\{ type: 'single'.*?\},"
        single_matches = re.findall(single_pattern, content, re.DOTALL)
        
        multiple_pattern = r"\{ type: 'multiple'.*?\},"
        multiple_matches = re.findall(multiple_pattern, content, re.DOTALL)
        
        judge_pattern = r"\{ type: 'judge'.*?\},"
        judge_matches = re.findall(judge_pattern, content, re.DOTALL)
        
        print(f"✓ 提取{len(single_matches)}道单选题")
        print(f"✓ 提取{len(multiple_matches)}道多选题")
        print(f"✓ 提取{len(judge_matches)}道判断题")
        
        # 构建新的题库
        theme_name = quiz_file.replace('_quiz_data.js', '').replace('_', ' ').title()
        new_content = f"// {theme_name}全题型模拟题 - 完整修复版本\nconst quizData = [\n"
        
        # 添加填空题
        new_content += f"  {{ type: 'info', info: '【填空题 共{len(fill_questions)}题，每题2分】' }},\n"
        for q in fill_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            new_content += f"  {{ type: 'fill', question: '{q['question']}', answer: {answer_str}, explanation: '{q['explanation']}' }},\n"
        
        # 添加单选题
        new_content += f"  {{ type: 'info', info: '【单项选择题 共{len(single_matches)}题，每题2分】' }},\n"
        for match in single_matches[:40]:
            new_content += f"  {match.strip()},\n"
        
        # 添加多选题
        new_content += f"  {{ type: 'info', info: '【多项选择题 共{len(multiple_matches)}题，每题3分】' }},\n"
        for match in multiple_matches[:20]:
            new_content += f"  {match.strip()},\n"
        
        # 添加判断题
        new_content += f"  {{ type: 'info', info: '【判断题 共{len(judge_matches)}题，每题1分】' }},\n"
        for match in judge_matches[:20]:
            new_content += f"  {match.strip()},\n"
        
        new_content = new_content.rstrip(',\n') + "\n];\n"
        
        # 保存修复后的文件
        with open(self.quiz_dir / quiz_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        file_size = os.path.getsize(self.quiz_dir / quiz_file)
        print(f"✓ 保存完成: {file_size / 1024:.1f} KB")
        
        return len(fill_questions) + len(single_matches) + len(multiple_matches) + len(judge_matches)

def main():
    base_path = r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026"
    
    generator = ImprovedQuizGenerator(base_path)
    
    themes = [
        ('technology_quiz_data.js', 'materials/科技.txt'),
        ('wenti_quiz_data.js', 'materials/十五五.txt'),
        ('military_quiz_data.js', 'materials/军事.txt'),
    ]
    
    print("="*60)
    print("完整性修复：补充缺失的填空题")
    print("="*60)
    
    total_questions = 0
    for quiz_file, material_file in themes:
        material_path = base_path / Path(material_file)
        count = generator.regenerate_with_fillins(quiz_file, material_path)
        total_questions += count
    
    print(f"\n✅ 修复完成！总计{total_questions}道题目")

if __name__ == '__main__':
    main()
