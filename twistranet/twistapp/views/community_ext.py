from community_views import CommunityView

from twistranet.twistapp.models import Community
from twistranet.twistapp.forms.form_registry import FormRegistryManager

class CommunityExtView(CommunityView):
    """ An extended Community view.
    
        This community view allows to define specific templates for a community instance.
        it also supports form registering limited to a given community and even to a role.
    """

    _form_registries = {}
    
    @classmethod
    def form_register(cls, community_slug, form_class, role=None):
        reg_name = community_slug
        if role: reg_name = "%s:%s" % (role, reg_name)
        
        if not cls._form_registries.has_key(reg_name):
            cls._form_registries[reg_name] = FormRegistryManager()
        cls._form_registries[reg_name].register(form_class)
    
    def get_form_registry(self, role=None):
        if role:
            return self._form_registries["%s:%s" % (role, self.name)]
        return self._form_registries[self.name]

    @property
    def template(self):
        return "community/ext/view.html"