from ..models import *
from twistranet.twistapp.models.resource import Resource
from twistranet.twistapp.models.twistable import Twistable
from twistranet.twistapp.models.network import Network

from django.contrib import admin


class TwistableAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'model_name', 'static_score')
    date_hierarchy = 'created_at'
    list_filter = ('model_name', 'permissions')
    readonly_fields = ('permissions',)
admin.site.register(Document, TwistableAdmin)
admin.site.register(File, TwistableAdmin)
admin.site.register(Comment, TwistableAdmin)
admin.site.register(StatusUpdate, TwistableAdmin)
admin.site.register(Resource, TwistableAdmin)
admin.site.register(Twistable, TwistableAdmin)
admin.site.register(Network)
