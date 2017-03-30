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
import threading

import utils
import messages

class ServerConnection(threading.Thread):

    def __init__(self, outgoing):
        self.callback = outgoing
        self.server_host = 'server.slsknet.org'
        self.server_port = 4098
        self.server_sock = socket.socket()
        self.server_sock.connect((self.server_host, self.server_port))
        super(ServerConnection, self).__init__()

    def run(self):
        print('Connnected to SLSK')
        self.buff = bytearray()
        while True:
            data, addr = self.server_sock.recvfrom(1024)
            if data:
                self.buff += data
                if len(self.buff) >= utils.unpackInt(self.buff):
                    len_msg = utils.unpackInt(self.buff)
                    self.processMessage(self.buff[4:len_msg+4])
                    self.buff = self.buff[4+len_msg:]
            else:
                pass

    def send(self, message):
        print('[Server Thread] Sending message to server: ' + str(message['code']))
        self.server_sock.send(messages.servercodes[message['code']].packMessage(message))


    # TODO: rename to unpackMessage
    def processMessage(self, messageBytes):
        msg_code = 'S' + str(utils.unpackInt(messageBytes))
        if msg_code in messages.servercodes:
            message_obj = messages.servercodes[msg_code](messageBytes[4:])
            self.callback(message_obj.unpackMessage())
        else:
            print("[Server Thread] Discarding Unknown Message: " + str(msg_code))
        return
