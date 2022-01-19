""" RIP_lay
    Simulation simplifiée du protocole RIP
    Sur la base de l'exercice 5 du sujet zéro du baccalauréat
    de la session 2021 de NSI
    https://pixees.fr/informatiquelycee/term/suj_bac/2021/sujet_1.pdf
    par Eric Buonocore le 18/01/2022

    Objectifs:
      + Visualiser l'ensemble des tables de routage d'un petit réseau
      + Pas de notion d'adresses IP (ni de masques)
      + Aborder les notions de passerelles, de route
      + Faire le lien avec la notion de graphe
      (noeuds/routeurs, arêtes/liaisons ou segmentde réseau)
      + Visualiser la propagation de l'information dans les tables de routage
      + Observer la stabilisation du système après des perturbations
      + Visualiser la construction et la mise à jour des routes

    Contraintes:
      + Pour rester lisible: les noeuds doivent avoir des noms courts
      (moins de 3 caractères)
      + Le réseau ne doit pas compter un trop grand nombre de routeurs
      (un dizaine au  maximum)

    Sources images Freepix obtenues via flaticon.com pour les boutons:
          + Annuler
          + Configuration
          + Fusée
          + Paquet parachuté
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