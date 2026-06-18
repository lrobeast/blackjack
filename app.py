from flask import Flask, render_template, request, jsonify, session, redirect, url_for#-> importer depuis le module flask les classes et fonctions flask(pour mettre a jour sur une page), render_template, request, jsonify, session, redirect et url_for
import time#-> importer le module time pour gérer le temps et les délais
import threading#-> importer le mosule threading pour gerer la syncronisation des routes
from game import create_deck, hand_value, dealer_play, is_blackjack, hand_str, card_str, forced_blackjack_hand#-> importer depuis le module game les classes et fonctions create_deck, hand_value, dealer_play, is_blackjack, hand_str, card_str et forced_blackjack_hand
from wallet import get_balance, update_balance, get_all_balances, reset_wallet#-> importer depuis wallet les fonctions get_balance, update_balance, get_all_balances et reset_wallet

app = Flask(__name__)#-> créer une instance de l'application Flask
app.secret_key = 'jyss-secret-blackjack-2024'#-> definir la clee secrete de connexion pour l application flask

MASTER_LOGIN   = 'jyssmode'#-> definir le login du maitre du jeu
MASTER_NAME    = 'Lucas The Master Of The Universe'#-> definir le nom du maitre du jeu
TIMER_SECONDS  = 15#-> definir le temps limite pour miser ou jouer
JOIN_SECONDS   = 15#-> definir le temps limite pour rejoindre la partie

table = {#-> definir la table grace a un dictionnaire contenant les informations de la partie
    'deck': [],#-> deck
    'dealer_hand': [],#-> le jeu du croupier
    'players': {},#-> les joueurs
    'phase': 'waiting',   # waiting | joining | betting | playing | dealer | results#-> les phases du jeu et statut des players et de la partie
    'jyss_mode': False,#-> 
    'jyss_logs': [],#->
    'round_number': 0,#-> compter le nombre de round
    'join_deadline': None,#->join_deadline pour la phase de fin de joining et none pour la phase de waiting
}
table_lock = threading.Lock()#-> on cree un verrou pour sauvgarder l etat de la table et sycroniser avec tout les joueurs

# ─── Helpers ─────────────────────────────────────────────────────────────────

def jyss_log(msg):#-> fonction pour ajouter un message dans le journal de la partie
    table['jyss_logs'].append({'time': time.time(), 'msg': msg})#-> on cree l annonce tout en prenant le temps actuel et le message

def get_player(username):#-> pour recuperer les informations d un joueur grace a son username   
    if username not in table['players']:#-> si le joueur n est pas dans la table 
        status = 'idle' if table['phase'] in ('waiting', 'joining') else 'spectator'#-> si la phase est waiting ou joining le statu du joueur est idle(inactif) sinon le statut est spectator(spectateur)
        table['players'][username] = {#-> on cree un dictionnaire pour le joueur avec les informations suivantes
            'hand': [], 'bet': 0, 'status': status, 'timer_start': None,#-> On rentre la main du joueur sa mise son statu et le temps de debut du timer
        }
    return table['players'][username]#-> puis on renvoi toutes les informations du joueur

def compute_results():#-> fonction pour calculer les resultats de la partie
    dealer_val = hand_value(table['dealer_hand'])#-> on cree une variable dealer_val pour stocker la valeur de la main du croupier grace a la fonction hand_value
    dealer_bj  = is_blackjack(table['dealer_hand'])#-> on cree une variable dealer_bj pour stocker si le croupier a un blackjack grace a la fonction is_blackjack
    results = {}#-> on cree un dictionnaire pour stocker le resultat du croupier
    for username, p in table['players'].items():
        if p['status'] == 'spectator' or p['bet'] == 0:#-> si le statu du jouer est spectateur ou que sa mise est egale a 0
            continue#-> on continue la boucle pour passer au joueur suivant
        if p['status'] == 'bust':#-> si le statut du joueur est bust
            result, delta = 'bust', -p['bet']#-> on cree une variable result pour stocker le resultat du joueur et une variable delta pour stocker la difference de sa mise
        elif p['status'] == 'blackjack':#-> si le joueur a fait un blackjack
            result, delta = ('push', 0) if dealer_bj else ('blackjack', int(p['bet'] * 1.5))#-> si le croupier a lui aussi blackjack le resultat est push et on ne perd ou gagne rien sinin on gagne 2,5 fois sa mise
        elif dealer_bj:#-> si le croupier a fait un blackjack
            result, delta = 'lose', -p['bet']#-> le joueur perd lose et on fait moins la mise
        elif dealer_val > 21:#-> si le croupier a depassé 21
            result, delta = 'win', p['bet']#-> le joueur gagne win et on fait plus la mise
        elif hand_value(p['hand']) > dealer_val:#-> si la valeur de la main du joueur est superieur a celle du croupier
            result, delta = 'win', p['bet']#-> le joueur gagne win et on fait plus la mise
        elif hand_value(p['hand']) == dealer_val:#-> si la valeur de la main du joueur est egale a celle du croupier
            result, delta = 'push', 0#-> le joueur fait push et on ne perd ou gagne rien
        else:
            result, delta = 'lose', -p['bet']#-> sinon le joueur perd lose et on fait moins la mise
        update_balance(username, delta)#-> on met a jour le solde du joueur grace a la fonction update_balance
        results[username] = {#-> on cree un dictionnaire pour stocker et afficher le resultat du joueur avec les informations suivantes
            'result': result, 'delta': delta,#-> le dictionnaire contient le resultat du joueur et ses gains ou pertes
            'hand': hand_str(p['hand']), 'value': hand_value(p['hand']),#-> sa main et sa valeur
            'balance': get_balance(username),#-> et enfin sa solde grace a la fonction get_balance
        }
    return results#-> on renvoi le dictionnaire contenant les resultats de tous les joueurs

def _try_advance_to_playing():#->fonction pour changer de phase de de betting a playing si tous les joueurs ont misé
    still_betting = [p for p in table['players'].values() if p['status'] == 'betting']#-> on cree une variable qui stocke dans une liste les joueurs qui son toujours en train de parier
    if still_betting:#-> si la liste n est pas vide
        return#-> on sort de la fonction
    table['phase'] = 'playing'#-> sinon on change la phase de la table a playing
    now = time.time()#-> on attribue a now le temps actuel grace a la fonction time.time() qui renvoie le temps actuel en secondes
    for p in table['players'].values():#->pour tout les player qui sont sur la table avec une vlaure
        if p['status'] == 'playing':#->si le statut des joueurs est playing  alors
            p['timer_start'] = now#->le timer commence a l heure enregistrée par time.timte()
    _check_playing_done()#->permet de verifier si la phase de jeux est bien finie

def _check_playing_done():#->permet de verifier si la phase de jeux est bien finie
    if table['phase'] not in ('playing', 'betting'):#-> si la phase de la table n est pas sur playing ou betting
        return#->alors sortir de la fonction
    active = [p for p in table['players'].values() if p['status'] == 'playing']#->on cree une variable qui stocke dans une liste  les joueurs qui sont toujours en train de jouer
    if active:#-> si il le sont alors 
        return#->sortir de la fonction
    table['phase'] = 'dealer'#->sinon passer a la phase du dealer
    if table['dealer_hand']:#->si c est au tour du dealer alors
        table['dealer_hand'] = dealer_play(table['dealer_hand'], table['deck'])#-> faire jouer le dealer
    results = compute_results()#->utiliser la fonction compute resulte pour stocker les resultas
    table['phase'] = 'results'#->puis passer a la phase des resultats
    table['last_results'] = results#->et la phasse donne alors les resutats

def _start_betting_phase():#->fonction pour commencer la phase de la mise
    table['deck']          = create_deck()#->on met le deck que l ont cree avec la fonction create deck dans la table
    table['dealer_hand']   = []#->on reset la main du croupier en lui creant un nouvelle vide qui vas acceuillir ses prochaines cartes
    table['round_number'] += 1#->on signal le round suivant en ajoutant 1 au round
    table['phase']         = 'betting'#->on commence la phase de betting (mise)
    table['jyss_mode']     = False#->et on verifie le jyss_mode
    now = time.time()#->on prend le temps
    for p in table['players'].values():#->pour tous les players(joueurs) sur la table les values sont
        if p['status'] == 'idle':#->si le statut est inactif
            p['hand'], p['bet'], p['status'], p['timer_start'] = [], 0, 'betting', now#->on verifie la main la mise  le statu on met le timer et la mise a 0 et on enregistre le temps

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')#->app route est la pour creer une route un chemin local
def index():#->on defini l index de la session
    if 'username' not in session:#->si il n est pas dans la session alors
        return redirect(url_for('login'))#->on sort de la fonction pour rediriger vers la page de login
    return render_template('game.html', username=session['username'])#->on vas diriger l utilisateur vers la page de jeu avec sa session qui a ete rempli precedemant par lui

@app.route('/login', methods=['GET', 'POST'])#->on dirige vers le loging avec app route avec une metode de get post c est a dire que l on demande des données et on en donne pour qu elle soivent traite                                                                         
def login():#->permet de se connecter au jeu
    if request.method == 'POST':#->si la requete est un traitement de donne
        raw = request.form.get('username', '').strip()#->raw est la variable definie sous la forme d une demande de l username en str
        if not raw:#->si le pseudo ne correspond pas alors 
            return render_template('login.html', error='Pseudo invalide')#on renvoi pseudo invalide
        # Pseudo maître
        if raw.lower() == MASTER_LOGIN:#->si c est egal a master_login en minuscule
            session['username']  = MASTER_NAME#->alors la session passe sur Master name
            session['jyss_auth'] = True#->donc la session passe sur jyss_auth
            get_balance(MASTER_NAME)#->on reprend a la solde de master name
            return redirect(url_for('index'))#->on sort de la fonction pour rediriger vers l index
        if len(raw) > 20:#->si la longueur de la liste fait plus de 20 caractères(le pseudo)
            return render_template('login.html', error='Pseudo trop long (max 20)')#->on renvoi erreur pseudo trop long (max 20)
        session['username'] = raw#->si le pseudo est dans les username
        session.pop('jyss_auth', None)#->alors on enleve jyss_auth
        get_balance(raw)#->puis on utilise la fonction get_balance pour obtenir la solde du joueur
        return redirect(url_for('index'))#->puis on le met dans l index
    return render_template('login.html', error=None)#->sinon in met erreur il n y a rien

@app.route('/logout')#->cette route permet de se deconnecter
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── API state ────────────────────────────────────────────────────────────────

@app.route('/api/state')#->cette route permet de definir les statuts des joueurs et du jeu(@app.route est un decorateur il permet de remplacer une fonction il affiche envoie)
def api_state():
    if 'username' not in session:#->si il n est pas connecte
        return jsonify({'error': 'not logged in'}), 401
    username   = session['username']
    is_master  = bool(session.get('jyss_auth'))
    with table_lock:
        player = table['players'].get(username, {})
        timer_left      = None
        join_timer_left = None

        if table['phase'] == 'joining' and table['join_deadline']:
            join_timer_left = max(0, int(table['join_deadline'] - time.time()))
            if join_timer_left == 0:
                _start_betting_phase()

        if player.get('timer_start') and table['phase'] in ('betting', 'playing'):
            elapsed    = time.time() - player['timer_start']
            timer_left = max(0, TIMER_SECONDS - int(elapsed))
            if timer_left == 0 and player['status'] in ('betting', 'playing'):
                if player['status'] == 'betting':
                    player['status']      = 'spectator'
                    player['timer_start'] = None
                    _try_advance_to_playing()
                elif player['status'] == 'playing':
                    player['status'] = 'stand'
                    _check_playing_done()

        show_dealer_full = table['phase'] in ('dealer', 'results')
        # Master voit toujours la main complète du croupier
        dealer_display = table['dealer_hand'] if (show_dealer_full or is_master) else table['dealer_hand'][:1]

        state = {
            'phase':           table['phase'],
            'round':           table['round_number'],
            'join_timer_left': join_timer_left,
            'dealer_hand':     [card_str(c) for c in dealer_display],
            'dealer_value':    hand_value(dealer_display) if (show_dealer_full or is_master) else '?',
            'my_hand':         [card_str(c) for c in player.get('hand', [])],
            'my_value':        hand_value(player.get('hand', [])),
            'my_status':       player.get('status', 'idle'),
            'my_bet':          player.get('bet', 0),
            'my_balance':      get_balance(username),
            'timer_left':      timer_left,
            'is_master':       is_master,
            'jyss_mode':       table['jyss_mode'] if is_master else None,
            'players': {
                u: {
                    'status':    p['status'],
                    'bet':       p['bet'],
                    'hand_size': len(p['hand']),
                    'value':     hand_value(p['hand']) if (show_dealer_full or is_master) else '?',
                    'hand':      [card_str(c) for c in p['hand']] if (show_dealer_full or is_master) else [],
                }
                for u, p in table['players'].items()
            },
        }

        # Cartes "next" pour le master (prochaine carte visible du deck)
        if is_master and table['deck']:
            state['next_card']        = card_str(table['deck'][-1])   # prochaine piochée
            state['dealer_next_card'] = card_str(table['deck'][-1])   # même carte (croupier piocharait la même)

        import hashlib, json as _json#->hashlib permet de cripter et d enregistrer les mots de passes
        state['state_hash'] = hashlib.md5(
            _json.dumps({k: v for k, v in state.items()
                         if k not in ('timer_left', 'join_timer_left')},
                        sort_keys=True).encode()
        ).hexdigest()[:8]#->hexdigest c est pour transformer en string
    return jsonify(state)

# ─── API jeu ─────────────────────────────────────────────────────────────────

@app.route('/api/join', methods=['POST'])#->c est pour rejoindre la session
def api_join():
    if 'username' not in session:
        return jsonify({'error': 'not logged in'}), 401
    username = session['username']
    with table_lock:
        if table['phase'] in ('waiting', 'joining'):
            p = get_player(username)
            if p['status'] not in ('idle', 'betting', 'playing', 'stand', 'bust', 'blackjack'):
                p['status'] = 'idle'
        elif username not in table['players']:
            get_player(username)
    return jsonify({'ok': True})

@app.route('/api/join_round', methods=['POST'])#->c est pour pouvoir avoir des rounds
def api_join_round():
    if 'username' not in session:
        return jsonify({'error': 'not logged in'}), 401
    username = session['username']
    with table_lock:
        if table['phase'] != 'joining':
            return jsonify({'error': 'Pas en phase joining'}), 400
        p = get_player(username)
        p['status'] = 'idle'
    return jsonify({'ok': True})

@app.route('/api/leave', methods=['POST'])#-> c est pour pouvoir quitter le jeu
def api_leave():
    if 'username' not in session:
        return jsonify({'error': 'not logged in'}), 401
    username = session['username']
    with table_lock:
        if username not in table['players']:
            return jsonify({'ok': True})
        player = table['players'][username]
        if table['phase'] == 'playing' and player['status'] == 'playing':
            player['status'] = 'stand'
            _check_playing_done()
        del table['players'][username]#->del permet d effacer la table
    return jsonify({'ok': True})

@app.route('/api/start', methods=['POST'])#-> c est pour demarer le jeu
def api_start():
    if 'username' not in session:
        return jsonify({'error': 'not logged in'}), 401
    with table_lock:
        if table['phase'] != 'waiting':
            return jsonify({'error': 'Impossible de démarrer'}), 400
        if not table['players']:
            return jsonify({'error': 'Aucun joueur'}), 400
        table['phase']         = 'joining'
        table['join_deadline'] = time.time() + JOIN_SECONDS
        for p in table['players'].values():
            p['hand'], p['bet'], p['status'] = [], 0, 'idle'
    return jsonify({'ok': True})

@app.route('/api/bet', methods=['POST'])#->parier
def api_bet():
    if 'username' not in session:
        return jsonify({'error': 'not logged in'}), 401
    username = session['username']
    data     = request.get_json()
    amount   = int(data.get('amount', 0))#->permet de transformer le nombre string ""en entier pour faire des calculs
    with table_lock:
        if table['phase'] != 'betting':
            return jsonify({'error': 'Phase incorrecte'}), 400
        player  = get_player(username)
        if player['status'] != 'betting':
            return jsonify({'error': 'Pas ton tour de miser'}), 400
        balance = get_balance(username)
        if amount < 1 or amount > balance:
            return jsonify({'error': f'Mise invalide (max {balance}€)'}), 400
        player['bet'] = amount
        if table['jyss_mode'] == 'super':
            player['hand']   = forced_blackjack_hand()
            player['status'] = 'blackjack'
            jyss_log(f"🃏 SUPERJYSSMODE pour {username} — Blackjack forcé !")
        else:
            player['hand']   = [table['deck'].pop(), table['deck'].pop()]
            player['status'] = 'blackjack' if is_blackjack(player['hand']) else 'playing'
        if not table['dealer_hand']:
            table['dealer_hand'] = [table['deck'].pop(), table['deck'].pop()]
        _try_advance_to_playing()
    return jsonify({'ok': True})

@app.route('/api/hit', methods=['POST'])#->pour piocher 
def api_hit():
    if 'username' not in session:
        return jsonify({'error': 'not logged in'}), 401
    username = session['username']
    with table_lock:
        if table['phase'] != 'playing':
            return jsonify({'error': 'Phase incorrecte'}), 400
        player = get_player(username)
        if player['status'] != 'playing':
            return jsonify({'error': 'Action impossible'}), 400
        player['hand'].append(table['deck'].pop())
        player['timer_start'] = time.time()
        val = hand_value(player['hand'])
        if val > 21:    player['status'] = 'bust'
        elif val == 21: player['status'] = 'stand'
        _check_playing_done()
    return jsonify({'ok': True, 'value': hand_value(table['players'][username]['hand'])})

@app.route('/api/stand', methods=['POST'])
def api_stand():#->pour l attente du joueur
    if 'username' not in session:
        return jsonify({'error': 'not logged in'}), 401
    username = session['username']
    with table_lock:
        if table['phase'] != 'playing':
            return jsonify({'error': 'Phase incorrecte'}), 400
        player = get_player(username)
        if player['status'] != 'playing':
            return jsonify({'error': 'Action impossible'}), 400
        player['status'] = 'stand'
        _check_playing_done()
    return jsonify({'ok': True})

@app.route('/api/results')#->pour les resultats
def api_results():
    with table_lock:
        return jsonify(table.get('last_results', {}))

@app.route('/api/new_round', methods=['POST'])#->pour commencer un nouveau round
def api_new_round():
    if 'username' not in session:
        return jsonify({'error': 'not logged in'}), 401
    with table_lock:
        if table['phase'] != 'results':
            return jsonify({'error': 'Pas encore fini'}), 400
        for u in list(table['players']):
            if get_balance(u) == 0:
                reset_wallet(u)
        table['phase']         = 'joining'
        table['join_deadline'] = time.time() + JOIN_SECONDS
        for p in table['players'].values():
            p['status'], p['hand'], p['bet'] = 'idle', [], 0
    return jsonify({'ok': True})

@app.route('/api/leaderboard')#->pour le leaderboard
def api_leaderboard():
    sorted_lb = sorted(get_all_balances().items(), key=lambda x: x[1], reverse=True)
    return jsonify(sorted_lb)

# ─── API master ───────────────────────────────────────────────────────────────
#->pour pouvoir tricher
@app.route('/api/master/force_blackjack', methods=['POST'])#-> pour avoir un blackjack garanti
def api_master_force_blackjack():
    if not session.get('jyss_auth'):
        return jsonify({'error': 'unauthorized'}), 403
    with table_lock:
        table['jyss_mode'] = 'super'
        jyss_log("⚡ Force Blackjack activé par le Maître")
    return jsonify({'ok': True})

@app.route('/api/master/normal', methods=['POST'])#->pour pouvoir rejouer normalement
def api_master_normal():
    if not session.get('jyss_auth'):
        return jsonify({'error': 'unauthorized'}), 403
    with table_lock:
        table['jyss_mode'] = False
        jyss_log("✅ Mode normal rétabli")
    return jsonify({'ok': True})

@app.route('/api/master/reset', methods=['POST'])#->c est pour tout reset 
def api_master_reset():
    if not session.get('jyss_auth'):
        return jsonify({'error': 'unauthorized'}), 403
    with table_lock:
        table.update({
            'deck': [], 'dealer_hand': [], 'players': {},
            'phase': 'waiting', 'jyss_mode': False, 'round_number': 0,
            'join_deadline': None,
            'jyss_logs': [{'time': time.time(), 'msg': '🔴 RESET TOTAL par le Maître'}],
        })
    for u in get_all_balances():
        reset_wallet(u)
    return jsonify({'ok': True})

# Garder les anciennes routes jyss pour compatibilité
@app.route('/jyss')#->pour gerer le compte jyss et pouvoir r avoir au mm point
def jyss_panel():
    return redirect(url_for('index'))

if __name__ == '__main__':#-> si ce qui est a la ligne d en dessous est original (main)alors le lancer si il a ete importé alors ne pas
    app.run(debug=True, host='0.0.0.0', port=5000)#->on lance dans le resau local 127.0.0.1