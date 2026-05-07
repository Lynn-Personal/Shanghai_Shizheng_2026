// 题目渲染与交互逻辑
const container = document.getElementById('quiz-container');
let current = 0;
let answered = false;
let wrongList = [];
let reviewMode = false;
let reviewIdx = 0;
let reviewWrongList = []; // indices into wrongList that were wrong again during review

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
    html += '<button type="button" id="skip-btn" style="margin-left:10px;background:#9ca3af;">跳过（记为错误）</button>';
    html += '</form>';
    html += '<div id="feedback"></div>';
    container.innerHTML = html;
    document.getElementById('quiz-form').onsubmit = function(e) {
      e.preventDefault();
      if (!answered) checkAnswer(q);
    };
    document.getElementById('skip-btn').onclick = function() {
      if (!answered) checkAnswerEmpty(q);
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
  html += '<button type="button" id="skip-btn" style="margin-left:10px;background:#9ca3af;">跳过（记为错误）</button>';
  html += '</form>';
  html += '<div id="feedback"></div>';
  container.innerHTML = html;
  document.getElementById('quiz-form').onsubmit = function(e) {
    e.preventDefault();
    if (!answered) checkAnswer(q);
  };
  document.getElementById('skip-btn').onclick = function() {
    if (!answered) checkAnswerEmpty(q);
  };
}

function advanceQuestion() {
  if (reviewMode) {
    if (reviewIdx < wrongList.length - 1) { reviewIdx++; renderQuestion(reviewIdx); }
    else showEnd();
  } else {
    if (current < quizData.length - 1) { current++; renderQuestion(current); }
    else showEnd();
  }
}

function recordWrong() {
  if (!reviewMode) {
    if (!wrongList.includes(current)) wrongList.push(current);
  } else {
    if (!reviewWrongList.includes(reviewIdx)) reviewWrongList.push(reviewIdx);
  }
}

function showFeedbackAndNext(correct, correctLabel, explanation) {
  const feedbackEl = document.getElementById('feedback');
  if (!feedbackEl) return;
  let fb = `<div class="answer-feedback">${correct ? '✔️ 回答正确！' : '❌ 回答错误。'}`;
  fb += `<br>正确答案：${correctLabel}`;
  if (explanation) fb += `<br><span style='color:#888;font-size:0.95em;'>${explanation}</span>`;
  fb += '</div>';
  fb += `<button id="next-btn">下一题</button>`;
  const submitBtn = document.getElementById('submit-btn');
  const skipBtn = document.getElementById('skip-btn');
  if (submitBtn) submitBtn.style.display = 'none';
  if (skipBtn) skipBtn.style.display = 'none';
  feedbackEl.innerHTML = fb;
  document.getElementById('next-btn').onclick = advanceQuestion;
}

function checkAnswerEmpty(q) {
  answered = true;
  recordWrong();
  let correctLabel = '';
  if (q.type === 'single' || q.type === 'multiple') correctLabel = q.answer.map(i => q.options[i]).join('，');
  else if (q.type === 'judge') correctLabel = q.answer ? '正确' : '错误';
  else if (q.type === 'fill') correctLabel = q.answer.join('，');
  showFeedbackAndNext(false, correctLabel, q.explanation || '');
}

function checkAnswer(q) {
  let correct = false;
  let userAns;
  if (q.type === 'single' || q.type === 'judge') {
    const sel = document.querySelector('input[name="opt"]:checked');
    if (!sel) { checkAnswerEmpty(q); return; }
    userAns = q.type === 'judge' ? (sel.value === 'true') : [parseInt(sel.value)];
    correct = q.type === 'judge' ? (userAns === q.answer) : (userAns[0] === q.answer[0]);
  } else if (q.type === 'multiple') {
    const checked = Array.from(document.querySelectorAll('input[name="opt"]:checked')).map(x=>parseInt(x.value));
    if (checked.length === 0) { checkAnswerEmpty(q); return; }
    checked.sort();
    const ans = [...q.answer].sort();
    correct = checked.length === ans.length && checked.every((v,i)=>v===ans[i]);
    userAns = checked;
  } else if (q.type === 'fill') {
    const blanks = Array.isArray(q.answer) ? q.answer.length : 1;
    userAns = [];
    let anyEmpty = false;
    for (let i = 0; i < blanks; i++) {
      const val = document.querySelector(`input[name="blank${i}"]`).value.trim();
      if (!val) anyEmpty = true;
      userAns.push(val);
    }
    if (anyEmpty) { checkAnswerEmpty(q); return; }
    correct = userAns.every((v,i)=>v==q.answer[i]);
  }
  answered = true;
  if (!correct) recordWrong();
  let correctLabel = '';
  if (q.type === 'single' || q.type === 'multiple') correctLabel = q.answer.map(i=>q.options[i]).join('，');
  else if (q.type === 'judge') correctLabel = q.answer ? '正确' : '错误';
  else if (q.type === 'fill') correctLabel = q.answer.join('，');
  showFeedbackAndNext(correct, correctLabel, q.explanation || '');
}

function showEnd() {
  const total = reviewMode ? wrongList.length : quizData.filter(q => q.type !== 'info').length;
  const wrong = reviewMode ? reviewWrongList.length : wrongList.length;
  const score = total - wrong;
  let html = `<div class="question-title">${reviewMode ? '错题重做结束！' : '本轮答题结束！'}</div>`;
  html += `<div style="margin:16px 0;font-size:1.05em;">共 <b>${total}</b> 题&emsp;✔️ 正确 <b style="color:#16a34a">${score}</b>&emsp;❌ 错误/跳过 <b style="color:#dc2626">${wrong}</b></div>`;
  const nextWrong = reviewMode ? reviewWrongList.map(i => wrongList[i]) : wrongList;
  if (nextWrong.length > 0) {
    html += `<button id="review-btn" style="background:#f59e42;">错题重做（${nextWrong.length}题）</button> `;
  }
  html += `<button id="restart-btn" style="margin-left:8px;">重新全部作答</button>`;
  container.innerHTML = html;
  const reviewBtn = document.getElementById('review-btn');
  if (reviewBtn) {
    reviewBtn.onclick = function() {
      wrongList = nextWrong.slice();
      reviewMode = true;
      reviewIdx = 0;
      reviewWrongList = [];
      renderQuestion(reviewIdx);
    };
  }
  document.getElementById('restart-btn').onclick = function() {
    current = 0; answered = false; wrongList = []; reviewMode = false; reviewIdx = 0; reviewWrongList = [];
    renderQuestion(current);
  };
}

// 初始化
renderQuestion(current);
