import os
import sys
from datetime import datetime
from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView

# --- CONFIGURATION ---
URL_DEPART = "https://www.youtube.com"

# Fichier de sauvegarde pour le divertissement web (séparé de Playnite)
LOG_FILE_WEB = os.path.join(os.path.expanduser("~"), "web_entertainment_timer.txt")

# Dossier où seront stockés tes cookies, ton cache et tes connexions (Persistance)
PROFILE_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "MonEspaceDivertissement", "MoteurWeb")

class DivertissementApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Espace Divertissement Web")
        
        # 1) OUVERTURE MAXIMISÉE (Prend tout l'écran en laissant la barre des tâches)
        self.showMaximized()
        self.is_fullscreen = False
        
        # Initialisation du chronomètre journalier
        self.initial_daily_minutes = self.get_total_minutes_today()
        self.session_seconds = 0
        
        # 2) CONFIGURATION DU NAVIGATEUR PERSISTANT (Garde les connexions)
        os.makedirs(PROFILE_DIR, exist_ok=True)
        self.profil = QWebEngineProfile("MonProfilDivertissement", self)
        self.profil.setPersistentStoragePath(PROFILE_DIR)
        self.profil.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        
        # Création de la vue web associée au profil persistant
        self.navigateur = QWebEngineView(self)
        self.web_page = self.navigateur.page() # Accès à la page
        # Lie la page au profil personnalisé créé juste au-dessus
        self.navigateur.setPage(type(self.web_page)(self.profil, self.navigateur))
        
        self.navigateur.setUrl(QUrl(URL_DEPART))
        
        # Mise en page (Layout) sans bordures intérieures
        layout = QVBoxLayout()
        layout.addWidget(self.navigateur)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # 3) INITIALISATION DU TIMER (Mise à jour à la seconde)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000) # S'exécute toutes les 1000ms (1 seconde)

    def get_total_minutes_today(self):
        """Lit le fichier texte pour récupérer le temps déjà accumulé aujourd'hui."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(LOG_FILE_WEB):
            with open(LOG_FILE_WEB, "r") as f:
                lines = f.readlines()
                if lines:
                    try:
                        date_part, mins_part = lines[0].strip().split("|")
                        if date_part == today_str:
                            return int(mins_part)
                    except ValueError:
                        return 0
        return 0

    def save_total_minutes_today(self, minutes):
        """Sauvegarde le cumul des minutes du jour dans le fichier texte."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        with open(LOG_FILE_WEB, "w") as f:
            f.write(f"{today_str}|{minutes}")

    def update_timer(self):
        """Incrémente le temps et sauvegarde automatiquement chaque minute."""
        self.session_seconds += 1
        
        # Sauvegarde automatique en tâche de fond toutes les minutes
        if self.session_seconds % 60 == 0:
            session_minutes = self.session_seconds // 60
            total_global = self.initial_daily_minutes + session_minutes
            self.save_total_minutes_today(total_global)

    def keyPressEvent(self, event):
        """Permet de basculer en VRAI plein écran ou d'en sortir en pressant F11."""
        if event.key() == Qt.Key.Key_F11:
            if not self.is_fullscreen:
                self.showFullScreen()
                self.is_fullscreen = True
            else:
                self.showMaximized()
                self.is_fullscreen = False
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Action déclenchée automatiquement dès que la fenêtre est fermée."""
        final_session_minutes = self.session_seconds // 60
        final_daily_minutes = self.initial_daily_minutes + final_session_minutes
        self.save_total_minutes_today(final_daily_minutes)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = DivertissementApp()
    fenetre.show()
    sys.exit(app.exec())