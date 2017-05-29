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


class Room(object):
    def __init__(self, message):
        self.room  = message['room']
        self.users = message['users']
        self.slots = message['slots']

        self.chat_messages = []

    def addUser(self, message):
        pass

    def removeUser(self, message):
        pass

    def addComment(self, message):
        self.chat_messages.append({'user': message['user'], 'message' : message['message']})

    def roomInfo(self):
        return {
            'room'      : self.room,
            'users'     : self.users,
            'slots'     : self.slots,
            'messages'  : self.chat_messages
        }
