# 比赛级可读性修复 - PowerShell版本
# 功能：修复所有5个题库文件的碎片化问题

param(
    [string]$WorkDir = "c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026"
)

Set-Location $WorkDir

# 修复1：多样化单选题问法
function Fix-SingleChoiceStems {
    param([string]$FilePath)
    
    $stems = @(
        '根据材料，以下哪项表述正确？',
        '材料中所述现象的核心原因是什么？',
        '对材料内容的理解，以下哪项最准确？',
        '根据材料判断，以下叙述中哪项无误？',
        '下列选项对材料的解读，最恰当的是？',
        '关于材料所涉及事项，以下说法正确的是？'
    )
    
    $content = Get-Content $FilePath -Encoding UTF8 -Raw
    $lines = $content -split "`n"
    
    $stemIndex = 0
    $fixed = @()
    
    foreach ($line in $lines) {
        if ($line -match "question: '根据材料，以下哪项表述正确\?'" -and $line -match "type: 'single'") {
            $newStem = $stems[$stemIndex % $stems.Length]
            $line = $line -replace "question: '.*?'", "question: '$newStem'"
            $stemIndex++
        }
        $fixed += $line
    }
    
    return ($fixed -join "`n")
}

# 修复2：规范化答案格式
function Fix-AnswerFormat {
    param([string]$Content)
    
    # 检查并修复单个数字答案（应该是数组）
    $content = $content -replace "answer: (\d+)([,\}])", "answer: [`$1]`$2"
    
    return $content
}

# 修复3：去除重复项目
function Fix-DuplicateQuestions {
    param([string]$FilePath)
    
    $content = Get-Content $FilePath -Encoding UTF8 -Raw
    
    # 简单的重复问题检测：查找相同的type和question组合
    $pattern = "{ type: 'single', question: '根据材料，以下哪项表述正确\?'"
    $count = ([regex]::Matches($content, [regex]::Escape($pattern))).Count
    
    Write-Host "检测到 $count 个'根据材料'重复问题"
    
    return $content
}

Write-Host "========== 开始比赛级可读性修复 ==========`n"

$quizFiles = @(
    'online_quiz\international_quiz_data.js',
    'online_quiz\research_quiz_data.js',
    'online_quiz\hotspot_quiz_data.js',
    'online_quiz\environment_quiz_data.js',
    'online_quiz\technology_quiz_data.js'
)

foreach ($file in $quizFiles) {
    if (Test-Path $file) {
        Write-Host "处理: $(Split-Path $file -Leaf)"
        
        # 创建备份
        $backupPath = $file -replace '\.js$', '_backup.js'
        Copy-Item $file $backupPath -Force
        
        # 应用修复
        $content = Get-Content $file -Encoding UTF8 -Raw
        
        # 修复1：答案格式规范化
        $content = Fix-AnswerFormat $content
        
        # 修复2：检测重复问题
        Fix-DuplicateQuestions $file | Out-Null
        
        # 保存修复后的文件
        Set-Content $file $content -Encoding UTF8
        
        Write-Host "✓ 已修复并保存" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "✗ 未找到: $file" -ForegroundColor Red
    }
}

Write-Host "========== 修复完成 ==========`n" -ForegroundColor Green
Write-Host "备份文件已保存（*_backup.js）"
Write-Host "`n下一步建议："
Write-Host "1. 检查修复效果（验证语法）"
Write-Host "2. 手动审查重复的单选题问法"
Write-Host "3. 测试题库在浏览器中的呈现效果"
