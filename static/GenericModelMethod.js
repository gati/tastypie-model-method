var GenericModelMethod = Backbone.Model.extend({
  initialize: function(options) {
    this.resourceEndpoint = options.resourceEndpoint;
    this.proxyModel = options.proxyModel;
    this.proxyModelProperty = options.proxyModelProperty;
    this.forceRaiseChange = options.forceRaiseChange || false;
    this.forceRetrieve = options.forceRetrieve || false;
  },
  idAttribute: 'id',
  url: function(options) {
    return this.resourceEndpoint;
  },
  fetch: function(options) {
    exists = this.proxyModel.get(this.proxyModelProperty);
    if !exists || this.forceRetrieve {
      Backbone.Model.prototype.fetch.call(this, options);
    }
    else if this.forceRaiseChange {
      this.proxyModel.trigger("change:"+this.proxyModelProperty);
    }
  },
  parse: function(response, xhr) {
    if(!_.isUndefined(this.proxyModel) && !_.isUndefined(this.proxyModelProperty)) {
      returned_obj = response.objects[0];
      returned_val = returned_obj.computed_value;
      
      this.proxyModel.set(this.proxyModelProperty, returned_val);
      
      if(_.isObject(returned_val)) {
        newModel = this.proxyModel.get(this.proxyModelProperty);
        newModel.id = returned_obj.id; // id on the object
        newModel.set('id', returned_obj.id); // id attribute, both are required
      }
      
      if(this.forceRaiseChange && _.isNull(this.proxyModel.get(this.proxyModelProperty))) {
        this.proxyModel.trigger("change:"+this.proxyModelProperty);
      }
      
    }
  }
});