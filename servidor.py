from flask import Flask, request, jsonify
import threading
import json
from datetime import datetime
import time

app = Flask(__name__)

# Carrega os dados dos usuários de um arquivo JSON
def carregar_dados_usuarios():
    with open('dados_usuarios.json', 'r') as f:
        return json.load(f)

users_db = carregar_dados_usuarios()

# Função para verificar se a assinatura expirou
def check_expiration(date_str):
    try:
        expiration_date = datetime.fromisoformat(date_str)
        current_date = datetime.now()
        return current_date >= expiration_date
    except ValueError:
        return True  # Considere como expirado em caso de erro na data

# Função de monitoramento de expirações
def monitorar_expiracoes():
    while True:
        for username, user_data in users_db.items():
            if 'status' not in user_data or 'expiracao' not in user_data:
                continue  # Usuário com dados incompletos

            if user_data['status'] == 'ativo' and check_expiration(user_data['expiracao']):
                user_data['status'] = 'expirado'
                print(f"[INFO] Assinatura de {username} expirada.")

        time.sleep(600)  # Verifica a cada 10 minutos

# Inicia o monitoramento de expiração em uma thread separada
expiracao_thread = threading.Thread(target=monitorar_expiracoes, daemon=True)
expiracao_thread.start()

@app.route('/check_access', methods=['POST'])
def check_access():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users_db.get(username)

    if user and user['senha'] == password:
        if user['status'] == 'ativo':
            if check_expiration(user['expiracao']):
                user['status'] = 'expirado'
                return jsonify({"access": False, "reason": "Subscription expired or inactive"})
            return jsonify({"access": True}), 200
        else:
            return jsonify({"access": False, "reason": "Subscription expired or inactive"})
    return jsonify({"access": False, "reason": "Invalid username or password"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)



