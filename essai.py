from flask import Flask, jsonify
app = Flask(__name__)
@app.route("/")
def acceuil():
    return"Bienvenue au Blackjack!"
@app.route("/api/etat")
def etat():
     return jsonify({"phase":"mise","joueurs": 3})
app.run(debug=True)