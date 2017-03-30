/*
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
*/

var BrowseModel = Backbone.Model.extend({
    defaults: function() {
        return {
            instances: new BrowseInstanceCollection()
        }
    },
    add: function(options){
        this.get('instances').add(new BrowseInstanceModel(
            {user: options.user,
            data : options.data}
        ));
    }
});

var BrowseInstanceModel = Backbone.Model.extend({ });

var BrowseInstanceCollection = Backbone.Collection.extend({
    model: BrowseInstanceModel
});
