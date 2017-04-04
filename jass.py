'''
Jass is an open source client and recommender system for the SoulSeek network.
Copyright (C) 2017 Richard Dunn

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from __future__ import print_function
import socket
import os
import threading
import json
import time
import struct
import utils
import messages
from pprint import pprint

import file_reader
from database import Database
from room import Room
from indexer import Indexer
from content_filter import ContentFilter
from peer_connection import PeerConnection
from server_connection import ServerConnection


class Jass(threading.Thread):

    def __init__(self, outgoing_callback):

        db = Database()
        config = db.getConfig()
        db.close()

        # TODO: move to serverConnection
        self.username = config['username']
        self.password = config['password']
        # TODO: change to list of dirs
        self.shares_path = 'collection'

        self.listen_port = config['listen_port']

        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.listen_sock.bind(('',self.listen_port))
        self.listen_sock.listen(1)


        self.client_gui_callback = outgoing_callback

        self.joinedRooms = []
        self.userBrowseData = {}
        self.usersToBeAddedToDB = {}

        self.peerConnections = []
        self.peerConnsQueue = []

        self.lock = threading.Lock()
        self.lockCount = 0

        super(Jass, self).__init__()

        self.addOwnUserData()

        self.startJass()


    def startJass(self):
        self.server_conn = ServerConnection(self.serverRouter)
        self.server_conn.daemon = True
        self.server_conn.start()

        self.peer_accept = threading.Thread(target=self.peerAccept)
        self.peer_accept.daemon = True
        self.peer_accept.start()
        # login
        self.server_conn.send({'code' : 'S1', "user" : self.username, "pass" : self.password})
        # set wait port
        self.server_conn.send({'code' : 'S2', "port" : self.listen_port})
        # set num shared files & folders
        self.server_conn.send({'code' : 'S35', 'dirs' : 43, 'files' : 100}) # TODO: Send actual numbers



    # Messages are forwarded here from the serverConnection
    def serverRouter(self, message):
        print('[Jass Thread] Incoming Server Message: ' + str(message['code']))
        if message['code'] == 'S3':
            self.outgoingPeerConns(message)
        elif message['code'] == 'S5':
            if message['exists']:
                pprint(message)
                db = Database()
                db.addUser((message['user'], message['country_code']))
                db.close()

        elif message['code'] == 'S13':
            self.findRoom(message).addComment(message)
        elif message['code'] == 'S14':
            new_room = Room(message, self.client_gui_callback)
            self.joinedRooms.append(new_room)
        elif message['code'] == 'S15':
            self.joinedRooms.remove(self.findRoom(message))
        elif message['code'] == 'S18':
            # self.peerCreate(message)
            self.incomingPeerConns(message)
            return

        self.client_gui_callback(message) # forward the message to the Flask Server


    # Messages are forwarded here from peerConnections
    def peerRouter(self, message):
        # self.lock.acquire()
        # self.lockCount += 1
        # print('[Jass Thread] Lock Acquired: ', self.lockCount)
        print('[Jass Thread] Incoming Peer Message: ' + str(message['code']))


        if message['code'] == 'P4':

            for p in self.peerConnections:
                print(p.user)

            pprint(message, depth=1)
            shares = file_reader.buildFileFolder(self.shares_path)
            peer = next((x for x in self.peerConnections if x.user == message['user']), None)
            peer.send({'code': 'P5', 'shares': shares})
            return

        # browse files response
        if message['code'] == 'P5':
            # cache data
            self.userBrowseData[message['user']] = message

            # if request pending to add to DB, reissue request
            if message['user'] in self.usersToBeAddedToDB:
                del self.usersToBeAddedToDB[message['user']]
                self.clientRouter({"code": 'J2', "user" : message['user']})
                return # Don't re-add to browse

        self.client_gui_callback(message)
        # print('[Jass Thread] Lock Released: ', self.lockCount)
        # self.lock.release()


    # callback for Flask thread
    def clientRouter(self, message):
        # self.lock.acquire()
        # self.lockCount += 1
        # print('[Jass Thread] Lock Acquired: ', self.lockCount)
        print("[Jass Thread] Incoming Flask Message:", str(message['code']))

        if message['code'] in messages.servercodes:
            self.server_conn.send(message)

        elif message['code'] in messages.peercodes:
            peer = next((x for x in self.peerConnections if x.user == message['user']), None)
            # if connection already in progess use it
            if peer and peer.is_alive():
                peer.send(message)
            # otherwise create a new connection and send the message
            else:
                if peer:
                    # cleanup any old connection objects to same user
                    self.peerConnections.remove(peer)
                new_peer = PeerConnection(parent=self, out=self.peerRouter, user=message['user'], mType='P')
                new_peer.daemon = True
                new_peer.send(message)
                self.peerConnections.append(new_peer)
                self.server_conn.send({'code' : 'S3', 'user' : message['user']})

        # NOTE: This is a custom Jass code, not a SLSK code, it is for resending
        # info when a user reconnects to the session
        elif message['code'] == 'J1':

            # ask server for an update on the rooms list
            # the response will be automatically forwarded to the GUI
            self.server_conn.send({'code' : 'S64'})

            # get users from database
            db = Database()
            users = db.getAllUsers()
            db.close()

            # TODO: not filter self.username? probably should remove once 'browse' uploading is available
            if users:
                users = [{'user':u[0], 'country':u[1], 'country_code':u[2]} for u in users if u[0] != self.username]

            # send current session data to the GUI.
            # rooms, chats, open browse views, etc.
            data = {'code' : 'J1',
                    'rooms' : [room.roomInfo() for room in self.joinedRooms],
                    'browse': self.userBrowseData,
                    'users' : users}
            self.client_gui_callback(data)

        # adds user data to database
        elif message['code'] == 'J2':
            # if users browsedata already cached
            if message['user'] in self.userBrowseData:
                db = Database()
                db.start()
                db.addUserData(message['user'], self.userBrowseData[message['user']]['rec_data'])
            # else we ask peer for browsedata and set flag to add to DB on receipt
            else:
                self.usersToBeAddedToDB[message['user']] = None
                self.clientRouter({"code": 'P4', "user" : message['user']})


        # removes browse data for user
        elif message['code'] == 'J3':
            if message['user'] in self.userBrowseData:
                del self.userBrowseData[message['user']]

        # run the MB Indexer
        elif message['code'] == 'J4':
            db = Database()
            users = [x[0] for x in db.getAllUsers()]
            db.close()

            for user in users:
                print('[Jass Thread] Starting Indexer for user:', user)
                idx = Indexer(user)
                idx.daemon = True
                idx.start()
                idx.join()

        # run the recommender
        elif message['code'] == 'J5':
            print('[Jass Thread] Starting Recommender')

            anon = lambda x: self.client_gui_callback({'code' : 'J5', 'recommendations': x})
            cf = ContentFilter(self.username, 10, anon)
            cf.daemon = True
            cf.start()





        # print('[Jass Thread] Lock Released: ', self.lockCount)
        # self.lock.release()


    def peerAccept(self):
        while True:
            conn, address = self.listen_sock.accept()
            print('[Jass Thread] New peer connection from:', address)

            # 'Cut' message from buffer
            buff = conn.recv(4)
            lenMsg = utils.unpackInt(buff)
            data = conn.recv(lenMsg)

            # read message
            initCode = struct.unpack("B", data[0:1])[0]
            message = messages.initcodes[initCode](data[1:]).unpackMessage()

            # PierceFirewall
            if initCode == 0:
                peer = next((x for x in self.peerConnections if x.token == message['token']), None)
                if peer and peer.conn == None:
                    peer.conn = conn
                    init = {'user': self.username, 'type': peer.type, 'token': peer.token}
                    peer.conn.send(messages.PeerInit.packMessage(init))
                    if not peer.is_alive():
                        print('Starting thread from peerAccept')
                        peer = peer.clone()
                        peer.start()
                else:
                    print('[Jass Thread] PierceFirewall for unknown connection!')

            # PeerInit
            elif initCode == 1:
                #TODO: try accept connection
                self.peerConnsQueue.append({'user' : message['user'], 'conn' : conn})
            else:
                print('[Jass Thread] Incoming initMessage (Unknown Message): ' + str(initCode))

    def outgoingPeerConns(self, message):
        peer = next((x for x in self.peerConnections if x.user == message['user']), None)
        # Code 3 from server, triggered by us trying to connect to a peer
        if peer and peer.conn == None:
            peer.host = message['ip']
            peer.port = message['port']
            print('[Jass Thread] Creating Connection:', peer.user, peer.host, peer.port, peer.type, peer.token)
            try:
                conn = socket.socket()
                conn.settimeout(10)
                conn.connect((peer.host, peer.port))

                init = {'user': self.username, 'type': peer.type, 'token': peer.token}
                conn.send(messages.PeerInit.packMessage(init))

                print('[Jass Thread] Starting thread from outgoingPeerConns')
                peer.conn = conn
                peer.start()

            except Exception as e:
                print('[Jass Thread] Exception connecting:', str(e))
                if message['code'] == 'S18':
                    self.server_conn.send({'code': 'S1001', 'user': peer.user, 'token': peer.token})
                elif message['code'] == 'S3':
                    self.server_conn.send({ 'code' : 'S18',
                                            'token': peer.token,
                                            'user' : peer.user,
                                            'type' : peer.type})

    def incomingPeerConns(self, message):
        peer = PeerConnection(
            parent=self,
            host=message['ip'],
            port=message['port'],
            out=self.peerRouter,
            user=message['user'],
            token=message['token'],
            mType=message['type']
        )
        tries = 0
        while tries < 10:
            qConn = next((x for x in self.peerConnsQueue if x['user'] == message['user']), None)
            if qConn:
                peer.conn = qConn['conn']
                self.peerConnections.append(peer)
                peer.start()
                break
            time.sleep(1)
            tries += 1
        else:
            try:
                conn = socket.socket()
                conn.connect((peer.host, peer.port))
                peer.conn = conn
                print('Starting thread from incomingPeerConns')
                peer.start()
                msg = {'token': peer.token}
                conn.send(messages.PierceFirewall.packMessage(msg))
            except:
                self.server_conn.send({'code': 'S1001', 'user': peer.user, 'token': peer.token})

    def findRoom(self, message):
        return next((x for x in self.joinedRooms if x.room == message['room']), None)

    def addOwnUserData(self):
        db = Database()
        db.start()
        pprint(file_reader.buildFileFolder(self.shares_path), depth=1)
        db.addUserData(self.username, file_reader.buildFileFolder(self.shares_path))
        db.close()
