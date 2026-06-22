import json
import os

WALLET_FILE = 'data/wallets.json'
STARTING_BALANCE = 10000

def load_wallets():
    if not os.path.exists(WALLET_FILE):
        return {}
    with open(WALLET_FILE, 'r') as f:
        return json.load(f)

def save_wallets(wallets):
    os.makedirs('data', exist_ok=True)
    with open(WALLET_FILE, 'w') as f:
        json.dump(wallets, f, indent=2)

def get_balance(username):
    wallets = load_wallets()
    if username not in wallets:
        wallets[username] = STARTING_BALANCE
        save_wallets(wallets)
    return wallets[username]

def update_balance(username, amount):
    """amount can be positive (win) or negative (loss)"""
    wallets = load_wallets()
    if username not in wallets:
        wallets[username] = STARTING_BALANCE
    wallets[username] += amount
    if wallets[username] < 0:
        wallets[username] = 0
    save_wallets(wallets)
    return wallets[username]

def get_all_balances():
    return load_wallets()

def reset_wallet(username):
    wallets = load_wallets()
    wallets[username] = STARTING_BALANCE
    save_wallets(wallets)
