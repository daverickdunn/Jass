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

var RoomsListModel = Backbone.Model.extend({
    defaults: {
        std_rooms : []
    }
});

var UserModel = Backbone.Model.extend({});
var UserCollection = Backbone.Collection.extend({
    model: UserModel
});

var ChatModel = Backbone.Model.extend({});
var ChatCollection = Backbone.Collection.extend({
    model: ChatModel
});

var ChatRoomModel = Backbone.Model.extend({
    defaults: function() {
        return {
            room: '',
            users: new UserCollection(),
            chats: new ChatCollection()
        }
    },
    addUser: function(data) {
        this.get('users').add(new UserModel({ user: data.user, files : data.files}));
    },
    // removeUser: function(username) {
    //     var users = this.get('users');
    //     var user = users.find(function(item) {
    //         return item.get('name') == username
    //     });
    //     if (user) {
    //         users.remove(user);
    //     }
    // },
    addChat: function(chat) {
        this.get('chats').add(new ChatModel({ user: chat.user, message: chat.message }));
    },
});

var ChatRoomsCollection = Backbone.Collection.extend({
    model: ChatRoomModel
});
