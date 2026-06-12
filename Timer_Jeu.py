import os
import sys
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# --- CONFIGURATION ---
FONT_FAMILY = "Montserrat"
FONT_SIZE = 14
COLOR_BLUE = "#1A365D"       # Bleu foncé
COLOR_RED = "#E53E3E"        # Rouge clair
ALERT_MINUTES = 50        # Seuil pour la pause

# Fichier temporaire pour stocker le temps total de la journée
LOG_FILE = os.path.join(os.path.expanduser("~"), "playnite_daily_timer.txt")

def get_total_minutes_today():
    """Récupère le temps total déjà joué aujourd'hui dans le fichier log."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            if lines:
                date_part, mins_part = lines[0].strip().split("|")
                if date_part == today_str:
                    return int(mins_part)
    return 0

def save_total_minutes_today(minutes):
    """Sauvegarde le temps total joué aujourd'llui."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    with open(LOG_FILE, "w") as f:
        f.write(f"{today_str}|{minutes}")

class GameTimerOverlay:
    def __init__(self):
        self.root = tk.Tk()
        
        # Initialisation des compteurs (en secondes)
        self.session_seconds = 0
        self.initial_daily_minutes = get_total_minutes_today()
        self.alert_triggered = False
        
        # Configuration de la fenêtre transparente et sans bordure
        self.root.overrideredirect(True)  # Supprime le cadre, les boutons fermer/réduire
        self.root.wm_attributes("-topmost", True)  # Toujours au-dessus
        self.root.wm_attributes("-transparentcolor", "black")  # Rend le fond noir invisible
        self.root.config(bg="black")
        
        # Positionnement en haut à gauche (décalage de 20px pour respirer)
        self.root.geometry("+20+20")
        
        # Création du label pour le texte
        self.label = tk.Label(
            self.root, 
            text="", 
            font=(FONT_FAMILY, FONT_SIZE, "bold"), 
            fg=COLOR_BLUE, 
            bg="black"
        )
        self.label.pack()
        
        # Liaison de l'événement de fermeture pour sauvegarder avant de quitter
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Lancement de la boucle de mise à jour
        self.update_timer()
        
    def format_time(self, total_minutes):
        """Formatte les minutes en xxhxx."""
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}h{minutes:02d}"

    def update_timer(self):
        self.session_seconds += 1
        session_minutes = self.session_seconds // 60
        total_daily_minutes = self.initial_daily_minutes + session_minutes
        
        # Formatage des textes
        session_str = self.format_time(session_minutes)
        daily_str = self.format_time(total_daily_minutes)
        
        display_text = f"🎮 Session : {session_str} | 📅 Jour : {daily_str}"
        
        # Gestion du seuil des 50 minutes
        if session_minutes >= ALERT_MINUTES:
            display_text += " (Pense à faire une pause !)"
            self.label.config(fg=COLOR_RED)
            
            # Déclenche l'alerte Windows une seule fois
            if not self.alert_triggered:
                self.alert_triggered = True
                # Utilisation d'un callback après 100ms pour ne pas figer l'interface
                self.root.after(100, self.show_alert)
        else:
            self.label.config(fg=COLOR_BLUE)
            
        # Mise à jour du texte affiché
        self.label.config(text=display_text)
        
        # Sauvegarde automatique toutes les minutes (au cas où)
        if self.session_seconds % 60 == 0:
            save_total_minutes_today(total_daily_minutes)
            
        # Rappel de la fonction toutes les 1000ms (1 seconde)
        self.root.after(1000, self.update_timer)
        
    def show_alert(self):
        """Affiche la boîte de dialogue Windows."""
        messagebox.showwarning(
            "Rappel de pause", 
            "Cela serait idéal de faire une pause après tant de temps, non ?"
        )
        # Remet le focus sur la fenêtre (même si elle est transparente) pour éviter les bugs
        self.root.lift()

    def on_closing(self):
        """Action exécutée à la fermeture du script."""
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