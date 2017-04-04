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
import sqlite3, os, re
from pprint import pprint
import threading
import argparse

class Database(threading.Thread):

    def __init__(self):

        self.db = 'database.sqlite'
        self.countries = 'iso_3166_country_codes.csv'

        if not os.path.isfile( os.path.join( os.getcwd(), self.db)):
            self.conn = sqlite3.connect(self.db)
            self.cursor = self.conn.cursor()
            print('Initalising New Database <<<<<<<<<<')
            self.initalSetup()
        else:
            self.conn = sqlite3.connect(self.db)
            self.cursor = self.conn.cursor()

        super(Database, self).__init__()

    def initalSetup(self):
        try:
            with self.conn:

                # JASS config. TODO: add upload/download folders, bandwidth limits, etc.
                self.conn.execute('CREATE TABLE config (username TEXT PRIMARY KEY, password TEXT, listen_port INTEGER);')

                # SoulSeek users table
                self.conn.execute('CREATE TABLE users (name TEXT PRIMARY KEY, country_id INTEGER, FOREIGN KEY(country_id) REFERENCES countries(rowid));')

                # SoulSeek users folders table
                self.conn.execute('''CREATE TABLE folders (user_id INTEGER NOT NULL, releasegroup_id INTEGER, level3 TEXT, level2 TEXT, level1 TEXT,
                PRIMARY KEY (user_id, level3, level2, level1) ON CONFLICT ABORT, FOREIGN KEY(user_id) REFERENCES users(rowid) ON DELETE CASCADE,
                FOREIGN KEY(releasegroup_id) REFERENCES releasegroups(rowid));''')

                # SoulSeek files table
                self.conn.execute('''CREATE TABLE files (folder_id INTEGER, title TEXT, length INTEGER,
                FOREIGN KEY(folder_id) REFERENCES folders(rowid));''')

                # MusicBrainz artists table
                # gender is: 0: female, 1: male, null: unknown/non-applicable
                self.conn.execute('''CREATE TABLE artists (mbid TEXT PRIMARY KEY, artist_name TEXT, gender INTEGER, country_id INTEGER,
                FOREIGN KEY(country_id) REFERENCES countries(rowid));''')

                # Countries table
                self.conn.execute('CREATE TABLE countries (country TEXT, code TEXT, PRIMARY KEY (country, code) ON CONFLICT ABORT);')

                # MusicBrainz release-group table
                self.conn.execute('CREATE TABLE releasegroups (mbid TEXT PRIMARY KEY, title TEXT, year TEXT, count INTEGER, type_id INTEGER,'+
                'FOREIGN KEY(type_id) REFERENCES types(rowid));')

                # MusicBrainz release-group types. e.g. 'Album', 'Single', etc.
                self.conn.execute('CREATE TABLE types (type TEXT PRIMARY KEY);')

                # MusicBrainz tags
                self.conn.execute('CREATE TABLE tags (tag TEXT PRIMARY KEY);')

                # ~~~~~~~~~~~~~~~~~~~~~~~~~~

                # user to artist relation
                self.conn.execute('''CREATE TABLE user_artist_relation (user_id INTEGER, artist_id INTEGER,
                PRIMARY KEY (user_id, artist_id) ON CONFLICT IGNORE, FOREIGN KEY(user_id) REFERENCES users(rowid), FOREIGN KEY(artist_id) REFERENCES artists(rowid));''')

                # user to releasegroup relation
                self.conn.execute('''CREATE TABLE user_releasegroup_relation (user_id INTEGER, releasegroup_id INTEGER,
                PRIMARY KEY (user_id, releasegroup_id) ON CONFLICT IGNORE, FOREIGN KEY(user_id) REFERENCES users(rowid), FOREIGN KEY(releasegroup_id) REFERENCES releasegroups(rowid));''')

                # ~~~~~~~~~~~~~~~~~~~~~~~~~~

                # artist to releasegroup relation
                self.conn.execute('''CREATE TABLE artist_releasegroup_relation (artist_id INTEGER, releasegroup_id INTEGER,
                PRIMARY KEY (artist_id, releasegroup_id) ON CONFLICT IGNORE, FOREIGN KEY(artist_id) REFERENCES artists(rowid), FOREIGN KEY(releasegroup_id) REFERENCES releasegroups(rowid));''')

                # artist to tag relation
                self.conn.execute('''CREATE TABLE artist_tag_relation (artist_id INTEGER, tag_id INTEGER, count INTEGER,
                PRIMARY KEY (artist_id, tag_id) ON CONFLICT IGNORE, FOREIGN KEY(artist_id) REFERENCES artists(rowid), FOREIGN KEY(tag_id) REFERENCES tags(rowid));''')

                # ~~~~~~~~~~~~~~~~~~~~~~~~~~

                # release-group to tag relation
                self.conn.execute('''CREATE TABLE releasegroup_tag_relation (releasegroup_id INTEGER, tag_id INTEGER, count INTEGER,
                PRIMARY KEY (releasegroup_id, tag_id) ON CONFLICT IGNORE, FOREIGN KEY(releasegroup_id) REFERENCES releasegroups(rowid), FOREIGN KEY(tag_id) REFERENCES tags(rowid));''')

                # ~~~~~~~~~~~~~~~~~~~~~~~~~~
                # add defaults:
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~
                with open(self.countries, 'r') as f:
                    read_data = f.read().splitlines()

                countrys_codes = [(x[0].strip(), x[1].strip() ) for x in (x.rsplit(',', 1) for x in read_data)]

                self.conn.executemany('INSERT INTO countries (country, code) VALUES (?, ?);', countrys_codes)

                self.conn.execute('INSERT INTO config (username, password, listen_port) VALUES (?, ?, ?);', ('', '', 2444,))
                self.addUser(('', 'XW'))


        except:
            try:
                os.remove(self.db)
                raise
            except:
                raise

    def close(self):
        self.conn.close()


    ''' Update or Insert Methods '''

    def setFolderAsUnknown(self, folder_id):
        self.cursor.execute('UPDATE folders SET releasegroup_id=? WHERE rowid=?', ('unknown', folder_id))
        self.conn.commit()


    def addUser(self, user):
        try:
            country_id = self.cursor.execute('SELECT rowid FROM countries WHERE code=?;', (user[1],) ).fetchone()[0]
            return self.cursor.execute('INSERT INTO users (name, country_id) VALUES (?, ?)', (user[0], country_id)).lastrowid
        except Exception as e:
            print(str(e))
        finally:
            self.conn.commit()

    def setLogin(self, username, password):
        try:
            self.conn.execute('UPDATE config set username=?, password=? WHERE rowid=?;', (username, password, 1))
            self.conn.execute('UPDATE users set name=? WHERE rowid=?;', (username, 1,))
        except Exception as e:
            print(str(e))
        finally:
            self.conn.commit()

    def setListenPort(self, port):
        try:
            self.conn.execute('UPDATE config set listen_port=? WHERE rowid=?;', (port, 1))
        except Exception as e:
            print(str(e))
        finally:
            self.conn.commit()



    def addUserData(self, user, data):
        # cleans, validates, and inserts users browsed data to database
        # TODO: quite slow implementation, can be updated to make inserts much more efficient

        formats = set(['3gp', 'aa', 'aac', 'aax', 'act', 'aiff', 'amr',
        'ape', 'au', 'awb', 'dct', 'dss', 'dvf', 'flac', 'gsm', 'iklax',
        'ivs', 'm4a', 'm4b', 'm4p', 'mmf', 'mp3', 'mpc', 'msv', 'ogg',
        'oga', 'opus', 'ra', 'rm', 'raw', 'sln', 'tta', 'vox', 'wav',
        'wma', 'wv', 'webm'])

        cleaned = {}
        for path, files in data.items():
            cleaned[path] = []
            for item in files:
                temp = item['title'].rsplit('.', 1)
                # check if file is an audio format
                if len(temp) > 1 and temp[1] in formats:
                    # remove junk characters in title
                    for exp in [r'^[0-9]*|-|_|\.|\(|\)|\[|\]|\{|\}', ' {2,}']:
                        temp[0] = re.sub(exp, " ", temp[0]).strip()

                    title = temp[0]
                    if temp[0] == '':
                        title = None

                    cleaned[path].append({'title': title, 'attributes': item['attributes']})
            # remove empty folders
            if len(cleaned[path]) == 0:
                del cleaned[path]

        try:
            user_id = self.cursor.execute("SELECT rowid FROM users WHERE name=(?)", (user,)).fetchone()[0]
        except Exception as e:
            #TODO: auto add user, requires passing (name, country) instead of just name
            print(e)
            print('Must add user before adding data')
            return

        print('[Database] Adding', user + '\'s browse data.')

        files_to_add = []
        for path, files in cleaned.items():
            # dir_list = path.split('\\')

            if '\\' in path:
                dir_list = path.split('\\')
            else:
                dir_list = path.split('/')

            if len(dir_list) > 0: level1 = dir_list[-1]
            else: level1 = None
            if len(dir_list) > 1: level2 = dir_list[-2]
            else: level2 = None
            if len(dir_list) > 2: level3 = dir_list[-3]
            else: level3 = None

            temp_files = []
            for fi in files:
                if 1 in fi['attributes']:
                    temp_attr = fi['attributes'][1]
                else:
                    temp_attr = None

                temp_files.append((fi['title'], temp_attr))

            if len(temp_files) > 0:
                pprint((user_id, level3, level2, level1))
                self.cursor.execute('INSERT INTO folders (user_id, level3, level2, level1) VALUES (?, ?, ?, ?);', (user_id, level3, level2, level1))
                fo_id = self.cursor.lastrowid
                files_to_add += [(fo_id, f[0], f[1]) for f in temp_files]

        self.cursor.executemany('INSERT INTO files (folder_id, title, length) VALUES (?, ?, ?);', files_to_add)
        self.conn.commit()
        print('[Database] Done.')


    def _addMusicBrainzItem(self, user_id, item):

        pprint(item)

        # >>>>> insert type
        type_id = self.cursor.execute('SELECT rowid FROM types WHERE type=?;', (item['type'],) ).fetchone()
        if not type_id:
            self.cursor.execute('INSERT INTO types (type) VALUES (?);', (item['type'],) )
            type_id = self.cursor.lastrowid
        else:
            type_id = type_id[0]


        # >>>>> insert release-group
        release_id = self.cursor.execute('SELECT rowid FROM releasegroups WHERE mbid=?;', (item['release'][0],) ).fetchone()
        if not release_id:
            self.cursor.execute('INSERT INTO releasegroups VALUES (?, ?, ?, ?, ?);', ( item['release'] + (type_id,) ))
            release_id = self.cursor.lastrowid
        else:
            release_id = release_id[0]
            print('[Database] Release-group already exists in the database')


        # >>>>> insert release-group tags
        tag_ids = []
        for tag in item['tags']:
            tag_id = self.cursor.execute("SELECT rowid FROM tags WHERE tag=(?)", (tag[0],)).fetchone()
            if tag_id:
                tag_ids.append((tag_id[0], tag[1]))
            else:
                self.cursor.execute('INSERT INTO tags (tag) VALUES (?);', (tag[0],) )
                tag_ids.append((self.cursor.lastrowid, tag[1]))


        # >>>>> associcate tags with release-group
        for tag_id in tag_ids:
            self.cursor.execute('INSERT INTO releasegroup_tag_relation VALUES (?, ?, ?);', ((release_id,) + tag_id))


        # >>>>> associate user with this release-group
        self.cursor.execute('INSERT INTO user_releasegroup_relation VALUES (?, ?);', (user_id, release_id))


        # >>>>> insert artists
        artist_ids = []
        for art in item['artists']:

            art_mbid = art[0]
            art_name = art[1]
            art_country_code = art[2]
            art_tags = art[3]

            # if there's a country associated with artist x, find its rowid
            if art[2]:
                country_id = self.cursor.execute('SELECT rowid FROM countries WHERE code=?;', (art_country_code,) ).fetchone()[0]
            else:
                country_id = None

            # check if the artist already exists, otherwise add new artist.
            art_id = self.cursor.execute('SELECT rowid FROM artists WHERE mbid=?;', (art_mbid,) ).fetchone()
            if not art_id:
                self.cursor.execute('INSERT INTO artists (mbid, artist_name, country_id) VALUES (?, ?, ?);', (art_mbid, art_name, country_id) )
                art_id = self.cursor.lastrowid
            else:
                art_id = art_id[0]

            # store artist id's for later inserts
            artist_ids.append(art_id)

            # >>>>> insert artist tags
            art_tag_ids = []
            for tag in art_tags:
                tag_id = self.cursor.execute("SELECT rowid FROM tags WHERE tag=(?)", (tag[0],)).fetchone()
                if tag_id:
                    art_tag_ids.append((tag_id[0], tag[1]))
                else:
                    self.cursor.execute('INSERT INTO tags (tag) VALUES (?);', (tag[0],) )
                    art_tag_ids.append((self.cursor.lastrowid, tag[1]))

            for tag_id in art_tag_ids:
                self.cursor.execute('INSERT INTO artist_tag_relation VALUES (?, ?, ?);', ((art_id,) + tag_id))


        # >>>>> associate all artists with user and release group
        for artist_id in artist_ids:
            # user-artist-relation
            self.cursor.execute('INSERT INTO user_artist_relation VALUES (?, ?);', (user_id, artist_id))
            self.cursor.execute('INSERT INTO artist_releasegroup_relation VALUES (?, ?);', (artist_id, release_id))


        # >>>>> finally, update folder entry so future searches can skip, retry, etc.
        self.cursor.execute('UPDATE folders SET releasegroup_id=? WHERE rowid=?', (release_id, item['folder_id']))


    def bulkAddMusicBrainzData(self, user, data):
        user_id = self.cursor.execute("SELECT rowid FROM users WHERE name=(?)", (user,)).fetchone()[0]
        for item in data:
            self._addMusicBrainzItem(user_id, item)
        self.conn.commit()

    def addMusicBrainzItem(self, user, item):
        user_id = self.cursor.execute("SELECT rowid FROM users WHERE name=(?)", (user,)).fetchone()[0]
        self._addMusicBrainzItem(user_id, item)
        self.conn.commit()

    '''Get Methods'''

    def getAllUsers(self):
        return self.cursor.execute("SELECT users.name, countries.country, countries.code FROM users JOIN countries ON countries.rowid=users.country_id").fetchall()

    def getFoldersByUser(self, user):
        return self.cursor.execute("SELECT folders.rowid, folders.* FROM folders JOIN users ON folders.user_id=users.rowid WHERE name=(?)", (user,)).fetchall()

    def getFilesByFolderIDs(self, folder_ids):
        files = []
        # iterate over folders id's 100 at a time (SQLite has some query length limit)
        for i in range(0, len(folder_ids), 100):
            files_sql = "SELECT files.rowid, files.* FROM files WHERE folder_id in ({seq})".format(seq=','.join('?'*len(folder_ids[i:i+100])))
            files += self.cursor.execute(files_sql, tuple(folder_ids[i:i+100])).fetchall()
        return files

    def getUserBrowseData(self, user):
        folders = self.getFoldersByUser(user)
        files = self.getFilesByFolderIDs([x[0] for x in folders])
        data = {}
        for x in folders:
            data[x[0]] = [tuple(x[1:])]
        for x in files:
            data[x[1]].append(tuple(x[2:]))
        return data


    def getArtistByID(self, art_id):
        return self.cursor.execute("SELECT artist_name FROM artists WHERE rowid=" + str(art_id)).fetchone()[0]

    def getArtistsTags(self):
        tags = self.cursor.execute("SELECT artist_tag_relation.artist_id, tags.tag FROM artist_tag_relation JOIN tags on artist_tag_relation.tag_id = tags.rowid").fetchall()
        tags2 = {}
        for key, val in tags:
            if key in tags2:
                tags2[key] += ' ' + val
            else:
                tags2[key] = val
        return tags2

    def getConfig(self):
        config_tuple = self.cursor.execute('SELECT * FROM config;').fetchone()
        return {"username": config_tuple[0], "password": config_tuple[1], "listen_port": config_tuple[2]}

    def getReleaseIDsByUser(self, user):
        return [x[0] for x in self.cursor.execute('''
            SELECT releasegroup_id
            FROM user_releasegroup_relation
            JOIN users ON user_releasegroup_relation.user_id=users.rowid
            WHERE users.name=?;''', (user,)).fetchall()]

    def getArtistIDsByUser(self, user):
        return [x[0] for x in self.cursor.execute('''
            SELECT user_artist_relation.artist_id
            FROM user_artist_relation
            JOIN users ON user_artist_relation.user_id=users.rowid
            WHERE users.name=?;''', (user,) ).fetchall()]

    def getTagIDsByReleaseID(self, release_id):
        return [x[0] for x in self.cursor.execute('''
            SELECT tag_id
            FROM releasegroup_tag_relation
            WHERE releasegroup_id=?;''', (release_id,)).fetchall()]

    def getTagIDsByArtistID(self, artist_id):
        return [x[0] for x in self.cursor.execute('''
            SELECT tag_id
            FROM artist_tag_relation
            WHERE artist_id=?;''', (artist_id,)).fetchall()]

    def getUserIDsByReleaseIDs(self, release_ids):
        user_ids = []
        for release_id in release_ids:
            user_ids += [x[0] for x in self.cursor.execute('''
                SELECT user_id
                FROM user_releasegroup_relation
                WHERE releasegroup_id=?;''', (release_id,)).fetchall()]
        return user_ids


    def getUserIDsByArtistIDs(self, artist_ids):
        user_ids = []
        for artist_id in artist_ids:
            user_ids += [x[0] for x in self.cursor.execute('''
                SELECT user_id
                FROM user_artist_relation
                WHERE artist_id=?;''', (artist_id,)).fetchall()]
        return user_ids


    def getReleaseIDsByTagIDs(self, tag_ids):
        release_ids = []
        for tag_id in tag_ids:
            release_ids += [x[0] for x in self.cursor.execute('''
                SELECT releasegroup_id
                FROM releasegroup_tag_relation
                WHERE tag_id=?;''', (str(tag_id),)).fetchall()]
        return release_ids


    def getArtistIDsByTagIDs(self, tag_ids):
        artist_ids = []
        for tag_id in tag_ids:
            artist_ids += [x[0] for x in self.cursor.execute('''
                SELECT artist_id
                FROM artist_tag_relation
                WHERE tag_id=?;''', (str(tag_id),)).fetchall()]
        return artist_ids

    ''' Deletion Methods '''

    def removeUser(self, user):
        print('Removing user:', user)
        try:
            with self.conn:

                '''
                TO BE DELETED:
                user
                folders
                    files
                user_releasegroup_relation
                    releasegroups with no other user
                        tags with no other releasegroup
                user_artist_relation
                    artists with no other user
                        tags with no other artist
                '''

                ''' get all IDs associated with this user '''
                user_id     = self.conn.execute("SELECT rowid FROM users WHERE name=(?)", (user,)).fetchone()[0]
                folder_ids  = [x[0] for x in self.getFoldersByUser(user)]
                file_ids    = [x[0] for x in self.getFilesByFolderIDs(folder_ids)]

                release_ids = self.getReleaseIDsByUser(user)
                artist_ids = self.getArtistIDsByUser(user)

                release_tag_ids = {}
                for release_id in release_ids:
                    release_tag_ids[release_id] = self.getTagIDsByReleaseID(release_id)

                artist_tag_ids = {}
                for artist_id in artist_ids:
                    artist_tag_ids[artist_id] = self.getTagIDsByArtistID(artist_id)

                ''' find IDs that are referenced elsewhere '''
                release_user_ids = self.getUserIDsByReleaseIDs(release_ids)
                artist_user_ids = self.getUserIDsByArtistIDs(artist_ids)

                release_tag_release_ids = self.getReleaseIDsByTagIDs(release_tag_ids)
                artist_tag_artist_ids = self.getArtistIDsByTagIDs(artist_tag_ids)

                ''' filter IDs that are referenced elsewhere '''




                ''' remove records from database '''




                # print(user_id)
                # print(folder_ids)
                # print(file_ids)
                pprint(release_tag_ids)
                pprint(artist_tag_ids)
                # print(release_tag_release_ids)
                # print(artist_tag_artist_ids)

                # self.conn.execute('PRAGMA foreign_keys = ON;')
                # self.conn.execute('DELETE FROM users WHERE name=?;', (user,) )
                self.conn.commit()
        except Exception as e:

            raise
            print(e)
            print('Error deleting user:', user)




if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--setlogin", nargs=2, metavar=('<username>', '<password>'), help="update the username and password")
    parser.add_argument("--setlistenport", type=int, help="set a listening port number in the range 0-65535 (restart required before change takes affect)")
    args = parser.parse_args()

    if args.setlogin:
        db = Database()
        db.setLogin(args.setlogin[0], args.setlogin[1])
        db.close()

    elif args.setlistenport:
        db = Database()
        db.setListenPort(args.setlistenport)
        db.close()

    # db.removeUser('britpop trump')
