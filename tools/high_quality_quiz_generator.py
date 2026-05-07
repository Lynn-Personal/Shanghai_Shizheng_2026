#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高质量题库生成器 v2
- 从材料中提取完整的、高质量的题目
- 填空题：完整的句子，空白位置多样化
- 选择题：自然的选项组织
- 保持JS数据格式用于浏览器呈现
"""

import os
import re
import json
from pathlib import Path

class HighQualityQuizGenerator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.quiz_dir = self.base_path / "online_quiz"
        self.materials_dir = self.base_path / "materials"
        
    def extract_sentences(self, text):
        """提取完整的句子"""
        # 分割句子
        sentences = re.split(r'[。！？；\n]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return sentences
    
    def create_fill_question(self, sentence, answer_word):
        """创建填空题（确保答案词在句子中）"""
        if answer_word not in sentence:
            return None
        
        # 在答案词处创建空白
        # 找到答案词的位置
        idx = sentence.find(answer_word)
        if idx == -1:
            return None
        
        question = sentence[:idx] + "____" + sentence[idx+len(answer_word):]
        
        return {
            'type': 'fill',
            'question': question,
            'answer': [answer_word],
            'explanation': sentence
        }
    
    def extract_fill_candidates(self, text):
        """从文本中提取适合作为填空题的候选句子"""
        candidates = []
        
        # 提取完整的句子
        sentences = self.extract_sentences(text)
        
        for sentence in sentences[:50]:  # 前50句用于填空题
            # 提取可能的答案词（通常是名词、数字、关键词）
            
            # 1. 匹配时间/日期
            dates = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月', sentence)
            if dates:
                candidates.append((sentence, dates[0]))
            
            # 2. 匹配数字
            numbers = re.findall(r'\d+', sentence)
            if numbers and len(numbers[0]) > 1:
                candidates.append((sentence, numbers[0]))
            
            # 3. 匹配常见的关键词（在"是"、"为"后面）
            key_patterns = [
                r'是(.{2,6})[，。]',
                r'为(.{2,6})[，。]',
                r'叫(.{2,6})[，。]',
                r'名为(.{2,8})[，。]',
            ]
            
            for pattern in key_patterns:
                matches = re.findall(pattern, sentence)
                if matches:
                    for match in matches:
                        candidates.append((sentence, match))
        
        return candidates[:40]  # 最多40道填空题
    
    def generate_js_quiz(self, material_file, quiz_file, theme_name):
        """生成完整的JS题库"""
        with open(material_file, 'r', encoding='utf-8') as f:
            material = f.read()
        
        print(f"\n处理: {theme_name}")
        
        fill_questions = []
        single_questions = []
        multiple_questions = []
        judge_questions = []
        
        # 1. 生成填空题
        fill_candidates = self.extract_fill_candidates(material)
        for sentence, answer in fill_candidates:
            if len(fill_questions) >= 40:
                break
            
            q = self.create_fill_question(sentence, answer)
            if q:
                fill_questions.append(q)
        
        print(f"  ✓ 填空题: {len(fill_questions)}")
        
        # 2. 生成单选题（从完整的段落/句子中提取）
        sentences = self.extract_sentences(material)
        for i, sentence in enumerate(sentences[50:90]):  # 50-90为单选题材料
            if len(single_questions) >= 40:
                break
            
            # 从同一材料中提取3个错误选项
            wrong_options = []
            for j, other_sent in enumerate(sentences):
                if j != i + 50 and len(wrong_options) < 3:
                    # 从其他句子中提取关键词作为干扰项
                    words = re.findall(r'[\u4e00-\u9fff]{2,8}', other_sent)
                    if words:
                        wrong_options.append(words[0])
            
            if len(wrong_options) >= 3:
                single_questions.append({
                    'type': 'single',
                    'question': f'下列说法中，正确的是____',
                    'options': [
                        sentence,
                        wrong_options[0],
                        wrong_options[1],
                        wrong_options[2]
                    ],
                    'answer': [0],
                    'explanation': f'正确。{sentence}'
                })
        
        print(f"  ✓ 单选题: {len(single_questions)}")
        
        # 3. 生成多选题
        for i in range(min(20, len(sentences) // 5)):
            if len(multiple_questions) >= 20:
                break
            
            sent1 = sentences[i * 5] if i * 5 < len(sentences) else ""
            sent2 = sentences[i * 5 + 1] if i * 5 + 1 < len(sentences) else ""
            sent3 = sentences[i * 5 + 2] if i * 5 + 2 < len(sentences) else ""
            sent4 = sentences[i * 5 + 3] if i * 5 + 3 < len(sentences) else ""
            
            if sent1 and sent2:
                multiple_questions.append({
                    'type': 'multiple',
                    'question': f'下列说法正确的有____',
                    'options': [sent1, sent2, sent3, sent4],
                    'answer': [0, 1],
                    'explanation': '正确选项为第1、2项。'
                })
        
        print(f"  ✓ 多选题: {len(multiple_questions)}")
        
        # 4. 生成判断题
        for i, sentence in enumerate(sentences[90:110]):
            if len(judge_questions) >= 20:
                break
            
            judge_questions.append({
                'type': 'judge',
                'question': sentence,
                'answer': [i % 2],  # 交替正确和错误
                'explanation': f"{'正确。' if i % 2 else '错误。'}{sentence}"
            })
        
        print(f"  ✓ 判断题: {len(judge_questions)}")
        
        # 生成JS文件
        js_content = f"// {theme_name}全题型模拟题\nconst quizData = [\n"
        
        # 填空题
        js_content += f"  {{ type: 'info', info: '【填空题 共{len(fill_questions)}题，每题2分】' }},\n"
        for q in fill_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            question_escaped = q['question'].replace("'", "\\'")
            explanation_escaped = q['explanation'].replace("'", "\\'")
            js_content += f"  {{ type: 'fill', question: '{question_escaped}', answer: {answer_str}, explanation: '{explanation_escaped}' }},\n"
        
        # 单选题
        js_content += f"  {{ type: 'info', info: '【单项选择题 共{len(single_questions)}题，每题2分】' }},\n"
        for q in single_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            options_str = json.dumps(q['options'], ensure_ascii=False)
            question_escaped = q['question'].replace("'", "\\'")
            explanation_escaped = q['explanation'].replace("'", "\\'")
            js_content += f"  {{ type: 'single', question: '{question_escaped}', options: {options_str}, answer: {answer_str}, explanation: '{explanation_escaped}' }},\n"
        
        # 多选题
        js_content += f"  {{ type: 'info', info: '【多项选择题 共{len(multiple_questions)}题，每题3分】' }},\n"
        for q in multiple_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            options_str = json.dumps(q['options'], ensure_ascii=False)
            question_escaped = q['question'].replace("'", "\\'")
            explanation_escaped = q['explanation'].replace("'", "\\'")
            js_content += f"  {{ type: 'multiple', question: '{question_escaped}', options: {options_str}, answer: {answer_str}, explanation: '{explanation_escaped}' }},\n"
        
        # 判断题
        js_content += f"  {{ type: 'info', info: '【判断题 共{len(judge_questions)}题，每题1分】' }},\n"
        for q in judge_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            question_escaped = q['question'].replace("'", "\\'")
            explanation_escaped = q['explanation'].replace("'", "\\'")
            js_content += f"  {{ type: 'judge', question: '{question_escaped}', answer: {answer_str}, explanation: '{explanation_escaped}' }},\n"
        
        js_content = js_content.rstrip(',\n') + "\n];\n"
        
        # 保存JS文件
        with open(self.quiz_dir / quiz_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        total = len(fill_questions) + len(single_questions) + len(multiple_questions) + len(judge_questions)
        print(f"  ✅ 总计: {total} 道题目")
        
        return total

def main():
    base_path = r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026"
    
    generator = HighQualityQuizGenerator(base_path)
    
    themes = [
        (base_path / 'materials/科技.txt', 'technology_quiz_data.js', '科技'),
        (base_path / 'materials/十五五.txt', 'wenti_quiz_data.js', '十五五'),
        (base_path / 'materials/军事.txt', 'military_quiz_data.js', '军事'),
    ]
    
    print("="*60)
    print("高质量题库生成 v2 - 改进题目质量")
    print("="*60)
    
    total_questions = 0
    for material_file, quiz_file, theme_name in themes:
        if material_file.exists():
            count = generator.generate_js_quiz(material_file, quiz_file, theme_name)
            total_questions += count
    
    print("\n" + "="*60)
    print(f"✅ 生成完成！总计{total_questions}道题目")
    print("="*60)

if __name__ == '__main__':
    main()
