import os
import sys
import time
import subprocess
import psutil
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# --- CONFIGURATION FIXE ---
FONT_FAMILY = "Montserrat"
FONT_SIZE = 14
COLOR_BLUE = "#1A365D"       # Bleu foncé
COLOR_RED = "#E53E3E"        # Rouge clair
ALERT_MINUTES = 50           # Seuil pour la pause
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# --- CONFIGURATION DYNAMIQUE (Arguments passés par le Widget) ---
# Si le script est lancé manuellement sans arguments, il prend YouTube par défaut
TARGET_NAME = sys.argv[1] if len(sys.argv) > 1 else "YouTube"
TARGET_URL = sys.argv[2] if len(sys.argv) > 2 else "https://www.youtube.com"
ICON_EMOJI = sys.argv[3] if len(sys.argv) > 3 else "📺"

# Fichier de log unique par site de divertissement
LOG_FILE = os.path.join(os.path.expanduser("~"), f"divertissement_{TARGET_NAME.lower()}_timer.txt")

def get_total_minutes_today():
    today_str = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            if lines:
                try:
                    date_part, mins_part = lines[0].strip().split("|")
                    if date_part == today_str:
                        return int(mins_part)
                except ValueError:
                    return 0
    return 0

def save_total_minutes_today(minutes):
    today_str = datetime.now().strftime("%Y-%m-%d")
    with open(LOG_FILE, "w") as f:
        f.write(f"{today_str}|{minutes}")

class TransparentTimer:
    def __init__(self, chrome_process):
        self.root = tk.Tk()
        self.chrome_process = chrome_process
        
        self.initial_daily_minutes = get_total_minutes_today()
        self.session_seconds = 0
        self.alert_triggered = False

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True) # Le timer reste au-dessus de Chrome
        self.root.attributes("-transparentcolor", "black")
        self.root.geometry("+10+10")

        self.label = tk.Label(
            self.root, 
            text="", 
            font=(FONT_FAMILY, FONT_SIZE, "bold"), 
            fg=COLOR_BLUE, 
            bg="black"
        )
        self.label.pack()
        self.update_timer()

    def update_timer(self):
        if not self.is_chrome_running():
            self.on_closing()
            return

        self.session_seconds += 1
        session_minutes = self.session_seconds // 60
        total_daily_minutes = self.initial_daily_minutes + session_minutes

        sh, sm = divmod(session_minutes, 60)
        dh, dm = divmod(total_daily_minutes, 60)

        # Utilisation de l'icône dynamique passée en argument
        display_text = f"{ICON_EMOJI} {TARGET_NAME} | Sess : {sh:02d}h{sm:02d} | Jour : {dh:02d}h{dm:02d}"

        if session_minutes >= ALERT_MINUTES:
            display_text += " (Fais une pause !)"
            self.label.config(fg=COLOR_RED)
            if not self.alert_triggered:
                self.alert_triggered = True
                self.root.after(100, self.show_alert)
        else:
            self.label.config(fg=COLOR_BLUE)

        self.label.config(text=display_text)

        if self.session_seconds % 60 == 0:
            save_total_minutes_today(total_daily_minutes)

        self.root.after(1000, self.update_timer)

    def is_chrome_running(self):
        try:
            if self.chrome_process.poll() is None:
                return True
            for proc in psutil.process_iter(['cmdline']):
                cmd = proc.info.get('cmdline')
                if cmd and f"--app={TARGET_URL}" in "".join(cmd):
                    return True
        except Exception:
            pass
        return False

    def show_alert(self):
        messagebox.showwarning(
            "Rappel de pause", 
            f"Cela serait idéal de faire une pause de {TARGET_NAME} après tant de temps, non ?"
        )
        self.root.lift()

    def on_closing(self):
        final_session_minutes = self.session_seconds // 60
        final_daily_minutes = self.initial_daily_minutes + final_session_minutes
        save_total_minutes_today(final_daily_minutes)
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    try:
        pwa_process = subprocess.Popen([CHROME_PATH, f"--app={TARGET_URL}"])
    except FileNotFoundError:
        print("Erreur : Google Chrome est introuvable.")
        sys.exit()

    time.sleep(1)
    app = TransparentTimer(pwa_process)
    app.root.mainloop()