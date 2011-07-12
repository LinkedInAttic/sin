$(function() {
  window._void = function(){};

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
      var me = this;
      _.bindAll(this, 'read', 'create', 'update');
      ContentStoreModel.__super__.initialize.call(this);
      // console.log(this.get('config'));
      var columns = new ContentColumnCollection;
      var config = eval('('+this.get('config')+')');
      var table = config['table'];
      if (table) {
        _.each(table.columns, function(col) {
          col['parentModel'] = me;
          var column = new ContentColumnModel(col);
          var view = new ContentColumnView({model: column});
          columns.add(column);
        });
      }

      this.set({
        newColumn: new ContentColumnView({model: new ContentColumnModel({add: true, parentModel: me})}).model
      });

      var facets = new ContentFacetCollection;
      _.each(config.facets, function(obj) {
        obj['parentModel'] = me;
        var facet = new ContentFacetModel(obj);
        var params = new ContentFacetParamCollection;
        _.each(obj.params, function(param) {
          param['parentModel'] = facet;
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
        newFacet: new ContentFacetView({model: new ContentFacetModel({add: true, parentModel: me})}).model
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

  var validateColumn = function(col) {
    var res = {ok: true, msg: 'good'};

    if (!col.name) {
      res.ok = false;
      res.msg = 'Name is required.';
    }

    return res;
  };

  var validateFacet = function(obj) {
    var res = {ok: true, msg: 'good'};

    if (!obj.name) {
      res.ok = false;
      res.msg = 'Name is required.';
    }

    return res;
  };


  window.ContentColumnView = Backbone.View.extend({
    template: $('#content-column-tmpl').html(),

    className: 'content-column-item',

    events: {
      'click .edit': 'showEditor',
      'click .remove': 'removeMe',
      'click .save-column': 'saveColumn'
    },

    initialize: function() {
      _.bindAll(this, 'showEditor', 'removeMe', 'saveColumn', 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    removeMe: function() {
      this.model.get('parentModel').get('columns').remove(this.model);
      $(this.el).detach();
    },

    saveColumn: function() {
      var el = $(this.el);
      var obj = {
        name: el.find('.name').val(),
        type: el.find('.type').val(),
        from: el.find('.from').val(),
        delimiter: el.find('.delimiter').val(),
        index: el.find('.index').val(),
        multi: el.find('.multi').val(),
        store: el.find('.store').val(),
        termvector: el.find('.termvector').val()
      };

      var res = validateColumn(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }
      this.model.set(obj);
      this.render();
    },

    showEditor: function() {
      this.$('.editor').toggle();
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      this.$('.type').val(this.model.get('type'));
      this.$('.index').val(this.model.get('index'));
      this.$('.multi').val(this.model.get('multi'));
      this.$('.store').val(this.model.get('store'));
      this.$('.termvector').val(this.model.get('termvector'));

      return this;
    }
  });

  window.ContentFacetParamView = Backbone.View.extend({
    template: $('#content-facet-param-tmpl').html(),

    className: 'content-facet-param-item',

    events: {
      'click .remove-param': 'removeMe',
      'click .param-edit': 'showEditor',
    },

    initialize: function() {
      _.bindAll(this, 'showEditor', 'removeMe', 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    removeMe: function() {
      console.log(this.model.get('parentModel').get('params'));
      this.model.get('parentModel').get('params').remove(this.model);
      $(this.el).detach();
    },

    showEditor: function() {
      this.$('.param-editor').toggle();
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      return this;
    }
  });

  var validateParam = function(param) {
    var res = {ok: true, msg: 'good'};

    if (!param.name) {
      res.ok = false;
      res.msg = 'Name is required.';
    }

    return res;
  };

  window.ContentFacetView = Backbone.View.extend({
    template: $('#content-facet-tmpl').html(),

    className: 'content-facet-item',

    events: {
      'click .edit': 'showEditor',
      'click .remove': 'removeMe',
      'click .add-param': 'addParam',
      'click .save-facet': 'saveFacet'
    },

    initialize: function() {
      _.bindAll(this, 'showEditor', 'removeMe', 'saveFacet', 'render', 'addParam');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    removeMe: function() {
      this.model.get('parentModel').get('facets').remove(this.model);
      $(this.el).detach();
    },

    saveFacet: function() {
      var el = $(this.el);
      var obj = {
        name: el.find('.name').val(),
        type: el.find('.type').val(),
        depends: el.find('.depends').val(),
        dynamic: el.find('.dynamic').val(),
      };

      var res = validateFacet(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }
      this.model.set(obj);
      this.render();
    },

    addParam: function() {
      var obj = {
        name: this.$('.add-new-param .param-name').val(),
        value: this.$('.add-new-param .param-value').val()
      };

      var res = validateParam(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }

      obj['parentModel'] = this.model;
      var model = new ContentFacetParamModel(obj);
      var view = new ContentFacetParamView({model: model});
      if (!this.model.get('params'))
        this.model.set({'params': new ContentFacetParamCollection});
      this.model.get('params').add(model);

      this.render();
    },

    showEditor: function() {
      this.$('.editor').toggle();
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      this.$('select').val(this.model.get('type'));

      var container = this.$('.facet-params');
      if (this.model.get('params')) {
        this.model.get('params').each(function(obj) {
          container.append(obj.view.render().el);
        });
      }

      return this;
    }
  });

  window.ContentStoreView = Backbone.View.extend({
    template: $('#content-store-tmpl').html(),

    className: 'content-store-item',

	
	events:{
		'click .deleteStore': 'deleteStore',
    'click .add-column': 'addColumn',
    'click .add-facet': 'addFacet',
    'click .manage': 'showManage',
    'click .restart': 'restart',
    'click .save-store': 'saveStore'
	},
	
	deleteStore: function(){
		var model = this.model;
		$.getJSON('/store/delete-store/'+model.get('name'),function(resp){
			if (resp["ok"]){
				sinView.collection.remove(model);
				$('#main-area').empty().append(sinView.render().el);
			}
			else{
				alert(resp["msg"]);
			}	
		});
	},

    initialize: function() {
      _.bindAll(this, 'showManage', 'restart', 'render', 'saveStore', 'deleteStore', 'addColumn', 'addFacet');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    restart: function() {
      $.getJSON('/store/restart-store/'+this.model.get('name') + '/', function(res) {
        if (!res.ok)
          alert(res.error);
        else
          alert('done');
      });
    },

    addColumn: function() {
      var addNew = this.$('.add-new-column');
      var obj = {
        name: addNew.find('.name').val(),
        type: addNew.find('.type').val(),
        from: addNew.find('.from').val(),
        delimiter: addNew.find('.delimiter').val(),
        index: addNew.find('.index').val(),
        multi: addNew.find('.multi').val(),
        store: addNew.find('.store').val(),
        termvector: addNew.find('.termvector').val()
      };

      var res = validateColumn(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }
      obj['parentModel'] = this.model;
      var model = new ContentColumnModel(obj);
      var view = new ContentColumnView({model: model});
      this.model.get('columns').add(model);

      this.render();
    },

    addFacet: function() {
      var addNew = this.$('.add-new-facet');
      var obj = {
        name: addNew.find('.name').val(),
        type: addNew.find('.type').val(),
        depends: addNew.find('.depends').val(),
        dynamic: addNew.find('.dynamic').val(),
      };

      var res = validateFacet(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }
      obj['parentModel'] = this.model;
      var model = new ContentFacetModel(obj);

      if (this.model.get('newFacet').get('params')) {
        model.set({params: this.model.get('newFacet').get('params')});
        this.model.get('newFacet').set({params: new ContentFacetParamCollection()});
      }

      var view = new ContentFacetView({model: model});
      this.model.get('facets').add(model);

      this.render();
    },

    saveStore: function() {
      var schema = {
        "facets": [],
        "table": {
          "columns": [],
          "compress-src-data": true,
          "delete-field": "",
          "src-data-store": "src_data",
          "uid": "id"
        }
      };
      this.model.get('columns').each(function(obj) {
        schema.table.columns.push(obj.toJSON());
      });
      this.model.get('facets').each(function(obj) {
        var facet = obj.toJSON();
        if (facet.params)
          facet.params = facet.params.toJSON();
        schema.facets.push(facet);
      });
      this.model.set({config: JSON.stringify(schema)});
      var me = this;
      $.post('/store/update-config/'+this.model.get('name')+'/', {config: this.model.get('config')}, function(res) {
        if (!res.ok)
          alert(res.error);
        else {
          me.$('.manage-tab').hide();
        }
      }, 'json');
    },

    showManage: function() {
      this.$('.manage-tab').toggle();
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));

      var columns = this.$('.columns');
      this.model.get('columns').each(function(obj) {
        columns.append(obj.view.render().el);
      });

      this.$('.add-new-column').empty().append(this.model.get('newColumn').view.render().el);

      var facets = this.$('.facets');
      this.model.get('facets').each(function(obj) {
        facets.append(obj.view.render().el);
      });

      this.$('.add-new-facet').empty().append(this.model.get('newFacet').view.render().el);

      return this;
    }
  });

  window.SinView = Backbone.View.extend({
    initialize: function() {
      _.bindAll(this, "render");
//	  this.collection.bind('add', function(){alert('change event')});
    },

    render: function() {
      var el = $(this.el).empty();
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
      window.stores = new ContentStoreCollection;
      window.sinView = new SinView({
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

