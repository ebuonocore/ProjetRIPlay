import RIP_lay_outils as ro


class Réseau:
    COULEURS = ['#9FA8DA', '#90CAF9', '#81D4FA', '#80DEEA', '#80CBC4',
                '#A5D6A7', '#C5E1A5', '#E6EE9C', '#FFAB91', '#EF9A9A',
                '#F48FB1', '#CE93D8', '#D1C4E9', '#BCAAA4', '#EEEEEE',
                '#B0BEC5']

    def __init__(self):
        self.noeuds = []  # Agrégateurs de noeuds
        self.animation = False
        # Liaison (couple de noeuds) susceptible d'être supprimée
        self.liaison_cible = (None, None)
        # Valeur par défaut de la distance considérée comme non atteignable
        self.infini = 16
        self.ttl_route = 6  # Durée de vie par défaut d'une route perdue
        # Pas de passerelle par défaut si False, sinon, on choisit le premier
        # noeud voisin
        self.passerelle_par_défaut = False
        self.maj_rapide = True
        self.paquet = Paquet()

    def ensemble_labels_noeuds(self):
        """ Renvoie l'ensemble des labels des noeuds
        """
        noms = set()
        for noeud in self.noeuds:
            noms.add(noeud.label)
        return noms

    def créer_noeud(self, label=None):
        """ Ajoute le noeud au réseau
        """
        listes_noms_noeuds = [noeud.label for noeud in self.noeuds]
        if label is None or label in listes_noms_noeuds:
            label = ro.nom_noeud_suivant(listes_noms_noeuds)
        nouveau_noeud = Noeud(label, self.infini, self.maj_rapide)
        nouveau_noeud.couleur =\
            Réseau.COULEURS[len(self.noeuds) % len(Réseau.COULEURS)]
        self.ajouter_noeud(nouveau_noeud)
        return nouveau_noeud

    def ajouter_noeud(self, noeud):
        """ Ajoute le noeud au réseau
        """
        self.noeuds.append(noeud)

    def supprimer(self, noeud_à_supprimer):
        """ Supprime le noeud du réseau s'il existe
        """
        indice = self.indice_dans_réseau(noeud_à_supprimer)
        if indice is not None:
            del self.noeuds[indice]
            # Supprime ce noeud de tous ces anciens voisins
            for noeud_voisin in noeud_à_supprimer.voisins:
                noeud_voisin.supprimer_voisin(noeud_à_supprimer)
                if self.maj_rapide:
                    noeud_voisin.table[noeud_à_supprimer] =\
                        [self.infini, noeud_voisin, 0]
                    noeud_voisin.lignes_modifiées.append(noeud_à_supprimer)
            noeud_à_supprimer.voisins = []

    def indice_dans_réseau(self, noeud):
        if noeud in self.noeuds:
            return self.noeuds.index(noeud)
        else:
            return None

    def supprimer_liaison(self, noeud_A, noeud_B):
        """ Supprime l'arête commune entre les noeuds A et B
        """
        noeud_A.supprimer_voisin(noeud_B)
        noeud_B.supprimer_voisin(noeud_A)

    def mettre_à_jour_tables(self):
        """ Met à jour la table de routage de chaque noeud à partir des tables des noeuds voisins.
            Pour chaque noeud, on construit la fusion des tables voisines (tables_fusion):
                Sauvegarde de l'ancienne table pour conserver l'information sur le TTL.
                Une métrique ne est incrémentée de noeud en noeud.
                Elle sature à self.infini.
            Reconstruction de la table de routage:
            On supprime les lignes où métrique > self.infini(TTL atteint)
            Pour chaque destination, cherche la ligne où la métrique est la plus petite
            destination -> source : métrique
        """
        for noeud in self.noeuds:
            tables_fusion = []
            noeud.ancienne_table = noeud.table.copy()
            for destination, (distance, passerelle, ttl) in noeud.table.items():
                # Réinitialise toutes les routes existantes à une distance 'Infinie'
                # sauf la route qui pointe sur le noeud lui-même (distance à 0)
                if destination == noeud:
                    tables_fusion.append([noeud, destination, passerelle, 0])
                else:
                    tables_fusion.append([noeud, destination, passerelle,
                                          self.infini])
            # Alimente tables_fusion à partir des routes des noeuds voisins en
            # incrémentant la distance la distance de 1, à condition que cette
            # route ne mentionne pas comme passerelle le noeud courant, un autre
            # voisin direct et que la distance reste inférieure à 'Infini'
            for voisin in noeud.voisins:
                # Construction de la liste des autres voisins directs
                autres_voisins = noeud.voisins.copy()
                autres_voisins.remove(voisin)
                for destination, (distance, passerelle, ttl) in\
                        voisin.table.items():
                    distance = min(distance + 1, self.infini)
                    if passerelle not in autres_voisins and passerelle != noeud:
                        if distance < self.infini:
                            tables_fusion.append([voisin, destination,
                                                  passerelle, distance])
            # Reconstruction de la table de routage à partir de tables_fusion :
            # [noeud_source, destination, via, métrique]
            # noeud_source est la potentielle passerelle vue par le noeud courant
            # via est la passerelle de la passerelle (noeud_source)
            noeud.table_tempo = {}
            while len(tables_fusion) > 0:
                source = tables_fusion[0][0]
                destination = tables_fusion[0][1]
                métrique = tables_fusion[0][3]
                # Si l'ancienne route allant vers cette destination est toujours
                # dans la table_fusion avec la même métrique, alors on la privilégie.
                for i in range(len(tables_fusion)):
                    # Recherche les autres routes menant à destination
                    if tables_fusion[i][1] == destination:
                        # Si l'ancienne route menant à destination est toujours présente,
                        # on la choisit comme réference de la recherche
                        if destination in noeud.ancienne_table.keys():
                            ancienne_passerelle = noeud.ancienne_table[destination][1]
                            ancienne_métrique = noeud.ancienne_table[destination][0]
                            if tables_fusion[i][3] == métrique == ancienne_métrique and\
                                    ancienne_passerelle == tables_fusion[i][0]:
                                métrique = tables_fusion[i][3]
                                source = tables_fusion[i][0]
                        if tables_fusion[i][3] < métrique:
                            métrique = tables_fusion[i][3]
                            source = tables_fusion[i][0]

                ttl = 0
                if destination in noeud.ancienne_table.keys():
                    ttl = noeud.ancienne_table[destination][2]
                if métrique >= self.infini:
                    ttl += 1
                if ttl < self.ttl_route:
                    noeud.table_tempo[destination] = (métrique, source, ttl)
                tables_fusion = ro.nettoyer(tables_fusion, destination)
        # Validation des tables temporaires
        for noeud in self.noeuds:
            noeud.table = noeud.table_tempo.copy()
            # Initialisation de noeud.lignes_modifiées: Liste vide sauf si la table a changé.
            if noeud.représentation_table(noeud.ancienne_table) ==\
                    noeud.représentation_table(noeud.table_tempo):
                noeud.lignes_modifiées = []
            else:
                noeud.lignes_modifiées = [noeud]
            # Vérification des lignes de la table modifiées
            for destination, (distance, passerelle, ttl) in noeud.table.items():
                if destination not in noeud.ancienne_table.keys():
                    noeud.lignes_modifiées.append(destination)  # Nouvelle ligne
                else:
                    if distance != noeud.ancienne_table[destination][0] or\
                            passerelle != noeud.ancienne_table[destination][1]:
                        # Ancienne ligne modifiée
                        noeud.lignes_modifiées.append(destination)

    def mettre_à_jour_tailles_noeuds(self, base_largeur, base_hauteur):
        """ Modifie l'attirbut taille de chaque noeud en fonction du nombre d'élément
            dans la table de routage.
        """
        for noeud in self.noeuds:
            noeud.taille[0] = base_largeur
            noeud.taille[1] = 20 + base_hauteur * len(noeud.table)

    def __repr__(self):
        réseau_str = ""
        for noeud in self.noeuds:
            réseau_str += repr(noeud)
        return réseau_str + '\n'


class Noeud:
    def __init__(self, label, infini, maj_rapide, voisins=None, position=None,
                 couleur=None):
        self.label = label  # Désignation du noeud (a priori une seule lettre)
        self.infini = infini
        self.maj_rapide = maj_rapide
        # Liste des noeuds voisins initialisée à une liste vide
        self.voisins = []
        if voisins is not None:
            # L'ajout d'un voisin est réciproque: Le Graphe est non-orienté
            for voisin in voisins:
                self.voisins.append(voisin)
                voisin.ajouter_voisin(self)
        self.couleur = couleur
        if couleur is None:
            self.couleur = '#A0EEA0'
        self.position = position  # Coordonnées (x,y) du noeud
        if position is None:
            # Position par défaut en dehors du canevas
            self.position = (-100, -100)
        # Table de routage actuelle. { destination : [distance, passerelle] }
        self.taille = [40, 40]  # Dimensions par défaut d'un noeud
        # Dictionnaire des destinations:[métrique, passerelle, ttl]
        self.table = {self: [0, self, 0]}
        # Construction temporaire de la table de routage avant validation
        self.table_tempo = {}
        # Mémorisation de la table de routage du tour précédent
        self.ancienne_table = {}
        # Liste des destinations modifiées dans la table
        self.lignes_modifiées = []

    def changer_position(self, position):
        self.position = position

    def indice_voisins(self, noeud):
        """ Renvoie l'indice du noeud dans la liste des voisins s'il existe.
            Renvoie None si le noeud n'existe pas dans la liste.
        """
        if noeud in self.voisins:
            return self.voisins.index(noeud)
        else:
            return None

    def ajouter_voisin(self, voisin):
        """ Ajoute noeud à la liste des voisins s'il n'existe pas déjà.
            Renvoie True si l'ajout est effectif. Sinon, renvoie False.
        """
        if self.indice_voisins(voisin) is None:
            self.voisins.append(voisin)
            return True
        return False

    def supprimer_voisin(self, noeud_cible):
        """ Supprime noeud_cible de la liste des voisins.
        Renvoie True si l'opération est effective.
        Sinon, renvoie False.
        """
        indice = self.indice_voisins(noeud_cible)
        if indice is not None:
            del self.voisins[indice]
            if self.maj_rapide:
                for destination in self.table.keys():
                    if self.table[destination][1] == noeud_cible:
                        self.table[destination] = [self.infini, self,
                                                   self.table[destination][2]]
                        self.lignes_modifiées.append(destination)
            return True  # La supression s'est bien déroulée
        return False  # La supression n'a pas pu se faire

    def idx(self):
        """ Renvoie l'id de l'objet noeud transtypé en str
            Pour la sauvegarde au format JSON, le label du neoud n'est pas une
            clef unique pour les identifier.
            On utilise l'id de l'objet. Mais les clefs des dictionnaires sont
            transtyper en str.
            idx() permet detranstyperpar défaut les id dans les valeurs.
        """
        return str(id(self))

    def représentation_table(self, table):
        """ Représentation en chaîne de caractères d'une table de routage.
        """
        table_str = ""
        for destination, (distance, passerelle, ttl) in table.items():
            table_str += '  + ' + str(destination.label)
            table_str += ' ->' + str(passerelle.label)
            table_str += ':' + str(distance) + '\n'
        return table_str

    def __repr__(self):
        noeud_str = '*** ' + str(self.label) + ' ***\n'
        noeud_str += self.représentation_table(self.table)
        noeud_str += 'voisins: ['
        for i in range(len(self.voisins)):
            noeud_str += str(self.voisins[i].label)
            if i < len(self.voisins) - 1:
                noeud_str += ', '
        noeud_str += ']\n'
        return noeud_str


class Paquet():
    def __init__(self, passerelle_par_défaut=False, source=None, destination=None):
        self.source = source
        self.passerelle_par_défaut = passerelle_par_défaut
        self.destination = destination
        # Succession des noeuds de la route
        self.route_noeuds = [source]
        # Succession des liaisons de la route
        self.route_liaisons = []
        # Nombre de tours avant de déclarer un paquet perdu
        self.ttl_paquet = 15

    def route_valide(self):
        """ Renvoie True si la route atteint la destination.
            Sinon False
        """
        return self.route_noeuds[-1] is self.destination

    def résoudre_route(self):
        """ Construit la route depuis la source vers la destination
            Construit self.route_noeuds et self.route_liaisons
        """
        # Initialisation des attributs et du nombre de tours maximum avant de
        # jeter l'éponge
        if self.source is not None:
            self.route_noeuds = [self.source]
            self.route_liaisons = []
            ttl = 0
            noeud_courant = self.source
            while ttl < self.ttl_paquet and not self.route_valide():
                noeud_suivant = None
                if self.destination in noeud_courant.table.keys():
                    noeud_probable = noeud_courant.table[self.destination][1]
                    if noeud_probable in noeud_courant.voisins:
                        noeud_suivant = noeud_probable
                elif self.passerelle_par_défaut and len(noeud_courant.voisins) > 0:
                    noeud_suivant = noeud_courant.voisins[0]
                if noeud_suivant is not None:
                    self.route_noeuds.append(noeud_suivant)
                    self.route_liaisons.append((noeud_courant, noeud_suivant))
                    ttl += 1
                    noeud_courant = noeud_suivant
                else:
                    ttl = self.ttl_paquet
                    return False
            return self.route_valide()


class Refaire:
    def __init__(self, taille):
        """ self.mémoire : agrégateur des états passés du réseau
            self.index : indice du dernier élément ajouté dans self.mémoire
            self.base : indice du premier élément dans l'agrégateur
            self.limite_max : taille maximale de l'agrégateur
        """
        self.index = 0
        self.base = 0
        self.taille = taille
        self.mémoire = [None] * self.taille

    def ajouter(self, état_courant):
        """ Ajoute état_courant à l'indice suivant de l'agrégateur modulo
            self.limite_max s'il est différent de létat précédent
        """
        if état_courant != self.mémoire[self.index]:
            self.index = (self.index + 1) % self.taille
            if self.base == self.index:
                self.base = (self.base + 1) % self.taille
            self.mémoire[self.index] = état_courant

    def retirer(self):
        """ Renvoie, s'il existe, le dernier élément ajouté. Décrémente self.index
            Sinon, renvoie False
        """
        if self.est_vide():
            return None
        else:
            état_retourné = self.mémoire[self.index]
            if self.index != self.base:
                self.mémoire[self.index] = None
                self.index = (self.index - 1) % self.taille
            return état_retourné

    def dimension(self):
        """ Renvoie le nombre d'éléments enregistrés
        """
        if self.est_vide():
            return 0
        elif self.index > self.base:
            return self.index - self.base
        else:
            return self.taille - self.base + self.index + 1

    def est_vide(self):
        """ Renvoie True si la liste ne contient rien. Sinon False
        """
        return self.index == self.base

    def __str__(self):
        chaîne = str(self.base) + '>' + str(self.index) + ':'
        i = self.base
        while i != self.index:
            chaîne += str(self.mémoire[i])
            i = (i + 1) % self.taille
            if i == 0:
                chaîne += '|'
        return chaîne