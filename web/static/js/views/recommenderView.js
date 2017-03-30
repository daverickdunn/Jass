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

var RecommenderView = Backbone.View.extend({
    template: _.template($('#recommender-template').html()),
    // TODO: events won't work when doing a hard-reload of page!
    // events:{
    //     'click #index-all-collections' : 'indexAll',
    //     'click #refresh-recommendations' : 'refreshRec'
    // },
    initialize: function(options) {
        this.model = options.model;
        this.vent = options.vent;
        this.model.on('change', function(){ this.renderRecs(); }, this);
        this.childViews = [];
        this.render();
    },
    indexAll: function(e) {
        e.preventDefault();
        this.vent.trigger('index-all');
    },
    refreshRec: function(e) {
        e.preventDefault();
        this.vent.trigger('refresh-recommendations');
    },
    renderRecs: function(){
        var self = this;
        var list = self.$el.find('#recommendations-list');
        Object.keys(this.model.get('recommendations')).forEach(function(key){
            var node = $(`<div><li class="list-group-item justify-content-between">${key}</li></div>`);
            // <div class="badge badge-default badge badge-default badge-pill">${self.size}</div>


            // var popover = $(this).popover('dispose');
            //
            // popover.popover({
            //     html: true,
            //     content: element,
            //     trigger: 'focus'
            // }).popover('show');


            list.append(node);
        });
    },
    render: function() {
        var self = this;
        self.$el.html(self.template());

        self.$el.find('#index-all-collections').on('click', function(e){
            self.indexAll(e);
        });

        self.$el.find('#refresh-recommendations').on('click', function(e){
            self.refreshRec(e);
        });
        return this;
    }
});
