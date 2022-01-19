from math import sqrt
import tkinter as tk
from tkinter import ttk

def distance_point_droite(xp, yp, xm, ym, xn, yn):
    """ Soit un point P(xp, yp) et une droite D passant par M(xm, ym) et N(xn, yn)
        Renvoie la distance entre le point P et la droite D
    """
    if xm != xn:
        # D d'équation y = a*x + b
        a = (ym - yn) / (xm - xn)
        if a != 0:
            b = ym - (a * xm)
            # D' perpendiculaire à D passant par P, d'équation y = -a*x + c
            c = yp + (xp / a)
            # K intersection de D et D'
            xk = a * (c - b) / (a**2 + 1)
            yk = a * xk + b
            distance_PK = sqrt((xp - xk)**2 + (yp - yk)**2)
        else:
            distance_PK = abs(yp - ym)
    else:
        distance_PK = abs(xp - xm)
    return distance_PK

def plus_sombre(couleur):
    """ couleur est au format hexadécimal
        Renvoie la couleur 2 fois plus sombre
    """
    R = int(couleur[1:3], 16)*3//4
    Rx = ('00' + str(hex(R))[2:4])[-2:]
    V = int(couleur[3:5], 16)*3//4
    Vx = ('00' + str(hex(V))[2:4])[-2:]
    B = int(couleur[5:8], 16)*3//4
    Bx = ('00' + str(hex(B))[2:4])[-2:]
    return '#' + Rx + Vx + Bx

def plus_clair(couleur):
    """ couleur est au format hexadécimal
        Renvoie la couleur 2 fois plus sombre
    """
    R = (127 + int(couleur[1:3], 16)//2)
    Rx = ('00' + str(hex(R))[2:4])[-2:]
    V = (127 + int(couleur[3:5], 16)//2)
    Vx = ('00' + str(hex(V))[2:4])[-2:]
    B = (127 + int(couleur[5:8], 16)//2)
    Bx = ('00' + str(hex(B))[2:4])[-2:]
    return '#' + Rx + Vx + Bx

def afficher_tables(source, tables_fusion):
    """ [noeud_source, destination, via, métrique]
    """
    print('**** tables_fusion de:', source.label)
    for i in range(len(tables_fusion)):
        print('[', tables_fusion[i][0].label, tables_fusion[i][1].label, tables_fusion[i][2].label, tables_fusion[i][3], ']')

def nettoyer(table, destination):
    """ Renvoie la liste table, nettoyées de toutes les
        lignes où table[i][1] == destination
    """
    table_tempo = []
    for i in range(len(table)):
        if table[i][1] != destination:
            table_tempo.append(table[i])
    return table_tempo

def nom_noeud_suivant(listes_noms_noeuds):
    """ Renvoie le nom du noeud suivant par rapport aux symbôles autorisés.
    """
    # Liste des symbôles autorisées pour les noms de noeuds
    SYMBOLES = ['_'] + [chr(i) for i in range(ord('0'), ord('0')+10)] + \
               [chr(i) for i in range(ord('A'), ord('A')+26)]
    valeurs_noms = [10]  # Valeur minimale correspondant à 'A'
    for nom in listes_noms_noeuds:
        valeur_nom = 0
        for i in range(len(nom)):
            if nom[i] in SYMBOLES:
                indice_caractère = SYMBOLES.index(nom[i])
            else:
                indice_caractère = 0
            valeur_nom += indice_caractère * len(SYMBOLES) ** (len(nom) -i - 1)
        valeurs_noms.append(valeur_nom)
    valeur_nom_suivant = sorted(valeurs_noms)[-1] + 1
    nom_suivant = ''
    while valeur_nom_suivant >= len(SYMBOLES):
        nom_suivant = SYMBOLES[valeur_nom_suivant % len(SYMBOLES)] + nom_suivant
        valeur_nom_suivant = valeur_nom_suivant // len(SYMBOLES)
    return SYMBOLES[valeur_nom_suivant] + nom_suivant

def est_sur_la_route(noeud, table_destination, table_passerelle, paquet):
    """ Renvoie True si on identifie une ligne de la table de routage de noeud
        correspondant au chemin défini par la liste de segments liaisons
    """
    if noeud in paquet.route_noeuds and table_destination == paquet.destination:
        if (noeud, table_passerelle) in paquet.route_liaisons:
            return True
    return False

def est_un_segment(noeud, voisin, paquet):
    """ Renvoie True si on identifie un segment
        du chemin défini par la liste de segments liaisons
    """
    if (noeud, voisin) in paquet.route_liaisons or (voisin, noeud) in paquet.route_liaisons:
        return True
    return False

class ScrollableFrame(ttk.Frame):
    """ source: https://blog.teclado.com/tkinter-scrollable-frames/
    """
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

if __name__ == '__main__':
    print(nom_noeud_suivant([]))
    print(nom_noeud_suivant(['31', 'B1']))
    print(nom_noeud_suivant(['51', 'A_0', 'B9']))