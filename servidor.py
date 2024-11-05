import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import requests

app = Flask(__name__)

FLASK_LOCAL_URL = " http://127.0.0.1:8080"  # Substitua pelo IP do seu servidor local

app.config['SECRET_KEY'] = 'secret!'  # Define uma chave secreta
socketio = SocketIO(app)

# Armazena conexões de clientes ativas
connected_clients = {}
users_db = {}

# Simulando dados dos usuários
def carregar_dados_usuarios():
    with open('dados_usuarios.json', 'r') as f:
        return json.load(f)

users_db = carregar_dados_usuarios()

connected_clients = {}

def check_expiration(date_str):
    try:
        expiration_date = datetime.fromisoformat(date_str)
        current_date = datetime.now()
        return current_date >= expiration_date
    except ValueError:
        return True  # Considere como expirado em caso de erro na data

def monitorar_expiracoes():
    estado_anterior = {}  # Armazenar o estado anterior de cada usuário

    while True:
        for username, user_data in users_db.items():
            if 'status' not in user_data or 'expiracao' not in user_data:
                continue  # Usuário com dados incompletos

            is_expired = check_expiration(user_data['expiracao'])

            # Se o usuário era ativo e expirou
            if user_data['status'] == 'ativo' and is_expired:
                if username in connected_clients and (
                    username not in estado_anterior or not estado_anterior[username]['expirado']
                ):
                    try:
                        socketio.emit('disconnect_client', {'message': 'Sessão expirada'}, room=connected_clients[username])
                        del connected_clients[username]  # Remover cliente da lista após emitir o sinal
                    except Exception:
                        pass  # Manter os logs apenas onde for estritamente necessário

            # Atualizar o estado do usuário
            estado_anterior[username] = {'expirado': is_expired}

        # Aumentar o tempo de verificação para cada 10 minutos (600 segundos)
        time.sleep(600)

# Iniciar o monitoramento de expiração em uma thread separada
expiracao_thread = threading.Thread(target=monitorar_expiracoes, daemon=True)
expiracao_thread.start()

@app.route('/check_access', methods=['POST'])
def check_access():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    users_db = carregar_dados_usuarios()
    user = users_db.get(username)

    if user and user['senha'] == password:
        if user['status'] == 'ativo':
            is_expired = check_expiration(user['expiracao'])
            if is_expired:
                # Usuário está ativo, mas a assinatura expirou
                if username in connected_clients:
                    try:
                        socketio.emit('disconnect_client', {'message': 'Sessão expirada'}, room=connected_clients[username])
                        del connected_clients[username]  # Remover cliente da lista após emitir o sinal
                    except Exception:
                        pass
                return jsonify({"access": False, "reason": "Subscription expired or inactive"})
            else:
                # Usuário está ativo e a assinatura é válida
                return jsonify({"access": True}), 200
        return jsonify({"access": False, "reason": "Subscription expired or inactive"})

    return jsonify({"access": False, "reason": "Invalid username or password"})

@app.route('/flask_local_check', methods=['POST'])
def flask_local_check():
    try:
        response = requests.post(f"{FLASK_LOCAL_URL}/check_access", json=request.json)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": "Falha ao comunicar com o servidor local", "details": str(e)}), 500
    
@app.route('/monitorar_expiracoes', methods=['POST'])
def monitorar_expiracoes():
    # Repassar a requisição de monitoramento ao servidor Flask local
    try:
        response = requests.post(f"{FLASK_LOCAL_URL}monitorar_expiracoes")
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({"error": "Falha ao comunicar com o servidor local", "details": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    pass

@socketio.on('register')
def handle_register(data):
    username = data.get('username')
    if username:
        connected_clients[username] = request.sid
        print(f"Usuário {username} registrado com o SID {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    for username, client_sid in list(connected_clients.items()):
        if client_sid == sid:
            del connected_clients[username]
            print(f"Cliente ({username}) desconectado")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)


