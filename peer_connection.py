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
import struct
import threading
import socket
import time
from pprint import pprint

import utils
import messages

class PeerConnection(threading.Thread):

    tokenCount = 0

    def __init__(self, parent=None, host=None, port=None, conn=None, out=None, user=None, token=None, mType=None):

        self.parent = parent
        self.host = host
        self.port = port
        self.conn = conn
        self.out  = out
        self.user = user
        self.type = mType

        self.messageQueue = []
        self.initPhase = True

        if token == None:
            PeerConnection.tokenCount += 1
            self.token = PeerConnection.tokenCount
        else:
            self.token = token

        print('[Peer Thread ' + str(self.token) + '] New peerConnection for user: ' + self.user)

        super(PeerConnection, self).__init__()

    def clone(self):
        pc = PeerConnection(self.parent,self.host,self.port,self.conn,self.out,self.user,self.token,self.type)
        pc.messageQueue = self.messageQueue
        return pc

    def send(self, message):
        if self.initPhase:
            print('[Peer Thread ' + str(self.token) + '] Queueing message to peer: ' + str(message['code']))
            self.messageQueue.append(message)
        else:
            print('[Peer Thread ' + str(self.token) + '] Sending message to peer: ' + str(message['code']))
            pprint(message)
            self.conn.send(messages.peercodes[message['code']].packMessage(message))


    def sendAll(self):
        self.initPhase = False
        while len(self.messageQueue) > 0:
            self.send(self.messageQueue.pop())


    def run(self):
        self.conn.setblocking(0)
        buff = bytearray()
        while True:
            try:
                print('[Peer Thread ' + str(self.token) + '] Waiting for data')
                data = self.conn.recv(1024)
                if data:
                    print('[Peer Thread ' + str(self.token) + '] Received data')
                    buff += data
                    while len(buff) > 4 and len(buff) >= utils.unpackInt(buff):
                        len_msg = utils.unpackInt(buff)
                        self.peerMessages(buff[4:len_msg+4])
                        buff = buff[4+len_msg:]
                else:
                    print('[Peer Thread ' + str(self.token) + '] Connection closed!')
                    self.conn = None
                    break
            except IOError as e:
                if e.errno == 11:
                    # print '[Peer Thread ' + str(self.token) + '] Error: ' + str(e)
                    self.sendAll()
                    time.sleep(1)
                    continue
            except Exception as e:
                print('[Peer Thread ' + str(self.token) + '] Other exception:', str(e))
                raise
        return

    # TODO: rename to unpack message
    def peerMessages(self, messageBytes):
        msg_code = 'P' + str(utils.unpackInt(messageBytes))
        if msg_code in messages.peercodes:
            print('[Peer Thread ' + str(self.token) + '] Incoming peerMessage: ' + str(msg_code))
            message_obj = messages.peercodes[msg_code](messageBytes[4:]).unpackMessage()
            message_obj['user'] = self.user
            message_obj['token'] = self.token
            self.out(message_obj)
        else:
            print('[Peer Thread ' + str(self.token) + '] Incoming peerMessage (Unknown Message): ' + str(msg_code))
        return
