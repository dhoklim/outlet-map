"""도면 캔버스: 배경(도면 PNG 또는 placeholder)과 마커를 그리고 클릭을 처리한다."""
from __future__ import annotations

import os
import tkinter as tk

from models import Device, TYPE_OUTLET, summarize
import storage

MARKER_R = 9          # 마커 반지름(px)
HIT_RADIUS = 16       # 클릭 인식 거리(px)


class MapView(tk.Frame):
    def __init__(self, master, on_select, on_add, **kw):
        super().__init__(master, **kw)
        self.on_select = on_select        # 마커 선택 콜백(device)
        self.on_add = on_add              # 편집모드에서 추가 콜백(fx, fy)
        self.canvas = tk.Canvas(self, bg="#eef2f7", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.floor = None
        self.devices = []                 # 현재 층 기기
        self.evaluations = []
        self.selected_id = None
        self.edit_mode = False
        self._bg_image = None             # PhotoImage 참조 보관(GC 방지)
        self._hits = []                   # (device, px, py) 히트테스트용

        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self._on_click)

    # ---- 외부에서 호출 ----
    def show_floor(self, floor, devices, evaluations):
        self.floor = floor
        self.devices = devices
        self.evaluations = evaluations
        self.selected_id = None
        self.redraw()

    def set_evaluations(self, evaluations):
        self.evaluations = evaluations
        self.redraw()

    def set_edit_mode(self, on: bool):
        self.edit_mode = on
        self.canvas.config(cursor="tcross" if on else "")

    def select(self, device_id):
        self.selected_id = device_id
        self.redraw()

    # ---- 그리기 ----
    def redraw(self):
        c = self.canvas
        c.delete("all")
        w = c.winfo_width() or 600
        h = c.winfo_height() or 400
        self._draw_background(w, h)
        self._draw_markers(w, h)
        self._draw_legend()

    def _draw_background(self, w, h):
        img = self._load_image()
        if img is not None:
            self._bg_image = img
            self.canvas.create_image(w // 2, h // 2, image=img)
            return
        # 도면이 없으면 안내용 placeholder 평면도를 그린다.
        c = self.canvas
        c.create_rectangle(10, 10, w - 10, h - 10, outline="#9aa0a6", width=2)
        c.create_rectangle(20, h * 0.45, w - 20, h * 0.55, fill="#e3e8ef", outline="")
        for fx in (0.18, 0.38, 0.6, 0.82):
            c.create_rectangle(w * fx - 50, 30, w * fx + 50, h * 0.42,
                               fill="#f6f8fb", outline="#cdd4de")
        name = self.floor.name if self.floor else ""
        c.create_text(w / 2, h - 24, fill="#9aa0a6",
                      text=f"[{name}] 임시 도면 — 학교 도면 PNG를 넣으면 교체됩니다")

    def _load_image(self):
        if not self.floor or not self.floor.image_file:
            return None
        path = os.path.join(storage.IMAGES_DIR, self.floor.image_file)
        if not os.path.exists(path):
            return None
        try:
            return tk.PhotoImage(file=path)
        except Exception:
            return None  # Tk 8.5 등에서 PNG 미지원이면 placeholder로 대체

    def _draw_markers(self, w, h):
        self._hits = []
        for d in self.devices:
            px, py = d.x * w, d.y * h
            self._hits.append((d, px, py))
            color = summarize(d, self.evaluations).color
            selected = (d.device_id == self.selected_id)
            outline = "#1d1d1f" if selected else "#ffffff"
            width = 3 if selected else 1
            r = MARKER_R + (2 if selected else 0)
            if d.dtype == TYPE_OUTLET:   # 콘센트 = 원
                self.canvas.create_oval(px - r, py - r, px + r, py + r,
                                        fill=color, outline=outline, width=width)
            else:                         # 에어컨 = 사각형
                self.canvas.create_rectangle(px - r, py - r, px + r, py + r,
                                             fill=color, outline=outline, width=width)
            self.canvas.create_text(px, py + r + 9, text=d.name,
                                    font=("", 8), fill="#3d3d3f")

    def _draw_legend(self):
        items = [("사용가능", "#1f9d55"), ("고장", "#e02424"),
                 ("점유", "#ff9f1c"), ("미평가", "#9aa0a6")]
        x, y = 18, 18
        self.canvas.create_text(x, y, anchor="w", font=("", 8, "bold"),
                                fill="#3d3d3f", text="● 콘센트  ■ 에어컨")
        for i, (label, color) in enumerate(items):
            yy = y + 16 + i * 15
            self.canvas.create_oval(x, yy - 5, x + 10, yy + 5, fill=color, outline="")
            self.canvas.create_text(x + 16, yy, anchor="w", font=("", 8),
                                    fill="#3d3d3f", text=label)

    # ---- 클릭 ----
    def _on_click(self, event):
        w = self.canvas.winfo_width() or 1
        h = self.canvas.winfo_height() or 1
        if self.edit_mode:
            self.on_add(event.x / w, event.y / h)
            return
        nearest, best = None, HIT_RADIUS
        for d, px, py in self._hits:
            dist = ((event.x - px) ** 2 + (event.y - py) ** 2) ** 0.5
            if dist <= best:
                nearest, best = d, dist
        if nearest is not None:
            self.selected_id = nearest.device_id
            self.redraw()
            self.on_select(nearest)
