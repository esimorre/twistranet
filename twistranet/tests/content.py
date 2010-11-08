"""
This is a set of account permissions tests
"""
from django.test import TestCase
from twistranet.models import *
from twistranet.lib import permissions, roles
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError
from helloworld.models import HelloWorld

from twistranet.lib import dbsetup

class ContentTest(TestCase):
    """
    Just to remember:
    A <=> admin
    B  => admin
    """
    def setUp(self, ):
        """
        Get A and B users
        """
        dbsetup.bootstrap()
        dbsetup.repair()
        __account__ = SystemAccount.get()
        self.system = __account__
        self.B = UserAccount.objects.get(user__username = "B").account_ptr
        self.A = UserAccount.objects.get(user__username = "A").account_ptr
        self.admin = UserAccount.objects.get(user__username = "admin").account_ptr

    def test_headline(self, ):
        """
        Check if headline is ok
        """
        __account__ = self.admin
        n = Notification(
            who = self.A,
            did_what = "joined",
            on_who = self.B,
            )
        n.save()
        self.failUnlessEqual(n.text_headline, "Albert Durand joined Bernard Dubois De La Fontaine")
        self.failUnlessEqual(n.html_headline, """<a href="/account/A/">Albert Durand</a> joined <a href="/account/B/">Bernard Dubois De La Fontaine</a>""", )
        self.failUnlessEqual(n.html_summary, "", )
        
    def test_helloworld_headline(self,):
        """
        Check our example product's headline.
        """
        __account__ = self.admin
        h = HelloWorld()
        h.save()
        c = Content.objects.get(id = h.id)
        self.failUnlessEqual(c.text_headline, "Hello, World!")
        
        
        