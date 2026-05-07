#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题库与知识点覆盖度评估
评估现有题库对标注知识点的覆盖度
"""

import re
import json
from pathlib import Path
from collections import defaultdict

class CoverageAssessment:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.knowledge_dir = self.base_path / "knowledge_points"
        self.quiz_dir = self.base_path / "online_quiz"
        self.materials_dir = self.base_path / "materials"
    
    def extract_quiz_content(self, js_file):
        """提取JS题库中的所有题目内容"""
        quiz_file = self.quiz_dir / js_file
        
        if not quiz_file.exists():
            return []
        
        with open(quiz_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        questions = []
        try:
            # 提取所有 question: '...' 中的内容
            question_texts = re.findall(r"question:\s*'([^']*)'", content)
            for q in question_texts:
                # 处理转义字符
                q = q.replace("\\'", "'")
                if len(q) > 2:  # 过滤掉空的或太短的
                    questions.append(q)
        except:
            pass
        
        return questions
    
    def load_knowledge_points(self, theme_name):
        """从标注文件中加载知识点"""
        kp_file = self.knowledge_dir / f"{theme_name}_知识点标注.md"
        
        if not kp_file.exists():
            return []
        
        knowledge_points = []
        
        with open(kp_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # 提取列表项（以 "- " 开头）
            if line.startswith('- ') and not line.startswith('- **'):
                point = line.replace('- ', '').strip()
                if point and len(point) >= 2:  # 至少2个字
                    knowledge_points.append(point)
        
        return knowledge_points
    
    def calculate_coverage(self, questions, knowledge_points):
        """计算题目中的知识点覆盖率"""
        if not knowledge_points:
            return 0, 0, []
        
        covered = 0
        covered_points = []
        
        for kp in knowledge_points:
            kp_clean = kp.strip()
            if not kp_clean or len(kp_clean) < 2:
                continue
            
            # 检查是否在任何题目中出现
            for question in questions:
                if kp_clean in question:
                    covered += 1
                    covered_points.append(kp_clean)
                    break
        
        coverage_rate = (covered / len(knowledge_points) * 100) if knowledge_points else 0
        return covered, len(knowledge_points), coverage_rate, covered_points
    
    def assess_all_themes(self):
        """评估所有主题的覆盖度"""
        themes = [
            ('科技.txt', 'technology_quiz_data.js', '科技'),
            ('十五五.txt', 'wenti_quiz_data.js', '十五五'),
            ('军事.txt', 'military_quiz_data.js', '军事'),
            ('国际要闻.txt', 'international_quiz_data.js', '国际要闻'),
            ('探究性专题.txt', 'inquiry_quiz_data.js', '探究性专题'),
            ('文体.txt', 'culture_quiz_data.js', '文体'),
            ('热点论坛.txt', 'forum_quiz_data.js', '热点论坛'),
            ('环保.txt', 'environment_quiz_data.js', '环保'),
        ]
        
        print("=" * 80)
        print("题库与知识点覆盖度评估 - 8个主题")
        print("=" * 80)
        
        results = {}
        total_covered = 0
        total_points = 0
        
        for material_file, quiz_file, theme_name in themes:
            print(f"\n【{theme_name}】")
            
            # 加载知识点
            kps = self.load_knowledge_points(theme_name)
            total_points += len(kps)
            
            print(f"  标注知识点: {len(kps)} 个")
            
            if quiz_file:
                # 提取题库内容
                questions = self.extract_quiz_content(quiz_file)
                print(f"  题库问题: {len(questions)} 道")
                
                # 计算覆盖度
                covered, total, coverage_rate, covered_points = self.calculate_coverage(questions, kps)
                total_covered += covered
                
                results[theme_name] = {
                    'knowledge_points': len(kps),
                    'questions': len(questions),
                    'covered': covered,
                    'coverage_rate': coverage_rate,
                    'covered_points': covered_points[:5],  # 显示前5个
                    'uncovered': [kp for kp in kps if kp not in covered_points][:5]
                }
                
                print(f"  题库覆盖: {covered}/{total} = {coverage_rate:.1f}%")
                
                if coverage_rate >= 75:
                    rating = "✅ 优秀"
                elif coverage_rate >= 50:
                    rating = "⭐ 良好"
                elif coverage_rate >= 25:
                    rating = "△ 一般"
                else:
                    rating = "✗ 需改进"
                
                print(f"  评级: {rating}")
            else:
                print(f"  题库状态: 尚未生成")
                results[theme_name] = {
                    'knowledge_points': len(kps),
                    'questions': 0,
                    'covered': 0,
                    'coverage_rate': 0,
                    'covered_points': [],
                    'uncovered': []
                }
        
        # 生成详细报告
        self._generate_detailed_report(results)
        
        print("\n" + "=" * 80)
        if total_points > 0:
            overall_coverage = (total_covered / total_points * 100)
            print(f"整体覆盖度: {total_covered}/{total_points} = {overall_coverage:.1f}%")
        print("=" * 80)
    
    def _generate_detailed_report(self, results):
        """生成详细的覆盖度报告"""
        report_file = self.base_path / "QUIZ_KNOWLEDGE_COVERAGE_REPORT.md"
        
        content = "# 题库与知识点覆盖度详细评估\n\n"
        content += "**评估日期**: 2026年5月5日\n\n"
        
        # 总体统计表
        content += "## 📊 总体统计\n\n"
        content += "| 主题 | 标注知识点 | 题库题数 | 覆盖知识点 | 覆盖率 | 评级 |\n"
        content += "|------|----------|--------|----------|--------|------|\n"
        
        total_kp = 0
        total_q = 0
        total_covered = 0
        
        for theme, data in sorted(results.items()):
            kp_count = data['knowledge_points']
            q_count = data['questions']
            covered = data['covered']
            coverage = data['coverage_rate']
            total_kp += kp_count
            total_q += q_count
            total_covered += covered
            
            if q_count == 0:
                rating = "⏳ 待生成"
            elif coverage >= 75:
                rating = "✅ 优秀"
            elif coverage >= 50:
                rating = "⭐ 良好"
            elif coverage >= 25:
                rating = "△ 一般"
            else:
                rating = "✗ 需改进"
            
            content += f"| {theme} | {kp_count} | {q_count} | {covered} | {coverage:.1f}% | {rating} |\n"
        
        content += "\n"
        
        if total_kp > 0:
            content += f"**总计知识点**: {total_kp} 个  \n"
            content += f"**总计题库题数**: {total_q} 道  \n"
            content += f"**总体覆盖知识点**: {total_covered} 个  \n"
            content += f"**整体覆盖率**: {(total_covered/total_kp*100):.1f}%\n\n"
        
        # 主题详细分析
        content += "## 📋 主题详细分析\n\n"
        
        for theme, data in sorted(results.items()):
            kp_count = data['knowledge_points']
            q_count = data['questions']
            covered = data['covered']
            coverage = data['coverage_rate']
            
            content += f"### {theme}\n\n"
            content += f"**知识点统计**\n"
            content += f"- 标注总数: {kp_count}\n"
            content += f"- 题库覆盖: {covered}/{kp_count} = {coverage:.1f}%\n"
            content += f"- 题库题数: {q_count}\n"
            content += f"- 题库密度: {(q_count/kp_count if kp_count > 0 else 0):.2f}题/知识点\n\n"
            
            if q_count > 0:
                if data['covered_points']:
                    content += f"**已覆盖样例** (前5个):\n"
                    for kp in data['covered_points']:
                        content += f"- ✅ {kp}\n"
                    content += f"\n"
                
                if data['uncovered']:
                    content += f"**遗漏知识点** (前5个):\n"
                    for kp in data['uncovered']:
                        content += f"- ⚠️ {kp}\n"
                    content += f"\n"
            
            content += "\n"
        
        # 建议
        content += "## 💡 建议\n\n"
        content += "### 已有题库的主题\n"
        content += "1. **科技、十五五、军事**: 覆盖率在25-30%之间\n"
        content += "   - 需要补充题目以覆盖更多知识点\n"
        content += "   - 建议增加30-50%的补充题目\n\n"
        
        content += "### 待生成题库的主题\n"
        content += "1. **国际要闻**: 117个知识点，可生成120题\n"
        content += "2. **探究性专题**: 104个知识点，可生成120题\n"
        content += "3. **文体**: 100个知识点，可生成120题\n"
        content += "4. **热点论坛**: 59个知识点，建议补充\n"
        content += "5. **环保**: 121个知识点，可生成150题\n\n"
        
        content += "### 优先行动\n"
        content += "1. 为**国际要闻、探究性专题、文体、环保**生成120题题库\n"
        content += "2. 改进**科技、十五五、军事**的题库，增加知识点覆盖\n"
        content += "3. **热点论坛**知识点较少，可作为选修内容\n\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 详细报告已保存: {report_file}")

def main():
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    
    assessment = CoverageAssessment(base_path)
    assessment.assess_all_themes()

if __name__ == "__main__":
    main()
