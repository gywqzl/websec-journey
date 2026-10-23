# Day 26 · 实战任务卡：内部便签站 XSS 审计（Day 16–25 综合）

> 第四次实战任务卡。前三次是「查一台主机」，这次是「审一个站」。
> 考的不是多打几个洞，是**能不能把看到的东西说准**——报告写错，开发就照着错的改。

## 今天做了什么

自己搭了一个带漏洞的小站（`site26.py`，只监听 `127.0.0.1:8090`），在**不给看源码**的前提下做黑盒审计：
六个入口逐个走一遍 → 找输入点和输出点 → 判每个输出落在哪种「格子」→ 按格子配 payload → 弹窗/Console 验证 → 用 curl 留证据 → 写成审计报告。

## 靶场（自建，故意带洞）

```bash
python3 site26.py          # 然后浏览器打开 http://127.0.0.1:8090/
```

| 入口 | 用途 | 有洞吗 |
|---|---|---|
| `/` | 首页 | 没有输入点 |
| `/search?q=` | 站内搜索 | ✅ 标签之间 |
| `/profile?name=` | 个人资料（昵称从 URL 取） | ✅ 属性值里 |
| `/feedback?msg=` | 反馈（内测版，走 URL） | ✅ JS 字符串里 |
| `/note` | 留言板（表单 POST，服务器存在内存） | ✅ 存储型（content 字段）；**title 字段打不通** |
| `/dashboard` | 控制台（`#` 后的内容交给页面 JS） | ✅ DOM 型 |

## 审计结果

| 编号 | 入口/参数 | 类型 | 上下文 | payload |
|---|---|---|---|---|
| F-1 | `/search?q=` | Reflected | 标签之间 | `<img src=x onerror=alert(1)>` |
| F-2 | `/profile?name=` | Reflected | 属性值里 | `' autofocus onfocus=alert(1) ` |
| F-3 | `/feedback?msg=` | Reflected | JS 字符串里 | `</script><script>alert(1)</script>` |
| F-4 | `/note` 的 `content` | Stored | 标签之间 | `<img src=x onerror=alert(1)>` |
| F-5 | `/dashboard#…` | DOM | 标签之间 | `#<img src=x onerror=alert(1)>` |

完整判定、证据、修复建议见 [`report26.md`](report26.md)。

## 今天真正学到的东西

**1. 五种格子（判上下文的唯一依据）**

| 格子 | 长什么样 | 要逃什么 |
|---|---|---|
| 标签之间 | `<h2>数据</h2>` / `<div id='out'>数据</div>` | `<` `>` |
| 属性值里 | `<input value='数据'>` | 包裹它的那个引号 |
| JS 字符串里 | `<script>var a='数据'</script>` | JS 引号 / `</script>` |
| URL 里 | `<a href="？x=数据">` | `javascript:` 之类协议 |
| HTML 注释里 | `<!-- 数据 -->` | `-->` |

判法只有一个：**看 payload 前后紧挨着的字符**。

**2. 类型 ≠ 上下文** —— 类型说「数据从哪来」（Reflected / Stored / DOM），上下文说「落在哪一格」。DOM 型不是第六种格子。

**3. 「0 命中」有三种可能** —— ① 请求没发出去 ② 发错门 ③ 真的没有。前两个不排除，`0` 不是证据。

**4. 存储型要两步、DOM 型要两条** —— 存储型：先存（`303`，body 是空的）再干净 GET；DOM 型：响应里没有 **+** 服务器日志里也没有。

**5. 未加引号的属性值「吃到哪」** —— 一直读到空白或 `>` 才结束，所以 payload 末尾那个空格是语法必需的收尾符。

## 取证命令（报告里的证据全靠它们）

```bash
# 反射型：请求里必须带 payload，grep 用长特征串
curl -sG --data-urlencode "q=<img src=x onerror=alert(1)>" http://127.0.0.1:8090/search \
  | grep -o "onerror=alert(1)"

# 存储型：两步
curl -o /dev/null -w '%{http_code}\n' -d "title=t1&content=<img src=x onerror=alert(1)>" http://127.0.0.1:8090/note
curl -s http://127.0.0.1:8090/note | grep -o "title='t1'><img src=x onerror=alert(1)>"

# DOM 型：编码后请求（# 后面空格要写 %20）+ 看服务器日志
curl -sS -o /tmp/dash.html -w '%{http_code} %{size_download}\n' \
  "http://127.0.0.1:8090/dashboard#%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E"
grep -c onerror /tmp/dash.html        # → 0
```

## 我实际卡住的

1. **卡在 `#` 后面那截**：我以为它是注释，记混了。其实它是 URL 的 fragment（片段），浏览器根本不发给服务器，是页面自己的 JS 用 `location.hash` 读的。
2. **卡在 F-4 的输出点落在哪**：我以为在 `title='...'` 里面（属性值里）。其实 `title` 那个字段是打不通的，我真正打进去的 `content` 落在 `</a>` 前面 —— 两个字段的处理方式不一样。
3. **卡在 F-5 的证据**：我看到 `0` 就当成了"测不出"。其实是 URL 里写了裸空格，`curl: (3) URL rejected`，请求根本没发出去，`-s` 还把报错吞了。

## 我以后会这样做

1. 看到 `0` 先确认请求到底发没发出去 —— 注意 `grep` 本身证明不了这一点，得看 `http_code`（`000` = 没发/没连上）或 `-S` 的报错，确认发出去了再判断是不是"真没有"。
2. 填「上下文」之前先看网站源代码（`Ctrl+U` 或 `curl`），看输出落在哪个位置、前后紧挨着什么字符。

## 环境说明

- 本地练习靶场，`HTTPServer` 只绑定 `127.0.0.1:8090`，不对外；留言板数据只存在内存，重启即清空。
- 靶场**故意**包含 XSS 缺陷，仅用于合法授权环境下的学习与自测，**请勿部署到公网或任何他人可访问的机器**。
- 报告中所有域名/地址均为本机回环地址（`127.0.0.1`），不含任何真实目标信息。
