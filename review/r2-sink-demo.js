// R2 备课自测 2（node 版）：字符串什么时候被当「代码」处理
// 用法：node review/r2-sink-demo.js
//
// 注意：setTimeout 的「字符串版」是浏览器老特性，node 会直接 TypeError 拒收，
// 所以那一项在 r2-sink-demo.html 里用真浏览器（Edge --headless=new）验证。

// 1. eval 的两副面孔
console.log('1a eval("1+1")            =', eval('1+1'), '（算出来，返回 2）');
globalThis.hit = 0;
eval('globalThis.hit = 1');
console.log('1b eval("globalThis.hit=1")后 hit =', globalThis.hit, '（字符串被当代码跑了）');

// 2. node 对「字符串版 setTimeout」的态度
try {
  setTimeout('globalThis.hit2 = 2', 0);
  console.log('2  setTimeout(字符串) 被接受了');
} catch (e) {
  console.log('2  setTimeout(字符串) 报错:', e.name, '| 浏览器接受、node 不接受 → 该项见 r2-sink-demo.html');
}

// 3. 对照：字符串当「数据」传，没人去执行它
const asData = '<img src=x onerror=globalThis.hit3=1>';
let box = asData;          // 类比 textContent：只当纯文本存着
console.log('3  box 里存的字 =', box);
console.log('   存了这么多字，hit3 =', globalThis.hit3 === undefined ? '从未定义（没有任何东西去执行它）' : globalThis.hit3);
