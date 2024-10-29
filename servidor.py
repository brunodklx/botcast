import json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

def carregar_dados_usuarios():
    with open("dados_usuarios.json", "r") as f:
        return json.load(f)

def check_expiration(date_str):
    expiration_date = datetime.fromisoformat(date_str)
    return expiration_date >= datetime.now()

@app.route('/check_access', methods=['POST'])
def check_access():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    users_db = carregar_dados_usuarios()
    user = users_db.get(username)
    
    if user and user['senha'] == password:
        if user['status'] == 'ativo' and check_expiration(user['expiracao']):
            return jsonify({"access": True}), 200
        else:
            return jsonify({"access": False, "reason": "Subscription expired or inactive"}), 403
    else:
        return jsonify({"access": False, "reason": "Invalid username or password"}), 403

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)