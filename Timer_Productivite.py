import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from pygame import mixer
import time
import json
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
DOSSIER_SCRIPT = Path(__file__).parent.resolve()
FICHIER_SAUVEGARDE = DOSSIER_SCRIPT / "daily_stats.json"
FICHIER_SON_LEVELUP = DOSSIER_SCRIPT / "skyrim_levelup.mp3"
TAILLE_POLICE_HUD = 14
POLICE_PRINCIPALE = "Montserrat"

# Couleurs du HUD (Statistiques)
COULEUR_EN_COURS = "#008000"
COULEUR_PAUSE = "#1E90FF"
COULEUR_TERMINE = "#FFD700"

# --- CONFIGURATION DES RANGS ---
RANGS = [
    {"min": 600, "nom_prefixe": "(11) 👑 ", "mot": "LÉGENDE", "couleur": "#E2583E", "couleur_shine": "#FF8A75", "cycle_shine": 20000, "message_levelup": "Incroyable ! Vous avez atteint le sommet absolu. Vous êtes une véritable LÉGENDE ! 👑"}, 
    {"min": 470, "nom_prefixe": "(10) 🌟 ", "mot": "CHAMPION", "couleur": "#A335EE", "couleur_shine": "#D996FF", "cycle_shine": 30000, "message_levelup": "Quel exploit ! Vous entrez dans l'arène des plus grands. Rang CHAMPION débloqué ! 🌟"}, 
    {"min": 360, "nom_prefixe": "(9) 🔥 ", "mot": "HÉROS", "couleur": "#FF8000", "couleur_shine": "#FFAE59", "cycle_shine": 40000, "message_levelup": "Votre détermination inspire le respect. Vous êtes désormais un HÉROS ! 🔥"},       
    {"min": 260, "nom_prefixe": "(8) 🔱 ", "mot": "PALADIN", "couleur": "#0070DD", "couleur_shine": "#66B2FF", "cycle_shine": 50000, "message_levelup": "Une force inébranlable vous habite. Vous voilà élevé au rang de PALADIN ! 🔱"},     
    {"min": 180, "nom_prefixe": "(7) ⚔️ ", "mot": "CHEVALIER", "couleur": "#1EFF00", "couleur_shine": "#A3FF94", "cycle_shine": 60000, "message_levelup": "Adoubé pour votre assiduité ! Vous atteignez le rang de CHEVALIER ! ⚔️"}, 
    {"min": 120, "nom_prefixe": "(6) 🛡️ DÉFENSEUR", "couleur": "#00FFDD", "message_levelup": "Votre discipline devient votre meilleur bouclier. Vous êtes un DÉFENSEUR ! 🛡️"},
    {"min": 75,  "nom_prefixe": "(5) 🏟️ GLADIATEUR", "couleur": "#FFFF00", "message_levelup": "Vous maîtrisez le rythme de votre travail. Bienvenue au rang de GLADIATEUR ! 🏟️"},
    {"min": 45,  "nom_prefixe": "(4) 💰 MERCENAIRE", "couleur": "#B0B0B0", "message_levelup": "L'effort commence à porter ses fruits ! Vous passez MERCENAIRE ! 💰"},
    {"min": 25,  "nom_prefixe": "(3) 👁️ GARDIEN", "couleur": "#714321", "message_levelup": "Votre concentration s'aiguise. Vous débloquez le rang de GARDIEN ! 👁️"},
    {"min": 10,  "nom_prefixe": "(2) 🎒 AVENTURIER", "couleur": "#FFFFFF", "message_levelup": "Premier pas important ! Vous quittez l'état sauvage pour devenir AVENTURIER ! 🎒"},
    {"min": 0,   "nom_prefixe": "(1) 🌱 NOVICE", "couleur": "#90EE90", "message_levelup": ""}
]

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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

def charger_temps_du_jour():
    stats = lire_statistiques_jour()
    return stats["pro"], stats["perso"]

def sauvegarder_temps_du_jour(min_pro, min_perso):
    sauvegarder_statistiques_jour({"pro": min_pro, "perso": min_perso})

# --- APPLICATION PRINCIPALE ---
class LifeRPGApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.overrideredirect(True) 
        largeur_ecran = self.winfo_screenwidth()
        largeur_widget = 320
        hauteur_widget = 210  
        pos_x = largeur_ecran - largeur_widget - 20
        pos_y = 20
        self.geometry(f"{largeur_widget}x{hauteur_widget}+{pos_x}+{pos_y}")
        
        self.lower() 
        self.bind("<FocusIn>", lambda e: self.lower()) 
        self.attributes("-topmost", True) 
        self.config(bg='#1a1a1a')

        self.status = "STOPPED"
        self.session_minutes = 0
        
        self.jour_minutes_pro, self.jour_minutes_perso = charger_temps_du_jour()
        self.type_travail = "Pro" 
        
        self.sound_limit_minutes = 0
        self.secondes_accumulees = 0 
        
        self.rang_precedent = self.obtenir_rang_et_prochain()[0]
        
        self.lettre_brillante_index = -1
        self.id_animation_shine = None
        
        mixer.init()
        
        self.hud = None
        self.label_stats = None
        self.frame_basse = None
        
        self.label_prefixe = None
        self.label_mot_avant = None
        self.label_mot_brillant = None
        self.label_mot_apres = None
        self.label_barre = None 
        
        self.setup_ui()

    @property
    def jour_minutes(self):
        return self.jour_minutes_pro + self.jour_minutes_perso

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
        if self.status == "STOPPED" or not self.hud: return
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

    def declencher_popup_levelup(self, rang_actuel):
        if rang_actuel["min"] > 0 and FICHIER_SON_LEVELUP.exists():
            try:
                mixer.Sound(str(FICHIER_SON_LEVELUP)).play()
            except Exception as e: 
                print(f"Erreur audio Level Up : {e}")

        boite_forcee = tk.Toplevel()
        boite_forcee.withdraw()
        boite_forcee.attributes("-topmost", True)
        
        messagebox.showinfo(
            "⚡ MONTEE DE NIVEAU ! ⚡", 
            rang_actuel["message_levelup"],
            parent=boite_forcee
        )
        boite_forcee.destroy()

    def gerer_hud(self):
        if self.status == "STOPPED":
            if self.hud:
                if self.id_animation_shine: self.after_cancel(self.id_animation_shine)
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

        if self.status == "RUNNING":
            emoji_statut = "💼 [EN COURS]" if self.type_travail == "Pro" else "📓 [EN COURS]"
        else:
            emoji_statut = "🛡️ [EN PAUSE]" if self.status == "PAUSED" else "🏆 [TERMINÉ]"

        couleur_stats = COULEUR_EN_COURS if self.status == "RUNNING" else COULEUR_PAUSE if self.status == "PAUSED" else COULEUR_TERMINE
        
        h_sess, m_sess = divmod(self.session_minutes, 60)
        h_jour, m_jour = divmod(self.jour_minutes, 60)
        
        self.label_stats.config(
            text=f"{emoji_statut} Session: {h_sess:02d}h{m_sess:02d} | 📅 Jour Total: {h_jour:02d}h{m_jour:02d}", 
            fg=couleur_stats
        )

        rang_actuel, prochain_rang = self.obtenir_rang_et_prochain()
        
        if rang_actuel["nom_prefixe"] != self.rang_precedent["nom_prefixe"]:
            self.rang_precedent = rang_actuel
            if self.id_animation_shine: self.after_cancel(self.id_animation_shine)
            self.label_prefixe.config(text=rang_actuel["nom_prefixe"], fg=rang_actuel["couleur"])
            self.label_mot_avant.config(text=rang_actuel.get("mot", ""), fg=rang_actuel["couleur"])
            self.label_barre.config(text=self.generer_barre_progression(rang_actuel, prochain_rang), fg=rang_actuel["couleur"])
            
            self.declencher_popup_levelup(rang_actuel)
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

        self.frame_menus = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_menus.pack(pady=5, fill="x", padx=15)

        self.type_option = ctk.CTkOptionMenu(self.frame_menus, width=130, font=(POLICE_PRINCIPALE, 11), dropdown_font=(POLICE_PRINCIPALE, 11), values=["💼 Travail Pro", "📓 Travail Perso"], command=self.change_type_setting)
        self.type_option.pack(side="left", expand=True, padx=2)

        self.sound_option = ctk.CTkOptionMenu(self.frame_menus, width=150, font=(POLICE_PRINCIPALE, 11), dropdown_font=(POLICE_PRINCIPALE, 11), values=["Pas d'alerte sonore", "Alerte après 25 min", "Alerte après 50 min", "Alerte Custom (1 min)"], command=self.change_sound_setting)
        self.sound_option.pack(side="right", expand=True, padx=2)

        self.frame_boutons = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_boutons.pack(pady=10, fill="x", padx=20)

        self.btn_action = ctk.CTkButton(self.frame_boutons, text="Lancer", fg_color="green", font=(POLICE_PRINCIPALE, 11, "bold"), command=self.action_clic)
        self.btn_action.pack(side="left", expand=True, padx=5)

        self.btn_stop = ctk.CTkButton(self.frame_boutons, text="Arrêter", fg_color="#4a4a4a", state="disabled", font=(POLICE_PRINCIPALE, 11, "bold"), command=self.stop_timer)
        self.btn_stop.pack(side="right", expand=True, padx=5)

        self.btn_close = ctk.CTkButton(self, text="× Quitter l'application", fg_color="transparent", text_color="gray", hover_color="#2b2b2b", height=15, font=(POLICE_PRINCIPALE, 10), command=self.quit)
        self.btn_close.pack(side="bottom", pady=5)

    def generer_texte_total(self):
        h_pro, m_pro = divmod(self.jour_minutes_pro, 60)
        h_perso, m_perso = divmod(self.jour_minutes_perso, 60)
        return f"💼 Pro: {h_pro:02d}h{m_pro:02d} | 📓 Perso: {h_perso:02d}h{m_perso:02d}"

    def change_sound_setting(self, choice):
        self.sound_limit_minutes = 0 if choice == "Pas d'alerte sonore" else 25 if choice == "Alerte après 25 min" else 50 if choice == "Alerte après 50 min" else 1

    def change_type_setting(self, choice):
        self.type_travail = "Pro" if "Pro" in choice else "Perso"
        if self.status != "STOPPED":
            self.gerer_hud()

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
        self.status = "STOPPED"; self.session_minutes = 0; self.secondes_accumulees = 0
        if self.id_animation_shine: self.after_cancel(self.id_animation_shine); self.id_animation_shine = None
        self.btn_action.configure(text="Lancer", fg_color="green"); self.btn_stop.configure(state="disabled", fg_color="#4a4a4a")
        self.gerer_hud()

    def update_timer(self):
        if self.status == "RUNNING":
            self.secondes_accumulees += 1
            if self.secondes_accumulees >= 60:
                self.secondes_accumulees = 0; self.session_minutes += 1
                
                if self.type_travail == "Pro":
                    self.jour_minutes_pro += 1
                else:
                    self.jour_minutes_perso += 1
                    
                sauvegarder_temps_du_jour(self.jour_minutes_pro, self.jour_minutes_perso)
                self.label_total.configure(text=self.generer_texte_total())
                self.gerer_hud()
                
                if self.sound_limit_minutes > 0 and self.session_minutes >= self.sound_limit_minutes:
                    self.status = "FINISHED"
                    self.btn_action.configure(text="Relancer", fg_color="green")
                    self.gerer_hud()
                    self.play_alert_sound()
                    
                    boite_forcee = tk.Toplevel()
                    boite_forcee.withdraw()
                    boite_forcee.attributes("-topmost", True)
                    
                    messagebox.showinfo(
                        "Session Terminée", 
                        f"Félicitations ! Votre session de {self.sound_limit_minutes} min est terminée.",
                        parent=boite_forcee
                    )
                    boite_forcee.destroy()
                    return
            self.after(1000, self.update_timer)

    def play_alert_sound(self):
        try: mixer.music.load("notification.mp3"); mixer.music.play()
        except Exception: print("Alerte sonore de fin de session déclenchée.")

if __name__ == "__main__":
    app = LifeRPGApp()
    app.mainloop()