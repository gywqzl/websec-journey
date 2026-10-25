# Day 27 · URL 格子（`href` / `javascript:` 协议）

> 五格表的最后一格。日期：2026-10-25。环境：本机靶场 `127.0.0.1:8084` + PortSwigger Academy（Apprentice）。

## 一、今天做了什么

1. 用自建靶场搞清「**同一时刻，源码里没有、DOM 里有**」到底是什么意思；
2. 打通官方 lab：`DOM XSS in jQuery anchor href attribute sink using location.search source`（`✓ Solved`）；
3. 学会一条判据：**`Ctrl+U` 是服务器字节（定格），`F12 → Elements` 才是活体 DOM**。

## 二、URL 格子：这一格逃的不是引号，是「协议」

| scheme | 交给谁处理 | 结果 |
|---|---|---|
| `http:` / `https:` | 网络栈 | 发请求、换页面 |
| `mailto:` | 邮件客户端 | 打开写信窗口 |
| **`javascript:`** | **JS 引擎** | 把 `:` 后面整段当代码，在**当前页面**里执行，不发请求 |

三个要点：

1. `javascript:alert(1)` —— `:` 后面**直接是代码**，没有 `//`；
2. 执行环境是**当前页面**，所以 `document.cookie`、`document.domain` 都能直接读；
3. 触发时机是**点击那一刻**，不是页面加载。

**为什么 Day 23 那招在这里全废**：`" onmouseover="alert(1)` 需要你的值**以文本形式出现在 HTML 属性里**，让 HTML 解析器读到引号「关门」再加一个新属性。
而这里的值是页面 JS 运行时**赋值**给 DOM 属性（`.attr("href", 值)`），**没有解析器在场，只是赋值**——引号和空格就只是普通字符，等于「没有门可关」。

> 一句话：**属性注入需要 HTML 解析器在场；DOM 赋值没有解析器。**

## 三、jQuery 只是换了写法

| 原生（我会） | jQuery 等价 |
|---|---|
| `document.getElementById('back')` | `$('#back')` |
| `el.href`（读） | `$('#back').attr('href')` |
| `el.href = '/new'`（写） | `$('#back').attr('href', '/new')` |

`attr` = attribute（属性）；**一个参数是读、两个参数是写**。选择器里的 `#` = “按 id 找”（CSS 写法），**跟地址栏的 `#`（fragment）没关系**。

## 四、lab 的标准流程（我最后是照这个复现的）

1. 实例页 → **Submit feedback** 页面（URL 上带 `?returnPath=/`）；
2. 把参数改成随机串（如 `/zhangsan123`）→ **右键 Back 链接 → 检查（Elements）** → 看到它被塞进 `<a href="...">`；
3. 改成 `javascript:alert(document.cookie)` → 回车 → **点 back 链接** → 弹窗 → `✓ Solved`。

> 官方 Solution 第 2 步用的是 **Elements** 而不是 `Ctrl+U`——正因为这是 **DOM 型**：值由页面 JS 运行时写进去，源码字节里永远看不到。

## 五、取证：怎么证明「服务器从没见过我的值」

| 手段 | 命令 / 做法 | 结论 |
|---|---|---|
| 标记值 | `?returnPath=/MARKER123` | 探针必须「只可能来自我」，别用 `/`（与默认值撞车） |
| 指纹对照 | `curl …?returnPath=AAA \| md5sum` vs `BBB` | **md5 相同 = 输出与输入无关** |
| 计数 | `curl … \| grep -c MARKER123` | `0` 命中；但要先排除“请求没发出/发错门” |
| 活体 DOM | `msedge --headless=new --dump-dom "URL"` 或 Console 敲 `el.outerHTML` | 跑完 JS 的 DOM 里能看到我的值 |

实测对照（同一个 `/dom` 页面）：

```
curl（服务器字节）        → href="#"
Edge --dump-dom（活体 DOM）→ href="javascript:alert(1)"
```

## 六、修复：白名单，不是转义

```python
if not value.startswith("/") or value.startswith("//") or ":" in value:
    value = "/blocked-by-safe"
```

三条都要卡：

- `:` → 挡掉 `javascript:`；
- 不以 `/` 开头 → 挡掉 `http://evil`；
- `//` 开头 → 挡掉 `//evil`；
- 还要注意浏览器把 `\` 也当 `/`（`/\evil` 等价于 `//evil`）。

**为什么不转义**：转义了 `:` 这个地址也就废了，正常的「返回」功能跟着坏；而且黑名单永远漏。正解是**只允许站内相对路径**。

## 七、我实际卡住的

我当时没搞清楚 JS 是在浏览器接收到网页源码之后才运行的，所以产生了「为什么 DOM 型更改的值明明也有展示的区域，查看源码却看不到改动」的疑问，询问后理解了。

## 八、我学到了什么（费曼）

今天学习了往 URL 格子里写东西做 XSS。URL 格子和属性格子的区别在于：URL 格子（比如 `href=""` 之间）在语义上只能是一个地址、需要有协议；而且这里是 DOM 赋值，属性格子那边是把值拼进 HTML 文本，两者不一样。关键点是 `javascript:` 这种协议，payload 里根本用不到 `<>` 和引号，过滤 `<>` 的检查也不看协议这一块。

## 环境说明

- 本地靶场 `href_demo.py` 只绑 `127.0.0.1:8084`，不对外；三个页面 `/server`（服务端原样拼）、`/dom`（死页面 + 页面 JS 改 href）、`/safe`（白名单对照）。
- `props_demo.html` 是前置知识示范页（元素属性读写、`URLSearchParams`、`||` 兜底、jQuery 对照、`document.domain`），用 `python3 -m http.server 8085` 打开。
- `verify.sh` 是自测脚本：断言「照步骤做时，预期现象真的会出现」（含用 Edge 无头浏览器验证 JS 真的改了 DOM）。
- 靶场**故意**含 XSS 缺陷，仅用于合法授权环境下的学习与自测，**请勿部署到公网或他人可访问的机器**。
