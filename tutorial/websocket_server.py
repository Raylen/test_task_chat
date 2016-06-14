__author__ = 'Kael'

import json
import psycopg2
from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

# 2-d list
# [0] - connection
# [1] - username
# [2] - user_id
# [3] - group_id
cursor = ''
clients = []


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print(self.peer, 'connected')

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))
        message = payload.decode('utf8')   # message - python string, payload - json string
        words = message.split('"')[1].split(" ")
        # message structure will match one of the following types:
        #   message - "<name>: <message>"
        if words[0] == '(User_entered)':
            # check if user already exists, 1 - return id, 0 - create and return id
            try:
                cursor.execute("""SELECT user_id FROM active_users WHERE name='{0}' """.format(words[1]))
            except:
                print('Cannot execute query ' + 'SELECT user_id FROM active_users WHERE name=' + words[1])
                print("""SELECT user_id FROM active_users WHERE name="{0}" """.format(words[1]));
                return
            rows = cursor.fetchall()
            if len(rows) == 0:
                try:
                    cursor.execute("""INSERT INTO active_users (name, created) VALUES (%s, now()) RETURNING user_id""",
                                   words[1])
                except:
                    print('Cannot execute query ' + 'INSERT INTO active_users (name) VALUES ' + words[1] +
                          'RETURNING user_id')
                    return
                rows = cursor.fetchall()
            self.sendJSONmsg(rows[0][0][0], isBinary)
        elif words[0] == '(Get_groups)':
            # getting group list
            try:
                cursor.execute("""SELECT group_id, topic FROM groups""")
            except:
                print('Cannot execute query ' + 'SELECT group_id, topic FROM groups')
                return
            rows = cursor.fetchall()
            for row in rows:
                self.sendJSONmsg(row[0][0] + ',' + row[0][1], isBinary)
        elif words[0] == '(Group_created)':
            # created new group
            topic = message.split('"')[1].split(") ")[1]
            try:
                cursor.execute("""INSERT INTO groups (topic, created) VALUES ((%s), now()) RETURNING group_id""",
                               topic)
            except:
                print('Cannot execute query ' + 'INSERT INTO groups (topic, created) VALUES ' + topic + 'now()' +
                      'RETURNING group_id')
                return
            rows = cursor.fetchall()
            group_id = rows[0][0][0]
            self.sendJSONmsg(group_id + "," + topic, isBinary)
        elif words[0] == '(Get_names)':
            # user requested group members upon entering group
            for i in range(len(clients[0])):
                if clients[3][i] == words[1]:   # if client is in group
                    self.sendJSONmsg('(user) ' + clients[1][i], isBinary)
        elif words[0] == '(User_connected)':
            # 1)register entering user
            # 2)return user his name and group topic
            # 3)send welcoming messages to everyone in group
            try:
                cursor.execute("""SELECT name FROM active_users WHERE user_id=(%s)""", words[1])
            except:
                print('Cannot execute query ' + 'SELECT user_id FROM active_users WHERE name=' + words[1])
                return
            rows = cursor.fetchall()
            username = rows[0][0][0]
            try:
                cursor.execute("""SELECT topic FROM groups WHERE group_id=(%s)""", words[2])
            except:
                print('Cannot execute query ' + 'SELECT topic FROM groups WHERE group_id=' + words[2])
                return
            rows = cursor.fetchall()
            topic = rows[0][0][0]
            # 1)
            clients.append([self, username, words[1], words[2]])
            # 2)
            self.sendJSONmsg('(self) ' + username + ' ' + topic, isBinary)
            # 3)
            for i in clients:
                if clients[3][i] == words[2]:
                    clients[0][i].sendJSONmsg('(msg) Welcome ' + username + ' !', isBinary)
#        elif words[0] == '(Rename)':
            # 1) update info in db
            # 2) update everyone's in this group display of this name
#            username = words[1]
#            uid = words[2]
#            gid = words[3]
            # 1)
#            try:
#                cursor.execute("""UPDATE active_users SET name=(%s) WHERE user_id=(%s)""", username, uid)
#            except:
#                print('Cannot execute query ' + 'UPDATE active_users SET name=' + username + ' WHERE user_id=' + uid)
#                return
            # 2)
#            for i in range(len(clients[0])):
#                if clients[2][i] == uid and clients[3][i] == gid:
#                    oldname = clients[1][i]
#                    clients[1][i] = username
#                    break
#            for i in range(len(clients[0])):
#                if clients[3][i] == gid:
#                    clients[0][i].sendJSONmsg('(Rename) ' + oldname + ' ' + username)
        elif words[0] == '(User_disconnected)':
            # 1)register leaving user
            # 2)send welcoming messages to everyone in group
            uid = words[1]
            gid = words[2]
            # 1)
            for i in range(len(clients[0])):
                if clients[2][i] == uid and clients[3][i] == gid:
                    username = clients[1][i]
                    del clients[0][i]
                    del clients[1][i]
                    del clients[2][i]
                    del clients[3][i]
                    break
            # 2)
            for i in clients:
                if clients[3][i] == words[2]:
                    clients[0][i].sendJSONmsg('(remove) ' + username, isBinary)
                    clients[0][i].sendJSONmsg('(msg) Farewell ' + username + ' !', isBinary)
        elif words[0] == '(Msg)':
            # message received
            # 1) write message into db
            # 2) send message to everyone in this group
            uid = words[1]
            gid = words[2]
            i = 3
            msg = ''
            while i < len(words):
                msg += words[i]
                i += 1
            # msg = whole message data without ids
            try:
                cursor.execute("""INSERT INTO messages (message, created, user_id, group_id) VALUES (%s,now(),%s,%s)""",
                               msg, uid, gid)
            except:
                print('Cannot execute query ' + 'INSERT INTO messages (message, created, user_id, group_id) VALUES ' +
                      msg + ',now(),' + uid + ',' + gid)
                return
            for i in range(len(clients[0])):
                if clients[3][i] == uid:
                    clients[0][i].sendJSONmsg(msg, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def sendJSONmsg(self, message, isBinary):
        jsonmsg = json.dumps(message)
        self.sendMessage(jsonmsg, isBinary)


if __name__ == '__main__':

    try:
        import asyncio
    except ImportError:
        # Trollius >= 0.3 was renamed
        # import trollius as asyncio
        print('import asyncio failed')

    try:
        connection = psycopg2.connect("dbname='test_chat' user='postgres' host='localhost' port='5432' password='Wgv61x^Xt1'")
    except:
        print('Database connection failed. Server will shut down.')
        exit()
    cursor = connection.cursor()
    factory = WebSocketServerFactory(u"ws://localhost:6544")
    factory.protocol = MyServerProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', 6544)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()