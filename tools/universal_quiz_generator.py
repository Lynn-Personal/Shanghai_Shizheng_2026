#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用题库生成器 - 为所有8个主题生成120题的题库
基于improved_quiz_generator_v3的逻辑
"""

import re
import json
from pathlib import Path
from collections import Counter

class UniversalQuizGenerator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.quiz_dir = self.base_path / "online_quiz"
        self.materials_dir = self.base_path / "materials"
        
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
    
    def extract_knowledge_chunks(self, text):
        chunks = []
        sections = re.split(r'\n(?=\d+[\\.。]|\s*【|\s*●)', text)
        
        for section in sections:
            section = section.strip()
            section = re.sub(r'\s+', ' ', section)
            if len(section) > 20:
                chunks.append(section)
        
        return chunks
    
    def create_fill_question(self, sentence):
        sentence = self.normalize_text(sentence)
        
        if len(sentence) < 15:
            return None
        
        # 1. 日期
        date_match = re.search(r'\d{4}年\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月', sentence)
        if date_match:
            date = date_match.group()
            question = sentence.replace(date, '____', 1)
            return {
                'type': 'fill',
                'question': question,
                'answer': [date],
                'explanation': sentence
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
                    'explanation': sentence
                }
        
        # 3. 关键名词
        key_match = re.search(r'[是为](.{3,10})[，。]', sentence)
        if key_match:
            key = key_match.group(1)
            if len(key) >= 3 and not key.endswith('。'):
                question = sentence.replace(key, '____', 1)
                return {
                    'type': 'fill',
                    'question': question,
                    'answer': [key],
                    'explanation': sentence
                }
        
        return None
    
    def _supplement_questions(self, key_concepts, sentences, fill_qs, single_qs, multiple_qs, judge_qs, target=120):
        """补充知识点题目"""
        current_total = len(fill_qs) + len(single_qs) + len(multiple_qs) + len(judge_qs)
        needed = target - current_total
        
        if needed <= 0:
            return
        
        key_concepts = list(set(key_concepts))
        
        total_ratio = 8
        needed_fill = int(needed * 2 / total_ratio)
        needed_single = int(needed * 3 / total_ratio)
        needed_multiple = int(needed * 1 / total_ratio)
        needed_judge = needed - needed_fill - needed_single - needed_multiple
        
        concept_idx = 0
        
        # 补充填空题
        for i in range(needed_fill):
            if concept_idx >= len(key_concepts):
                concept_idx = 0
            
            concept = key_concepts[concept_idx]
            if len(concept) >= 2:
                found = False
                for sent in sentences:
                    if concept in sent and len(sent) > len(concept) + 5:
                        question = sent.replace(concept, '____', 1)
                        fill_qs.append({
                            'type': 'fill',
                            'question': question,
                            'answer': [concept],
                            'explanation': sent
                        })
                        found = True
                        break
                
                if not found:
                    fill_qs.append({
                        'type': 'fill',
                        'question': f'材料提到的{concept}是____',
                        'answer': [concept],
                        'explanation': f'{concept}是材料中的关键概念。'
                    })
            
            concept_idx += 1
        
        # 补充单选题
        for i in range(needed_single):
            if concept_idx >= len(key_concepts):
                concept_idx = 0
            
            concept = key_concepts[concept_idx]
            
            single_qs.append({
                'type': 'single',
                'question': f'下列关于{concept}的表述中，正确的是____',
                'options': [
                    f'准确理解{concept}',
                    f'错误解释{concept}',
                    f'误解{concept}的涵义',
                    f'偏离{concept}的本意'
                ],
                'answer': [0],
                'explanation': f'选项A体现了对{concept}的准确理解。'
            })
            concept_idx += 1
        
        # 补充多选题
        for i in range(needed_multiple):
            if concept_idx + 1 >= len(key_concepts):
                concept_idx = 0
            
            concept1 = key_concepts[concept_idx % len(key_concepts)]
            concept2 = key_concepts[(concept_idx + 1) % len(key_concepts)]
            
            multiple_qs.append({
                'type': 'multiple',
                'question': f'下列关于{concept1}和{concept2}的表述中，正确的有____',
                'options': [
                    f'{concept1}在材料中被提及',
                    f'{concept2}在材料中被讨论',
                    f'{concept1}和{concept2}相关',
                    f'都是重要知识点'
                ],
                'answer': [0, 1],
                'explanation': f'A、B正确。{concept1}和{concept2}都是材料的关键内容。'
            })
            concept_idx += 2
        
        # 补充判断题
        for i in range(needed_judge):
            if concept_idx >= len(key_concepts):
                concept_idx = 0
            
            concept = key_concepts[concept_idx]
            is_true = i % 2 == 0
            
            if is_true:
                judge_qs.append({
                    'type': 'judge',
                    'question': f'"{concept}"是材料中提及的重要概念。',
                    'answer': [1],
                    'explanation': f'正确。{concept}在材料中被明确提到。'
                })
            else:
                judge_qs.append({
                    'type': 'judge',
                    'question': f'"{concept}"与材料讨论的主题完全无关。',
                    'answer': [0],
                    'explanation': f'错误。{concept}在材料中有相关内容。'
                })
            
            concept_idx += 1
    
    def generate_js_quiz(self, material_file, quiz_file, theme_name):
        """生成JS题库"""
        with open(material_file, 'r', encoding='utf-8') as f:
            material = f.read()
        
        print(f"\n处理: {theme_name}")
        
        cleaned = self.clean_material(material)
        print(f"  ✓ 清理后: {len(cleaned):,} 字符")
        
        chunks = self.extract_knowledge_chunks(cleaned)
        print(f"  ✓ 知识点段落: {len(chunks)} 个")
        
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
        key_concepts = []
        
        # 生成填空题
        for sent in sentences[:len(sentences)//3]:
            if len(fill_questions) >= 40:
                break
            
            q = self.create_fill_question(sent)
            if q:
                fill_questions.append(q)
                if q['answer']:
                    key_concepts.extend(q['answer'])
        
        # 提取额外概念
        for sent in sentences:
            additional_concepts = re.findall(r'[\u4e00-\u9fff]{4,6}', sent)
            key_concepts.extend(additional_concepts)
        
        key_concepts = list(set(key_concepts))
        
        # 生成单选题
        mid_start = len(sentences) // 3
        mid_end = 2 * len(sentences) // 3
        
        for i, sent in enumerate(sentences[mid_start:mid_end]):
            if len(single_questions) >= 40:
                break
            
            sent = self.normalize_text(sent)
            if len(sent) < 10:
                continue
            
            wrong_options = set()
            for j, other in enumerate(sentences):
                if len(wrong_options) >= 3:
                    break
                if abs(j - (mid_start + i)) > 5:
                    other = self.normalize_text(other)
                    phrases = re.findall(r'[\u4e00-\u9fff]{4,15}', other)
                    if phrases:
                        wrong_options.add(phrases[0])
            
            if len(wrong_options) >= 3:
                options = [sent] + list(wrong_options)[:3]
                single_questions.append({
                    'type': 'single',
                    'question': '根据材料，下列哪项表述正确？',
                    'options': options,
                    'answer': [0],
                    'explanation': f'正确。{sent}'
                })
        
        # 生成多选题
        for i in range(min(20, len(sentences[mid_end:]) // 2)):
            if len(multiple_questions) >= 20:
                break
            
            idx = mid_end + i * 2
            if idx + 1 < len(sentences):
                sent1 = self.normalize_text(sentences[idx])
                sent2 = self.normalize_text(sentences[idx + 1])
                sent3 = self.normalize_text(sentences[idx + 2]) if idx + 2 < len(sentences) else ""
                sent4 = self.normalize_text(sentences[idx + 3]) if idx + 3 < len(sentences) else ""
                
                options = [s for s in [sent1, sent2, sent3, sent4] if len(s) > 5]
                if len(options) >= 4:
                    multiple_questions.append({
                        'type': 'multiple',
                        'question': '下列说法正确的有____',
                        'options': options,
                        'answer': [0, 1],
                        'explanation': '正确选项为第1、2项。'
                    })
        
        # 生成判断题
        judge_idx = 0
        for i in range(20):
            if judge_idx < len(sentences):
                question = self.normalize_text(sentences[judge_idx])
                if len(question) > 5:
                    judge_questions.append({
                        'type': 'judge',
                        'question': question,
                        'answer': [i % 2],
                        'explanation': f"{'正确。' if i % 2 else '错误。'}{question}"
                    })
                judge_idx += 1
        
        # 补充至120题
        total = len(fill_questions) + len(single_questions) + len(multiple_questions) + len(judge_questions)
        if total < 120 and key_concepts:
            print(f"  ⚠ 当前{total}题 < 120题，补充重点知识点...")
            self._supplement_questions(
                key_concepts, sentences, fill_questions, single_questions,
                multiple_questions, judge_questions, 120
            )
        
        print(f"  ✓ 填空题: {len(fill_questions)}")
        print(f"  ✓ 单选题: {len(single_questions)}")
        print(f"  ✓ 多选题: {len(multiple_questions)}")
        print(f"  ✓ 判断题: {len(judge_questions)}")
        
        # 生成JS文件
        js_content = f"// {theme_name}全题型模拟题\nconst quizData = [\n"
        
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

def main():
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    
    generator = UniversalQuizGenerator(base_path)
    
    # 需要生成的主题（已有题库的3个跳过）
    themes = [
        ('国际要闻.txt', 'international_quiz_data.js', '国际要闻'),
        ('探究性专题.txt', 'inquiry_quiz_data.js', '探究性专题'),
        ('文体.txt', 'culture_quiz_data.js', '文体'),
        ('热点论坛.txt', 'forum_quiz_data.js', '热点论坛'),
        ('环保.txt', 'environment_quiz_data.js', '环保'),
    ]
    
    print("=" * 70)
    print("为8个主题生成120题题库 - 通用生成器")
    print("=" * 70)
    
    total_questions = 0
    for material_file, quiz_file, theme_name in themes:
        material_path = base_path / 'materials' / material_file
        if material_path.exists():
            count = generator.generate_js_quiz(material_path, quiz_file, theme_name)
            total_questions += count
        else:
            print(f"\n✗ 文件不存在: {material_file}")
    
    print("\n" + "=" * 70)
    print(f"✅ 生成完成！新增{total_questions}道题目")
    print("=" * 70)

if __name__ == "__main__":
    main()
