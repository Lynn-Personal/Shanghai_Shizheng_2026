#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优先级感知的题库生成器
只使用高优先级(2025年及以后)的知识点生成题库
"""

import re
import json
from pathlib import Path
from collections import Counter

class PriorityAwareQuizGenerator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.quiz_dir = self.base_path / "online_quiz"
        self.materials_dir = self.base_path / "materials"
        self.priority_dir = self.base_path / "knowledge_points_priority"
        
        self.priority_years = {2024, 2025, 2026}
        self.priority_start_month = 9
        
        self.filter_patterns = [
            r'^[第\d]+页.*',
            r'^新闻现场\s*$',
            r'^背景资料.*',
            r'^责任编辑.*',
            r'^邮箱.*',
            r'^美术编辑.*',
        ]
    
    def should_filter(self, text):
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
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if not self.should_filter(line):
                cleaned_lines.append(line.strip())
        
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = re.sub(r'\n\n+', '\n', cleaned_text)
        
        return cleaned_text
    
    def normalize_text(self, text):
        text = re.sub(r'\n+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def load_high_priority_concepts(self, theme_name):
        """加载主题的高优先级知识点"""
        priority_file = self.priority_dir / f"{theme_name}_优先级分类.md"
        
        if not priority_file.exists():
            return []
        
        concepts = []
        in_high_section = False
        
        with open(priority_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('## 🔴 高优先级'):
                    in_high_section = True
                elif line.startswith('## ⚪ 低优先级'):
                    in_high_section = False
                elif in_high_section and line.startswith('| ') and '|' in line:
                    # 表格行：| 知识点 | 分类 |
                    parts = line.split('|')
                    if len(parts) >= 3:
                        concept = parts[1].strip()
                        if concept and concept not in ['知识点', '---']:
                            concepts.append(concept)
        
        return concepts
    
    def extract_knowledge_chunks(self, text):
        chunks = []
        sections = re.split(r'\n(?=\d+[\\.。]|\s*【|\s*●)', text)
        
        for section in sections:
            section = section.strip()
            section = re.sub(r'\s+', ' ', section)
            if len(section) > 20:
                chunks.append(section)
        
        return chunks
    
    def create_fill_question(self, sentence, high_priority_concepts):
        """创建填空题，优先使用高优先级知识点"""
        sentence = self.normalize_text(sentence)
        
        if len(sentence) < 15:
            return None
        
        # 优先从高优先级知识点中找答案
        for concept in high_priority_concepts:
            if concept in sentence and len(concept) >= 2:
                question = sentence.replace(concept, '____', 1)
                return {
                    'type': 'fill',
                    'question': question,
                    'answer': [concept],
                    'explanation': sentence,
                    'priority': 'high'
                }
        
        # 回退到标准方法
        # 1. 日期
        date_match = re.search(r'\d{4}年\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月', sentence)
        if date_match:
            date = date_match.group()
            question = sentence.replace(date, '____', 1)
            return {
                'type': 'fill',
                'question': question,
                'answer': [date],
                'explanation': sentence,
                'priority': 'date'
            }
        
        # 2. 数字
        num_match = re.search(r'[一二三四五六七八九十百千万亿]+|[0-9]{2,}', sentence)
        if num_match:
            num = num_match.group()
            if len(num) > 1:
                question = sentence.replace(num, '____', 1)
                return {
                    'type': 'fill',
                    'question': question,
                    'answer': [num],
                    'explanation': sentence,
                    'priority': 'number'
                }
        
        return None
    
    def generate_js_quiz(self, material_file, quiz_file, theme_name, target_questions=120):
        """生成JS题库，优先使用高优先级知识点"""
        with open(material_file, 'r', encoding='utf-8') as f:
            material = f.read()
        
        print(f"\n处理: {theme_name}")
        
        # 加载高优先级知识点
        high_priority_concepts = self.load_high_priority_concepts(theme_name)
        print(f"  ✓ 高优先级知识点: {len(high_priority_concepts)} 个")
        
        cleaned = self.clean_material(material)
        chunks = self.extract_knowledge_chunks(cleaned)
        
        # 提取句子
        sentences = []
        for chunk in chunks:
            sents = re.split(r'[。！？；，]+', chunk)
            for sent in sents:
                sent = sent.strip()
                if len(sent) > 8:
                    sentences.append(sent)
        
        print(f"  ✓ 知识点句子: {len(sentences)} 条")
        
        fill_questions = []
        single_questions = []
        multiple_questions = []
        judge_questions = []
        
        # 优先生成高优先级相关的填空题
        for sent in sentences:
            if len(fill_questions) >= 20:
                break
            
            q = self.create_fill_question(sent, high_priority_concepts)
            if q and q.get('priority') == 'high':
                fill_questions.append(q)
        
        # 再补充其他填空题
        for sent in sentences:
            if len(fill_questions) >= 40:
                break
            
            q = self.create_fill_question(sent, high_priority_concepts)
            if q and q not in fill_questions:
                fill_questions.append(q)
        
        # 生成单选题
        for i, sent in enumerate(sentences):
            if len(single_questions) >= 40:
                break
            
            sent = self.normalize_text(sent)
            if len(sent) < 10:
                continue
            
            # 检查是否涉及高优先级知识点
            has_priority_kp = any(kp in sent for kp in high_priority_concepts)
            
            wrong_options = set()
            for j, other in enumerate(sentences):
                if len(wrong_options) >= 3:
                    break
                if abs(j - i) > 5:
                    other = self.normalize_text(other)
                    phrases = re.findall(r'[\u4e00-\u9fff]{4,15}', other)
                    if phrases:
                        wrong_options.add(phrases[0])
            
            if len(wrong_options) >= 3:
                options = [sent] + list(wrong_options)[:3]
                priority = 'high' if has_priority_kp else 'medium'
                
                single_questions.append({
                    'type': 'single',
                    'question': '根据材料，下列哪项表述正确？',
                    'options': options,
                    'answer': [0],
                    'explanation': f'正确。{sent}',
                    'priority': priority
                })
        
        # 生成多选题
        for i in range(min(20, len(sentences) // 2)):
            if len(multiple_questions) >= 20:
                break
            
            idx = i * 2
            if idx + 1 < len(sentences):
                sent1 = self.normalize_text(sentences[idx])
                sent2 = self.normalize_text(sentences[idx + 1])
                sent3 = self.normalize_text(sentences[idx + 2]) if idx + 2 < len(sentences) else ""
                sent4 = self.normalize_text(sentences[idx + 3]) if idx + 3 < len(sentences) else ""
                
                options = [s for s in [sent1, sent2, sent3, sent4] if len(s) > 5]
                if len(options) >= 4:
                    # 检查是否涉及高优先级知识点
                    has_priority_kp = any(
                        any(kp in opt for kp in high_priority_concepts) 
                        for opt in options
                    )
                    priority = 'high' if has_priority_kp else 'medium'
                    
                    multiple_questions.append({
                        'type': 'multiple',
                        'question': '下列说法正确的有____',
                        'options': options,
                        'answer': [0, 1],
                        'explanation': '正确选项为第1、2项。',
                        'priority': priority
                    })
        
        # 生成判断题
        judge_idx = 0
        for i in range(20):
            if judge_idx < len(sentences):
                question = self.normalize_text(sentences[judge_idx])
                if len(question) > 5:
                    has_priority_kp = any(kp in question for kp in high_priority_concepts)
                    priority = 'high' if has_priority_kp else 'medium'
                    
                    judge_questions.append({
                        'type': 'judge',
                        'question': question,
                        'answer': [i % 2],
                        'explanation': f"{'正确。' if i % 2 else '错误。'}{question}",
                        'priority': priority
                    })
                judge_idx += 1
        
        # 补充至目标数量
        total = len(fill_questions) + len(single_questions) + len(multiple_questions) + len(judge_questions)
        print(f"  ⚠ 当前{total}题 < {target_questions}题，使用高优先级知识点补充...")
        
        if total < target_questions and high_priority_concepts:
            self._supplement_with_priority(
                high_priority_concepts, sentences,
                fill_questions, single_questions, multiple_questions, judge_questions,
                target_questions
            )
        
        print(f"  ✓ 填空题: {len(fill_questions)}")
        print(f"  ✓ 单选题: {len(single_questions)}")
        print(f"  ✓ 多选题: {len(multiple_questions)}")
        print(f"  ✓ 判断题: {len(judge_questions)}")
        
        # 统计高优先级题目比例
        high_priority_count = sum(
            1 for q in (fill_questions + single_questions + multiple_questions + judge_questions)
            if q.get('priority') == 'high'
        )
        total = len(fill_questions) + len(single_questions) + len(multiple_questions) + len(judge_questions)
        print(f"  ✓ 高优先级题目: {high_priority_count}/{total} ({high_priority_count/total*100:.1f}%)")
        
        # 生成JS文件
        js_content = f"// {theme_name}全题型模拟题(优先级感知版)\nconst quizData = [\n"
        
        js_content += f"  {{ type: 'info', info: '【填空题 共{len(fill_questions)}题，每题2分】' }},\n"
        for q in fill_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            question_escaped = q['question'].replace("'", "\\'")
            explanation_escaped = q['explanation'].replace("'", "\\'")
            js_content += f"  {{ type: 'fill', question: '{question_escaped}', answer: {answer_str}, explanation: '{explanation_escaped}' }},\n"
        
        js_content += f"  {{ type: 'info', info: '【单项选择题 共{len(single_questions)}题，每题2分】' }},\n"
        for q in single_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            options_str = json.dumps(q['options'], ensure_ascii=False)
            question_escaped = q['question'].replace("'", "\\'")
            explanation_escaped = q['explanation'].replace("'", "\\'")
            js_content += f"  {{ type: 'single', question: '{question_escaped}', options: {options_str}, answer: {answer_str}, explanation: '{explanation_escaped}' }},\n"
        
        js_content += f"  {{ type: 'info', info: '【多项选择题 共{len(multiple_questions)}题，每题3分】' }},\n"
        for q in multiple_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            options_str = json.dumps(q['options'], ensure_ascii=False)
            question_escaped = q['question'].replace("'", "\\'")
            explanation_escaped = q['explanation'].replace("'", "\\'")
            js_content += f"  {{ type: 'multiple', question: '{question_escaped}', options: {options_str}, answer: {answer_str}, explanation: '{explanation_escaped}' }},\n"
        
        js_content += f"  {{ type: 'info', info: '【判断题 共{len(judge_questions)}题，每题1分】' }},\n"
        for q in judge_questions:
            answer_str = json.dumps(q['answer'], ensure_ascii=False)
            question_escaped = q['question'].replace("'", "\\'")
            explanation_escaped = q['explanation'].replace("'", "\\'")
            js_content += f"  {{ type: 'judge', question: '{question_escaped}', answer: {answer_str}, explanation: '{explanation_escaped}' }},\n"
        
        js_content = js_content.rstrip(',\n') + "\n];\n"
        
        with open(self.quiz_dir / quiz_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        total = len(fill_questions) + len(single_questions) + len(multiple_questions) + len(judge_questions)
        print(f"  ✅ 总计: {total} 道题目")
        
        return total
    
    def _supplement_with_priority(self, concepts, sentences, fill_qs, single_qs, multiple_qs, judge_qs, target=120):
        """使用高优先级知识点补充"""
        current_total = len(fill_qs) + len(single_qs) + len(multiple_qs) + len(judge_qs)
        needed = target - current_total
        
        if needed <= 0 or not concepts:
            return
        
        concept_idx = 0
        
        # 补充填空题
        for i in range(min(needed // 4, len(concepts))):
            if concept_idx >= len(concepts):
                concept_idx = 0
            
            concept = concepts[concept_idx]
            if len(concept) >= 2:
                found = False
                for sent in sentences:
                    if concept in sent and len(sent) > len(concept) + 5:
                        question = sent.replace(concept, '____', 1)
                        fill_qs.append({
                            'type': 'fill',
                            'question': question,
                            'answer': [concept],
                            'explanation': sent,
                            'priority': 'high'
                        })
                        found = True
                        break
                
                if not found:
                    fill_qs.append({
                        'type': 'fill',
                        'question': f'材料提到的{concept}是____',
                        'answer': [concept],
                        'explanation': f'{concept}是材料中的关键概念。',
                        'priority': 'high'
                    })
            
            concept_idx += 1

def main():
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    
    generator = PriorityAwareQuizGenerator(base_path)
    
    themes = [
        ('科技.txt', 'technology_quiz_priority.js', '科技'),
        ('十五五.txt', 'wenti_quiz_priority.js', '十五五'),
        ('军事.txt', 'military_quiz_priority.js', '军事'),
        ('国际要闻.txt', 'international_quiz_priority.js', '国际要闻'),
        ('探究性专题.txt', 'inquiry_quiz_priority.js', '探究性专题'),
        ('文体.txt', 'culture_quiz_priority.js', '文体'),
        ('热点论坛.txt', 'forum_quiz_priority.js', '热点论坛'),
        ('环保.txt', 'environment_quiz_priority.js', '环保'),
    ]
    
    print("=" * 80)
    print("优先级感知的题库生成器 - 2025年及以后时政竞赛")
    print("=" * 80)
    
    total_questions = 0
    for material_file, quiz_file, theme_name in themes:
        material_path = base_path / 'materials' / material_file
        if material_path.exists():
            count = generator.generate_js_quiz(material_path, quiz_file, theme_name, target_questions=120)
            total_questions += count
        else:
            print(f"\n✗ 文件不存在: {material_file}")
    
    print("\n" + "=" * 80)
    print(f"✅ 生成完成！总计{total_questions}道题目")
    print(f"📁 优先级感知题库文件保存在: online_quiz/*_priority.js")
    print("=" * 80)

if __name__ == "__main__":
    main()
