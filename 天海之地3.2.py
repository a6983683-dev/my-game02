import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import time
from PIL import Image, ImageTk

# =============================================================================
# 核心路徑與環境預檢系統
# =============================================================================
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("天海之地:領域對決")
        
        self.current_w, self.current_h = 1180, 880
        self.root.geometry(f"{self.current_w}x{self.current_h}")
        
        self.CARD_W = 100
        self.CARD_H = 145

        self.bg_img_original = None
        self.resize_timer = None
        self.setup_background_engine()

        self.attrs = ['天', '地', '海']
        self.seasons = ['天季', '地季', '海季']
        self.current_season = random.choice(self.seasons)
        self.turn = 1
        self.start_time = time.time()
        self.difficulty = tk.IntVar(value=1) 
        
        self.player = {
            "hp": 50, "max_hp": 50, "energy": 0, 
            "hand": [], "shuffle": 3, "sel_main": None, 
            "sel_sub": None, "awakening": 0
        }
        self.opponent = {
            "hp": 50, "max_hp": 50, "energy": 0, 
            "hand": [], "awakening": 0
        }
        
        self.load_all_visual_resources()
        self.init_game_engine()
        self.setup_interface_layout()
        self.update_live_timer()

    # -------------------------------------------------------------------------
    # 視覺系統：背景縮放與資源載入
    # -------------------------------------------------------------------------
    def setup_background_engine(self):
        try:
            bg_path = get_resource_path("assets/bg.jpg")
            if os.path.exists(bg_path):
                self.bg_img_original = Image.open(bg_path)
                initial_render = self.bg_img_original.resize((self.current_w, self.current_h), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(initial_render)
                self.bg_label = tk.Label(self.root, image=self.bg_photo)
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self.root.bind("<Configure>", self.handle_resize_event)
            else:
                self.root.configure(bg="#1a1a1a")
        except:
            self.root.configure(bg="#1a1a1a")

    def handle_resize_event(self, event):
        if event.widget is self.root:
            if event.width == self.current_w and event.height == self.current_h:
                return
            if self.resize_timer:
                self.root.after_cancel(self.resize_timer)
            self.resize_timer = self.root.after(200, lambda: self.rebuild_background(event.width, event.height))

    def rebuild_background(self, new_w, new_h):
        if self.bg_img_original and new_w > 100 and new_h > 100:
            self.current_w, self.current_h = new_w, new_h
            resized = self.bg_img_original.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized)
            self.bg_label.config(image=self.bg_photo)

    def load_all_visual_resources(self):
        self.p_avatar = None
        self.o_avatar = None
        self.patterns = {}

        try:
            self.p_avatar = ImageTk.PhotoImage(Image.open(get_resource_path("assets/player.png")).resize((90, 90), Image.Resampling.LANCZOS))
            self.o_avatar = ImageTk.PhotoImage(Image.open(get_resource_path("assets/opponent.png")).resize((90, 90), Image.Resampling.LANCZOS))
        except: pass

        tex_configs = {
            "front_main": ("assets/card_front_pattern.png", "#ffffff"),
            "front_special": ("assets/card_front_special_pattern.png", "#2a1a0a"),
            "back_main": ("assets/card_back_pattern.png", "#223344"),
            "back_special": ("assets/card_back_special_pattern.png", "#1a1a1a")
        }

        for key, (path, fallback_color) in tex_configs.items():
            try:
                img = Image.open(get_resource_path(path)).resize((self.CARD_W, self.CARD_H), Image.Resampling.LANCZOS)
                self.patterns[key] = ImageTk.PhotoImage(img)
            except:
                img = Image.new('RGB', (self.CARD_W, self.CARD_H), color=fallback_color)
                self.patterns[key] = ImageTk.PhotoImage(img)

    # -------------------------------------------------------------------------
    # UI 框架系統：排版與組件配置
    # -------------------------------------------------------------------------
    def setup_interface_layout(self):
        self.header = tk.Frame(self.root, bg="#222", height=60, relief="raised", bd=2)
        self.header.pack(fill="x", pady=5)
        self.info_label = tk.Label(self.header, text="", fg="#fff", bg="#222", font=("微軟正黑體", 14, "bold"))
        self.info_label.pack(side="left", padx=30)
        self.timer_label = tk.Label(self.header, text="00:00", fg="#00ff00", bg="#000", font=("Consolas", 18, "bold"), width=8)
        self.timer_label.pack(side="right", padx=30)

        self.log_frame = tk.Frame(self.root, bg="#111", bd=2, relief="sunken")
        self.log_frame.pack(side="right", fill="y", padx=15, pady=10)
        tk.Label(self.log_frame, text=" 📜 戰術日誌 ", fg="#aaa", bg="#111", font=("微軟正黑體", 10)).pack()
        self.log_box = scrolledtext.ScrolledText(self.log_frame, bg="#000", fg="#00ff00", font=("微軟正黑體", 10), width=42, bd=0)
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)

        self.opp_zone = tk.LabelFrame(self.root, text=" ENEMY AREA ", fg="#ff4d4d", bg="#1a1a1a", font=("Arial", 10, "bold"))
        self.opp_zone.pack(fill="x", padx=20, pady=5)
        self.opp_meta = tk.Frame(self.opp_zone, bg="#1a1a1a")
        self.opp_meta.pack(fill="x", padx=10, pady=5)
        self.opp_av_lbl = tk.Label(self.opp_meta, bg="#333", width=90, height=90)
        if self.o_avatar: self.opp_av_lbl.config(image=self.o_avatar)
        self.opp_av_lbl.pack(side="left", padx=15)
        self.opp_status_lbl = tk.Label(self.opp_meta, text="", fg="#ff4d4d", bg="#1a1a1a", font=("微軟正黑體", 14, "bold"), justify="left")
        self.opp_status_lbl.pack(side="left", padx=10)
        self.opp_hand_container = tk.Frame(self.opp_zone, bg="#1a1a1a")
        self.opp_hand_container.pack(pady=10)

        self.action_bar = tk.Frame(self.root, bg="#1a1a1a")
        self.action_bar.pack(fill="x", padx=20, pady=15)
        
        self.l_btns = tk.Frame(self.action_bar, bg="#1a1a1a")
        self.l_btns.pack(side="left", expand=True)
        tk.Button(self.l_btns, text="📜 規則", command=self.show_rules, bg="#0277bd", fg="white", width=10, font=("微軟正黑體", 10, "bold")).pack(side="left", padx=5)
        tk.Button(self.l_btns, text="🌀 洗牌", command=self.shuffle_hand, bg="#444", fg="white", width=10, font=("微軟正黑體", 10, "bold")).pack(side="left", padx=5)

        self.btn_resolve = tk.Button(self.action_bar, text="術 式 開 始 (ENTER)", command=self.resolve_turn, 
                                     bg="#2e7d32", fg="white", font=("微軟正黑體", 16, "bold"), 
                                     width=28, height=2, relief="raised", bd=5)
        self.btn_resolve.pack(side="left", padx=10)
        self.root.bind('<Return>', lambda e: self.resolve_turn())

        self.r_btns = tk.Frame(self.action_bar, bg="#1a1a1a")
        self.r_btns.pack(side="left", expand=True)
        tk.Button(self.r_btns, text="♻️ 重啟", command=self.reset_game, bg="#c62828", fg="white", width=10, font=("微軟正黑體", 10, "bold")).pack(side="left", padx=5)
        
        d_frame = tk.Frame(self.r_btns, bg="#1a1a1a")
        d_frame.pack(side="left", padx=15)
        tk.Label(d_frame, text="難度:", fg="#fff", bg="#1a1a1a", font=("微軟正黑體", 9)).pack()
        for v in [1, 2, 3]:
            tk.Radiobutton(d_frame, text=f"L{v}", variable=self.difficulty, value=v, 
                           bg="#1a1a1a", fg="#4da6ff", selectcolor="#000", command=self.reset_game,
                           font=("Consolas", 9)).pack(side="left")

        self.pla_zone = tk.LabelFrame(self.root, text=" PLAYER AREA ", fg="#4da6ff", bg="#1a1a1a", font=("Arial", 10, "bold"))
        self.pla_zone.pack(fill="x", padx=20, pady=5)
        self.pla_meta = tk.Frame(self.pla_zone, bg="#1a1a1a")
        self.pla_meta.pack(fill="x", padx=10, pady=5)
        self.pla_av_lbl = tk.Label(self.pla_meta, bg="#333", width=90, height=90)
        if self.p_avatar: self.pla_av_lbl.config(image=self.p_avatar)
        self.pla_av_lbl.pack(side="left", padx=15)
        self.pla_status_lbl = tk.Label(self.pla_meta, text="", fg="#ffa500", bg="#1a1a1a", font=("微軟正黑體", 14, "bold"), justify="left")
        self.pla_status_lbl.pack(side="left", padx=10)
        self.pla_hand_container = tk.Frame(self.pla_zone, bg="#1a1a1a")
        self.pla_hand_container.pack(pady=10)

        self.refresh_ui_display()

    # -------------------------------------------------------------------------
    # 邏輯系統
    # -------------------------------------------------------------------------
    def init_game_engine(self):
        hp_setting = {1: 50, 2: 75, 3: 100}.get(self.difficulty.get(), 50)
        self.player.update({"hp": 50, "max_hp": 50, "energy": 0, "shuffle": 3, "awakening": 0})
        self.opponent.update({"hp": hp_setting, "max_hp": hp_setting, "energy": 0, "awakening": 0})
        self.player["hand"] = [self.create_dynamic_card() for _ in range(4)]
        self.opponent["hand"] = [self.create_dynamic_card() for _ in range(4)]
        self.turn = 1

    def create_dynamic_card(self):
        roll = random.random()
        if roll < 0.6:
            at = random.choice(self.attrs)
            n, d, e = random.choice([('極', 20, 3), ('特', 15, 2), ('強', 10, 1)])
            return {"cat": "main", "attr": at, "name": n, "dmg": d, "opp_e": e}
        elif roll < 0.8:
            return {"cat": "sub", "attr": "副", "name": random.choice(['200%最大功率', '黑閃']), "dmg": 0}
        else:
            return {"cat": "special", "attr": "特", "name": random.choice(['無下限', '流水擊', '極之番', '反轉術式', '領域展開']), "dmg": 0}

    def log(self, msg):
        self.log_box.insert("end", f"{msg}\n")
        self.log_box.see("end")

    def show_rules(self):
        r_win = tk.Toplevel(self.root); r_win.title("戰術協議"); r_win.geometry("450x550"); r_win.configure(bg="#111")
        txt = scrolledtext.ScrolledText(r_win, bg="#111", fg="#eee", font=("微軟正黑體", 11), padx=15, pady=15)
        txt.pack(fill="both", expand=True)
        rules_text = """【核心協議內容】

1. 屬性壓制：當季屬性全面壓制其他屬性。
2. 戰意系統：滿 6 點觸發「覺醒」，接下來2回合對碰必勝。
3. 副牌機制：
  - 200%最大功率：贏則傷害兩倍，輸則自身戰意清零。
  - 黑閃：無論輸贏自身+1戰意，贏額外再+1。
4. 特殊牌效果：
  - 無下限：免疫傷害，對手+2戰意。
  - 流水擊：反彈傷害，成功則對手戰意清零。
  - 極之番：必勝(10傷)，對手+3戰意。
  - 反轉術式：自身回滿血，對手戰意全滿。
  - 領域展開：指定季節，免疫本次攻擊。"""
        txt.insert("end", rules_text)
        txt.config(state="disabled")

    def refresh_ui_display(self):
        self.info_label.config(text=f"回合: {self.turn}  |  領域: 【{self.current_season}】")
        p_awk = " [🔥覺醒]" if self.player["awakening"] > 0 else ""
        o_awk = " [🔥覺醒]" if self.opponent["awakening"] > 0 else ""
        self.opp_status_lbl.config(text=f"HP: {self.opponent['hp']}/{self.opponent['max_hp']}\n戰意: {self.opponent['energy']}/6 {o_awk}")
        self.pla_status_lbl.config(text=f"HP: {self.player['hp']}/{self.player['max_hp']}\n戰意: {self.player['energy']}/6  |  洗牌: {self.player['shuffle']} {p_awk}")

        for w in self.opp_hand_container.winfo_children(): w.destroy()
        for w in self.pla_hand_container.winfo_children(): w.destroy()

        for c in self.opponent["hand"]:
            pat = self.patterns["back_special"] if c['cat'] == 'special' else self.patterns["back_main"]
            tk.Label(self.opp_hand_container, text=f"[{c['attr']}]\n\n?\n\n咒能", image=pat, compound="center", fg="#1a2a3a", bg="#000", font=("微軟正黑體", 10, "bold"), width=self.CARD_W, height=self.CARD_H, relief="raised", bd=2).pack(side="left", padx=8)

        for i, card in enumerate(self.player["hand"]):
            is_sel = (self.player["sel_main"] == i) or (self.player["sel_sub"] == i)
            
            if card['cat'] == 'special':
                p, f, b, t = self.patterns["front_special"], "#443300", "#2a1a0a", f"【術式】\n\n{card['name']}"
            elif card['cat'] == 'sub':
                p, f, b, t = self.patterns["front_main"], "#222222", "#333", f"【強化】\n\n{card['name']}"
            else:
                ac = {"天": "#001a33", "地": "#1a0033", "海": "#002200"}.get(card['attr'], "#111111")
                p, f, b, t = self.patterns["front_main"], ac, "#eee", f"[{card['attr']}]\n\n{card['name']}\n\nATK:{card['dmg']}"

            border_color = "#FFD700" if is_sel else "#1a1a1a"
            border_width = 3 if is_sel else 0
            card_frame = tk.Frame(self.pla_hand_container, bg=border_color, bd=border_width, relief="solid" if is_sel else "flat")
            card_frame.pack(side="left", padx=8)

            btn = tk.Button(card_frame, text=t, font=("微軟正黑體", 10, "bold"), image=p, compound="center", 
                            fg=f, bg=b, width=self.CARD_W, height=self.CARD_H, relief="raised", bd=2, 
                            command=lambda idx=i: self.select_card_action(idx))
            btn.pack(padx=2 if is_sel else 0, pady=2 if is_sel else 0)

    def select_card_action(self, idx):
        card = self.player["hand"][idx]
        if card["cat"] in ["main", "special"]:
            self.player["sel_main"] = None if self.player["sel_main"] == idx else idx
            if card["cat"] == "special": self.player["sel_sub"] = None
        else:
            if self.player["sel_main"] is not None and self.player["hand"][self.player["sel_main"]]["cat"] == "main":
                self.player["sel_sub"] = None if self.player["sel_sub"] == idx else idx
        self.refresh_ui_display()

    # -------------------------------------------------------------------------
    # 領域展開：自訂視窗選擇
    # -------------------------------------------------------------------------
    def choose_season_dialog(self):
        """ 彈出視窗讓玩家選擇季節，程式會等待玩家選擇完畢才繼續 """
        dialog = tk.Toplevel(self.root)
        dialog.title("領域展開")
        dialog.geometry("320x160")
        dialog.configure(bg="#111")
        dialog.transient(self.root) 
        dialog.grab_set()           
        
        x = self.root.winfo_x() + (self.current_w // 2) - 160
        y = self.root.winfo_y() + (self.current_h // 2) - 80
        dialog.geometry(f"+{x}+{y}")
        
        chosen_season = tk.StringVar(value="天季") 

        tk.Label(dialog, text="請選擇要展開的領域季節：", fg="#FFD700", bg="#111", font=("微軟正黑體", 12, "bold")).pack(pady=15)
        btn_frame = tk.Frame(dialog, bg="#111")
        btn_frame.pack(pady=5)

        def set_season(s):
            chosen_season.set(s)
            dialog.destroy()

        tk.Button(btn_frame, text="天季", bg="#003366", fg="white", font=("微軟正黑體", 12, "bold"), width=8, 
                  command=lambda: set_season("天季"), relief="raised", bd=3).pack(side="left", padx=8)
        tk.Button(btn_frame, text="地季", bg="#4d004d", fg="white", font=("微軟正黑體", 12, "bold"), width=8, 
                  command=lambda: set_season("地季"), relief="raised", bd=3).pack(side="left", padx=8)
        tk.Button(btn_frame, text="海季", bg="#004d00", fg="white", font=("微軟正黑體", 12, "bold"), width=8, 
                  command=lambda: set_season("海季"), relief="raised", bd=3).pack(side="left", padx=8)

        self.root.wait_window(dialog) 
        return chosen_season.get()

    # -------------------------------------------------------------------------
    # 戰鬥結算
    # -------------------------------------------------------------------------
    def resolve_turn(self):
        if self.player["sel_main"] is None:
            messagebox.showwarning("系統提示", "請選定出牌。")
            return

        pm_idx, ps_idx = self.player["sel_main"], self.player["sel_sub"]
        pm, ps = self.player["hand"][pm_idx], (self.player["hand"][ps_idx] if ps_idx is not None else None)
        o_cand = [i for i, c in enumerate(self.opponent["hand"]) if c['cat'] in ['main', 'special']]
        om_idx = random.choice(o_cand)
        om = self.opponent["hand"][om_idx]
        
        os_idx = None
        if om['cat'] == 'main':
            s_ids = [i for i, c in enumerate(self.opponent["hand"]) if c['cat'] == 'sub']
            if s_ids and random.random() > 0.4: os_idx = random.choice(s_ids)
        os = self.opponent["hand"][os_idx] if os_idx is not None else None

        self.log(f"\n>>>> 回合 {self.turn} <<<<")
        self.log(f"你：[{pm['attr']}] {pm['name']}" + (f" + [{ps['attr']}] {ps['name']}" if ps else ""))
        self.log(f"敵：[{om['attr']}] {om['name']}" + (f" + [{os['attr']}] {os['name']}" if os else ""))

        if om["name"] == "領域展開":
            self.current_season = random.choice(self.seasons)
            self.log(f"🌌 對手重塑了領域：{self.current_season}")
            
        if pm["name"] == "領域展開":
            self.current_season = self.choose_season_dialog()
            self.log(f"🌌 你展開了領域：{self.current_season}")

        pd, od = pm.get("dmg", 0), om.get("dmg", 0)
        p_win, o_win = False, False
        p_imm = pm["name"] in ["無下限", "領域展開"]
        o_imm = om["name"] in ["無下限", "領域展開"]

        p_season_match = self.current_season.startswith(pm.get('attr', ''))
        o_season_match = self.current_season.startswith(om.get('attr', ''))

        if not p_imm and not o_imm:
            if pm["name"] == "極之番" and om["name"] != "極之番": p_win, pd = True, 10
            elif om["name"] == "極之番" and pm["name"] != "極之番": o_win, od = True, 10
            elif self.player["awakening"] > 0 and self.opponent["awakening"] == 0: p_win = True
            elif self.opponent["awakening"] > 0 and self.player["awakening"] == 0: o_win = True
            elif p_season_match and not o_season_match: p_win = True
            elif o_season_match and not p_season_match: o_win = True
            elif pd > od: p_win = True
            elif od > pd: o_win = True

        # ===== 結算特防與戰意 =====
        if pm["name"] == "無下限": self.opponent["energy"] = min(6, self.opponent["energy"] + 2); self.log("🛡️ 你發動無下限，免疫傷害。")
        if om["name"] == "無下限": self.player["energy"] = min(6, self.player["energy"] + 2); self.log("🛡️ 對手發動無下限，免疫傷害。")
        if pm["name"] == "極之番": self.opponent["energy"] = min(6, self.opponent["energy"] + 3)
        if om["name"] == "極之番": self.player["energy"] = min(6, self.player["energy"] + 3)

        if pm["name"] == "反轉術式": 
            self.player["hp"] = self.player["max_hp"]
            self.opponent["energy"] = 6
            self.log("✨ 赫！你發動反轉術式，生命全滿！對手戰意暴漲至滿！")
        if om["name"] == "反轉術式":
            self.opponent["hp"] = self.opponent["max_hp"]
            self.player["energy"] = 6
            self.log("✨ 敵方發動反轉術式，生命全滿！你的戰意暴漲至滿！")

        if pm.get("cat") == "main": self.opponent["energy"] = min(6, self.opponent["energy"] + pm.get("opp_e", 0))
        if om.get("cat") == "main": self.player["energy"] = min(6, self.player["energy"] + om.get("opp_e", 0))

        if ps:
            if ps["name"] == "黑閃":
                self.player["energy"] = min(6, self.player["energy"] + (2 if p_win else 1))
                self.log(f"⚡ 黑閃空間扭曲！戰意增加。")
            if ps["name"] == "200%最大功率": 
                if p_win: pd *= 2; self.log("🔥 雙倍功率輸出！")
                else: self.player["energy"] = 0; self.log("⚠️ 功率過載，自身戰意清零！")
        
        if os:
            if os["name"] == "黑閃":
                self.opponent["energy"] = min(6, self.opponent["energy"] + (2 if o_win else 1))
            if os["name"] == "200%最大功率":
                if o_win: od *= 2
                else: self.opponent["energy"] = 0

        # ===== 結算傷害與流水擊 =====
        if p_win and not o_imm:
            if om["name"] == "流水擊": 
                self.player["hp"] -= pd
                self.opponent["energy"] = 0
                self.log(f"🔄 對手發動流水擊！你受到反彈 {pd} 傷害，對手戰意清零。")
            else: 
                self.opponent["hp"] -= pd
                self.log(f"🎯 突破防禦，對敵方造成 {pd} 傷害。")
        elif o_win and not p_imm:
            if pm["name"] == "流水擊": 
                self.opponent["hp"] -= od
                self.player["energy"] = 0
                self.log(f"🔄 你發動流水擊！成功反擊 {od} 傷害，自身戰意清零。")
            else: 
                self.player["hp"] -= od
                self.log(f"💥 遭受 {od} 點創傷。")
        else: 
            if not p_imm and not o_imm and not p_win and not o_win:
                self.log("⚔️ 勢均力敵，咒力相互抵銷。")

        self._update_awk(self.player, "你"); self._update_awk(self.opponent, "對手")
        self.finalize_turn(pm_idx, ps_idx, om_idx, os_idx)

    def _update_awk(self, ent, name):
        if ent["awakening"] > 0:
            ent["awakening"] -= 1
            if ent["awakening"] == 0: self.log(f"❄️ {name} 覺醒狀態結束。")
        elif ent["energy"] >= 6:
            ent["energy"] = 0; ent["awakening"] = 2; self.log(f"🔥 {name} 戰意沸騰，觸發覺醒！")

    def finalize_turn(self, pm, ps, om, os):
        p_pop = sorted([i for i in [pm, ps] if i is not None], reverse=True)
        o_pop = sorted([i for i in [om, os] if i is not None], reverse=True)
        for i in p_pop: self.player["hand"].pop(i)
        for i in o_pop: self.opponent["hand"].pop(i)
        
        while len(self.player["hand"]) < 4: self.player["hand"].append(self.create_dynamic_card())
        while len(self.opponent["hand"]) < 4: self.opponent["hand"].append(self.create_dynamic_card())
        
        self.player["sel_main"] = self.player["sel_sub"] = None
        
        if self.turn % 2 == 0: 
            self.current_season = random.choice(self.seasons)
            self.log(f"🌪️ 氣候變遷，進入【{self.current_season}】")
        
        self.turn += 1
        self.refresh_ui_display()
        self.check_terminal_condition()

    def check_terminal_condition(self):
        if self.player["hp"] <= 0 or self.opponent["hp"] <= 0:
            res = "【勝利】" if self.player["hp"] > 0 else "【失敗】"
            self.log(f"戰鬥結束：系統自動重置...")
            messagebox.showinfo("協議終止", f"本次戰鬥結果：{res}\n系統即將重啟。")
            self.reset_game()

    def shuffle_hand(self):
        if self.player["shuffle"] > 0:
            self.player["hand"] = [self.create_dynamic_card() for _ in range(4)]
            self.player["shuffle"] -= 1
            self.player["sel_main"] = self.player["sel_sub"] = None
            self.log("🌀 手牌重構完成。")
            self.refresh_ui_display()

    def update_live_timer(self):
        elapsed = int(time.time() - self.start_time)
        self.timer_label.config(text=f"{elapsed//60:02d}:{elapsed%60:02d}")
        self.root.after(1000, self.update_live_timer)

    def reset_game(self):
        self.log_box.delete('1.0', tk.END)
        self.log("系統：環境重新編譯中...")
        self.start_time = time.time()
        self.init_game_engine()
        self.refresh_ui_display()

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    app = GameApp(root)
    root.mainloop()