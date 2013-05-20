from models import *
from django import forms

from django.contrib import admin
from twistranet.tagging.models import Tag
from twistranet.twistapp.models.twistable import Twistable

class PContentForm(forms.ModelForm):
    permissions = forms.CharField(help_text="""
public|network|private|members|intranet|workgroup|blog|interest|internet.
roles: public = 1, network = 2, manager = 4, owner = 8,system = 16""")
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), required=False)
    class Meta:
        model = PContent


class PContentAdmin(admin.ModelAdmin):
    form = PContentForm
    list_display = ('pk', 'title', 'model_name', 'static_score')
    date_hierarchy = 'created_at'
    list_filter = ('model_name', 'permissions')
    readonly_fields = ('_p_can_view', '_p_can_edit', '_p_can_list',
        '_p_can_list_members', '_p_can_publish', '_p_can_join', '_p_can_leave', '_p_can_create')
    
    def save_model(self, request, obj, form, change):
        app = obj.app_label
        model = obj.model_name
        obj.save()
        obj.app_label = app
        obj.model_name = model
        super(Twistable, obj).save()
        
        
admin.site.register(PContent, PContentAdmin)
