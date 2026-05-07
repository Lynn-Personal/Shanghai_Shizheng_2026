#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将生成的题库转换为标准TXT格式试卷
格式参考：question_examples/样题.txt
"""

import os
import re
import json
from pathlib import Path

class TxtQuizGenerator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.quiz_dir = self.base_path / "online_quiz"
        self.materials_dir = self.base_path / "materials"
        
    def extract_from_js(self, js_file):
        """从JavaScript文件提取题目数据"""
        with open(self.quiz_dir / js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取quizData数组
        match = re.search(r'const quizData = \[(.*)\];', content, re.DOTALL)
        if not match:
            return None
        
        array_str = '[' + match.group(1) + ']'
        
        # 简单的JSON解析（处理JavaScript对象）
        try:
            # 将JavaScript对象转换为JSON
            json_str = array_str.replace("'", '"')
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)
            
            data = json.loads(json_str)
            return data
        except:
            print(f"警告：无法解析 {js_file}")
            return None
    
    def generate_txt_quiz(self, js_file, material_name, output_file):
        """生成TXT格式试卷"""
        data = self.extract_from_js(js_file)
        if not data:
            return False
        
        # 分类题目
        fill_questions = []
        single_questions = []
        multiple_questions = []
        judge_questions = []
        
        for item in data:
            if item.get('type') == 'fill':
                fill_questions.append(item)
            elif item.get('type') == 'single':
                single_questions.append(item)
            elif item.get('type') == 'multiple':
                multiple_questions.append(item)
            elif item.get('type') == 'judge':
                judge_questions.append(item)
        
        # 生成TXT文件
        txt_content = f"{material_name}模拟题\n\n"
        txt_content += "一、填空题（每小题2分，共{}分。写错别字不得分。）\n\n".format(len(fill_questions) * 2)
        
        for i, q in enumerate(fill_questions, 1):
            question = q.get('question', '')
            answer = q.get('answer', [''])[0] if q.get('answer') else ''
            txt_content += f"{i}. {question}\n"
            txt_content += f"答案：{answer}\n\n"
        
        txt_content += "二、单项选择题（每小题2分，共{}分。四个选项中，只有一个选项最符合题意。）\n\n".format(len(single_questions) * 2)
        
        for i, q in enumerate(single_questions, 1):
            question = q.get('question', '')
            options = q.get('options', [])
            answer_idx = q.get('answer', [0])[0]
            
            txt_content += f"{i}. {question}\n"
            
            choices = ['A', 'B', 'C', 'D']
            for j, option in enumerate(options[:4]):
                txt_content += f"{choices[j]}. {option}\n"
            
            if answer_idx < len(choices):
                txt_content += f"答案：{choices[answer_idx]}\n\n"
            else:
                txt_content += f"\n"
        
        txt_content += "三、多项选择题（每小题3分，共{}分。四个选项中，至少有两个选项符合题意。错选、多选、漏选，该题不得分。）\n\n".format(len(multiple_questions) * 3)
        
        for i, q in enumerate(multiple_questions, 1):
            question = q.get('question', '')
            options = q.get('options', [])
            answer_indices = q.get('answer', [0])
            
            txt_content += f"{i}. {question}\n"
            
            choices = ['A', 'B', 'C', 'D']
            for j, option in enumerate(options[:4]):
                txt_content += f"{choices[j]}. {option}\n"
            
            answer_choices = [choices[idx] for idx in answer_indices if idx < len(choices)]
            txt_content += f"答案：{', '.join(answer_choices)}\n\n"
        
        txt_content += "四、判断题（每小题1分，共{}分。正确打√，错误打×。）\n\n".format(len(judge_questions) * 1)
        
        for i, q in enumerate(judge_questions, 1):
            question = q.get('question', '')
            answer = q.get('answer', [0])[0]
            
            txt_content += f"{i}. {question}\n"
            txt_content += f"答案：{'√' if answer else '×'}\n\n"
        
        # 保存文件
        with open(self.base_path / output_file, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        print(f"✓ 生成: {output_file}")
        print(f"  - 填空题: {len(fill_questions)}")
        print(f"  - 单选题: {len(single_questions)}")
        print(f"  - 多选题: {len(multiple_questions)}")
        print(f"  - 判断题: {len(judge_questions)}")
        
        return True

def main():
    base_path = r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026"
    
    generator = TxtQuizGenerator(base_path)
    
    themes = [
        ('technology_quiz_data.js', '科技', '科技模拟题.txt'),
        ('wenti_quiz_data.js', '十五五', '十五五模拟题.txt'),
        ('military_quiz_data.js', '军事', '军事模拟题.txt'),
    ]
    
    print("="*60)
    print("生成TXT格式标准试卷")
    print("="*60 + "\n")
    
    for js_file, material_name, output_file in themes:
        generator.generate_txt_quiz(js_file, material_name, output_file)
        print()
    
    print("="*60)
    print("✅ 转换完成！")
    print("="*60)

if __name__ == '__main__':
    main()
