from community_views import CommunityView, CommunityCreate
from twistranet.twistapp.forms import community_ext_forms

class CommunityExtView(CommunityView):
    """ An extended Community view.
    
        This community view allows to define specific templates for a community instance.
        it also supports form registering limited to a given community and even to a role.
    """


    @property
    def template(self):
        return "community/ext/view.html"

class CommunityExtCreate(CommunityCreate):
    def get_form_class(self,):
        """
        You can use self.request and self.object to find your form here
        if you need to determinate it with an acute precision.
        """
        if self.auth.is_admin:
            return self.form_class
        else:
            return community_ext_forms.CommunityPrivateForm