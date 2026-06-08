"""오른쪽 정보/평가 패널: 선택한 기기의 요약을 보여주고 새 평가를 입력받는다."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from models import STATUSES, STATUS_COLORS, validate_rating


def stars(avg) -> str:
    if avg is None:
        return "평가 없음"
    full = int(round(avg))
    return "★" * full + "☆" * (5 - full) + f"  ({avg})"


class DetailPanel(tk.Frame):
    def __init__(self, master, on_submit, **kw):
        super().__init__(master, width=240, **kw)
        self.on_submit = on_submit
        self.pack_propagate(False)
        self.device = None

        self.info = tk.Frame(self)
        self.info.pack(fill="x", padx=12, pady=(12, 6))

        tk.Frame(self, height=1, bg="#d1d1d6").pack(fill="x", padx=12, pady=6)

        self._build_form()
        self.show(None, None)

    # ---- 평가 입력 폼 (한 번만 생성) ----
    def _build_form(self):
        self.form = tk.Frame(self)
        self.form.pack(fill="x", padx=12, pady=6)

        tk.Label(self.form, text="이 기기 평가하기",
                 font=("", 11, "bold")).pack(anchor="w", pady=(0, 6))

        self.status_var = tk.StringVar(value=STATUSES[0])
        row = tk.Frame(self.form)
        row.pack(anchor="w")
        tk.Label(row, text="상태").pack(side="left")
        for s in STATUSES:
            tk.Radiobutton(row, text=s, value=s,
                           variable=self.status_var).pack(side="left")

        rrow = tk.Frame(self.form)
        rrow.pack(anchor="w", pady=4)
        tk.Label(rrow, text="별점").pack(side="left")
        self.rating_var = tk.IntVar(value=5)
        tk.Spinbox(rrow, from_=1, to=5, width=4,
                   textvariable=self.rating_var, state="readonly").pack(side="left")
        tk.Label(rrow, text="(1~5)").pack(side="left")

        tk.Label(self.form, text="한줄평").pack(anchor="w")
        self.comment_var = tk.StringVar()
        self.comment_entry = tk.Entry(self.form, textvariable=self.comment_var)
        self.comment_entry.pack(fill="x")

        self.save_btn = tk.Button(self.form, text="평가 등록", command=self._submit)
        self.save_btn.pack(anchor="e", pady=8)

    # ---- 선택된 기기 표시 ----
    def show(self, device, summary):
        self.device = device
        for w in self.info.winfo_children():
            w.destroy()

        if device is None:
            tk.Label(self.info, text="도면에서 마커를 클릭하세요",
                     fg="#86868b").pack(anchor="w")
            self._set_form_state("disabled")
            return

        self._set_form_state("normal")
        icon = "🔌" if device.dtype == "콘센트" else "❄️"
        tk.Label(self.info, text=f"{icon} {device.name}",
                 font=("", 13, "bold")).pack(anchor="w")
        tk.Label(self.info, text=device.dtype, fg="#86868b").pack(anchor="w")

        status = summary.latest_status or "미평가"
        color = STATUS_COLORS.get(summary.latest_status, STATUS_COLORS[None])
        tk.Label(self.info, text=f"● {status}", fg=color,
                 font=("", 11, "bold")).pack(anchor="w", pady=(6, 0))
        tk.Label(self.info, text=stars(summary.avg_rating)).pack(anchor="w")
        tk.Label(self.info, text=f"평가 {summary.count}건",
                 fg="#86868b").pack(anchor="w")

        if summary.recent:
            tk.Label(self.info, text="최근 한줄평", font=("", 10, "bold")
                     ).pack(anchor="w", pady=(8, 0))
            for e in summary.recent:
                if e.comment:
                    tk.Label(self.info, text=f"· {e.comment}", wraplength=210,
                             justify="left", fg="#3d3d3f").pack(anchor="w")

    def _set_form_state(self, state):
        for w in (self.save_btn, self.comment_entry):
            w.config(state=state)

    def _submit(self):
        if self.device is None:
            return
        try:
            rating = validate_rating(self.rating_var.get())
        except ValueError as e:
            messagebox.showwarning("입력 오류", str(e))
            return
        self.on_submit(self.device.device_id, self.status_var.get(),
                       rating, self.comment_var.get().strip())
        self.comment_var.set("")
