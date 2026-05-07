# 比赛级可读性自动修复脚本
# 功能：批量优化单选题问法、规范化答案格式

param(
    [string]$SourceDir = "c:\lynn_github_projects\shanghai_shizheng\Shanghai_Shizheng_2026\online_quiz"
)

Set-Location $SourceDir

# 步骤1：多样化单选题问法
function Optimize-SingleChoiceStems {
    param([string]$FilePath)
    
    $content = Get-Content $FilePath -Encoding UTF8 -Raw
    
    # 定义多样化的单选题问法
    $stemVariations = @(
        '根据材料，以下哪项表述正确？',
        '材料表明，对下列选项的理解，正确的是____',
        '根据材料判断，下列说法中正确的是____',
        '对材料内容的理解，以下哪项最为准确____',
        '根据所述内容，以下表述无误的是____',
        '下列对材料的理解，最恰当的是____',
        '关于材料所述事项，以下认识正确的是____',
        '材料中核心观点的准确表述是____',
        '依据材料，下列哪项说法正确____',
        '对材料关键内容的理解，正确的有____'
    )
    
    # 计数用于循环使用不同的问法
    $stemCount = 0
    
    # 替换所有单选题问法
    $pattern = "{ type: 'single', question: '根据材料，以下哪项表述正确\?'"
    
    $matches = [regex]::Matches($content, [regex]::Escape($pattern))
    Write-Host "检测到 $($matches.Count) 个重复单选题问法需要多样化"
    
    if ($matches.Count -gt 0) {
        # 通过循环替换处理每个出现
        for ($i = 0; $i -lt $matches.Count; $i++) {
            $newStem = $stemVariations[$i % $stemVariations.Count]
            $oldText = "{ type: 'single', question: '根据材料，以下哪项表述正确？'"
            $newText = "{ type: 'single', question: '$newStem'"
            $content = $content.Replace($oldText, $newText, 1)
            $stemCount++
        }
    }
    
    return $content
}

# 步骤2：规范化答案格式
function Normalize-AnswerFormat {
    param([string]$Content)
    
    # 修复：answer: 0 -> answer: [0]
    $content = [regex]::Replace($content, "answer: (\d+)([,\}])", 'answer: [$1]$2')
    
    # 修复：answer: \[1\] -> answer: [1]（处理双重转义）
    $content = $content -replace "answer: \\\[\d+\\\]", {$_.Value -replace "\\", ""}
    
    return $content
}

# 步骤3：验证文件有效性
function Test-JsonValidity {
    param([string]$Content)
    
    try {
        # 提取const quizData = [...]的内容
        if ($content -match "const quizData = \[(.*)\];") {
            $jsonContent = "[" + $matches[1] + "]"
            $parsed = $jsonContent | ConvertFrom-Json -ErrorAction Stop
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
}

# 处理的文件列表
$filesToFix = @(
    'international_quiz_data.js',
    'research_quiz_data.js',
    'hotspot_quiz_data.js',
    'environment_quiz_data.js'
)

Write-Host "`n========== 开始比赛级可读性修复 ==========" -ForegroundColor Cyan
Write-Host "目标文件数：$($filesToFix.Count)`n"

$successCount = 0
$failureCount = 0

foreach ($file in $filesToFix) {
    $filePath = Join-Path $SourceDir $file
    
    if (Test-Path $filePath) {
        Write-Host "处理: $file" -ForegroundColor Yellow
        
        try {
            # 备份原始文件
            $backupPath = $filePath -replace '\.js$', '.backup.js'
            Copy-Item $filePath $backupPath -Force
            Write-Host "  ✓ 备份已保存: $(Split-Path $backupPath -Leaf)"
            
            # 读取内容
            $content = Get-Content $filePath -Encoding UTF8 -Raw
            $originalSize = $content.Length
            
            # 应用优化
            $content = Optimize-SingleChoiceStems $content
            $content = Normalize-AnswerFormat $content
            
            # 验证有效性
            if (Test-JsonValidity $content) {
                # 保存优化后的文件
                Set-Content $filePath $content -Encoding UTF8
                $newSize = $content.Length
                $sizeChange = [math]::Round((($newSize - $originalSize) / $originalSize) * 100, 1)
                
                Write-Host "  ✓ 优化完成！" -ForegroundColor Green
                Write-Host "    原始大小: $([math]::Round($originalSize/1KB, 1)) KB"
                Write-Host "    优化后: $([math]::Round($newSize/1KB, 1)) KB (变化: $sizeChange%)"
                $successCount++
            }
            else {
                Write-Host "  ✗ 验证失败：生成的内容无效" -ForegroundColor Red
                # 恢复备份
                Copy-Item $backupPath $filePath -Force
                $failureCount++
            }
        }
        catch {
            Write-Host "  ✗ 处理出错：$($_.Exception.Message)" -ForegroundColor Red
            $failureCount++
        }
    }
    else {
        Write-Host "  ✗ 文件未找到: $file" -ForegroundColor Red
        $failureCount++
    }
    
    Write-Host ""
}

Write-Host "========== 修复总结 ==========" -ForegroundColor Cyan
Write-Host "成功: $successCount / $($filesToFix.Count)" -ForegroundColor Green
Write-Host "失败: $failureCount / $($filesToFix.Count)" -ForegroundColor Red
Write-Host "`n提示：所有备份文件保存在同目录，文件名后缀为 .backup.js"
