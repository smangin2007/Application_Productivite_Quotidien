import os
import sys
import time
import subprocess
import psutil
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# --- CONFIGURATION ---
FONT_FAMILY = "Montserrat"
FONT_SIZE = 14
COLOR_BLUE = "#1A365D"       # Bleu foncé
COLOR_RED = "#E53E3E"        # Rouge clair
ALERT_MINUTES = 50           # Seuil pour la pause

# Cible du divertissement (Modifie l'URL selon tes besoins)
TARGET_URL = "https://www.youtube.com"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Fichier de log pour le divertissement (séparé du fichier de jeu !)
LOG_FILE = os.path.join(os.path.expanduser("~"), "divertissement_daily_timer.txt")

def get_total_minutes_today():
    """Récupère le temps total de divertissement déjà accumulé aujourd'hui."""
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
    """Sauvegarde le temps total de divertissement du jour."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    with open(LOG_FILE, "w") as f:
        f.write(f"{today_str}|{minutes}")

class TransparentTimer:
    def __init__(self, chrome_process):
        self.root = tk.Tk()
        self.chrome_process = chrome_process
        
        # Initialisation du temps
        self.initial_daily_minutes = get_total_minutes_today()
        self.session_seconds = 0
        self.alert_triggered = False

        # Fenêtre transparente et sans bordure
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")
        
        # Positionnement en haut à gauche (X: 10, Y: 10)
        self.root.geometry("+10+10")

        # Label avec fond noir (qui sera rendu invisible grâce à transparentcolor)
        self.label = tk.Label(
            self.root, 
            text="", 
            font=(FONT_FAMILY, FONT_SIZE, "bold"), 
            fg=COLOR_BLUE, 
            bg="black"
        )
        self.label.pack()

        # Premier lancement de la boucle de mise à jour
        self.update_timer()

    def update_timer(self):
        """Met à jour le chronomètre et vérifie si Chrome est toujours en vie."""
        # 1. Vérification de l'état de Chrome
        if not self.is_chrome_running():
            self.on_closing()
            return

        # 2. Calcul du temps
        self.session_seconds += 1
        session_minutes = self.session_seconds // 60
        total_daily_minutes = self.initial_daily_minutes + session_minutes

        sh, sm = divmod(session_minutes, 60)
        dh, dm = divmod(total_daily_minutes, 60)

        # Formatage sans les secondes (anti-oppression)
        display_text = f"📺 Session : {sh:02d}h{sm:02d} | 📅 Jour : {dh:02d}h{dm:02d}"

        # 3. Gestion du seuil d'alerte (50 minutes)
        if session_minutes >= ALERT_MINUTES:
            display_text += " (Prends une pause !)"
            self.label.config(fg=COLOR_RED)
            
            if not self.alert_triggered:
                self.alert_triggered = True
                self.root.after(100, self.show_alert)
        else:
            self.label.config(fg=COLOR_BLUE)

        self.label.config(text=display_text)

        # Sauvegarde auto de sécurité toutes les minutes
        if self.session_seconds % 60 == 0:
            save_total_minutes_today(total_daily_minutes)

        # Rappel de la fonction dans 1 seconde (1000ms)
        self.root.after(1000, self.update_timer)

    def is_chrome_running(self):
        """Vérifie si notre instance de PWA Chrome spécifique tourne encore."""
        try:
            # On vérifie si le processus d'origine existe encore
            if self.chrome_process.poll() is None:
                return True
            
            # Double sécurité : on cherche si une fenêtre Chrome avec l'argument app est active
            for proc in psutil.process_iter(['cmdline']):
                cmd = proc.info.get('cmdline')
                if cmd and f"--app={TARGET_URL}" in "".join(cmd):
                    return True
        except Exception:
            pass
        return False

    def show_alert(self):
        """Affiche la boîte de dialogue Windows pour la pause."""
        messagebox.showwarning(
            "Rappel de pause", 
            "Cela serait idéal de faire une pause après tant de temps, non ?"
        )
        self.root.lift()

    def on_closing(self):
        """Sauvegarde finale et fermeture propre du widget."""
        final_session_minutes = self.session_seconds // 60
        final_daily_minutes = self.initial_daily_minutes + final_session_minutes
        save_total_minutes_today(final_daily_minutes)
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    # Lancement de Google Chrome en mode application (PWA)
    # L'argument --app= transforme l'onglet en fenêtre d'application autonome
    try:
        pwa_process = subprocess.Popen([CHROME_PATH, f"--app={TARGET_URL}"])
    except FileNotFoundError:
        print("Erreur : Google Chrome est introuvable au chemin spécifié.")
        sys.exit()

    # Pause d'une seconde pour laisser la fenêtre s'ouvrir avant d'attacher le tracker
    time.sleep(1)

    # Lancement du widget de tracking
    app = TransparentTimer(pwa_process)
    app.root.mainloop()