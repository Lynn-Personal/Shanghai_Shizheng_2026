// 军事专题全题型模拟题
const quizData = [
  // ========== 填空题 ========== //
  { type: 'info', info: '【填空题 共40题，每题2分】' },
  { type: 'fill', question: '纪念中国人民抗日战争暨世界反法西斯战争胜利80周年阅兵式于____年____月____日在天安门广场举行。', answer: ['2025','9','3'], explanation: '2025年9月3日。' },
  { type: 'fill', question: '此次阅兵式的主题是纪念抗战伟大胜利、弘扬____伟大精神。', answer: ['抗战'], explanation: '弘扬抗战伟大精神。' },
  { type: 'fill', question: '中共中央总书记、国家主席、中央军委主席____检阅部队。', answer: ['习近平'], explanation: '习近平。' },
  { type: 'fill', question: '阅兵式彰显中国人民抗日战争作为世界反法西斯战争____主战场的历史地位。', answer: ['东方'], explanation: '东方主战场。' },
  { type: 'fill', question: '阅兵式上，____、网络空间部队、信息支援部队首次亮相天安门广场。', answer: ['军事航天部队'], explanation: '军事航天部队。' },
  { type: 'fill', question: '地面突击方队采用____型编队。', answer: ['箭'], explanation: '箭型编队。' },
  { type: 'fill', question: '99B坦克增加了____武器站。', answer: ['无人'], explanation: '无人武器站。' },
  { type: 'fill', question: '100坦克和100支援战车升级了____装甲。', answer: ['格栅'], explanation: '格栅装甲。' },
  { type: 'fill', question: '陆上无人作战方队装备的尺寸较小，主要考虑其____性和隐蔽性。', answer: ['灵活'], explanation: '灵活性和隐蔽性。' },
  { type: 'fill', question: '无人装备可与一线作战官兵协同配合，形成更强的____力。', answer: ['战斗'], explanation: '战斗力。' },
  { type: 'fill', question: '反无人机装备方队由____和空军混合编组而成。', answer: ['陆军'], explanation: '陆军和空军混合编组。' },
  { type: 'fill', question: '激光武器具备发射即到、海量弹仓、高精度性能及作战____低等优势。', answer: ['成本'], explanation: '作战成本低。' },
  { type: 'fill', question: '弹炮结合武器主要用于要地和重要目标的____。', answer: ['防卫'], explanation: '要地和重要目标的防卫。' },
  { type: 'fill', question: '高功率微波武器主要对____机、无人机群进行干扰。', answer: ['无人'], explanation: '无人机、无人机群。' },
  { type: 'fill', question: '战略打击群序幕由____导弹方队拉开。', answer: ['巡航'], explanation: '巡航导弹方队。' },
  { type: 'fill', question: '鹰击-21、东风-17、东风-26D导弹属于____音速导弹。', answer: ['高超'], explanation: '高超音速导弹。' },
  { type: 'fill', question: '巨浪-3属于____射洲际导弹。', answer: ['潜'], explanation: '潜射洲际导弹。' },
  { type: 'fill', question: '东风-5C属于____体洲际战略核导弹。', answer: ['液'], explanation: '液体洲际战略核导弹。' },
  { type: 'fill', question: '空警-500A和空警-600属于____机。', answer: ['预警'], explanation: '预警机。' },
  { type: 'fill', question: '歼-15DH、歼-15DT、歼-15T、歼-35组成的梯队属于____机梯队。', answer: ['舰载'], explanation: '舰载机梯队。' },
  { type: 'fill', question: '运-20B运输机装配____台国产发动机。', answer: ['4'], explanation: '4台国产发动机。' },
  { type: 'fill', question: '轰-6J轰炸机是此次阅兵的____面孔。', answer: ['新'], explanation: '新面孔。' },
  { type: 'fill', question: '歼-16D是我国自主研制的新型专用____战飞机。', answer: ['电子'], explanation: '电子战飞机。' },
  { type: 'fill', question: '歼-20、歼-20A属于重型隐身____座多用途战斗机。', answer: ['单'], explanation: '单座多用途战斗机。' },
  { type: 'fill', question: '歼-20S属于重型隐身____座多用途战斗机。', answer: ['双'], explanation: '双座多用途战斗机。' },
  { type: 'fill', question: '专家解读指出，九三阅兵展示的军事装备和作战体系代表了中国捍卫国家____、安全和发展利益的决心与能力。', answer: ['主权'], explanation: '国家主权、安全和发展利益。' },
  { type: 'fill', question: '中国防御性国防政策的辩证法是强大但不____，坚定而负责任。', answer: ['霸道'], explanation: '强大但不霸道。' },
  { type: 'fill', question: '一支更加成熟、专业和现代化的人民军队是维护中国国家安全的中流____。', answer: ['砥柱'], explanation: '中流砥柱。' },
  { type: 'fill', question: '中国特色军事变革的道路上，强大与____、自信与审慎实现了辩证统一。', answer: ['克制'], explanation: '强大与克制。' },
  { type: 'fill', question: '世界各国共同构建人类命运____体时，真正的普遍安全与持久和平才能到来。', answer: ['共同'], explanation: '人类命运共同体。' },
  // ...（可继续补充至40题）

  // ========== 单选题 ========== //
  { type: 'info', info: '【单项选择题 共20题，每题2分】' },
  { type: 'single', question: '2025年纪念中国人民抗日战争暨世界反法西斯战争胜利80周年阅兵式的地点是？', options: ['人民大会堂', '天安门广场', '人民英雄纪念碑', '长安街'], answer: [1], explanation: '天安门广场。' },
  { type: 'single', question: '此次阅兵式的主题不包括下列哪项？', options: ['纪念抗战伟大胜利', '弘扬抗战伟大精神', '展示经济成就', '彰显中国共产党作用'], answer: [2], explanation: '不包括展示经济成就。' },
  { type: 'single', question: '阅兵式上首次亮相的兵种不包括？', options: ['军事航天部队', '网络空间部队', '信息支援部队', '装甲兵部队'], answer: [3], explanation: '装甲兵部队。' },
  { type: 'single', question: '地面突击方队采用的编队类型是？', options: ['方形', '箭型', '圆形', '梯形'], answer: [1], explanation: '箭型编队。' },
  { type: 'single', question: '99B坦克升级的主要内容不包括？', options: ['无人武器站', '火力升级', '格栅装甲', '主防系统'], answer: [2], explanation: '格栅装甲是100坦克升级内容。' },
  { type: 'single', question: '反无人机装备方队的激光武器优势不包括？', options: ['发射即到', '高精度', '高成本', '海量弹仓'], answer: [2], explanation: '高成本不是优势。' },
  { type: 'single', question: '高功率微波武器的主要作用是？', options: ['打击坦克', '干扰无人机', '防御导弹', '侦察'], answer: [1], explanation: '干扰无人机。' },
  { type: 'single', question: '战略打击群的第二个方队是？', options: ['巡航导弹方队', '高超音速导弹方队', '核导弹第一方队', '核导弹第二方队'], answer: [1], explanation: '高超音速导弹方队。' },
  { type: 'single', question: '巨浪-3属于哪类导弹？', options: ['空基导弹', '潜射洲际导弹', '陆基导弹', '巡航导弹'], answer: [1], explanation: '潜射洲际导弹。' },
  { type: 'single', question: '歼-35属于哪类飞机？', options: ['运输机', '舰载战斗机', '轰炸机', '电子战飞机'], answer: [1], explanation: '舰载战斗机。' },
  // ...（补足20题）

  // ========== 多选题 ========== //
  { type: 'info', info: '【多项选择题 共20题，每题3分】' },
  { type: 'multiple', question: '此次阅兵式彰显了哪些内容？', options: ['中国人民抗日战争的历史地位', '中国共产党中流砥柱作用', '中国推动人类命运共同体', '中国经济成就'], answer: [0,1,2], explanation: '不包括经济成就。' },
  { type: 'multiple', question: '地面突击方队的装备升级包括？', options: ['无人武器站', '火力升级', '格栅装甲', '主防系统'], answer: [0,1,3], explanation: '不包括格栅装甲。' },
  { type: 'multiple', question: '陆上无人作战方队的无人装备功能包括？', options: ['打击', '扫雷排爆', '支援', '娱乐'], answer: [0,1,2], explanation: '不包括娱乐。' },
  { type: 'multiple', question: '反无人机装备方队的作战手段包括？', options: ['弹', '炮', '光', '电', '网'], answer: [0,1,2,3,4], explanation: '弹、炮、光、电、网。' },
  { type: 'multiple', question: '高功率微波武器的优势包括？', options: ['反应速度快', '不受精确瞄准限制', '覆盖多个目标', '高作战成本'], answer: [0,1,2], explanation: '不包括高作战成本。' },
  { type: 'multiple', question: '战略打击群的导弹类型包括？', options: ['巡航导弹', '高超音速导弹', '核导弹', '空空导弹'], answer: [0,1,2], explanation: '不包括空空导弹。' },
  { type: 'multiple', question: '空中梯队包括哪些类型？', options: ['预警机', '舰载机', '运输机', '轰炸机'], answer: [0,1,2,3], explanation: '四类均有。' },
  { type: 'multiple', question: '歼-20系列飞机的特点包括？', options: ['隐身', '多用途', '单座/双座', '高原适应'], answer: [0,1,2], explanation: '前三项正确。' },
  // ...（补足20题）

  // ========== 判断题 ========== //
  { type: 'info', info: '【判断题 共20题，每题1分】' },
  { type: 'judge', question: '纪念中国人民抗日战争暨世界反法西斯战争胜利80周年阅兵式于2025年举行。', answer: true, explanation: '判断为正确。' },
  { type: 'judge', question: '此次阅兵式首次亮相的信息支援部队是全新打造的战略性兵种。', answer: true, explanation: '判断为正确。' },
  { type: 'judge', question: '99B坦克升级后增加了无人武器站。', answer: true, explanation: '判断为正确。' },
  { type: 'judge', question: '高功率微波武器只能打击单一目标。', answer: false, explanation: '判断为错误。' },
  { type: 'judge', question: '歼-35是我国自主研制的新型隐身舰载战斗机。', answer: true, explanation: '判断为正确。' },
  { type: 'judge', question: '轰-6J轰炸机是此次阅兵的“新面孔”。', answer: true, explanation: '判断为正确。' },
  { type: 'judge', question: '中国防御性国防政策强调强大但不霸道。', answer: true, explanation: '判断为正确。' },
  { type: 'judge', question: '一支现代化的人民军队是维护国家安全的中流砥柱。', answer: true, explanation: '判断为正确。' },
  // ...（补足20题）
];
