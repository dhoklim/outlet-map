"""콘센트맵 — 학교 건물의 콘센트/전자기기 위치 안내 및 사용 평가 (데모).

실행:  /usr/bin/python3 main.py   (tkinter 포함 Python 필요)
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import storage
from models import DEVICE_TYPES, summarize
from map_view import MapView
from detail_panel import DetailPanel


class AddDeviceDialog(tk.Toplevel):
    """편집 모드에서 도면을 클릭했을 때 종류/이름을 입력받는 작은 창."""

    def __init__(self, master, fx, fy):
        super().__init__(master)
        self.title("기기 추가")
        self.resizable(False, False)
        self.result = None
        self.fx, self.fy = fx, fy

        tk.Label(self, text="새 기기 등록", font=("", 12, "bold")).pack(
            padx=16, pady=(14, 8))
        self.type_var = tk.StringVar(value=DEVICE_TYPES[0])
        row = tk.Frame(self)
        row.pack(padx=16, anchor="w")
        for t in DEVICE_TYPES:
            tk.Radiobutton(row, text=t, value=t,
                           variable=self.type_var).pack(side="left")

        tk.Label(self, text="이름").pack(padx=16, anchor="w")
        self.name_var = tk.StringVar()
        entry = tk.Entry(self, textvariable=self.name_var, width=24)
        entry.pack(padx=16)
        entry.focus_set()

        btns = tk.Frame(self)
        btns.pack(padx=16, pady=12)
        tk.Button(btns, text="저장", command=self._ok).pack(side="left", padx=4)
        tk.Button(btns, text="취소", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Return>", lambda e: self._ok())

        self.transient(master)
        self.grab_set()

    def _ok(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("입력 오류", "이름을 입력하세요.", parent=self)
            return
        self.result = (self.type_var.get(), name, self.fx, self.fy)
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("콘센트맵 — 콘센트·전자기기 위치 안내 및 평가")
        self.geometry("900x560")

        storage.ensure_data_files()
        self.floors = storage.load_floors()
        self.devices = storage.load_devices()
        self.evaluations = storage.load_evaluations()
        self.current_floor = self.floors[0] if self.floors else None

        self._build_topbar()

        body = tk.Frame(self)
        body.pack(fill="both", expand=True)
        self.map_view = MapView(body, on_select=self._on_select, on_add=self._on_add)
        self.map_view.pack(side="left", fill="both", expand=True)
        self.panel = DetailPanel(body, on_submit=self._on_submit)
        self.panel.pack(side="right", fill="y")

        self._show_current_floor()

    # ---- 상단 바 ----
    def _build_topbar(self):
        bar = tk.Frame(self, bg="#f5f5f7")
        bar.pack(fill="x")

        self.floor_btns = {}
        for fl in self.floors:
            b = tk.Button(bar, text=fl.name,
                          command=lambda f=fl: self.select_floor(f))
            b.pack(side="left", padx=2, pady=6)
            self.floor_btns[fl.floor_id] = b

        tk.Frame(bar, width=16, bg="#f5f5f7").pack(side="left")
        self.search_var = tk.StringVar()
        e = tk.Entry(bar, textvariable=self.search_var, width=16)
        e.pack(side="left", pady=6)
        e.bind("<Return>", lambda ev: self._do_search())
        tk.Button(bar, text="찾기", command=self._do_search).pack(side="left", padx=4)

        self.edit_var = tk.BooleanVar(value=False)
        tk.Checkbutton(bar, text="편집 모드(도면 클릭→기기 추가)",
                       variable=self.edit_var, bg="#f5f5f7",
                       command=self._toggle_edit).pack(side="right", padx=8)

    # ---- 층 전환 ----
    def select_floor(self, floor):
        self.current_floor = floor
        self._show_current_floor()

    def _show_current_floor(self):
        for fid, btn in self.floor_btns.items():
            btn.config(relief="sunken" if self.current_floor and
                       fid == self.current_floor.floor_id else "raised")
        self.map_view.show_floor(self.current_floor,
                                 self._devices_here(), self.evaluations)
        self.panel.show(None, None)

    def _devices_here(self):
        if not self.current_floor:
            return []
        return [d for d in self.devices
                if d.floor_id == self.current_floor.floor_id]

    # ---- 콜백 ----
    def _on_select(self, device):
        self.panel.show(device, summarize(device, self.evaluations))

    def _on_submit(self, device_id, status, rating, comment):
        storage.add_evaluation(device_id, status, rating, comment)
        self.evaluations = storage.load_evaluations()
        self.map_view.set_evaluations(self.evaluations)
        device = next((d for d in self.devices if d.device_id == device_id), None)
        if device:
            self.map_view.select(device_id)
            self.panel.show(device, summarize(device, self.evaluations))
        messagebox.showinfo("등록 완료", "평가가 등록되었습니다.")

    def _on_add(self, fx, fy):
        if not self.current_floor:
            return
        dlg = AddDeviceDialog(self, fx, fy)
        self.wait_window(dlg)
        if not dlg.result:
            return
        dtype, name, x, y = dlg.result
        storage.add_device(self.current_floor.floor_id, dtype, name, x, y)
        self.devices = storage.load_devices()
        self.map_view.show_floor(self.current_floor,
                                 self._devices_here(), self.evaluations)

    def _do_search(self):
        q = self.search_var.get().strip()
        if not q:
            return
        for d in self._devices_here():
            if q in d.name:
                self.map_view.select(d.device_id)
                self._on_select(d)
                return
        messagebox.showinfo("검색", f"'{q}' 와(과) 일치하는 기기가 이 층에 없습니다.")

    def _toggle_edit(self):
        self.map_view.set_edit_mode(self.edit_var.get())


if __name__ == "__main__":
    App().mainloop()
