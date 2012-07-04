"""
Placeholder object required by a Resource (as opposed to a ModelResource).
Even though this is technically associated with Django models it will
use model methods and therefore isn't compatible with Tastypie's ORM-based
ModelResource

This class comes almost verbatim from Tastypie docs.
"""

class Generic(object):
  def __init__(self, initial=None):
    self.__dict__['data'] = {}
    
    if hasattr(initial, 'items'):
      self.__dict['_data'] = initial
  
  def __getattr__(self, name):
    return self._data.get(name, None)
  
  def __setattr__(self, name, value):
    self.__dict__['data'][name] = value
  
  def to_dict(self):
    return self._data