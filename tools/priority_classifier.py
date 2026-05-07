#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识点优先级分类工具
根据时间范围(2025年及以后)将知识点分为高/低优先级
"""

import re
from pathlib import Path

class PriorityClassifier:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.knowledge_dir = self.base_path / "knowledge_points"
        self.priority_dir = self.base_path / "knowledge_points_priority"
        self.priority_dir.mkdir(exist_ok=True)
        
        # 时间范围: 2025年及以后
        self.priority_min_year = 2025
    
    def extract_year_from_text(self, text):
        """从文本中提取年份"""
        # 查找所有 YYYY年 的模式
        years = re.findall(r'(\d{4})年', text)
        return [int(y) for y in years if y.isdigit()]
    
    def is_high_priority(self, knowledge_point, section=None):
        """
        判断知识点是否为高优先级
        分类规则:
        - 日期类知识点: 2025年及以后为高优先级，2025年之前为低优先级
        - 如果知识点不包含日期(概念/组织/术语等): 直接为高优先级
        """
        is_date_section = section is not None and ('日期' in section)

        # 非日期类知识点默认高优先级
        if not is_date_section:
            return True

        # 1. 提取文本中的年份
        years = self.extract_year_from_text(knowledge_point)
        
        if not years:
            # 日期类但没有具体年份时，保守按高优先级处理
            return True
        
        # 2. 知识点包含日期，检查是否在2025年及以后
        for year in years:
            if year >= self.priority_min_year:
                return True
            # 2025年之前均为低优先级
        
        return False
    
    def classify_knowledge_points(self, theme_name):
        """分类单个主题的知识点"""
        kp_file = self.knowledge_dir / f"{theme_name}_知识点标注.md"
        priority_file = self.priority_dir / f"{theme_name}_优先级分类.md"
        
        if not kp_file.exists():
            return None
        
        high_priority = []
        low_priority = []
        
        with open(kp_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 解析知识点
        current_section = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('## '):
                current_section = line.replace('## ', '').split(' -')[0]
            elif line.startswith('- ') and not line.startswith('- **'):
                point = line.replace('- ', '').strip()
                if point and len(point) >= 2:
                    if self.is_high_priority(point, current_section):
                        high_priority.append((point, current_section))
                    else:
                        low_priority.append((point, current_section))
        
        # 生成优先级分类文件
        self._save_priority_file(theme_name, high_priority, low_priority, priority_file)
        
        return {
            'theme': theme_name,
            'high_priority': high_priority,
            'low_priority': low_priority,
            'high_count': len(high_priority),
            'low_count': len(low_priority),
            'total': len(high_priority) + len(low_priority),
            'ratio': (len(high_priority) / (len(high_priority) + len(low_priority) + 1) * 100) if (len(high_priority) + len(low_priority)) > 0 else 0
        }
    
    def _save_priority_file(self, theme_name, high_priority, low_priority, priority_file):
        """保存优先级分类文件"""
        content = f"# {theme_name} - 知识点优先级分类\n\n"
        content += f"**分类标准**: 2025年及以后（高优先级）vs 2025年之前（低优先级）\n"
        content += f"**高优先级知识点**: {len(high_priority)} 个\n"
        content += f"**低优先级知识点**: {len(low_priority)} 个\n"
        content += f"**优先级比例**: {len(high_priority)}/{len(high_priority)+len(low_priority)} = {len(high_priority)/(len(high_priority)+len(low_priority)+1)*100:.1f}%\n\n"
        
        # 高优先级知识点
        content += f"## 🔴 高优先级知识点 (进入题库)\n\n"
        content += f"共 {len(high_priority)} 个，可进入模拟题库。\n\n"
        
        if high_priority:
            content += "| 知识点 | 分类 |\n"
            content += "|--------|------|\n"
            for point, section in sorted(high_priority):
                content += f"| {point} | {section} |\n"
            content += "\n"
        else:
            content += "（无高优先级知识点）\n\n"
        
        # 低优先级知识点
        content += f"## ⚪ 低优先级知识点 (不进入题库)\n\n"
        content += f"共 {len(low_priority)} 个，不进入模拟题库。\n\n"
        
        if low_priority:
            content += "| 知识点 | 分类 |\n"
            content += "|--------|------|\n"
            for point, section in sorted(low_priority):
                content += f"| {point} | {section} |\n"
            content += "\n"
        else:
            content += "（无低优先级知识点）\n\n"
        
        # 建议
        content += "## 💡 说明\n\n"
        content += "- **高优先级**: 日期类知识点中年份>=2025，或非日期类知识点\n"
        content += "- **低优先级**: 日期类知识点中年份<2025\n"
        content += "- **使用建议**: 在生成模拟题库时，优先选择高优先级知识点\n\n"
        
        with open(priority_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def classify_all_themes(self):
        """分类所有主题的知识点"""
        themes = [
            '科技', '十五五', '军事', '国际要闻',
            '探究性专题', '文体', '热点论坛', '环保'
        ]
        
        print("=" * 80)
        print("知识点优先级分类 - 2025年及以后时政竞赛")
        print("=" * 80)
        
        results = {}
        total_high = 0
        total_low = 0
        
        for theme in themes:
            result = self.classify_knowledge_points(theme)
            if result:
                results[theme] = result
                total_high += result['high_count']
                total_low += result['low_count']
                
                print(f"\n【{theme}】")
                print(f"  高优先级: {result['high_count']:3d} 个  ({result['ratio']:.1f}%)")
                print(f"  低优先级: {result['low_count']:3d} 个")
                print(f"  总计: {result['total']:3d} 个")
        
        print("\n" + "=" * 80)
        print(f"总体统计")
        print("=" * 80)
        print(f"高优先级知识点: {total_high:3d} 个")
        print(f"低优先级知识点: {total_low:3d} 个")
        print(f"总知识点数:    {total_high + total_low:3d} 个")
        print(f"优先级比例:    {total_high}/{total_high+total_low} = {total_high/(total_high+total_low+1)*100:.1f}%")
        
        # 生成综合报告
        self._generate_summary_report(results, total_high, total_low)
        
        return results
    
    def _generate_summary_report(self, results, total_high, total_low):
        """生成综合优先级报告"""
        report_file = self.base_path / "PRIORITY_CLASSIFICATION_REPORT.md"
        
        content = "# 知识点优先级分类报告 - 2025年及以后时政竞赛\n\n"
        content += "**分类日期**: 2026年5月5日\n"
        content += "**分类标准**: \n"
        content += "- **高优先级**: 日期类知识点中年份>=2025，或非日期类知识点\n"
        content += "- **低优先级**: 日期类知识点中年份<2025\n\n"
        
        # 统计表
        content += "## 📊 主题优先级统计\n\n"
        content += "| 主题 | 高优先级 | 低优先级 | 总计 | 高优先比例 | 建议 |\n"
        content += "|------|--------|--------|------|----------|------|\n"
        
        for theme, result in sorted(results.items()):
            high = result['high_count']
            low = result['low_count']
            total = high + low
            ratio = (high / total * 100) if total > 0 else 0
            
            if ratio >= 80:
                suggest = "✅ 优秀"
            elif ratio >= 60:
                suggest = "⭐ 良好"
            elif ratio >= 40:
                suggest = "△ 一般"
            else:
                suggest = "⚠️ 低优先级较多"
            
            content += f"| {theme} | {high:3d} | {low:3d} | {total:3d} | {ratio:5.1f}% | {suggest} |\n"
        
        content += f"\n**总计** | {total_high:3d} | {total_low:3d} | {total_high+total_low:3d} | {total_high/(total_high+total_low+1)*100:.1f}% | |\n\n"
        
        # 主题详解
        content += "## 🎯 主题详细分析\n\n"
        
        for theme, result in sorted(results.items(), key=lambda x: x[1]['ratio'], reverse=True):
            high_count = result['high_count']
            low_count = result['low_count']
            ratio = result['ratio']
            
            content += f"### {theme} ({ratio:.1f}% 高优先级)\n\n"
            
            if high_count > 0:
                content += f"**高优先级示例** (前3个):\n"
                for point, section in result['high_priority'][:3]:
                    content += f"- {point}\n"
                content += f"\n"
            
            if low_count > 0:
                content += f"**低优先级示例** (前3个):\n"
                for point, section in result['low_priority'][:3]:
                    content += f"- {point}\n"
                content += f"\n"
            
            content += "\n"
        
        # 建议
        content += "## 💡 使用建议\n\n"
        content += "1. **题库生成**: 在生成模拟题库时，优先使用高优先级知识点\n"
        content += "2. **最低要求**: 高优先级知识点必须全部覆盖(100%)\n"
        content += "3. **其他知识**: 低优先级知识点作为背景或延伸阅读\n"
        content += "4. **题目数量**: 根据高优先级知识点数量调整题库规模\n\n"
        
        # 优先级排序
        content += "## 📈 主题优先级排序\n\n"
        
        sorted_by_ratio = sorted(results.items(), key=lambda x: x[1]['ratio'], reverse=True)
        for i, (theme, result) in enumerate(sorted_by_ratio, 1):
            content += f"{i}. **{theme}** - {result['high_count']}/{result['total']} ({result['ratio']:.1f}%)\n"
        
        content += "\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 优先级分类报告已保存: {report_file}")

def main():
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    
    classifier = PriorityClassifier(base_path)
    results = classifier.classify_all_themes()

if __name__ == "__main__":
    main()
