import community_forms
from django import forms
from twistranet.twistapp.forms.widgets import ResourceWidget

from django.forms import widgets

from twistranet.twistapp.models import Community
from twistranet.twistapp.forms.form_registry import FormRegistryManager as _FormRegistryManager

class CommunityPrivateForm(community_forms.CommunityForm):
    """ 
    """
    def __init__(self, *args, **kw):
        super(CommunityPrivateForm, self).__init__(*args, **kw)
        self.fields['permissions'].choices = self.fields['permissions'].choices[-1:]

class SimpleFormRegistryManager(_FormRegistryManager):
    def __init__(self):
        self._registry_ = {}

class FormRegistryManager:
    _form_registries = {}
    
    def register(self, community_slug, form_class, role=None):
        reg_name = community_slug
        if role: reg_name = "%s:%s" % (role, reg_name)
        
        if not self._form_registries.has_key(reg_name):
            self._form_registries[reg_name] = SimpleFormRegistryManager()
        self._form_registries[reg_name].register(form_class)
    
    def get_form_registry(self, name, role=None):
        if role:
            return self._form_registries["%s:%s" % (role, name)]
        return self._form_registries[name]

form_registry = FormRegistryManager()