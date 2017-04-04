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
import os
import mutagen
from pprint import pprint

def recurAndPrint(path):

    for entry in os.scandir(path):
        if not entry.name.startswith('.') and entry.is_dir():
            recurAndPrint(entry.path)
        elif not entry.name.startswith('.') and entry.is_file():
            try:
                print('Size:', entry.stat().st_size)
                print('0:', mutagen.File(entry.path).info.bitrate)
                print('1:', mutagen.File(entry.path).info.length)
                print('\n')
            except mutagen.MutagenError as e:
                print('Mutagen error:', e)
            except AttributeError:
                pass


def _buildFileFolder(path, file_folder):

    fake_path = '@@wlaqp/' + path

    file_folder[fake_path] = []

    for entry in os.scandir(path):
        if not entry.name.startswith('.') and entry.is_dir():
            _buildFileFolder(entry.path, file_folder)

        elif not entry.name.startswith('.') and entry.is_file():

            this_file = {
                'title': entry.name,
                'size': entry.stat().st_size,
                'ext' : entry.name.rsplit('.', 1)[1],
                'attributes': {}
            }

            try:
                mutagen_file = mutagen.File(entry.path)
                if mutagen_file:
                    this_file['attributes']['0'] = mutagen_file.info.bitrate
                    this_file['attributes']['1'] = round(mutagen_file.info.length)
            except mutagen.MutagenError as e:
                print('Mutagen error:', e)
            finally:
                file_folder[fake_path].append(this_file)

def buildFileFolder(path):
    file_folder = {}
    _buildFileFolder(path, file_folder)
    return file_folder


if __name__ == '__main__':

    path = 'collection'
    file_folder = buildFileFolder(path)
    pprint(file_folder)
