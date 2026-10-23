# Day 26 实战任务卡 · 内部便签站 XSS 审计报告

- 审计人：Qzl
- 日期：2026-10-23
- 靶场：http://127.0.0.1:8090/ （本地练习站，仅监听 127.0.0.1）
- 审计方式：浏览器实际操作 + curl 取证

---

## 一、审计对象与环境

站点用途：一个给某小组内部用的小站：搜索、资料、反馈、留言板、控制台。

| 入口 | 用途 |
|---|---|
| `/` | 仅仅对本站有一个介绍，没什么特别的 |
| `/search?q=` | 可以通过改变 url 的 query 进行站内搜索 |
| `/profile?name=` | 一个个人界面，写了昵称和角色。昵称有一个输入框但点击无法更改，昵称可从 url 更改 |
| `/feedback?msg=` | 可以通过改变 url 的 query msg 来提交反馈内容，并且页面上会打印出来反馈内容 |
| `/note` | 可以写标题和内容进行存储留言 |
| `/dashboard` | 当前权限不够，只能看到当前视角为默认，没有任何内容 |

以上测试方法均为浏览器实操（取证阶段另用 curl）。

---

## 二、漏洞清单（概览）

| 编号 | 入口/参数 | 类型 | 上下文 | 危险度 |
|---|---|---|---|---|
| F-1 | `/search?q=` | Reflected | 标签之间 | 中 —— `<>'""` 均未编码，打开链接即触发 |
| F-2 | `/profile?name=` | Reflected | 属性值里 | 中 —— 对 `<>` 编码了，但没编码 `'` |
| F-3 | `/feedback?msg=` | Reflected | JS 字符串里 | 中 —— 对 `'` 和 `\` 转义了，但 `<>` 未编码 |
| F-4 | `/note` 表单的 content 字段 | Stored | 标签之间 | 高，只要进这个网站的人都会在中招 |
| F-5 | `/dashboard`（`#` 后的内容） | DOM | 标签之间 | 高 服务器无法拦截 |

> 上下文只能填：标签之间 / 属性值里 / JS 字符串里 / URL 里 / HTML 注释里
> 危险度三维度：① 受害者要不要配合 ② 影响几个人 ③ 服务端能不能拦

---

## 三、逐条详情

### F-1 搜索页反射型 XSS

- **入口 / 参数**：`/search?q=`
- **输入点**：url 的 query 参数 `q`
- **输出点**：
  ```
  <h2>Search results for ''<img src=x onerror=alert(1)>'</h2><p>没有找到相关记录。</p>
  ```
- **上下文判定**：标签之间。依据：payload 前后是 `<h2>…` 和 `</h2>`，直接落在文字区
- **payload**：`'<img src=x onerror=alert(1)>`
- **触发方式**：需要点击加了 payload 的特殊链接
- **证据**：
  ```bash
  curl -sG --data-urlencode "q=<img src=x onerror=alert(1)>" http://127.0.0.1:8090/search | grep -o "onerror=alert(1)"
  ```
  ```
  onerror=alert(1)
  ```
- **修复建议**：对 `<` `>` `'` 做 HTML 实体编码

### F-2 我的资料页属性注入

- **入口 / 参数**：`/profile?name=`
- **输入点**：url 的 query 参数 `name`
- **输出点**：昵称：<input type='text' value='' autofocus onfocus=alert(1) ' readonly></p><p>角色：普通用户</p>
- **上下文判定**：属性值里
- **payload**：`' autofocus onfocus=alert(1) `（**末尾空格是语法必需的**）
- **触发方式**：点击进页面就会触发（`autofocus` 让它自动获得焦点）
- **证据**：
  ```bash
  curl -sG --data-urlencode "name=' autofocus onfocus=alert(1) " http://127.0.0.1:8090/profile | grep -o "alert(1)"
  ```
  ```
  alert(1)
  ```
- **修复建议**：对单引号进行编码或转义（属性值统一做 HTML 实体编码）

### F-3 反馈页 JS 字符串上下文

- **入口 / 参数**：`/feedback?msg=`
- **输入点**：url 的 query 参数 `msg`
- **输出点**：
  ```
  var msg = '</script><script>alert(1)</script>';document.getElementById('out').innerHTML = '感谢反馈：' + msg;</script>
  ```
- **上下文判定**：JS 字符串里。依据：数据被拼进 `var msg = '...'` 的引号内部
- **payload**：`</script><script>alert(1)</script>`
- **触发方式**：进入页面即触发
- **证据**：
  ```bash
  curl -sG --data-urlencode "msg=</script><script>alert(1)</script>" http://127.0.0.1:8090/feedback | grep -o "alert(1)"
  ```
  ```
  alert(1)
  ```
- **修复建议**：对 `<` `>` 做 HTML 实体编码，使 `</script>` 无法结束脚本块；更彻底的做法是**不把输入拼进 `<script>`** —— 改用 `data-*` 属性传值，前端用 `dataset` 读、`textContent` 写（Day 24 选择题的 b 方案）

### F-4 留言板存储型 XSS

- **入口 / 参数**：`/note` 表单的 `content` 字段（POST 提交，GET 回显）
- **输入点**：留言板表单的 content；表单有 `maxlength` 和 `onsubmit` 拦 `<`，用 curl 直接 POST 绕过
- **输出点**：
  ```
  title='t1'><img src=x onerror=alert(1)></a>
  ```
- **上下文判定**：标签之间。依据：payload 落在 `<a href='#' title='t1'>` 与 `</a>` 之间，落地为 `title='t1'><img src=x onerror=alert(1)></a>`
- **payload**：`curl -d "title=t1&content=<img src=x onerror=alert(1)>" http://127.0.0.1:8090/note`
- **触发方式**：进网页就会弹
- **证据**（两步：先存、再用干净 URL 读）：
  ```bash
  curl -o /dev/null -w '%{http_code}\n' -d "title=t1&content=<img src=x onerror=alert(1)>" http://127.0.0.1:8090/note
  curl -s http://127.0.0.1:8090/note | grep -o "title='t1'><img src=x onerror=alert(1)>"
  ```
  ```
  303
  title='t1'><img src=x onerror=alert(1)>
  ```
- **修复建议**：从服务器那边对 `<>` 进行编码处理

### F-5 控制台 DOM 型 XSS

- **入口 / 参数**：`/dashboard`，`#` 后面的 fragment
- **输入点**：url 的 `#` 后面那段（**浏览器不会发给服务器**，由页面自己的 JS 读取）
- **source**：`var h = location.hash.slice(1);`
- **sink**：`document.getElementById('out').innerHTML = decodeURIComponent(h);`
- **输出点**：document.getElementById('out').innerHTML = decodeURIComponent(h);把payload塞进了out里
- **上下文判定**：标签之间。依据：`innerHTML` 把 payload 当 HTML 解析后作为 `div#out` 的子内容插入，落在 `<div id="out">` 与 `</div>` 之间
- **payload**：`#<img src=x onerror=alert(1)>`
- **触发方式**：点进带 payload 的特殊链接
- **证据**（要两条：响应里没有 + 服务器日志里也没有）：
  ```bash
  curl -sS -o /tmp/dash.html -w '%{http_code} %{size_download}\n' "http://127.0.0.1:8090/dashboard#%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E"
  grep -c onerror /tmp/dash.html
  ```
  ```
 200 995
 0
  ```
  ```
  ```
 127.0.0.1 - - [23/Oct/2026 13:07:26] "GET /dashboard HTTP/1.1" 200 -
- **修复建议**：sink 那里把 `innerHTML` 换成 `textContent`（让数据当文字打印而不是当 HTML 解析）；如确实要显示富文本，接入 HTML 净化库。服务端不参与这一步，只能在前端修

---

## 四、打不通的字段 / 试过但没成的路

1. F-2 的 `onnmouseover` / `onnmouseout` 试了没反应，因为单词拼写错了多写了n
2. F-2 的 `' autofocus onfocus=alert(1)` 不加末尾空格 —— 试了，没弹，原因：alert需要与后面的东西隔开不然会被连读成alert'没意义了

> 注：「我的 curl 命令报错」属于测试过程失误，不进这一节。

---

## 五、curl 能测出 / 测不出

F1–F4 都能测出，F5 测不出，因为 F1–F4 都经过了服务器（payload 进了服务器返回的 HTML 里），而 F5 的 payload 在 `#` 后面，浏览器根本不发给服务器。

| 编号 | curl 能否拿到证据 | 为什么 |
|---|---|---|
| F-1 | 能 | payload 在服务器返回的 HTML 里 |
| F-2 | 能 | 同上 |
| F-3 | 能 | 同上 |
| F-4 | 能（存之后 GET 干净 URL） | 服务器把 payload 存在内存里，再原样吐给每个访客 |
| F-5 | 不能 | `#` 后的内容不发往服务器，服务器返回的是死页面 |

---

## 六、风险总结与修复优先级

排序：**F-4 > F-5 > F-1 > F-2 > F-3**

1. **F-4** —— 占维度①②：不需要受害者做任何配合，所有打开留言板的人都会中招
2. **F-5** —— 占维度③：服务器完全不参与，WAF/服务端编码都拦不住
3. **F-1** —— 需特殊网址触发只针对点击网址的人，未编码的符号更多更易渗透
4. **F-2** —— 需特殊网址触发只针对点击网址的人
5. **F-3** —— 需特殊网址触发只针对点击网址的人

**总体建议**：好好处理一下编码上的问题

---

## 七、提示使用记录

- F-4 写 curl 不太熟练，用了 AI 帮忙修正
