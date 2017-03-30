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

$(document).ready(function() {
    // memory management!
    Backbone.View.prototype.close = function(){
        this.remove();
        this.unbind();

        if (this.childViews) {
            _.each(this.childViews, function(childView){
                if (childView.close){
                    childView.close();
                }
            });
        }

        if (this.onClose){
            this.onClose();
        }
    };

    var main = new Main();
    main.init();
});

var Main = function() {

    var _this = this;
    _this.clientToServer = _.extend({}, Backbone.Events);
    _this.serverToClient = _.extend({}, Backbone.Events);

    _this.init = function() {

        // connect to server
        _this.socket = io('http://' + document.domain + ':' + location.port + '/test');

        // { viewState: roomsView}
        var containerModel = new ContainerModel();
        var roomsListModel = new RoomsListModel();
        var joined_rooms = new ChatRoomsCollection(); // TODO: move into RoomsListModel
        var browseModel = new BrowseModel();
        var usersModel = new UsersModel();
        var recommenderModel = new RecommenderModel();

        var containerView = new ContainerView({ model: containerModel });

        var browseView = new BrowseView({
            model : browseModel,
            vent: _this.clientToServer
        });

        var usersView = new UsersView({
            model: usersModel,
            vent: _this.clientToServer
        });

        var roomsView = new RoomsView({
            joinedRooms: joined_rooms,
            roomsList: roomsListModel,
            vent: _this.clientToServer
        });

        var recommenderView = new RecommenderView({
            model : recommenderModel,
            vent: _this.clientToServer
        });

        var searchView =        new SearchView();
        var chatView =          new ChatView();
        var downloadsView =     new DownloadsView();
        var uploadsView =       new UploadsView();
        var optionsView =       new OptionsView();

        // must initalise containerModel before router
        containerModel.set({ viewState: roomsView, activeTab: '#rooms-tab' });

        var router = Backbone.Router.extend({
        	routes: {
                '': 'rooms',
        		'rooms': 'rooms',
                'chat': 'chat',
        		'search': 'search',
                'users': 'users',
                'browse': 'browse',
                'uploads': 'uploads',
                'downloads': 'downloads',
                'recommender': 'recommender',
                'options': 'options',
        	},

        	rooms: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: roomsView, activeTab: '#rooms-tab' });
        	},
            chat: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: chatView, activeTab: '#chat-tab' });
        	},
        	search: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: searchView, activeTab: '#search-tab' });
        	},
            users: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: usersView, activeTab: '#users-tab' });
        	},
            browse: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: browseView, activeTab: '#browse-tab' });
        	},
            uploads: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: uploadsView, activeTab: '#uploads-tab' });
        	},
            downloads: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: downloadsView, activeTab: '#downloads-tab' });
        	},
            recommender: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: recommenderView, activeTab: '#recommender-tab' });
        	},
            options: function(){
                containerModel.get('viewState').close();
                containerModel.set({ viewState: optionsView, activeTab: '#options-tab' });
        	},

        });

        _this.socket.on('slsk', function (msg) {

            var json = JSON.parse(msg);

            if (json.code == 'S5'){
                console.log(json)
                usersModel.add(json);

            } else if (json.code == 'S13'){
                // chat message has been received in room x
                var room = joined_rooms.findWhere({room : json.room});
                room.addChat(json);

            } else if (json.code == 'S14'){
                // we've joined a room: create new room model and add users
                var crm = new ChatRoomModel({room : json.room});
                json.users.forEach(function(user, idx, array){
                    crm.addUser(user);
                })
                joined_rooms.add(crm)


            } else if (json.code == 'S15'){
                // remove a user who has left a room
                var room = joined_rooms.findWhere({room : json.room});
                joined_rooms.remove(room);
                roomsView.render();

            } else if (json.code == 'S64'){
                // list of available chat rooms
                roomsListModel.set(json);


            } else if (json.code == 'J1'){ // Custom message to restore session

                // update rooms
                joined_rooms.reset();
                json.rooms.forEach(function(data, idx, array){
                    var crm = new ChatRoomModel({room : data.room});
                    data.users.forEach(function(user, idx, array){
                        crm.addUser(user);
                    });
                    joined_rooms.add(crm);
                });

                // update browse views
                Object.keys(json.browse).forEach(function(user){
                    browseModel.add({user: user, data: json.browse[user].data});
                });

                // update user view
                json.users.forEach(function(user){
                    console.log(user)
                    usersModel.add(user);
                })

            } else if (json.code == 'P5'){ // peer message - browse files
                browseModel.add({user: json.user, data: json.data});

            } else if (json.code == 'J5'){
                recommenderModel.set(json);
            }

            json = null;


        });

        /*
        *   Trigger Server Messages
        */
        _this.clientToServer.on('add-to-users', function (user) {
            _this.socket.emit('message_from_gui', {"code": 'S5', "user" : user});
        });

        _this.clientToServer.on('say-room', function (room, message) {
            _this.socket.emit('message_from_gui', {"code": 'S13', "room" : room, 'message' : message});
        });

        _this.clientToServer.on('join-room', function (room) {
            _this.socket.emit('message_from_gui', {"code": 'S14', "room" : room});
        });

        _this.clientToServer.on('leave-room', function (room) {
            _this.socket.emit('message_from_gui', {"code": 'S15', "room" : room});
        });

        /*
        *   Trigger Peer Messages
        */
        _this.clientToServer.on('browse-files', function (user) {
            _this.socket.emit('message_from_gui', {"code": 'P4', "user" : user});
        });

        /*
        *   Trigger JASS Messages
        */
        _this.clientToServer.on('add-to-db', function (user) {
            _this.socket.emit('message_from_gui', {"code": 'J2', "user" : user});
        });

        _this.clientToServer.on('close-browse', function (user) {
            _this.socket.emit('message_from_gui', {"code": 'J3', "user" : user});
        });

        _this.clientToServer.on('index-all', function () {
            _this.socket.emit('message_from_gui', {"code": 'J4'});
        });

        _this.clientToServer.on('refresh-recommendations', function () {
            _this.socket.emit('message_from_gui', {"code": 'J5'});
        });


        // kick everything off ...
        new router;
        Backbone.history.start();
        containerView.render();

    }
}
