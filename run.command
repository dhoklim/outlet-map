#!/bin/bash
# Finder에서 더블클릭하면 콘센트맵이 실행됩니다.
cd "$(dirname "$0")"

# tkinter가 되는 파이썬을 찾는다.
for PY in /opt/homebrew/bin/python3.14 /opt/homebrew/bin/python3 python3; do
  if "$PY" -c "import tkinter" >/dev/null 2>&1; then
    exec "$PY" main.py
  fi
done

echo "tkinter가 있는 파이썬을 찾지 못했습니다."
echo "먼저  brew install python-tk@3.14  를 실행하세요."
read -r -p "엔터를 누르면 닫힙니다..."
