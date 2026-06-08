#!/bin/bash
# Finder에서 더블클릭하면 웹 데모 서버가 실행되고 브라우저가 열립니다.
cd "$(dirname "$0")"

for PY in /opt/homebrew/bin/python3.14 /opt/homebrew/bin/python3 python3; do
  if command -v "$PY" >/dev/null 2>&1; then
    ( sleep 1; open "http://localhost:8000" ) &
    exec "$PY" web_server.py
  fi
done

echo "python3 를 찾지 못했습니다."
read -r -p "엔터를 누르면 닫힙니다..."
