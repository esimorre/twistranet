import community_forms
from django import forms
from twistranet.twistapp.forms.widgets import ResourceWidget

from django.forms import widgets

class CommunityPrivateForm(community_forms.CommunityForm):
    """ 
    """
    def __init__(self, *args, **kw):
        super(CommunityPrivateForm, self).__init__(*args, **kw)
        self.fields['permissions'].choices = self.fields['permissions'].choices[-1:]
        