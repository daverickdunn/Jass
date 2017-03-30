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

var UsersView = Backbone.View.extend({
    className: 'row justify-content-center',
    template: _.template($('#user-list-template').html()),
    initialize: function (options) {
        this.model = options.model;
        this.vent = options.vent;
        this.model.on('add remove', function(){
            this.render();
        }, this);
    },
    render: function(){
        console.log('rendering UsersView')
        var self = this;
        var element = self.$el.html($(self.template()));

        self.model.get('users').forEach(function(user, idx, array){

            var node = $(`<li class="list-group-item justify-content-between">
                            ${user.get('user')}
                            <div class="badge badge-default badge badge-default badge-pill">${user.get('country_code')}</div>
                            </li>`);


           // self binding view, for right-click options menu
           var cmv = new ContextMenuView({
               user : user.get('user'),
               parent: node,
               vent: self.vent,
               list: [{title: "Browse files", event: "browse-files"},
                        {title: "Add files to DB", event: "add-to-db"}]
           });

            element.find('#user_list').append(node);
        });
        return self;
    }
});
