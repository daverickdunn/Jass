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

var BrowseView = Backbone.View.extend({
    className: '',
    initialize: function(options) {
        this.model = options.model;
        this.vent = options.vent;

        this.model.get('instances').on('add remove', function(){
            this.renderInstances();
        }, this);

        this.childViews = [];
        this.render();
    },
    template: _.template($('#browse').html()),

    renderInstances: function(){

        var self = this;
        self.$('#browse-tabs').html('');  // clear tabs

        // recreate tabs with event listeners
        this.model.get('instances').each(function(instance){
            var node = $(`<li class="nav-item" data-toggle="popover">
            <span class="close" id="close-browse"> &times;</span>
            <a class="nav-link">${instance.get('user')}</a>
            </li>`);

            // add new tab for user x
            self.$('#browse-tabs').append(node);

            // display view if tab selected
            node.on('click', function () {
                $(node).find('a').tab('show');      // show active tab
                self.currentInstance = instance;    // keep track of active tab
                var biv = new BrowseInstanceView({ model: instance, vent: self.vent});
                self.childViews.push(biv);
                self.$('#browse-instance-container').html('');
    			self.$('#browse-instance-container').append(biv.render().el);
            });

            // remove view if tab closed - also notify JASS server
            $(node).find('#close-browse').on('click', function(){
                self.vent.trigger('close-browse', instance.get('user'));
                self.model.get('instances').remove(instance);
                self.render();
            })

            // self binding view, for right-click options menu
            self.childViews.push(new ContextMenuView({
                user : instance.attributes.user,
                parent: node,
                vent: self.vent,
                list: [{title: "Add files to DB", event: "add-to-db"},
                        {title: "Add to users", event: "add-to-users"}]
            }));

            // highlight active tab when list is updated
            if (self.currentInstance == instance){
                $(node).find('a').tab('show');
            }

        }, this);

    },

    render: function() {
        this.$el.html(this.template());
        this.renderInstances();
        return this;
    }
});

var BrowseInstanceView = Backbone.View.extend({
    className: 'BrowseInstanceView',
    template: _.template($('#browse-instance').html()),
    initialize: function (options) {
        this.user = options.model.attributes.user;
        this.data = options.model.attributes.data;
        this.vent = options.vent;
        this.childViews = [];
    },

    recurFolders: function(data, element, depth){
        var self = this;

        var keys = Object.keys(data.dir);

        for (var i=0; i<keys.length; i++){

            var key = keys[i];                                  // folder title
            var files = data.dir[key].bin;                      // file attributes
            var length = Object.keys(data.dir[key].bin).length; // num of files

            // template literal
            var node = $(`<li class="list-group-item justify-content-between"
            style="padding-left:${String(1.25 + (1.25 * depth))}rem">${key}
            <div class="badge badge-default badge badge-default badge-pill">${length}</div></li>`);

            node.on('click', $.proxy( self.showFiles, self, files ));

            $(element).append(node);

            self.recurFolders(data.dir[key], element, depth+1);
        }
    },

    showFiles: function(files){
        var self = this;
        var element = self.$el.find('#browse-files-list').html('');
        Object.keys(files).forEach(function(file){
            var temp = new BrowseFileView({attr: files[file], title: file})
            self.childViews.push(temp);
            element.append(temp.render().el);
        });
    },

    render: function(){
        var self = this;
        var element = $(self.template({user: self.user}));
        self.recurFolders(self.data, element.find('#browse-folders-list'), 0);
        self.$el.html(element);
        return self;
    }
});

var BrowseFileView = Backbone.View.extend({
    className: 'BrowseFileView',
    template: _.template($('#browse-instance-files-panel-file').html()),
    initialize: function (options) {

        this.title = options.title;
        if (options.attr < 1024){
            this.size = options.attr + " B"
        } else if (options.attr < 1048576){
            this.size = (Math.round((options.attr/1024)*100)/100).toString() + " KiB"
        } else {
            this.size = (Math.round((options.attr/1048576)*100)/100).toString() + " MiB"
        }

    },
    render: function(){
        var self = this;
        var node = $(`<li class="list-group-item justify-content-between">${self.title}
        <div class="badge badge-default badge badge-default badge-pill">${self.size}</div></li>`);

        node.on('click', function(){
            window.alert('TODO: Download File ...')
        });
        self.$el.html(node);
        return self;
    }
});
