#!/usr/bin/env bash
# Day 27 靶场自测：断言「学生照着步骤做时，预期的现象真的会出现」
# 用法：bash /mnt/c/Users/qzl20/.qwenpaw/workspaces/websec_coach/lab/day27/verify.sh
set -u
EDGE="/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
# 脚本所在目录（放在 ~/day27 或仓库 day27/ 都能跑）
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || { echo "找不到 $DIR"; exit 1; }

pkill -f href_demo.py 2>/dev/null
sleep 0.3
python3 href_demo.py >/tmp/h27_verify.log 2>&1 &
sleep 1.5

fail=0
chk() { # 名称 期望 实际
  if [ "$2" = "$3" ]; then
    echo "PASS  $1"
  else
    echo "FAIL  $1"
    echo "      期望: [$2]"
    echo "      实际: [$3]"
    fail=1
  fi
}

# 1) 反射型：服务端原样拼，值必须出现在响应里
got=$(curl -s 'http://127.0.0.1:8084/server?returnPath=javascript:alert(1)' | grep -o 'id="back"[^>]*')
chk "1 /server 原样落地" 'id="back" href="javascript:alert(1)"' "$got"

# 2) DOM 型：响应里不能出现标记值
got=$(curl -s 'http://127.0.0.1:8084/dom?returnPath=MARKER123' | grep -c MARKER123)
chk "2 /dom 响应不含标记值" '0' "$got"

# 3) DOM 型：两次不同输入，响应字节必须完全相同
a=$(curl -s 'http://127.0.0.1:8084/dom?returnPath=AAA' | md5sum | cut -d' ' -f1)
b=$(curl -s 'http://127.0.0.1:8084/dom?returnPath=BBB' | md5sum | cut -d' ' -f1)
chk "3 /dom 输出与输入无关（md5 相同）" "$a" "$b"

# 4) 关键：用真浏览器跑一遍，证明页面 JS 真的把值塞进了 href（这条以前从没验过）
if [ -x "$EDGE" ]; then
  "$EDGE" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=3000 \
    --dump-dom 'http://127.0.0.1:8084/dom?returnPath=javascript:alert(1)' \
    2>/dev/null > /tmp/d_dom.html
  got=$(grep -o 'id="back"[^>]*' /tmp/d_dom.html | head -1)
  chk "4 /dom 浏览器渲染后 href 被 JS 改写" 'id="back" href="javascript:alert(1)"' "$got"
else
  echo "SKIP  4 未找到 Edge，跳过浏览器验证"
fi

# 5) 修复对照：白名单必须拦下来
got=$(curl -s 'http://127.0.0.1:8084/safe?returnPath=javascript:alert(1)' | grep -o 'id="back"[^>]*')
chk "5 /safe 白名单拦截" 'id="back" href="/blocked-by-safe"' "$got"

pkill -f href_demo.py 2>/dev/null
if [ "$fail" -eq 0 ]; then echo "===== 全部通过 ====="; else echo "===== 有失败项 ====="; fi
exit "$fail"
