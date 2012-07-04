Tastypie Model Methods:
----

I was porting a recent Django project to a single-page client app using [Tastypie](https://github.com/toastdriven/django-tastypie) and [Backbone.js](http://backbonejs.org). While some business logic rightly moves to the client in this scenario, some calculations make more sense on the server -- namely because it has access to the entire database all the time, and presumably your client does not. Plus in the event future applications need access to the same resources (native mobile apps, whatever), it'd be a shame to rewrite that logic over and over in every new client.

Hence, Tastypie Model Methods. 

This assumes you're familiar with both Backbone.js and Tastypie, as I can't imagine this need arising until you're already up and running with at least a small application. If not, go do that first. Then...

In your Django Project:
----
Let's assume you have the following model.
    
    from django.db import models
    from django.contrib.auth.models import User
    
    class UserProfile(models.Model):
      user = models.OneToOneField(User)
      
      def full_name(self):
        return "%s %s" %(self.user.first_name, self.user.last_name)

You can't possibly afford to duplicate the highly complex full_name method on your UserProfile model, so want the client to access it via your API. Sweet. You'll first need to define a new resource (just like a would a ModelResource), that subclasses ModelMethodResource.

    from tastypie_model_method.resource import ModelMethodResource
    from myapp.models import UserProfile
    
    class MyMethodResource(ModelMethodResource):
      related_class = UserProfile
      expose_to_api = [
        'full_name',
      ]
      
      authorization_manager = 'viewable_by_user'
      
      class Meta(ModelMethodResource.Meta):
        resource_name = 'my-awesome/super-awesome-method'

As you've probably surmised:
* `related_class` is the model containing the method you'd like to call
* `expose_to_api` contains the only model methods the API can access - choose wisely
* `authorization_manager` is optional. If used it limits which objects the requesting user can access. This can be a Manager, or even better a Queryset - check out [PassThroughManagers in django-model-utils](https://github.com/carljm/django-model-utils/) for an example. This is just a string, but make sure it's method you could call on your model class' `objects` property. Like `MyModel.objects.viewable_by_user()`
 
This may be all you need, in which case download this bad boy and go write some code. Included however is a Backbone.js model that you may also find useful. It takes the computed_value returned by your ModelMethodResource and assigns it to a client model instance, taking case of trigger `change` events and other goodies. Just include that file in your template after Backbone and its dependencies, and then in your routes, controllers, or wherever your keep this kind of logic in your Backbone app ...


In your Backbone app:
---
    var modelMethodName = 'first_name';
    var user = new User(); // assuming User is a Backbone model
    var genericModel = new GenericModelMethod({
      proxyModel: user,
      proxyModelProperty: 'first_name',
      resourceEndpoint: '/api/v1/my-awesome/super-awesome-method/',
      forceRaiseChange: true, // defaults to false
      forceRetrieve: true // also defaults to false
    });
    


* `proxyModel` is the client model instance that we'll update after retrieving the returned value from the server model method

* `proxyModelProperty` is the property on the client model where you'll access whatever the model method returned

* `resourceEndpoint` in this example is the full path to the resource (like /api/v1/my-awesome/super-awesome-method/). You may want to prototype GenericModelMethod and define a `url` method that uses any system-wide variables you're setting for commonly-used things like your base API endpoint

* `forceRaiseChange` does just what it says. Often I'll bind a view to the change:[model_method] event so I can hold off on rendering views and avoid popcorn UI (bits of the UI suddenly appearing as data trickles in from the server). However if the model method returns null, and you want to do something with that information, you'll want to trigger the change event manually as that property on your Backbone model was null in the first place.

* `forceRetrieve` also does just what it says. Data returned from a model method isn't retrieved over and over again unless you explicity ask for it.


Status:
-----

This is a work in progress. you'll notice in ModelMethodResource that if your model method can only return a string, int or a single model object. Work needs to be done in order to accept obviously useful values, like a Queryset.