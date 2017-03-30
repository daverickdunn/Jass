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

var RoomsView = Backbone.View.extend({
    className: 'container-fluid',
    template: _.template($('#rooms').html()),
    initialize: function(options) {

        this.joinedRooms = options.joinedRooms;
        this.vent = options.vent;

        this.roomsListView = new RoomsListView({
            model: options.roomsList,
            vent: options.vent
        });

        // if we joined a new room
        this.joinedRooms.on('add', function(){ this.render(); }, this);

    },
    render: function() {
        var self = this;
        self.$el.html($(self.template()));

        // rooms list
        self.$el.find('#rooms-list-panel').html(self.roomsListView.render().el);

        // joined rooms
        var rooms_container = self.$el.find('#chatrooms-panel')
        self.joinedRooms.each(function(m) {
            var chatroom = new ChatRoomView({
                vent: self.vent,
                model: m
            });
            rooms_container.append(chatroom.render().el);
        });

        return self;
    }
});


var ChatRoomView = Backbone.View.extend({
    events: {
        'submit #chatInput': 'chatInput',
        'click #leaveRoom' : 'leaveRoom'
    },
    template: _.template($('#chatroom-template').html()),
    initialize: function(options) {
        this.vent = options.vent;
        this.model.get('chats').on('add', function(){
            this.render();
        }, this);
    },
    render: function() {
        this.$el.html(this.template({
            room  : this.model.attributes.room,
            chats : this.model.attributes.chats.toJSON(),
        }));

        this.model.attributes.users.each(function(user){
            var userView = new UserView({ model: user, vent: this.vent});
			this.$('#open_room_users').append(userView.render().el);
        }, this)

        var self = this;
        setTimeout(function() {
            self.$('#open_room_chat').scrollTop(self.$('#open_room_chat').prop("scrollHeight"));
        }, 0);

        return this;
    },
    chatInput: function(e){
        e.preventDefault();
        var textbox = this.$('#chatInputText');
        this.vent.trigger('say-room', this.model.attributes.room, textbox.val());
        textbox.val("");
    },
    leaveRoom: function(){
        this.vent.trigger('leave-room', this.model.attributes.room);
    }

});

var UserView = Backbone.View.extend({
    // className: 'UserView',
    template: _.template($('#person-template').html()),
    initialize: function (options) {
        this.vent = options.vent;
        this.childViews = [];
    },
    render: function(){
        this.$el.html(this.template(this.model.toJSON()));

        this.childViews.push(new ContextMenuView({
            user : this.model.get('user'),
            parent: this.$el,
            vent: this.vent,
            list: [{title: "Browse files", event: "browse-files"},
            {title: "Add to users", event: "add-to-users"}]
        }));

        return this;
    }
});


var RoomsListView = Backbone.View.extend({
    // className: 'roomlist-card',
    template: _.template($('#roomlist-template').html()),
    initialize: function (options) {
        this.vent = options.vent;
        this.model.on('add remove change', function(){
            this.render();
        }, this);
    },
    render: function(){
        var self = this;
        var element = $(this.template());

        this.model.attributes.std_rooms.forEach(function(room, idx, array){

            // TODO: Add option to render all rooms ...
            if (room.num_users < 3){
                return;
            }

            var node = $(`<div><li class="list-group-item justify-content-between">
            ${room.room_name}
            <div class="badge badge-default badge badge-default badge-pill">${room.num_users}</div>
            </li></div>`);

            node.on('click', function () {
                self.vent.trigger('join-room', room.room_name)
            });

            element.find('#rooms_list').append(node);
        });

        this.$el.html(element);
        return this;
    }
});
