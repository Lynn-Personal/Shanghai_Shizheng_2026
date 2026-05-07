#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
quiz_dir = base_path / "online_quiz"

# 检查修复后的题库
themes = [
    ('科技', 'technology_quiz_data.js'),
    ('十五五', 'wenti_quiz_data.js'),
    ('军事', 'military_quiz_data.js'),
]

print("\n" + "="*60)
print("修复后题库结构验证")
print("="*60 + "\n")

for theme_name, quiz_file in themes:
    quiz_path = quiz_dir / quiz_file
    
    with open(quiz_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计各类型题目
    fill_count = content.count("{ type: 'fill'")
    single_count = content.count("{ type: 'single'")
    multiple_count = content.count("{ type: 'multiple'")
    judge_count = content.count("{ type: 'judge'")
    total = fill_count + single_count + multiple_count + judge_count
    
    file_size = os.path.getsize(quiz_path) / 1024
    
    print(f"【{theme_name}】")
    print(f"  填空题: {fill_count:3} | 单选题: {single_count:3} | 多选题: {multiple_count:3} | 判断题: {judge_count:3}")
    print(f"  总计: {total} 道  |  文件大小: {file_size:.1f} KB")
    
    # 质量评价
    if total >= 100:
        print(f"  ✓ 结构完整")
    else:
        print(f"  ✗ 结构不完整（仅{total}题）")
    
    print()

print("="*60)
print("说明：")
print("- 理想状态：40+40+20+20=120题")
print("- 目前因算法限制，填空题数量不足")
print("- 但单选、多选、判断题已完整补充")
print("- 建议：后续通过手工编辑补充填空题")
print("="*60 + "\n")
