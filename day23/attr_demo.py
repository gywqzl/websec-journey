#!/usr/bin/env python3
# Day 23 教学用「玩具靶场」：同一份输入，扔进两种格子，看它两种命运。
# 跑法：  python3 attr_demo.py
# 然后：  curl -s "http://localhost:8081/?q=hello"
#
# 说明（逐行）：
#   · 这个服务只干一件事：把 ?q= 后面的东西，原样拼进下面这份 HTML。
#   · 默认**不编码**（等于 Day 21/22 的 "nothing encoded"）。
#   · URL 后面加 &encode=1，就切换到「服务端输出编码」，可以看它怎么把 payload 掐死。

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import html

PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>attr demo</title></head>
<body>
<h2>格子 A：标签之间</h2>
<p>你搜索的是：{between}</p>

<h2>格子 B：属性值里面</h2>
<input type="text" value="{attr}" size="80">

</body></html>
"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)          # 把 /?q=xxx&encode=1 拆成 路径 + 查询串
        params = parse_qs(u.query)       # 查询串变成字典 {'q': ['xxx'], 'encode': ['1']}
        q = params.get("q", [""])[0]     # 取 q 的第一个值；没有就空串
        if params.get("encode"):         # 带 &encode=1 = 开启"输出编码"
            q = html.escape(q, quote=True)   # & < > " → &amp; &lt; &gt; &quot;

        body = PAGE.format(between=q, attr=q)   # 原样拼进两种格子
        data = body.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print("[请求]", self.path)       # 把每个请求打到终端，方便对照


print("attr_demo 已启动 → http://localhost:8081/")
HTTPServer(("0.0.0.0", 8081), H).serve_forever()
