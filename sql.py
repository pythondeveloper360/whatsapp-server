import datetime
import random
from os import read

import psycopg2
from psycopg2 import sql

alphabet = [*[chr(i) for i in range(97, 123)], *[chr(i)
                                                 for i in range(65, 91)], *[chr(i) for i in range(48, 58)]]

db = psycopg2.connect(host="localhost",
                      user="postgres",
                      database="whatsapp",
                      port="5432",
                      password="qsa-1299")

cursor = db.cursor()


def time(time):
    t = time.split(':')
    if int(t[0]) > 12:
        return(f"{int(t[0])-12}:{t[1]}:{t[2]}")
    else:
        return f"{t[0]}:{t[1]}:{t[2]}"


def idGenerator(range_=10):
    random.shuffle(alphabet)
    return ''.join(alphabet[0:int(range_)])


def authenticateUser(username, password):
    sqlquery = sql.SQL('select * from users where {username} = %s and {password} = %s').format(
        username=sql.Identifier("user_id"),
        password=sql.Identifier("password")
    )
    try:
        cursor.execute(sqlquery, (username, password))
        data = cursor.fetchall()
        return (True if data else False)
    except psycopg2.ProgrammingError:
        return authenticateUser(username=username,password=password)


def nameFromId(id):
    sqlquery = sql.SQL('select name from users where {user_id} = %s').format(
        user_id=sql.Identifier("user_id"))
    try:
        cursor.execute(sqlquery, (id,))
        data = cursor.fetchone()
        return {"id": id, "name": data[0]} if data else False
    except psycopg2.ProgrammingError:
        return nameFromId(id = id)


def getChats(user_id):
    returnData = []
    sqlquery = sql.SQL('select {chats} from rooms where %s = any(chats) ').format(
        chats=sql.Identifier("chats")
    )
    try:
        cursor.execute(sqlquery, (user_id,))
        data = cursor.fetchall()
        for i in data:
            i[0].remove(user_id)
            returnData.append({**nameFromId(i[0][0])})

        return(returnData)
    except psycopg2.ProgrammingError:
        return getChats(user_id= user_id)


def getRoomId(chat1, chat2):
    sqlquery = sql.SQL(
        'select {id} from rooms where  %s = any (chats) and  %s = any(chats) ').format(id=sql.Identifier("id"))
    try:
        cursor.execute(sqlquery, (chat1, chat2))
        temp = cursor.fetchone()
        return temp[0] if temp else False
    except psycopg2.ProgrammingError:
        return getRoomId(chat1=chat1,chat2=chat2)
    


def createRoom(chat1, chat2):
    if getRoomId(chat1, chat2) == False:
        sqlquery = sql.SQL('insert into rooms ({id},{date},{chats}) values(%s,%s,%s)').format(
            id=sql.Identifier("id"),
            date=sql.Identifier("date"),
            chats=sql.Identifier("chats")
        )
        cursor.execute(sqlquery, (idGenerator(), datetime.datetime.today().strftime(
            '%Y-%m-%d'), [chat1, chat2]))
        db.commit()
    else:
        return False


def message(msg, receiver_id, sender_id):
    message_id = idGenerator()
    room_id = getRoomId(receiver_id, sender_id)
    tm = datetime.datetime.today()
    ti = time(tm.strftime('%X'))
    sqlquery = sql.SQL('insert into messages ({id},{message},{time},{sender_id},{receiver_id},{sender_name},{receiver_name},{date},{room_id}) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)').format(
        id=sql.Identifier("id"),
        message=sql.Identifier("message"),
        time=sql.Identifier("time"),
        sender_id=sql.Identifier("sender_id"),
        receiver_id=sql.Identifier("receiver_id"),
        sender_name=sql.Identifier("sender_name"),
        receiver_name=sql.Identifier("receiver_name"),
        room_id=sql.Identifier("room_id"),
        date=sql.Identifier("date")
    )
    if room_id:
        cursor.execute(sqlquery, (message_id, msg, ti, sender_id, receiver_id, nameFromId(
            sender_id)['name'], nameFromId(receiver_id)['name'], datetime.datetime.today().strftime('%Y-%m-%d'), room_id))
        db.commit()
        return {"id": message_id, "msg": msg, "time": ti, "sender_id": sender_id, "receiver_id": receiver_id, "serder_name": nameFromId(
            sender_id)['name'], "receiver_name": nameFromId(receiver_id)['name'], "date": datetime.datetime.today().strftime('%Y-%m-%d'), "room_id": room_id}
    else:
        return False


def getMessages(sender_id, receiver_id):
    returnData = []
    room_id = getRoomId(sender_id, receiver_id)
    sqlquery1 = sql.SQL('select * from messages where {room_id} = %s').format(
        room_id=sql.Identifier("room_id")
    )
    try:
        cursor.execute(sqlquery1, (room_id,))
        data = cursor.fetchall()
        for i in data:
            returnData.append({"id": i[0], "msg": i[1], "time": i[2].strftime('%X'), "sender_id": i[3],
                            "receiver_id": i[4], "sender_name": i[5], "receiver_name": i[6], "date": i[7].strftime("%x"), "room_id": i[8], "read": i[9]})

        return(returnData)
    except psycopg2.ProgrammingError:
        return getMessages(sender_id= sender_id,receiver_id=receiver_id)

def readAllMEssages(sender_id,receiver_id):
    sqlquery = sql.SQL('update messages set {read} = true where {sender_id} = %s and {receiver_id} = %s').format(
        read = sql.Identifier("read"),
        sender_id = sql.Identifier("sender_id"),
        receiver_id = sql.Identifier("recevier_id")
    )
    cursor.execute(sqlquery,(sender_id,receiver_id))
    db.commit()


def getUnReadMessagesStatus(user_id):
    returnData = []
    chats = getChats(user_id)
    for i in chats:
        sqlquery = sql.SQL('select read from messages where {sender_id} = %s and {receiver_id} = %s and read = false').format(
            sender_id=sql.Identifier("sender_id"),
            receiver_id=sql.Identifier("receiver_id")
        )
        cursor.execute(sqlquery, (i['id'], user_id))
        data = cursor.fetchall()
        returnData.append(
            {'id': i['id'], 'messages': len(data)})if data else False
    return returnData


def readMessage(msg_id):
    sqlquery = sql.SQL('update messages set read = true where {id} = %s').format(
        id=sql.Identifier("id"))
    cursor.execute(sqlquery, (msg_id,))
    db.commit()


def authenticateUserLogin(username, token, client_id):
    sqlquery = sql.SQL('select * from logins where {username} = %s and {token} = %s and {client_id} = %s').format(
        username=sql.Identifier("username"),
        token=sql.Identifier("token"),
        client_id=sql.Identifier("client_id")
    )
    cursor.execute(sqlquery, (username, token, client_id))
    d = cursor.fetchall()
    return (True if d else False)


def loginUser(username, password):
    token = idGenerator(range_=15)
    client_id = idGenerator(range_=15)
    if authenticateUser(username, password):
        sqlquery = sql.SQL(
            "insert into logins (token,username,client_id) values (%s,%s,%s)")
        cursor.execute(sqlquery, (token, username, client_id))
        db.commit()
        return {"status": True, "client_id": client_id, "token": token}
    else:
        return {"status": False}


def getChatListOnly(user_id):
    returnData = []
    sqlquery = sql.SQL('select chats from rooms where %s = any({chats})').format(
        chats=sql.Identifier("chats"))
    cursor.execute(sqlquery, (user_id,))
    data = list(cursor.fetchall())
    for i in data:
        i[0].remove(user_id)
        returnData.append(i[0][0])
    return returnData


def getChatsUnreadMessages(user_id):
    chats = getChats(user_id)
    unreadMessages = getUnReadMessagesStatus(user_id)
    for i in chats:
        for x in unreadMessages:
            if x['id'] == i['id']:
                i.update({'unReadMessages': x['messages']})
            else:
                i.update({"unReadMessages": 0})
    return chats


def userConnected(id,username):
    check = nameFromId(username)
    check = True if check else False
    if check:
        sqlquery = sql.SQL('select {username} from connected_users where {id} =  %s').format(
            username=sql.Identifier("username"), id=sql.Identifier("id"))
        cursor.execute(sqlquery, (username,))
        data = cursor.fetchone()
        data = False if data else True
        if (data):
            sqlquery = sql.SQL("insert into connected_users ({id},{username}) values (%s,%s)").format(
                id=sql.Identifier("id"), username=sql.Identifier("username"))
            
            cursor.execute(sqlquery,(id,username))
            db.commit()
def connectedUsersId(username):
    rL = []
    sqlquery = sql.SQL("select id from connected_users where {username} = %s").format(username = sql.Identifier("username"))
    cursor.execute(sqlquery,(username,))
    data = cursor.fetchall()
    for i in data:
        rL.append(i[0])
    return rL
def disconnectUser(id):
    sqlquery = sql.SQL('delete from connected_users where {id} = %s').format(id = sql.Identifier("id"))
    cursor.execute(sqlquery,(id,))
    db.commit()
