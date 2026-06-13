import tkinter as tk
from tkinter import messagebox  # Import pour la boîte de message Windows
import customtkinter as ctk
from pygame import mixer
import time
from pathlib import Path
from PIL import Image, ImageTk, ImageSequence

# --- CONFIGURATION ---
DOSSIER_SCRIPT = Path(__file__).parent.resolve()
FICHIER_SAUVEGARDE = DOSSIER_SCRIPT / "temps_travail.txt"
FICHIER_GIF_LEVELUP = DOSSIER_SCRIPT / "levelup.gif"
TAILLE_POLICE_HUD = 14
POLICE_PRINCIPALE = "Montserrat"

# Couleurs du HUD (Statistiques)
COULEUR_EN_COURS = "#008000"
COULEUR_PAUSE = "#1E90FF"
COULEUR_TERMINE = "#FFD700"

# --- CONFIGURATION DES RANGS ---
RANGS = [
    {"min": 600, "nom_prefixe": "(11) 👑 ", "mot": "LÉGENDE", "couleur": "#E2583E", "couleur_shine": "#FF8A75", "cycle_shine": 20000, "son": "level_legende.mp3", "duree_son": 13000, "gif_rang": "gif_legende.gif"}, 
    {"min": 470, "nom_prefixe": "(10) 🌟 ", "mot": "CHAMPION", "couleur": "#A335EE", "couleur_shine": "#D996FF", "cycle_shine": 30000, "son": "level_champion.mp3", "duree_son": 13000, "gif_rang": "gif_champion.gif"}, 
    {"min": 360, "nom_prefixe": "(9) 🔥 ", "mot": "HÉROS", "couleur": "#FF8000", "couleur_shine": "#FFAE59", "cycle_shine": 40000, "son": "level_heros.mp3", "duree_son": 10000, "gif_rang": "gif_heros.gif"},       
    {"min": 260, "nom_prefixe": "(8) 🔱 ", "mot": "PALADIN", "couleur": "#0070DD", "couleur_shine": "#66B2FF", "cycle_shine": 50000, "son": "level_paladin.mp3", "duree_son": 10000, "gif_rang": "gif_paladin.gif"},     
    {"min": 180, "nom_prefixe": "(7) ⚔️ ", "mot": "CHEVALIER", "couleur": "#1EFF00", "couleur_shine": "#A3FF94", "cycle_shine": 60000, "son": "level_chevalier.mp3", "duree_son": 8000, "gif_rang": "gif_chevalier.gif"}, 
    {"min": 120, "nom_prefixe": "(6) 🛡️ DÉFENSEUR", "couleur": "#00FFDD", "son": "level_defenseur.mp3", "duree_son": 8000, "gif_rang": "gif_defenseur.gif"},
    {"min": 75,  "nom_prefixe": "(5) 🏟️ GLADIATEUR", "couleur": "#FFFF00", "son": "level_gladiateur.mp3", "duree_son": 8000, "gif_rang": "gif_gladiateur.gif"},
    {"min": 45,  "nom_prefixe": "(4) 💰 MERCENAIRE", "couleur": "#B0B0B0", "son": "level_mercenaire.mp3", "duree_son": 5000, "gif_rang": "gif_mercenaire.gif"},
    {"min": 25,  "nom_prefixe": "(3) 👁️ GARDIEN", "couleur": "#714321", "son": "level_gardien.mp3", "duree_son": 5000, "gif_rang": "gif_gardien.gif"},
    {"min": 10,  "nom_prefixe": "(2) 🎒 AVENTURIER", "couleur": "#FFFFFF", "son": "level_aventurier.mp3", "duree_son": 5000, "gif_rang": "gif_aventurier.gif"},
    {"min": 0,   "nom_prefixe": "(1) 🌱 NOVICE", "couleur": "#90EE90", "son": None, "duree_son": 0, "gif_rang": None}
]

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def charger_temps_du_jour():
    date_aujourdhui = time.strftime("%Y-%m-%d")
    if FICHIER_SAUVEGARDE.exists():
        with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
            contenu = f.read().strip()
            if not contenu or "|" not in contenu:
                return 0
            try:
                date_sauvegardee, minutes = contenu.split("|")
                if date_sauvegardee == date_aujourdhui:
                    return int(minutes)
            except ValueError:
                return 0
    return 0

def sauvegarder_temps_du_jour(minutes):
    date_aujourdhui = time.strftime("%Y-%m-%d")
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        f.write(f"{date_aujourdhui}|{minutes}")

class LifeRPGApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.overrideredirect(True) 
        largeur_ecran = self.winfo_screenwidth()
        largeur_widget = 320
        hauteur_widget = 150  # Réduction de la hauteur car le menu de test a été supprimé
        pos_x = largeur_ecran - largeur_widget - 20
        pos_y = 20
        self.geometry(f"{largeur_widget}x{hauteur_widget}+{pos_x}+{pos_y}")
        
        self.lower() 
        self.bind("<FocusIn>", lambda e: self.lower()) 
        self.attributes("-topmost", True) 
        self.config(bg='#1a1a1a')

        self.status = "STOPPED"
        self.session_minutes = 0
        self.jour_minutes = charger_temps_du_jour()
        self.sound_limit_minutes = 0
        self.secondes_accumulees = 0 
        
        self.rang_precedent = self.obtenir_rang_et_prochain()[0]
        self.en_animation_levelup = False
        self.opacite_actuelle = 1.0
        
        self.lettre_brillante_index = -1
        self.id_animation_shine = None
        self.id_animation_gif = None
        
        mixer.init()
        
        self.hud = None
        self.label_stats = None
        self.frame_basse = None
        self.label_gif_levelup = None
        self.label_gif_custom = None
        
        self.label_prefixe = None
        self.label_mot_avant = None
        self.label_mot_brillant = None
        self.label_mot_apres = None
        self.label_barre = None 
        
        self.frames_levelup = []
        self.caches_gifs_rangs = {} 
        self.charger_tous_les_gifs()
        
        self.setup_ui()

    def decouper_gif(self, chemin_fichier, dimension=(160, 50)):
        liste_frames = []
        if chemin_fichier and chemin_fichier.exists():
            try:
                im = Image.open(chemin_fichier)
                for frame in ImageSequence.Iterator(im):
                    frame_res = frame.copy().convert("RGBA").resize(dimension, Image.Resampling.LANCZOS)
                    liste_frames.append(ImageTk.PhotoImage(frame_res))
            except Exception as e:
                print(f"Erreur découpage GIF ({chemin_fichier.name}) : {e}")
        return liste_frames

    def charger_tous_les_gifs(self):
        self.frames_levelup = self.decouper_gif(FICHIER_GIF_LEVELUP, (160, 45))
        for rang in RANGS:
            if rang["gif_rang"]:
                chemin_gif = DOSSIER_SCRIPT / rang["gif_rang"]
                if chemin_gif.exists():
                    self.caches_gifs_rangs[rang["gif_rang"]] = self.decouper_gif(chemin_gif, (160, 55))

    def animer_gifs_conjointement(self, index_levelup=0, index_custom=0):
        if not self.hud or not self.en_animation_levelup:
            if self.label_gif_levelup: self.label_gif_levelup.pack_forget()
            if self.label_gif_custom: self.label_gif_custom.pack_forget()
            return

        rang_actuel = self.rang_precedent

        if self.frames_levelup:
            img_lu = self.frames_levelup[index_levelup]
            self.label_gif_levelup.config(image=img_lu)
            index_levelup = (index_levelup + 1) % len(self.frames_levelup)

        nom_gif_custom = rang_actuel["gif_rang"]
        if nom_gif_custom and nom_gif_custom in self.caches_gifs_rangs:
            frames_custom = self.caches_gifs_rangs[nom_gif_custom]
            if frames_custom:
                img_cust = frames_custom[index_custom]
                self.label_gif_custom.config(image=img_cust)
                index_custom = (index_custom + 1) % len(frames_custom)

        self.id_animation_gif = self.after(50, lambda: self.animer_gifs_conjointement(index_levelup, index_custom))

    def obtenir_rang_et_prochain(self):
        for i, rang in enumerate(RANGS):
            if self.jour_minutes >= rang["min"]:
                prochain_rang = RANGS[i-1] if i > 0 else None
                return rang, prochain_rang
        return RANGS[-1], RANGS[-2]

    def generer_barre_progression(self, rang_actuel, prochain_rang):
        if not prochain_rang:
            return " [■■■■■■■■■■] 100% (MAX)"
        min_actuel = rang_actuel["min"]
        min_prochain = prochain_rang["min"]
        total_palier = min_prochain - min_actuel
        minutes_acquises = self.jour_minutes - min_actuel
        pourcentage = max(0, min(int((minutes_acquises / total_palier) * 100), 100))
        blocs_remplis = pourcentage // 10
        return f" [{'■' * blocs_remplis}{'□' * (10 - blocs_remplis)}] {pourcentage}%"

    def planifier_prochain_cycle_brillance(self, delai_ms):
        if self.id_animation_shine: self.after_cancel(self.id_animation_shine)
        self.lettre_brillante_index = -1
        self.id_animation_shine = self.after(delai_ms, self.executer_brillance_lettre)

    def executer_brillance_lettre(self):
        if self.status == "STOPPED" or not self.hud or self.en_animation_levelup: return
        rang_actuel, _ = self.obtenir_rang_et_prochain()
        if "mot" not in rang_actuel: return
        mot = rang_actuel["mot"]
        self.lettre_brillante_index += 1
        if self.lettre_brillante_index >= len(mot):
            self.label_mot_avant.config(text=mot, fg=rang_actuel["couleur"])
            self.label_mot_brillant.config(text="", fg=rang_actuel["couleur"])
            self.label_mot_apres.config(text="", fg=rang_actuel["couleur"])
            self.planifier_prochain_cycle_brillance(rang_actuel["cycle_shine"])
            return
        self.label_mot_avant.config(text=mot[:self.lettre_brillante_index], fg=rang_actuel["couleur"])
        self.label_mot_brillant.config(text=mot[self.lettre_brillante_index], fg=rang_actuel["couleur_shine"])
        self.label_mot_apres.config(text=mot[self.lettre_brillante_index + 1:], fg=rang_actuel["couleur"])
        self.id_animation_shine = self.after(120, self.executer_brillance_lettre)

    def fade_in(self):
        if not self.hud or not self.en_animation_levelup: return
        if self.opacite_actuelle < 1.0:
            self.opacite_actuelle += 0.1
            self.hud.wm_attributes("-alpha", self.opacite_actuelle)
            self.after(30, self.fade_in)

    def fade_out(self):
        if not self.hud: return
        if self.opacite_actuelle > 0.0:
            self.opacite_actuelle -= 0.1
            self.hud.wm_attributes("-alpha", self.opacite_actuelle)
            self.after(30, self.fade_out)
        else:
            self.en_animation_levelup = False
            if self.label_gif_levelup: self.label_gif_levelup.pack_forget()
            if self.label_gif_custom: self.label_gif_custom.pack_forget()
            self.opacite_actuelle = 1.0
            self.hud.wm_attributes("-alpha", 1.0)
            self.gerer_hud()

    def jouer_son_et_declencher_double_gif(self, rang_actuel):
        self.en_animation_levelup = True
        if rang_actuel["son"]:
            try:
                mixer.Sound(str(DOSSIER_SCRIPT / rang_actuel["son"])).play()
            except Exception as e: print(f"Erreur audio : {e}")

        self.opacite_actuelle = 0.0
        self.hud.wm_attributes("-alpha", 0.0)
        self.fade_in()

        if self.frames_levelup and self.label_gif_levelup:
            self.label_gif_levelup.pack(anchor="w", pady=(4, 0))
        nom_gif_custom = rang_actuel["gif_rang"]
        if nom_gif_custom and nom_gif_custom in self.caches_gifs_rangs and self.label_gif_custom:
            self.label_gif_custom.pack(anchor="w", pady=(2, 0))

        self.animer_gifs_conjointement()
        self.after(max(500, rang_actuel["duree_son"] - 400), self.fade_out)

    def gerer_hud(self):
        if self.status == "STOPPED" and not self.en_animation_levelup:
            if self.hud:
                if self.id_animation_shine: self.after_cancel(self.id_animation_shine)
                if self.id_animation_gif: self.after_cancel(self.id_animation_gif)
                self.hud.destroy()
                self.hud = None
            return

        if not self.hud:
            self.hud = tk.Toplevel(self)
            self.hud.overrideredirect(True)
            self.hud.geometry("+20+20")  
            self.hud.lift()
            self.hud.wm_attributes("-topmost", True)
            self.hud.wm_attributes("-disabled", True)
            self.hud.wm_attributes("-transparentcolor", "black")
            self.hud.config(bg="black")

            self.label_stats = tk.Label(self.hud, font=(POLICE_PRINCIPALE, TAILLE_POLICE_HUD, "bold"), bg="black")
            self.label_stats.pack(anchor="w")
            self.frame_basse = tk.Frame(self.hud, bg="black")
            self.frame_basse.pack(anchor="w", pady=(2, 0))
            
            self.label_prefixe = tk.Label(self.frame_basse, font=(POLICE_PRINCIPALE, TAILLE_POLICE_HUD, "bold"), bg="black")
            self.label_prefixe.pack(side="left")
            self.label_mot_avant = tk.Label(self.frame_basse, font=(POLICE_PRINCIPALE, TAILLE_POLICE_HUD, "bold"), bg="black")
            self.label_mot_avant.pack(side="left")
            self.label_mot_brillant = tk.Label(self.frame_basse, font=(POLICE_PRINCIPALE, TAILLE_POLICE_HUD, "bold"), bg="black")
            self.label_mot_brillant.pack(side="left")
            self.label_mot_apres = tk.Label(self.frame_basse, font=(POLICE_PRINCIPALE, TAILLE_POLICE_HUD, "bold"), bg="black")
            self.label_mot_apres.pack(side="left")
            self.label_barre = tk.Label(self.frame_basse, font=(POLICE_PRINCIPALE, TAILLE_POLICE_HUD - 1, "bold"), bg="black")
            self.label_barre.pack(side="left")
            
            self.label_gif_levelup = tk.Label(self.hud, bg="black")
            self.label_gif_custom = tk.Label(self.hud, bg="black")

        if self.en_animation_levelup: return

        prefixe = "⚔️ [EN COURS]" if self.status == "RUNNING" else "🛡️ [EN PAUSE]" if self.status == "PAUSED" else "🏆 [TERMINÉ]"
        couleur_stats = COULEUR_EN_COURS if self.status == "RUNNING" else COULEUR_PAUSE if self.status == "PAUSED" else COULEUR_TERMINE
        h_sess, m_sess = divmod(self.session_minutes, 60)
        h_jour, m_jour = divmod(self.jour_minutes, 60)
        self.label_stats.config(text=f"{prefixe} Session: {h_sess:02d}h{m_sess:02d} | 📅 Jour: {h_jour:02d}h{m_jour:02d}", fg=couleur_stats)

        rang_actuel, prochain_rang = self.obtenir_rang_et_prochain()
        
        if rang_actuel["nom_prefixe"] != self.rang_precedent["nom_prefixe"]:
            self.rang_precedent = rang_actuel
            if self.id_animation_shine: self.after_cancel(self.id_animation_shine)
            self.label_prefixe.config(text=rang_actuel["nom_prefixe"], fg=rang_actuel["couleur"])
            self.label_mot_avant.config(text=rang_actuel.get("mot", ""), fg=rang_actuel["couleur"])
            self.label_barre.config(text=self.generer_barre_progression(rang_actuel, prochain_rang), fg=rang_actuel["couleur"])
            self.jouer_son_et_declencher_double_gif(rang_actuel)
            return

        self.label_prefixe.config(text=rang_actuel["nom_prefixe"], fg=rang_actuel["couleur"])
        self.label_barre.config(text=self.generer_barre_progression(rang_actuel, prochain_rang), fg=rang_actuel["couleur"])

        if "mot" in rang_actuel:
            if not self.id_animation_shine:
                self.label_mot_avant.config(text=rang_actuel["mot"], fg=rang_actuel["couleur"])
                self.label_mot_brillant.config(text="", fg=rang_actuel["couleur"])
                self.label_mot_apres.config(text="", fg=rang_actuel["couleur"])
                self.planifier_prochain_cycle_brillance(2000)
        else:
            if self.id_animation_shine: self.after_cancel(self.id_animation_shine); self.id_animation_shine = None
            self.label_mot_avant.config(text="", fg=rang_actuel["couleur"])

    def setup_ui(self):
        self.label_total = ctk.CTkLabel(self, text=self.generer_texte_total(), font=(POLICE_PRINCIPALE, 13, "bold"), text_color="#aaaaaa")
        self.label_total.pack(pady=(15, 5))

        self.sound_option = ctk.CTkOptionMenu(self, font=(POLICE_PRINCIPALE, 12), dropdown_font=(POLICE_PRINCIPALE, 12), values=["Pas d'alerte sonore", "Alerte après 25 min", "Alerte après 50 min", "Alerte Custom (1 min)"], command=self.change_sound_setting)
        self.sound_option.pack(pady=5)

        self.frame_boutons = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_boutons.pack(pady=10, fill="x", padx=20)

        self.btn_action = ctk.CTkButton(self.frame_boutons, text="Lancer", fg_color="green", font=(POLICE_PRINCIPALE, 11, "bold"), command=self.action_clic)
        self.btn_action.pack(side="left", expand=True, padx=5)

        self.btn_stop = ctk.CTkButton(self.frame_boutons, text="Arrêter", fg_color="#4a4a4a", state="disabled", font=(POLICE_PRINCIPALE, 11, "bold"), command=self.stop_timer)
        self.btn_stop.pack(side="right", expand=True, padx=5)

        self.btn_close = ctk.CTkButton(self, text="× Quitter l'application", fg_color="transparent", text_color="gray", hover_color="#2b2b2b", height=15, font=(POLICE_PRINCIPALE, 10), command=self.quit)
        self.btn_close.pack(side="bottom", pady=5)

    def generer_texte_total(self):
        h_jour, m_jour = divmod(self.jour_minutes, 60)
        return f"📊 TEMPS TOTAL DU JOUR : {h_jour:02d}h{m_jour:02d}"

    def change_sound_setting(self, choice):
        self.sound_limit_minutes = 0 if choice == "Pas d'alerte sonore" else 25 if choice == "Alerte après 25 min" else 50 if choice == "Alerte après 50 min" else 1

    def action_clic(self):
        if self.status in ["STOPPED", "PAUSED"]:
            self.status = "RUNNING"
            self.btn_action.configure(text="Pause", fg_color="#1f538d")
            self.btn_stop.configure(state="normal", fg_color="red")
            self.gerer_hud()
            self.update_timer()
        elif self.status == "RUNNING":
            self.status = "PAUSED"
            self.btn_action.configure(text="Reprendre", fg_color="green")
            self.gerer_hud()

    def stop_timer(self):
        self.status = "STOPPED"; self.session_minutes = 0; self.secondes_accumulees = 0; self.en_animation_levelup = False
        if self.id_animation_shine: self.after_cancel(self.id_animation_shine); self.id_animation_shine = None
        if self.id_animation_gif: self.after_cancel(self.id_animation_gif); self.id_animation_gif = None
        self.btn_action.configure(text="Lancer", fg_color="green"); self.btn_stop.configure(state="disabled", fg_color="#4a4a4a")
        self.gerer_hud()

    def update_timer(self):
        if self.status == "RUNNING":
            self.secondes_accumulees += 1
            if self.secondes_accumulees >= 60:
                self.secondes_accumulees = 0; self.session_minutes += 1; self.jour_minutes += 1
                sauvegarder_temps_du_jour(self.jour_minutes)
                self.label_total.configure(text=self.generer_texte_total())
                self.gerer_hud()
                
                if self.sound_limit_minutes > 0 and self.session_minutes >= self.sound_limit_minutes:
                    self.status = "FINISHED"
                    self.btn_action.configure(text="Relancer", fg_color="green")
                    self.gerer_hud()
                    self.play_alert_sound()
                    
                    # --- ASTUCE POUR FORCER LE PREMIER PLAN ABSOLU ---
                    # Création d'une fenêtre de support invisible
                    boite_forcee = tk.Toplevel()
                    boite_forcee.withdraw()  # On cache la fenêtre principale de support
                    boite_forcee.attributes("-topmost", True)  # On la positionne au premier plan absolu
                    
                    # On affiche l'alerte attachée à ce support prioritaire
                    messagebox.showinfo(
                        "Session Terminée", 
                        f"Félicitations ! Votre session de {self.sound_limit_minutes} min est terminée.",
                        parent=boite_forcee
                    )
                    
                    # Nettoyage de la fenêtre de support après fermeture de l'alerte
                    boite_forcee.destroy()
                    return
            self.after(1000, self.update_timer)

    def play_alert_sound(self):
        try: mixer.music.load("notification.mp3"); mixer.music.play()
        except Exception: print("Alerte sonore de fin déclenchée.")

if __name__ == "__main__":
    app = LifeRPGApp()
    app.mainloop()