import os
import sys
import time
import subprocess
import threading
import psutil
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# --- CONFIGURATION GRAPHIQUE & POSITION ---
FONT_FAMILY = "Montserrat"
COLOR_BG = "#1A202C"         # Fond sombre pour le launcher
COLOR_BLUE = "#1A365D"       # Bleu foncé (Texte Timer)
COLOR_RED = "#E53E3E"        # Rouge clair (Alerte Timer)
COLOR_ACCENT = "#3182CE"     # Bleu boutons actifs
COLOR_DISABLED = "#4A5568"   # Gris boutons bloqués
ALERT_MINUTES = 50           # Seuil d'alerte pour la pause

# Positionnement du Widget principal (Ex: à droite de l'écran, 400x500)
WIDGET_GEOMETRY = "400x500+1100+200" 

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
LOG_FILE = os.path.join(os.path.expanduser("~"), "divertissement_daily_timer.txt")

# Liste restreinte aux 4 sites de divertissement principaux
SITES = {
    "YouTube": "https://www.youtube.com",
    "Netflix": "https://www.netflix.com",
    "Animes": "https://anime-sama.pw/",
    "Free TV": "https://tv.free.fr/"
}

def get_total_minutes_today():
    """Récupère le temps accumulé aujourd'hui dans le log."""
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
                    pass
    return 0

def save_total_minutes_today(minutes):
    """Sauvegarde le temps total du jour."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    with open(LOG_FILE, "w") as f:
        f.write(f"{today_str}|{minutes}")

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Menu Divertissement")
        self.root.geometry(WIDGET_GEOMETRY)
        self.root.configure(bg=COLOR_BG)
        
        # --- Transformation en Widget de Fond d'écran ---
        self.root.overrideredirect(True) # Supprime la barre de titre et les bordures
        self.root.lower() # Place la fenêtre au niveau du fond d'écran
        
        # Astuce pour maintenir le widget en arrière-plan sous Windows
        self.root.bind("<FocusIn>", lambda e: self.root.lower())
        
        self.session_active = False
        self.current_target_url = ""
        self.pwa_process = None
        
        # Données de suivi du temps
        self.initial_daily_minutes = get_total_minutes_today()
        self.session_seconds = 0
        
        # --- Interface du Launcher ---
        self.label_title = tk.Label(
            root, text="Plateforme Divertissement", 
            font=(FONT_FAMILY, 16, "bold"), fg="white", bg=COLOR_BG, pady=25
        )
        self.label_title.pack()

        # Dictionnaire pour stocker les composants des boutons
        self.buttons = {}
        
        for name, url in SITES.items():
            btn = tk.Button(
                root, text=name, font=(FONT_FAMILY, 12),
                bg=COLOR_ACCENT, fg="white", activebackground=COLOR_ACCENT,
                bd=0, height=2, width=25,
                command=lambda n=name, u=url: self.start_session(n, u)
            )
            btn.pack(pady=10)
            self.buttons[name] = btn

        # --- Note de rappel en bas du widget ---
        self.label_note = tk.Label(
            root, text="NB : ferme tes fenêtres chrome",
            font=(FONT_FAMILY, 10, "italic"), fg="#A0AEC0", bg=COLOR_BG
        )
        # Le pack avec side="bottom" et pady pousse le texte tout en bas
        self.label_note.pack(side="bottom", pady=20)

        # --- Fenêtre du Chronomètre Transparent (cachée au début) ---
        self.timer_window = None
        self.label_timer = None

    def start_session(self, name, url):
        """Lance l'application sélectionnée et active le tracker."""
        if self.session_active:
            return 
            
        self.session_active = True
        self.current_target_url = url
        self.session_seconds = 0
        self.initial_daily_minutes = get_total_minutes_today()
        
        # 1. Bloquer visuellement l'interface du Launcher
        for btn_name, btn_widget in self.buttons.items():
            if btn_name == name:
                btn_widget.configure(bg="#2B6CB0", state="disabled") 
            else:
                btn_widget.configure(bg=COLOR_DISABLED, state="disabled") 

        # 2. Créer la fenêtre du Chronomètre Transparent floating
        self.create_transparent_timer()

        # 3. Lancer Chrome en mode PWA
        try:
            self.pwa_process = subprocess.Popen([CHROME_PATH, f"--app={url}"])
        except FileNotFoundError:
            messagebox.showerror("Erreur", "Google Chrome est introuvable.")
            self.reset_launcher_interface()
            return

        # 4. Lancer la surveillance de session dans un thread séparé
        threading.Thread(target=self.monitor_session, daemon=True).start()

    def create_transparent_timer(self):
        """Crée le widget de chronomètre transparent en haut à gauche."""
        self.timer_window = tk.Toplevel(self.root)
        self.timer_window.geometry("+10+10")
        self.timer_window.overrideredirect(True)
        self.timer_window.wm_attributes("-topmost", True) # Le timer reste visible pendant qu'on regarde la PWA
        self.timer_window.config(bg="black")
        self.timer_window.wm_attributes("-transparentcolor", "black")

        self.label_timer = tk.Label(
            self.timer_window, text="📺 Session : 00h00 | 📅 Jour : 00h00",
            font=(FONT_FAMILY, 14, "bold"), fg=COLOR_BLUE, bg="black"
        )
        self.label_timer.pack()
        self.update_timer_display()

    def update_timer_display(self):
        """Met à jour l'affichage du texte du chronomètre toutes les minutes."""
        if not self.session_active or not self.timer_window:
            return

        session_mins = self.session_seconds // 60
        total_mins = self.initial_daily_minutes + session_mins

        sh = session_mins // 60
        sm = session_mins % 60
        th = total_mins // 60
        tm = total_mins % 60

        timer_text = f"实用 Session : {sh:02d}h{sm:02d} | 📅 Jour : {th:02d}h{tm:02d}"

        if session_mins >= ALERT_MINUTES:
            timer_text += " (Fais une pause !)"
            self.label_timer.configure(fg=COLOR_RED)
            if self.session_seconds == ALERT_MINUTES * 60:
                threading.Thread(target=self.show_alert).start()
        else:
            self.label_timer.configure(fg=COLOR_BLUE)

        self.label_timer.configure(text=timer_text)

    def show_alert(self):
        """Affiche l'alerte Windows sans bloquer le timer."""
        messagebox.showwarning(
            "Rappel de pause", 
            "Cela serait idéal de faire une pause après tant de temps, non ?"
        )

    def is_chrome_pwa_open(self):
        """Vérifie si la fenêtre Chrome applicative spécifique est toujours active."""
        try:
            for proc in psutil.process_iter(['cmdline']):
                cmd = proc.info.get('cmdline')
                if cmd and f"--app={self.current_target_url}" in "".join(cmd):
                    return True
        except Exception:
            pass
        return False

    def monitor_session(self):
        """Boucle de fond qui suit le temps et attend la fermeture de Chrome."""
        time.sleep(2) 
        
        while self.session_active:
            if not self.is_chrome_pwa_open():
                self.end_session()
                break
                
            time.sleep(1)
            self.session_seconds += 1
            
            if self.session_seconds % 60 == 0 or self.session_seconds == 1:
                self.root.after(0, self.update_timer_display)

    def end_session(self):
        """Ferme le chronomètre, sauvegarde et réactive le Launcher automatiquement."""
        self.session_active = False
        
        final_session_minutes = self.session_seconds // 60
        final_daily_minutes = self.initial_daily_minutes + final_session_minutes
        save_total_minutes_today(final_daily_minutes)

        if self.timer_window:
            self.root.after(0, self.timer_window.destroy)
            self.timer_window = None

        self.root.after(0, self.reset_launcher_interface)

    def reset_launcher_interface(self):
        """Rend à nouveau tous les boutons cliquables et remet le widget en arrière-plan."""
        for name, btn_widget in self.buttons.items():
            btn_widget.configure(bg=COLOR_ACCENT, state="normal")
        self.root.lower()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()