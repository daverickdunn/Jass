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
from database import Database
from pprint import pprint
import threading, musicbrainzngs, re

class Indexer(threading.Thread):

    def __init__(self, user):
        # musicbrainzngs.set_rate_limit(limit_or_interval=0.5)
        musicbrainzngs.set_useragent("Jass Alpha", "0.1")
        # musicbrainzngs.set_useragent("python-musicbrainz", "0.7.3")
        self.mb_results = {}
        self.mb_unknown = []
        self.user = user
        db = Database()
        self.data = db.getUserBrowseData(user)
        db.close()
        super(Indexer, self).__init__()

    def run(self):
        self.runMusicBrainzSearch(self.user, self.data)

    def runMusicBrainzSearch(self, user, data):

        results = []
        match_count = 0
        unknown = []

        for fold_id, data_tups in data.items():

            fold = data_tups[0]
            files = data_tups[1:]

            # already indexed
            if fold[1]:
                continue

            if len(files) == 0:
                print('[Indexer] WARNING Folder without files found')
                continue

            # search 1st parent folder as 'release-group'
            print('[Indexer] Searching for release: ' + fold[-1])
            release_groups = self.search_release_groups(fold[-1])

            # select first two tracks to try match with release-group
            file_1 = files[0][0]
            file_2 = None
            if len(files) > 1:
                file_2 = files[1][0]

            match_rg = None

            if file_1:
                print('[Indexer] Searching for recording: ' + file_1)
                recordings = musicbrainzngs.search_recordings(recording=file_1)
                match_rg = self.match_group_recording_ids(release_groups, recordings)

            if not match_rg and file_2:
                print('[Indexer] No match, searching second recording: ' + file_2)
                recordings = musicbrainzngs.search_recordings(recording=file_2)
                match_rg = self.match_group_recording_ids(release_groups, recordings)

            if match_rg:
                artists_raw = list(filter(lambda x: type(x) is not str, match_rg['artist-credit'])) # remove multiple artists "join" terms
                artists = []
                for artist in artists_raw:
                    print('[Indexer] Searching artist info:', artist['artist']['name'])

                    artist_data = musicbrainzngs.get_artist_by_id(artist['artist']['id'], includes=['tags'])

                    art_tags = []
                    if 'tag-list' in artist_data['artist']:
                        for tag in artist_data['artist']['tag-list']:
                            art_tags.append((tag['name'], tag['count']))

                    country = None
                    if 'country' in artist_data['artist']:
                        country = artist_data['artist']['country']

                    artists.append((artist['artist']['id'], artist['artist']['name'], country, art_tags))

                rg_tags = []
                if 'tag-list' in match_rg:
                    for tag in match_rg['tag-list']:
                        rg_tags.append((tag['name'], tag['count']))


                year_str = musicbrainzngs.get_release_group_by_id(match_rg['id'])['release-group']['first-release-date']
                year_temp = re.search(r'(19|20|21)([0-9]{2})', year_str)
                if year_temp:
                    year = year_temp.group(0)
                else:
                    year = None

                # only sending single values or tuples, to minimise further processing in DB module
                result = {
                    'artists' : artists,
                    'release': tuple((match_rg['id'], match_rg['title'], year, match_rg['release-count'])),
                    'type': match_rg['primary-type'] if 'primary-type' in match_rg else None,
                    'tags': rg_tags,
                    'folder_id' : fold_id
                }

                results.append(result)

                print('[Indexer] Saving to database')
                print('\n===========================\n')

                db = Database()
                db.start()
                db.addMusicBrainzItem(user, result)

                match_count += 1
                continue
            else:
                print('[Indexer] Could not identify release')
                print('\n===========================\n')

                db = Database()
                db.start()
                db.setFolderAsUnknown(fold_id)

                unknown.append(fold)

        # pprint(results)
        # pprint(unknown)
        print("[Indexer] Found:", str(match_count), "Unknown:", len(unknown))
        return results, unknown


    def search_release_groups(self, title):
        # remove noisy characters
        # TODO: explore effectiveness and optimisation

        for exp in [r'_|\.|\(|\)|\[|\]|\{|\}', ' {2,}']:
            title = re.sub(exp, " ", title).strip()
        return musicbrainzngs.search_release_groups(releasegroup=title)

    def match_group_recording_ids(self, groups, recordings):
        # for each release-group search result
        for rg in groups['release-group-list']:
            rg_arid = rg['artist-credit'][0]['artist']['id']

            # TODO: if all release-groups are VA, then there's no point in searching a second track..

            if rg_arid == '89ad4ac3-39f7-470e-963a-56509c546377':
                print('[Indexer] Various Artists - Skipping')
                continue

            for rec in recordings['recording-list']:
                rec_aid = rec['artist-credit'][0]['artist']['id']

                if rec_aid == rg_arid: # if we've found a match
                    print('[Indexer] Found Match (Type 1)')
                    # pprint(rg)
                    return rg
                # else might have to check this way
                try:
                    for rel in rec['release-list']:
                        rel_aid = rel['artist-credit'][0]['artist']['id']
                        if rel_aid == rg_arid: # if we've found a match
                            print('[Indexer] Found Match (Type 2)')
                            # pprint(rg)
                            return rg
                except:
                    pass
        else:
            return None


if __name__ == '__main__':

    db = Database()
    users = [x[0] for x in db.getAllUsers()]
    db.close()

    for user in users:
        idx = Indexer(user)
        idx.start()
        idx.join()
