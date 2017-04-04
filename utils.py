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

import struct
import binascii

# pack
def packInt(uInt32):
    return struct.pack("<I", int(uInt32))

def packLargeInt(sInt64):
    return struct.pack("<Q", int(sInt64))

def packString(string):
    return struct.pack("<I", len(string)) + bytes(string, 'latin-1')

def packBool(boolean):
    return struct.pack("c", boolean.encode('ascii'))

def createMessage(message_string):
    messageHex = binascii.hexlify(message_string)
    return bytearray.fromhex((binascii.hexlify(packInt(len(messageHex)/2)) + messageHex).decode('utf-8'))

# unpack
def unpackInt(byteArray):
    return struct.unpack("<I", byteArray[0:4])[0] # , 4

def unpackLargeInt(byteArray):
    return struct.unpack("<Q", byteArray[0:8])[0] # , 8

def unpackString(byteArray):
    len_str = struct.unpack("I", byteArray[0:4])[0]
    return str(struct.unpack("%ds" % len_str, byteArray[4:])[0]) # , len_str + 4

def unpackBool(byteArray):
    return struct.unpack("c", byteArray[0])[0] # , 4

# convert JSON to UTF-8 Python data structure. i.e. Strings, Lists and Dicts
def _byteify(data, ignore_dicts = False):
    if isinstance(data, str): return data#.encode('utf16') # 'cp1252' 'ISO-8859-1'
    if isinstance(data, list): return [ _byteify(item, ignore_dicts=True) for item in data ]
    if isinstance(data, dict) and not ignore_dicts:
        return dict((_byteify(key, ignore_dicts=True), _byteify(value, ignore_dicts=False)) for key, value in data.items())
    return data
