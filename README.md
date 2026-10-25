# Web 安全学习记录（websec-journey）

我在系统学习 Web 安全 / 漏洞挖掘过程中的全部脚本、笔记与练习记录。

## 我在学什么

Linux → 计算机网络 → HTTP → Web 基础（HTML/JS）→ Python → Web 漏洞 → 合法授权范围内的漏洞挖掘

**方向**：Web 安全 / 应用安全（渗透测试、漏洞挖掘）

## 目录导航

| 目录 | 内容 |
|---|---|
| [`day18/`](day18/) | 字典爆破目录扫描脚本（Python + urllib） |
| [`day19/`](day19/) | Python POST 登录 + 会话保持（CookieJar） |
| [`day20/`](day20/) | 本地靶场（LAMP + DVWA）+ 反射型 XSS |
| [`day21/`](day21/) | PortSwigger 官方靶场（第一个 lab：反射型 XSS） |
| [`day22/`](day22/) | 存储型 XSS（Stored XSS）：DVWA + PortSwigger lab |
| [`day23/`](day23/) | 属性上下文 XSS：不用标签，靠属性注入（PortSwigger） |
| [`day24/`](day24/) | JS 字符串上下文 XSS：转义绕不过去就掀桌子（PortSwigger） |
| [`day25/`](day25/) | DOM 型 XSS：服务器从没见过你的 payload（PortSwigger） |
| [`day26/`](day26/) | 实战任务卡：给自建便签站做 XSS 审计（Day 16–25 综合） |
| [`day27/`](day27/) | URL 格子：javascript: 协议 + jQuery href sink（PortSwigger） |

## 学习进度

| Day | 主题 | 产物 |
|---|---|---|
| 18 | 字典文件 + 目录爆破雏形 | [`day18/dirscan.py`](day18/dirscan.py) |
| 19 | Python 发带数据的请求 + 会话（CookieJar） | [`day19/login19.py`](day19/login19.py) |
| 20 | 本地靶场（LAMP/DVWA）+ 反射型 XSS | [`day20/README.md`](day20/README.md) |
| 21 | PortSwigger 官方靶场：第一个 lab（反射型 XSS，未编码） | [`day21/README.md`](day21/README.md) |
| 22 | 存储型 XSS（Stored XSS）+ 逐字段试 | [`day22/README.md`](day22/README.md) |
| 23 | 属性上下文 XSS（attribute context）+ 事件属性 / autofocus | [`day23/README.md`](day23/README.md) |
| 24 | JavaScript 字符串上下文 XSS + 转义符吃掉模型与 </script> 出口 | [`day24/README.md`](day24/README.md) |
| 25 | DOM 型 XSS + source/sink 与 document.write 传送门 | [`day25/README.md`](day25/README.md) |
| 26 | 第四次实战任务卡：五格上下文 + 证据链 + 审计报告 | [`day26/README.md`](day26/README.md) |
| 27 | URL 格子（href / javascript:）+ DOM 赋值 vs HTML 解析器 + 源码/活体 DOM 两视图 | [`day27/README.md`](day27/README.md) |

（以后每学完一天，就在这里加一行）

## 合规声明

本仓库所有脚本仅用于个人实验环境与已获授权的靶场（如 PortSwigger Web Security Academy），
所有练习目标均为本地搭建。未经授权测试他人系统是违法行为，本仓库不包含任何此类内容。
