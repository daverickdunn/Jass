#!/usr/bin/python3.5

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
import threading, time, json
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from jass import Jass
from pprint import pprint
from utils import _byteify

# Flask global settings
app = Flask(__name__, template_folder='web/templates', static_url_path='', static_folder='web/static')
app.config['SECRET_KEY'] = 'secret!'

# app.config['DEBUG'] = True
socketio = SocketIO(app, static_url_path='', async_mode='threading', logger=True)

jass_callback = None # give Jass method global scope

# messages forwarded here by Jass
def send_message(message):
    print('[Flask Thread] Message To GUI: ' + str(message['code']))
    socketio.emit('slsk', json.dumps(message), namespace='/test')

# Serve index.html to client browser
@app.route('/')
def index():
    return render_template('index.html')

# accept websocket connection
@socketio.on('connect', namespace='/test')
def connect():
    jass_callback(_byteify({"code": 'J1'}))

# accept json messages from websocket
@socketio.on('message_from_gui', namespace='/test')
def handle_message(message):
    print('[Flask Thread] Message From GUI: ' + str(message['code']))
    global jass_callback
    jass_callback(_byteify(message))

# Flask thread
class flaskThread(threading.Thread):
    def __init__(self, conn_t):
        global jass_callback
        jass_callback = conn_t.messagesFromGUI
        super(flaskThread, self).__init__()

    # override run to launch socketio from within Flask thread
    def run(self):
        socketio.run(app, host='0.0.0.0')


if __name__ == '__main__':

    print('Starting SLSK')
    conn_t = Jass(send_message)
    conn_t.daemon = True

    print('Starting Flask')
    flask_t = flaskThread(conn_t)
    flask_t.daemon = True

    conn_t.start()
    flask_t.start()

    while True:
        time.sleep(1)
