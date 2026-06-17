import json#->importer json pour sauvegarder les données du wallet
import os#->importer os pour vérifier si le fichier existe et créer le dossier data si nécessaire

WALLET_FILE = 'data/wallets.json'#-> variable qui donne ou on sauvgarde le fichier json qui contient les données du wallet
STARTING_BALANCE = 10000#-> Variable qui definit le solde de départ pour chaque joueur

def load_wallets():#->fonction permettant de reprendre la ou on en etait en chargant les donnee du wallet depuis le fichier json ou d en creer un nouveau
    if not os.path.exists(WALLET_FILE):#->si aucun ficher n existe alors
        return {}#->on en cree un nouveau avec un dictionnaire vide
    with open(WALLET_FILE, 'r') as f:#->on ouvre le wallet en mode lecture
        return json.load(f)#->on charge les données du wallet depuis le fichier json et on les retourne sous forme de dictionnaire

def save_wallets(wallets):#->fonction qui permet de sauvegarder ses données
    os.makedirs('data', exist_ok=True)#->on cree le dossier si il n existe pas deja grace a exist_ok=True
    with open(WALLET_FILE, 'w') as f:#->ou on ouvre le wallet en mode ecriture pour modifer les anciennes donnes et mettre les nouvelles
        json.dump(wallets, f, indent=2)#->on met toutes les données dans le fichier json

def get_balance(username):#->Permet d avoir la solde du joueur
    wallets = load_wallets()#->reprend la ou le joueur en etait en chargeant les donnees ou creer un nouveau en appelant l fonction idoine
    if username not in wallets:#->si le joueur n est pas dans le wallet alors
        wallets[username] = STARTING_BALANCE#->on prend son nom et on lui met la solde de depart
        save_wallets(wallets)#->on enregistre
    return wallets[username]#->on renvoi les donnees associe a son nom dans wallet

def update_balance(username, amount):#->sert a changer la solde du joueur en cas de gains ou de pertes
    """amount can be positive (win) or negative (loss)"""
    wallets = load_wallets()#->reprend la ou le joueur en etait en chargeant les donnees ou creer un nouveau
    if username not in wallets:#->si le joueur n est pas dans le wallet alors
        wallets[username] = STARTING_BALANCE#->on prend son nom et on lui met la solde de depart
    wallets[username] += amount#->on ajoute la somme de l utilisateur a son wallet
    if wallets[username] < 0:#->si elle est plus petite que 0
        wallets[username] = 0#->alors elle est egale a 0, impossibilité métier d'avoir des montants negatifs
    save_wallets(wallets)#->on enregistre
    return wallets[username]#->on renvoi les donnees associe a son nom dans wallet


def get_all_balances():#->pour avoir la solde de tout les joueurs
    return load_wallets()#->renvoie les sauvgardes du wallet


def reset_wallet(username):#->permet de reinitialiser le wallet
    wallets = load_wallets()#->on charge le wallet 
    wallets[username] = STARTING_BALANCE#->on le remet a la solde de base
    save_wallets(wallets)#->on sauvegarde ensuite le wallet

