#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 27 玩具靶场：URL 格子（href 属性 + javascript: 协议）
仅绑定 127.0.0.1，故意包含 XSS 缺陷，只用于本机学习。

用法：
    cd ~/day27 && python3 href_demo.py
    浏览器打开 http://127.0.0.1:8084/

三个页面：
    /server?returnPath=...   服务端把参数原样拼进 <a href="...">  —— 反射型、可见于 Ctrl+U
    /dom?returnPath=...      服务端发死页面，页面 JS 运行时改 href   —— DOM 型、Ctrl+U 搜不到
    /safe?returnPath=...     服务端做了白名单校验（修复对照）
"""
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8084

STYLE = """body{font-family:system-ui,sans-serif;max-width:48em;margin:2em auto;
line-height:1.8;color:#222} code{background:#f0f0f0;padding:1px 5px;border-radius:3px}
pre{background:#f7f7f7;border:1px solid #ddd;padding:10px;overflow-x:auto}
a{color:#0a58ca} .dim{color:#888;font-size:.9em}"""

# 服务端直接拼（/server 与 /safe 共用）
SERVER_PAGE = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>day27 · {mode}</title>
<style>{style}</style></head>
<body>
<h2>{mode} · URL 格子演练</h2>
<p>「返回首页」这个链接的地址，来自你 URL 里的 <code>returnPath</code> 参数。</p>
<p><a id="back" {attr}>← 返回首页</a> <span class="dim">（要真的点它一下）</span></p>
<p>服务器这次发出去的 HTML 就是这一行：</p>
<pre>{raw}</pre>
<p>你送进来的 <code>returnPath</code> = <code>{shown}</code></p>
{extra}
</body></html>
"""

# 服务端发死页面（/dom）：跟 query 完全无关
DOM_PAGE = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>day27 · dom</title>
<style>{style}</style></head>
<body>
<h2>dom · URL 格子演练（DOM 型）</h2>
<p>「返回首页」这个链接在服务器发出来的页面里 href 是空的，是页面自己的 JS 运行时改的。</p>
<p><a id="back" href="#">← 返回首页</a> <span class="dim">（要真的点它一下）</span></p>
<p>服务器这次发出去的 HTML（跟你传什么都不变）：</p>
<pre>{raw}</pre>
<p>打开 <b>F12 → Console</b>，敲 <code>document.getElementById('back').href</code> 看当前值。</p>
<p class="dim">注意：这一页的源码里有一段 &lt;script&gt;，它从地址栏读 <code>returnPath</code>、
再写进上面那个 a 的 href —— 但源码里<b>没有你的值</b>。</p>
{script}
</body></html>
"""

DOM_SCRIPT = """<script>
  // 1. location.search  = 地址栏 ? 及后面那整截
  // 2. URLSearchParams  = 浏览器自带的“查询串解析器”，把 a=1&b=2 变成可查询的键值表
  var q = new URLSearchParams(window.location.search);
  // 3. .get("returnPath") 取这个键的值；没传就用 "/" 兜底
  var p = q.get("returnPath") || "/";
  // 4. 把这个值塞进 a 标签的 href 属性（sink）
  document.getElementById("back").href = p;
</script>"""

INDEX_PAGE = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>day27 靶场</title>
<style>{style}</style></head>
<body>
<h2>Day 27 玩具靶场 · URL 格子</h2>
<ol>
  <li><a href="/server?returnPath=/">/server?returnPath=</a> —— 服务端原样拼进 href</li>
  <li><a href="/dom?returnPath=/">/dom?returnPath=</a> —— 页面 JS 运行时改 href</li>
  <li><a href="/safe?returnPath=/">/safe?returnPath=</a> —— 服务端白名单（修复对照）</li>
</ol>
<p class="dim">换成你的 payload 再打开。只在本机玩。</p>
</body></html>
"""


def safe_scheme(value: str) -> str:
    """最朴素的修复：只放行站内相对路径，别的 scheme 一律丢掉。"""
    if not value.startswith("/") or value.startswith("//"):
        return "/blocked-by-safe"
    if ":" in value:
        return "/blocked-by-safe"
    return value


class Handler(BaseHTTPRequestHandler):
    server_version = "day27-demo/1.0"

    def _send(self, body: str, code: int = 200) -> None:
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query, keep_blank_values=True)
        value = qs.get("returnPath", [""])[0]

        if path in ("/", "/index.html"):
            self._send(INDEX_PAGE.format(style=STYLE))
            return

        if path == "/server":
            raw_line = '<a id="back" href="%s">← 返回首页</a>' % value
            self._send(SERVER_PAGE.format(
                mode="server", style=STYLE, attr='href="%s"' % value,
                raw=html.escape(raw_line), shown=html.escape(value or "(没传)"),
                extra='<p class="dim">这一页没有任何编码，也没有任何校验。</p>',
            ))
            return

        if path == "/dom":
            # 服务器发的是死页面：这段字节跟你传什么完全无关
            dom_source = '<a id="back" href="#">← 返回首页</a>\n\n' + DOM_SCRIPT
            self._send(DOM_PAGE.format(style=STYLE, raw=html.escape(dom_source),
                                       script=DOM_SCRIPT))
            return

        if path == "/safe":
            fixed = safe_scheme(value)
            raw_line = '<a id="back" href="%s">← 返回首页</a>' % fixed
            self._send(SERVER_PAGE.format(
                mode="safe", style=STYLE, attr='href="%s"' % fixed,
                raw=html.escape(raw_line), shown=html.escape(value or "(没传)"),
                extra='<p class="dim">服务端只放行以 / 开头的站内路径，'
                      '带 : 或 // 的一律换成 <code>/blocked-by-safe</code>。</p>',
            ))
            return

        self._send("<h1>404</h1><p>只有 / /server /dom /safe</p>", 404)

    def log_message(self, fmt: str, *args) -> None:
        print("[%s] %s" % (self.address_string(), fmt % args), flush=True)


def main() -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("day27 靶场已启动: http://127.0.0.1:%d/" % PORT, flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
