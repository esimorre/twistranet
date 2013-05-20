from django.db import models

from twistranet.twistapp.models import Content

from django.utils.translation import ugettext_lazy as _

class PContent(Content):
    """ But: permettre l'edition de certains champs dans la console admin
        par exemple, owner: pour pouvoir editer les contenus help
    """
    class Meta:
        proxy = True
        #db_table = u'twistapp_content'
        verbose_name = 'Editable content'
