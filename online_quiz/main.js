// 题目渲染与交互逻辑
const container = document.getElementById('quiz-container');
let current = 0;
let answered = false;
let wrongList = [];
let reviewMode = false;
let reviewIdx = 0;

function renderQuestion(idx) {
  answered = false;
  const q = reviewMode ? quizData[wrongList[idx]] : quizData[idx];
  let html = `<div class="progress">${reviewMode ? `错题第${idx+1}题 / 共${wrongList.length}题` : `第${idx+1}题 / 共${quizData.length}题`}</div>`;
  if (q.type === 'info') {
    html += `<div class="question-title" style="color:#2563eb;text-align:center;font-size:1.15em;">${q.info}</div>`;
    html += '<button id="next-btn">进入下一题</button>';
    container.innerHTML = html;
    document.getElementById('next-btn').onclick = function() {
      if (reviewMode) {
        if (reviewIdx < wrongList.length-1) {
          reviewIdx++;
          renderQuestion(reviewIdx);
        } else {
          showEnd();
        }
      } else {
        if (current < quizData.length-1) {
          current++;
          renderQuestion(current);
        } else {
          showEnd();
        }
      }
    };
    return;
  }
  if (q.type === 'fill') {
    let blanks = Array.isArray(q.answer) ? q.answer.length : 1;
    let blankIdx = 0;
    let questionHTML = q.question.replace(/_{2,}/g, function() {
      let html = '';
      if (blankIdx < blanks) {
        html = `<input type="text" name="blank${blankIdx}" placeholder="请填写第${blankIdx+1}空" style="display:inline-block;width:80px;margin:0 4px;">`;
      } else {
        html = '____';
      }
      blankIdx++;
      return html;
    });
    html += `<div class="question-title">${questionHTML}</div>`;
    html += '<form id="quiz-form">';
    html += '<button type="submit" id="submit-btn">提交</button>';
    html += '</form>';
    html += '<div id="feedback"></div>';
    container.innerHTML = html;
    document.getElementById('quiz-form').onsubmit = function(e) {
      e.preventDefault();
      if (!answered) checkAnswer(q);
    };
    return;
  }
  html += `<div class="question-title">${q.question}</div>`;
  html += '<form id="quiz-form">';
  if (q.type === 'single') {
    html += '<div class="options">';
    q.options.forEach((opt, i) => {
      html += `<label class="option-label"><input type="radio" name="opt" value="${i}"> ${opt}</label>`;
    });
    html += '</div>';
  } else if (q.type === 'multiple') {
    html += '<div class="options">';
    q.options.forEach((opt, i) => {
      html += `<label class="option-label"><input type="checkbox" name="opt" value="${i}"> ${opt}</label>`;
    });
    html += '</div>';
  } else if (q.type === 'judge') {
    html += '<div class="options">';
    html += `<label class="option-label"><input type="radio" name="opt" value="true"> 正确</label>`;
    html += `<label class="option-label"><input type="radio" name="opt" value="false"> 错误</label>`;
    html += '</div>';
  }
  html += '<button type="submit" id="submit-btn">提交</button>';
  html += '</form>';
  html += '<div id="feedback"></div>';
  container.innerHTML = html;
  document.getElementById('quiz-form').onsubmit = function(e) {
    e.preventDefault();
    if (!answered) checkAnswer(q);
  };
}

function checkAnswer(q) {
  let correct = false;
  let userAns;
  if (q.type === 'single' || q.type === 'judge') {
    const sel = document.querySelector('input[name="opt"]:checked');
    if (!sel) return alert('请选择答案');
    userAns = q.type === 'judge' ? (sel.value === 'true') : [parseInt(sel.value)];
    correct = q.type === 'judge' ? (userAns === q.answer) : (userAns[0] === q.answer[0]);
  } else if (q.type === 'multiple') {
    const checked = Array.from(document.querySelectorAll('input[name="opt"]:checked')).map(x=>parseInt(x.value));
    if (checked.length === 0) return alert('请选择答案');
    checked.sort();
    const ans = [...q.answer].sort();
    correct = checked.length === ans.length && checked.every((v,i)=>v===ans[i]);
    userAns = checked;
  } else if (q.type === 'fill') {
    const blanks = Array.isArray(q.answer) ? q.answer.length : 1;
    userAns = [];
    for (let i = 0; i < blanks; i++) {
      const val = document.querySelector(`input[name="blank${i}"]`).value.trim();
      if (!val) return alert('请填写所有空');
      userAns.push(val);
    }
    correct = userAns.every((v,i)=>v==q.answer[i]);
  }
  answered = true;
  let feedback = `<div class="answer-feedback">${correct ? '✔️ 回答正确！' : '❌ 回答错误。'}<br>正确答案：`;
  if (q.type === 'single' || q.type === 'multiple') {
    feedback += q.answer.map(i=>q.options[i]).join('，');
  } else if (q.type === 'judge') {
    feedback += q.answer ? '正确' : '错误';
  } else if (q.type === 'fill') {
    feedback += q.answer.join('，');
  }
  feedback += `<br><span style='color:#888;font-size:0.95em;'>${q.explanation||''}</span>`;
  feedback += '</div>';
  feedback += `<button id="next-btn">下一题</button>`;
  document.getElementById('feedback').innerHTML = feedback;
  document.getElementById('next-btn').onclick = function() {
    if (reviewMode) {
      if (reviewIdx < wrongList.length-1) {
        reviewIdx++;
        renderQuestion(reviewIdx);
      } else {
        showEnd();
      }
    } else {
      if (current < quizData.length-1) {
        current++;
        renderQuestion(current);
      } else {
        showEnd();
      }
    }
  };
  // 错题收集
  if (!correct && !reviewMode) {
    if (!wrongList.includes(current)) wrongList.push(current);
  }
}

function showEnd() {
  let html = `<div class="question-title">答题结束！</div><div style="margin:24px 0;">感谢您的作答，可刷新页面重新开始。</div>`;
  if (!reviewMode && wrongList.length > 0) {
    html += `<button id="review-btn" style="background:#f59e42;">错题重做（${wrongList.length}题）</button>`;
  }
  container.innerHTML = html;
  if (!reviewMode && wrongList.length > 0) {
    document.getElementById('review-btn').onclick = function() {
      reviewMode = true;
      reviewIdx = 0;
      renderQuestion(reviewIdx);
    };
  }
}

// 初始化
renderQuestion(current);
