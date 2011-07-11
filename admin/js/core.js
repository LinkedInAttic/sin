$(function() {
  var _void = function(){};

  window.ContentColumnModel = Backbone.Model.extend({
  });

  window.ContentFacetParamModel = Backbone.Model.extend({
  });

  window.ContentFacetModel = Backbone.Model.extend({
  });

  window.ContentColumnCollection = Backbone.Collection.extend({
    model: ContentColumnModel
  });

  window.ContentFacetParamCollection = Backbone.Collection.extend({
    model: ContentFacetParamModel
  });

  window.ContentFacetCollection = Backbone.Collection.extend({
    model: ContentFacetModel
  });

  window.ContentStoreModel = Backbone.Model.extend({
    defaults: {
    },

    initialize: function() {
      _.bindAll(this, 'read', 'create', 'update');
      ContentStoreModel.__super__.initialize.call(this);
      // console.log(this.get('config'));
      var columns = new ContentColumnCollection;
      var config = eval('('+this.get('config')+')');
      var table = config['table'];
      if (table) {
        _.each(table.columns, function(col) {
          var column = new ContentColumnModel(col);
          var view = new ContentColumnView({model: column});
          columns.add(column);
        });
      }

      var facets = new ContentFacetCollection;
      _.each(config.facets, function(obj) {
        var facet = new ContentFacetModel(obj);
        var params = new ContentFacetParamCollection;
        _.each(obj.params, function(param) {
          var p = new ContentFacetParamModel(param);
          var pv = new ContentFacetParamView({model: p});
          params.add(p);
        });
        facet.set({
          params: params
        });
        var view = new ContentFacetView({model: facet});
        facets.add(facet);
      });

      this.set({
        columns: columns,
        facets: facets
      });
    },

    read: function() {
    },

    create: function () {
    },

    update: function () {
    }
  });

  window.ContentStoreCollection = Backbone.Collection.extend({
    model: ContentStoreModel,
    url: '/store/stores/'
  });

  window.ContentColumnView = Backbone.View.extend({
    template: $('#content-column-tmpl').html(),

    className: 'content-column-item',

    initialize: function() {
      _.bindAll(this, 'showEditor', 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    showEditor: function() {
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      this.$('select').val(this.model.get('type'));

      this.$('.edit').bind('click', this.showEditor);

      return this;
    }
  });

  window.ContentFacetParamView = Backbone.View.extend({
    template: $('#content-facet-param-tmpl').html(),

    className: 'content-facet-param-item',

    initialize: function() {
      _.bindAll(this, 'showEditor', 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    showEditor: function() {
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      this.$('.edit').bind('click', this.showEditor);
      return this;
    }
  });

  window.ContentFacetView = Backbone.View.extend({
    template: $('#content-facet-tmpl').html(),

    className: 'content-facet-item',

    initialize: function() {
      _.bindAll(this, 'showEditor', 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    showEditor: function() {
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      this.$('select').val(this.model.get('type'));

      var container = this.$('.facet-params');
      this.model.get('params').each(function(obj) {
        container.append(obj.view.render().el);
      });

      this.$('.edit').bind('click', this.showEditor);

      return this;
    }
  });

  window.ContentStoreView = Backbone.View.extend({
    template: $('#content-store-tmpl').html(),

    className: 'content-store-item',

    initialize: function() {
      _.bindAll(this, 'showManage', 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    showManage: function() {
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));

      var columns = this.$('.columns');
      this.model.get('columns').each(function(obj) {
        columns.append(obj.view.render().el);
      });

      var facets = this.$('.facets');
      this.model.get('facets').each(function(obj) {
        facets.append(obj.view.render().el);
      });

      this.$('.manage').bind('click', this.showManage);
      return this;
    }
  });

  window.SinView = Backbone.View.extend({
    initialize: function() {
      _.bindAll(this, "render");
    },

    render: function() {
      var el = $(this.el);
      // console.log(this.collection);
      window.t = this.collection;

      this.collection.each(function(store) {
        if (!store.view) {
          var view = new ContentStoreView({
            model: store
          });
        }
        el.append(store.view.render().el);
      });

      return this;
    }
  });

  var baseSync = Backbone.sync;

  Backbone.sync = function(method, model, success, error) {
    _.bind(baseSync, this);

    var resp;

    switch (method) {
      case "read":
        if (model.read)
          resp = model.read();
        else
          return baseSync(method, model, success, error);
        break;
      case "create":
        if (model.create)
          resp = model.create();
        else
          return baseSync(method, model, success, error);
        break;
      case "update":
        if (model.update)
          resp = model.update();
        else
          return baseSync(method, model, success, error);
        break;
      case "delete":
        if (model.delete)
          resp = model.delete();
        else
          return baseSync(method, model, success, error);
        break;
    }

    if (resp) {
      success(resp);
    } else {
      error("Record not found");
    }
  };

  var SinSpace = Backbone.Router.extend({
    routes: {
      'dashboard':        'dashboard', //#dashboard
      '.*':               'index',
    },

    initialize: function() {
      _.bindAll(this, 'dashboard', 'manage');
      /*var info = new SenseiSystemInfo();*/
      /*window.senseiSysInfo = new SenseiSystemInfoView({model: info});*/
      /*info.fetch();*/
    },

    index: function() {
      //console.log('>>> index called');
      this.dashboard();
      this.navigate('dashboard');
    },

    dashboard: function() {
      var stores = new ContentStoreCollection;
      var sinView = new SinView({
        collection: stores
      });
      stores.fetch();
      // console.log(stores);
      _.delay(function() {
        $('#main-area').empty().append(sinView.render().el);
      }, 500);

                 /*$('#nav-node').text("");*/
                 /*$('#main-container').children().hide();*/

                 /*if (_.isUndefined(this.overviewRendered)) {*/
                 /*senseiSysInfo.model.nodesView.render();*/
                 /*this.overviewRendered = true;*/
                 /*}*/

                 /*$(senseiSysInfo.model.nodesView.el).show();*/
    },

    manage: function(id) {
              /*$('#nav-node').text(" > Node " + id);*/
              /*//console.log('>>> node '+id+' jmx called');*/
              /*$('#main-container').children().hide();*/
              /*if (_.isUndefined(senseiSysInfo.model.nodes.get(id))) {*/
              /*_.delay(this.jmx, 1000, id);*/
              /*return;*/
              /*}*/
              /*var jmxView = senseiSysInfo.model.nodes.get(id).jmxModel.view;*/

              /*var ukey = 'jmx' + id;*/
              /*if (_.isUndefined(this[ukey])) {*/
              /*jmxView.render();*/
              /*this[ukey] = true;*/
              /*}*/

              /*$(jmxView.el).show();*/
    }
  });

  window.sinSpace = new SinSpace();
  Backbone.history.start();
});

