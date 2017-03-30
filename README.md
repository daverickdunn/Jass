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

Requirements:
* Python 3.5
* Python packages: Flask, Flask-SocketIO, scikit-learn, musicbrainzngs, numpy, (probably a few more, just run and add them as it throws errors. I'll make it pip installable soon.)

Known Issues:

Besides all the missing features, there are two immediate issues with the current features that will be fixed over the coming days:

* username and password has to be manually set by modifying _database.py_ and adding them to lines 32 and 33.
* recommender will try to find _your_ files in the db, but scanning local directories hasn't been added yet, only solution is to run the offical client under preferred name, add user to jass, add files to db, shutdown official client, rename jass user to same name, relaunch jass and run recommender. Or... just wait a few days till it's fixed ;)
