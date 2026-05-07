/**
 * 比赛级可读性修复工具
 * 功能：统一优化所有5个主题的题库
 * - 整合碎片化题目
 * - 改善单选题重复问题
 * - 规范化答案格式
 * - 验证答案有效性
 */

const fs = require('fs');
const path = require('path');

// 修复规则
const fixRules = {
  // 规则1：合并碎片化的填空题
  mergeFillQuestions: (questions) => {
    return questions.map(q => {
      if (q.type === 'fill' && q.question && q.question.length > 100) {
        // 检查是否为碎片化句子
        if (q.question.includes('____')) {
          // 尝试从explanation中恢复完整句子
          const fullSentence = q.explanation || '';
          // 用完整句子替换问题
          q.question = fullSentence;
        }
      }
      return q;
    });
  },

  // 规则2：多样化单选题问法
  diversifySingleChoiceStems: (questions) => {
    const stems = [
      '根据材料，以下哪项表述正确？',
      '材料中所述现象的核心原因是什么？',
      '对材料内容的理解，以下哪项最准确？',
      '根据材料判断，以下叙述中哪项无误？',
      '下列选项对材料的解读，最恰当的是？',
      '关于材料所涉及事项，以下说法正确的是？'
    ];
    
    let stemIndex = 0;
    return questions.map(q => {
      if (q.type === 'single') {
        q.question = stems[stemIndex % stems.length];
        stemIndex++;
      }
      return q;
    });
  },

  // 规则3：验证答案索引有效性
  validateAnswerIndices: (questions) => {
    return questions.map(q => {
      if (['single', 'multiple'].includes(q.type)) {
        // 检查answer是否为数组
        if (!Array.isArray(q.answer)) {
          q.answer = [q.answer];
        }
        // 检查索引是否在选项范围内
        if (q.options) {
          q.answer = q.answer.filter(idx => idx < q.options.length && idx >= 0);
        }
      }
      return q;
    });
  },

  // 规则4：规范填空题答案格式
  normalizeFillinAnswers: (questions) => {
    return questions.map(q => {
      if (q.type === 'fill') {
        // 确保answer为数组
        if (!Array.isArray(q.answer)) {
          q.answer = [q.answer];
        }
        // 去除多余空格
        q.answer = q.answer.map(a => a.trim());
      }
      return q;
    });
  },

  // 规则5：清理重复问题
  deduplicateQuestions: (questions) => {
    const seen = new Set();
    return questions.filter(q => {
      const key = `${q.type}-${q.question}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }
};

// 应用所有修复规则
function applyAllFixes(quizData) {
  let fixed = [...quizData];
  
  fixed = fixRules.mergeFillQuestions(fixed);
  fixed = fixRules.diversifySingleChoiceStems(fixed);
  fixed = fixRules.validateAnswerIndices(fixed);
  fixed = fixRules.normalizeFillinAnswers(fixed);
  
  // 保留info项目，只对题目去重
  const questions = fixed.filter(q => q.type !== 'info');
  const infoItems = fixed.filter(q => q.type === 'info');
  
  const deduped = fixRules.deduplicateQuestions(questions);
  
  return [...infoItems, ...deduped];
}

// 生成修复后的文件
function generateRefactoredFile(originalPath, outputPath) {
  try {
    // 动态导入原始数据
    const module = require(originalPath);
    const quizData = module.quizData;
    
    console.log(`\n处理文件: ${path.basename(originalPath)}`);
    console.log(`原始题目数: ${quizData.filter(q => q.type !== 'info').length}`);
    
    // 应用修复
    const fixedData = applyAllFixes(quizData);
    const fixedQuestions = fixedData.filter(q => q.type !== 'info').length;
    
    console.log(`修复后题目数: ${fixedQuestions}`);
    
    // 生成输出代码
    const output = `// ${path.basename(originalPath).replace('_quiz_data.js', '')}模拟题 - 比赛级可读性版本
const quizData = ${JSON.stringify(fixedData, null, 2)};`;
    
    // 写入文件
    fs.writeFileSync(outputPath, output, 'utf8');
    console.log(`✓ 已保存: ${path.basename(outputPath)}`);
    
  } catch (error) {
    console.error(`✗ 处理失败: ${error.message}`);
  }
}

// 主程序
const quizFiles = [
  'international_quiz_data.js',
  'research_quiz_data.js',
  'hotspot_quiz_data.js',
  'environment_quiz_data.js',
  'technology_quiz_data.js'
];

const onlineQuizDir = path.join(__dirname, '../online_quiz');
const backupDir = path.join(__dirname, '../online_quiz/backup_before_refactor');

// 创建备份目录
if (!fs.existsSync(backupDir)) {
  fs.mkdirSync(backupDir, { recursive: true });
}

console.log('========== 比赛级可读性修复开始 ==========\n');

quizFiles.forEach(file => {
  const originalPath = path.join(onlineQuizDir, file);
  const backupPath = path.join(backupDir, file);
  
  // 备份原文件
  if (fs.existsSync(originalPath)) {
    fs.copyFileSync(originalPath, backupPath);
    
    // 生成修复版本
    generateRefactoredFile(originalPath, originalPath);
  } else {
    console.log(`⚠ 未找到: ${file}`);
  }
});

console.log('\n========== 修复完成 ==========');
console.log('备份位置:', backupDir);
console.log('提示: 修复包括 - 合并碎片化题目、多样化问法、验证答案、规范格式');
