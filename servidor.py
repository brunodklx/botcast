from flask import Flask, request, jsonify
from datetime import datetime
import logging
import os
import json

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carregando os dados dos usuários de um arquivo JSON
def carregar_dados_usuarios():
    with open('dados_usuarios.json', 'r') as f:
        return json.load(f)

users_db = carregar_dados_usuarios()

def check_expiration(date_str):
    try:
        expiration_date = datetime.strptime(date_str, "%Y-%m-%d")
        current_date = datetime.now()
        return current_date >= expiration_date
    except ValueError:
        print(f"[ERROR] Data inválida fornecida: {date_str}")
        return True  # Considere como expirado em caso de erro na data

@app.route('/check_access', methods=['POST'])
def check_access():
    logging.info("Recebendo requisição de acesso...")
    data = request.json
    username = data.get('username')
    password = data.get('password')

    logging.info(f"Tentativa de login: usuário '{username}'")

    user = users_db.get(username)
    if user:
        logging.info(f"Usuário encontrado: {username}")

        # Verifica se a senha está correta
        if user['senha'] == password and user['status'] == 'ativo':
            # Verifica se a expiração é válida
            if not check_expiration(user['expiracao']):
                logging.info(f"Acesso concedido para o usuário '{username}'")
                return jsonify({"access": True}), 200
            else:
                logging.warning(f"Acesso negado: assinatura expirada para o usuário '{username}'")
                return jsonify({"access": False, "reason": "Subscription expired"}), 403
        else:
            logging.warning(f"Acesso negado: usuário ou senha inválidos para '{username}'")
            return jsonify({"access": False, "reason": "Invalid username or password"}), 403

    logging.warning(f"Acesso negado: usuário '{username}' não encontrado")
    return jsonify({"access": False, "reason": "User not found"}), 403

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
