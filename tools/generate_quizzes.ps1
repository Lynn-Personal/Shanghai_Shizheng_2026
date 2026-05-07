$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$themes = @(
  @{ cn='国际要闻'; txt='materials/国际要闻.txt'; js='international_quiz_data.js'; html='国际要闻模拟.html' },
  @{ cn='探究性专题'; txt='materials/探究性专题.txt'; js='research_quiz_data.js'; html='探究性专题模拟.html' },
  @{ cn='热点论坛'; txt='materials/热点论坛.txt'; js='hotspot_quiz_data.js'; html='热点论坛模拟.html' },
  @{ cn='环保'; txt='materials/环保.txt'; js='environment_quiz_data.js'; html='环保模拟.html' },
  @{ cn='科技'; txt='materials/科技.txt'; js='technology_quiz_data.js'; html='科技模拟.html' }
)

function Escape-JS([string]$s){
  return ($s -replace '\\','\\\\' -replace "'","\\'")
}

function Normalize-Lines([string[]]$lines){
  $result = New-Object System.Collections.Generic.List[string]
  foreach($line in $lines){
    $t = $line.Trim()
    if([string]::IsNullOrWhiteSpace($t)){ continue }
    if($t -match '^第\d+页'){ continue }
    if($t -match '^(新闻现场|相关链接|背景资料)$'){ continue }
    $t = $t -replace '^[•◦·\-]+\s*',''
    $t = $t -replace '^\d+\.\s*',''
    $t = $t -replace '\s+',' '
    if($t.Length -lt 8){ continue }
    $result.Add($t)
  }
  return $result
}

function Pick-AnswerToken([string]$fact){
  $matches = [regex]::Matches($fact, '[\u4e00-\u9fffA-Za-z0-9]{2,12}')
  if($matches.Count -eq 0){ return '相关表述' }
  $cand = $matches | ForEach-Object { $_.Value } | Where-Object { $_.Length -ge 2 }
  if($cand.Count -eq 0){ return $matches[0].Value }
  return ($cand | Sort-Object Length -Descending | Select-Object -First 1)
}

foreach($theme in $themes){
  $raw = Get-Content $theme.txt -Encoding UTF8
  $facts = Normalize-Lines $raw
  if($facts.Count -lt 20){ throw "素材有效行过少: $($theme.cn)" }

  $sb = New-Object System.Text.StringBuilder
  [void]$sb.AppendLine("// $($theme.cn)专题全题型模拟题")
  [void]$sb.AppendLine('const quizData = [')

  [void]$sb.AppendLine("  { type: 'info', info: '【填空题 共40题，每题2分】' },")
  for($i=0; $i -lt 40; $i++){
    $fact = $facts[$i % $facts.Count]
    $ans = Pick-AnswerToken $fact
    $q = $fact
    if($q.Contains($ans)){
      $q = $q.Replace($ans, '____')
    } else {
      $q = "根据材料填写：____（$q）"
    }
    $qEsc = Escape-JS $q
    $ansEsc = Escape-JS $ans
    $expEsc = Escape-JS $fact
    [void]$sb.AppendLine("  { type: 'fill', question: '$qEsc', answer: ['$ansEsc'], explanation: '$expEsc' },")
  }

  [void]$sb.AppendLine("  { type: 'info', info: '【单项选择题 共40题，每题2分】' },")
  for($i=0; $i -lt 40; $i++){
    $base = ($i*4) % $facts.Count
    $opts = @(
      $facts[$base % $facts.Count],
      $facts[($base+1) % $facts.Count],
      $facts[($base+2) % $facts.Count],
      $facts[($base+3) % $facts.Count]
    )
    $qEsc = Escape-JS '根据材料，以下哪项表述正确？'
    $o0 = Escape-JS $opts[0]; $o1 = Escape-JS $opts[1]; $o2 = Escape-JS $opts[2]; $o3 = Escape-JS $opts[3]
    $expEsc = Escape-JS $opts[0]
    [void]$sb.AppendLine("  { type: 'single', question: '$qEsc', options: ['$o0', '$o1', '$o2', '$o3'], answer: [0], explanation: '正确项：$expEsc' },")
  }

  [void]$sb.AppendLine("  { type: 'info', info: '【多项选择题 共20题，每题3分】' },")
  for($i=0; $i -lt 20; $i++){
    $base = ($i*5) % $facts.Count
    $opts = @(
      $facts[$base % $facts.Count],
      $facts[($base+1) % $facts.Count],
      $facts[($base+2) % $facts.Count],
      $facts[($base+3) % $facts.Count]
    )
    $qEsc = Escape-JS '根据材料，以下哪些表述正确？'
    $o0 = Escape-JS $opts[0]; $o1 = Escape-JS $opts[1]; $o2 = Escape-JS $opts[2]; $o3 = Escape-JS $opts[3]
    $expEsc = Escape-JS ($opts[0] + '；' + $opts[1])
    [void]$sb.AppendLine("  { type: 'multiple', question: '$qEsc', options: ['$o0', '$o1', '$o2', '$o3'], answer: [0,1], explanation: '正确项：$expEsc' },")
  }

  [void]$sb.AppendLine("  { type: 'info', info: '【判断题 共20题，每题1分】' },")
  for($i=0; $i -lt 20; $i++){
    $fact = $facts[$i % $facts.Count]
    if($i % 2 -eq 0){
      $stmt = "下列说法与材料一致：$fact"
      $ans = 'true'
      $exp = '判断为正确。'
    } else {
      $stmt = "下列说法与材料一致：材料明确否定“" + $fact + "”这一内容。"
      $ans = 'false'
      $exp = '判断为错误，原材料并未作该否定性表述。'
    }
    $sEsc = Escape-JS $stmt
    $eEsc = Escape-JS $exp
    [void]$sb.AppendLine("  { type: 'judge', question: '$sEsc', answer: $ans, explanation: '$eEsc' },")
  }

  $text = $sb.ToString().TrimEnd()
  $text = [regex]::Replace($text, ',\s*$', '')
  $text += "`r`n];`r`n"
  Set-Content -Path (Join-Path 'online_quiz' $theme.js) -Value $text -Encoding UTF8

  $html = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$($theme.cn)模拟题在线答题</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="quiz-container">
    <!-- 题目内容将由JS动态渲染 -->
  </div>
  <script src="$($theme.js)"></script>
  <script src="main.js"></script>
</body>
</html>
"@
  Set-Content -Path (Join-Path 'online_quiz' $theme.html) -Value $html -Encoding UTF8
}

Write-Output 'Generated successfully for 5 themes.'
