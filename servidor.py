import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time

app = Flask(__name__)
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

# Função auxiliar para verificar expiração
def check_expiration(date_str):
    try:
        expiration_date = datetime.fromisoformat(date_str)
        current_date = datetime.now()

        expired = current_date >= expiration_date
        return expired
    except ValueError as e:
        print(f"[ERRO] Erro ao analisar a data de expiração: {e}")
        return True  # Por segurança, considere a assinatura expirada se houver um erro na data
    
# Função para monitorar a expiração de assinaturas
def monitorar_expiracoes():
    estado_anterior = {}  # Armazenar o estado anterior de cada usuário

    while True:
        for username, user_data in users_db.items():
            if 'status' not in user_data or 'expiracao' not in user_data:
                print(f"[ERRO] Dados incompletos para o usuário: {username}")
                continue

            is_expired = check_expiration(user_data['expiracao'])

            # Se o estado do usuário mudou para expirado e ele está conectado
            if user_data['status'] == 'ativo' and is_expired:
                if username in connected_clients:
                    if username not in estado_anterior or not estado_anterior[username]['expirado']:
                        print(f"[INFO] Assinatura de {username} expirou. Enviando sinal de desconexão.")
                        try:
                            socketio.emit('disconnect_client', {'message': 'Sessão expirada'}, room=connected_clients[username])
                            print(f"[INFO] Sinal de desconexão enviado para {username}.")
                            del connected_clients[username]  # Remover cliente da lista após emitir o sinal
                        except Exception as e:
                            print(f"[ERRO] Falha ao emitir sinal de desconexão para {username}: {e}")
                    
                    # Atualizar o estado do usuário para indicar que ele foi desconectado
                    estado_anterior[username] = {'expirado': True}
            else:
                # Caso o usuário não esteja expirado, atualizar o estado como não expirado
                estado_anterior[username] = {'expirado': False}

        time.sleep(60)  # Verifica a cada 60 segundos

# Iniciar o monitoramento de expiração em uma thread separada
expiracao_thread = threading.Thread(target=monitorar_expiracoes, daemon=True)
expiracao_thread.start()
print("[INFO] Monitoramento de expiração iniciado.")




# Iniciar o monitoramento de expiração em uma thread separada
print("[INFO] Iniciando o monitoramento de expiração.")
expiracao_thread = threading.Thread(target=monitorar_expiracoes, daemon=True)
expiracao_thread.start()
print("[INFO] Monitoramento de expiração iniciado.")
 
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
                print(f"Assinatura expirada ou inativa para o usuário: {username}")
                if username in connected_clients:
                    print(f"Emitindo sinal de desconexão para o cliente: {username}")
                    try:
                        socketio.emit('disconnect_client', {'message': 'Sessão expirada'}, room=connected_clients[username])
                        print(f"Sinal de desconexão emitido com sucesso para o cliente: {username}")
                        # Remover cliente da lista após emitir o sinal
                        del connected_clients[username]
                    except Exception as e:
                        print(f"[ERRO] Falha ao emitir sinal de desconexão: {e}")
                else:
                    print(f"Cliente ({username}) não encontrado em `connected_clients`.")
                return jsonify({"access": False, "reason": "Subscription expired or inactive"})
            else:
                # Usuário está ativo e a assinatura é válida
                print(f"Usuário {username} está ativo e a assinatura é válida.")
                return jsonify({"access": True}), 200
        else:
            print(f"Assinatura expirada ou inativa para o usuário: {username}")
            return jsonify({"access": False, "reason": "Subscription expired or inactive"})
    else:
        print(f"Falha de login para o usuário: {username}")
        return jsonify({"access": False, "reason": "Invalid username or password"})

@socketio.on('connect')
def handle_connect():
    print(f"Cliente conectado: {request.sid}")

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
    socketio.run(app, host="0.0.0.0", port=8080)



