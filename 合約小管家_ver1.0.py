# -*- coding: utf-8 -*-
# """
# 🌸 合約小管家1.0 -By 楊芯語🌸  v1.0
# --------------------------------------------------
# 離線執行、資料存本機、可愛風格、深色文字高對比
# 適用：簽呈 / 合約 / 補充協議書 / NNS 登記 流程管理

# 打包成 exe：
#     pip install pyinstaller
#     pyinstaller --onefile --windowed --name ContractFlow contract_flow.py
# """

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

# ══════════════════════════════════════════════
#  基本常數
# ══════════════════════════════════════════════
APP_TITLE = "🌸 合約小管家｜ContractFlow 🌸"
APP_VER = "1.0.0"
DATA_LOAD_FAILED = False


def data_dir():
    """預設存於使用者家目錄；可用環境變數隔離測試資料。"""
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


# ── 可愛配色（全部深色文字，避免白字悲劇） ──
C_BG        = "#FFF8F4"   # 奶油底色
C_PANEL     = "#FFFEFD"
C_BORDER    = "#EFCBD5"
C_TEXT      = "#3B3B4F"   # 主要文字
C_TEXT2     = "#6E6E85"   # 次要文字
C_PINK      = "#F8B8CA"
C_PINK_D    = "#E985A3"
C_PINK_L    = "#FDE7ED"
C_BLUE_L    = "#DCEEFB"
C_MINT_L    = "#DFF5E8"
C_MINT_D    = "#2E6B4F"
C_YELLOW_L  = "#FFF6D6"
C_PURPLE_L  = "#EDE7F6"
C_GRAY_L    = "#EFEFF3"
C_DANGER_L  = "#FFDCDC"
C_DANGER_D  = "#8B3A3A"
C_ROSE      = "#D96F91"
C_ROSE_D    = "#B94F75"
C_CREAM     = "#FFFDF8"
C_SHADOW    = "#E8D5DC"

# ── 階段定義 ──
STAGES = [
    ("received",     "🆕 待檢查",         "#FFF0F4"),
    ("rejected",     "🚫 已退件",         "#FFE4E4"),
    ("to_leader",    "📮 待送組長",       "#FFFBEA"),
    ("leader_back",  "↩️ 組長退回",       "#FFE4E4"),
    ("signing",      "✍️ 組長簽核中",     "#EAF5FF"),
    ("to_vp",        "👔 待送件",       "#F2EDFF"),
    ("printing",     "🖨️ 送印中",         "#EAFBF1"),
    ("returned",     "📬 已回件",         "#E6F8EE"),
    ("registered",   "📝 已登記",         "#E8F0FF"),
    ("notify",       "📦 待通知/寄送",    "#FFF6E5"),
    ("nns_pending",  "🗂️ 需NNS登記",     "#F0E6FF"),
    ("done",         "✅ 已結案",         "#F0F0F4"),
]
STAGE_MAP = {k: (n, c) for k, n, c in STAGES}
STAGE_ORDER = [k for k, _, _ in STAGES]

# 一鍵推進的順序（分支階段不在此列）
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
  td{border:1px solid #C9C9D6;padding:10px 18px;font-size:15px;}
  td.k{background:#FFE8EF;font-weight:bold;width:130px;text-align:center;}
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
    """把 'YYYY-MM-DD HH:MM' 拆成 ('YYYY-MM-DD', 'HH:MM')"""
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
    """建立可垂直滾動的 canvas + inner frame，回傳 (canvas, inner)"""
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
        },
        "contracts": [],
        "nns": [],
        "memos": [],
        "log": [],
    }


def load_data():
    """讀取資料；若資料損壞，先保留原檔並進入安全模式，避免空資料覆蓋原檔。"""
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
        # 留存損壞檔副本，不覆寫原檔
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
    """以暫存檔原子替換，避免寫檔中斷造成主資料檔不完整。"""
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
        self.geometry("720x780")
        self.minsize(560, 480)
        self.resizable(False, True)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._load()
        self.bind("<Escape>", lambda e: self.destroy())

    # ----------------------------------
    def _lbl(self, parent, text, r, c=0):
        tk.Label(parent, text=text, bg=C_PANEL, fg=C_TEXT,
                 font=(self.app.F, 10, "bold"), anchor="e", width=11
                 ).grid(row=r, column=c, sticky="e", padx=(14, 8), pady=7)

    def _build(self):
        F = self.app.F

        # ── 底部固定按鈕列（先 pack 到最下面） ──
        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=16, pady=(6, 14))

        def btn(txt, cmd, bg, fg=C_TEXT):
            return tk.Button(bar, text=txt, command=cmd, font=(F, 11, "bold"),
                             bg=bg, fg=fg, activebackground=bg,
                             relief="flat", padx=18, pady=8,
                             cursor="hand2", bd=0)
        btn("💾 儲存", self.on_save, C_MINT_L, C_MINT_D).pack(side="right")
        btn("❌ 取消", self.destroy, C_GRAY_L).pack(side="right", padx=8)
        if not self.is_new:
            btn("🗑️ 刪除", self.on_delete, C_DANGER_L, C_DANGER_D).pack(side="left")

        # ── 可滾動內容 ──
        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text=("➕ 新增案件" if self.is_new else "✏️ 編輯案件"),
                 font=(F, 15, "bold"), bg=C_BG, fg=C_TEXT
                 ).pack(anchor="w", padx=16, pady=(14, 0))

        form = tk.Frame(outer, bg=C_PANEL,
                        highlightbackground=C_BORDER, highlightthickness=1)
        form.pack(fill="both", expand=True, pady=(10, 0))
        form.columnconfigure(1, weight=1)

        self.v = {}
        self.chk_vars = {}
        r = 0

        def add(label, key, widget="entry", values=None):
            nonlocal r
            tk.Label(form, text=label, bg=C_PANEL, fg=C_TEXT,
                     font=(F, 10, "bold"), width=11, anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(14, 8), pady=8)
            if widget == "entry":
                w = tk.Entry(form, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                             relief="solid", bd=1, highlightthickness=0)
            elif widget == "combo":
                w = ttk.Combobox(form, values=values, state="readonly", font=(F, 11))
            elif widget == "check":
                var = tk.BooleanVar(value=False)
                w = tk.Checkbutton(form, variable=var,
                                   bg=C_PANEL, activebackground=C_PANEL,
                                   fg=C_TEXT, selectcolor="#FFFFFF",
                                   font=(F, 11), anchor="w")
                self.chk_vars[key] = var
            w.grid(row=r, column=1, sticky="ew", padx=(0, 16), pady=8)
            self.v[key] = w
            r += 1
            return w

        add("客戶代碼", "code")
        add("客戶名稱", "name")
        add("業務名字", "sales")
        add("文件類型", "dtype", "combo", DOC_TYPES)
        add("區域", "region", "combo", REGIONS)

        # 收件日 + 時間
        self._add_datetime_row(form, "收件日", "recv_date", r)
        r += 1

        # 送件日 + 時間
        self._add_datetime_row(form, "送件日", "send_date", r)
        r += 1

        # 回件日 + 時間
        self._add_datetime_row(form, "回件日", "return_date", r)
        r += 1

        add("當前階段", "stage", "combo", [n for _, n, _ in STAGES])

        # 勾選項
        self._lbl(form, "狀態標記", r)
        chk = tk.Frame(form, bg=C_PANEL)
        chk.grid(row=r, column=1, sticky="w", padx=(0, 16), pady=4)
        self.chk_vars = {}
        for key, txt in (("ok_mail", "主旨已加 -OK"),
                         ("has_card", "有製卡")):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(chk, text=txt, variable=var,
                                bg=C_PANEL, activebackground=C_PANEL,
                                fg=C_TEXT, selectcolor="#FFFFFF",
                                font=(F, 10))
            cb.pack(side="left", padx=(0, 12))
            self.v[key] = cb
            self.chk_vars[key] = var
        r += 1

        self._lbl(form, "備註", r)
        self.v["notes"] = tk.Text(form, height=5, font=(F, 10),
                                  bg="#FFFFFF", fg=C_TEXT, relief="solid",
                                  bd=1, highlightthickness=0, wrap="word")
        self.v["notes"].grid(row=r, column=1, sticky="ew",
                             padx=(0, 16), pady=7)
        r += 1

       # 提示
        tk.Label(outer, text="⏰ 收件截止 15:30　|　📮 寄件時段 10:00、14:00（最晚 14:00 送總機）",
                 font=(F, 9), bg=C_BG, fg=C_TEXT2
                 ).pack(anchor="w", padx=16, pady=(8, 14))
        
    # ----------------------------------
    # def _set_date(self, key, val):
    #     self.v[key].delete(0, "end")
    #     self.v[key].insert(0, val)

    def _add_datetime_row(self, form, label, key, r):
        """建立『日期 + 時間(HH:MM)』輸入列"""
        F = self.app.F
        self._lbl(form, label, r)
        fr = tk.Frame(form, bg=C_PANEL)
        fr.grid(row=r, column=1, sticky="ew", padx=(0, 16), pady=7)

        e_date = tk.Entry(fr, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                          relief="solid", bd=1, width=12, highlightthickness=0)
        e_date.pack(side="left")

        tk.Label(fr, text=" ", bg=C_PANEL).pack(side="left")

        e_time = tk.Entry(fr, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                          relief="solid", bd=1, width=6, highlightthickness=0)
        e_time.pack(side="left")
        tk.Label(fr, text=" HH:MM", font=(F, 8), bg=C_PANEL,
                 fg=C_TEXT2).pack(side="left", padx=(3, 6))

        tk.Button(fr, text="現在", font=(F, 9), bg=C_BLUE_L, fg=C_TEXT,
                  relief="flat", padx=6, cursor="hand2",
                  command=lambda: self._set_now(key)).pack(side="left", padx=2)
        tk.Button(fr, text="今天", font=(F, 9), bg=C_YELLOW_L, fg=C_TEXT,
                  relief="flat", padx=6, cursor="hand2",
                  command=lambda: self._set_today(key)).pack(side="left", padx=2)
        tk.Button(fr, text="清空", font=(F, 9), bg=C_GRAY_L, fg=C_TEXT,
                  relief="flat", padx=6, cursor="hand2",
                  command=lambda: self._clear_dt(key)).pack(side="left", padx=2)

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
        # 新案件收件日預設今天
        if self.is_new:
            self.v["recv_date"].delete(0, "end")
            self.v["recv_date"].insert(0, today_str())
        sname = STAGE_MAP.get(c.get("stage", "received"), ("", ""))[0]
        self.v["stage"].set(sname or STAGES[0][1])
        for k in ("ok_mail", "has_card"):
            if c.get(k):
                self.chk_vars[k].set(True)
        self.v["notes"].insert("1.0", c.get("notes", ""))

    # ----------------------------------
    def on_save(self):
        code = self.v["code"].get().strip()
        name = self.v["name"].get().strip()
        if not code and not name:
            messagebox.showwarning("提醒", "請至少填寫「客戶代碼」或「客戶名稱」！", parent=self)
            return
        # 日期格式驗證：允許 YYYY-MM-DD 或 YYYY-MM-DD HH:MM
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
                    messagebox.showwarning("日期格式錯誤", "%s請使用 YYYY-MM-DD 或 YYYY-MM-DD HH:MM 格式。\n目前輸入：%s" % (label, value), parent=self)
                    return
        chronology = [("收件日", date_values["recv_date"]),
                      ("送件日", date_values["send_date"]),
                      ("回件日", date_values["return_date"])]
        present = [(label, value) for label, value in chronology if value]
        if len(present) >= 2:
            parsed = []
            for label, value in present:
                try:
                    parsed.append((label, datetime.strptime(value, "%Y-%m-%d %H:%M") if len(value) > 10 else datetime.strptime(value, "%Y-%m-%d")))
                except ValueError:
                    pass
            if any(parsed[i][1] > parsed[i+1][1] for i in range(len(parsed)-1)):
                if not messagebox.askyesno("日期順序提醒", "收件、送件、回件日期看起來不是由早到晚。\n若這是補登歷史資料，可以繼續；要返回修改嗎？", parent=self):
                    return
        stage_label = self.v["stage"].get()
        stage_key = "received"
        for k, n, _ in STAGES:
            if n == stage_label:
                stage_key = k
                break

        data = {
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
        self.result = data
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
        self.geometry("600x580")
        self.minsize(500, 400)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._load()

    def _build(self):
        F = self.app.F

        # ── 底部固定按鈕列 ──
        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=16, pady=(6, 14))
        tk.Button(bar, text="💾 儲存", command=self.on_save, font=(F, 11, "bold"),
                  bg=C_MINT_L, fg=C_MINT_D, relief="flat", padx=18, pady=8,
                  cursor="hand2", bd=0).pack(side="right")
        tk.Button(bar, text="❌ 取消", command=self.destroy, font=(F, 11, "bold"),
                  bg=C_GRAY_L, fg=C_TEXT, relief="flat", padx=18, pady=8,
                  cursor="hand2", bd=0).pack(side="right", padx=8)

        # ── 可滾動內容 ──
        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text=("➕ 新增 NNS 紀錄" if self.is_new else "✏️ 編輯 NNS 紀錄"),
                 font=(F, 15, "bold"), bg=C_BG, fg=C_TEXT
                 ).pack(anchor="w", padx=16, pady=(14, 0))

        form = tk.Frame(outer, bg=C_PANEL, highlightbackground=C_BORDER,
                        highlightthickness=1)
        form.pack(fill="both", expand=True, pady=(10, 0))
        form.columnconfigure(1, weight=1)

        self.v = {}
        self.chk_vars = {}
        r = 0

        def add(label, key, widget="entry", values=None):
            nonlocal r
            tk.Label(form, text=label, bg=C_PANEL, fg=C_TEXT,
                     font=(F, 10, "bold"), width=11, anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(14, 8), pady=8)
            if widget == "entry":
                w = tk.Entry(form, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                             relief="solid", bd=1, highlightthickness=0)
            elif widget == "combo":
                w = ttk.Combobox(form, values=values, state="readonly", font=(F, 11))
            elif widget == "check":
                var = tk.BooleanVar(value=False)
                w = tk.Checkbutton(form, variable=var,
                                   bg=C_PANEL, activebackground=C_PANEL,
                                   fg=C_TEXT, selectcolor="#FFFFFF",
                                   font=(F, 11), anchor="w")
                self.chk_vars[key] = var
            w.grid(row=r, column=1, sticky="ew", padx=(0, 16), pady=8)
            self.v[key] = w
            r += 1

        add("客戶代碼", "code")
        add("客戶名稱", "name")
        add("業務名字", "sales")
        add("類型", "kind", "combo", NNS_KINDS)

        # 收件日 + 時間
        self._add_dt_row(form, "收件日", "req_date", r)
        r += 1

        # 完成日 + 時間
        self._add_dt_row(form, "完成日", "done_date", r)
        r += 1

        add("已回信 -OK", "replied", "check")

        tk.Label(form, text="備註", bg=C_PANEL, fg=C_TEXT,
                 font=(F, 10, "bold"), width=11, anchor="e"
                 ).grid(row=r, column=0, sticky="ne", padx=(14, 8), pady=8)
        self.v["note"] = tk.Text(form, height=4, font=(F, 10), bg="#FFFFFF",
                                 fg=C_TEXT, relief="solid", bd=1,
                                 highlightthickness=0, wrap="word")
        self.v["note"].grid(row=r, column=1, sticky="ew", padx=(0, 16), pady=8)

    # ── 日期+時間編輯 ──
    def _add_dt_row(self, form, label, key, r):
        """建立『日期 + 時間(HH:MM)』輸入列"""
        F = self.app.F
        tk.Label(form, text=label, bg=C_PANEL, fg=C_TEXT,
                 font=(F, 10, "bold"), width=11, anchor="e"
                 ).grid(row=r, column=0, sticky="e", padx=(14, 8), pady=8)

        fr = tk.Frame(form, bg=C_PANEL)
        fr.grid(row=r, column=1, sticky="ew", padx=(0, 16), pady=8)

        e_date = tk.Entry(fr, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                          relief="solid", bd=1, width=12, highlightthickness=0)
        e_date.pack(side="left")

        tk.Label(fr, text=" ", bg=C_PANEL).pack(side="left")

        e_time = tk.Entry(fr, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                          relief="solid", bd=1, width=6, highlightthickness=0)
        e_time.pack(side="left")
        tk.Label(fr, text=" HH:MM", font=(F, 8), bg=C_PANEL,
                 fg=C_TEXT2).pack(side="left", padx=(3, 6))

        tk.Button(fr, text="現在", font=(F, 9), bg=C_BLUE_L, fg=C_TEXT,
                  relief="flat", padx=6, cursor="hand2",
                  command=lambda: self._set_now(key)).pack(side="left", padx=2)
        tk.Button(fr, text="今天", font=(F, 9), bg=C_YELLOW_L, fg=C_TEXT,
                  relief="flat", padx=6, cursor="hand2",
                  command=lambda: self._set_today(key)).pack(side="left", padx=2)
        tk.Button(fr, text="清空", font=(F, 9), bg=C_GRAY_L, fg=C_TEXT,
                  relief="flat", padx=6, cursor="hand2",
                  command=lambda: self._clear_dt(key)).pack(side="left", padx=2)

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

        # 收件日 / 完成日
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
        self.geometry("520x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()

    def _build(self):
        F = self.app.F

        # ── 底部固定按鈕列 ──
        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=16, pady=(6, 14))
        tk.Button(bar, text="✨ 產生並開啟", command=self.on_gen,
                  font=(F, 11, "bold"), bg=C_PINK, fg=C_TEXT,
                  relief="flat", padx=18, pady=9, cursor="hand2", bd=0
                  ).pack(side="right")
        tk.Button(bar, text="取消", command=self.destroy, font=(F, 11),
                  bg=C_GRAY_L, fg=C_TEXT, relief="flat", padx=18, pady=9,
                  cursor="hand2", bd=0).pack(side="right", padx=8)

        # ── 可滾動內容 ──
        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text="🖨️ 產生封面函", font=(F, 15, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(anchor="w", padx=16, pady=(14, 0))

        form = tk.Frame(outer, bg=C_PANEL, highlightbackground=C_BORDER,
                        highlightthickness=1)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self.v = {}
        rows = [("客戶代碼", "code", self.case.get("code", "")),
                ("客戶名稱", "name", self.case.get("name", "")),
                ("函的編號", "letter_no", "")]
        for i, (lab, key, default) in enumerate(rows):
            tk.Label(form, text=lab, bg=C_PANEL, fg=C_TEXT, width=10,
                     anchor="e", font=(F, 10, "bold")
                     ).grid(row=i, column=0, sticky="e", padx=(14, 8), pady=10)
            e = tk.Entry(form, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                         relief="solid", bd=1, highlightthickness=0)
            e.insert(0, default)
            e.grid(row=i, column=1, sticky="ew", padx=(0, 16), pady=10)
            self.v[key] = e

        tk.Label(outer, text="附件：", bg=C_BG, fg=C_TEXT,
                 font=(F, 10, "bold")).pack(anchor="w", pady=(12, 4))
        self.item_vars = {}
        items = [("合約書", True), ("補充協議書", False), ("製卡", False), ("簽呈", False)]
        box = tk.Frame(outer, bg=C_BG)
        box.pack(anchor="w")
        for txt, default in items:
            var = tk.BooleanVar(value=default)
            tk.Checkbutton(box, text=txt, variable=var, bg=C_BG,
                           activebackground=C_BG, fg=C_TEXT,
                           selectcolor="#FFFFFF", font=(F, 10)
                           ).pack(side="left", padx=(0, 14))
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
        self.case = case     # 直接引用原 dict，儲存時直接改它
        self.title("📮 寄件 / 領取 - %s" % case.get("name", ""))
        self.configure(bg=C_BG)
        self.geometry("640x620")
        self.minsize(540, 500)
        self.resizable(False, True)
        self.transient(parent)
        self.grab_set()
        self._build()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        F = self.app.F

        # ── 底部固定按鈕列 ──
        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=16, pady=(6, 14))

        tk.Button(bar, text="💾 儲存", command=self.on_save,
                  font=(F, 11, "bold"), bg=C_MINT_L, fg=C_MINT_D,
                  relief="flat", padx=18, pady=8, cursor="hand2", bd=0
                  ).pack(side="right")
        tk.Button(bar, text="❌ 取消", command=self.destroy,
                  font=(F, 11, "bold"), bg=C_GRAY_L, fg=C_TEXT,
                  relief="flat", padx=18, pady=8, cursor="hand2", bd=0
                  ).pack(side="right", padx=8)
        tk.Button(bar, text="✅ 結案", command=self.on_done,
                  font=(F, 11, "bold"), bg=C_PINK, fg=C_TEXT,
                  relief="flat", padx=18, pady=8, cursor="hand2", bd=0
                  ).pack(side="left")

        # ── 可滾動內容 ──
        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text="📮 寄件 / 領取",
                 font=(F, 15, "bold"), bg=C_BG, fg=C_TEXT
                 ).pack(anchor="w", padx=16, pady=(14, 0))

        c = self.case

        # 客戶資訊（唯讀）
        info = tk.Frame(outer, bg=C_PANEL,
                        highlightbackground=C_BORDER, highlightthickness=1)
        info.pack(fill="x", padx=16, pady=(10, 0))
        info.columnconfigure(1, weight=1)

        def info_row(r, label, value):
            tk.Label(info, text=label, bg=C_PANEL, fg=C_TEXT2,
                     font=(F, 10, "bold"), width=10, anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(14, 8), pady=6)
            tk.Label(info, text=value or "—", bg=C_PANEL, fg=C_TEXT,
                     font=(F, 11), anchor="w"
                     ).grid(row=r, column=1, sticky="w", padx=(0, 16), pady=6)

        info_row(0, "客戶代碼", c.get("code", ""))
        info_row(1, "客戶名稱", c.get("name", ""))
        info_row(2, "業務", c.get("sales", ""))
        info_row(3, "區域", c.get("region", ""))
        info_row(4, "文件類型", c.get("dtype", ""))
        info_row(5, "製卡", "💳 有製卡" if c.get("has_card") else "—")

        # 日期編輯區
        edit = tk.Frame(outer, bg=C_PANEL,
                        highlightbackground=C_BORDER, highlightthickness=1)
        edit.pack(fill="x", padx=16, pady=(10, 0))
        edit.columnconfigure(1, weight=1)

        self.v = {}
        self._add_dt_row(edit, "📨 通知日", "notify_date", 0)
        self._add_dt_row(edit, "📬 領取/寄出日", "deliver_date", 1)

        # 說明
        tk.Label(outer,
                 text="💡 狀態說明：\n"
                      "　• 兩個都空 → ⏳ 待通知業務\n"
                      "　• 只填通知日 → 📨 已通知，待領取/寄送\n"
                      "　• 兩者都填 → ✅ 北區已簽領　或　📦 中/南區已寄出",
                 font=(F, 9), bg=C_BG, fg=C_TEXT2, justify="left"
                 ).pack(anchor="w", padx=16, pady=(12, 14))

    def _add_dt_row(self, parent, label, key, r):
        F = self.app.F
        tk.Label(parent, text=label, bg=C_PANEL, fg=C_TEXT,
                 font=(F, 10, "bold"), width=11, anchor="e"
                 ).grid(row=r, column=0, sticky="e", padx=(14, 8), pady=10)

        fr = tk.Frame(parent, bg=C_PANEL)
        fr.grid(row=r, column=1, sticky="ew", padx=(0, 16), pady=10)

        d_val, t_val = parse_dt(self.case.get(key, ""))

        e_date = tk.Entry(fr, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                          relief="solid", bd=1, width=12, highlightthickness=0)
        e_date.insert(0, d_val)
        e_date.pack(side="left")

        tk.Label(fr, text=" ", bg=C_PANEL).pack(side="left")

        e_time = tk.Entry(fr, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                          relief="solid", bd=1, width=6, highlightthickness=0)
        e_time.insert(0, t_val)
        e_time.pack(side="left")

        tk.Label(fr, text=" HH:MM", font=(F, 8), bg=C_PANEL,
                 fg=C_TEXT2).pack(side="left", padx=(3, 6))

        tk.Button(fr, text="現在", font=(F, 9), bg=C_BLUE_L, fg=C_TEXT,
                  relief="flat", padx=8, cursor="hand2",
                  command=lambda k=key: self._set_now(k)
                  ).pack(side="left", padx=2)
        tk.Button(fr, text="今天", font=(F, 9), bg=C_YELLOW_L, fg=C_TEXT,
                  relief="flat", padx=8, cursor="hand2",
                  command=lambda k=key: self._set_today(k)
                  ).pack(side="left", padx=2)
        tk.Button(fr, text="清空", font=(F, 9), bg=C_GRAY_L, fg=C_TEXT,
                  relief="flat", padx=8, cursor="hand2",
                  command=lambda k=key: self._clear(k)
                  ).pack(side="left", padx=2)

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
        if not messagebox.askyesno("確認結案",
                                    "確定要結案嗎？案件將移到『已結案』。",
                                    parent=self):
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
        ("粉", "#FFE8EF"),
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
        self.geometry("500x560")
        self.minsize(420, 420)
        self.resizable(False, True)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._load()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        F = self.app.F

        # 底部按鈕列
        bar = tk.Frame(self, bg=C_BG)
        bar.pack(side="bottom", fill="x", padx=16, pady=(6, 14))

        tk.Button(bar, text="💾 儲存", command=self.on_save,
                  font=(F, 11, "bold"), bg=C_MINT_L, fg=C_MINT_D,
                  relief="flat", padx=18, pady=8, cursor="hand2", bd=0
                  ).pack(side="right")
        tk.Button(bar, text="❌ 取消", command=self.destroy,
                  font=(F, 11, "bold"), bg=C_GRAY_L, fg=C_TEXT,
                  relief="flat", padx=18, pady=8, cursor="hand2", bd=0
                  ).pack(side="right", padx=8)
        if not self.is_new:
            tk.Button(bar, text="🗑️ 刪除", command=self.on_delete,
                      font=(F, 11, "bold"), bg=C_DANGER_L, fg=C_DANGER_D,
                      relief="flat", padx=18, pady=8, cursor="hand2", bd=0
                      ).pack(side="left")

        canvas, outer = make_scrollable(self, bg=C_BG)
        self._scroll_canvas = canvas

        tk.Label(outer, text=("➕ 新增備忘錄" if self.is_new else "✏️ 編輯備忘錄"),
                 font=(F, 15, "bold"), bg=C_BG, fg=C_TEXT
                 ).pack(anchor="w", padx=16, pady=(14, 0))

        form = tk.Frame(outer, bg=C_PANEL,
                        highlightbackground=C_BORDER, highlightthickness=1)
        form.pack(fill="both", expand=True, padx=16, pady=(10, 0))
        form.columnconfigure(1, weight=1)

        # 標題
        tk.Label(form, text="標題", bg=C_PANEL, fg=C_TEXT,
                 font=(F, 10, "bold"), width=6, anchor="e"
                 ).grid(row=0, column=0, sticky="e", padx=(14, 8), pady=10)
        self.e_title = tk.Entry(form, font=(F, 11), bg="#FFFFFF", fg=C_TEXT,
                                relief="solid", bd=1, highlightthickness=0)
        self.e_title.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=10)

        # 內容
        tk.Label(form, text="內容", bg=C_PANEL, fg=C_TEXT,
                 font=(F, 10, "bold"), width=6, anchor="ne"
                 ).grid(row=1, column=0, sticky="ne", padx=(14, 8), pady=10)
        self.txt_content = tk.Text(form, height=10, font=(F, 11),
                                   bg="#FFFFFF", fg=C_TEXT, relief="solid",
                                   bd=1, highlightthickness=0, wrap="word")
        self.txt_content.grid(row=1, column=1, sticky="ew",
                              padx=(0, 16), pady=10)

        # 顏色
        tk.Label(form, text="顏色", bg=C_PANEL, fg=C_TEXT,
                 font=(F, 10, "bold"), width=6, anchor="e"
                 ).grid(row=2, column=0, sticky="e", padx=(14, 8), pady=10)
        self.color_var = tk.StringVar(value="#FFF6D6")
        color_box = tk.Frame(form, bg=C_PANEL)
        color_box.grid(row=2, column=1, sticky="w", padx=(0, 16), pady=10)
        for name, c in self.COLORS:
            rb = tk.Radiobutton(color_box, text=name, variable=self.color_var,
                                value=c, bg=c, activebackground=c,
                                fg=C_TEXT, selectcolor=c,
                                indicatoron=False, width=3, height=1,
                                relief="solid", bd=1, font=(F, 9, "bold"),
                                cursor="hand2")
            rb.pack(side="left", padx=3)

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
        self.ship_region = "全部"

        # 讀取上次儲存的縮放倍率
        try:
            self.scale = float(self.data["settings"].get("ui_scale", 1.0))
        except Exception:
            self.scale = 1.0
        self.scale = max(0.7, min(2.5, self.scale))

        root.title(APP_TITLE)
        root.configure(bg=C_BG)
        root.geometry("1480x980")
        root.minsize(1020, 700)
        self._center(1480, 980)

        self._style()
        self._build()
        if self.safe_mode:
            self.lbl_safe_mode = tk.Label(
                self.root,
                text="⚠ 安全模式：資料檔讀取失敗，目前操作不會寫入原始資料。請從「設定與備份」匯入有效備份。",
                font=(self.F, 10, "bold"), bg="#FFF0D6", fg="#7A4B00",
                padx=10, pady=7, anchor="w"
            )
            self.lbl_safe_mode.pack(fill="x", before=self.nb, padx=12, pady=(6, 0))

        # 第一次：快照所有原始字型
        self._snapshot_fonts(self.root)
        self._fonts_snapshotted = True

        self.apply_scale(self.scale, save=False)   # 套用縮放
        self.refresh_all()

        root.protocol("WM_DELETE_WINDOW", self.on_close)

        # ── 縮放快捷鍵 ──
        root.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
        root.bind("<Control-Button-4>",   lambda e: self.apply_scale(self.scale + 0.1))
        root.bind("<Control-Button-5>",   lambda e: self.apply_scale(self.scale - 0.1))
        root.bind("<Control-plus>",   lambda e: self.apply_scale(self.scale + 0.1))
        root.bind("<Control-equal>",  lambda e: self.apply_scale(self.scale + 0.1))
        root.bind("<Control-minus>",  lambda e: self.apply_scale(self.scale - 0.1))
        root.bind("<Control-0>",      lambda e: self.apply_scale(1.0))
        root.bind("<F11>", self.toggle_fullscreen)

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
        """統一全系統視覺：奶油底、玫瑰粉重點、清楚的表格與頁籤。"""
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except Exception:
            pass
        F = self.F
        st.configure("TFrame", background=C_BG)
        st.configure("TLabel", background=C_BG, foreground=C_TEXT, font=(F, 10))
        st.configure("TEntry", padding=(8, 7), fieldbackground=C_CREAM,
                     foreground=C_TEXT, bordercolor=C_BORDER, lightcolor=C_BORDER,
                     darkcolor=C_BORDER)
        st.configure("TCombobox", padding=(8, 6), fieldbackground=C_CREAM,
                     foreground=C_TEXT, arrowcolor=C_ROSE_D)
        st.map("TCombobox", fieldbackground=[("readonly", C_CREAM)],
               foreground=[("readonly", C_TEXT)])
        st.configure("TCheckbutton", background=C_BG, foreground=C_TEXT,
                     font=(F, 10))
        st.map("TCheckbutton", background=[("active", C_BG)])
        st.configure("Treeview", background=C_CREAM, foreground=C_TEXT,
                     fieldbackground=C_CREAM, rowheight=32, font=(F, 10),
                     borderwidth=0, relief="flat")
        st.configure("Treeview.Heading", background="#F9DDE5", foreground=C_TEXT,
                     font=(F, 10, "bold"), relief="flat", padding=(9, 11))
        st.map("Treeview.Heading", background=[("active", C_PINK)])
        st.map("Treeview", background=[("selected", "#F8D7E2")],
               foreground=[("selected", C_TEXT)])
        st.configure("Vertical.TScrollbar", background="#F3D5DF",
                     troughcolor=C_BG, bordercolor=C_BG, arrowcolor=C_ROSE_D)
        st.configure("Horizontal.TScrollbar", background="#F3D5DF",
                     troughcolor=C_BG, bordercolor=C_BG, arrowcolor=C_ROSE_D)
        st.configure("TNotebook", background=C_BG, borderwidth=0,
                     tabmargins=(4, 10, 4, 0))
        st.configure("TNotebook.Tab", background="#F4E6EA", foreground=C_TEXT2,
                     padding=(19, 12), font=(F, 10, "bold"), borderwidth=0)
        st.map("TNotebook.Tab",
               background=[("selected", C_ROSE), ("active", "#F9DDE5")],
               foreground=[("selected", "#FFFFFF"), ("active", C_TEXT)])

    # ── 縮放 ─────────────────────────
    def _snapshot_fonts(self, widget):
        """遞迴記錄所有 widget 的原始字型設定（只記一次）"""
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
        """遞迴把每個 widget 的字型大小乘上倍率"""
        if hasattr(widget, "_orig_font"):
            orig = widget._orig_font
            new_font = None
            if isinstance(orig, (tuple, list)) and len(orig) >= 2:
                parts = list(orig)
                if isinstance(parts[1], int):
                    parts[1] = max(7, int(round(parts[1] * factor)))
                    new_font = tuple(parts)
            elif isinstance(orig, str):
                # 字型名（例如 'TkDefaultFont'）→ 交給 ttk 樣式處理，這裡跳過
                pass
            if new_font:
                try:
                    widget.configure(font=new_font)
                except Exception:
                    pass
        # Text / Treeview 要另外處理，因為 cget 有時回傳字串
        try:
            for child in widget.winfo_children():
                self._scale_fonts(child, factor)
        except Exception:
            pass

    def apply_scale(self, factor, save=True):
        """套用介面縮放倍率（直接改字型大小，最穩定）"""
        try:
            factor = round(max(0.7, min(3.0, float(factor))), 2)
        except Exception:
            factor = 1.0
        self.scale = factor

        # 1) 所有 tk widget（Label / Button / Entry / Text…）字型一起放大縮小
        self._scale_fonts(self.root, factor)

        # 2) ttk 元件的字型 / 內距（用 Style 控制）
        style = ttk.Style()
        style.configure("Treeview",
                        rowheight=int(34 * factor),
                        font=(self.F, max(8, int(10 * factor))))
        style.configure("Treeview.Heading",
                        font=(self.F, max(8, int(10 * factor)), "bold"),
                        padding=(6, int(8 * factor)))
        style.configure("TNotebook.Tab",
                        font=(self.F, max(8, int(11 * factor)), "bold"),
                        padding=(int(19 * factor), int(12 * factor)))
        style.configure("TCombobox",
                        padding=int(4 * factor))
        try:
            self.root.option_add("*TCombobox*Listbox.font",
                                 (self.F, max(8, int(10 * factor))))
        except Exception:
            pass

        # 3) 頂部標題列高度也一起縮放
        try:
            self.head_frame.configure(height=int(82 * factor))
        except Exception:
            pass

        # 4) 記住設定
        self.data["settings"]["ui_scale"] = factor
        if save:
            self.save()

        # 5) 更新右上角顯示
        if hasattr(self, "lbl_scale"):
            self.lbl_scale.configure(text="🔍 %d%%" % int(round(factor * 100)))

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
        """按 F11 切換全螢幕 / 還原視窗"""
        try:
            if getattr(self, "_is_fullscreen", False):
                # 離開全螢幕：還原原本視窗大小
                self.root.attributes("-fullscreen", False)
                if getattr(self, "_saved_geometry", None):
                    self.root.geometry(self._saved_geometry)
                self._is_fullscreen = False
            else:
                # 進入全螢幕：先記住目前視窗 geometry
                self._saved_geometry = self.root.geometry()
                self.root.attributes("-fullscreen", True)
                self._is_fullscreen = True
        except Exception:
            # 某些平台不支援 -fullscreen，改用 zoomed 模式作為備援
            try:
                self._is_fullscreen = not getattr(self, "_is_fullscreen", False)
                self.root.attributes("-zoomed", self._is_fullscreen)
            except Exception:
                pass
        return "break"

    # ----------------------------------
    def _build(self):
        F = self.F

        # ── 頂部標題列 ──
        head = tk.Frame(self.root, bg="#F8C6D4", height=82)
        head.pack(fill="x")
        head.pack_propagate(False)
        self.head_frame = head   # 保存起來，縮放時要一起改高度
        
        brand = tk.Frame(head, bg="#F8C6D4")
        brand.pack(side="left", fill="y", padx=(24, 0), pady=10)
        tk.Label(brand, text="🌸 合約小管家", font=(F, 20, "bold"),
                 bg="#F8C6D4", fg="#633D4B").pack(anchor="w")
        tk.Label(brand, text="努力工作，養星導ショウ（X",
                 font=(F, 9), bg="#F8C6D4", fg="#8D5B6C").pack(anchor="w", pady=(2, 0))
        info = tk.Frame(head, bg="#F8C6D4")
        info.pack(side="right", padx=(0, 22))
        self.lbl_clock = tk.Label(info, text="", font=(F, 10, "bold"),
                                  bg="#F8C6D4", fg=C_TEXT)
        self.lbl_clock.pack(anchor="e")
        self.lbl_cut = tk.Label(info, text="", font=(F, 9),
                                bg="#F8C6D4", fg="#8D5B6C")
        self.lbl_cut.pack(anchor="e")
        self._tick()

        # ── 縮放控制（在時鐘左邊） ──
        zbox = tk.Frame(head, bg="#F8C6D4")
        zbox.pack(side="right", padx=(0, 18))
        tk.Label(zbox, text="縮放", font=(F, 9, "bold"),
                 bg="#F8C6D4", fg="#8D5B6C").pack(side="left", padx=(0, 4))
        tk.Button(zbox, text="－", font=(F, 12, "bold"), bg="#FFB3C6",
                  fg=C_TEXT, relief="flat", width=2, cursor="hand2", bd=0,
                  command=lambda: self.apply_scale(self.scale - 0.1)
                  ).pack(side="left")
        self.lbl_scale = tk.Label(zbox, text="🔍 100%", font=(F, 10, "bold"),
                                  bg="#F8C6D4", fg=C_TEXT, width=8)
        self.lbl_scale.pack(side="left", padx=2)
        tk.Button(zbox, text="＋", font=(F, 12, "bold"), bg="#FFB3C6",
                  fg=C_TEXT, relief="flat", width=2, cursor="hand2", bd=0,
                  command=lambda: self.apply_scale(self.scale + 0.1)
                  ).pack(side="left")
        tk.Button(zbox, text="重置", font=(F, 9), bg="#FFD9E1",
                  fg=C_TEXT, relief="flat", padx=8, pady=2,
                  cursor="hand2", bd=0,
                  command=lambda: self.apply_scale(1.0)
                  ).pack(side="left", padx=(6, 0))

        # ── 頁籤 ──
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=18, pady=(12, 7))
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.footer = tk.Frame(self.root, bg=C_CREAM, height=30,
                               highlightbackground=C_BORDER, highlightthickness=1)
        self.footer.pack(fill="x", padx=18, pady=(0, 10))
        self.lbl_footer = tk.Label(self.footer, text="🌷 系統就緒", font=(F, 9),
                                   bg=C_CREAM, fg=C_TEXT2, anchor="w")
        self.lbl_footer.pack(side="left", padx=12, pady=5)
        self.lbl_footer_right = tk.Label(self.footer, text="本機儲存 · 記得定期備份",
                                         font=(F, 9), bg=C_CREAM, fg=C_TEXT2)
        self.lbl_footer_right.pack(side="right", padx=12, pady=5)

        self.tab_contracts = tk.Frame(self.nb, bg=C_BG)
        self.tab_nns = tk.Frame(self.nb, bg=C_BG)
        self.tab_ship = tk.Frame(self.nb, bg=C_BG)
        self.tab_stats = tk.Frame(self.nb, bg=C_BG)
        self.tab_memos = tk.Frame(self.nb, bg=C_BG)     # 新增
        self.tab_set = tk.Frame(self.nb, bg=C_BG)

        self.nb.add(self.tab_contracts, text="📋 合約流水線")
        self.nb.add(self.tab_nns, text="🗂️ NNS 管理")
        self.nb.add(self.tab_ship, text="📮 寄件 / 領取")
        self.nb.add(self.tab_stats, text="📊 統計與日誌")
        self.nb.add(self.tab_memos, text="📝 備忘錄")     # 新增
        self.nb.add(self.tab_set, text="⚙️ 設定與備份")

        self._build_contracts()
        self._build_nns()
        self._build_ship()
        self._build_stats()
        self._build_memos()      # 新增
        self._build_settings()

    def _on_tab_changed(self, _event=None):
        """頁籤切換時更新底部提示，不影響各頁原本功能。"""
        try:
            tab = self.nb.tab(self.nb.select(), "text")
            count = len(self.data.get("contracts", []))
            self.lbl_footer.configure(text=f"🌷 {tab}　·　目前合約 {count} 筆")
        except Exception:
            pass

    def _section_heading(self, parent, title, subtitle=None):
        """一致的頁面標題區；高度精簡，讓表格有更多空間。"""
        frame = tk.Frame(parent, bg=C_BG)
        frame.pack(fill="x", pady=(0, 6))
        tk.Label(frame, text=title, font=(self.F, 15, "bold"),
                 bg=C_BG, fg="#704656").pack(anchor="w")
        if subtitle:
            tk.Label(frame, text=subtitle, font=(self.F, 8),
                     bg=C_BG, fg=C_TEXT2).pack(anchor="w", pady=(1, 0))
        return frame

    # ─────────────────────────────────
    #  小工具：建立按鈕
    # ─────────────────────────────────
    def _btn(self, parent, text, cmd, bg=C_BLUE_L, fg=C_TEXT, width=None):
        b = tk.Button(parent, text=text, command=cmd,
                      font=(self.F, 10, "bold"), bg=bg, fg=fg,
                      activebackground="#F8D7E2", activeforeground=C_TEXT,
                      relief="flat", padx=15, pady=8, cursor="hand2", bd=0,
                      highlightthickness=0, takefocus=True)
        if width:
            b.configure(width=width)
        # 輕量 hover 效果：滑入稍微加深，離開還原原色
        b.bind("<Enter>", lambda _e, widget=b: widget.configure(relief="raised", bd=1))
        b.bind("<Leave>", lambda _e, widget=b: widget.configure(relief="flat", bd=0))
        return b

    # ══════════════════════════════════
    #  頁籤 1：合約流水線
    # ══════════════════════════════════
    def _build_contracts(self):
        F = self.F
        wrap = tk.Frame(self.tab_contracts, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=16)
        self._section_heading(wrap, "📋 合約流水線", "追蹤每份合約目前走到哪個階段，先處理需要行動的案件。")

         # ── 工具列 ──
        bar = tk.Frame(wrap, bg=C_BG)
        bar.pack(fill="x", pady=(0, 4))

        self._btn(bar, "➕ 新增案件", self.add_contract, C_PINK).pack(side="left")
        self._btn(bar, "✏️ 編輯", self.edit_contract, C_BLUE_L).pack(side="left", padx=4)
        self._btn(bar, "⏩ 推進階段", self.advance_contract, C_MINT_L, C_MINT_D).pack(side="left")
        self._btn(bar, "↩️ 退回原寄件人", lambda: self.set_stage("rejected"),
                  C_DANGER_L, C_DANGER_D).pack(side="left", padx=4)
        self._btn(bar, "🗑️ 刪除", self.del_contract, C_DANGER_L, C_DANGER_D).pack(side="left")

        # 搜尋
        sf = tk.Frame(bar, bg=C_BG)
        sf.pack(side="right")
        tk.Label(sf, text="🔍", font=(F, 12), bg=C_BG, fg=C_TEXT).pack(side="left")
        self.ent_search = tk.Entry(sf, font=(F, 11), width=18, bg="#FFFFFF",
                                   fg=C_TEXT, relief="solid", bd=1,
                                   highlightthickness=0)
        self.ent_search.pack(side="left", padx=(4, 0), ipady=4)
        self.ent_search.bind("<KeyRelease>", self._on_search)
        self._btn(sf, "清除", self.clear_search, C_PINK_L).pack(side="left", padx=(4, 0))

        # ── 摘要小標籤（一行） ──
        summary = tk.Frame(wrap, bg=C_BG)
        summary.pack(fill="x", pady=(0, 4))
        self.summary_values = {}
        summary_specs = [
            ("total",    "📚 全部",     C_PINK_L),
            ("received", "🆕 待檢查",   "#FFF0F4"),
            ("to_leader","📮 待送組長", C_YELLOW_L),
            ("notify",   "📦 待通知",   "#FFF1D9"),
            ("nns",      "🗂️ NNS待辦", C_PURPLE_L),
        ]
        for key, title, color in summary_specs:
            tag = tk.Frame(summary, bg=color, highlightbackground=C_BORDER,
                           highlightthickness=1, padx=8, pady=2)
            tag.pack(side="left", padx=(0, 6))
            tk.Label(tag, text=title, font=(F, 9), bg=color,
                     fg=C_TEXT2).pack(side="left")
            v = tk.Label(tag, text="0", font=(F, 11, "bold"), bg=color, fg=C_TEXT)
            v.pack(side="left", padx=(4, 0))
            self.summary_values[key] = v

        # ── 階段 chips（單行） ──
        chips = tk.Frame(wrap, bg=C_BG)
        chips.pack(fill="x", pady=(0, 6))
        self.chip_btns = {}

        allbtn = tk.Button(chips, text="📋 全部", font=(F, 9, "bold"),
                           bg=C_PINK_L, fg=C_TEXT, relief="flat",
                           padx=6, pady=3, cursor="hand2", bd=0,
                           command=lambda: self.set_filter("all"))
        allbtn.pack(side="left", padx=(0, 2))
        self.chip_btns["all"] = allbtn

        for key, name, _ in STAGES:
            b = tk.Button(chips, text=name, font=(F, 9),
                          bg=C_GRAY_L, fg=C_TEXT, relief="flat",
                          padx=6, pady=3, cursor="hand2", bd=0,
                          command=lambda k=key: self.set_filter(k))
            b.pack(side="left", padx=(0, 2))
            self.chip_btns[key] = b

        # 表格
        tf = tk.Frame(wrap, bg=C_PANEL, highlightbackground=C_BORDER,
                      highlightthickness=1)
        tf.pack(fill="both", expand=True)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("serial", "code", "name", "sales", "dtype", "stage",
                "recv", "send", "ret", "ok_mail", "card", "notes")
        heads = ("編號", "客戶代碼", "客戶名稱", "業務", "類型", "階段",
                 "收件日", "送件日", "回件日", "-OK", "製卡", "備註")
        widths = (55, 100, 180, 85, 105, 130, 130, 130, 130, 60, 60, 250)

        self.tv_contracts = ttk.Treeview(tf, columns=cols, show="headings",
                                         selectmode="extended")
        for c, h, w in zip(cols, heads, widths):
            self.tv_contracts.heading(c, text=h)
            self.tv_contracts.column(c, width=w, minwidth=w,
                                     anchor="center", stretch=False)

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

        # 狀態列
        self.lbl_c_status = tk.Label(wrap, text="", font=(F, 9),
                                     bg=C_BG, fg=C_TEXT2, anchor="w")
        self.lbl_c_status.pack(fill="x", pady=(6, 0))

    # ── 右鍵選單 ──
    def _contract_menu(self, event):
        iid = self.tv_contracts.identify_row(event.y)
        if not iid:
            return
        if iid not in self.tv_contracts.selection():
            self.tv_contracts.selection_set(iid)
        m = tk.Menu(self.root, tearoff=0, font=(self.F, 10))
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
            if k == key:
                b.configure(bg=C_PINK, fg=C_TEXT, font=(self.F, 9, "bold"))
            else:
                b.configure(bg=C_GRAY_L, fg=C_TEXT, font=(self.F, 9))
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
        t = today_str()
        # 送印中 → 自動填送件日
        if key == "printing" and not c.get("send_date"):
            c["send_date"] = now_str()
        # 已回件 → 自動填回件日
        if key == "returned" and not c.get("return_date"):
            c["return_date"] = now_str()
        # 標記曾進入過的流程（結案後仍留在寄件區/NNS區）
        if key in ("returned", "registered", "notify", "nns_pending"):
            c["ship_visited"] = True
        if key == "nns_pending":
            c["nns_visited"] = True
        if key == "leader_back":
            c["ok_mail"] = False   # 被退貨，取消 -OK
        c.setdefault("history", []).append({
            "time": now_str(),
            "text": "階段 %s → %s" % (STAGE_MAP.get(old, ("?",))[0],
                                     STAGE_MAP.get(key, ("?",))[0])
        })
        self._log("%s：%s → %s" % (c.get("name", ""),
                                   STAGE_MAP.get(old, ("?",))[0],
                                   STAGE_MAP.get(key, ("?",))[0]))

    # ----------------------------------
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
            notes = c.get("notes", "")
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
                              ok, card, notes),
                      tags=(c.get("stage", "received"),))

        # 更新 chip 數量
        counts = {}
        for c in self.data["contracts"]:
            counts[c.get("stage")] = counts.get(c.get("stage"), 0) + 1
        total = len(self.data["contracts"])
        if hasattr(self, "summary_values"):
            self.summary_values["total"].configure(text=str(total))
            for stage_key in ("received", "to_leader", "notify"):
                count = sum(1 for item in self.data["contracts"] if item.get("stage") == stage_key)
                self.summary_values[stage_key].configure(text=str(count))
            nns_count = sum(1 for item in self.data.get("nns", [])
                            if not (item.get("replied") and item.get("done_date")))
            self.summary_values["nns"].configure(text=str(nns_count))
        self.chip_btns["all"].configure(text="📋 全部 (%d)" % total)
        for key, name, _ in STAGES:
            self.chip_btns[key].configure(text="%s (%d)" % (name, counts.get(key, 0)))

        self.lbl_c_status.configure(
            text="顯示 %d 筆 / 共 %d 筆　|　資料位置：%s" % (len(rows), total, data_file()))

    # ══════════════════════════════════
    #  頁籤 2：NNS
    # ══════════════════════════════════
    def _build_nns(self):
        F = self.F
        wrap = tk.Frame(self.tab_nns, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=16)
        self._section_heading(wrap, "🗂️ NNS 登記管理", "集中追蹤新合約登記與資料變更，完成後記得回信並標記。")

        bar = tk.Frame(wrap, bg=C_BG)
        bar.pack(fill="x", pady=(0, 8))
        self._btn(bar, "➕ 新增 NNS 紀錄", self.add_nns, C_PINK).pack(side="left")
        self._btn(bar, "✏️ 編輯", self.edit_nns, C_BLUE_L).pack(side="left", padx=6)
        self._btn(bar, "✅ 標記完成並回信", self.done_nns, C_MINT_L, C_MINT_D).pack(side="left")
        self._btn(bar, "🗑️ 刪除", self.del_nns, C_DANGER_L, C_DANGER_D).pack(side="left", padx=6)
        self._btn(bar, "🔄 從合約帶入新合約", self.pull_from_contracts,
                  C_YELLOW_L).pack(side="left", padx=6)

        tf = tk.Frame(wrap, bg=C_PANEL, highlightbackground=C_BORDER,
                      highlightthickness=1)
        tf.pack(fill="both", expand=True)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("code", "name", "sales", "kind", "req", "done", "replied", "note")
        heads = ("客戶代碼", "客戶名稱", "業務", "類型", "收件日", "完成日", "已回信 -OK", "備註")
        widths = (110, 180, 100, 130, 150, 150, 100, 240)

        self.tv_nns = ttk.Treeview(tf, columns=cols, show="headings",
                                    selectmode="extended")
        for c, h, w in zip(cols, heads, widths):
            self.tv_nns.heading(c, text=h)
            self.tv_nns.column(c, width=w, minwidth=w,
                               anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tv_nns.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tv_nns.xview)
        self.tv_nns.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tv_nns.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tv_nns.tag_configure("pending", background="#FFF6E5")
        self.tv_nns.tag_configure("done", background="#EAFBF1")
        self.tv_nns.tag_configure("case", background="#F0E6FF")
        self.tv_nns.tag_configure("case_done", background="#E0D5F5")
        self.tv_nns.bind("<Double-1>", lambda e: self.edit_nns())
        self.tv_nns.bind("<Button-3>", self._nns_menu)

        tk.Label(wrap,
                 text="💡 提示：新合約回件後，NNS 登記會自動列在這裡；變更需求完成後記得回信並標記 -OK。",
                 font=(F, 9), bg=C_BG, fg=C_TEXT2, anchor="w").pack(fill="x", pady=(6, 0))

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

        # 來自合約的案件 → 開合約編輯
        if rid.startswith("case_"):
            cid = rid[5:]
            c = self.get_case(cid)
            if not c:
                return
            dlg = ContractDialog(self.root, self, c)
            self.root.wait_window(dlg)
            if not dlg.result or dlg.result == "__DELETE__":
                return
            old_stage = c.get("stage")
            c.update(dlg.result)
            self.save()
            self.refresh_all()
            return

        # 一般 NNS 紀錄
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
            messagebox.showinfo("提醒",
                                "來自合約流水線的案件，請從『📋 合約流水線』頁面處理。")
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
        """NNS 管理的右鍵選單"""
        iid = self.tv_nns.identify_row(event.y)
        if not iid:
            return
        if iid not in self.tv_nns.selection():
            self.tv_nns.selection_set(iid)

        m = tk.Menu(self.root, tearoff=0, font=(self.F, 10))
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
        """把『🗂️ 需NNS登記』階段的合約，轉存成獨立 NNS 紀錄"""
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

        # 收集：手動紀錄 + 曾進入 NNS 流程的合約案件
        rows = []
        for r in self.data["nns"]:
            rows.append(("manual", r))
        for c in self.data["contracts"]:
            if c.get("stage") == "nns_pending" or c.get("nns_visited") or c.get("nns_done"):
                rows.append(("case", c))

        # 排序：未完成在前
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
        wrap = tk.Frame(self.tab_ship, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=16)
        self._section_heading(wrap, "📮 寄件與領取", "集中處理通知、簽領、寄出與結案，減少遺漏。")

        banner = tk.Frame(wrap, bg=C_YELLOW_L, highlightbackground="#F0DFA8",
                          highlightthickness=1)
        banner.pack(fill="x", pady=(0, 10))
        tk.Label(banner,
                 text="📮 公司寄件時段：早上 10:00 與下午 14:00　|　最晚必須在 14:00 前交給總機",
                 font=(F, 11, "bold"), bg=C_YELLOW_L, fg="#7A5A20",
                 pady=10).pack(anchor="w", padx=16)

        bar = tk.Frame(wrap, bg=C_BG)
        bar.pack(fill="x", pady=(0, 8))
        self._btn(bar, "📨 標記已通知業務", self.notify_sales, C_BLUE_L).pack(side="left")
        self._btn(bar, "✍️ 北區已簽領", self.pickup_north, C_MINT_L, C_MINT_D).pack(side="left", padx=6)
        self._btn(bar, "📦 中/南區已寄出", self.mail_out, C_PURPLE_L).pack(side="left")
        self._btn(bar, "↩️ 取消簽領/寄出", self.cancel_deliver, C_GRAY_L).pack(side="left", padx=6)
        self._btn(bar, "✅ 結案", lambda: self.set_ship_done(), C_MINT_L, C_MINT_D).pack(side="left")

        rf = tk.Frame(bar, bg=C_BG)
        rf.pack(side="right")
        tk.Label(rf, text="區域：", font=(F, 10), bg=C_BG, fg=C_TEXT).pack(side="left")
        self.cb_region = ttk.Combobox(rf, values=["全部"] + REGIONS,
                                      state="readonly", width=8, font=(F, 10))
        self.cb_region.set("全部")
        self.cb_region.pack(side="left")
        self.cb_region.bind("<<ComboboxSelected>>", lambda e: self.refresh_ship())

        tf = tk.Frame(wrap, bg=C_PANEL, highlightbackground=C_BORDER,
                      highlightthickness=1)
        tf.pack(fill="both", expand=True)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("code", "name", "sales", "region", "dtype", "card", "notify", "status")
        heads = ("客戶代碼", "客戶名稱", "業務", "區域", "類型", "製卡", "通知日", "狀態")
        widths = (110, 220, 100, 80, 120, 80, 130, 220)

        self.tv_ship = ttk.Treeview(tf, columns=cols, show="headings",
                                     selectmode="extended")
        for c, h, w in zip(cols, heads, widths):
            self.tv_ship.heading(c, text=h)
            self.tv_ship.column(c, width=w, minwidth=w,
                                anchor="center", stretch=False)

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

        tk.Label(wrap,
                 text="💡 雙擊案件可編輯通知日 / 領取寄出日　|　北區：簽名領回　|　中/南區：需先做封面函，有製卡的客戶要一起寄出。",
                 font=(F, 9), bg=C_BG, fg=C_TEXT2, anchor="w").pack(fill="x", pady=(6, 0))

    def _ship_rows(self):
        region = self.cb_region.get()
        out = []
        for c in self.data["contracts"]:
            st = c.get("stage", "")
            show = st in ("returned", "registered", "notify", "nns_pending")
            # 曾進入寄件流程、或已結案但有寄件記錄 → 繼續顯示
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
        """取消『已簽領 / 已寄出』狀態，把案件退回待通知"""
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
        """雙擊案件 → 開啟寄件編輯對話框"""
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

        m = tk.Menu(self.root, tearoff=0, font=(self.F, 10))
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
    #  頁籤：備忘錄
    # ══════════════════════════════════
    def _build_memos(self):
        F = self.F
        wrap = tk.Frame(self.tab_memos, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=16)
        self._section_heading(wrap, "📝 工作備忘錄", "把臨時交辦、待確認事項與提醒集中記下來。")

        # 工具列
        bar = tk.Frame(wrap, bg=C_BG)
        bar.pack(fill="x", pady=(0, 10))

        self._btn(bar, "➕ 新增備忘錄", self.add_memo, C_PINK).pack(side="left")
        self._btn(bar, "🗑️ 清除已完成", self.del_done_memos, C_GRAY_L).pack(side="left", padx=6)

        rf = tk.Frame(bar, bg=C_BG)
        rf.pack(side="right")
        self.memo_show_done = tk.BooleanVar(value=True)
        tk.Checkbutton(rf, text="顯示已完成", variable=self.memo_show_done,
                       bg=C_BG, activebackground=C_BG, fg=C_TEXT,
                       selectcolor="#FFFFFF", font=(F, 10),
                       cursor="hand2",
                       command=self.refresh_memos).pack(side="left")

        # 卡片區（可垂直捲動）
        canvas, inner = make_scrollable(wrap, bg=C_BG)
        self.memo_canvas = canvas
        self.memo_inner = inner

    def refresh_memos(self):
        inner = self.memo_inner
        for w in inner.winfo_children():
            w.destroy()

        memos = list(self.data.get("memos", []))
        show_done = self.memo_show_done.get()

        # 排序：未完成在前、更新時間新的在前
        def _key(m):
            return (bool(m.get("done")),
                    -(0 if not m.get("updated") else 1),   # placeholder
                    )
        # 用簡單版：先按 done 分群，再按 updated 反序
        memos.sort(key=lambda m: m.get("updated", m.get("created", "")), reverse=True)
        memos.sort(key=lambda m: bool(m.get("done")))

        # 過濾
        if not show_done:
            memos = [m for m in memos if not m.get("done")]

        if not memos:
            tk.Label(inner, text="📭 目前沒有備忘錄\n按上方「➕ 新增備忘錄」開始記錄吧！",
                     font=(self.F, 12), bg=C_BG, fg=C_TEXT2,
                     justify="center").grid(row=0, column=0, columnspan=3,
                                            padx=20, pady=60)
            for i in range(3):
                inner.columnconfigure(i, weight=1, minsize=280)
            return

        cols = 3
        for i in range(cols):
            inner.columnconfigure(i, weight=1, minsize=280)

        r = 0
        c = 0
        for m in memos:
            card = self._make_memo_card(inner, m)
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            c += 1
            if c >= cols:
                c = 0
                r += 1

    def _make_memo_card(self, parent, memo):
        F = self.F
        color = memo.get("color", "#FFF6D6")
        done = bool(memo.get("done"))

        if done:
            bg = "#F0F0F4"
            title_fg = "#A0A0B0"
            content_fg = "#B0B0C0"
        else:
            bg = color
            title_fg = C_TEXT
            content_fg = C_TEXT2

        card = tk.Frame(parent, bg=bg,
                        highlightbackground=C_BORDER, highlightthickness=1, bd=0)

        # 標題列（勾選框 + 標題）
        head = tk.Frame(card, bg=bg)
        head.pack(fill="x", padx=10, pady=(10, 0))

        var = tk.BooleanVar(value=done)

        def _toggle():
            memo["done"] = var.get()
            memo["updated"] = now_str()
            self.save()
            self.refresh_memos()

        cb = tk.Checkbutton(head, variable=var, command=_toggle,
                            bg=bg, activebackground=bg,
                            fg=C_TEXT, selectcolor="#FFFFFF",
                            font=(F, 11), cursor="hand2")
        cb.pack(side="left")

        title_text = memo.get("title", "")
        if done:
            title_text = "✓ " + title_text
        title_lbl = tk.Label(head, text=title_text, bg=bg, fg=title_fg,
                             font=(F, 11, "bold"), anchor="w", justify="left",
                             wraplength=220)
        title_lbl.pack(side="left", fill="x", expand=True)

        # 內容
        content = memo.get("content", "")
        if content:
            content_lbl = tk.Label(card, text=content, bg=bg, fg=content_fg,
                                   font=(F, 10), anchor="w", justify="left",
                                   wraplength=260)
            content_lbl.pack(fill="x", padx=14, pady=(6, 8))
        else:
            tk.Frame(card, bg=bg, height=6).pack()

        # 底部（時間 + 按鈕）
        foot = tk.Frame(card, bg=bg)
        foot.pack(fill="x", padx=10, pady=(4, 10))

        time_txt = memo.get("updated") or memo.get("created", "")
        tk.Label(foot, text=time_txt, bg=bg, fg=C_TEXT2,
                 font=(F, 8)).pack(side="left")

        tk.Button(foot, text="🗑️", font=(F, 10),
                  bg=bg, fg=C_DANGER_D, relief="flat", bd=0,
                  cursor="hand2", padx=4, activebackground=bg,
                  command=lambda: self.del_memo(memo["id"])
                  ).pack(side="right")

        tk.Button(foot, text="✏️", font=(F, 10),
                  bg=bg, fg=C_TEXT, relief="flat", bd=0,
                  cursor="hand2", padx=4, activebackground=bg,
                  command=lambda: self.edit_memo(memo["id"])
                  ).pack(side="right", padx=2)

        # 雙擊卡片編輯
        def _dbl(_e):
            self.edit_memo(memo["id"])
        card.bind("<Double-1>", _dbl)
        title_lbl.bind("<Double-1>", _dbl)
        head.bind("<Double-1>", _dbl)

        return card

    def add_memo(self):
        dlg = MemoDialog(self.root, self, None)
        self.root.wait_window(dlg)
        if not dlg.result or dlg.result == "__DELETE__":
            return
        rec = dlg.result
        rec["id"] = str(uuid.uuid4())
        rec["done"] = False
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
    #  頁籤 4：統計與日誌
    # ══════════════════════════════════
    def _build_stats(self):
        F = self.F
        wrap = tk.Frame(self.tab_stats, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=16)
        self._section_heading(wrap, "📊 統計與操作日誌", "回顧目前工作量與系統操作紀錄。")

        self.stat_frame = tk.Frame(wrap, bg=C_BG)
        self.stat_frame.pack(fill="x", pady=(0, 12))

        tk.Label(wrap, text="📜 操作日誌", font=(F, 13, "bold"),
                 bg=C_BG, fg=C_TEXT).pack(anchor="w", pady=(0, 6))

        tf = tk.Frame(wrap, bg=C_PANEL, highlightbackground=C_BORDER,
                      highlightthickness=1)
        tf.pack(fill="both", expand=True)
        self.txt_log = tk.Text(tf, font=(F, 10), bg="#FFFFFF", fg=C_TEXT,
                               relief="flat", wrap="word", padx=12, pady=10)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=vsb.set, state="disabled")
        vsb.pack(side="right", fill="y")
        self.txt_log.pack(fill="both", expand=True)

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
            ("總案件", len(self.data["contracts"]), C_PINK_L),
            ("待檢查", counts.get("received", 0), C_YELLOW_L),
            ("待送組長", counts.get("to_leader", 0), C_BLUE_L),
            ("簽核中", counts.get("signing", 0) + counts.get("to_vp", 0), C_PURPLE_L),
            ("送印/回件", counts.get("printing", 0) + counts.get("returned", 0)
                        + counts.get("registered", 0), C_MINT_L),
            ("待寄送", counts.get("notify", 0), C_YELLOW_L),
            ("需NNS登記", nns_from_case + nns_total, C_PURPLE_L),
            ("已結案", counts.get("done", 0), C_GRAY_L),
        ]
        
        for i, (lab, val, color) in enumerate(cards):
            f = tk.Frame(self.stat_frame, bg=color,
                         highlightbackground=C_BORDER, highlightthickness=1)
            f.grid(row=0, column=i, padx=5, sticky="nsew")
            self.stat_frame.columnconfigure(i, weight=1)
            tk.Label(f, text=str(val), font=(F, 22, "bold"),
                     bg=color, fg=C_TEXT).pack(pady=(12, 0))
            tk.Label(f, text=lab, font=(F, 10),
                     bg=color, fg=C_TEXT2).pack(pady=(0, 12))

        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        for item in self.data["log"][:300]:
            self.txt_log.insert("end", "[%s]  %s\n" % (item.get("time", ""), item.get("text", "")))
        self.txt_log.configure(state="disabled")

    # ══════════════════════════════════
    #  頁籤 5：設定
    # ══════════════════════════════════
    def _build_settings(self):
        F = self.F
        wrap = tk.Frame(self.tab_set, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=16)
        self._section_heading(wrap, "⚙️ 設定與資料備份", "調整工作時段、封面函樣板，並定期備份本機資料。")

        # 基本設定
        box = tk.Frame(wrap, bg=C_PANEL, highlightbackground=C_BORDER,
                       highlightthickness=1)
        box.pack(fill="x", pady=(0, 12))
        tk.Label(box, text="⚙️ 基本設定", font=(F, 13, "bold"),
                 bg=C_PANEL, fg=C_TEXT).grid(row=0, column=0, columnspan=3,
                                             sticky="w", padx=16, pady=(12, 6))

        tk.Label(box, text="收件截止時間", font=(F, 11), bg=C_PANEL, fg=C_TEXT
                 ).grid(row=1, column=0, sticky="e", padx=(16, 8), pady=8)
        self.e_cutoff = tk.Entry(box, font=(F, 11), width=12, bg="#FFFFFF",
                                 fg=C_TEXT, relief="solid", bd=1, highlightthickness=0)
        self.e_cutoff.grid(row=1, column=1, sticky="w", pady=8)

        tk.Label(box, text="寄件時段", font=(F, 11), bg=C_PANEL, fg=C_TEXT
                 ).grid(row=2, column=0, sticky="e", padx=(16, 8), pady=8)
        self.e_mail = tk.Entry(box, font=(F, 11), width=24, bg="#FFFFFF",
                               fg=C_TEXT, relief="solid", bd=1, highlightthickness=0)
        self.e_mail.grid(row=2, column=1, sticky="w", pady=8)
        tk.Label(box, text="（例如：10:00, 14:00）", font=(F, 9),
                 bg=C_PANEL, fg=C_TEXT2).grid(row=2, column=2, sticky="w", pady=8)

        self.e_cutoff.insert(0, self.data["settings"].get("cutoff", "15:30"))
        self.e_mail.insert(0, self.data["settings"].get("mail_times", "10:00, 14:00"))

        tk.Button(box, text="💾 儲存設定", command=self.save_settings,
                  font=(F, 11, "bold"), bg=C_MINT_L, fg=C_MINT_D,
                  relief="flat", padx=18, pady=8, cursor="hand2", bd=0
                  ).grid(row=3, column=0, columnspan=3, pady=(4, 14))


        # 資料管理
        box3 = tk.Frame(wrap, bg=C_PANEL, highlightbackground=C_BORDER,
                        highlightthickness=1)
        box3.pack(fill="x")
        tk.Label(box3, text="💾 資料管理", font=(F, 13, "bold"),
                 bg=C_PANEL, fg=C_TEXT).pack(anchor="w", padx=16, pady=(12, 4))
        tk.Label(box3, text="資料夾：%s" % data_dir(),
                 font=(F, 9), bg=C_PANEL, fg=C_TEXT2).pack(anchor="w", padx=16)

        bb = tk.Frame(box3, bg=C_PANEL)
        bb.pack(fill="x", padx=16, pady=12)
        self._btn(bb, "📂 開啟資料夾", self.open_data_dir, C_BLUE_L).pack(side="left")
        self._btn(bb, "🗄️ 立即備份", self.do_backup, C_MINT_L, C_MINT_D).pack(side="left", padx=6)
        self._btn(bb, "📤 匯出 CSV", self.export_csv, C_YELLOW_L).pack(side="left")
        self._btn(bb, "📥 匯入資料", self.import_data, C_PURPLE_L).pack(side="left", padx=6)
        self._btn(bb, "🔄 重新載入", self.reload_data, C_GRAY_L).pack(side="left")

        tk.Label(wrap, text="🌸 合約小管家 v%s　—　所有資料僅儲存在您的電腦中。" % APP_VER,
                 font=(F, 9), bg=C_BG, fg=C_TEXT2).pack(anchor="w", pady=(10, 0))

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
            # 匯入前先保留現有資料檔；即使匯入失敗也能回復
            if os.path.exists(data_file()):
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                shutil.copy2(data_file(), os.path.join(backup_dir(), "before_import_%s.json" % stamp))
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
            self.refresh_all()
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
            self.lbl_safe_mode = tk.Label(
                self.root,
                text="⚠ 安全模式：資料檔讀取失敗，目前操作不會寫入原始資料。請從「設定與備份」匯入有效備份。",
                font=(self.F, 10, "bold"), bg="#FFF0D6", fg="#7A4B00", padx=10, pady=7, anchor="w"
            )
            self.lbl_safe_mode.pack(fill="x", before=self.nb, padx=12, pady=(6, 0))
        elif not self.safe_mode and hasattr(self, "lbl_safe_mode"):
            self.lbl_safe_mode.destroy()
            del self.lbl_safe_mode
        self.refresh_all()

    # ══════════════════════════════════
    #  共用
    # ══════════════════════════════════
    def save(self):
        """回傳是否成功；讀檔失敗時禁止將預設空資料覆寫原檔。"""
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
        clock_text = "📅 %s (%s)  🕐 %s" % (
            now.strftime("%Y/%m/%d"),
            weekday,
            now.strftime("%H:%M:%S"),
        )
        self.lbl_clock.configure(text=clock_text)
        cutoff = self.data["settings"].get("cutoff", "15:30")
        try:
            hh, mm = [int(x) for x in cutoff.split(":")]
            over = (now.hour, now.minute) >= (hh, mm)
        except Exception:
            over = False
        if over:
            self.lbl_cut.configure(text="⏰ 已過收件截止 %s，新案件排明日處理" % cutoff,
                                   fg="#8B3A3A")
        else:
            self.lbl_cut.configure(text="✅ 收件截止 %s 前" % cutoff, fg="#2E6B4F")
        self.root.after(1000, self._tick)

    def check_reminders(self):
        """開機提醒"""
        F = self.F
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
            lines.append("🗂️ NNS 待辦：%d 筆" % n_nns)

        if lines:
            messagebox.showinfo("🌸 今日待辦提醒", "\n\n".join(lines))

    def on_close(self):
        if getattr(self, "safe_mode", False):
            if messagebox.askyesno("安全模式", "目前處於安全模式，原始資料未被覆寫。確定關閉程式嗎？"):
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
        # # 高 DPI 修正（Windows）
        # if sys.platform.startswith("win"):
        #     try:
        #         from ctypes import windll
        #         windll.shcore.SetProcessDpiAwareness(1)
        #     except Exception:
        #         pass
        app = ContractApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        messagebox.showerror("程式錯誤", traceback.format_exc())
        raise


if __name__ == "__main__":
    main()