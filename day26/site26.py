#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内部便签站 —— Day 26 实战任务卡的练习靶场（本地学习用）

启动：  python3 site26.py
访问：  http://127.0.0.1:8090/

⚠️ 只监听 127.0.0.1，仅供本地练习，请勿部署到公网或他人机器。
"""

import html
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8090
NOTES = []          # 留言板数据：(title, content) —— 存在内存里，重启即清空

LAYOUT = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>Internal Notes</title>
<style>
  body { font-family: sans-serif; max-width: 760px; margin: 40px auto; line-height: 1.7; }
  .note { border: 1px solid #ccc; padding: 8px; margin: 8px 0; }
  input, textarea { width: 100%; padding: 4px; margin: 3px 0; }
  small { color: #777; }
</style>
</head>
<body>
<p><a href="/">首页</a> ·
   <a href="/search?q=abc">搜索</a> ·
   <a href="/profile?name=guest">我的资料</a> ·
   <a href="/feedback?msg=hello">反馈</a> ·
   <a href="/note">留言板</a> ·
   <a href="/dashboard">控制台</a></p>
<hr>
__BODY__
</body>
</html>"""


def page(body):
    return LAYOUT.replace("__BODY__", body)


class Handler(BaseHTTPRequestHandler):
    server_version = "Notes/1.0"

    # ---------- 工具 ----------
    def _send(self, body, status=200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ---------- GET ----------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            body = ("<h2>内部便签站</h2>"
                    "<p>一个给我们小组内部用的小站：搜索、资料、反馈、留言板、控制台。</p>"
                    "<p><small>当前版本 v1.0</small></p>")
            self._send(page(body))

        elif path == "/search":
            q = qs.get("q", [""])[0]
            body = ("<h2>Search results for '" + q + "'</h2>"
                    "<p>没有找到相关记录。</p>")
            self._send(page(body))

        elif path == "/profile":
            name = qs.get("name", ["guest"])[0]
            shown = html.escape(name, quote=False)          # 只处理 & < >
            body = ("<h2>我的资料</h2>"
                    "<p>昵称：<input type='text' value='" + shown + "' readonly></p>"
                    "<p>角色：普通用户</p>")
            self._send(page(body))

        elif path == "/feedback":
            msg = qs.get("msg", [""])[0]
            shown = msg.replace("\\", "\\\\").replace("'", "\\'")
            body = ("<h2>反馈</h2>"
                    "<p>请把意见写在链接的 msg 参数里（内测简化版）。</p>"
                    "<div id='out'></div>"
                    "<script>"
                    "var msg = '" + shown + "';"
                    "document.getElementById('out').innerHTML = '感谢反馈：' + msg;"
                    "</script>")
            self._send(page(body))

        elif path == "/note":
            items = ""
            for title, content in NOTES:
                items += ("<div class='note'>"
                          "<a href='#' title='" + html.escape(title, quote=True) + "'>"
                          + content +
                          "</a>"
                          "<br><small>标题：" + html.escape(title, quote=True) + "</small>"
                          "</div>")
            if not items:
                items = "<p><small>还没有留言。</small></p>"
            form = """
<h2>留言板</h2>
<form method="post" action="/note" onsubmit="return checkForm();">
  <input name="title" placeholder="标题（20 字以内）" maxlength="20">
  <textarea name="content" placeholder="内容（100 字以内）" maxlength="100" rows="3"></textarea>
  <button type="submit">发布</button>
</form>
<script>
function checkForm() {
  var c = document.querySelector('textarea[name=content]').value;
  if (c.indexOf('<') >= 0) { alert('内容不能包含 <'); return false; }
  return true;
}
</script>
"""
            self._send(page(form + "<hr>" + items))

        elif path == "/dashboard":
            body = """
<h2>控制台</h2>
<p>当前视角：<b id="view">默认</b></p>
<div id="out">（无内容）</div>
<script>
window.onload = function () {
  var h = location.hash.slice(1);
  if (h.length > 0) {
    document.getElementById('view').textContent = '自定义视角';
    document.getElementById('out').innerHTML = decodeURIComponent(h);
  }
};
</script>
"""
            self._send(page(body))

        else:
            self._send(page("<h2>404</h2><p>页面不存在。</p>"), 404)

    # ---------- POST ----------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/note":
            self._send(page("<h2>404</h2><p>页面不存在。</p>"), 404)
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8", "replace")
        data = urllib.parse.parse_qs(raw)
        title = data.get("title", [""])[0]
        content = data.get("content", [""])[0]

        NOTES.append((title, content))
        self.send_response(303)
        self.send_header("Location", "/note")
        self.end_headers()


if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", PORT), Handler)
    print("内部便签站已启动： http://127.0.0.1:%d/" % PORT)
    print("按 Ctrl+C 停止。")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
