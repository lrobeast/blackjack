import random #-> imorter la fonction aleatoire pour mélanger le deck

# DEFINITIONS DES LISTES POUR LES SIGNE ET NUMERO DES CARTES
SUITS = ['♠', '♥', '♦', '♣']#->liste pour definir les signes des cartes
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']#->Liste pour definir les numero des cartes

def create_deck():#->La fonction permet de creer le dec tout melangé
    deck = [{'suit': s, 'rank': r} for s in SUITS for r in RANKS]#->on cree un dictionaire pour assicier suit a s et rank a r puis avec for in range qui associe les rang et signes entre eux
    random.shuffle(deck)
    return deck#-> Return permet de faire sortis le resultat de la fonction

def card_value(card):#->Donne la valeur des cartes
    if card['rank'] in ['J', 'Q', 'K']:#-> if correspond a si et si leur rang est JQK alors
        return 10#-> les cartes J Q K valent 10
    elif card['rank'] == 'A':#->elif met une autre condition, si le rang est A alors
        return 11#-> l'as vaut 11
    else:#-> else correspond a sinon, si les conditions precedentes ne sont pas remplies alors
        return int(card['rank'])#-> int permet de convertir le rang de la carte (string) en nombre integer pour pouvoir faire la somme de la main a la fin et 

def hand_value(hand):#-> on cree une fonction pour calculer la valeur de la main
    value = sum(card_value(c) for c in hand)#->sum permet de faire la somme des arguments renvoyes par card_value pour chaque carte c dans la main
    aces = sum(1 for c in hand if c['rank'] == 'A')#-> on compte le nombre d'as dans la main en faisant la somme grace a sum de 1 pour c dans la main si le rang de c est A
    while value > 21 and aces:#-> tant que la valeur de la main est superieur a 21 et qu il y a des as dans la main on fait -10 au niveau de la valeur et on retire 1 as 
        value -= 10
        aces -= 1
    return value

def card_str(card):#-> on cree une fonction pour afficher le numero et le symbole de la carte choisie str correspond a string qui permet d afficher le resultat de la fonction
    return f"{card['rank']}{card['suit']}"#-> on fait 2 appels au dictionnaire card avec les key "rank" et "suit" pour afficher le rang et le symbole de la carte (value)

def hand_str(hand):
    return ' '.join(card_str(c) for c in hand)#-> on affiche la main avec join permettant l affichage d une seule chaine de caractere (concaténation)

def is_blackjack(hand):#-> on cree une fonction pour verifier si la main est un blackjack
    return len(hand) == 2 and hand_value(hand) == 21#->on verifie que le nombre de carte dans la main est strictement egal a 2 cartes grace a la fonction len qui permet de calculer la longuer de la liste et au test avec == et que la valeur de la main est egale a 21

def dealer_play(hand, deck):#-> on cree une fonction pour le jeu du croupier qui tire des cartes jusqu a ce que la valeur de sa main soit superieur ou egale a 17 (regle métier liée au blackjack)
    """Dealer draws until 17+"""
    while hand_value(hand) < 17:#-> while permet de dire tant qu'une codition est remplie une boucle est jouée en infini. Et ici la condition est tant que la valeur de la main est inferieure a 17
        hand.append(deck.pop())#->tant que la condition n est pas remplie on ajoute une carte a la main du croupier avec append et on retire la carte du deck avec pop (retire le dernier élément d'une liste)
    return hand


def forced_blackjack_hand():
    """For /superjyssmode — returns a guaranteed blackjack hand"""
    ace = {'suit': random.choice(SUITS), 'rank': 'A'}
    ten = {'suit': random.choice(SUITS), 'rank': random.choice(['10', 'J', 'Q', 'K'])}
    return [ace, ten]
#-> on definie une fonction qui permet d avoir un blackjack garanti tout en choisissant aleatoirement toutes les possibilite pour faire un blackjack
# TODO :  penser à verifier que e=les cartes prises n'apparaissent pas chez les autres joueurs