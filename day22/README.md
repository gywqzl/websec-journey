# Day 22 · 存储型 XSS（Stored XSS）

- **日期**：2026-10-19
- **靶场**：DVWA `XSS (Stored)`（本地，Security = Low）+ PortSwigger Web Security Academy
- **Lab**：Stored XSS into HTML context with nothing encoded（Apprentice 学徒档）
- **题目要求**：评论区有一个存储型 XSS，提交一条评论，使文章页被查看时调用 `alert` 函数。

## 一、它和反射型（Reflected）差在哪

| | Reflected（Day 21） | Stored（今天） |
|---|---|---|
| 数据留不留 | 不存，当场回显 | **存进服务器**（数据库 / 文件） |
| 谁中招 | 点了那条链接的人 | **所有访问该页面的人**（包括管理员） |
| 证据在哪 | URL 的 query 里 | **服务器返回的 HTML 正文里** |
| URL 干净吗 | 不干净，带着 payload | **干净**，只带 `?postId=10` |

## 二、今天的新模型：输入点 ≠ 输出点

- **输入点（input point）**：数据塞进去的地方 —— 评论表单的四个字段（comment / name / email / website）
- **输出点（output point / sink）**：数据被吐出来、拼进 HTML 的地方 —— 文章页的评论列表

这两个点**不在同一个请求里**，这就是存储型和反射型的结构差别。

## 三、操作步骤

### 1. DVWA（本地靶场）

1. 登录 DVWA，`DVWA Security` 设为 **Low**，进入 `XSS (Stored)`
2. 先做一次干净的留言当基线：Name = `Qzl`，Message = `123456`
3. `Ctrl+U` 看源码，确认输出位置：

   ```html
   <pre>Name: Qzl<br />Message: 123456</pre>
   ```

4. 把 Message 换成 payload：`<img src=x onerror=alert('Qzl')>`
5. 刷新 3 次 + 关掉页面重开 → **每次都弹**
6. 看地址栏：`http://localhost/dvwa/vulnerabilities/xss_s/` —— **没有任何 `?` 参数**

### 2. PortSwigger lab

1. Access the lab，先随便发一条正常评论，看它出现在文章页的哪个位置
2. 判断上下文：评论正文落在 `<p>...</p>` 之间（**标签之间**）
3. 提交 payload，回到博客文章页刷新 → 弹窗
4. 页面显示 `✓ Solved` / `Congratulations, you solved the lab!`

## 四、payload 与为什么能生效

```html
<img src=x onerror=alert('Qzl')>
```

1. payload 从评论框进来（**输入点**）
2. 服务器把它**原样存进数据库**（nothing encoded，一点编码都没做）
3. 任何人打开文章页，服务器从数据库取出来、**原样拼进** `<p>` 标签里（**输出点**）
4. 浏览器读到 `<img src=x ...>`：真的去加载 `x` → 加载失败 → 触发 `onerror` → 里面的 JS 执行 → 弹窗
5. 刷新一百次、换个人来看，结果一样 —— 因为毒存在服务器上

## 五、证据

### 证据 1：lab 判定

`LAB: Solved` + `Congratulations, you solved the lab!`

### 证据 2：curl 打开「干净的 URL」，页面里却有 payload

```bash
curl -s "https://0a99004f038516d58224933d000900db.web-security-academy.net/post?postId=10" -o /tmp/post.html
grep -o "onerror.\{0,30\}" /tmp/post.html
```

输出：

```
onerror=alert(Qzl)&gt;</a> | 19 Octob
onerror=alert(&quot;Qzl&quot;)&gt;</a
onerror=alert("Q")></p>
```

**判据**：请求的 URL 只带 `postId=10`、**不含任何 payload**；但服务器返回的响应正文里 payload 以原样字符存在 → 毒存在服务器端（持久化） → 判定 **Stored XSS**。

### 证据 3：DVWA 存储型

刷新多次 / 关页面重开后仍然弹窗，`Ctrl+U` 源码里 payload 是原文（没变成 `&lt;img`）。

## 六、一个意外发现：同一个表单，不同字段处理不一样

三条命中里只有一条是「活的」：

| 落点 | 服务器怎么处理 | 结果 |
|---|---|---|
| comment 字段（在 `<p>` 之间） | 原样输出 | ✅ `onerror=alert("Q")></p>` → 执行 |
| name 字段（在 `<a>` 里） | `"` → `&quot;`、`>` → `&gt;` | ❌ 标签开不出来，不执行 |

**教训：不能试一个字段就下结论，同一个表单要逐字段、逐个参数试。**

(`&quot;` / `&gt;` 叫 **HTML 实体（entity）** —— 服务器把特殊字符「翻译」成不会被当成代码的写法，这正是修复 XSS 的正解「输出编码」在做的事。)

## 七、我实际卡住的

（本人原话，未改一字）

今天在检查网站时的乱七八糟的元素那里愣住了，产生了疑问为什么这跟源代码不一样？之后得到了答案。这些元素时浏览器加工过的，要看我需要的需要在源代码看

## 八、我学到了什么（费曼）

（本人原话，未改一字）

存储型xss的原理是在输入点输入信息后寻找输出点在哪，找到输出点的位置验证输出点的规则，找到合适的输入输出点后配备payload。最大的区别是这个是存在服务器的人人中招。
