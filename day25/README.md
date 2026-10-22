# Day 25 · DOM 型 XSS（DOM-based XSS）

> 目标：搞清「服务器从头到尾没见过 payload」这一类 XSS，并打掉 PortSwigger
> `DOM XSS in document.write sink using source location.search`（Apprentice）。
>
> 环境：本地玩具靶场 `~/day25/`（8083 端口）+ PortSwigger Web Security Academy。

## 一、DOM 型 XSS 是什么

一句话：**服务器发的是一个固定不变的死页面，是页面自己的 JavaScript 读了地址栏、把内容拼进页面，结果被浏览器当 HTML 解析了。**

服务器在这条链上只干了两件事：把 `dom_search.html` 原样发出去、把 `tracker.gif` 原样发出去。**它从来没收到过 payload。**

## 二、两个零件：source 和 sink

| 零件 | 中文 | 是什么 | 今天的例子 |
|---|---|---|---|
| **source** | 源 | 攻击者能控制的输入从哪进来 | `location.search`（`?` 后）、`location.hash`（`#` 后） |
| **sink** | 汇 | 哪个函数把字符串当「代码 / HTML」处理 | `document.write`、`innerHTML` |

**漏洞条件 = source 的数据流到了 sink，中间没有编码 / 过滤。**

注意：`location.search` 本身只是**一个字符串**，无害。它危险是因为被送进了 `document.write`。
**sink 才是那把刀，source 只是递刀的手。**

## 三、操作步骤（今天实际做的）

1. `cd ~/day25 && python3 -m http.server 8083`
2. 浏览器打开 `http://localhost:8083/dom_search.html?q=hello` → 页面显示「你搜的是：hello」
3. Console 认零件：依次敲 `location.href` / `location.search` / `location.hash` / `document.referrer`
4. `nano dom_search.html` 找两个零件 → source 是 `var s = location.search;`，sink 是 `document.write(...)`
5. 打它：`?q=<img src=x onerror=alert(1)>` → 弹窗
6. 取证：两条 `curl | grep -c "onerror"` → 都是 `0`
7. 对照 `Ctrl+U`（搜不到 payload）与 `F12 → Elements`（搜得到）
8. 打官方 lab → `LAB Solved`

## 四、payload 与为什么生效

最终 payload：

```
"><img src=x onerror=alert(1)>
```

lab 的 sink 是：

```js
document.write('<img src="/resources/images/tracker.gif?searchTerms=' + query + '">');
```

拼出来之后，浏览器拿到的是这一串：

```html
<img src="/resources/images/tracker.gif?searchTerms=">' ) <img src=x onerror=alert(1) >; //">
```

HTML 解析器逐段读：

| 片段 | 解析器怎么读 |
|---|---|
| `<img src="...searchTerms=` | 开始一个 img 标签、开始 src 属性值 |
| `"` | **结束 src 属性值** |
| `>` | **结束整个 img 标签** |
| `<img src=x onerror=alert(1)>` | **新标签**；`src=x` 加载失败 → `onerror` 执行 → 弹窗 |
| `; //` `">` | 标签之间的普通文字（所以页面上能看见） |

**关键：payload 在 JS 里只是一个字符串的值（数据），JS 不把它当语法；等 `document.write` 把它倒到页面上，它才变成 HTML 源码，由 HTML 解析器读。**

## 五、证据

### 5.1 lab 判定

`LAB Solved` + `Congratulations, you solved the lab!`

### 5.2 本地 8083 取证：服务器从没发过 payload

```bash
curl -s "http://localhost:8083/dom_search.html?q=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E" | grep -c "onerror"
curl -s "http://localhost:8083/dom_hash.html#%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E" | grep -c "onerror"
```

两条都是 `0`。

原因：静态服务器只发固定文件，它不解析 `?q=`，所以响应字节里没有 payload；`#` 后面的内容浏览器根本不发出去。

### 5.3 Ctrl+U vs F12 Elements

| 视图 | 搜 `onerror` | 说明 |
|---|---|---|
| `Ctrl+U`（服务器原文） | **0 命中** | 服务器那份文件里没有 payload |
| `F12 → Elements`（活体 DOM） | **命中**，而且是真的 `<img>` 元素 | 是页面 JS 现场拼进去的 |

**「`Ctrl+U` 搜不到、`F12` 有」就是这个类型的判据。**

### 5.4 Console 对账

```js
trackSearch.toString()
```

打印出函数源码，里面只有一个 `query` 变量，**没有我的 payload**——
证明 payload 从来没变成过 JS 源码。

## 六、复盘：今天最贵的两个教训

1. **payload 是「数据」还是「源码」，取决于它被放在哪。**
   - 服务器 `echo` 进 `<script>` 的字符串（Day 24）→ 它是 **JS 源码**，要算转义
   - 页面 JS 用 `+ query +` 拼（今天）→ 它是**字符串的值**，JS 语法永远合法，`//` 也不是注释

2. **`//` 要当注释，必须同时满足「JS 正在读」和「不在字符串里」。**
   再进一步：注释符是方言 —— JS 用 `//`、HTML 用 `<!--`、SQL 用 `--`。**用注释必须用对层。**

## 七、我实际卡住的

理解错了层级之间的关系，页面里的 js 跑在浏览器里，html 和 js 可以通过特定的方法来回倒，做事要留意 payload 的最终落点是在 html 还是 js。

## 八、我学到了什么（费曼）

今天学习了 DOM 型 XSS。这种类型需要找 source 和 sink，找内容在哪能写入、在哪能被执行。DOM 型的 XSS 在 `Ctrl+U` 里搜不到，没有被打印出来。页面 JS 会去读地址栏或者别的信息（主要用 `location.search`）得到那个字符串，然后通过 `document.write` 等等倒进 HTML 层进行执行。
