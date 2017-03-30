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

var ContainerView = Backbone.View.extend({

    className: 'main',

    template: _.template($('#container-template').html()),

    initialize: function(options) {
        this.model.on("change:viewState", this.render, this);
        this.childViews = [];
    },

    changeView: function(){
        var view = this.model.get('viewState');
        this.childViews.push(view);
        this.$el.find('#container').html(view.render().el);
        this.$el.find(this.model.get('activeTab')).tab('show'); // 'tab' is bootstrap js
    },

    render: function() {
        this.close();
        this.$el.html(this.template());
        this.changeView();
        $('body').html(this.$el);
    }
});


var ContextMenuView = Backbone.View.extend({

    template: _.template($('#contextmenu-template').html()),

    initialize: function(options) {
        this.childViews = [];
        this.user = options.user;
        this.list = options.list;
        this.vent = options.vent;
        this.parent = options.parent;
        this.render();
    },

    render: function() {

        var self = this;

        $(self.parent).on('contextmenu', function (e) {

            // hide all other popovers
            $('.popover').popover('dispose');

            // completely reset this popover in case it already existed
            self.$el.html('');
            var element = self.$el.html(self.template());

            $(self.parent).popover('dispose');

            // options.parent 'this'
            var pop = $(this)

            pop.popover({
                html: true,
                content: element,
                trigger: 'focus'
            }).popover('show');

            pop.on('shown.bs.popover', function(e){

                $(self.el).find('#close-contextmenu').on('click', function(e){
                    pop.popover('dispose');
                });

                var list = $(self.el).find('#contextmenu-list');

                self.list.forEach(function(item){
                    var node = $(`<li class="list-group-item"><a href="javascript:;">${item.title}</a>`);
                    $(node).on('click', function(e){
                        self.vent.trigger(item.event, self.user);
                        pop.popover('dispose');
                    });
                    list.append(node);
                });

            });
            return false;
        });
        return this;
    }
});
