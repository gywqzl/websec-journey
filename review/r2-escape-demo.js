// R2 备课自测：反斜杠「吃掉紧跟的一个字符」到底吃掉什么
// 用法：node review/r2-escape-demo.js
// 用 (globalThis.hit = 1) 代替 alert(1)，这样命令行能看到「有没有真的执行」

function show(label, src) {
  globalThis.hit = 0;
  try {
    eval(src);
    console.log(label, '=> 没报错，hit =', globalThis.hit, globalThis.hit ? '（代码执行了）' : '（被当普通字符吃掉了）');
  } catch (e) {
    console.log(label, '=> 报错:', e.constructor.name, '|', e.message);
  }
}

// 1. \' 把引号变成普通字符：字符串不结束
show('1 反斜杠吃引号', "'it\\'s';");

// 2. \\ = 两颗互吃，剩一个真反斜杠，谁都不保护
show('2 两颗互吃    ', "'a\\\\b';");

// 3. 反斜杠吃掉收尾引号 -> 字符串永远不结束 -> 语法错误
show('3 吃掉收尾引号', "'abc\\';");

// 服务端两种打法
function onlyQuote(s) { return s.replace(/'/g, "\\'"); }                        // 只把 ' -> \'
function both(s) {                                                              // ' -> \'  且  \ -> \\
  return s.replace(/\\/g, '\\\\\\\\').replace(/'/g, "\\'");
}

const payload = "\\';globalThis.hit=1//";   // 输入：反斜杠 + 引号 + ; 执行 ; // 注释掉尾巴
const a = onlyQuote(payload);
const b = both(payload);
console.log('输入            :', JSON.stringify(payload));
console.log('只转义引号      :', JSON.stringify(a));
console.log('引号和反斜杠都转:', JSON.stringify(b));

show('4 只转义引号    ', "var x = '" + a + "';");
show('5 两个都转义    ', "var y = '" + b + "';");
