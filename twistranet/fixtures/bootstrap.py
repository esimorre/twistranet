"""
The minimal bootstrap for TN to work.
We use a python file to ensure proper DB alimentation. Django fixtures are not enough to ensure DB consistancy.

Objects in those fixtures will get created but NEVER updated.
"""
from twistranet.models import *
from twistranet.lib.python_fixture import Fixture

FIXTURES = [
    Fixture(
        GlobalCommunity,
        slug = "all_twistranet",
        screen_name = "All TwistraNet Members",
        description = "This community contains all TwistraNet members. It's mainly used for critical information.",
        permissions = "intranet",
    ),
    
    Fixture(
        AdminCommunity,
        slug = "administrators",
        screen_name = "Administrators",
        description = "TwistraNet admin team",
        permissions = "workgroup",
    ),

    # Default menu items
    Fixture(
        Menu,
        slug = "menu_main",
        name = "Main Menu",
    ),

    Fixture(
        MenuItem,
        menu = Menu.objects.filter(slug = "menu_main"),
        order = 0,
        view_path = "twistranet.views.home",
        title = "Home",
        slug = "menuitem_home",
    ),

    Fixture(
        MenuItem,
        menu = Menu.objects.filter(slug = "menu_main"),
        order = 10,
        view_path = 'twistranet.views.communities',
        title = "Communities",
        slug = "menuitem_communities",
    ),

    Fixture(
        MenuItem,
        menu = Menu.objects.filter(slug = "menu_main"),
        parent = MenuItem.objects.filter(slug = "menuitem_communities"),
        order = 0,
        view_path = 'twistranet.views.communities',
        title = "View all communities",
        slug = "menuitem_all_communities",
    ),
    
]


