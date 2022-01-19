from tkinter import filedialog as fd
from tkinter import font as tkfont
import tkinter as tki  # Importation de la bibliothèque  Tkinter
from PIL import Image, ImageTk
import RIP_lay_outils as ro
import RIP_lay_classes as rc
import json


class Fenêtre:
    COULEUR_MODIF = '#801010'
    COULEUR_TEXTE = 'black'
    COULEUR_FLUX = '#007000'
    COULEUR_FLUX_HS = '#703020'
    TABLE_LARGEUR = 84
    TABLE_LIGNE_HAUTEUR = 13
    """ Fenêtre Tkinter:
          + Affichage des noeuds et des liaisons dans le Réseau
          + Boutons zoom +/- []
          + Ajout d'un noeud
          + Ajout de liaison
          + Vitesse de simulation +/-
          + Création d'un paquet
    """

    def __init__(self, réseau):
        self.tk = tki.Tk()
        self.tk.title('RIPlay')
        self.réseau = réseau
        # Délai entre chaque mise à jour en mode automatique (en ms)
        self.période_auto = 500
        self.charger_préférences()
        self.état = 1
        # Mémorisation des états précédents du système
        self.retour= rc.Refaire(100)
        """ Etats possibles
            1: Etat normal: Sélection de boutons, animation arrêtée.
            2: Création de noeud. En attente du placement du noeud.
            3: Suppression de noeud. Attente de sélection du noeud à supprimer.
            4: Edition d'un noeud: Saisie des champs Label, Couleur.
            6: Déplacement d'un noeud.Jusqu'au point d'ancrage sélectionné.
            7: Ajout du départ d'une liaison. Sélection du noeud d'origine.
            8: Ajout de la destination d'une liaison.
                Sélection du noeud de destination.
            9: Créer un paquet. Sélection du noeud source du flux de paquets.
            10: Déposer un paquet. Sélection du noeud destination du flux.
            11: Mode automatique. Neutralise la sélection.
                Attente de passage au mode Pas à pas (Etat 1).
            12: Noeud en cours de déplacement
        """
        # Noeud cible de l'action à exécuter. None si aucun noeud visé.
        self.noeud_cible = None
        self.WIDTH, self.HEIGHT = self.dimensions()
        # Indique si les paquets doivent être relancés
        self.flux_paquets = False
        # Indique si les tables de routage doivent être affichées
        self.vue = True
        # Fenêtre principale
        self.can = tki.Canvas(self.tk, width=self.WIDTH,
                              height=self.HEIGHT, bg='white')
        # Zone du menu
        self.menu = tki.Canvas(self.tk, width=self.WIDTH, height=80,
                               bg='#F0F0F0')
        self.menu_label = tki.Label(self.menu)
        self.menu_label.pack(padx=1, pady=1, fill=tki.X, side=tki.LEFT)
        self.texte_message = tki.StringVar()
        self.texte_message.set('\n')
        self.message = tki.Label(self.menu, textvariable=self.texte_message)
        self.message.pack(side=tki.LEFT)
        # Importation de la banque d'images dans un dictionnaire
        self.images = self.construire_banque_images()
        self.boutons = {}
        self.ajouter_boutons()  # Construction du dictionnaire des boutons
        self.menu.pack(fill=tki.X)
        self.can.pack()
        self.afficher()

    def charger_préférences(self):
        """ Charge les informations stockées dans le fichiers préférences.json
            et met à jour les attributs du réseau et du paquet
        """
        with open('préférences.json', 'r') as fichier:
            sauvegarde = json.load(fichier)
        self.période_auto = sauvegarde['Période_auto']
        self.réseau.infini = sauvegarde['infini']
        self.réseau.ttl_route = sauvegarde['ttl_route']
        self.réseau.paquet.ttl_paquet = sauvegarde['ttl_paquet']
        self.réseau.maj_rapide = (sauvegarde['maj_rapide'] == 'oui')
        passerelle_par_défaut = (sauvegarde['passerelle_par_défaut'] == 'oui')
        self.réseau.passerelle_par_défaut = passerelle_par_défaut
        self.réseau.paquet.passerelle_par_défaut = passerelle_par_défaut

    def dimensions(self):
        WIDTH = self.tk.winfo_screenwidth()
        HEIGHT = self.tk.winfo_screenheight()
        return WIDTH, HEIGHT

    def afficher(self):
        """ Met à jour l'affichage du réseau dans la fenêtre Tkinter
        """
        normal_font = tkfont.Font(family="Consolas", size=12, weight="bold")
        table_font = tkfont.Font(family="Consolas", size=8, weight="normal")
        table_paquet_font = tkfont.Font(family="Consolas", size=8,
                                        weight="bold")
        # if self.flux_paquets:
        self.réseau.paquet.résoudre_route()
        # Mise à jour des tailles de noeuds
        self.réseau.mettre_à_jour_tailles_noeuds(
            Fenêtre.TABLE_LARGEUR, Fenêtre.TABLE_LIGNE_HAUTEUR)
        # Efface tous les objets du canevas avant de les recréer
        self.can.delete("all")
        # Trace les arêtes
        # Set de tuples (xA, yA, xB, yB): A noeud origine, B destination.
        arêtes_tracées = set()
        for noeud in self.réseau.noeuds:
            x, y = noeud.position
            x, y = int(x + noeud.taille[0]/2),\
                int(y + Fenêtre.TABLE_LIGNE_HAUTEUR)
            for voisin in noeud.voisins:
                x1, y1 = voisin.position
                x1, y1 = int(x1 + noeud.taille[0]/2),\
                    int(y1 + Fenêtre.TABLE_LIGNE_HAUTEUR)
                couleur_trait = None
                largeur_trait = 2
                # Ne trace l'arête que si l'arête opposée
                # n'a pas déjà été tracée.
                if (voisin, noeud) not in arêtes_tracées:
                    arêtes_tracées.add((noeud, voisin))
                    couleur_trait = 'grey'
                # Identifie une liaisons sur la route du paquet
                if ro.est_un_segment(noeud, voisin, self.réseau.paquet):
                    couleur_trait = 'green'
                    largeur_trait = 6
                    if not self.réseau.paquet.route_valide():
                        couleur_trait = Fenêtre.COULEUR_FLUX_HS
                # Identifie le segment à supprimer
                if (noeud, voisin) == self.réseau.liaison_cible:
                    couleur_trait = 'red'
                if couleur_trait is not None:
                    self.can.create_line(x, y, x1, y1, width=largeur_trait,
                                         fill=couleur_trait)
        # Trace les noeuds
        for noeud in self.réseau.noeuds:
            x, y = noeud.position
            # Dimension globale du neoud
            x1, y1 = int(x + noeud.taille[0]), int(y + noeud.taille[1])
            # Rectangle du titre
            x2, y2 = int(x + noeud.taille[0]), int(y + 20)
            x_array = [x, x1, x1, x]
            y_array1 = [y, y, y1, y1]
            y_array2 = [y, y, y2, y2]
            couleur_fond = ro.plus_clair(noeud.couleur)
            couleur_bord = ro.plus_sombre(noeud.couleur)
            if len(noeud.lignes_modifiées) != 0:
                couleur_bord = Fenêtre.COULEUR_MODIF
            if self.vue:
                self.roundPolygon(x_array, y_array1, 4, width=1,
                                  outline=couleur_bord, fill=couleur_fond)
                # Affiche les textes
                # Affiche le label du noeud
                x, y = noeud.position
                x, y = x+10, y+30
                for destination, (distance, passerelle, ttl) in\
                        noeud.table.items():
                    # Affiche les passerelles et les métriques
                    if distance > 0:
                        texte = str(destination.label) + ' ' + chr(0x2192) +\
                                ' ' + str(passerelle.label) + ':' + \
                                str(distance)
                        if destination in noeud.lignes_modifiées:
                            couleur_texte = Fenêtre.COULEUR_MODIF
                        else:
                            couleur_texte = Fenêtre.COULEUR_TEXTE
                        if ro.est_sur_la_route(noeud, destination, passerelle,
                                               self.réseau.paquet):
                            police = table_paquet_font
                            couleur_texte = 'white'
                            xa = x-5
                            ya = y-Fenêtre.TABLE_LIGNE_HAUTEUR//2
                            xb = xa+Fenêtre.TABLE_LARGEUR-10
                            yb = ya+Fenêtre.TABLE_LIGNE_HAUTEUR
                            if self.réseau.paquet.route_valide():
                                couleur_flux = Fenêtre.COULEUR_FLUX
                            else:
                                couleur_flux = Fenêtre.COULEUR_FLUX_HS
                            couleur_bordure = ro.plus_clair(couleur_flux)
                            self.can.create_rectangle(xa, ya, xb, yb,
                                                      fill=couleur_flux,
                                                      outline=couleur_bordure)
                        else:
                            police = table_font
                        self.can.create_text(x, y, text=texte, font=police,
                                             anchor='w', fill=couleur_texte)
                        y += Fenêtre.TABLE_LIGNE_HAUTEUR
            # Dessin de l'entête du noeud (avec label et indicateur de flux)
            self.roundPolygon(x_array, y_array2, 4, width=3,
                              outline=couleur_bord, fill=noeud.couleur)
            # Affiche le label du noeud
            x, y = noeud.position
            x, y = x+5, y+10
            label_noeud = str(noeud.label)
            # Ajoute l'indicateur de flux: Départ ou arrivée des paquets
            if noeud == self.réseau.paquet.source:
                label_noeud += chr(0x2690)
            if noeud == self.réseau.paquet.destination:
                label_noeud += chr(0x2691)
            self.can.create_text(x, y, text=label_noeud,
                                 anchor='w', font=normal_font)

    def importer_image(self, banque, nom):
        """ Importe l'image en fonction du nom passé en paramètre
            et l'associe à une clef du dictionnaire banque
        """
        fichier = 'images/' + nom + '.png'
        image = Image.open(fichier)
        banque[nom] = ImageTk.PhotoImage(image)

    def construire_banque_images(self):
        banque = {}
        self.importer_image(banque, 'nouveau')
        self.importer_image(banque, 'ouvrir')
        self.importer_image(banque, 'enregistrer')
        self.importer_image(banque, 'ajouter_noeud')
        self.importer_image(banque, 'supprimer_noeud')
        self.importer_image(banque, 'éditer')
        self.importer_image(banque, 'déplacer')
        self.importer_image(banque, 'ajouter_liaison')
        self.importer_image(banque, 'supprimer_liaison')
        self.importer_image(banque, 'avancer')
        self.importer_image(banque, 'retour')
        self.importer_image(banque, 'lancer')
        self.importer_image(banque, 'lancer_stop')
        self.importer_image(banque, 'poser_paquet')
        self.importer_image(banque, 'poser_paquet_stop')
        self.importer_image(banque, 'vue')
        self.importer_image(banque, 'vue_stop')
        self.importer_image(banque, 'information')
        self.importer_image(banque, 'configuration')
        return banque

    def créer_bouton(self, nom, commande):
        self.boutons[nom] = tki.Button(self.menu_label,
                                       image=self.images[nom],
                                       command=commande)

    def ajouter_boutons(self):
        """ Ajoute les boutons
        """
        # self.créer_bouton('inter_Fichiers', self.cmd_pass)
        self.créer_bouton('nouveau', self.cmd_nouveau)
        self.créer_bouton('ouvrir', self.cmd_ouvrir)
        self.créer_bouton('enregistrer', self.cmd_enregistrer)
        # self.créer_bouton('inter_Noeuds', self.cmd_pass)
        self.créer_bouton('ajouter_noeud', self.cmd_ajouter_noeud)
        self.créer_bouton('supprimer_noeud', self.cmd_supprimer_noeud)
        self.créer_bouton('éditer', self.cmd_éditer)
        self.créer_bouton('déplacer', self.cmd_déplacer)
        # self.créer_bouton('inter_Liaisons', self.cmd_pass)
        self.créer_bouton('ajouter_liaison', self.cmd_ajouter_liaison)
        self.créer_bouton('supprimer_liaison', self.cmd_supprimer_liaison)
        # self.créer_bouton('inter_Actions', self.cmd_pass)
        self.créer_bouton('retour', self.cmd_retour)
        self.créer_bouton('avancer', self.cmd_avancer)
        self.créer_bouton('lancer', self.cmd_lancer)
        self.créer_bouton('poser_paquet', self.cmd_poser_paquet)
        self.créer_bouton('vue', self.cmd_vue)
        self.créer_bouton('information', self.cmd_information)
        self.créer_bouton('configuration', self.cmd_configuration)
        for clef_bouton, bouton in self.boutons.items():
            bouton.pack(side=tki.LEFT)

    def état_réseau(self):
        """ Construit le dictionnaire sauvegarde, image de l'état du réseau
            en vue d'un enregistrement au format JSON ou une mémorisation.
            Les routes où figurent des passerelles et des destinations détruites
            ne sont pas enregistrées.
        """
        sauvegarde = {}
        for noeud in self.réseau.noeuds:
            sauvegarde[noeud.idx()] = {}
            sauvegarde[noeud.idx()]['label'] = noeud.label
            sauvegarde[noeud.idx()]['couleur'] = noeud.couleur
            sauvegarde[noeud.idx()]['position'] = noeud.position
            sauvegarde[noeud.idx()]['voisins'] = []
            for voisin in noeud.voisins:
                sauvegarde[noeud.idx()]['voisins'].append(voisin.idx())
            sauvegarde[noeud.idx()]['table'] = {}
            for destination, (distance, passerelle, ttl) in noeud.table.items():
                if destination in self.réseau.noeuds\
                        and passerelle in self.réseau.noeuds:
                    sauvegarde[noeud.idx()]['table'][destination.idx()] =\
                            [distance, passerelle.idx(), ttl]
        return sauvegarde

    def purger_réseau(self):
        """ Nettoie le contenu du réseau actuel: Noeuds, tables de routage
        """
        for noeud in self.réseau.noeuds:
            noeud.table = {noeud: [0, noeud, 0]}
            del noeud
        self.réseau.noeuds = []

    def charger_état(self, sauvegarde):
        """ Reconstruit l'état du réseau décrit par le dictionnaire sauvegarde.
            Remarque: Certaines référence à des noeuds détruits subsistent.
            Il faut le recréer à la volée.
        """
        self.purger_réseau()
        # Instanciation de tous les noeuds qui doivent apparaître
        dico_noeuds = {}  # Fait le lien entre l'id_noeud et l'instance créée
        for id_noeud in sauvegarde.keys():
            noeud = rc.Noeud(sauvegarde[id_noeud]['label'],
                             self.réseau.infini, self.réseau.maj_rapide)
            dico_noeuds[id_noeud] = noeud
            noeud.couleur = sauvegarde[id_noeud]['couleur']
            noeud.position = sauvegarde[id_noeud]['position']
            self.réseau.noeuds.append(noeud)
        # Alimentation de la liste des voisins
        for id_noeud in sauvegarde.keys():
            noeud = dico_noeuds[id_noeud]
            for id_voisin in sauvegarde[id_noeud]['voisins']:
                if id_voisin not in dico_noeuds.keys():
                    voisin = self.réseau.créer_noeud()
                else:
                    voisin = dico_noeuds[id_voisin]
                noeud.voisins.append(voisin)
            # Alimentation des tables de routage
            for id_destination, (distance, id_passerelle, ttl) in\
                    sauvegarde[id_noeud]['table'].items():
                if id_destination not in dico_noeuds.keys():
                    destination = self.réseau.créer_noeud()
                else:
                    destination = dico_noeuds[id_destination]
                if id_passerelle not in dico_noeuds.keys():
                    passerelle = self.réseau.créer_noeud()
                else:
                    passerelle = dico_noeuds[id_passerelle]
                noeud.table[destination] = [distance, passerelle, ttl]

    def avancer_auto(self):
        """ Tant que self.réseau.animation est à True,
            Lance la méthode self.avancer et
            relance l'animation au bout de self.période_auto
            (500ms par défaut)
        """
        if self.réseau.animation:
            self.réseau.mettre_à_jour_tables()
            # Mémorise l'état actuel
            sauvegarde = self.état_réseau()
            self.retour.ajouter(sauvegarde)
            self.afficher()
            self.tk.after(self.période_auto, self.avancer_auto)

    def cmd_nouveau(self):
        """ Vide la liste des noeuds et réinitialise l'instace de Réseau
        """
        self.état = 30
        self.texte_message.set('')
        self.can.config(cursor="arrow")
        self.purger_réseau()
        self.réseau = rc.Réseau()
        self.cmd_avancer()

    def cmd_ouvrir(self):
        """ Ouvre le fichier JSON sélectionné et reconstruit l'instance de
            Réseau
            Puis, créé les voisins et les tables
            Renvoie True si la procédure aboutit sinon False
        """
        fichier_sélectionné = fd.askopenfilename(title='Ouvrir')
        if fichier_sélectionné == '':
            self.texte_message.set('Ouverture abandonnée')
            return False
        with open(fichier_sélectionné, 'r') as fichier:
            sauvegarde = json.load(fichier)
        self.charger_état(sauvegarde)
        self.afficher()
        return True

    def cmd_enregistrer(self):
        """ Enregistre la configuration du réseau dans un fichier au
            format JSON.
            liste des noeuds (Nom, liste des voisins, position, couleur,
            contenu de la table)
        """
        self.texte_message.set('')
        sauvegarde = self.état_réseau()
        types = [('JSON', '*.json')]
        fichier_sélectionné = fd.asksaveasfile(
            title='Enregistrer', filetypes=types, defaultextension=types[0])
        if fichier_sélectionné is not None:
            with open(fichier_sélectionné.name, 'w') as fichier:
                json.dump(sauvegarde, fichier)
                return True
        else:
            self.texte_message.set('Enregistrement abandonné')
            return False

    def cmd_ajouter_noeud(self):
        """ Ajoute un nouveau noeud dans le réseau
        """
        self.texte_message.set('Positionnez le nouveau noeud')
        self.can.config(cursor="plus")
        self.noeud_cible = self.réseau.créer_noeud()
        self.état = 2  # Déplacement du noeud créé

    def cmd_supprimer_noeud(self):
        """ Supprime le noeud qui sera sélectionné
        """
        self.texte_message.set('Sélectionnez le noeud à supprimer')
        self.can.config(cursor="target")
        self.état = 3

    def cmd_éditer(self):
        """ Permet d'éditer le label et la couleur du noeud qui sera
            sélectionné
        """
        # Arrête l'animation s'il est en cours
        if self.réseau.animation:
            self.cmd_lancer()
        self.texte_message.set('Sélectionnez le noeud à éditer')
        self.can.config(cursor="pencil")
        self.état = 4

    def cmd_déplacer(self):
        """ Permet de déplacer un noeud
        """
        self.texte_message.set('Sélectionnez le noeud à déplacer')
        self.can.config(cursor="fleur")
        self.état = 6

    def cmd_ajouter_liaison(self):
        """ Ajoute une liaison entre deux noeuds
        """
        self.texte_message.set('Sélectionner le noeud source de la liaison')
        self.can.config(cursor="cross")
        self.état = 7

    def cmd_supprimer_liaison(self):
        """ Supprime la liaison qui sera sélectionnée
        """
        self.texte_message.set('Sélectionner la liaison à supprimer')
        self.can.config(cursor="target")
        self.état = 13

    def cmd_retour(self):
        """ Recharge l'état précédent
        """
        # Arrêt de l'animation
        self.réseau.animation = False
        self.boutons['lancer'].config(image=self.images['lancer'])
        self.état = 1
        sauvegarde = self.retour.retirer()
        reste = self.retour.dimension()
        if sauvegarde is None:
            self.texte_message.set("Aucune sauvegarde")
        else:
            self.charger_état(sauvegarde)
            self.texte_message.set("Etat précédent rechargé. Reste " + str(reste))
            self.afficher()

    def cmd_avancer(self):
        """ Passe au tour suivant. Met à jour les tables.
        """
        # self.texte_message.set('Avance pas à pas')
        # Arrêt de l'animation
        self.réseau.animation = False
        self.boutons['lancer'].config(image=self.images['lancer'])
        # Mémorise l'état actuel
        sauvegarde = self.état_réseau()
        self.retour.ajouter(sauvegarde)
        # Avance d'un tour
        self.réseau.mettre_à_jour_tables()
        self.afficher()

    def cmd_lancer(self):
        """ Lance l'animation. Chaque tour est lancé automatiquement
            au bout d'un laps de temps. Par défaut 500ms.
        """
        if self.réseau.animation:
            self.texte_message.set('')
            self.réseau.animation = False
            self.boutons['lancer'].config(image=self.images['lancer'])
        else:
            self.texte_message.set('Mode animation: 1 tour toutes les ' +
                                   str(self.période_auto) + 'ms')
            self.réseau.animation = True
            self.boutons['lancer'].config(image=self.images['lancer_stop'])
            self.avancer_auto()

    def cmd_poser_paquet(self):
        """ Routage d'un flux de paquets: Sélection du noeud source
            puis du noeud destination
        """
        if self.flux_paquets:
            self.texte_message.set('')
            self.boutons['poser_paquet'].config(image=self.images['poser_paquet'])
            # Initialise un paquet vide (sans source ni destination)
            self.réseau.paquet = rc.Paquet(self.réseau.passerelle_par_défaut)
            self.flux_paquets = False
            self.afficher()
            self.état = 1
        else:
            self.can.config(cursor="dot")
            self.texte_message.set('Sélectionnez le noeud source ' +
                                   chr(0x2690)+' du flux de paquets')
            self.état = 9

    def cmd_information(self):
        """ Ouvre la fenêtre annexe contenant les descriptions des boutons
            et la licence
        """
        # Arrête l'animation si elle est en cours
        if self.réseau.animation:
            self.cmd_lancer()
        Fenêtre_information(self.tk, self.images)

    def cmd_configuration(self):
        """ Ouvre la fenêtre de paramétrage des préférences
        """
        # Arrête l'animation s'elle est en cours
        if self.réseau.animation:
            self.cmd_lancer()
        Fenêtre_configuration(self)

    def cmd_vue(self):
        """ Bascule l'état de l'indicateur vue.
            Cet indicateur valide l'affichage des tables de routage
            si il est à True
        """
        if self.vue:
            self.vue = False
            self.texte_message.set('Masque les tables de routage')
            self.boutons['vue'].config(image=self.images['vue'])
        else:
            self.vue = True
            self.texte_message.set('Affiche les tables de routage')
            self.boutons['vue'].config(image=self.images['vue_stop'])
        self.afficher()

    def maj_afficher(self, event):
        """ L'affichage est lancé suite à la surveillance d'un évènement
        """
        self.afficher()

    def retour_état_initial(self):
        """ Replace le système dans l'état initial
        """
        self.état = 1
        self.afficher()
        self.can.config(cursor="arrow")

    def clic_gauche(self, event):
        Xpix = event.x
        Ypix = event.y
        if self.état == 1:
            self.afficher()
            self.can.config(cursor="arrow")
        if self.état == 2:  # Création de noeud.
            self.retour_état_initial()
        elif self.état == 3:  # Suppression de noeud.
            noeud_à_supprimer = self.noeud_plus_proche(Xpix, Ypix)
            self.texte_message.set('')
            self.réseau.supprimer(noeud_à_supprimer)
            self.retour_état_initial()
        elif self.état == 4:  # Edition d'un noeud
            noeud_à_éditer = self.noeud_plus_proche(Xpix, Ypix)
            fen_édition = Fenêtre_édition(
                self.tk, noeud_à_éditer, self.réseau)
            # Surveille la destruction du bouton pour mettre à jour l'affichage
            fen_édition.bt_valider.bind('<Destroy>', self.maj_afficher)
            self.retour_état_initial()
        elif self.état == 6:  # Déplacement: Choix du noeud
            self.noeud_cible = self.noeud_plus_proche(Xpix, Ypix)
            self.état = 12
        elif self.état == 7:  # Ajout de liaison: Choix du noeud de départ
            self.can.config(cursor="cross_reverse")
            self.noeud_cible = self.noeud_plus_proche(Xpix, Ypix)
            self.texte_message.set("Sélectionner le noeud destination de " +
                                   "la liaison")
            self.état = 8
        elif self.état == 8:  # Ajout de liaison: Choix du noeud de destination
            noeud_destination = self.noeud_plus_proche(Xpix, Ypix)
            # Il ne faut pas tenir compte de cette liaison
            # si elle reboucle sur elle-même
            if noeud_destination != self.noeud_cible:
                noeud_destination.ajouter_voisin(self.noeud_cible)
                self.noeud_cible.ajouter_voisin(noeud_destination)
                self.afficher()
                self.cmd_ajouter_liaison()
        elif self.état == 9:  # Routage: Sélection de la source
            self.can.config(cursor="dot")
            self.noeud_cible = self.noeud_plus_proche(Xpix, Ypix)
            self.texte_message.set('Sélectionner le noeud destination ' +
                                   chr(0x2691) + ' du flux de paquets')
            self.état = 10
        elif self.état == 10:  # Routage: Sélection de la destination
            noeud_destination = self.noeud_plus_proche(Xpix, Ypix)
            self.texte_message.set('')
            # Instancie le nouveau paquet
            self.réseau.paquet = rc.Paquet(
                self.réseau.passerelle_par_défaut,
                self.noeud_cible,
                noeud_destination)
            self.flux_paquets = True
            self.boutons['poser_paquet'].config(
                image=self.images['poser_paquet_stop'])
            # Met à jour la route
            self.réseau.paquet.résoudre_route()
            self.retour_état_initial()
        elif self.état == 12:  # Déplacement: Sélection de la destination
            self.can.config(cursor="fleur")
            self.état = 6  # Reste en mode déplacement par défaut
        elif self.état == 13:  # Sélection de la liaison à supprimer
            # Renvoie un couple de noeud
            noeud_A, noeud_B = self.liaison_plus_proche(Xpix, Ypix)
            if noeud_A is not None:
                self.réseau.supprimer_liaison(noeud_A, noeud_B)
                self.afficher()
            self.réseau.liaison_cible = (None, None)
            self.retour_état_initial()
        else:
            self.afficher()

    def clic_droit(self, event):
        self.can.config(cursor="arrow")
        self.texte_message.set('')
        self.état = 1

    def mouvement_souris(self, event):
        Xpix = event.x
        Ypix = event.y
        # Déplacement du noeud cible créé
        if self.état == 2 or self.état == 12:
            if self.noeud_cible is not None:
                self.noeud_cible.position = (Xpix, Ypix)
            self.afficher()
        if self.état == 13:  # Phase de sélection de la liaison à supprimer
            self.réseau.liaison_cible = self.liaison_plus_proche(Xpix, Ypix)
            noeud_A, noeud_B = self.réseau.liaison_cible
            self.afficher()

    def noeud_plus_proche(self, x, y):
        """ Renvoie le noeud le plus proche de la position x, y
            Sinon, renvoie None
        """
        LIMITE_MIN = 10000  # Carré de la distance limite
        noeud_plus_proche, record = None, None
        for noeud in self.réseau.noeuds:
            xn, yn = noeud.position
            # distance2 est une surface
            # Comparaison des carrés des distances pour s'épargner
            # le calcul de la racine carrée
            distance2 = (x - xn)**2 + (y - yn)**2
            if record is None:
                record = distance2
                noeud_plus_proche = noeud
            elif distance2 < record:
                record = distance2
                noeud_plus_proche = noeud
        if record is None:
            return None
        elif record <= LIMITE_MIN:
            return noeud_plus_proche

    def liaison_plus_proche(self, xP, yP):
        """ Soit un point P (xP, yP),
            Renvoie le couple de noeuds qui représentent la liaison
            la plus proche de P.
            Sinon, renvoie (None, None)
        """
        MARGE = 10
        noeud_A, noeud_B = None, None
        record = None
        maj = False  # Faut-il mettre à jour le record ?
        for noeud in self.réseau.noeuds:
            xM, yM = noeud.position
            xM, yM = int(xM + noeud.taille[0]/2),\
                int(yM + Fenêtre.TABLE_LIGNE_HAUTEUR)
            for voisin in noeud.voisins:
                xN, yN = voisin.position
                xN, yN = int(xN + noeud.taille[0]/2),\
                    int(yN + Fenêtre.TABLE_LIGNE_HAUTEUR)
                distance = ro.distance_point_droite(xP, yP, xM, yM, xN, yN)
                if record is None:
                    maj = True
                elif distance < record:
                    maj = True
                    # La mise à jour n'est effective que si P est
                    # dans un rectangle dont les côtés sont // aux axes
                    # incluant M et N
                if maj:
                    if xP > min(xM, xN) - MARGE and xP < max(xM, xN)+MARGE\
                            and yP > min(yM, yN) - MARGE\
                            and yP < max(yM, yN) + MARGE:
                        noeud_A, noeud_B = noeud, voisin
                        record = distance
        return noeud_A, noeud_B

    def fermer_fenêtre(self):
        """ Redirection de la croix de fermeture de fenêtre de façon à fermer
            l'animation avant.
        """
        # S'assure que la relance automatique de l'animation est arrêtée
        if self.réseau.animation:
            self.réseau.animation = False
            self.tk.after(self.période_auto, self.fermer_fenêtre)
        else:
            self.tk.after(self.période_auto, self.fermer_définitivement)

    def fermer_définitivement(self):
        self.tk.quit()
        self.tk.destroy()

    def roundPolygon(self, x, y, sharpness, **kwargs):
        """ source: https://newbedev.com/how-to-make-a-tkinter-canvas-
                    rectangle-with-rounded-corners """
        # The sharpness here is just how close the sub-points
        # are going to be to the vertex. The more the sharpness,
        # the more the sub-points will be closer to the vertex.
        # (This is not normalized)
        if sharpness < 2:
            sharpness = 2
        ratioMultiplier = sharpness - 1
        ratioDividend = sharpness
        # Array to store the points
        points = []
        # Iterate over the x points
        for i in range(len(x)):
            # Set vertex
            points.append(x[i])
            points.append(y[i])
            # If it's not the last point
            if i != (len(x) - 1):
                # Insert submultiples points. The more the sharpness,
                # the more these points will be closer to the vertex.
                points.append((ratioMultiplier*x[i] + x[i + 1])/ratioDividend)
                points.append((ratioMultiplier*y[i] + y[i + 1])/ratioDividend)
                points.append((ratioMultiplier*x[i + 1] + x[i])/ratioDividend)
                points.append((ratioMultiplier*y[i + 1] + y[i])/ratioDividend)
            else:
                # Insert submultiples points.
                points.append((ratioMultiplier*x[i] + x[0])/ratioDividend)
                points.append((ratioMultiplier*y[i] + y[0])/ratioDividend)
                points.append((ratioMultiplier*x[0] + x[i])/ratioDividend)
                points.append((ratioMultiplier*y[0] + y[i])/ratioDividend)
                # Close the polygon
                points.append(x[0])
                points.append(y[0])
        return self.can.create_polygon(points, **kwargs, smooth=True)


class Fenêtre_édition():
    def __init__(self, tk, noeud, réseau):
        self.tk = tk
        self.noeud = noeud
        self.réseau = réseau
        self.fenêtre = tki.Toplevel(self.tk)
        self.fenêtre.geometry("250x100")
        self.fenêtre.title('Noeud')
        cadre = tki.Frame(self.fenêtre, width=250, height=100)
        cadre.columnconfigure(0, weight=70)
        cadre.columnconfigure(1, weight=180)
        tki.Label(cadre, text="Label", anchor='w').grid(row=0, column=0)
        self.titre_texte = tki.StringVar()
        self.titre_texte.set(self.noeud.label)
        self.titre = tki.Entry(cadre, textvariable=self.titre_texte)
        self.titre_texte.trace('w', self.valider_titre)
        self.titre.grid(row=0, column=1)
        tki.Label(cadre, text="Couleur", anchor='w').grid(row=1, column=0)
        self.couleur_texte = tki.StringVar()
        self.couleur_texte.set(self.noeud.couleur)
        self.couleur = tki.Entry(cadre, textvariable=self.couleur_texte)
        self.couleur_texte.trace('w', self.valider_couleur)
        self.couleur.grid(row=1, column=1)
        self.bt_valider = tki.Button(cadre, text="Valider",
                                     command=self.cmd_valider_édition)
        self.bt_valider.grid(row=2, columnspan=2)
        self.texte_message = tki.StringVar()
        self.texte_message.set('')
        self.message = tki.Label(cadre, textvariable=self.texte_message)
        self.message.grid(row=3, columnspan=2, sticky=tki.W)
        cadre.pack(fill=tki.BOTH)

    def valider_titre(self, var, index, mode):
        """ Lancé par la modification du label
            Modifie la couleur de fond  de la zone de saisie
            et le texte d'alerte si le label est trop long
        """
        texte = self.titre.get()
        if texte in self.réseau.ensemble_labels_noeuds():
            self.texte_message.set('Ce nom a déjà été donné')
            self.titre.config(bg='orange')
        elif len(texte) > 2:
            self.texte_message.set("Un label trop long perturbera l'affichage")
            self.titre.config(bg='orange')
        else:
            self.texte_message.set('')
            self.titre.config(bg='white')

    def valider_couleur(self, var, index, mode):
        """ Lancé par la modification de la valeur de la couleur
            Modifie la couleur de fond de la zone de saisie
            et le texte d'alerte si le label est trop long
        """
        if self.couleur_est_valide():
            self.texte_message.set('\n')
            self.couleur.config(bg='white')
        else:
            self.texte_message.set('Couleur invalide. Exemple: #9FA8DA')
            self.couleur.config(bg='red')

    def lire_couleur(self):
        """ Renvoie les six derniers caractères de la zone de saisie de la
            couleur en supprimant le premier caractère (a priori #)
            et en complétant de zéros devant si il y a moins de 6 caractères
        """
        couleur_saisie = '000000' + self.couleur.get()[1:]
        couleur_saisie = couleur_saisie[-6:]
        return couleur_saisie

    def couleur_est_valide(self):
        """ Renvoie True si couleur est une valur valide.
            C'est à dire au plus 6 chiffres hexa précédés d'un #
        """
        try:
            # Il faut que couleur_saisie puisse être convertie en hexa et
            # inférieure à #FFFFFF
            if int(self.lire_couleur(), 16) < int('ffffff', 16):
                return True
        except:
            return False

    def cmd_valider_édition(self):
        """ Valide les modificaiton apportée à self.noeud_cible
            à partir de la fenêtre Toplevel ouverte
            si le lable et la couleur sont valides
        """
        label = self.titre.get()
        if self.couleur_est_valide():
            self.noeud.label = label
            self.noeud.couleur = '#' + self.lire_couleur()
            # La destruction du bouton déclenche l'affichage du réseau
            self.bt_valider.destroy()
            self.fenêtre.destroy()


class Fenêtre_information():
    def __init__(self, tk, images):
        self.tk = tk
        # Dictionnaire d'images
        self.images = images
        self.fenêtre = tki.Toplevel(self.tk)
        self.fenêtre.geometry("400x300")
        self.fenêtre.title('Informations')
        self.afficher_infos()

    def afficher_infos(self):
        tableau_aide = []
        cadre = ro.ScrollableFrame(self.fenêtre)
        tableau_aide.append(('nouveau', "Créer une feuille vierge"))
        tableau_aide.append(('ouvrir', "Ouvrir un fichier"))
        tableau_aide.append(('enregistrer', "Enregistrer le réseau"))
        tableau_aide.append(('ajouter_noeud', "Ajouter un noeud"))
        tableau_aide.append(('supprimer_noeud', "Supprimer un noeud"))
        tableau_aide.append(('éditer',
                             "Editer le nom et la couleur d'un noeud"))
        tableau_aide.append(('déplacer', "Déplacer un noeud"))
        tableau_aide.append(('ajouter_liaison', "Ajouter une liaison"))
        tableau_aide.append(('supprimer_liaison', "Supprimer une liaison"))
        tableau_aide.append(('retour', "Défaire: Retour aux états précédents"))
        tableau_aide.append(('avancer', "Avancer pas à pas"))
        tableau_aide.append(('lancer',
                             "Avancement automatique: 1 tour toutes les" +
                             "500ms\nsource de l'image:Freepix"))
        tableau_aide.append(('poser_paquet',
                             "Désigner les extrémités d'un flux " +
                             "d'informations\nsource de l'image:Freepix"))
        tableau_aide.append(('vue',
                             "Faire apparaître/cacher les tables de " +
                             "routage\nsource de l'image:Freepix"))
        tableau_aide.append(('information', "Descriptif des menus et licence"))
        tableau_aide.append(('configuration', "Configuration des préférences" +
                             "(paramètres généraux)" +
                             "\nsource de l'image:Freepix"))
        for nom, texte in tableau_aide:
            ligne = tki.Frame(cadre.scrollable_frame)
            lbl_img = tki.Label(ligne, image=self.images[nom])
            lbl_txt = tki.Label(ligne, text=texte, justify=tki.LEFT,
                                anchor='w')
            lbl_img.pack(side=tki.LEFT, fill='both')
            lbl_txt.pack(fill='both')
            ligne.pack(fill='both', expand=True)
        titre = tki.Label(cadre.scrollable_frame,
                          text="RIP-lay par Eric Buonocore\n janvier 2022",
                          anchor='w')
        titre.pack(side=tki.BOTTOM)
        image_licence = Image.open('images/licence-by-nc-sa.png')
        image_licence_tk = ImageTk.PhotoImage(image_licence)
        label_image = tki.Label(cadre.scrollable_frame,
                                image=image_licence_tk)
        # Conserve une référence pour ne pas êre supprimé par le garbage-collector
        label_image.image = image_licence_tk
        label_image.pack(side=tki.BOTTOM)
        cadre.pack(fill=tki.BOTH)


class Fenêtre_configuration():
    def __init__(self, fenêtre_principale):
        self.fenêtre_principale = fenêtre_principale
        self.tk = self.fenêtre_principale.tk
        self.réseau = self.fenêtre_principale.réseau
        self.fenêtre = tki.Toplevel(self.tk)
        self.fenêtre.geometry("400x180")
        self.fenêtre.title('Préférences')
        cadre1 = tki.Frame(self.fenêtre, width=400, height=180)
        cadre1.columnconfigure(0, weight=320)
        cadre1.columnconfigure(1, weight=80)
        tki.Label(cadre1, text="Période d'un tour en mode automatique (ms)",
                  anchor='w').grid(row=0, column=0, sticky=tki.W)
        tki.Label(cadre1, text='Valeur maximale des distances',
                  anchor='w').grid(row=1, column=0, sticky=tki.W)
        tki.Label(cadre1, text='Durée de vie d\'une route perdue',
                  anchor='w').grid(row=2, column=0, sticky=tki.W)
        tki.Label(cadre1, text='Durée d\'un paquet',
                  anchor='w').grid(row=3, column=0, sticky=tki.W)
        self.période_auto_texte = tki.StringVar()
        self.période_auto_texte.set(self.fenêtre_principale.période_auto)
        self.période_auto_texte.trace('w', self.valider_Période_auto)
        self.période_auto_entry = tki.Entry(
            cadre1, textvariable=self.période_auto_texte)
        self.période_auto_entry.grid(row=0, column=1)
        self.infini_texte = tki.StringVar()
        self.infini_texte.set(self.réseau.infini)
        self.infini_texte.trace('w', self.valider_infini)
        self.infini_entry = tki.Entry(cadre1, textvariable=self.infini_texte)
        self.infini_entry.grid(row=1, column=1)
        self.ttl_route_texte = tki.StringVar()
        self.ttl_route_texte.set(self.réseau.ttl_route)
        self.ttl_route_texte.trace('w', self.valider_ttl_route)
        self.ttl_route_entry = tki.Entry(
            cadre1, textvariable=self.ttl_route_texte)
        self.ttl_route_entry.grid(row=2, column=1)
        self.ttl_paquet_texte = tki.StringVar()
        self.ttl_paquet_texte.set(self.réseau.paquet.ttl_paquet)
        self.ttl_paquet_texte.trace('w', self.valider_ttl_paquet)
        self.ttl_paquet_entry = tki.Entry(
            cadre1, textvariable=self.ttl_paquet_texte)
        self.ttl_paquet_entry.grid(row=3, column=1)
        cadre1.pack(fill=tki.X)
        cadre2 = tki.Frame(self.fenêtre, width=400, height=180)
        cadre2.columnconfigure(0, weight=400)
        txt = "Mise à jour rapide des tables en cas de suppression de liaison"
        cbt_maj_texte = txt
        self.cbt_maj_var = tki.StringVar()
        self.cbt_maj_rapide = tki.Checkbutton(cadre2, text=cbt_maj_texte,
                                              variable=self.cbt_maj_var,
                                              onvalue='oui', offvalue='non')
        if self.réseau.maj_rapide:
            self.cbt_maj_rapide.select()
        else:
            self.cbt_maj_rapide.deselect()
        self.cbt_maj_rapide.grid(row=0, column=0, sticky=tki.W)
        cbt_passerelle_texte = 'Passerelle par défaut: Premier noeud voisin'
        self.cbt_passerelle_var = tki.StringVar()
        self.cbt_passerelle_par_défaut = tki.Checkbutton(
            cadre2, text=cbt_passerelle_texte,
            variable=self.cbt_passerelle_var,
            onvalue='oui', offvalue='non')
        if self.réseau.passerelle_par_défaut:
            self.cbt_passerelle_par_défaut.select()
        else:
            self.cbt_passerelle_par_défaut.deselect()
        self.cbt_passerelle_par_défaut.grid(row=1, column=0, sticky=tki.W)
        self.bt_valider = tki.Button(cadre2, text="Valider",
                                     command=self.cmd_valider_préférences)
        self.bt_valider.grid(row=2, column=0)
        self.texte_message = tki.StringVar()
        self.texte_message.set('')
        self.message = tki.Label(cadre2, textvariable=self.texte_message)
        self.message.grid(row=3, column=0, sticky=tki.W)
        cadre2.pack(fill=tki.X)

    def est_valide(self, valeur, valeur_max):
        if valeur.isdigit():
            if 0 < int(valeur) < valeur_max:
                return True
        return False

    def valider_infini(self, var, index, mode):
        """ Lancé par la modification de la valeur maximale des distances
            Modifie la couleur de fond de la zone de saisie
            et le texte d'alerte si la valeur n'est pas comprise dans [0, 100]
        """
        if self.est_valide(self.infini_entry.get(), 100):
            self.texte_message.set('\n')
            self.infini_entry.config(bg='white')
        else:
            self.texte_message.set('Valeur non-valide')
            self.infini_entry.config(bg='red')

    def valider_ttl_route(self, var, index, mode):
        """ Lancé par la modification de la durée de vie d'une route perdue
            Modifie la couleur de fond de la zone de saisie
            et le texte d'alerte si la valeur n'est pas comprise dans [0, 100]
        """
        if self.est_valide(self.ttl_route_entry.get(), 100):
            self.texte_message.set('\n')
            self.ttl_route_entry.config(bg='white')
        else:
            self.texte_message.set('Valeur non-valide')
            self.ttl_route_entry.config(bg='red')

    def valider_Période_auto(self, var, index, mode):
        """ Lancé par la modification de période de relance en mode automatique
            Modifie la couleur de fond de la zone de saisie
            et le texte d'alerte si la valeur n'est pas
            comprise dans [0, 10000]
        """
        if self.est_valide(self.période_auto_entry.get(), 10000):
            self.texte_message.set('\n')
            self.période_auto_entry.config(bg='white')
        else:
            self.texte_message.set('Valeur non-valide')
            self.période_auto_entry.config(bg='red')

    def valider_ttl_paquet(self, var, index, mode):
        """ Lancé par la modification de la durée de vie d'un paquet perdu
            Modifie la couleur de fond de la zone de saisie
            eet le texte d'alerte si la valeur n'est pas
            comprise dans [0, 100]
        """
        if self.est_valide(self.ttl_paquet_entry.get(), 100):
            self.texte_message.set('\n')
            self.ttl_paquet_entry.config(bg='white')
        else:
            self.texte_message.set('Valeur non-valide')
            self.ttl_paquet_entry.config(bg='red')

    def cmd_valider_préférences(self):
        if self.est_valide(self.période_auto_entry.get(), 10000) and\
           self.est_valide(self.infini_entry.get(), 100) and\
           self.est_valide(self.ttl_route_entry.get(), 100) and\
           self.est_valide(self.ttl_paquet_entry.get(), 100):
            self.fenêtre_principale.période_auto =\
                    int(self.période_auto_entry.get())
            self.réseau.infini = int(self.infini_entry.get())
            self.réseau.ttl_route = int(self.ttl_route_entry.get())
            self.réseau.paquet.ttl_paquet = int(self.ttl_paquet_entry.get())
            sauvegarde = {}
            sauvegarde['Période_auto'] = int(self.période_auto_entry.get())
            sauvegarde['infini'] = int(self.infini_entry.get())
            sauvegarde['ttl_route'] = int(self.ttl_route_entry.get())
            sauvegarde['ttl_paquet'] = int(self.ttl_paquet_entry.get())
            sauvegarde['maj_rapide'] = self.cbt_maj_var.get()
            sauvegarde['passerelle_par_défaut'] = self.cbt_passerelle_var.get()
            self.fenêtre_principale = int(self.période_auto_entry.get())
            maj_rapide = (self.cbt_maj_var.get() == 'oui')
            self.réseau.maj_rapide = maj_rapide
            for noeud in self.réseau.noeuds:
                noeud.maj_rapide = maj_rapide
            cbt_passerelle = (self.cbt_passerelle_var.get() == 'oui')
            self.réseau.passerelle_par_défaut = cbt_passerelle
            self.réseau.paquet.passerelle_par_défaut = cbt_passerelle
            with open('préférences.json', 'w') as fichier:
                json.dump(sauvegarde, fichier)
            self.fenêtre.destroy()
        else:
            self.texte_message.set('Modifications non validées')