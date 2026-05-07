#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
材料清理工具
直接从txt材料文件中移除非知识点内容（水印、元数据等）
可作为题库生成的第一步
"""

import os
import re
from pathlib import Path

class MaterialCleaner:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.materials_dir = self.base_path / "materials"
        
        # 需要过滤的关键词/模式（与improved_quiz_generator_v3.py一致）
        self.filter_patterns = [
            r'^[第\d]+页.*',
            r'^新闻现场\s*$',
            r'^背景资料.*',
            r'^责任编辑.*',
            r'^邮箱.*',
            r'^美术编辑.*',
        ]
        
        self.explanation_keywords = [
            '一键复制', '导出为PDF', '导出为', 'Word', 'Typora', 'Markdown',
            'PDF文件', '内容整理', '所有内容', '电子版', 'Markdown编辑器',
            '我已完整', '当前对话', '网页搜索', '无法直接', '可下载',
            '图片附', '临时禁用', '我无法', '但我已'
        ]
    
    def should_filter(self, text):
        """检查是否应该过滤这一行"""
        text = text.strip()
        
        # 过短的行（通常是标题或标记）
        if len(text) < 5:
            return True
        
        # 匹配过滤模式
        for pattern in self.filter_patterns:
            if re.match(pattern, text):
                return True
        
        # 过滤纯页码、连接符
        if re.match(r'^[-—_•·]+$', text):
            return True
        
        # 过滤纯数字
        if re.match(r'^[\d\s]+$', text):
            return True
        
        # 过滤包含说明性内容的行
        for keyword in self.explanation_keywords:
            if keyword in text:
                return True
        
        return False
    
    def clean_material(self, input_file, output_file=None):
        """清理材料文件"""
        if output_file is None:
            # 如果没有指定输出文件，覆盖原文件
            output_file = input_file
        
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 过滤行
        cleaned_lines = []
        for line in lines:
            if not self.should_filter(line):
                cleaned_lines.append(line)
        
        # 移除多个连续的空行
        final_lines = []
        prev_empty = False
        for line in cleaned_lines:
            if line.strip() == '':
                if not prev_empty:
                    final_lines.append(line)
                prev_empty = True
            else:
                final_lines.append(line)
                prev_empty = False
        
        # 保存清理后的文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)
        
        original_size = os.path.getsize(input_file)
        cleaned_size = os.path.getsize(output_file)
        reduction_ratio = (1 - cleaned_size / original_size) * 100
        
        print(f"✓ {output_file.name}")
        print(f"  原始: {original_size:6} 字节 → 清理后: {cleaned_size:6} 字节")
        print(f"  削减: {reduction_ratio:.1f}%\n")
        
        return cleaned_size - original_size

def main():
    base_path = Path(r"c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026")
    
    cleaner = MaterialCleaner(base_path)
    
    materials = [
        'materials/科技.txt',
        'materials/十五五.txt',
        'materials/军事.txt',
    ]
    
    print("="*60)
    print("材料清理工具 - 移除非知识点内容")
    print("="*60 + "\n")
    
    total_reduction = 0
    for material in materials:
        material_path = base_path / material
        if material_path.exists():
            reduction = cleaner.clean_material(material_path)
            total_reduction += reduction
        else:
            print(f"✗ 文件不存在: {material}\n")
    
    print("="*60)
    print(f"✅ 清理完成！总削减: {abs(total_reduction)} 字节")
    print("="*60)

if __name__ == '__main__':
    main()
