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
        message = json.loads(payload.decode('utf8'))   # message - python string, payload - utf8 encoded json string
        words = message.split(" ")
        # message structure will match one of the following types:
        #   "(User_entered) <username>"
        #   "(Get_groups)"
        #   "(Group_created) <topic>"
        #   "(Get_names) <group_id>"
        #   "(User_connected) <user_id> <group_id>"
        #   "(User_disconnected) <user_id> <group_id>"
        #   "(Msg) <user_id> <group_id> <message>"
        if words[0] == '(User_entered)':
            # check if user already exists, 1 - return id, 0 - create and return id
            try:
                cursor.execute("""SELECT user_id FROM active_users WHERE name='{0}' """.format(words[1]))
            except psycopg2.Error as exc:
                print(exc)
                return
            result = cursor.fetchone()
            if result is None:
                try:
                    cursor.execute("""INSERT INTO active_users (name, created, updated) VALUES ('{0}', now(), now())
                                      RETURNING user_id""".format(words[1]))
                except psycopg2.Error as exc:
                    print(exc)
                    return
                result = cursor.fetchone()
            # print(result)
            self.sendJSONmsg(result[0], isBinary)
        elif words[0] == '(Get_groups)':
            # getting group list
            try:
                cursor.execute("""SELECT group_id, topic FROM groups""")
            except psycopg2.Error as exc:
                print(exc)
                return
            rows = cursor.fetchall()
            for row in rows:
                self.sendJSONmsg(str(row[0]) + ',' + row[1], isBinary)
        elif words[0] == '(Group_created)':
            # created new group
            topic = message.split(") ")[1]
            try:
                cursor.execute("""INSERT INTO groups (topic, created, updated) VALUES ('{0}', now(), now())
                                  RETURNING group_id""".format(topic))
            except psycopg2.Error as exc:
                print(exc)
                return
            except Exception as exc:
                print(exc)
                return
            result = cursor.fetchone()
            group_id = result[0]
            self.sendJSONmsg(str(group_id) + "," + topic, isBinary)
        elif words[0] == '(Get_names)':
            # user requested group members upon entering group
            for i in range(len(clients)):
                if clients[i][3] == words[1]:   # if client is in group
                    self.sendJSONmsg('(user) ' + clients[i][1], isBinary)
        elif words[0] == '(User_connected)':
            # 1)register entering user
            # 2)return user his name and group topic
            # 3)send welcoming messages to everyone in group
            try:
                cursor.execute("""SELECT name FROM active_users WHERE user_id='{0}'""".format(words[1]))
            except psycopg2.Error as exc:
                print(exc)
                return
            except Exception as exc:
                print(exc)
                return
            result = cursor.fetchone()
            username = result[0]
            try:
                cursor.execute("""SELECT topic FROM groups WHERE group_id='{0}'""".format(words[2]))
            except psycopg2.Error as exc:
                print(exc)
                return
            except Exception as exc:
                print(exc)
                return
            result = cursor.fetchone()
            topic = result[0]
            # 1)
            #clients[0].append(self)
            #clients[1].append(username)
            #clients[2].append(words[1])
            #clients[3].append(words[2])
            clients.append([self, username, words[1], words[2]])
            # 2)
            self.sendJSONmsg('(self) ' + username + ' ' + topic, isBinary)
            # 3)
            for i in range(len(clients)):
                if clients[i][3] == words[2]:
                    clients[i][0].sendJSONmsg('(msg) Welcome ' + username + ' !', isBinary)
                    clients[i][0].sendJSONmsg('(user) ' + username, isBinary)
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
            for i in range(len(clients)):
                if clients[i][2] == uid and clients[i][3] == gid:
                    username = clients[i][1]
                    del clients[i]
                    break
            # 2)
            for i in range(len(clients)):
                if clients[i][3] == words[2]:
                    clients[i][0].sendJSONmsg('(remove) ' + username, isBinary)
                    clients[i][0].sendJSONmsg('(msg) Farewell ' + username + ' !', isBinary)
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
                msg += ' '
                i += 1
            # msg = whole message data without ids
            try:
                cursor.execute("""INSERT INTO messages (message, created, updated, user_id, group_id)
                                  VALUES ('{0}', now(), now(), '{1}', '{2}')""".format(msg, int(uid), int(gid)))
            except psycopg2.Error as exc:
                print(exc)
                return
            except Exception as exc:
                print(exc)
                return
            for i in range(len(clients)):
                if clients[i][3] == gid:
                    clients[i][0].sendJSONmsg(msg, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def sendJSONmsg(self, message, isBinary):
        jsonmsg = json.dumps(message)
        self.sendMessage(jsonmsg.encode('utf-8'), isBinary)


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
    connection.autocommit = True
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