#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Day 24 靶场：JavaScript 字符串上下文
--------------------------------------------------
模仿 PortSwigger lab:
  "Reflected XSS into a JavaScript string with single quote and backslash escaped"

服务器的错误防护：只把  '  ->  \'   和   \  ->  \\    （别的什么都不处理）
也就是：< > " 原样落地，单引号和反斜杠被"加盾牌"。

启动：python3 ~/day24/js_demo.py
访问：http://localhost:8082/js?q=hello
对照：http://localhost:8082/js?q=hello&raw=1   （raw=1 = 关掉转义，裸奔对照组）
"""

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8082

PAGE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>JS string context</title></head>
<body>
<h1>搜索一下</h1>
<form action="/js" method="GET">
  <input type="text" name="q" placeholder="input keyword">
  <button type="submit">搜索</button>
</form>
<p>页面回显（这一格是 HTML 编码过的）：<b>__SHOWN__</b></p>
<hr>
<script>
var searchTerms = '__JS__';
document.write('<img src="/tracker.gif?q=' + searchTerms + '">');
</script>
</body>
</html>
"""


def js_escape(s):
    """模仿服务端的错误防护：先给反斜杠加盾，再给单引号加盾。
    顺序很重要：反斜杠必须先处理，否则新加的盾也会被再加一层。
    """
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    return s


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)
        if u.path != "/js":
            self.send_error(404, "only /js exists")
            return

        qs = parse_qs(u.query, keep_blank_values=True)
        q = qs.get("q", [""])[0]
        raw = qs.get("raw", ["0"])[0] == "1"

        js_value = q if raw else js_escape(q)
        html = PAGE.replace("__SHOWN__", escape(q)).replace("__JS__", js_value)

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print("[log] %s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    print("Day 24 靶场启动，端口 %d" % PORT)
    print("  正常站（单引号/反斜杠被转义）：http://localhost:%d/js?q=hello" % PORT)
    print("  裸奔对照（什么都不转义）  ：http://localhost:%d/js?q=hello&raw=1" % PORT)
    print("  Ctrl+C 停止")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
