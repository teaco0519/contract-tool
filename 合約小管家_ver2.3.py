# -*- coding: utf-8 -*-
# 🌸 合約小管家 v2.3 — 現代化響應式介面 × 奶油粉配色 × 頂部裝飾圖片 🌸
# --------------------------------------------------
# 打包成 exe：
#     pip install auto-to-py-exe
#     auto-to-py-exe
# 如需支援 JPG/JPEG/WEBP 等圖片格式，建議：
#     pip install Pillow
# --------------------------------------------------
# ver2.3 - 改變卡片檢視位置到右上角

import json
import os
import sys
import uuid
import shutil
import csv
import webbrowser
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta

# ── 可選：Pillow（支援更多圖片格式與縮放） ──
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
    try:
        _LANCZOS = Image.Resampling.LANCZOS
    except AttributeError:
        _LANCZOS = Image.LANCZOS
except Exception:
    HAS_PIL = False
    _LANCZOS = None

APP_TITLE = "🌸 合約小管家｜ContractFlow 🌸"
APP_VER = "2.3.0"
DATA_LOAD_FAILED = False

# ── 頂部標題列尺寸（集中管理，方便調整） ──
HEADER_BASE_HEIGHT  = 110   # 標題列預設高度
HEADER_IMG_MAX_H    = 94    # 裝飾圖片最大高度
HEADER_IMG_MAX_W    = 1400  # 單張裝飾圖片最大寬度
HEADER_IMG_MAX_W_DUAL = 700 # 兩張並排時，每張最大寬度


# ══════════════════════════════════════════════
#  資料路徑
# ══════════════════════════════════════════════
def data_dir():
    override = os.environ.get("CONTRACTFLOW_DATA_DIR", "").strip()
    d = os.path.abspath(os.path.expanduser(override)) if override else os.path.join(os.path.expanduser("~"), "ContractFlow")
    os.makedirs(d, exist_ok=True)
    return d


def data_file():
    return os.path.join(data_dir(), "data.json")


def backup_dir():
    d = os.path.join(data_dir(), "backup")
    os.makedirs(d, exist_ok=True)
    return d


def letter_dir():
    d = os.path.join(data_dir(), "letters")
    os.makedirs(d, exist_ok=True)
    return d


def decor_dir():
    """放頂部裝飾圖片的地方。"""
    d = os.path.join(data_dir(), "decor")
    os.makedirs(d, exist_ok=True)
    return d


# ══════════════════════════════════════════════
#  配色（沿用 v1.2 的柔和奶油粉色系）
# ══════════════════════════════════════════════
C_BG          = "#FFF8F4"
C_SURFACE     = "#FFFEFD"
C_SURFACE_2   = "#FDF8F3"
C_SURFACE_3   = "#FCE9EF"
C_BORDER      = "#EFCBD5"
C_BORDER_2    = "#E5C4D0"

C_TEXT        = "#3B3B4F"
C_TEXT_2      = "#6E6E85"
C_TEXT_3      = "#9B93A5"

C_PRIMARY     = "#D96F91"
C_PRIMARY_D   = "#B94F75"
C_PRIMARY_L   = "#FDE7ED"
C_PRIMARY_XL  = "#FDF2F6"

C_INFO_L      = "#DCEEFB"
C_INFO_D      = "#3A6EA5"

C_SUCCESS_L   = "#DFF5E8"
C_SUCCESS_D   = "#2E6B4F"

C_WARNING_L   = "#FFF6D6"
C_WARNING_D   = "#8B6914"

C_DANGER_L    = "#FFDCDC"
C_DANGER_D    = "#8B3A3A"

C_PURPLE_L    = "#EDE7F6"
C_PURPLE_D    = "#6B4A9E"

C_GRAY_L      = "#EFEFF3"
C_GRAY_D      = "#6E6E85"

C_CREAM       = "#FFFDF8"
C_SHADOW      = "#E8D5DC"

C_HEADER      = "#F8C6D4"


# ══════════════════════════════════════════════
#  階段定義
# ══════════════════════════════════════════════
STAGES = [
    ("received",     "🆕 待檢查",         "#FFF0F4"),
    ("rejected",     "🚫 已退件",         "#FFE4E4"),
    ("to_leader",    "📮 待送組長",       "#FFFBEA"),
    ("leader_back",  "↩️ 組長退回",       "#FFE4E4"),
    ("signing",      "✍️ 組長簽核中",     "#EAF5FF"),
    ("to_vp",        "👔 待送件",         "#F2EDFF"),
    ("printing",     "📩 送印中",         "#EAFBF1"),
    ("returned",     "📬 已回件",         "#E6F8EE"),
    ("registered",   "📝 已登記",         "#E8F0FF"),
    ("notify",       "📦 待通知/寄送",    "#FFF6E5"),
    ("nns_pending",  "💾 需NNS登記",     "#F0E6FF"),
    ("done",         "✅ 已結案",         "#F0F0F4"),
]
STAGE_MAP = {k: (n, c) for k, n, c in STAGES}
STAGE_ORDER = [k for k, _, _ in STAGES]

FORWARD = {
    "received":    "to_leader",
    "to_leader":   "signing",
    "signing":     "to_vp",
    "to_vp":       "printing",
    "printing":    "returned",
    "returned":    "registered",
    "registered":  "notify",
    "notify":      "nns_pending",
    "nns_pending": "done",
}

DOC_TYPES = ["新合約", "補充協議書", "修正合約", "續約", "其他"]
REGIONS = ["北區", "中區", "南區", "其他"]
NNS_KINDS = ["新合約登記", "資料變更"]

DEFAULT_LETTER_TPL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>封面函</title>
<style>
  body{font-family:"Microsoft JhengHei","PingFang TC",sans-serif;
       color:#3B3B4F;padding:48px;line-height:1.7;}
  h1{font-size:22px;text-align:center;letter-spacing:6px;margin-bottom:6px;}
  .sub{text-align:center;color:#6E6E85;font-size:13px;margin-bottom:28px;}
  table{border-collapse:collapse;margin:0 auto;min-width:520px;}
  td{border:1px solid #E5C4D0;padding:10px 18px;font-size:15px;}
  td.k{background:#FDE7ED;font-weight:bold;width:130px;text-align:center;}
  .foot{margin-top:34px;text-align:center;color:#6E6E85;font-size:13px;}
</style></head><body>
<h1>封 面 函</h1>
<div class="sub">Contract Cover Letter</div>
<table>
  <tr><td class="k">函　　號</td><td>{letter_no}</td></tr>
  <tr><td class="k">客戶代碼</td><td>{customer_code}</td></tr>
  <tr><td class="k">客戶名稱</td><td>{customer_name}</td></tr>
  <tr><td class="k">業務姓名</td><td>{sales}</td></tr>
  <tr><td class="k">隨函附件</td><td>{items}</td></tr>
  <tr><td class="k">日　　期</td><td>{date}</td></tr>
</table>
<div class="foot">此為系統自動產生之封面函，請連同附件一併歸還業務。</div>
</body></html>"""


# ══════════════════════════════════════════════
#  小工具
# ══════════════════════════════════════════════
def today_str():
    return date.today().strftime("%Y-%m-%d")


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def parse_dt(s):
    if not s:
        return "", ""
    s = str(s).strip()
    if " " in s:
        parts = s.split(" ", 1)
        return parts[0], parts[1]
    return s, ""


def shift_date(s, n):
    try:
        d = datetime.strptime(str(s), "%Y-%m-%d").date()
    except Exception:
        d = date.today()
    return (d + timedelta(days=n)).strftime("%Y-%m-%d")


def pick_font():
    try:
        fams = set(tkfont.families())
    except Exception:
        fams = set()
    for f in ("Microsoft JhengHei UI", "Microsoft JhengHei",
              "PingFang TC", "Noto Sans TC", "Arial Unicode MS"):
        if f in fams:
            return f
    return "TkDefaultFont"


def make_scrollable(parent, bg=C_BG):
    canvas = tk.Canvas(parent, bg=bg, highlightthickness=0, bd=0)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>",
                lambda e: canvas.itemconfig(win_id, width=e.width))

    def _on_wheel(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_wheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    return canvas, inner


def default_data():
    return {
        "version": APP_VER,
        "settings": {
            "cutoff": "15:30",
            "mail_times": "10:00, 14:00",
            "letter_tpl": DEFAULT_LETTER_TPL,
            "serial": 0,
            "letter_serial": 0,
            "ui_scale": 1.0,
            "header_image": "",
            "header_image_2": "",
        },
        "contracts": [],
        "nns": [],
        "memos": [],
        "log": [],
    }


def load_data():
    global DATA_LOAD_FAILED
    DATA_LOAD_FAILED = False
    p = data_file()
    if not os.path.exists(p):
        return default_data()
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict):
            raise ValueError("資料檔最外層格式應為 JSON 物件。")
        base = default_data()
        for k, v in base.items():
            d.setdefault(k, v)
        if not isinstance(d.get("settings"), dict):
            raise ValueError("settings 欄位格式錯誤，應為物件。")
        for k, v in base["settings"].items():
            d["settings"].setdefault(k, v)
        for key in ("contracts", "nns", "memos", "log"):
            if not isinstance(d.get(key), list):
                raise ValueError("%s 欄位格式錯誤，應為清單。" % key)
        return d
    except Exception as e:
        DATA_LOAD_FAILED = True
        try:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            damaged_copy = os.path.join(backup_dir(), "data_corrupt_%s.json" % stamp)
            shutil.copy2(p, damaged_copy)
        except Exception:
            damaged_copy = "（自動備份失敗，請勿刪除原始資料檔）"
        messagebox.showerror(
            "資料讀取失敗｜已啟用安全模式",
            "無法正常讀取資料檔：\n%s\n\n原始檔已保留。程式會以空白畫面開啟供檢查，且不會覆寫原資料。\n備份位置：%s\n\n請先從「設定與備份」匯入有效備份，或手動修復資料檔。" % (e, damaged_copy)
        )
        return default_data()


def save_data(d):
    p = data_file()
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise


# ══════════════════════════════════════════════
#  案件編輯對話框
# ══════════════════════════════════════════════
class ContractDialog(tk.Toplevel):
    def __init__(self, parent, app, case=None):
        super().__init__(parent)
        self.app = app
        self.is_new = case is None
        self.case = dict(case) if case else {}
        self.result = None
        self.title("➕ 新增案件" if self.is_new else "✏️ 編輯案件")
        self.configure(bg=C_BG)
        self.geometry("760x800")
        self.minsize(620, 500)
        self.resizable(False, True)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._load()
        self.bind("<Escape>", lambda e: self.destroy())

    def _lbl(self, parent, text, r, c=0):
        tk.Label(parent, text=text, bg=C_SURFACE, fg=C_TEXT_2,
                 font=(self.app.F, 10, "bold"), anchor="e", width=11
                 ).grid(row=r, column=c, sticky="e", padx=(14, 10), pady=7)

    def _build(self):
        F = self.app.F

        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=20, pady=(6, 16))

        def btn(txt, cmd, kind):
            palettes = {
                "success": (C_SUCCESS_L, C_SUCCESS_D, "#C8EAD6"),
                "danger":  (C_DANGER_L, C_DANGER_D, "#F4C0C0"),
                "ghost":   (C_SURFACE_3, C_TEXT, "#F3D6DE"),
            }
            bg, fg, hov = palettes[kind]
            b = tk.Button(bar, text=txt, command=cmd, font=(F, 11, "bold"),
                          bg=bg, fg=fg, activebackground=hov, activeforeground=fg,
                          relief="flat", padx=20, pady=9, cursor="hand2",
                          bd=0, highlightthickness=0)
            b.bind("<Enter>", lambda e: b.configure(bg=hov))
            b.bind("<Leave>", lambda e: b.configure(bg=bg))
            return b

        btn("💾 儲存", self.on_save, "success").pack(side="right")
        btn("❌ 取消", self.destroy, "ghost").pack(side="right", padx=8)
        if not self.is_new:
            btn("🗑️ 刪除", self.on_delete, "danger").pack(side="left")

        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text=("➕ 新增案件" if self.is_new else "✏️ 編輯案件"),
                 font=(F, 17, "bold"), bg=C_BG, fg=C_TEXT
                 ).pack(anchor="w", padx=20, pady=(18, 0))

        form = tk.Frame(outer, bg=C_SURFACE,
                        highlightbackground=C_BORDER, highlightthickness=1)
        form.pack(fill="both", expand=True, padx=20, pady=(12, 0))
        form.columnconfigure(1, weight=1)

        self.v = {}
        self.chk_vars = {}
        r = 0

        def add(label, key, widget="entry", values=None):
            nonlocal r
            tk.Label(form, text=label, bg=C_SURFACE, fg=C_TEXT_2,
                     font=(F, 10, "bold"), width=11, anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(14, 10), pady=8)
            if widget == "entry":
                w = tk.Entry(form, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                             relief="flat", bd=0, highlightthickness=1,
                             highlightbackground=C_BORDER,
                             highlightcolor=C_PRIMARY)
            elif widget == "combo":
                w = ttk.Combobox(form, values=values, state="readonly", font=(F, 11))
            w.grid(row=r, column=1, sticky="ew", padx=(0, 18), pady=8, ipady=4)
            self.v[key] = w
            r += 1
            return w

        add("客戶代碼", "code")
        add("客戶名稱", "name")
        add("業務名字", "sales")
        add("文件類型", "dtype", "combo", DOC_TYPES)
        add("區域", "region", "combo", REGIONS)

        self._add_datetime_row(form, "收件日", "recv_date", r); r += 1
        self._add_datetime_row(form, "送件日", "send_date", r); r += 1
        self._add_datetime_row(form, "回件日", "return_date", r); r += 1

        add("當前階段", "stage", "combo", [n for _, n, _ in STAGES])

        self._lbl(form, "狀態標記", r)
        chk = tk.Frame(form, bg=C_SURFACE)
        chk.grid(row=r, column=1, sticky="w", padx=(0, 18), pady=4)
        for key, txt in (("ok_mail", "主旨已加 -OK"),
                         ("has_card", "有製卡")):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(chk, text=txt, variable=var,
                                bg=C_SURFACE, activebackground=C_SURFACE,
                                fg=C_TEXT, selectcolor=C_SURFACE,
                                font=(F, 10), cursor="hand2")
            cb.pack(side="left", padx=(0, 14))
            self.v[key] = cb
            self.chk_vars[key] = var
        r += 1

        self._lbl(form, "備註", r)
        self.v["notes"] = tk.Text(form, height=5, font=(F, 10),
                                  bg=C_SURFACE, fg=C_TEXT, relief="flat",
                                  bd=0, highlightthickness=1,
                                  highlightbackground=C_BORDER,
                                  highlightcolor=C_PRIMARY, wrap="word")
        self.v["notes"].grid(row=r, column=1, sticky="ew",
                             padx=(0, 18), pady=8)
        r += 1

        tk.Label(outer, text="⏰ 收件截止 15:30　|　📮 寄件時段 10:00、14:00（最晚 14:00 送總機）",
                 font=(F, 9), bg=C_BG, fg=C_TEXT_3
                 ).pack(anchor="w", padx=20, pady=(10, 16))

    def _add_datetime_row(self, form, label, key, r):
        F = self.app.F
        self._lbl(form, label, r)
        fr = tk.Frame(form, bg=C_SURFACE)
        fr.grid(row=r, column=1, sticky="ew", padx=(0, 18), pady=7)

        e_date = tk.Entry(fr, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                          relief="flat", bd=0, width=12, highlightthickness=1,
                          highlightbackground=C_BORDER, highlightcolor=C_PRIMARY)
        e_date.pack(side="left", ipady=4)

        tk.Label(fr, text=" ", bg=C_SURFACE).pack(side="left")

        e_time = tk.Entry(fr, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                          relief="flat", bd=0, width=6, highlightthickness=1,
                          highlightbackground=C_BORDER, highlightcolor=C_PRIMARY)
        e_time.pack(side="left", ipady=4)
        tk.Label(fr, text=" HH:MM", font=(F, 8), bg=C_SURFACE,
                 fg=C_TEXT_3).pack(side="left", padx=(4, 8))

        def mk(txt, bg, cmd, hover):
            b = tk.Button(fr, text=txt, font=(F, 9), bg=bg, fg=C_TEXT,
                          relief="flat", bd=0, padx=8, pady=3, cursor="hand2",
                          highlightthickness=0, command=cmd)
            b.bind("<Enter>", lambda e: b.configure(bg=hover))
            b.bind("<Leave>", lambda e: b.configure(bg=bg))
            return b

        mk("現在", C_INFO_L, lambda: self._set_now(key), "#C9E0F7").pack(side="left", padx=2)
        mk("今天", C_WARNING_L, lambda: self._set_today(key), "#F8E8AD").pack(side="left", padx=2)
        mk("清空", C_GRAY_L, lambda: self._clear_dt(key), "#E2E2EA").pack(side="left", padx=2)

        self.v[key] = e_date
        self.v[key + "_time"] = e_time

    def _set_now(self, key):
        now = datetime.now()
        self.v[key].delete(0, "end")
        self.v[key].insert(0, now.strftime("%Y-%m-%d"))
        self.v[key + "_time"].delete(0, "end")
        self.v[key + "_time"].insert(0, now.strftime("%H:%M"))

    def _set_today(self, key):
        self.v[key].delete(0, "end")
        self.v[key].insert(0, today_str())

    def _clear_dt(self, key):
        self.v[key].delete(0, "end")
        self.v[key + "_time"].delete(0, "end")

    def _get_dt(self, key):
        d = self.v[key].get().strip()
        t = self.v[key + "_time"].get().strip()
        if not d:
            return ""
        if t:
            return d + " " + t
        return d

    def _load(self):
        c = self.case
        self.v["code"].insert(0, c.get("code", ""))
        self.v["name"].insert(0, c.get("name", ""))
        self.v["sales"].insert(0, c.get("sales", ""))
        self.v["dtype"].set(c.get("dtype", DOC_TYPES[0]))
        self.v["region"].set(c.get("region", REGIONS[0]))
        for key in ("recv_date", "send_date", "return_date"):
            val = c.get(key, "")
            d, t = parse_dt(val)
            self.v[key].insert(0, d)
            self.v[key + "_time"].insert(0, t)
        if self.is_new:
            self.v["recv_date"].delete(0, "end")
            self.v["recv_date"].insert(0, today_str())
        sname = STAGE_MAP.get(c.get("stage", "received"), ("", ""))[0]
        self.v["stage"].set(sname or STAGES[0][1])
        for k in ("ok_mail", "has_card"):
            if c.get(k):
                self.chk_vars[k].set(True)
        self.v["notes"].insert("1.0", c.get("notes", ""))

    def on_save(self):
        code = self.v["code"].get().strip()
        name = self.v["name"].get().strip()
        if not code and not name:
            messagebox.showwarning("提醒", "請至少填寫「客戶代碼」或「客戶名稱」！", parent=self)
            return
        date_values = {k: self._get_dt(k).strip() for k in ("recv_date", "send_date", "return_date")}
        for label, value in (("收件日", date_values["recv_date"]),
                             ("送件日", date_values["send_date"]),
                             ("回件日", date_values["return_date"])):
            if value:
                valid = False
                for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M"):
                    try:
                        datetime.strptime(value, fmt)
                        valid = True
                        break
                    except ValueError:
                        continue
                if not valid:
                    messagebox.showwarning("日期格式錯誤",
                                           "%s請使用 YYYY-MM-DD 或 YYYY-MM-DD HH:MM 格式。\n目前輸入：%s" % (label, value),
                                           parent=self)
                    return
        stage_label = self.v["stage"].get()
        stage_key = "received"
        for k, n, _ in STAGES:
            if n == stage_label:
                stage_key = k
                break

        self.result = {
            "code": code,
            "name": name,
            "sales": self.v["sales"].get().strip(),
            "dtype": self.v["dtype"].get(),
            "region": self.v["region"].get(),
            "recv_date": self._get_dt("recv_date"),
            "send_date": self._get_dt("send_date"),
            "return_date": self._get_dt("return_date"),
            "stage": stage_key,
            "ok_mail": bool(self.chk_vars["ok_mail"].get()),
            "has_card": bool(self.chk_vars["has_card"].get()),
            "nns_needed": (stage_key == "nns_pending"),
            "notes": self.v["notes"].get("1.0", "end").strip(),
        }
        self.destroy()

    def on_delete(self):
        if messagebox.askyesno("確認刪除", "確定要刪除這筆案件嗎？此動作無法復原。", parent=self):
            self.result = "__DELETE__"
            self.destroy()


# ══════════════════════════════════════════════
#  NNS 編輯對話框
# ══════════════════════════════════════════════
class NNSDialog(tk.Toplevel):
    def __init__(self, parent, app, rec=None):
        super().__init__(parent)
        self.app = app
        self.is_new = rec is None
        self.rec = dict(rec) if rec else {}
        self.result = None
        self.title("➕ 新增 NNS 紀錄" if self.is_new else "✏️ 編輯 NNS 紀錄")
        self.configure(bg=C_BG)
        self.geometry("640x620")
        self.minsize(520, 460)
        self.resizable(False, True)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._load()

    def _build(self):
        F = self.app.F

        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=20, pady=(6, 16))

        def btn(txt, cmd, kind):
            p = {"success": (C_SUCCESS_L, C_SUCCESS_D, "#C8EAD6"),
                 "ghost": (C_SURFACE_3, C_TEXT, "#F3D6DE")}[kind]
            bg, fg, hov = p
            b = tk.Button(bar, text=txt, command=cmd, font=(F, 11, "bold"),
                          bg=bg, fg=fg, activebackground=hov, activeforeground=fg,
                          relief="flat", padx=20, pady=9, cursor="hand2",
                          bd=0, highlightthickness=0)
            b.bind("<Enter>", lambda e: b.configure(bg=hov))
            b.bind("<Leave>", lambda e: b.configure(bg=bg))
            return b
        btn("💾 儲存", self.on_save, "success").pack(side="right")
        btn("❌ 取消", self.destroy, "ghost").pack(side="right", padx=8)

        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text=("➕ 新增 NNS 紀錄" if self.is_new else "✏️ 編輯 NNS 紀錄"),
                 font=(F, 17, "bold"), bg=C_BG, fg=C_TEXT
                 ).pack(anchor="w", padx=20, pady=(18, 0))

        form = tk.Frame(outer, bg=C_SURFACE,
                        highlightbackground=C_BORDER, highlightthickness=1)
        form.pack(fill="both", expand=True, padx=20, pady=(12, 0))
        form.columnconfigure(1, weight=1)

        self.v = {}
        self.chk_vars = {}
        r = 0

        def add(label, key, widget="entry", values=None):
            nonlocal r
            tk.Label(form, text=label, bg=C_SURFACE, fg=C_TEXT_2,
                     font=(F, 10, "bold"), width=11, anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(14, 10), pady=8)
            if widget == "entry":
                w = tk.Entry(form, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                             relief="flat", bd=0, highlightthickness=1,
                             highlightbackground=C_BORDER,
                             highlightcolor=C_PRIMARY)
            elif widget == "combo":
                w = ttk.Combobox(form, values=values, state="readonly", font=(F, 11))
            w.grid(row=r, column=1, sticky="ew", padx=(0, 18), pady=8, ipady=4)
            self.v[key] = w
            r += 1

        add("客戶代碼", "code")
        add("客戶名稱", "name")
        add("業務名字", "sales")
        add("類型", "kind", "combo", NNS_KINDS)

        self._add_dt_row(form, "收件日", "req_date", r); r += 1
        self._add_dt_row(form, "完成日", "done_date", r); r += 1

        tk.Label(form, text="已回信 -OK", bg=C_SURFACE, fg=C_TEXT_2,
                 font=(F, 10, "bold"), width=11, anchor="e"
                 ).grid(row=r, column=0, sticky="e", padx=(14, 10), pady=8)
        var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(form, variable=var, bg=C_SURFACE,
                            activebackground=C_SURFACE, fg=C_TEXT,
                            selectcolor=C_SURFACE, font=(F, 11),
                            cursor="hand2", anchor="w")
        cb.grid(row=r, column=1, sticky="w", padx=(0, 18), pady=8)
        self.chk_vars["replied"] = var
        self.v["replied"] = cb
        r += 1

        tk.Label(form, text="備註", bg=C_SURFACE, fg=C_TEXT_2,
                 font=(F, 10, "bold"), width=11, anchor="ne"
                 ).grid(row=r, column=0, sticky="ne", padx=(14, 10), pady=8)
        self.v["note"] = tk.Text(form, height=4, font=(F, 10), bg=C_SURFACE,
                                 fg=C_TEXT, relief="flat", bd=0,
                                 highlightthickness=1,
                                 highlightbackground=C_BORDER,
                                 highlightcolor=C_PRIMARY, wrap="word")
        self.v["note"].grid(row=r, column=1, sticky="ew", padx=(0, 18), pady=8)

    def _add_dt_row(self, form, label, key, r):
        F = self.app.F
        tk.Label(form, text=label, bg=C_SURFACE, fg=C_TEXT_2,
                 font=(F, 10, "bold"), width=11, anchor="e"
                 ).grid(row=r, column=0, sticky="e", padx=(14, 10), pady=8)

        fr = tk.Frame(form, bg=C_SURFACE)
        fr.grid(row=r, column=1, sticky="ew", padx=(0, 18), pady=8)

        e_date = tk.Entry(fr, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                          relief="flat", bd=0, width=12, highlightthickness=1,
                          highlightbackground=C_BORDER, highlightcolor=C_PRIMARY)
        e_date.pack(side="left", ipady=4)

        tk.Label(fr, text=" ", bg=C_SURFACE).pack(side="left")

        e_time = tk.Entry(fr, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                          relief="flat", bd=0, width=6, highlightthickness=1,
                          highlightbackground=C_BORDER, highlightcolor=C_PRIMARY)
        e_time.pack(side="left", ipady=4)
        tk.Label(fr, text=" HH:MM", font=(F, 8), bg=C_SURFACE,
                 fg=C_TEXT_3).pack(side="left", padx=(4, 8))

        def mk(txt, bg, cmd, hover):
            b = tk.Button(fr, text=txt, font=(F, 9), bg=bg, fg=C_TEXT,
                          relief="flat", bd=0, padx=8, pady=3, cursor="hand2",
                          highlightthickness=0, command=cmd)
            b.bind("<Enter>", lambda e: b.configure(bg=hover))
            b.bind("<Leave>", lambda e: b.configure(bg=bg))
            return b

        mk("現在", C_INFO_L, lambda: self._set_now(key), "#C9E0F7").pack(side="left", padx=2)
        mk("今天", C_WARNING_L, lambda: self._set_today(key), "#F8E8AD").pack(side="left", padx=2)
        mk("清空", C_GRAY_L, lambda: self._clear_dt(key), "#E2E2EA").pack(side="left", padx=2)

        self.v[key] = e_date
        self.v[key + "_time"] = e_time

    def _set_now(self, key):
        now = datetime.now()
        self.v[key].delete(0, "end")
        self.v[key].insert(0, now.strftime("%Y-%m-%d"))
        self.v[key + "_time"].delete(0, "end")
        self.v[key + "_time"].insert(0, now.strftime("%H:%M"))

    def _set_today(self, key):
        self.v[key].delete(0, "end")
        self.v[key].insert(0, today_str())

    def _clear_dt(self, key):
        self.v[key].delete(0, "end")
        self.v[key + "_time"].delete(0, "end")

    def _get_dt(self, key):
        d = self.v[key].get().strip()
        t = self.v[key + "_time"].get().strip()
        if not d:
            return ""
        if t:
            return d + " " + t
        return d

    def _load(self):
        r = self.rec
        self.v["code"].insert(0, r.get("code", ""))
        self.v["name"].insert(0, r.get("name", ""))
        self.v["sales"].insert(0, r.get("sales", ""))
        self.v["kind"].set(r.get("kind", NNS_KINDS[0]))
        for key in ("req_date", "done_date"):
            val = r.get(key, "")
            if not val and key == "req_date" and self.is_new:
                val = today_str()
            d, t = parse_dt(val)
            self.v[key].insert(0, d)
            self.v[key + "_time"].insert(0, t)
        if r.get("replied"):
            self.chk_vars["replied"].set(True)
        self.v["note"].insert("1.0", r.get("note", ""))

    def on_save(self):
        code = self.v["code"].get().strip()
        name = self.v["name"].get().strip()
        if not code and not name:
            messagebox.showwarning("提醒", "請至少填寫「客戶代碼」或「客戶名稱」！", parent=self)
            return
        self.result = {
            "code": code,
            "name": name,
            "sales": self.v["sales"].get().strip(),
            "kind": self.v["kind"].get(),
            "req_date": self._get_dt("req_date"),
            "done_date": self._get_dt("done_date"),
            "replied": bool(self.chk_vars["replied"].get()),
            "note": self.v["note"].get("1.0", "end").strip(),
        }
        self.destroy()


# ══════════════════════════════════════════════
#  封面函對話框
# ══════════════════════════════════════════════
class LetterDialog(tk.Toplevel):
    def __init__(self, parent, app, case=None):
        super().__init__(parent)
        self.app = app
        self.case = case or {}
        self.title("🖨️ 產生封面函")
        self.configure(bg=C_BG)
        self.geometry("560x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()

    def _build(self):
        F = self.app.F

        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=20, pady=(6, 16))

        def mk(txt, cmd, kind):
            p = {"primary": (C_PRIMARY, "#FFFFFF", C_PRIMARY_D),
                 "ghost": (C_SURFACE_3, C_TEXT, "#F3D6DE")}[kind]
            bg, fg, hov = p
            b = tk.Button(bar, text=txt, command=cmd, font=(F, 11, "bold"),
                          bg=bg, fg=fg, activebackground=hov, activeforeground=fg,
                          relief="flat", padx=20, pady=9, cursor="hand2",
                          bd=0, highlightthickness=0)
            b.bind("<Enter>", lambda e: b.configure(bg=hov))
            b.bind("<Leave>", lambda e: b.configure(bg=bg))
            return b
        mk("✨ 產生並開啟", self.on_gen, "primary").pack(side="right")
        mk("取消", self.destroy, "ghost").pack(side="right", padx=8)

        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text="🖨️ 產生封面函", font=(F, 17, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(anchor="w", padx=20, pady=(18, 0))

        form = tk.Frame(outer, bg=C_SURFACE,
                        highlightbackground=C_BORDER, highlightthickness=1)
        form.pack(fill="x", padx=20, pady=(12, 0))
        form.columnconfigure(1, weight=1)
        self.v = {}
        rows = [("客戶代碼", "code", self.case.get("code", "")),
                ("客戶名稱", "name", self.case.get("name", "")),
                ("函的編號", "letter_no", "")]
        for i, (lab, key, default) in enumerate(rows):
            tk.Label(form, text=lab, bg=C_SURFACE, fg=C_TEXT_2, width=10,
                     anchor="e", font=(F, 10, "bold")
                     ).grid(row=i, column=0, sticky="e", padx=(14, 10), pady=10)
            e = tk.Entry(form, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=C_BORDER, highlightcolor=C_PRIMARY)
            e.insert(0, default)
            e.grid(row=i, column=1, sticky="ew", padx=(0, 18), pady=10, ipady=4)
            self.v[key] = e

        tk.Label(outer, text="附件：", bg=C_BG, fg=C_TEXT,
                 font=(F, 11, "bold")).pack(anchor="w", padx=20, pady=(14, 4))
        self.item_vars = {}
        items = [("合約書", True), ("補充協議書", False), ("製卡", False), ("簽呈", False)]
        box = tk.Frame(outer, bg=C_BG)
        box.pack(anchor="w", padx=20)
        for txt, default in items:
            var = tk.BooleanVar(value=default)
            tk.Checkbutton(box, text=txt, variable=var, bg=C_BG,
                           activebackground=C_BG, fg=C_TEXT,
                           selectcolor=C_SURFACE, font=(F, 10),
                           cursor="hand2").pack(side="left", padx=(0, 16))
            self.item_vars[txt] = var

    def on_gen(self):
        code = self.v["code"].get().strip()
        name = self.v["name"].get().strip()
        no = self.v["letter_no"].get().strip()
        if not (code or name):
            messagebox.showwarning("提醒", "請填寫客戶代碼或名稱！", parent=self)
            return
        items = [k for k, v in self.item_vars.items() if v.get()]
        items_txt = "、".join(items) if items else "（無）"
        tpl = self.app.data["settings"].get("letter_tpl", DEFAULT_LETTER_TPL)
        html = (tpl.replace("{letter_no}", no or "＿＿＿＿")
                   .replace("{customer_code}", code)
                   .replace("{customer_name}", name)
                   .replace("{sales}", self.case.get("sales", ""))
                   .replace("{items}", items_txt)
                   .replace("{date}", today_str()))
        fname = "封面函_%s_%s.html" % (code or name, datetime.now().strftime("%Y%m%d_%H%M%S"))
        fname = fname.replace("/", "_").replace("\\", "_")
        path = os.path.join(letter_dir(), fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        try:
            webbrowser.open("file:///" + path.replace("\\", "/"))
        except Exception:
            pass
        messagebox.showinfo("完成", "封面函已產生：\n%s" % path, parent=self)
        self.destroy()


# ══════════════════════════════════════════════
#  寄件 / 領取 編輯對話框
# ══════════════════════════════════════════════
class ShipDialog(tk.Toplevel):
    def __init__(self, parent, app, case):
        super().__init__(parent)
        self.app = app
        self.case = case
        self.title("📮 寄件 / 領取 - %s" % case.get("name", ""))
        self.configure(bg=C_BG)
        self.geometry("680x660")
        self.minsize(560, 520)
        self.resizable(False, True)
        self.transient(parent)
        self.grab_set()
        self._build()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        F = self.app.F

        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=20, pady=(6, 16))

        def mk(txt, cmd, kind):
            p = {"success": (C_SUCCESS_L, C_SUCCESS_D, "#C8EAD6"),
                 "primary": (C_PRIMARY, "#FFFFFF", C_PRIMARY_D),
                 "ghost":   (C_SURFACE_3, C_TEXT, "#F3D6DE")}[kind]
            bg, fg, hov = p
            b = tk.Button(bar, text=txt, command=cmd, font=(F, 11, "bold"),
                          bg=bg, fg=fg, activebackground=hov, activeforeground=fg,
                          relief="flat", padx=20, pady=9, cursor="hand2",
                          bd=0, highlightthickness=0)
            b.bind("<Enter>", lambda e: b.configure(bg=hov))
            b.bind("<Leave>", lambda e: b.configure(bg=bg))
            return b

        mk("💾 儲存", self.on_save, "success").pack(side="right")
        mk("❌ 取消", self.destroy, "ghost").pack(side="right", padx=8)
        mk("✅ 結案", self.on_done, "primary").pack(side="left")

        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text="📮 寄件 / 領取",
                 font=(F, 17, "bold"), bg=C_BG, fg=C_TEXT
                 ).pack(anchor="w", padx=20, pady=(18, 0))

        c = self.case

        info = tk.Frame(outer, bg=C_SURFACE,
                        highlightbackground=C_BORDER, highlightthickness=1)
        info.pack(fill="x", padx=20, pady=(12, 0))
        info.columnconfigure(1, weight=1)

        def info_row(r, label, value):
            tk.Label(info, text=label, bg=C_SURFACE, fg=C_TEXT_3,
                     font=(F, 10, "bold"), width=10, anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(14, 10), pady=6)
            tk.Label(info, text=value or "—", bg=C_SURFACE, fg=C_TEXT,
                     font=(F, 11), anchor="w"
                     ).grid(row=r, column=1, sticky="w", padx=(0, 18), pady=6)

        info_row(0, "客戶代碼", c.get("code", ""))
        info_row(1, "客戶名稱", c.get("name", ""))
        info_row(2, "業務", c.get("sales", ""))
        info_row(3, "區域", c.get("region", ""))
        info_row(4, "文件類型", c.get("dtype", ""))
        info_row(5, "製卡", "💳 有製卡" if c.get("has_card") else "—")

        edit = tk.Frame(outer, bg=C_SURFACE,
                        highlightbackground=C_BORDER, highlightthickness=1)
        edit.pack(fill="x", padx=20, pady=(12, 0))
        edit.columnconfigure(1, weight=1)

        self.v = {}
        self._add_dt_row(edit, "📨 通知日", "notify_date", 0)
        self._add_dt_row(edit, "📬 領取/寄出日", "deliver_date", 1)

        tk.Label(outer,
                 text="💡 狀態說明：\n"
                      "　• 兩個都空 → ⏳ 待通知業務\n"
                      "　• 只填通知日 → 📨 已通知，待領取/寄送\n"
                      "　• 兩者都填 → ✅ 北區已簽領　或　📦 中/南區已寄出",
                 font=(F, 9), bg=C_BG, fg=C_TEXT_3, justify="left"
                 ).pack(anchor="w", padx=20, pady=(14, 16))

    def _add_dt_row(self, parent, label, key, r):
        F = self.app.F
        tk.Label(parent, text=label, bg=C_SURFACE, fg=C_TEXT_2,
                 font=(F, 10, "bold"), width=11, anchor="e"
                 ).grid(row=r, column=0, sticky="e", padx=(14, 10), pady=12)

        fr = tk.Frame(parent, bg=C_SURFACE)
        fr.grid(row=r, column=1, sticky="ew", padx=(0, 18), pady=12)

        d_val, t_val = parse_dt(self.case.get(key, ""))

        e_date = tk.Entry(fr, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                          relief="flat", bd=0, width=12, highlightthickness=1,
                          highlightbackground=C_BORDER, highlightcolor=C_PRIMARY)
        e_date.insert(0, d_val)
        e_date.pack(side="left", ipady=4)

        tk.Label(fr, text=" ", bg=C_SURFACE).pack(side="left")

        e_time = tk.Entry(fr, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                          relief="flat", bd=0, width=6, highlightthickness=1,
                          highlightbackground=C_BORDER, highlightcolor=C_PRIMARY)
        e_time.insert(0, t_val)
        e_time.pack(side="left", ipady=4)

        tk.Label(fr, text=" HH:MM", font=(F, 8), bg=C_SURFACE,
                 fg=C_TEXT_3).pack(side="left", padx=(4, 8))

        def mk(txt, bg, cmd, hover):
            b = tk.Button(fr, text=txt, font=(F, 9), bg=bg, fg=C_TEXT,
                          relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
                          highlightthickness=0, command=cmd)
            b.bind("<Enter>", lambda e: b.configure(bg=hover))
            b.bind("<Leave>", lambda e: b.configure(bg=bg))
            return b

        mk("現在", C_INFO_L, lambda k=key: self._set_now(k), "#C9E0F7").pack(side="left", padx=2)
        mk("今天", C_WARNING_L, lambda k=key: self._set_today(k), "#F8E8AD").pack(side="left", padx=2)
        mk("清空", C_GRAY_L, lambda k=key: self._clear(k), "#E2E2EA").pack(side="left", padx=2)

        self.v[key] = e_date
        self.v[key + "_time"] = e_time

    def _set_now(self, key):
        now = datetime.now()
        self.v[key].delete(0, "end")
        self.v[key].insert(0, now.strftime("%Y-%m-%d"))
        self.v[key + "_time"].delete(0, "end")
        self.v[key + "_time"].insert(0, now.strftime("%H:%M"))

    def _set_today(self, key):
        self.v[key].delete(0, "end")
        self.v[key].insert(0, today_str())

    def _clear(self, key):
        self.v[key].delete(0, "end")
        self.v[key + "_time"].delete(0, "end")

    def _get_dt(self, key):
        d = self.v[key].get().strip()
        t = self.v[key + "_time"].get().strip()
        if not d:
            return ""
        if t:
            return d + " " + t
        return d

    def _apply(self):
        self.case["notify_date"] = self._get_dt("notify_date")
        self.case["deliver_date"] = self._get_dt("deliver_date")

    def on_save(self):
        self._apply()
        self.app._log("編輯寄件資訊：%s %s" % (
            self.case.get("code", ""), self.case.get("name", "")))
        self.app.save()
        self.app.refresh_all()
        self.destroy()

    def on_done(self):
        if not messagebox.askyesno("確認結案", "確定要結案嗎？案件將移到『已結案』。", parent=self):
            return
        self._apply()
        if not self.case.get("deliver_date"):
            self.case["deliver_date"] = now_str()
        self.case["stage"] = "done"
        self.app._log("結案：%s %s" % (
            self.case.get("code", ""), self.case.get("name", "")))
        self.app.save()
        self.app.refresh_all()
        self.destroy()


# ══════════════════════════════════════════════
#  備忘錄編輯對話框
# ══════════════════════════════════════════════
class MemoDialog(tk.Toplevel):
    COLORS = [
        ("黃", "#FFF6D6"),
        ("粉", "#FDE7ED"),
        ("藍", "#DCEEFB"),
        ("綠", "#DFF5E8"),
        ("紫", "#EDE7F6"),
        ("灰", "#EFEFF3"),
    ]

    def __init__(self, parent, app, memo=None):
        super().__init__(parent)
        self.app = app
        self.is_new = memo is None
        self.memo = dict(memo) if memo else {}
        self.result = None
        self.title("➕ 新增備忘錄" if self.is_new else "✏️ 編輯備忘錄")
        self.configure(bg=C_BG)
        self.geometry("540x600")
        self.minsize(440, 460)
        self.resizable(False, True)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._load()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        F = self.app.F

        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=20, pady=(6, 16))

        def mk(txt, cmd, kind):
            p = {"success": (C_SUCCESS_L, C_SUCCESS_D, "#C8EAD6"),
                 "danger":  (C_DANGER_L, C_DANGER_D, "#F4C0C0"),
                 "ghost":   (C_SURFACE_3, C_TEXT, "#F3D6DE")}[kind]
            bg, fg, hov = p
            b = tk.Button(bar, text=txt, command=cmd, font=(F, 11, "bold"),
                          bg=bg, fg=fg, activebackground=hov, activeforeground=fg,
                          relief="flat", padx=20, pady=9, cursor="hand2",
                          bd=0, highlightthickness=0)
            b.bind("<Enter>", lambda e: b.configure(bg=hov))
            b.bind("<Leave>", lambda e: b.configure(bg=bg))
            return b

        mk("💾 儲存", self.on_save, "success").pack(side="right")
        mk("❌ 取消", self.destroy, "ghost").pack(side="right", padx=8)
        if not self.is_new:
            mk("🗑️ 刪除", self.on_delete, "danger").pack(side="left")

        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text=("➕ 新增備忘錄" if self.is_new else "✏️ 編輯備忘錄"),
                 font=(F, 17, "bold"), bg=C_BG, fg=C_TEXT
                 ).pack(anchor="w", padx=20, pady=(18, 0))

        form = tk.Frame(outer, bg=C_SURFACE,
                        highlightbackground=C_BORDER, highlightthickness=1)
        form.pack(fill="both", expand=True, padx=20, pady=(12, 0))
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="標題", bg=C_SURFACE, fg=C_TEXT_2,
                 font=(F, 10, "bold"), width=6, anchor="e"
                 ).grid(row=0, column=0, sticky="e", padx=(14, 10), pady=12)
        self.e_title = tk.Entry(form, font=(F, 11), bg=C_SURFACE, fg=C_TEXT,
                                relief="flat", bd=0, highlightthickness=1,
                                highlightbackground=C_BORDER,
                                highlightcolor=C_PRIMARY)
        self.e_title.grid(row=0, column=1, sticky="ew", padx=(0, 18), pady=12, ipady=4)

        tk.Label(form, text="內容", bg=C_SURFACE, fg=C_TEXT_2,
                 font=(F, 10, "bold"), width=6, anchor="ne"
                 ).grid(row=1, column=0, sticky="ne", padx=(14, 10), pady=12)
        self.txt_content = tk.Text(form, height=10, font=(F, 11),
                                   bg=C_SURFACE, fg=C_TEXT, relief="flat",
                                   bd=0, highlightthickness=1,
                                   highlightbackground=C_BORDER,
                                   highlightcolor=C_PRIMARY, wrap="word")
        self.txt_content.grid(row=1, column=1, sticky="ew",
                              padx=(0, 18), pady=12)

        tk.Label(form, text="顏色", bg=C_SURFACE, fg=C_TEXT_2,
                 font=(F, 10, "bold"), width=6, anchor="e"
                 ).grid(row=2, column=0, sticky="e", padx=(14, 10), pady=12)
        self.color_var = tk.StringVar(value="#FFF6D6")
        color_box = tk.Frame(form, bg=C_SURFACE)
        color_box.grid(row=2, column=1, sticky="w", padx=(0, 18), pady=12)
        for name, c in self.COLORS:
            rb = tk.Radiobutton(color_box, text=name, variable=self.color_var,
                                value=c, bg=c, activebackground=c,
                                fg=C_TEXT, selectcolor=c,
                                indicatoron=False, width=3, height=1,
                                relief="flat", bd=0,
                                font=(F, 9, "bold"), cursor="hand2")
            rb.pack(side="left", padx=3, ipady=4)

    def _load(self):
        self.e_title.insert(0, self.memo.get("title", ""))
        self.txt_content.insert("1.0", self.memo.get("content", ""))
        self.color_var.set(self.memo.get("color", "#FFF6D6"))

    def on_save(self):
        title = self.e_title.get().strip()
        content = self.txt_content.get("1.0", "end").strip()
        if not title and not content:
            messagebox.showwarning("提醒", "請至少填寫「標題」或「內容」！", parent=self)
            return
        self.result = {
            "title": title or "（無標題）",
            "content": content,
            "color": self.color_var.get(),
        }
        self.destroy()

    def on_delete(self):
        if messagebox.askyesno("確認刪除", "確定要刪除這則備忘錄嗎？", parent=self):
            self.result = "__DELETE__"
            self.destroy()


# ══════════════════════════════════════════════
#  主程式
# ══════════════════════════════════════════════
class ContractApp:

    def __init__(self, root):
        self.root = root
        self.F = pick_font()
        self.data = load_data()
        self.safe_mode = DATA_LOAD_FAILED
        self.filter_stage = "all"
        self.search_kw = ""
        self._memo_cols = 3
        self._memo_resize_job = None
        self._is_fullscreen = False
        self._saved_geometry = None
        self._header_photo = None
        self._header_photo_2 = None

        try:
            self.scale = float(self.data["settings"].get("ui_scale", 1.0))
        except Exception:
            self.scale = 1.0
        self.scale = max(0.7, min(2.5, self.scale))

        root.title(APP_TITLE)
        root.configure(bg=C_BG)
        root.geometry("1440x900")
        root.minsize(1060, 700)
        self._center(1440, 900)

        self._style()
        self._build()

        if self.safe_mode:
            self._show_safe_banner()

        self._snapshot_fonts(self.root)
        self.apply_scale(self.scale, save=False)
        self.refresh_all()

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<F11>", self.toggle_fullscreen)
        root.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
        root.bind("<Control-plus>",   lambda e: self.apply_scale(self.scale + 0.1))
        root.bind("<Control-equal>",  lambda e: self.apply_scale(self.scale + 0.1))
        root.bind("<Control-minus>",  lambda e: self.apply_scale(self.scale - 0.1))
        root.bind("<Control-0>",      lambda e: self.apply_scale(1.0))

        self.check_reminders()

    # ----------------------------------
    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 20)
        self.root.geometry("%dx%d+%d+%d" % (w, h, x, y))

    def _style(self):
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except Exception:
            pass
        F = self.F
        st.configure("TFrame", background=C_BG)
        st.configure("TLabel", background=C_BG, foreground=C_TEXT, font=(F, 10))
        st.configure("TEntry", padding=(10, 8), fieldbackground=C_SURFACE,
                     foreground=C_TEXT, bordercolor=C_BORDER,
                     lightcolor=C_BORDER, darkcolor=C_BORDER,
                     insertcolor=C_TEXT)
        st.configure("TCombobox", padding=(10, 8), fieldbackground=C_SURFACE,
                     foreground=C_TEXT, arrowcolor=C_TEXT_2,
                     bordercolor=C_BORDER, lightcolor=C_BORDER, darkcolor=C_BORDER)
        st.map("TCombobox",
               fieldbackground=[("readonly", C_SURFACE), ("focus", C_SURFACE)],
               foreground=[("readonly", C_TEXT)],
               bordercolor=[("focus", C_PRIMARY)])
        st.configure("TCheckbutton", background=C_BG, foreground=C_TEXT, font=(F, 10))
        st.map("TCheckbutton", background=[("active", C_BG)])

        st.configure("Treeview",
                     background=C_SURFACE, foreground=C_TEXT,
                     fieldbackground=C_SURFACE, rowheight=36, font=(F, 10),
                     borderwidth=0, relief="flat")
        st.configure("Treeview.Heading",
                     background=C_SURFACE_3, foreground=C_TEXT_2,
                     font=(F, 10, "bold"), relief="flat", padding=(10, 12),
                     borderwidth=0)
        st.map("Treeview.Heading",
               background=[("active", C_PRIMARY_L)],
               foreground=[("active", C_TEXT)])
        st.map("Treeview",
               background=[("selected", C_PRIMARY_L)],
               foreground=[("selected", C_TEXT)])

        st.configure("Vertical.TScrollbar", background=C_SURFACE_3,
                     troughcolor=C_BG, bordercolor=C_BG, arrowcolor=C_TEXT_3,
                     relief="flat", borderwidth=0)
        st.configure("Horizontal.TScrollbar", background=C_SURFACE_3,
                     troughcolor=C_BG, bordercolor=C_BG, arrowcolor=C_TEXT_3,
                     relief="flat", borderwidth=0)

        st.configure("TNotebook", background=C_BG, borderwidth=0,
                     tabmargins=(0, 0, 0, 0))
        st.configure("TNotebook.Tab",
                     background=C_SURFACE_3, foreground=C_TEXT_2,
                     padding=(22, 12), font=(F, 10, "bold"), borderwidth=0)
        st.map("TNotebook.Tab",
               background=[("selected", C_SURFACE), ("active", C_PRIMARY_XL)],
               foreground=[("selected", C_PRIMARY_D), ("active", C_TEXT)])

    # ── 縮放 ─────────────────────────
    def _snapshot_fonts(self, widget):
        try:
            f = widget.cget("font")
            if f and not hasattr(widget, "_orig_font"):
                widget._orig_font = f
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._snapshot_fonts(child)
        except Exception:
            pass

    def _scale_fonts(self, widget, factor):
        if hasattr(widget, "_orig_font"):
            orig = widget._orig_font
            new_font = None
            if isinstance(orig, (tuple, list)) and len(orig) >= 2:
                parts = list(orig)
                if isinstance(parts[1], int):
                    parts[1] = max(7, int(round(parts[1] * factor)))
                    new_font = tuple(parts)
            if new_font:
                try:
                    widget.configure(font=new_font)
                except Exception:
                    pass
        try:
            for child in widget.winfo_children():
                self._scale_fonts(child, factor)
        except Exception:
            pass

    def apply_scale(self, factor, save=True):
        try:
            factor = round(max(0.7, min(3.0, float(factor))), 2)
        except Exception:
            factor = 1.0
        self.scale = factor

        self._snapshot_fonts(self.root)
        self._scale_fonts(self.root, factor)

        style = ttk.Style()
        style.configure("Treeview",
                        rowheight=int(36 * factor),
                        font=(self.F, max(8, int(10 * factor))))
        style.configure("Treeview.Heading",
                        font=(self.F, max(8, int(10 * factor)), "bold"),
                        padding=(10, int(10 * factor)))
        style.configure("TNotebook.Tab",
                        font=(self.F, max(8, int(10 * factor)), "bold"),
                        padding=(int(22 * factor), int(12 * factor)))
        try:
            self.root.option_add("*TCombobox*Listbox.font",
                                 (self.F, max(8, int(10 * factor))))
        except Exception:
            pass

        try:
            self.head_frame.configure(height=int(HEADER_BASE_HEIGHT * factor))
        except Exception:
            pass

        self.data["settings"]["ui_scale"] = factor
        if save:
            self.save()

        if hasattr(self, "lbl_scale"):
            self.lbl_scale.configure(text="%d%%" % int(round(factor * 100)))

        try:
            self._load_header_image()
        except Exception:
            pass

        try:
            self.root.update_idletasks()
        except Exception:
            pass

    def _on_ctrl_wheel(self, event):
        if event.delta > 0:
            self.apply_scale(self.scale + 0.1)
        else:
            self.apply_scale(self.scale - 0.1)

    def toggle_fullscreen(self, event=None):
        try:
            if self._is_fullscreen:
                self.root.attributes("-fullscreen", False)
                if self._saved_geometry:
                    self.root.geometry(self._saved_geometry)
                self._is_fullscreen = False
            else:
                self._saved_geometry = self.root.geometry()
                self.root.attributes("-fullscreen", True)
                self._is_fullscreen = True
        except Exception:
            try:
                self._is_fullscreen = not self._is_fullscreen
                self.root.attributes("-zoomed", self._is_fullscreen)
            except Exception:
                pass
        return "break"

    # ----------------------------------
    def _build(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_notebook()
        self._build_footer()

    def _build_header(self):
        F = self.F
        head = tk.Frame(self.root, bg=C_HEADER, height=HEADER_BASE_HEIGHT,
                        highlightbackground=C_BORDER, highlightthickness=1)
        head.grid(row=0, column=0, sticky="ew")
        head.grid_propagate(False)
        self.head_frame = head

        brand = tk.Frame(head, bg=C_HEADER)
        brand.pack(side="left", padx=(26, 0), pady=18)
        tk.Label(brand, text="🌸 合約小管家 🌸",
                 font=(F, 18, "bold"), bg=C_HEADER, fg="#633D4B").pack(anchor="w")
        tk.Label(brand, text="⭐努力工作，買星導ショウ周邊⭐",
                 font=(F, 10), bg=C_HEADER, fg="#8D5B6C").pack(anchor="w", pady=(3, 0))

        deco = tk.Frame(head, bg=C_HEADER)
        deco.pack(side="left", fill="both", expand=True, padx=14, pady=6)
        self.header_deco = deco

        right = tk.Frame(head, bg=C_HEADER)
        right.pack(side="right", padx=(0, 26))
        self.lbl_clock = tk.Label(right, text="", font=(F, 11, "bold"),
                                  bg=C_HEADER, fg=C_TEXT)
        self.lbl_clock.pack(anchor="e")
        self.lbl_cut = tk.Label(right, text="", font=(F, 9),
                                bg=C_HEADER, fg="#8D5B6C")
        self.lbl_cut.pack(anchor="e", pady=(3, 0))
        self._tick()

        zbox = tk.Frame(head, bg=C_HEADER)
        zbox.pack(side="right", padx=(0, 20))
        tk.Label(zbox, text="縮放", font=(F, 9),
                 bg=C_HEADER, fg="#8D5B6C").pack(side="left", padx=(0, 6))

        def mkbtn(txt, cmd):
            b = tk.Button(zbox, text=txt, font=(F, 11, "bold"),
                          bg=C_SURFACE, fg=C_TEXT, relief="flat",
                          width=2, cursor="hand2", bd=0, highlightthickness=0,
                          activebackground=C_PRIMARY_L, activeforeground=C_TEXT,
                          command=cmd)
            b.bind("<Enter>", lambda e: b.configure(bg=C_PRIMARY_L))
            b.bind("<Leave>", lambda e: b.configure(bg=C_SURFACE))
            return b

        mkbtn("−", lambda: self.apply_scale(self.scale - 0.1)).pack(side="left")
        self.lbl_scale = tk.Label(zbox, text="100%", font=(F, 10, "bold"),
                                  bg=C_HEADER, fg=C_TEXT, width=6)
        self.lbl_scale.pack(side="left", padx=2)
        mkbtn("+", lambda: self.apply_scale(self.scale + 0.1)).pack(side="left")

        rst = tk.Button(zbox, text="重置", font=(F, 9), bg=C_SURFACE,
                        fg=C_TEXT_2, relief="flat", padx=10, pady=3,
                        cursor="hand2", bd=0, highlightthickness=0,
                        activebackground=C_PRIMARY_L, activeforeground=C_TEXT,
                        command=lambda: self.apply_scale(1.0))
        rst.pack(side="left", padx=(8, 0))

        self._load_header_image()

    # ─────────────────────────────────
    #  裝飾圖片功能（雙槽位）
    # ─────────────────────────────────
    def _load_header_image(self):
        if not hasattr(self, "header_deco"):
            return
        for w in self.header_deco.winfo_children():
            w.destroy()
        self._header_photo = None
        self._header_photo_2 = None

        fname1 = self.data["settings"].get("header_image", "")
        fname2 = self.data["settings"].get("header_image_2", "")

        changed = False
        if fname1 and not os.path.exists(os.path.join(decor_dir(), fname1)):
            self.data["settings"]["header_image"] = ""
            fname1 = ""
            changed = True
        if fname2 and not os.path.exists(os.path.join(decor_dir(), fname2)):
            self.data["settings"]["header_image_2"] = ""
            fname2 = ""
            changed = True
        if changed:
            self.save()

        has1 = bool(fname1)
        has2 = bool(fname2)

        scale = getattr(self, "scale", 1.0) or 1.0
        target_h = int(HEADER_IMG_MAX_H * scale)
        if has1 and has2:
            max_w = int(HEADER_IMG_MAX_W_DUAL * scale)
        else:
            max_w = int(HEADER_IMG_MAX_W * scale)

        inner = tk.Frame(self.header_deco, bg=C_HEADER)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        if has1:
            self._make_header_image_widget(inner, fname1, 1, target_h, max_w)
        else:
            self._make_header_hint(inner, 1)

        tk.Frame(inner, bg=C_HEADER, width=10).pack(side="left")

        if has2:
            self._make_header_image_widget(inner, fname2, 2, target_h, max_w)
        else:
            self._make_header_hint(inner, 2)

    def _make_header_hint(self, parent, slot):
        hint = tk.Label(parent, text="＋", font=(self.F, 16),
                        bg=C_HEADER, fg="#8D5B6C",
                        cursor="hand2", padx=20, pady=18,
                        highlightbackground="#D8A5B8",
                        highlightthickness=1, bd=0)
        hint.pack(side="left")
        hint.bind("<Button-1>", lambda e, s=slot: self._pick_header_image(s))
        hint.bind("<Enter>", lambda e: hint.configure(bg="#F2B8CA"))
        hint.bind("<Leave>", lambda e: hint.configure(bg=C_HEADER))
        return hint

    def _make_header_image_widget(self, parent, fname, slot, target_h, max_w):
        path = os.path.join(decor_dir(), fname)
        photo = None
        try:
            if HAS_PIL:
                img = Image.open(path)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                w, h = img.size
                ratio = min(target_h / h, max_w / w, 1.0)
                new_w = max(1, int(round(w * ratio)))
                new_h = max(1, int(round(h * ratio)))
                if (new_w, new_h) != (w, h):
                    img = img.resize((new_w, new_h), _LANCZOS)
                photo = ImageTk.PhotoImage(img)
            else:
                photo = tk.PhotoImage(file=path)
                ph = photo.height()
                if ph > target_h:
                    factor = max(1, int(ph // target_h))
                    if factor > 1:
                        photo = photo.subsample(factor, factor)
                ph = photo.height()
                if ph > 0 and target_h > 0:
                    zoom = target_h / float(ph)
                    if zoom > 1.05:
                        z = min(4, max(1, int(zoom)))
                        photo = photo.zoom(z, z)
        except Exception as e:
            key = "header_image" if slot == 1 else "header_image_2"
            messagebox.showerror(
                "圖片載入失敗",
                "無法載入裝飾圖片（第 %d 張）：\n%s\n\n已自動清除此圖片設定。\n"
                "（若為 JPG/JPEG/WEBP 格式，請先安裝 Pillow：pip install Pillow）" % (slot, e))
            self.data["settings"][key] = ""
            self.save()
            return

        lbl = tk.Label(parent, image=photo, bg=C_HEADER,
                       cursor="hand2", bd=0, highlightthickness=0)
        lbl.image = photo
        if slot == 1:
            self._header_photo = photo
        else:
            self._header_photo_2 = photo
        lbl.pack(side="left")
        lbl.bind("<Button-1>", lambda e, s=slot: self._pick_header_image(s))
        lbl.bind("<Double-1>", lambda e, s=slot: self._pick_header_image(s))
        lbl.bind("<Button-3>", lambda e, s=slot: self._header_image_menu(e, s))
        return lbl

    def _pick_header_image(self, slot=1):
        if slot == 1:
            title = "選擇裝飾圖片 ①"
        else:
            title = "選擇裝飾圖片 ②"
        p = filedialog.askopenfilename(
            title=title,
            filetypes=[
                ("圖片檔", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("所有檔案", "*.*"),
            ])
        if not p:
            return

        ext = os.path.splitext(p)[1].lower()
        if not HAS_PIL and ext not in (".png", ".gif"):
            messagebox.showwarning(
                "缺少 Pillow",
                "目前未安裝 Pillow，僅支援 PNG / GIF 格式。\n\n"
                "若想使用 JPG / JPEG / WEBP / BMP 等格式，請先安裝：\n"
                "    pip install Pillow")
            return

        try:
            key = "header_image" if slot == 1 else "header_image_2"
            prefix = "header" if slot == 1 else "header2"
            fname = "%s_%s%s" % (prefix, datetime.now().strftime("%Y%m%d_%H%M%S"), ext or ".png")
            dst = os.path.join(decor_dir(), fname)
            shutil.copy2(p, dst)

            old = self.data["settings"].get(key, "")
            if old and old != fname:
                try:
                    old_path = os.path.join(decor_dir(), old)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except Exception:
                    pass

            self.data["settings"][key] = fname
            self.save()
            self._load_header_image()
            self._log("設定頂部裝飾圖片 %d：%s" % (slot, os.path.basename(p)))
        except Exception as e:
            messagebox.showerror("錯誤", "無法載入圖片：\n%s" % e)

    def _remove_header_image(self, slot=1):
        key = "header_image" if slot == 1 else "header_image_2"
        old = self.data["settings"].get(key, "")
        if not old:
            return
        if not messagebox.askyesno("確認", "確定要移除裝飾圖片 %d 嗎？" % slot):
            return
        try:
            old_path = os.path.join(decor_dir(), old)
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception:
            pass
        self.data["settings"][key] = ""
        self.save()
        self._load_header_image()
        self._log("移除頂部裝飾圖片 %d" % slot)

    def _remove_all_header_images(self):
        f1 = self.data["settings"].get("header_image", "")
        f2 = self.data["settings"].get("header_image_2", "")
        if not f1 and not f2:
            return
        if not messagebox.askyesno("確認", "確定要移除全部的裝飾圖片嗎？"):
            return
        for fname in (f1, f2):
            if fname:
                try:
                    p = os.path.join(decor_dir(), fname)
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
        self.data["settings"]["header_image"] = ""
        self.data["settings"]["header_image_2"] = ""
        self.save()
        self._load_header_image()
        self._log("移除全部頂部裝飾圖片")

    def _header_image_menu(self, event, slot):
        m = tk.Menu(self.root, tearoff=0, font=(self.F, 10),
                    bg=C_SURFACE, fg=C_TEXT, activebackground=C_PRIMARY_L,
                    activeforeground=C_TEXT, relief="flat", bd=1)
        m.add_command(label="🖼️ 更換第 %d 張" % slot,
                      command=lambda: self._pick_header_image(slot))
        m.add_command(label="🗑️ 移除第 %d 張" % slot,
                      command=lambda: self._remove_header_image(slot))
        m.add_separator()
        m.add_command(label="❌ 移除全部裝飾圖片",
                      command=self._remove_all_header_images)
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    # ----------------------------------
    def _build_notebook(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.grid(row=1, column=0, sticky="nsew", padx=18, pady=(12, 4))
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.tab_contracts = tk.Frame(self.nb, bg=C_BG)
        self.tab_nns       = tk.Frame(self.nb, bg=C_BG)
        self.tab_ship      = tk.Frame(self.nb, bg=C_BG)
        self.tab_stats     = tk.Frame(self.nb, bg=C_BG)
        self.tab_memos     = tk.Frame(self.nb, bg=C_BG)
        self.tab_set       = tk.Frame(self.nb, bg=C_BG)

        self.nb.add(self.tab_contracts, text="   📋  合約流水線   ")
        self.nb.add(self.tab_nns,       text="   💾  NNS 管理   ")
        self.nb.add(self.tab_ship,      text="   📮  寄件 / 領取   ")
        self.nb.add(self.tab_stats,     text="   📊  統計與日誌   ")
        self.nb.add(self.tab_memos,     text="   📝  備忘錄   ")
        self.nb.add(self.tab_set,       text="   ⚙️  設定與備份   ")

        self._build_contracts()
        self._build_nns()
        self._build_ship()
        self._build_stats()
        self._build_memos()
        self._build_settings()

    def _build_footer(self):
        F = self.F
        self.footer = tk.Frame(self.root, bg=C_SURFACE, height=32,
                               highlightbackground=C_BORDER, highlightthickness=1)
        self.footer.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        self.lbl_footer = tk.Label(self.footer, text="🌷 系統就緒", font=(F, 9),
                                   bg=C_SURFACE, fg=C_TEXT_2, anchor="w")
        self.lbl_footer.pack(side="left", padx=14, pady=6)
        self.lbl_footer_right = tk.Label(self.footer, text="本機儲存 · 記得定期備份",
                                         font=(F, 9), bg=C_SURFACE, fg=C_TEXT_3)
        self.lbl_footer_right.pack(side="right", padx=14, pady=6)

    def _show_safe_banner(self):
        self.lbl_safe_mode = tk.Frame(self.root, bg="#FFF0D6",
                                      highlightbackground="#F4D28B",
                                      highlightthickness=1)
        self.lbl_safe_mode.grid(row=1, column=0, sticky="ew", padx=18,
                                pady=(6, 0))
        tk.Label(self.lbl_safe_mode,
                 text="⚠  安全模式：資料檔讀取失敗，目前操作不會寫入原始資料。請從「設定與備份」匯入有效備份。",
                 font=(self.F, 10, "bold"), bg="#FFF0D6", fg="#7A4B00",
                 padx=12, pady=8, anchor="w").pack(fill="x")

    def _on_tab_changed(self, _e=None):
        try:
            tab = self.nb.tab(self.nb.select(), "text").strip()
            count = len(self.data.get("contracts", []))
            self.lbl_footer.configure(text="🌷 %s   ·   目前合約 %d 筆" % (tab, count))
        except Exception:
            pass

    def _section_heading(self, parent, title, subtitle=None):
        frame = tk.Frame(parent, bg=C_BG)
        frame.pack(fill="x", pady=(0, 8))
        tk.Label(frame, text=title, font=(self.F, 17, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(anchor="w")
        if subtitle:
            tk.Label(frame, text=subtitle, font=(self.F, 10),
                     bg=C_BG, fg=C_TEXT_3).pack(anchor="w", pady=(2, 0))
        return frame

    # ─────────────────────────────────
    #  小工具
    # ─────────────────────────────────
    def _btn(self, parent, text, cmd, kind="default"):
        palettes = {
            "primary": (C_PRIMARY, "#FFFFFF", C_PRIMARY_D),
            "success": (C_SUCCESS_L, C_SUCCESS_D, "#C8EAD6"),
            "danger":  (C_DANGER_L, C_DANGER_D, "#F4C0C0"),
            "info":    (C_INFO_L, C_INFO_D, "#C9E0F7"),
            "warning": (C_WARNING_L, C_WARNING_D, "#F8E8AD"),
            "purple":  (C_PURPLE_L, C_PURPLE_D, "#DED5F0"),
            "ghost":   (C_SURFACE, C_TEXT_2, C_PRIMARY_L),
            "default": (C_SURFACE_3, C_TEXT, "#F3D6DE"),
        }
        bg, fg, hover = palettes.get(kind, palettes["default"])
        b = tk.Button(parent, text=text, command=cmd,
                      font=(self.F, 10, "bold"),
                      bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
                      relief="flat", padx=14, pady=8, cursor="hand2",
                      bd=0, highlightthickness=0, takefocus=True)
        b.bind("<Enter>", lambda _e, w=b: w.configure(bg=hover))
        b.bind("<Leave>", lambda _e, w=b, c=bg: w.configure(bg=c))
        return b

    def _style_chip(self, b, active=False):
        if active:
            b.configure(bg=C_PRIMARY, fg="#FFFFFF", font=(self.F, 9, "bold"))
        else:
            b.configure(bg=C_SURFACE_3, fg=C_TEXT, font=(self.F, 9))

    # ══════════════════════════════════
    #  頁籤 1：合約流水線
    # ══════════════════════════════════
    def _build_contracts(self):
        F = self.F
        tab = self.tab_contracts
        tab.grid_rowconfigure(3, weight=1)   # 表格在 row 3
        tab.grid_columnconfigure(0, weight=1)

        # ── row 0：標題在左、搜尋在右 ──
        top = tk.Frame(tab, bg=C_BG)
        top.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 6))

        title_box = tk.Frame(top, bg=C_BG)
        title_box.pack(side="left")
        tk.Label(title_box, text="📋 合約流水線", font=(F, 17, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(side="left")
        tk.Label(title_box, text="追蹤每份合約目前走到哪個階段", font=(F, 10),
                 bg=C_BG, fg=C_TEXT_3).pack(side="left", padx=(12, 0), pady=(4, 0))

        # 搜尋框（右側）
        sf = tk.Frame(top, bg=C_BG)
        sf.pack(side="right")
        tk.Label(sf, text="🔍", font=(F, 12), bg=C_BG, fg=C_TEXT_3).pack(side="left")
        self.ent_search = tk.Entry(sf, font=(F, 11), width=22, bg=C_SURFACE,
                                   fg=C_TEXT, relief="flat", bd=0,
                                   highlightthickness=1,
                                   highlightbackground=C_BORDER,
                                   highlightcolor=C_PRIMARY)
        self.ent_search.pack(side="left", padx=(6, 0), ipady=6)
        self.ent_search.bind("<KeyRelease>", self._on_search)
        self._btn(sf, "清除", self.clear_search, "ghost").pack(side="left", padx=(6, 0))

        # ── row 1：動作按鈕在左、摘要卡片在右 ──
        bar = tk.Frame(tab, bg=C_BG)
        bar.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 6))

        # 左側動作按鈕
        left_btns = tk.Frame(bar, bg=C_BG)
        left_btns.pack(side="left")
        self._btn(left_btns, "➕ 新增案件", self.add_contract, "primary").pack(side="left")
        self._btn(left_btns, "✏️ 編輯", self.edit_contract, "info").pack(side="left", padx=6)
        self._btn(left_btns, "⏩ 推進階段", self.advance_contract, "success").pack(side="left")
        self._btn(left_btns, "↩️ 退回原寄件人", lambda: self.set_stage("rejected"),
                  "danger").pack(side="left", padx=6)
        self._btn(left_btns, "🗑️ 刪除", self.del_contract, "danger").pack(side="left")

        # 右側摘要卡片
        summary = tk.Frame(bar, bg=C_BG)
        summary.pack(side="right")
        self.summary_values = {}
        summary_specs = [
            ("total",     "📚 全部",     C_PRIMARY_L),
            ("received",  "🆕 待檢查",   "#FFF0F4"),
            ("to_leader", "📮 待送組長", C_WARNING_L),
            ("notify",    "📦 待通知",   "#FFF1D9"),
            ("nns",       "🗂️ NNS待辦", C_PURPLE_L),
        ]
        for key, title, color in summary_specs:
            tag = tk.Frame(summary, bg=color, highlightbackground=C_BORDER,
                           highlightthickness=1, padx=10, pady=4)
            tag.pack(side="left", padx=(0, 8))
            tk.Label(tag, text=title, font=(F, 9), bg=color,
                     fg=C_TEXT_2).pack(side="left")
            v = tk.Label(tag, text="0", font=(F, 12, "bold"), bg=color, fg=C_TEXT)
            v.pack(side="left", padx=(6, 0))
            self.summary_values[key] = v

        # ── row 2：chips + 表格（用 body 容器分兩列） ──
        body = tk.Frame(tab, bg=C_BG)
        body.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 12))
        body.grid_rowconfigure(1, weight=1)
        body.grid_columnconfigure(0, weight=1)

        # chips（body row 0）
        chips = tk.Frame(body, bg=C_BG)
        chips.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.chip_btns = {}

        def mkchip(text, cmd, key):
            b = tk.Button(chips, text=text, font=(F, 9),
                          bg=C_SURFACE_3, fg=C_TEXT, relief="flat",
                          padx=8, pady=4, cursor="hand2", bd=0,
                          highlightthickness=0, command=cmd)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=C_PRIMARY_L))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=w.cget("bg")))
            return b

        allbtn = mkchip("📋 全部", lambda: self.set_filter("all"), "all")
        allbtn.pack(side="left", padx=(0, 3))
        self.chip_btns["all"] = allbtn

        for key, name, _ in STAGES:
            b = mkchip(name, lambda k=key: self.set_filter(k), key)
            b.pack(side="left", padx=(0, 3))
            self.chip_btns[key] = b
        self._style_chip(self.chip_btns["all"], True)

        # 表格（body row 1）
        tf = tk.Frame(body, bg=C_SURFACE, highlightbackground=C_BORDER,
                      highlightthickness=1)
        tf.grid(row=1, column=0, sticky="nsew")
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("serial", "code", "name", "sales", "dtype", "stage",
                "recv", "send", "ret", "ok_mail", "card", "notes")
        heads = ("編號", "客戶代碼", "客戶名稱", "業務", "類型", "階段",
                 "收件日", "送件日", "回件日", "-OK", "製卡", "備註")
        widths = (60, 110, 190, 90, 110, 140, 135, 135, 135, 60, 60, 260)

        self.tv_contracts = ttk.Treeview(tf, columns=cols, show="headings",
                                         selectmode="extended")
        for c, h, w in zip(cols, heads, widths):
            self.tv_contracts.heading(c, text=h)
            self.tv_contracts.column(c, width=w, minwidth=int(w * 0.7),
                                     anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tv_contracts.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tv_contracts.xview)
        self.tv_contracts.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tv_contracts.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        for key, _, color in STAGES:
            self.tv_contracts.tag_configure(key, background=color)

        self.tv_contracts.bind("<Double-1>", lambda e: self.edit_contract())
        self.tv_contracts.bind("<Button-3>", self._contract_menu)

        # ── row 3：狀態列 ──
        self.lbl_c_status = tk.Label(tab, text="", font=(F, 9),
                                     bg=C_BG, fg=C_TEXT_3, anchor="w")
        self.lbl_c_status.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 10))

    def _contract_menu(self, event):
        iid = self.tv_contracts.identify_row(event.y)
        if not iid:
            return
        if iid not in self.tv_contracts.selection():
            self.tv_contracts.selection_set(iid)
        m = tk.Menu(self.root, tearoff=0, font=(self.F, 10),
                    bg=C_SURFACE, fg=C_TEXT, activebackground=C_PRIMARY_L,
                    activeforeground=C_TEXT, relief="flat", bd=1)
        m.add_command(label="✏️ 編輯", command=self.edit_contract)
        m.add_command(label="⏩ 推進階段", command=self.advance_contract)
        m.add_separator()
        for key, name, _ in STAGES:
            m.add_command(label="移至 " + name,
                          command=lambda k=key: self.set_stage(k))
        m.add_separator()
        m.add_command(label="🗑️ 刪除", command=self.del_contract)
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    def _on_search(self, _e=None):
        self.search_kw = self.ent_search.get().strip().lower()
        self.refresh_contracts()

    def clear_search(self):
        self.ent_search.delete(0, "end")
        self.search_kw = ""
        self.refresh_contracts()

    def set_filter(self, key):
        self.filter_stage = key
        for k, b in self.chip_btns.items():
            self._style_chip(b, k == key)
        self.refresh_contracts()

    def get_case(self, cid):
        for c in self.data["contracts"]:
            if c["id"] == cid:
                return c
        return None

    def _log(self, text):
        self.data["log"].insert(0, {"time": now_str(), "text": text})
        self.data["log"] = self.data["log"][:500]

    def add_contract(self):
        dlg = ContractDialog(self.root, self, None)
        self.root.wait_window(dlg)
        if not dlg.result or dlg.result == "__DELETE__":
            return
        self.data["settings"]["serial"] = self.data["settings"].get("serial", 0) + 1
        rec = dlg.result
        rec["id"] = str(uuid.uuid4())
        rec["serial"] = self.data["settings"]["serial"]
        rec["created"] = now_str()
        rec["notify_date"] = ""
        rec["deliver_date"] = ""
        rec["hold"] = False
        rec["nns_done"] = False
        rec["history"] = [{"time": now_str(), "text": "建立案件"}]
        self.data["contracts"].append(rec)
        self._log("新增案件 #%s %s %s" % (rec["serial"], rec["code"], rec["name"]))
        self.save()
        self.refresh_all()

    def edit_contract(self):
        sel = self.tv_contracts.selection()
        if not sel:
            messagebox.showinfo("提醒", "請先選取一筆案件。")
            return
        cid = sel[0]
        c = self.get_case(cid)
        if not c:
            return
        dlg = ContractDialog(self.root, self, c)
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        if dlg.result == "__DELETE__":
            self.data["contracts"] = [x for x in self.data["contracts"] if x["id"] != cid]
            self._log("刪除案件 %s" % c.get("name", ""))
            self.save()
            self.refresh_all()
            return
        old_stage = c.get("stage")
        c.update(dlg.result)
        if c.get("stage") != old_stage:
            c.setdefault("history", []).append(
                {"time": now_str(), "text": "階段 %s → %s" % (
                    STAGE_MAP.get(old_stage, ("?",))[0],
                    STAGE_MAP.get(c["stage"], ("?",))[0])})
        self.save()
        self.refresh_all()

    def del_contract(self):
        sel = self.tv_contracts.selection()
        if not sel:
            return
        if not messagebox.askyesno("確認刪除", "確定刪除選取的 %d 筆案件？" % len(sel)):
            return
        self.data["contracts"] = [c for c in self.data["contracts"] if c["id"] not in sel]
        self._log("刪除 %d 筆案件" % len(sel))
        self.save()
        self.refresh_all()

    def advance_contract(self):
        sel = self.tv_contracts.selection()
        if not sel:
            messagebox.showinfo("提醒", "請先選取案件。")
            return
        cnt = 0
        for cid in sel:
            c = self.get_case(cid)
            if not c:
                continue
            nxt = FORWARD.get(c.get("stage"))
            if nxt:
                self._enter_stage(c, nxt)
                cnt += 1
        if cnt == 0:
            messagebox.showinfo("提醒", "選取的案件已在分支階段，請用右鍵手動調整。")
        self.save()
        self.refresh_all()

    def set_stage(self, key):
        sel = self.tv_contracts.selection()
        if not sel:
            return
        for cid in sel:
            c = self.get_case(cid)
            if c:
                self._enter_stage(c, key)
        self.save()
        self.refresh_all()

    def _enter_stage(self, c, key):
        old = c.get("stage")
        if old == key:
            return
        c["stage"] = key
        if key == "printing" and not c.get("send_date"):
            c["send_date"] = now_str()
        if key == "returned" and not c.get("return_date"):
            c["return_date"] = now_str()
        if key in ("returned", "registered", "notify", "nns_pending"):
            c["ship_visited"] = True
        if key == "nns_pending":
            c["nns_visited"] = True
        if key == "leader_back":
            c["ok_mail"] = False
        c.setdefault("history", []).append({
            "time": now_str(),
            "text": "階段 %s → %s" % (STAGE_MAP.get(old, ("?",))[0],
                                     STAGE_MAP.get(key, ("?",))[0])
        })
        self._log("%s：%s → %s" % (c.get("name", ""),
                                   STAGE_MAP.get(old, ("?",))[0],
                                   STAGE_MAP.get(key, ("?",))[0]))

    def refresh_contracts(self):
        tv = self.tv_contracts
        tv.delete(*tv.get_children())
        kw = self.search_kw
        rows = []
        for c in self.data["contracts"]:
            if self.filter_stage != "all" and c.get("stage") != self.filter_stage:
                continue
            if kw:
                blob = " ".join(str(c.get(k, "")) for k in
                                ("code", "name", "sales", "dtype", "notes")).lower()
                if kw not in blob:
                    continue
            rows.append(c)
        rows.sort(key=lambda x: (x.get("recv_date", ""), x.get("serial", 0)))

        for c in rows:
            ok = "✅" if c.get("ok_mail") else "—"
            card = "💳" if c.get("has_card") else "—"
            stage_name = STAGE_MAP.get(c.get("stage"), ("?", ""))[0]
            tv.insert("", "end", iid=c["id"],
                      values=(c.get("serial", ""),
                              c.get("code", ""),
                              c.get("name", ""),
                              c.get("sales", ""),
                              c.get("dtype", ""),
                              stage_name,
                              c.get("recv_date", ""),
                              c.get("send_date", ""),
                              c.get("return_date", ""),
                              ok, card, c.get("notes", "")),
                      tags=(c.get("stage", "received"),))

        counts = {}
        for c in self.data["contracts"]:
            counts[c.get("stage")] = counts.get(c.get("stage"), 0) + 1
        total = len(self.data["contracts"])
        if hasattr(self, "summary_values"):
            self.summary_values["total"].configure(text=str(total))
            for stage_key in ("received", "to_leader", "notify"):
                cnt = counts.get(stage_key, 0)
                self.summary_values[stage_key].configure(text=str(cnt))
            nns_count = sum(1 for item in self.data.get("nns", [])
                            if not (item.get("replied") and item.get("done_date")))
            self.summary_values["nns"].configure(text=str(nns_count))

        self.chip_btns["all"].configure(text="📋 全部 (%d)" % total)
        for key, name, _ in STAGES:
            self.chip_btns[key].configure(text="%s (%d)" % (name, counts.get(key, 0)))

        self.lbl_c_status.configure(
            text="顯示 %d 筆 / 共 %d 筆   ·   資料位置：%s" % (len(rows), total, data_file()))

    # ══════════════════════════════════
    #  頁籤 2：NNS
    # ══════════════════════════════════
    def _build_nns(self):
        F = self.F
        tab = self.tab_nns
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        title_row = tk.Frame(tab, bg=C_BG)
        title_row.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 4))
        tk.Label(title_row, text="💾 NNS 登記管理", font=(F, 17, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(side="left")
        tk.Label(title_row, text="集中追蹤新合約登記與資料變更", font=(F, 10),
                 bg=C_BG, fg=C_TEXT_3).pack(side="left", padx=(12, 0), pady=(4, 0))

        bar = tk.Frame(tab, bg=C_BG)
        bar.grid(row=1, column=0, sticky="ew", padx=22, pady=(6, 10))
        self._btn(bar, "➕ 新增 NNS 紀錄", self.add_nns, "primary").pack(side="left")
        self._btn(bar, "✏️ 編輯", self.edit_nns, "info").pack(side="left", padx=6)
        self._btn(bar, "✅ 標記完成並回信", self.done_nns, "success").pack(side="left")
        self._btn(bar, "🗑️ 刪除", self.del_nns, "danger").pack(side="left", padx=6)
        self._btn(bar, "🔄 從合約帶入", self.pull_from_contracts,
                  "warning").pack(side="left", padx=6)

        tf = tk.Frame(tab, bg=C_SURFACE, highlightbackground=C_BORDER,
                      highlightthickness=1)
        tf.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 6))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("code", "name", "sales", "kind", "req", "done", "replied", "note")
        heads = ("客戶代碼", "客戶名稱", "業務", "類型", "收件日", "完成日", "已回信 -OK", "備註")
        widths = (120, 200, 110, 150, 155, 155, 110, 260)

        self.tv_nns = ttk.Treeview(tf, columns=cols, show="headings",
                                   selectmode="extended")
        for c, h, w in zip(cols, heads, widths):
            self.tv_nns.heading(c, text=h)
            self.tv_nns.column(c, width=w, minwidth=int(w * 0.7), anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tv_nns.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tv_nns.xview)
        self.tv_nns.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tv_nns.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tv_nns.tag_configure("pending", background=C_WARNING_L)
        self.tv_nns.tag_configure("done", background=C_SUCCESS_L)
        self.tv_nns.tag_configure("case", background=C_PURPLE_L)
        self.tv_nns.tag_configure("case_done", background="#DED5F0")
        self.tv_nns.bind("<Double-1>", lambda e: self.edit_nns())
        self.tv_nns.bind("<Button-3>", self._nns_menu)

        tk.Label(tab, text="💡 提示：新合約回件後，NNS 登記會自動列在這裡；變更需求完成後記得回信並標記 -OK。",
                 font=(F, 9), bg=C_BG, fg=C_TEXT_3, anchor="w"
                 ).grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 10))

    def add_nns(self):
        dlg = NNSDialog(self.root, self, None)
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        rec = dlg.result
        rec["id"] = str(uuid.uuid4())
        self.data["nns"].append(rec)
        self._log("新增 NNS：%s %s" % (rec["code"], rec["name"]))
        self.save()
        self.refresh_all()

    def edit_nns(self):
        sel = self.tv_nns.selection()
        if not sel:
            return
        rid = sel[0]
        if rid.startswith("case_"):
            cid = rid[5:]
            c = self.get_case(cid)
            if not c:
                return
            dlg = ContractDialog(self.root, self, c)
            self.root.wait_window(dlg)
            if not dlg.result or dlg.result == "__DELETE__":
                return
            c.update(dlg.result)
            self.save()
            self.refresh_all()
            return
        rec = next((r for r in self.data["nns"] if r["id"] == rid), None)
        if not rec:
            return
        dlg = NNSDialog(self.root, self, rec)
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        rec.update(dlg.result)
        self.save()
        self.refresh_all()

    def done_nns(self):
        sel = self.tv_nns.selection()
        if not sel:
            return
        for rid in sel:
            if rid.startswith("case_"):
                cid = rid[5:]
                c = self.get_case(cid)
                if c:
                    c["nns_done"] = True
                    c["nns_visited"] = True
                    if not c.get("done_date"):
                        c["done_date"] = now_str()
                    self._log("NNS 完成（合約案件）：%s %s" % (
                        c.get("code", ""), c.get("name", "")))
            else:
                rec = next((r for r in self.data["nns"] if r["id"] == rid), None)
                if rec:
                    if not rec.get("done_date"):
                        rec["done_date"] = now_str()
                    rec["replied"] = True
                    self._log("NNS 完成：%s %s" % (
                        rec.get("code", ""), rec.get("name", "")))
        self.save()
        self.refresh_all()

    def del_nns(self):
        sel = self.tv_nns.selection()
        if not sel:
            return
        case_ids = [s for s in sel if s.startswith("case_")]
        manual_ids = [s for s in sel if not s.startswith("case_")]
        if case_ids and not manual_ids:
            messagebox.showinfo("提醒", "來自合約流水線的案件，請從『📋 合約流水線』頁面處理。")
            return
        if not manual_ids:
            return
        msg = "確定刪除選取的 %d 筆 NNS 紀錄？" % len(manual_ids)
        if case_ids:
            msg += "\n（其中 %d 筆來自合約的案件將被略過）" % len(case_ids)
        if not messagebox.askyesno("確認刪除", msg):
            return
        self.data["nns"] = [r for r in self.data["nns"] if r["id"] not in manual_ids]
        self.save()
        self.refresh_all()

    def _nns_menu(self, event):
        iid = self.tv_nns.identify_row(event.y)
        if not iid:
            return
        if iid not in self.tv_nns.selection():
            self.tv_nns.selection_set(iid)
        m = tk.Menu(self.root, tearoff=0, font=(self.F, 10),
                    bg=C_SURFACE, fg=C_TEXT, activebackground=C_PRIMARY_L,
                    activeforeground=C_TEXT, relief="flat", bd=1)
        m.add_command(label="✏️ 編輯（雙擊也行）", command=self.edit_nns)
        m.add_separator()
        m.add_command(label="⏳ 標記為待處理",
                      command=lambda: self._nns_set_state(iid, "pending"))
        m.add_command(label="✅ 標記完成並回信",
                      command=lambda: self._nns_set_state(iid, "done"))
        m.add_separator()
        m.add_command(label="🗑️ 刪除", command=self.del_nns)
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    def _nns_set_state(self, iid, state):
        is_case = iid.startswith("case_")
        if is_case:
            cid = iid[5:]
            rec = self.get_case(cid)
        else:
            rec = next((r for r in self.data["nns"] if r["id"] == iid), None)
        if not rec:
            return
        name = "%s %s" % (rec.get("code", ""), rec.get("name", ""))
        if state == "pending":
            rec["done_date"] = ""
            if is_case:
                rec["nns_done"] = False
            else:
                rec["replied"] = False
            self._log("NNS 標記為待處理：%s" % name)
        elif state == "done":
            rec["done_date"] = now_str()
            if is_case:
                rec["nns_done"] = True
                rec["nns_visited"] = True
            else:
                rec["replied"] = True
            self._log("NNS 完成並回信：%s" % name)
        self.save()
        self.refresh_all()

    def pull_from_contracts(self):
        added = 0
        exist = {(r.get("code", ""), r.get("name", "")) for r in self.data["nns"]}
        for c in self.data["contracts"]:
            if c.get("stage") != "nns_pending":
                continue
            key = (c.get("code", ""), c.get("name", ""))
            if key in exist:
                continue
            self.data["nns"].append({
                "id": str(uuid.uuid4()),
                "code": c.get("code", ""),
                "name": c.get("name", ""),
                "sales": c.get("sales", ""),
                "kind": "新合約登記",
                "req_date": c.get("return_date") or today_str(),
                "done_date": "",
                "replied": False,
                "note": "由合約流水線轉存",
            })
            exist.add(key)
            added += 1
        if added:
            self._log("轉存 %d 筆 NNS 待登記" % added)
        self.save()
        self.refresh_all()
        messagebox.showinfo("完成",
                            "已轉存 %d 筆『需NNS登記』案件到 NNS 清單。\n"
                            "（原本的自動顯示仍會保留，此按鈕是另外建立獨立紀錄）" % added)

    def refresh_nns(self):
        tv = self.tv_nns
        tv.delete(*tv.get_children())
        rows = []
        for r in self.data["nns"]:
            rows.append(("manual", r))
        for c in self.data["contracts"]:
            if c.get("stage") == "nns_pending" or c.get("nns_visited") or c.get("nns_done"):
                rows.append(("case", c))

        def _key(item):
            src, r = item
            if src == "manual":
                replied = bool(r.get("replied") and r.get("done_date"))
                req = r.get("req_date", "")
            else:
                is_done = bool(r.get("nns_done")) or r.get("stage") == "done"
                replied = is_done
                req = r.get("return_date", "")
            return (replied, req)
        rows.sort(key=_key)

        for src, r in rows:
            if src == "manual":
                iid = r["id"]
                replied_done = bool(r.get("replied") and r.get("done_date"))
                tag = "done" if replied_done else "pending"
                kind = r.get("kind", "")
                req = r.get("req_date", "")
                done = r.get("done_date", "")
                replied_txt = "✅ 是" if r.get("replied") else "⏳ 否"
                note = r.get("note", "")
            else:
                iid = "case_" + r["id"]
                st = r.get("stage", "")
                is_done = bool(r.get("nns_done")) or st == "done"
                tag = "case_done" if is_done else "case"
                kind = "新合約登記（合約案件）"
                req = r.get("return_date", "")
                if st == "done" and r.get("done_date"):
                    done = r.get("done_date") + "（已結案）"
                elif st == "done":
                    done = "已結案"
                elif is_done:
                    done = r.get("done_date", "")
                else:
                    done = ""
                replied_txt = "✅ 是" if is_done else "⏳ 否"
                note = "（來自合約流水線）" + r.get("notes", "")

            tv.insert("", "end", iid=iid,
                      values=(r.get("code", ""), r.get("name", ""),
                              r.get("sales", ""), kind, req, done,
                              replied_txt, note),
                      tags=(tag,))

    # ══════════════════════════════════
    #  頁籤 3：寄件 / 領取
    # ══════════════════════════════════
    def _build_ship(self):
        F = self.F
        tab = self.tab_ship
        tab.grid_rowconfigure(3, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        title_row = tk.Frame(tab, bg=C_BG)
        title_row.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 4))
        tk.Label(title_row, text="📮 寄件與領取", font=(F, 17, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(side="left")
        tk.Label(title_row, text="集中處理通知、簽領、寄出與結案", font=(F, 10),
                 bg=C_BG, fg=C_TEXT_3).pack(side="left", padx=(12, 0), pady=(4, 0))

        banner = tk.Frame(tab, bg=C_WARNING_L,
                          highlightbackground="#F0DFA8", highlightthickness=1)
        banner.grid(row=1, column=0, sticky="ew", padx=22, pady=(6, 10))
        tk.Label(banner,
                 text="📮 公司寄件時段：早上 10:00 與下午 14:00   |   最晚必須在 14:00 前交給總機",
                 font=(F, 10, "bold"), bg=C_WARNING_L, fg=C_WARNING_D,
                 pady=10).pack(anchor="w", padx=16)

        bar = tk.Frame(tab, bg=C_BG)
        bar.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 10))
        self._btn(bar, "📨 標記已通知業務", self.notify_sales, "info").pack(side="left")
        self._btn(bar, "✍️ 北區已簽領", self.pickup_north, "success").pack(side="left", padx=6)
        self._btn(bar, "📦 中/南區已寄出", self.mail_out, "purple").pack(side="left")
        self._btn(bar, "↩️ 取消簽領/寄出", self.cancel_deliver, "ghost").pack(side="left", padx=6)
        self._btn(bar, "✅ 結案", lambda: self.set_ship_done(), "success").pack(side="left")

        rf = tk.Frame(bar, bg=C_BG)
        rf.pack(side="right")
        tk.Label(rf, text="區域：", font=(F, 10), bg=C_BG, fg=C_TEXT).pack(side="left")
        self.cb_region = ttk.Combobox(rf, values=["全部"] + REGIONS,
                                      state="readonly", width=8, font=(F, 10))
        self.cb_region.set("全部")
        self.cb_region.pack(side="left")
        self.cb_region.bind("<<ComboboxSelected>>", lambda e: self.refresh_ship())

        tf = tk.Frame(tab, bg=C_SURFACE, highlightbackground=C_BORDER,
                      highlightthickness=1)
        tf.grid(row=3, column=0, sticky="nsew", padx=22, pady=(0, 6))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("code", "name", "sales", "region", "dtype", "card", "notify", "status")
        heads = ("客戶代碼", "客戶名稱", "業務", "區域", "類型", "製卡", "通知日", "狀態")
        widths = (120, 240, 110, 90, 130, 80, 140, 240)

        self.tv_ship = ttk.Treeview(tf, columns=cols, show="headings",
                                    selectmode="extended")
        for c, h, w in zip(cols, heads, widths):
            self.tv_ship.heading(c, text=h)
            self.tv_ship.column(c, width=w, minwidth=int(w * 0.7), anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tv_ship.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tv_ship.xview)
        self.tv_ship.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tv_ship.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tv_ship.tag_configure("north", background="#EAF5FF")
        self.tv_ship.tag_configure("other", background="#FFF6E5")
        self.tv_ship.bind("<Double-1>", lambda e: self.edit_ship())
        self.tv_ship.bind("<Button-3>", self._ship_menu)

        tk.Label(tab,
                 text="💡 雙擊案件可編輯通知日 / 領取寄出日   |   北區：簽名領回   |   中/南區：需先做封面函，有製卡的客戶要一起寄出。",
                 font=(F, 9), bg=C_BG, fg=C_TEXT_3, anchor="w"
                 ).grid(row=4, column=0, sticky="ew", padx=22, pady=(0, 10))

    def _ship_rows(self):
        region = self.cb_region.get()
        out = []
        for c in self.data["contracts"]:
            st = c.get("stage", "")
            show = st in ("returned", "registered", "notify", "nns_pending")
            if not show:
                if c.get("ship_visited"):
                    show = True
                elif st == "done" and (c.get("notify_date") or c.get("deliver_date")):
                    show = True
            if not show:
                continue
            if region != "全部" and c.get("region") != region:
                continue
            out.append(c)
        order = {"returned": 0, "registered": 1, "notify": 2,
                 "nns_pending": 3, "done": 4}
        out.sort(key=lambda x: (order.get(x.get("stage", ""), 99),
                                x.get("recv_date", ""), x.get("serial", 0)))
        return out

    def refresh_ship(self):
        tv = self.tv_ship
        tv.delete(*tv.get_children())
        for c in self._ship_rows():
            region = c.get("region", "")
            card = "💳 有" if c.get("has_card") else "—"
            st = c.get("stage", "")
            if st == "done":
                status = "✅ 已結案"
                if c.get("deliver_date"):
                    status += " " + c.get("deliver_date", "")
            elif c.get("deliver_date"):
                if region == "北區":
                    status = "✅ 北區已簽領 " + c.get("deliver_date", "")
                elif region in ("中區", "南區"):
                    status = "📦 已寄出 " + c.get("deliver_date", "")
                else:
                    status = "✅ 已領取/寄出 " + c.get("deliver_date", "")
            elif c.get("hold"):
                status = "🚫 業務通知先不寄出"
            elif c.get("notify_date"):
                status = "📨 已通知，待領取/寄送"
            else:
                status = "⏳ 待通知業務"

            tag = "north" if region == "北區" else "other"
            tv.insert("", "end", iid=c["id"],
                      values=(c.get("code", ""), c.get("name", ""),
                              c.get("sales", ""), region, c.get("dtype", ""),
                              card, c.get("notify_date", ""), status),
                      tags=(tag,))

    def _ship_sel(self):
        sel = self.tv_ship.selection()
        if not sel:
            messagebox.showinfo("提醒", "請先選取案件。")
            return []
        return [self.get_case(i) for i in sel if self.get_case(i)]

    def notify_sales(self):
        rows = self._ship_sel()
        if not rows:
            return
        for c in rows:
            c["notify_date"] = c.get("notify_date") or today_str()
            self._log("通知業務領取：%s %s" % (c.get("code", ""), c.get("name", "")))
        self.save()
        self.refresh_all()

    def pickup_north(self):
        rows = self._ship_sel()
        if not rows:
            return
        for c in rows:
            c["deliver_date"] = now_str()
            c["ship_visited"] = True
            self._log("北區簽領：%s %s" % (c.get("code", ""), c.get("name", "")))
        self.save()
        self.refresh_all()

    def mail_out(self):
        rows = self._ship_sel()
        if not rows:
            return
        for c in rows:
            c["deliver_date"] = now_str()
            c["ship_visited"] = True
            self._log("中/南區寄出：%s %s" % (c.get("code", ""), c.get("name", "")))
        self.save()
        self.refresh_all()

    def set_ship_done(self):
        rows = self._ship_sel()
        if not rows:
            return
        for c in rows:
            c["stage"] = "done"
            c["ship_visited"] = True
            if not c.get("deliver_date"):
                c["deliver_date"] = now_str()
            self._log("結案：%s %s" % (c.get("code", ""), c.get("name", "")))
        self.save()
        self.refresh_all()

    def cancel_deliver(self):
        rows = self._ship_sel()
        if not rows:
            return
        if not messagebox.askyesno(
                "確認取消",
                "確定要取消選取案件的「簽領 / 寄出」狀態嗎？\n（會回到『待通知業務』）"):
            return
        n = 0
        for c in rows:
            if c.get("deliver_date"):
                c["deliver_date"] = ""
                n += 1
                self._log("取消簽領/寄出：%s %s" % (c.get("code", ""), c.get("name", "")))
        if n == 0:
            messagebox.showinfo("提醒", "選取的案件目前沒有「簽領 / 寄出」記錄。")
        self.save()
        self.refresh_all()

    def edit_ship(self):
        sel = self.tv_ship.selection()
        if not sel:
            messagebox.showinfo("提醒", "請先選取一筆案件。")
            return
        c = self.get_case(sel[0])
        if not c:
            return
        dlg = ShipDialog(self.root, self, c)
        self.root.wait_window(dlg)

    def _ship_menu(self, event):
        iid = self.tv_ship.identify_row(event.y)
        if not iid:
            return
        if iid not in self.tv_ship.selection():
            self.tv_ship.selection_set(iid)
        c = self.get_case(iid)
        if not c:
            return
        is_hold = bool(c.get("hold"))
        m = tk.Menu(self.root, tearoff=0, font=(self.F, 10),
                    bg=C_SURFACE, fg=C_TEXT, activebackground=C_PRIMARY_L,
                    activeforeground=C_TEXT, relief="flat", bd=1)
        m.add_command(label="✏️ 編輯（雙擊也行）", command=self.edit_ship)
        m.add_separator()
        m.add_command(label="⏳ 待通知業務",
                      command=lambda: self._ship_set_state(iid, "pending"))
        m.add_command(label="📨 標記已通知業務",
                      command=lambda: self._ship_set_state(iid, "notified"))
        m.add_command(label="🚫 業務通知先不寄出",
                      command=lambda: self._ship_set_state(iid, "hold"))
        if is_hold:
            m.add_command(label="🔄 取消暫緩寄出",
                          command=lambda: self._ship_set_state(iid, "unhold"))
        m.add_separator()
        m.add_command(label="✍️ 北區已簽領",
                      command=lambda: self._ship_set_state(iid, "delivered"))
        m.add_command(label="📦 中/南區已寄出",
                      command=lambda: self._ship_set_state(iid, "delivered"))
        m.add_command(label="↩️ 取消簽領/寄出",
                      command=lambda: self._ship_set_state(iid, "notified"))
        m.add_separator()
        m.add_command(label="✅ 結案",
                      command=lambda: self._ship_set_state(iid, "done"))
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    def _ship_set_state(self, cid, state):
        c = self.get_case(cid)
        if not c:
            return
        name = "%s %s" % (c.get("code", ""), c.get("name", ""))
        c["ship_visited"] = True
        if state == "pending":
            c["notify_date"] = ""
            c["deliver_date"] = ""
            c["hold"] = False
            self._log("寄件狀態→待通知：%s" % name)
        elif state == "notified":
            if not c.get("notify_date"):
                c["notify_date"] = now_str()
            c["deliver_date"] = ""
            c["hold"] = False
            self._log("寄件狀態→已通知：%s" % name)
        elif state == "hold":
            if not c.get("notify_date"):
                c["notify_date"] = now_str()
            c["deliver_date"] = ""
            c["hold"] = True
            self._log("寄件狀態→業務通知先不寄出：%s" % name)
        elif state == "unhold":
            c["hold"] = False
            self._log("取消暫緩寄出：%s" % name)
        elif state == "delivered":
            if not c.get("notify_date"):
                c["notify_date"] = now_str()
            c["deliver_date"] = now_str()
            c["hold"] = False
            self._log("寄件狀態→已領取/寄出：%s" % name)
        elif state == "done":
            if not c.get("deliver_date"):
                c["deliver_date"] = now_str()
            c["stage"] = "done"
            c["hold"] = False
            self._log("結案：%s" % name)
        self.save()
        self.refresh_all()

    # ══════════════════════════════════
    #  頁籤 4：備忘錄（響應式卡片）
    # ══════════════════════════════════
    def _build_memos(self):
        F = self.F
        tab = self.tab_memos
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        title_row = tk.Frame(tab, bg=C_BG)
        title_row.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 4))
        tk.Label(title_row, text="📝 工作備忘錄", font=(F, 17, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(side="left")
        tk.Label(title_row, text="臨時交辦、待確認事項與提醒；卡片會隨視窗寬度自動排列",
                 font=(F, 10), bg=C_BG, fg=C_TEXT_3).pack(side="left", padx=(12, 0), pady=(4, 0))

        bar = tk.Frame(tab, bg=C_BG)
        bar.grid(row=1, column=0, sticky="ew", padx=22, pady=(6, 10))
        self._btn(bar, "➕ 新增備忘錄", self.add_memo, "primary").pack(side="left")
        self._btn(bar, "🗑️ 清除已完成", self.del_done_memos, "ghost").pack(side="left", padx=6)

        rf = tk.Frame(bar, bg=C_BG)
        rf.pack(side="right")
        self.memo_show_done = tk.BooleanVar(value=True)
        tk.Checkbutton(rf, text="顯示已完成", variable=self.memo_show_done,
                       bg=C_BG, activebackground=C_BG, fg=C_TEXT,
                       selectcolor=C_SURFACE, font=(F, 10),
                       cursor="hand2",
                       command=self.refresh_memos).pack(side="left")

        board = tk.Frame(tab, bg=C_SURFACE_2,
                         highlightbackground=C_BORDER, highlightthickness=1)
        board.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 12))
        board.grid_rowconfigure(0, weight=1)
        board.grid_columnconfigure(0, weight=1)

        self.memo_canvas = tk.Canvas(board, bg=C_SURFACE_2,
                                     highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(board, orient="vertical", command=self.memo_canvas.yview)
        self.memo_canvas.configure(yscrollcommand=vsb.set)

        self.memo_canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.memo_inner = tk.Frame(self.memo_canvas, bg=C_SURFACE_2)
        self._memo_inner_id = self.memo_canvas.create_window(
            (0, 0), window=self.memo_inner, anchor="nw")

        self.memo_canvas.bind("<Configure>", self._on_memo_canvas_configure)
        self.memo_inner.bind(
            "<Configure>",
            lambda e: self.memo_canvas.configure(
                scrollregion=self.memo_canvas.bbox("all")))

        def _on_mousewheel(e):
            self.memo_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.memo_canvas.bind(
            "<Enter>",
            lambda e: self.memo_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.memo_canvas.bind(
            "<Leave>",
            lambda e: self.memo_canvas.unbind_all("<MouseWheel>"))

    def _on_memo_canvas_configure(self, e):
        try:
            self.memo_canvas.itemconfig(self._memo_inner_id, width=e.width)
        except Exception:
            pass
        cols = max(1, e.width // 320)
        if cols != self._memo_cols:
            self._memo_cols = cols
            if self._memo_resize_job:
                try:
                    self.root.after_cancel(self._memo_resize_job)
                except Exception:
                    pass
            self._memo_resize_job = self.root.after(80, self.refresh_memos)

    def refresh_memos(self):
        self._memo_resize_job = None
        inner = self.memo_inner
        for w in inner.winfo_children():
            w.destroy()

        memos = list(self.data.get("memos", []))
        if not self.memo_show_done.get():
            memos = [m for m in memos if not m.get("done")]

        memos.sort(key=lambda m: m.get("updated", m.get("created", "")), reverse=True)
        memos.sort(key=lambda m: bool(m.get("done")))
        memos.sort(key=lambda m: not bool(m.get("pinned")))

        cols = max(1, self._memo_cols)
        for c in range(cols):
            inner.grid_columnconfigure(c, weight=1, uniform="memo")

        if not memos:
            empty = tk.Frame(inner, bg=C_SURFACE_2)
            empty.grid(row=0, column=0, columnspan=cols, pady=80, sticky="ew")
            tk.Label(empty, text="📭", font=(self.F, 48),
                     bg=C_SURFACE_2, fg="#D8CFC4").pack()
            tk.Label(empty, text="目前沒有備忘錄",
                     font=(self.F, 13, "bold"),
                     bg=C_SURFACE_2, fg=C_TEXT_2).pack(pady=(10, 2))
            tk.Label(empty, text="按上方「➕ 新增備忘錄」開始記錄吧",
                     font=(self.F, 10),
                     bg=C_SURFACE_2, fg=C_TEXT_3).pack()
            return

        for i, m in enumerate(memos):
            row = i // cols
            col = i % cols
            card = self._make_memo_card(inner, m)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    def _make_memo_card(self, parent, memo):
        F = self.F
        color = memo.get("color", "#FFF6D6")
        done = bool(memo.get("done"))
        pinned = bool(memo.get("pinned"))

        if done:
            bg = C_SURFACE_3
            title_fg = C_TEXT_3
            content_fg = C_TEXT_3
            topbar_color = C_BORDER_2
        else:
            bg = color
            title_fg = C_TEXT
            content_fg = C_TEXT_2
            topbar_color = C_PRIMARY_D

        wrapper = tk.Frame(parent, bg=C_BORDER,
                           highlightbackground=C_BORDER, highlightthickness=1)
        card = tk.Frame(wrapper, bg=bg)
        card.pack(fill="both", expand=True, padx=1, pady=(1, 2))

        topbar = tk.Frame(card, bg=topbar_color, height=4)
        topbar.pack(fill="x")
        if pinned:
            topbar.configure(bg="#E8B923")

        head = tk.Frame(card, bg=bg)
        head.pack(fill="x", padx=14, pady=(10, 0))

        var = tk.BooleanVar(value=done)

        def _toggle():
            memo["done"] = var.get()
            memo["updated"] = now_str()
            self.save()
            self.refresh_memos()

        cb = tk.Checkbutton(head, variable=var, command=_toggle,
                            bg=bg, activebackground=bg,
                            fg=C_TEXT, selectcolor=C_SURFACE,
                            font=(F, 12), cursor="hand2",
                            bd=0, highlightthickness=0)
        cb.pack(side="left")

        title_text = memo.get("title", "")
        if done:
            title_text = "✓ " + title_text
        if pinned:
            title_text = "📌 " + title_text
        title_lbl = tk.Label(head, text=title_text, bg=bg, fg=title_fg,
                             font=(F, 11, "bold"), anchor="w", justify="left",
                             wraplength=200)
        title_lbl.pack(side="left", fill="x", expand=True, padx=(4, 0))

        def _toggle_pin():
            self.toggle_pin(memo["id"])

        pin_btn = tk.Button(head,
                            text="📌" if pinned else "📍",
                            font=(F, 10), bg=bg,
                            fg=C_PRIMARY_D if pinned else C_TEXT_3,
                            relief="flat", bd=0, cursor="hand2",
                            padx=2, activebackground=bg,
                            highlightthickness=0,
                            command=_toggle_pin)
        pin_btn.pack(side="right")

        content = memo.get("content", "")
        if content:
            body = tk.Frame(card, bg=bg)
            body.pack(fill="both", expand=True, padx=14, pady=(6, 8))
            content_lbl = tk.Label(body, text=content, bg=bg, fg=content_fg,
                                   font=(F, 10), anchor="nw", justify="left",
                                   wraplength=240)
            content_lbl.pack(fill="both", expand=True)
        else:
            tk.Frame(card, bg=bg, height=8).pack()

        foot = tk.Frame(card, bg=bg)
        foot.pack(fill="x", padx=14, pady=(4, 10))

        time_txt = memo.get("updated") or memo.get("created", "")
        tk.Label(foot, text=time_txt, bg=bg, fg=C_TEXT_3,
                 font=(F, 8)).pack(side="left")

        tk.Button(foot, text="🗑️", font=(F, 10),
                  bg=bg, fg=C_DANGER_D, relief="flat", bd=0,
                  cursor="hand2", padx=4, activebackground=bg,
                  highlightthickness=0,
                  command=lambda: self.del_memo(memo["id"])
                  ).pack(side="right")

        tk.Button(foot, text="✏️", font=(F, 10),
                  bg=bg, fg=C_TEXT_2, relief="flat", bd=0,
                  cursor="hand2", padx=4, activebackground=bg,
                  highlightthickness=0,
                  command=lambda: self.edit_memo(memo["id"])
                  ).pack(side="right", padx=2)

        def _dbl(_e):
            self.edit_memo(memo["id"])
        title_lbl.bind("<Double-1>", _dbl)
        card.bind("<Double-1>", _dbl)

        def _enter(_e):
            try:
                wrapper.configure(highlightbackground=C_PRIMARY,
                                  highlightthickness=2)
            except Exception:
                pass

        def _leave(_e):
            try:
                wrapper.configure(highlightbackground=C_BORDER,
                                  highlightthickness=1)
            except Exception:
                pass

        for w in (card, head, title_lbl, foot, topbar):
            w.bind("<Enter>", _enter, add="+")
            w.bind("<Leave>", _leave, add="+")

        return wrapper

    def toggle_pin(self, mid):
        memo = next((m for m in self.data.get("memos", []) if m["id"] == mid), None)
        if not memo:
            return
        memo["pinned"] = not memo.get("pinned", False)
        memo["updated"] = now_str()
        self.save()
        self.refresh_memos()
        self._log("釘選備忘錄：%s" % memo.get("title", ""))

    def add_memo(self):
        dlg = MemoDialog(self.root, self, None)
        self.root.wait_window(dlg)
        if not dlg.result or dlg.result == "__DELETE__":
            return
        rec = dlg.result
        rec["id"] = str(uuid.uuid4())
        rec["done"] = False
        rec["pinned"] = False
        rec["created"] = now_str()
        rec["updated"] = now_str()
        self.data.setdefault("memos", []).append(rec)
        self._log("新增備忘錄：%s" % rec.get("title", ""))
        self.save()
        self.refresh_memos()

    def edit_memo(self, mid):
        memo = next((m for m in self.data.get("memos", []) if m["id"] == mid), None)
        if not memo:
            return
        dlg = MemoDialog(self.root, self, memo)
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        if dlg.result == "__DELETE__":
            self.data["memos"] = [m for m in self.data["memos"] if m["id"] != mid]
            self._log("刪除備忘錄：%s" % memo.get("title", ""))
            self.save()
            self.refresh_memos()
            return
        memo.update(dlg.result)
        memo["updated"] = now_str()
        self.save()
        self.refresh_memos()

    def del_memo(self, mid):
        memo = next((m for m in self.data.get("memos", []) if m["id"] == mid), None)
        if not memo:
            return
        if not messagebox.askyesno(
                "確認刪除",
                "確定要刪除這則備忘錄嗎？\n\n%s" % memo.get("title", "")):
            return
        self.data["memos"] = [m for m in self.data["memos"] if m["id"] != mid]
        self._log("刪除備忘錄：%s" % memo.get("title", ""))
        self.save()
        self.refresh_memos()

    def del_done_memos(self):
        done_list = [m for m in self.data.get("memos", []) if m.get("done")]
        if not done_list:
            messagebox.showinfo("提醒", "目前沒有已完成的備忘錄。")
            return
        if not messagebox.askyesno(
                "確認刪除",
                "確定要刪除 %d 則已完成的備忘錄嗎？" % len(done_list)):
            return
        self.data["memos"] = [m for m in self.data["memos"] if not m.get("done")]
        self._log("刪除 %d 則已完成備忘錄" % len(done_list))
        self.save()
        self.refresh_memos()

    # ══════════════════════════════════
    #  頁籤 5：統計與日誌
    # ══════════════════════════════════
    def _build_stats(self):
        F = self.F
        tab = self.tab_stats
        tab.grid_rowconfigure(3, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        title_row = tk.Frame(tab, bg=C_BG)
        title_row.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 4))
        tk.Label(title_row, text="📊 統計與操作日誌", font=(F, 17, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(side="left")
        tk.Label(title_row, text="回顧目前工作量與系統操作紀錄", font=(F, 10),
                 bg=C_BG, fg=C_TEXT_3).pack(side="left", padx=(12, 0), pady=(4, 0))

        self.stat_frame = tk.Frame(tab, bg=C_BG)
        self.stat_frame.grid(row=1, column=0, sticky="ew", padx=22, pady=(8, 8))

        tk.Label(tab, text="📜 操作日誌", font=(F, 13, "bold"),
                 bg=C_BG, fg=C_TEXT).grid(row=2, column=0, sticky="w",
                                          padx=22, pady=(8, 6))

        tf = tk.Frame(tab, bg=C_SURFACE, highlightbackground=C_BORDER,
                      highlightthickness=1)
        tf.grid(row=3, column=0, sticky="nsew", padx=22, pady=(0, 12))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        self.txt_log = tk.Text(tf, font=(F, 10), bg=C_SURFACE, fg=C_TEXT,
                               relief="flat", wrap="word", padx=14, pady=12,
                               highlightthickness=0)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=vsb.set, state="disabled")
        self.txt_log.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

    def refresh_stats(self):
        for w in self.stat_frame.winfo_children():
            w.destroy()
        F = self.F
        counts = {}
        for c in self.data["contracts"]:
            counts[c.get("stage")] = counts.get(c.get("stage"), 0) + 1

        nns_total = sum(1 for r in self.data["nns"]
                        if not (r.get("replied") and r.get("done_date")))
        nns_from_case = counts.get("nns_pending", 0)

        cards = [
            ("總案件", len(self.data["contracts"]), C_PRIMARY_L),
            ("待檢查", counts.get("received", 0), "#FFF0F4"),
            ("待送組長", counts.get("to_leader", 0), C_WARNING_L),
            ("簽核中", counts.get("signing", 0) + counts.get("to_vp", 0), C_INFO_L),
            ("送印/回件", counts.get("printing", 0) + counts.get("returned", 0)
                        + counts.get("registered", 0), C_SUCCESS_L),
            ("待寄送", counts.get("notify", 0), "#FFF1D9"),
            ("需NNS登記", nns_from_case + nns_total, C_PURPLE_L),
            ("已結案", counts.get("done", 0), C_SURFACE_3),
        ]

        for i, (lab, val, color) in enumerate(cards):
            f = tk.Frame(self.stat_frame, bg=color,
                         highlightbackground=C_BORDER, highlightthickness=1)
            f.grid(row=0, column=i, padx=5, sticky="nsew")
            self.stat_frame.columnconfigure(i, weight=1)
            tk.Label(f, text=str(val), font=(F, 22, "bold"),
                     bg=color, fg=C_TEXT).pack(pady=(12, 0))
            tk.Label(f, text=lab, font=(F, 10),
                     bg=color, fg=C_TEXT_2).pack(pady=(0, 12))

        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        for item in self.data["log"][:300]:
            self.txt_log.insert("end", "[%s]  %s\n" % (item.get("time", ""), item.get("text", "")))
        self.txt_log.configure(state="disabled")

    # ══════════════════════════════════
    #  頁籤 6：設定
    # ══════════════════════════════════
    def _build_settings(self):
        F = self.F
        tab = self.tab_set
        tab.grid_columnconfigure(0, weight=1)

        title_row = tk.Frame(tab, bg=C_BG)
        title_row.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 4))
        tk.Label(title_row, text="⚙️ 設定與資料備份", font=(F, 17, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(side="left")
        tk.Label(title_row, text="調整工作時段、封面函樣板，並定期備份本機資料",
                 font=(F, 10), bg=C_BG, fg=C_TEXT_3).pack(side="left", padx=(12, 0), pady=(4, 0))

        box = tk.Frame(tab, bg=C_SURFACE, highlightbackground=C_BORDER,
                       highlightthickness=1)
        box.grid(row=1, column=0, sticky="ew", padx=22, pady=(10, 12))
        box.columnconfigure(3, weight=1)
        tk.Label(box, text="⚙️ 基本設定", font=(F, 13, "bold"),
                 bg=C_SURFACE, fg=C_TEXT).grid(row=0, column=0, columnspan=4,
                                               sticky="w", padx=18, pady=(14, 8))

        tk.Label(box, text="收件截止時間", font=(F, 11), bg=C_SURFACE, fg=C_TEXT_2
                 ).grid(row=1, column=0, sticky="e", padx=(18, 10), pady=8)
        self.e_cutoff = tk.Entry(box, font=(F, 11), width=12, bg=C_SURFACE,
                                 fg=C_TEXT, relief="flat", bd=0, highlightthickness=1,
                                 highlightbackground=C_BORDER,
                                 highlightcolor=C_PRIMARY)
        self.e_cutoff.grid(row=1, column=1, sticky="w", pady=8, ipady=4)

        tk.Label(box, text="寄件時段", font=(F, 11), bg=C_SURFACE, fg=C_TEXT_2
                 ).grid(row=2, column=0, sticky="e", padx=(18, 10), pady=8)
        self.e_mail = tk.Entry(box, font=(F, 11), width=26, bg=C_SURFACE,
                               fg=C_TEXT, relief="flat", bd=0, highlightthickness=1,
                               highlightbackground=C_BORDER,
                               highlightcolor=C_PRIMARY)
        self.e_mail.grid(row=2, column=1, sticky="w", pady=8, ipady=4)
        tk.Label(box, text="（例如：10:00, 14:00）", font=(F, 9),
                 bg=C_SURFACE, fg=C_TEXT_3).grid(row=2, column=2, sticky="w", pady=8)

        self.e_cutoff.insert(0, self.data["settings"].get("cutoff", "15:30"))
        self.e_mail.insert(0, self.data["settings"].get("mail_times", "10:00, 14:00"))

        self._btn(box, "💾 儲存設定", self.save_settings, "success").grid(
            row=3, column=0, columnspan=4, pady=(6, 16))

        box3 = tk.Frame(tab, bg=C_SURFACE, highlightbackground=C_BORDER,
                        highlightthickness=1)
        box3.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 12))
        tk.Label(box3, text="💾 資料管理", font=(F, 13, "bold"),
                 bg=C_SURFACE, fg=C_TEXT).pack(anchor="w", padx=18, pady=(14, 4))
        tk.Label(box3, text="資料夾：%s" % data_dir(),
                 font=(F, 9), bg=C_SURFACE, fg=C_TEXT_3).pack(anchor="w", padx=18)

        bb = tk.Frame(box3, bg=C_SURFACE)
        bb.pack(fill="x", padx=18, pady=14)
        self._btn(bb, "📂 開啟資料夾", self.open_data_dir, "info").pack(side="left")
        self._btn(bb, "🗄️ 立即備份", self.do_backup, "success").pack(side="left", padx=6)
        self._btn(bb, "📤 匯出 CSV", self.export_csv, "warning").pack(side="left")
        self._btn(bb, "📥 匯入資料", self.import_data, "purple").pack(side="left", padx=6)
        self._btn(bb, "🔄 重新載入", self.reload_data, "ghost").pack(side="left")

        tk.Label(tab, text="🌸 合約小管家 v%s　—　所有資料僅儲存在您的電腦中。" % APP_VER,
                 font=(F, 9), bg=C_BG, fg=C_TEXT_3).grid(
            row=3, column=0, sticky="w", padx=22, pady=(10, 0))

    def save_settings(self):
        self.data["settings"]["cutoff"] = self.e_cutoff.get().strip() or "15:30"
        self.data["settings"]["mail_times"] = self.e_mail.get().strip() or "10:00, 14:00"
        self.save()
        self._tick()
        messagebox.showinfo("完成", "設定已儲存 ✅")

    def open_data_dir(self):
        p = data_dir()
        try:
            if sys.platform.startswith("win"):
                os.startfile(p)
            elif sys.platform == "darwin":
                os.system('open "%s"' % p)
            else:
                os.system('xdg-open "%s"' % p)
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def do_backup(self):
        try:
            self.save()
            name = "data_%s.json" % datetime.now().strftime("%Y%m%d_%H%M%S")
            dst = os.path.join(backup_dir(), name)
            shutil.copy2(data_file(), dst)
            messagebox.showinfo("完成", "已備份至：\n%s" % dst)
        except Exception as e:
            messagebox.showerror("備份失敗", str(e))

    def export_csv(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV 檔", "*.csv")],
            initialfile="合約清單_%s.csv" % today_str())
        if not p:
            return
        try:
            with open(p, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["編號", "客戶代碼", "客戶名稱", "業務", "類型", "階段",
                            "區域", "收件日", "送件日", "回件日", "通知日",
                            "領取/寄出日", "-OK", "有製卡", "NNS", "備註"])
                for c in self.data["contracts"]:
                    w.writerow([
                        c.get("serial", ""), c.get("code", ""), c.get("name", ""),
                        c.get("sales", ""), c.get("dtype", ""),
                        STAGE_MAP.get(c.get("stage"), ("",))[0],
                        c.get("region", ""), c.get("recv_date", ""),
                        c.get("send_date", ""), c.get("return_date", ""),
                        c.get("notify_date", ""), c.get("deliver_date", ""),
                        "Y" if c.get("ok_mail") else "",
                        "Y" if c.get("has_card") else "",
                        "Y" if c.get("nns_needed") else "",
                        c.get("notes", ""),
                    ])
            messagebox.showinfo("完成", "已匯出：\n%s" % p)
        except Exception as e:
            messagebox.showerror("匯出失敗", str(e))

    def import_data(self):
        p = filedialog.askopenfilename(filetypes=[("JSON 檔", "*.json")])
        if not p:
            return
        if not messagebox.askyesno("確認", "匯入會覆蓋目前所有資料，確定嗎？"):
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict):
                raise ValueError("JSON 最外層必須是物件。")
            base = default_data()
            for k, v in base.items():
                d.setdefault(k, v)
            if not isinstance(d.get("settings"), dict):
                raise ValueError("settings 欄位格式錯誤。")
            for k, v in base["settings"].items():
                d["settings"].setdefault(k, v)
            for key in ("contracts", "nns", "memos", "log"):
                if not isinstance(d.get(key), list):
                    raise ValueError("%s 欄位必須是清單。" % key)
            if os.path.exists(data_file()):
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                shutil.copy2(data_file(), os.path.join(backup_dir(),
                                                       "before_import_%s.json" % stamp))
            old_data = self.data
            old_safe_mode = self.safe_mode
            self.data = d
            self.safe_mode = False
            if not self.save():
                self.data = old_data
                self.safe_mode = old_safe_mode
                return
            if hasattr(self, "lbl_safe_mode"):
                self.lbl_safe_mode.destroy()
                del self.lbl_safe_mode
            self.refresh_all()
            self._load_header_image()
            self._log("匯入資料完成")
            self.save()
            messagebox.showinfo("完成", "資料已匯入並完成匯入前備份。")
        except Exception as e:
            messagebox.showerror("匯入失敗", str(e))

    def reload_data(self):
        if not messagebox.askyesno("重新載入", "重新載入會捨棄目前尚未儲存的畫面變更。確定繼續嗎？"):
            return
        loaded = load_data()
        self.safe_mode = DATA_LOAD_FAILED
        self.data = loaded
        if self.safe_mode and not hasattr(self, "lbl_safe_mode"):
            self._show_safe_banner()
        elif not self.safe_mode and hasattr(self, "lbl_safe_mode"):
            self.lbl_safe_mode.destroy()
            del self.lbl_safe_mode
        self.refresh_all()
        self._load_header_image()

    # ══════════════════════════════════
    #  共用
    # ══════════════════════════════════
    def save(self):
        if getattr(self, "safe_mode", False):
            messagebox.showwarning(
                "安全模式｜尚未儲存",
                "原始資料讀取失敗，為避免覆蓋原檔，目前已停用儲存。\n請先從「設定與備份」匯入一份有效的 JSON 備份。"
            )
            return False
        try:
            save_data(self.data)
            return True
        except Exception as e:
            messagebox.showerror("儲存失敗", "資料未能儲存成功，請先不要關閉程式。\n\n%s" % e)
            return False

    def refresh_all(self):
        self.refresh_contracts()
        self.refresh_nns()
        self.refresh_ship()
        self.refresh_stats()
        try:
            self.refresh_memos()
        except Exception:
            pass

    def _tick(self):
        now = datetime.now()
        weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
        clock_text = "📅 %s (%s)   🕐 %s" % (
            now.strftime("%Y/%m/%d"),
            weekday,
            now.strftime("%H:%M:%S"),
        )
        try:
            self.lbl_clock.configure(text=clock_text)
        except Exception:
            return
        cutoff = self.data["settings"].get("cutoff", "15:30")
        try:
            hh, mm = [int(x) for x in cutoff.split(":")]
            over = (now.hour, now.minute) >= (hh, mm)
        except Exception:
            over = False
        if over:
            self.lbl_cut.configure(text="⏰ 已過收件截止 %s，新案件排明日處理" % cutoff,
                                   fg=C_DANGER_D)
        else:
            self.lbl_cut.configure(text="✅ 收件截止 %s 前" % cutoff, fg=C_SUCCESS_D)
        self.root.after(1000, self._tick)

    def check_reminders(self):
        lines = []
        now = datetime.now()
        cutoff = self.data["settings"].get("cutoff", "15:30")
        try:
            hh, mm = [int(x) for x in cutoff.split(":")]
            over = (now.hour, now.minute) >= (hh, mm)
        except Exception:
            over = False

        n_recv = sum(1 for c in self.data["contracts"] if c.get("stage") == "received")
        n_leader = sum(1 for c in self.data["contracts"] if c.get("stage") == "to_leader")
        n_back = sum(1 for c in self.data["contracts"] if c.get("stage") == "leader_back")
        n_notify = sum(1 for c in self.data["contracts"] if c.get("stage") == "notify")
        n_nns = sum(1 for r in self.data["nns"]
                    if not (r.get("replied") and r.get("done_date")))

        if over:
            lines.append("⏰ 已過收件截止 %s，新進案件請排到明天。" % cutoff)
        if n_recv:
            lines.append("🆕 待檢查案件：%d 筆" % n_recv)
        if n_back:
            lines.append("↩️ 組長退回待處理：%d 筆（記得回信說明問題）" % n_back)
        if n_leader:
            lines.append("📮 待送組長：%d 筆" % n_leader)
        if n_notify:
            lines.append("📦 待通知/寄送業務：%d 筆（封面函做好了嗎？）" % n_notify)
        if n_nns:
            lines.append("💾 NNS 待辦：%d 筆" % n_nns)

        if lines:
            messagebox.showinfo("🌸 今日待辦提醒", "\n\n".join(lines))

    def on_close(self):
        if getattr(self, "safe_mode", False):
            if messagebox.askyesno("安全模式",
                                    "目前處於安全模式，原始資料未被覆寫。確定關閉程式嗎？"):
                self.root.destroy()
            return
        if self.save():
            self.root.destroy()


# ══════════════════════════════════════════════
#  啟動
# ══════════════════════════════════════════════
def main():
    root = tk.Tk()
    try:
        app = ContractApp(root)
        root.mainloop()
    except Exception:
        import traceback
        messagebox.showerror("程式錯誤", traceback.format_exc())
        raise


if __name__ == "__main__":
    main()