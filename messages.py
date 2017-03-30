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

import hashlib
import struct
import zlib
from pprint import pprint
from utils import packInt, packLargeInt, packString, packBool, createMessage


# Parent class
class Message(object):
    def __init__(self, messageBytes):
        self.message = messageBytes
        self.cursor = 0
    def unpackInt(self):
        self.cursor += 4
        return struct.unpack("<I", self.message[ self.cursor-4 : self.cursor ])[0]
    def unpackLargeInt(self):
        self.cursor += 8
        return struct.unpack("q", self.message[ self.cursor-8 : self.cursor ])[0]
    def unpackString(self):
        len_str = struct.unpack("<I", self.message[ self.cursor : self.cursor+4 ])[0]
        self.cursor += 4 + len_str

        # TODO: make this better?
        try:
            return struct.unpack("%ds" % len_str, self.message[ self.cursor-len_str : self.cursor ])[0].decode("utf-8")
        except:
            try:
                return struct.unpack("%ds" % len_str, self.message[ self.cursor-len_str : self.cursor ])[0].decode("iso-8859-1")
            except:
                raise

    def unpackBool(self):
        self.cursor += 1
        return struct.unpack("?", self.message[ self.cursor-1 : self.cursor ])[0]
    def unpackIPv4(self):
        self.cursor += 4
        ip4, ip3, ip2, ip1 = struct.unpack("BBBB", self.message[ self.cursor-4 : self.cursor ])
        return str(ip1) +'.'+ str(ip2) +'.'+ str(ip3) +'.'+ str(ip4)
    def unpackMessage(self):
        return {'code' : 9999}


# Server Messages ...
#1
class Login(Message):
    @staticmethod
    def packMessage(options):
        b_msgCode = packInt(1)            # 1 - for Login
        b_ppl_un  = packString(options['user'])  # prepend username with it's length
        b_ppl_pw  = packString(options['pass'])  # prepend password with it's length
        b_ver     = packInt(181)

        # m = md5.new()
        m = hashlib.md5()
        m.update(b_ppl_un + b_ppl_pw)
        md5_unpw  = m.hexdigest()

        b_unpw    = packString(md5_unpw)
        some_num  = packInt(1)
        return createMessage(b_msgCode + b_ppl_un + b_ppl_pw + b_ver + b_unpw + some_num)

    def unpackMessage(self):
        try:
            ls, s, ip4, ip3, ip2, ip1, p = struct.unpack("IBBBBBB", self.message)
            return {'code' : 'S1', 'status' : 'success'}
        except Exception as e:
            return {'code' : 'S1', 'status' : 'error', 'error' : str(e)}

#2
class SetWaitPort(Message):
    @staticmethod
    def packMessage(options):
        msgCode = 2
        return createMessage(packInt(msgCode) + packInt(options['port']))
#3
class GetPeerAddress(Message):
    @staticmethod
    def packMessage(options):
        msgCode = 3
        return createMessage(packInt(msgCode) + packString(options['user']))

    def unpackMessage(self):
        user = self.unpackString()
        ip = self.unpackIPv4()
        port = self.unpackInt()
        return {'code' : 'S3', 'user' : user, 'ip' : ip, 'port' : port}
#5
class AddUser(Message):
    @staticmethod
    def packMessage(options):
        msgCode = 5
        return createMessage(packInt(msgCode) + packString(options['user']))

    def unpackMessage(self):
        status = avgspd = dldnum = files = dirs = country = None
        user    = self.unpackString()
        exists  = self.unpackBool()
        if exists:
            status = self.unpackInt()
            avgspd = self.unpackInt()
            dldnum = self.unpackLargeInt()
            files  = self.unpackInt()
            dirs   = self.unpackInt()
            country= self.unpackString()
        return {
            'code' : 'S5',
            'user' : user,
            'exists' : exists,
            'status' : status,
            'avgspd' : avgspd,
            'dldnum' : dldnum,
            'files'  : files,
            'dirs'   : dirs,
            'country_code': country}

#7
class GetUserStatus(Message):
    @staticmethod
    def packMessage(options):
        return createMessage(packInt(7) + packString(options['name']))
    # def unpackMessage(self):
        # string username
        # int status 0 == Offline, 1 == Away; 2 == Online
        # bool privileged

#13
class SayChatroom(Message):
    @staticmethod
    def packMessage(options):
        return createMessage(packInt(13) + packString(options['room']) + packString(options['message']))
    def unpackMessage(self):
        room = self.unpackString()
        user = self.unpackString()
        mess = self.unpackString()
        return {'code' : 'S13', 'room' : room, 'user' : user, 'message' : mess}


#14
class JoinRoom(Message):
    @staticmethod
    def packMessage(options):
        return createMessage(packInt(14) + packString(options['room']))

    def unpackMessage(self):
        room = self.unpackString()

        users = []
        for i in range(0,self.unpackInt()):
            users.append(self.unpackString())

        statuses = []
        for i in range(0,self.unpackInt()):
            statuses.append(self.unpackInt())

        avg_speeds  = []
        dl_nums     = []
        files       = []
        dirs        = []
        for i in range(0,self.unpackInt()):
            avg_speeds.append(self.unpackInt())
            dl_nums.append(self.unpackLargeInt())
            files.append(self.unpackInt())
            dirs.append(self.unpackInt())

        slots = []
        for i in range(0,self.unpackInt()):
            slots.append(self.unpackInt())

        country_codes = []
        for i in range(0,self.unpackInt()):
            country_codes.append(self.unpackString())

        user_data = []
        for i in range(0,len(users)):
            user_data.append({
                'user'          : users[i],
                'status'        : statuses[i],
                'avg_speed'     : avg_speeds[i],
                'downloads'     : dl_nums[i],
                'files'         : files[i],
                'dirs'          : dirs[i],
                'country_code'  : country_codes[i]
            })

        # NOTE: There's additional data for private rooms, not sure if depreciated
        return {'code' : 'S14', 'room' : room, 'users' : user_data, 'slots' : slots}


#15
class LeaveRoom(Message):
    @staticmethod
    def packMessage(options):
        return createMessage(packInt(15) + packString(options['room']))
    def unpackMessage(self):
        return {'code' : 'S15', 'room' : self.unpackString() }


#18
class ConnectToPeer(Message):
    @staticmethod
    def packMessage(options):
        msgCode = 18
        token = packInt(options['token'])
        user = packString(options['user'])
        msgType = packString(options['type'])
        return createMessage(packInt(msgCode) + token + user + msgType)

    def unpackMessage(self):
        return {
            'code' : 'S18',
            'user' : self.unpackString(),
            'type' : self.unpackString(),
            'ip' : self.unpackIPv4(),
            'port' : self.unpackInt(),
            'token' : self.unpackInt(),
            'privileged' : self.unpackBool()
        }

#26
class FileSearch(Message):
    @staticmethod
    def packMessage(options):
        ticket_id  = packInt(options['ticket'])
        packed_str = packString(options['query'])
        return createMessage(packInt(26) + ticket_id + packed_str)

    def unpackMessage(self):
        pass

#35
class SharedFoldersFiles(Message):
    @staticmethod
    def packMessage(options):
        return createMessage(packInt(35) + packInt(options['dirs']) + packInt(options['files']))

#64
class RoomList(Message):
    @staticmethod
    def packMessage(options):
        return createMessage(packInt(64))
    def unpackMessage(self):
        return {
            'code' : 'S64',
            'std_rooms' : self.getRooms()
            # 'prv_rooms_owned' : self.getRooms(),
            # 'prv_rooms_unowned' : self.getRooms()
            # 'prv_rooms_operated' : self.getRooms() # TODO: Still part of protocol??
        }

    def getRooms(self):
        rooms = []
        users = []
        dicts = []

        num_rooms = self.unpackInt()
        for i in range(0,num_rooms):
            rooms.append(self.unpackString())

        num_rooms = self.unpackInt()
        for i in range(0,num_rooms):
            users.append(self.unpackInt())

        for i in range(0,num_rooms):
            dicts.append({'room_name':rooms[i], 'num_users': users[i]})

        return dicts

#69
class PrivilegedUsers(Message):
    def unpackMessage(self):
        num_users = self.unpackInt()
        user_names = []
        while len(user_names) < num_users:
            user_names.append(self.unpackString())
        return {'code': 'S69', 'names' : user_names}

#1001
class CantConnectToPeer(Message):
    @staticmethod
    def packMessage(options):
        token = packInt(options['token'])
        user = packString(options['user'])
        return createMessage(packInt(1001) + token + user)
    # def unpackMessage(self):
    #     return {'code' : 1001,
    #             'token' : self.unpackInt(),
    #             'user'  : self.unpackString()}
    def unpackMessage(self):
        return {'code' : 'S1001',
                'token' : self.unpackInt()}


servercodes = {
    'S1':Login,
    'S2':SetWaitPort,
    'S3':GetPeerAddress,
    'S5':AddUser,
    'S7':GetUserStatus,
    'S13':SayChatroom,
    'S14':JoinRoom,
    'S15':LeaveRoom,
    # 16:UserJoinedRoom,
    # 17:UserLeftRoom,
    'S18':ConnectToPeer,
    # 22:MessageUser,
    # 23:MessageAcked,
    # 26:FileSearch,
    # 28:SetStatus,
    # 32:ServerPing,
    # 34:SendSpeed,
    'S35':SharedFoldersFiles,
    # 36:GetUserStats,
    # 40:QueuedDownloads,
    # 41:Relogged,
    # 42:UserSearch,
    # 51:AddThingILike,
    # 52:RemoveThingILike,
    # 54:Recommendations,
    # 56:GlobalRecommendations,
    # 60:PlaceInLineResponse,
    # 62:RoomAdded,
    # 63:RoomRemoved,
    'S64':RoomList,
    # 65:ExactFileSearch,
    # 66:AdminMessage,
    # 67:GlobalUserList,
    # 68:TunneledMessage,
    'S69':PrivilegedUsers,
    # 83:Msg83,
    # 84:Msg84,
    # 85:Msg85,
    # 86:ParentInactivityTimeout,
    # 87:SearchInactivityTimeout,
    # 88:MinParentsInCache,
    # 89:Msg89,
    # 90:DistribAliveInterval,
    # 91:AddToPrivileged,
    # 92:CheckPrivileges,
    'S1001':CantConnectToPeer,
    # 71:HaveNoParent,
    # 93:SearchRequest,
    # 102:NetInfo,
    # 103:WishlistSearch,
    # 104:WishlistInterval,
    # 110:SimilarUsers,
    # 111:ItemRecommendations,
    # 112:ItemSimilarUsers,
    # 113:RoomTickerState,
    # 114:RoomTickerAdd,
    # 115:RoomTickerRemove,
    # 116:RoomTickerSet,
    # 117:AddThingIHate,
    # 118:RemoveThingIHate,
    # 120:RoomSearch
}


# Init 0
class PierceFirewall(Message):
    @staticmethod
    def packMessage(options):
        # code = struct.pack("B", 0)
        code = chr(0)
        token = packInt(options['token'])
        return createMessage(code + token)

    def unpackMessage(self):
        return {'code': 'P0', 'token' : self.unpackInt()}

# Init 1
class PeerInit(Message):
    @staticmethod
    def packMessage(options):
        code = struct.pack("B", 1)
        name = packString(options['user'])
        connType = packString(options['type'])
        token = packInt(options['token'])
        msg = code + name + connType + token
        return packInt(len(msg)) + msg

    def unpackMessage(self):
        return {
            'code': 'P1',
            'user' : self.unpackString(),
            'type' : self.unpackString(),
            'token': self.unpackInt()
        }

initcodes={
    0:PierceFirewall,
    1:PeerInit
}

# Peer 4
class GetSharedFileList(Message):
    @staticmethod
    def packMessage(options):
        return createMessage(packInt(4))

    def unpackMessage(self):
        return {'code': 'P4'}



def recurDir(parent, nodes):
    if nodes[0] in parent['dir']:
        return recurDir(parent['dir'][nodes[0]], nodes[1:])
    else:
        parent['dir'][nodes[0]] = {'dir': {}, 'bin': {}}
        return parent['dir'][nodes[0]]

# Peer 5
class SharedFileList(Message):
    @staticmethod
    def packMessage(options):
        return None

    def unpackMessage(self):
        try:
            self.message=zlib.decompress(self.message)
        except:
            raise

        data={'code': 'P5', 'data': {'dir': {}, 'bin': {}}, 'rec_data' : {}}
        num_dirs = self.unpackInt()
        for i in range(0, num_dirs):
            directory = self.unpackString()

            data['rec_data'][directory] = []

            # data['flat_dirs'].append(directory) # for reccomender system

            nodes = directory.split('\\')
            leaf = recurDir(data['data'], nodes)
            num_files = self.unpackInt()

            for j in range(0, num_files):
                self.cursor += 1 # Byte not used ... ?
                file_name = self.unpackString()
                file_size = self.unpackLargeInt()
                file_ext = self.unpackString()
                file_num_attr = self.unpackInt()

                attributes = []
                for k in range(file_num_attr):
                    file_attr_pos = self.unpackInt()
                    file_attr = self.unpackInt()
                    attributes.append({'att' : file_attr_pos, 'val' : file_attr})
                leaf['bin'][file_name] = file_size

                data['rec_data'][directory].append({'title' : file_name, 'attributes': attributes})

        return data


peercodes = {
    'P0':PierceFirewall,
    'P1':PeerInit,
    'P4':GetSharedFileList,
    'P5':SharedFileList,
    # 8:FileSearchRequest,
    # 9:FileSearchResult,
    # 15:UserInfoRequest,
    # 16:UserInfoReply,
    # 36:FolderContentsRequest,
    # 37:FolderContentsResponse,
    # 40:TransferRequest,
    # 41:TransferResponse,
    # 42:PlaceholdUpload,
    # 43:QueueUpload,
    # 44:PlaceInQueue,
    # 46:UploadFailed,
    # 50:QueueFailed,
    # 51:PlaceInQueueRequest
}


# distribclasses = {
    # 0:DistribAlive,
    # 3:DistribSearch
# }
