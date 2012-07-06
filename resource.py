from django.db.models import Model
from django.db.models.queryset import QuerySet
from django.core import serializers
from tastypie.resources import Resource
from tastypie_model_method import container
import simplejson

class ModelMethodResource(Resource):
  """
  Outline values we'll include in the returned JSON.
  
  computed_value - string or json object
  error - string
  """
  computed_value = fields.CharField(attribute='computed_value',null=True)
  error = fields.CharField(attribute='error',null=True)
  
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
      
      """
      if isinstance(computed_value, Model):
        serialized = serializers.serialize('json', [computed_value,])
        obj = simplejson.loads(serialized)
        obj[0]['fields']['id'] = computed_value.pk
        computed_value = simplejson.dumps(obj[0]['fields'])
      
      elif isinstance(computed_value, QuerySet):
        return_list = []
        
        serialized = serializers.serialize('json', computed_value)
        obj_list = simplejson.loads(serialized)
        
        for obj in obj_list:
          obj['fields']['id'] = obj['pk']
          return_list.append(obj['fields'])
      
      return_val['computed_value'] = computed_value
      return [container.Generic(initial=return_val),]

  def obj_get_list(self, request=None, **kwargs):
    return self.get_object_list(request)
      