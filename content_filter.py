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
import threading
import pandas as pd
from pprint import pprint
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from database import Database

class ContentFilter(threading.Thread):

    def __init__(self, user, depth, callback):
        self.user = user
        self.depth = depth
        self.callback = callback
        super(ContentFilter, self).__init__()

    def run(self):
        self._run()

    def _run(self):

        print('[Content Filter] Processing started')

        db = Database()
        tags = db.getArtistsTags()

        d_frame = pd.DataFrame.from_dict(tags, orient='index')


        # A matrix of TF-Idf features.
        tf_idf = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 3),
            max_df = 0.40,
            min_df=0,
            stop_words='english')

        # Learn vocabulary and id_frame from training set.
        # Transform documents into a document-term matrix.
        matrix = tf_idf.fit_transform(d_frame[0])

        # L2 normalisation
        cosines = linear_kernel(matrix, matrix)

        results = {}
        for idx, item in enumerate(cosines):
            # cosine_similarity at idx, sorted, reversed, minus first result (beacuse it's the same artist)
            results[d_frame.iloc[idx].name] = [d_frame.iloc[i].name for i in item.argsort()[len(item)-2::-1]]

        # get artists associated with current user
        art_ids = db.getArtistIDsByUser(self.user)


        # filter results by current users artist ids
        user_results = { k: results[k] for k in art_ids if k in results }

        # create a dict of predictions : [ artists that caused prediction ]
        suggestions = {}
        for train_id, pred_ids in user_results.items():
            t = db.getArtistByID(train_id)
            for idx, pred in enumerate(x for x in pred_ids if x not in art_ids):
                p = db.getArtistByID(pred)
                if idx > self.depth:
                    break
                elif p in suggestions:
                    suggestions[p].append(t)
                else:
                    suggestions[p] = [t]

        db.close()

        print('[Content Filter] Processing complete')

        self.callback(suggestions)



if __name__ == '__main__':
    cf = ContentFilter('jass_test_1', 10, pprint)
    cf.start()
