from flask import Flask, request, jsonify
from datetime import datetime
import logging


app = Flask(__name__)

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Simulando um banco de dados de usuários e suas assinaturas
users_db = {
    "brunodklx": {"senha": "0daa85d9", "status": "ativo", "expiracao": "2024-10-29T00:00:00"},
    "usuario2": {"senha": "senha2", "status": "ativo", "expiracao": "2024-10-27T22:40:30"}
}

def check_expiration(date_str):
    """Verifica se a assinatura expirou com base na data fornecida."""
    expiration_date = datetime.strptime(date_str, "%Y-%m-%d")
    return expiration_date >= datetime.now()

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
            now = datetime.now().isoformat()
            if user['expiracao'] > now:
                logging.info(f"Acesso concedido para o usuário '{username}'")
                return jsonify({"access": True}), 200
            else:
                logging.warning(f"Acesso negado: assinatura expirada para o usuário '{username}'")
                return jsonify({"access": False, "reason": "Subscription expired"}), 403
        else:
            logging.warning(f"Acesso negado: usuário ou senha inválidos para '{username}'")
            return jsonify({"access": False, "reason": "Invalid username or password"}), 403
    else:
        logging.warning(f"Acesso negado: usuário '{username}' não encontrado")
        return jsonify({"access": False, "reason": "User not found"}), 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)