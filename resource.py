from django.db.models import Model
from django.core import serializers
from tastypie.resources import Resource
from tastypie_model_method import container
import simplejson

class ModelMethodResource(Resource):
  """
  Outline values we'll include in the returned JSON.
  
  computed_value - string or json object
  error - string
  id - of object that performed calculation, for reference by client-side models
  """
  computed_value = fields.CharField(attribute='computed_value',null=True)
  error = fields.CharField(attribute='error',null=True)
  id = fields.IntegerField(attribute='id', null=True)
  
  class Meta:
    allowed_methods = ['get',]
    filtering: { 'pk': ['in', 'exact'], 'method': ['exact'] }
    object_class = container.Generic
  
  def get_object_list(self, request):
    """
    Both pk and method need to be in any request from the client. Method is the
    string name of the method you want to call on the model instance, referenced
    by pk. You don't need to include 'format', but calling it out here so it's
    not confused with kwargs passed to the method, as outlined below.
    
    This assumes your class has provided a "related_class" - this is a reference
    to the model type of your object. (Like django.contrib.auth.models.User)
    """
    required_params = ['pk', 'method', 'format']
    return_val = {}
    
    object_id = request.GET.get('pk', None)
    method_name = request.GET.get('method', None)
    
    if object_id and method_name:
      object_instance = self.related_class.objects.get(pk=object_id)
      
      """
      You can optionally provide an authorization_manager, that will ensure the
      requested object is part of the collection the requesting user is allowed
      to access.
      """
      if hasattr(self, 'authorization_manager'):
        auth_method = getattr(self.related_class.objects, self.authorization_manager)
        if object_instance not in auth_method(request.user)
          return_val['error'] = 'You do not have permission to view that object'
          return [container.Generic(initial=return_val),]
      
      """
      Your resource must explicity outline the accessible model methods for obvious
      reasons. This is done through the expose_to_api property.
      """
      if method_name not in self.expose_to_api:
        return_val['error'] = 'You do not have permission to call that method'
        return [container.Generic(initial=return_val),]
      
      if not hasattr(object_instance, method_name):
        return_val['error'] = 'That method does not exist for that object'
        return [container.Generic(initial=return_val),]
      
      method = getattr(object_instance, method_name)
      return_val['id'] = object_instance.pk
      
      """
      In case we're returning a method decorated with @property
      """
      if not callable(method):
        return_val['computed_value'] = method
        return [container.Generic(initial=return_val),]
      
      kwargs = {}
      
      for param, val in request.GET.items():
        if param not in required_params:
          kwargs[param] = val
      
      computed_value = method(**kwargs)
      
      """
      If the returned value of the method is a subclass of Django's Model then we'll need 
      to take special steps to serialize it. 
      
      TODO - this currently assumes a single object (as opposed to a Queryset) and doesn't 
      inspect that object to return full data about its relations. We probably want to do
      something like:
      
      for field in computed_value._meta.fields:
        if field.get_internal_type() == 'ForeignKey':
          computed_value[field.name] = Object.objects.get(pk=computed_value[field.name])
          or something
      """
      if isinstance(computed_value, Model):
        serialized = serializers.serialize('json', [computed_value,])
        obj = simplejson.loads(serialized)
        return_val['id'] = computed_value.pk
        computed_value = obj[0]['fields']
      
      return_val['computed_value'] = computed_value
      return [container.Generic(initial=return_val),]

  def obj_get_list(self, request=None, **kwargs):
    return self.get_object_list(request)
      