from threading import Thread

from flask import Flask, abort, jsonify, request,make_response
from flask_socketio import SocketIO, emit, join_room, send

import sql

app = Flask(__name__)
app.secret_key = sql.idGenerator(range_=20)
app.config['CORS_HEADERS'] = 'Content-Type'
socketio = SocketIO(app, cors_allowed_origins="*")


@app.after_request
def after_request_func(response):
    origin = request.headers.get('Origin')
    if request.method == 'OPTIONS':
        # TODO i think I need to add content-type header in access-control-allow-headers on post requests
        response = make_response()

        response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-type, username,password,token,client_id,device_name')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, OPTIONS, PUT, PATCH, DELETE')
    else:
        pass

    return response

@app.route('/login', methods=["POST"])
def login():
    data = request.headers
    if data.get('username') and data.get('token'):
        if (sql.authenticateUserLogin(username=data.get('Username'), token=data.get('Token'), client_id=data.get('Client_id'))):
            res = jsonify(
                {"status": True, "cre": sql.nameFromId(data.get('username'))})
            res.headers.add('Access-Control-Allow-Origin', '*')
            return res
        else:
            res = jsonify({"status": False})
            res.headers.add('Access-Control-Allow-Origin', '*')
            return res
    else:
        abort(400)


@app.route("/chats")
def chats():
    data = request.headers
    if data.get('username') and data.get('token'):
        if (sql.authenticateUserLogin(username=data.get('username'), token=data.get('token'), client_id=data.get('client_id'))):

            res = jsonify({"chats": sql.getChatsUnreadMessages(
                data.get('username')), 'chatsList': sql.getChatListOnly(data.get('username'))})
            res.headers.add('Access-Control-Allow-Origin', '*')
            return res
        else:
            abort(404)
    else:
        abort(400)


@app.route('/msgs', methods=['POST'])
def msgs():
    headerData = request.headers
    if headerData.get('username') and headerData.get('token') and headerData.get('chat_id'):
        res = jsonify({{"msg": sql.getMessages(headerData.get('username'), headerData.get('chat_id')), "name": sql.nameFromId(headerData.get('chat_id'))['name']}})
        res.headers.add('Access-Control-Allow-Origin', '*')
        return res

    else:
        abort(404)


@app.route('/loginAuth')
def loginAuth():
    data = request.headers
    if (data.get('username') and data.get('password')):
        work = sql.loginUser(data.get('username'), data.get('password'))
        if work:
            res = jsonify(work)
            res.headers.add('Access-Control-Allow-Origin', '*')
            return res
        else:
            abort(400)
    else:
        abort(404)
@app.route('/create_account')
def createAccount():
    data = request.headers
    print(data)

@socketio.on('send_msg')
def send_msg(data):
    work = sql.message(msg=data.get('msg'), receiver_id=data.get(
        'receiver_id'), sender_id=data.get('sender_id'))
    if work:
        [Thread(emit('msg_sent', work, to=i)).start()
         for i in sql.connectedUsersId(data.get('receiver_id'))]
        [Thread(emit('msg_sent', work, to=i)).start()
         for i in sql.connectedUsersId(data.get('sender_id'))]


@socketio.on('connected')
def connected(data):
    work = sql.userConnected(data.get('id'), data.get('username'))


@socketio.on("disconnect")
def userDisconnected():
    work = sql.disconnectUser(request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
