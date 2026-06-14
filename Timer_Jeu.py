import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# --- CONFIGURATION ---
FONT_FAMILY = "Montserrat"
FONT_SIZE = 14
COLOR_BLUE = "#1A365D"       # Bleu foncé
COLOR_RED = "#E53E3E"        # Rouge clair
ALERT_MINUTES = 50           # Seuil pour la pause

DOSSIER_SCRIPT = Path(__file__).parent.resolve()
FICHIER_SAUVEGARDE = DOSSIER_SCRIPT / "daily_stats.json"

# --- FONCTIONS DE SAUVEGARDE CENTRALISEES ---
def lire_statistiques_jour():
    aujourdhui = datetime.now().strftime("%Y-%m-%d")
    stats_defaut = {"pro": 0, "perso": 0, "jeu": 0, "divertissement": 0}
    if FICHIER_SAUVEGARDE.exists():
        try:
            with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if aujourdhui in data:
                    stats_defaut.update(data[aujourdhui])
                    return stats_defaut
        except json.JSONDecodeError:
            pass
    return stats_defaut

def sauvegarder_statistiques_jour(nouvelles_valeurs):
    aujourdhui = datetime.now().strftime("%Y-%m-%d")
    data = {}
    if FICHIER_SAUVEGARDE.exists():
        try:
            with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
    if aujourdhui not in data:
        data[aujourdhui] = {"pro": 0, "perso": 0, "jeu": 0, "divertissement": 0}
        
    data[aujourdhui].update(nouvelles_valeurs)
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_total_minutes_today():
    return lire_statistiques_jour()["jeu"]

def save_total_minutes_today(minutes):
    sauvegarder_statistiques_jour({"jeu": minutes})

# --- APPLICATION PRINCIPALE ---
class GameTimerOverlay:
    def __init__(self):
        self.root = tk.Tk()
        
        self.session_seconds = 0
        self.initial_daily_minutes = get_total_minutes_today()
        self.alert_triggered = False
        
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.config(bg="black")
        
        self.root.geometry("+20+20")
        
        self.label = tk.Label(
            self.root, 
            text="", 
            font=(FONT_FAMILY, FONT_SIZE, "bold"), 
            fg=COLOR_BLUE, 
            bg="black"
        )
        self.label.pack()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_timer()
        
    def format_time(self, total_minutes):
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}h{minutes:02d}"

    def update_timer(self):
        self.session_seconds += 1
        session_minutes = self.session_seconds // 60
        total_daily_minutes = self.initial_daily_minutes + session_minutes
        
        session_str = self.format_time(session_minutes)
        daily_str = self.format_time(total_daily_minutes)
        
        display_text = f"🎮 Session : {session_str} | 📅 Jour : {daily_str}"
        
        if session_minutes >= ALERT_MINUTES:
            display_text += " (Pense à faire une pause !)"
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
        
    def show_alert(self):
        messagebox.showwarning(
            "Rappel de pause", 
            "Cela serait idéal de faire une pause après tant de temps, non ?"
        )
        self.root.lift()

    def on_closing(self):
        final_session_minutes = self.session_seconds // 60
        final_daily_minutes = self.initial_daily_minutes + final_session_minutes
        save_total_minutes_today(final_daily_minutes)
        self.root.destroy()

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

if __name__ == "__main__":
    app = GameTimerOverlay()
    app.run()