# Day 23 · 属性上下文（attribute context）：不用标签也能跑

- **日期**：2026-10-20
- **靶场**：PortSwigger Web Security Academy + 本地玩具靶场 `attr_demo.py`（8081）
- **Lab**：`Reflected XSS into attribute with angle brackets HTML-encoded`（Apprentice 学徒档）
- **题目要求**：搜索功能存在反射型 XSS，尖括号被 HTML 编码。要求**注入一个属性**并调用 `alert` 函数。

## 一、HTML 里只有三种「格子」（context）

| 格子 | 长什么样 | 我写的 `<` `>` 是什么 | 逃出去要什么 | 逃出去后写什么 |
|---|---|---|---|---|
| **A 标签之间** | `<p>这里</p>` | 标签语法 | 不用逃 | 新标签 `<img src=x onerror=...>` |
| **B 属性值里**（今天） | `value="这里"` | 只是属性值的内容，开不出标签 | 一个**没被编码的引号** | 新属性 `on...=` |
| **C JS 字符串里** | `var s = "这里";` | 普通 JS 字符（`<script>` 里不解析标签） | JS 的引号 | JS 代码 |

判 context 只做两件事：**① 我的输入落在哪个格子 ② 这个格子需要的「开门字符」服务器编码了没有。**

## 二、为什么不用标签也能执行

一个标签 = **一排属性，空格隔开**：

```html
<input type="text"  value=""  onmouseover="alert(1)"  size="80">
       属性1         属性2      属性3（我注入的）        属性4
```

- Day 15 那条 `<img src=x onerror=alert(1)>`，**执行代码的是 `onerror` 这个属性**，不是 `<img>` 标签本身。标签只负责声明"我是个什么元素"。
- 所以只要能把输入塞进标签的**属性区**，再用空格隔开、挂一个 `onxxx=` 上去，就能执行代码 —— **全程不需要 `<` `>`**。
- 这个 lab 尖括号被编码（`<` → `&lt;`），但引号没被编码 → 标签开不出来，属性却挂得上去。

## 三、操作步骤（今天实际做的）

1. 起玩具靶场 `python3 ~/day23/attr_demo.py`，用 curl 对照「标签之间」和「属性值里」两种格子：
   - `<b>hi</b>` 放标签之间 → 真变粗体
   - 同样的东西放 `value="..."` 里 → 只是输入框里的一段文字
2. 打开输出编码开关（`&encode=1`）→ 看 `&lt;b&gt;` 怎么把 payload 掐死
3. 练「逃引号」：`?q="><b>hi</b>` → 源码变成 `value=""><b>hi</b>" size="80">`
4. 上 PortSwigger lab：搜索 `qzl12345` → `Ctrl+U` 找它落在哪 → 确认在 `value="..."` 里、尖括号被编码、`"` 原样
5. 先按 Day 21 的 `<img src=x onerror=...>` 打一次 → 被编码，死
6. 改成「关门 + 空格 + 事件属性」→ 见下面第四节
7. `curl` 取证（见第五节），再回浏览器把 URL 拷到新标签页、鼠标移过搜索框 → 弹窗 → `LAB Solved`

## 四、payload 与为什么生效

```
" onmouseover="alert(1)
```

拼接后源码：

```html
<input type=text placeholder='Search the blog...' name=search value="" onmouseover="alert(1)">
```

四步：

1. `"` —— 把 `value="` 这个属性**提前关上**（值变成空串 `value=""`）
2. ` ` 空格 —— 属性与属性之间的**分隔符**
3. `onmouseover="alert(1)"` —— **新挂上去的属性**，它的值本身就是 JS 代码区
4. 鼠标移过输入框 → `mouseover` 事件发生 → 浏览器执行属性值里的 `alert(1)`

> 补充：`autofocus` + `onfocus="alert(1)"` 可以做到**零交互**（页面一打开就弹），因为 `autofocus` 会让元素在加载完成后自动获得焦点。`onmouseover` 则需要受害者正好把鼠标移过去 —— 真实报告里后者可信度低一档。

## 五、证据

### 5.1 lab 判定

`LAB Solved` + `Congratulations, you solved the lab!`

### 5.2 源码里 payload 落点（`Ctrl+U` / curl 第 55 行）

```html
<input type=text placeholder='Search the blog...' name=search value="" onmouseover="alert(1)">
```

### 5.3 curl 取证

```bash
P='%22%20onmouseover%3D%22alert%281%29'
curl -sS --http1.1 -o /tmp/d23.html -w 'HTTP=%{http_code} SIZE=%{size_download}\n' "https://<实例>/?search=$P"
grep -n 'value=' /tmp/d23.html
```

输出：

```
HTTP=200 SIZE=3355
55:  <input type=text placeholder='Search the blog...' name=search value="" onmouseover="alert(1)">
```

### 5.4 同一个参数、两个输出点、编码规则不同

| 输出点 | 输入是 `" > test123` 时的样子 | 能打吗 |
|---|---|---|
| `<h1>0 search results for '...'</h1>`（标签之间） | `&quot;&gt;test123`（引号也编码了） | ❌ 只能当文字 |
| `value="..."`（属性值里） | `value=""&gt;test123"`（**引号原样**） | ✅ 关门成功 |

> 所以「逐字段试」在 Day 23 升级成「**逐输出点试**」：同一次输入会被服务器的不同位置输出，每处规则可能都不同。

## 六、三轮调试复盘（这才是今天的主要收获）

| 轮次 | payload | 现象 | 根因 |
|---|---|---|---|
| 1 | `" oninput=alert("1")` | 不弹 | ① `oninput` 要**打字**才触发，页面加载时不会发生 ② 属性值没加引号，值里混进多余引号 → `SyntaxError` |
| 2 | `" onmouseover="alert("1")"` | 不弹 | **双引号套双引号**：值在 `alert(` 处就被 `"` 切断了 → 未闭合括号 |
| 3 | `" onmouseover="alert(1)` | 弹窗，`LAB Solved` | 引号三层理清：模板引号关门 / 属性值引号成对 / 值内字符串用单引号 |

另外还踩过：

- 照 Day 21 的记忆猜参数名 `searchTerm`、猜路径 `/search` → **404**（这个 lab 是 `action=/`、`name=search`，得抄表单）
- `curl -s` 把错误吞了 → 以为"没输出"，其实是静默失败（要用 `-sS`）
- URL 里写了裸空格 → 请求根本没发出去
- lab 实例休眠 → `504 Gateway Timeout`，回平台重置后地址变了（`0af6…` → `0ac9…`）

## 七、我实际卡住的

（本人原话，未改一字）

没搞懂onfocus是干嘛的，之后才知道这个焦点的意思。
没搞懂各种编码的不同，有的是浏览器编的有的是服务器编的。
引号使用错误了，要注意双引号套单引号各是各的。

## 八、我学到了什么（费曼）

（本人原话，未改一字）

今天学习了把内容插入value的xss方法，依然需要先测试哪个输入点可以不被编码的进入，找到突破口后根据源代码编写payload。

