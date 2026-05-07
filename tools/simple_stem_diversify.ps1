# 简化版：仅多样化单选题问法
# 这是最直接有效的可读性改进

$WorkDir = "c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026\online_quiz"
Set-Location $WorkDir

# 单选题问法变体
$stems = @(
    '根据材料，以下哪项表述正确？',
    '对材料所述内容，以下理解正确的是？',
    '材料表明，下列哪项表述无误？',
    '根据所述内容，以下说法中正确的有？',
    '对材料关键观点的理解，最准确的是？',
    '下列对材料的解读，最恰当的是？'
)

$files = @(
    'international_quiz_data.js',
    'hotspot_quiz_data.js',
    'environment_quiz_data.js',
    'research_quiz_data.js'
)

Write-Host "开始修复单选题问法...`n"

foreach ($file in $files) {
    if (-Not (Test-Path $file)) { 
        Write-Host "⚠ 跳过: $file (文件不存在)"
        continue 
    }
    
    Write-Host "处理: $file"
    
    $content = Get-Content $file -Encoding UTF8 -Raw
    $originalSize = $content.Length
    
    # 统计原有的重复问法
    $singleChoicePattern = "{ type: 'single', question: '[^']*'"
    $matches = [regex]::Matches($content, $singleChoicePattern)
    
    $stemIndex = 0
    foreach ($match in $matches) {
        if ($stemIndex -ge $stems.Count) {
            $stemIndex = 0
        }
        
        # 提取当前问题文本
        $currentMatch = $match.Value
        $newStem = $stems[$stemIndex]
        
        # 替换问题内容
        $oldQuestionPattern = "{ type: 'single', question: '[^']*'"
        $replacement = "{ type: 'single', question: '$newStem'"
        
        if ($currentMatch -match $oldQuestionPattern) {
            $content = $content -replace [regex]::Escape($currentMatch), $replacement, 1
        }
        
        $stemIndex++
    }
    
    # 保存文件
    Set-Content $file $content -Encoding UTF8
    $newSize = $content.Length
    
    Write-Host "✓ 完成: 已修改 $($matches.Count) 个单选题"
    Write-Host ""
}

Write-Host "修复完成！"
