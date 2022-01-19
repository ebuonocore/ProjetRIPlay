""" RIP_lay
    Simulation simplifiée du protocole RIP
"""

import RIP_lay_classes as rc
import RIP_lay_GUI as rgui

if __name__ == "__main__":
    réseau = rc.Réseau()
    # Instanciation du plateau de jeu
    fenêtre = rgui.Fenêtre(réseau)
    # Surveillance des clics sur le canevas
    fenêtre.tk.bind('<Button-1>', fenêtre.clic_gauche)
    fenêtre.tk.bind('<Button-3>', fenêtre.clic_droit)
    fenêtre.can.bind('<Motion>', fenêtre.mouvement_souris)
    # Redirection de la croix de fermeture de la fenêtre principale
    fenêtre.tk.protocol('WM_DELETE_WINDOW', fenêtre.fermer_fenêtre)
    fenêtre.tk.mainloop()
