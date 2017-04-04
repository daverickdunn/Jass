# Jass - Alpha

This project is currently only recommended for those interested in contributing, or diehard SoulSeek users, or both.

It doesn't currently transfer any files, and is missing a lot of other basic SoulSeek features.

What is does do:

* Chatrooms more or less fully work.
* Browsing other users collections works okay, but as mentioned, you can't download anything yet.
* You can _add_ other users, though user permissions, etc. hasn't been added yet.

Outside of the SoulSeek protocol:

* You can add users browse (i.e. a snapshot of their files/folders) to the local database.
* You can then _index_ users browse data. This searches the MusicBrainz API to identify artists/releases
* Once there's one or more collections indexed, you can run a recommendation algorithm to get a list of recommendations based on the contents of those collections.

HOWTO:

To set initial username/password, or listening port, run database.py with either of the following commands:

* --setlogin <_username_> <_password_>
* --setlistenport <_port_>

To run the application, run _start_server.py_, then navigate to you servers IP and go to port 5000 (e.g. _192.168.1.100:5000_)

For the recommender to work correctly you need to index some of your own files. Currently must be placed in the 'collection' folder in the root of the application (symbolic links haven't been tested but might work). On restart these files will be added to the DB. They'll be indexed along with all other users files when you select "index all collections" from the Recommender View


Requirements:
* Python 3.5
* Python packages:
    flask
    flask-socketio
    mutagen
    musicbrainzngs
    pandas
    sklearn
    scipy
