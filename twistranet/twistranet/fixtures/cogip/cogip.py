# -*- coding: utf-8 -*-
"""
Sample building script for the COGIP example.
"""
import csv
import os

from twistranet.twistranet.models import *
from twistranet.content_types.models import *
from twistranet.twistranet.lib.python_fixture import Fixture
from twistranet.twistranet.lib.slugify import slugify
from twistranet.twistranet.lib.log import *
from django.contrib.auth.models import User
from django.core.files import File as DjangoFile

HERE_COGIP = os.path.abspath(os.path.dirname(__file__))

def load_cogip():
    """
    WARNING: THIS IS MEANT TO BE LOAD FROM AN EMPTY DATABASE!
    We didn't bother testing it with a pre-populated one as it doesn't make that much sense.
    """
    # Just to be sure, we log as system account
    __account__ = SystemAccount.get()

    # Import the whole file, creating all needed fixtures, including Service as communities.
    f = open(os.path.join(HERE_COGIP, "cogip.csv"), "rU")
    c = csv.DictReader(f, delimiter = ';', fieldnames = ['firstname', 'lastname', 'sex', 'service', 'function', 'email', 'picture_file', 'network'])
    services = []
    for useraccount in c:
        # Create the user if necessary
        username = slugify("%s%s" % (useraccount['firstname'][0].decode('utf-8'), useraccount['lastname'].decode('utf-8'), ))
        username = username.lower()
        password = slugify(useraccount['lastname']).lower()
        if not User.objects.filter(username = username).exists():
            u = User.objects.create(
                username = username,
                email = useraccount['email'],
            )
            u.set_password(password)
            u.save()
        
        # Create the user account
        Fixture(
            UserAccount,
            slug = username,
            title = "%s %s" % (useraccount['firstname'], useraccount['lastname'], ),
    		description = useraccount['function'],
            permissions = "public",
            user = User.objects.get(username = username),
            force_update = True,
        ).apply()
        
        # Create a community matching user's service or make him join the service. And put it in a menu!
        service_slug = slugify(useraccount['service'])
        if not service_slug in services:
            services.append(service_slug)
            service = Fixture(
                Community,
                slug = service_slug,
                title = useraccount['service'],
                permissions = "blog",
                logged_account = username,
                force_update = True,
            ).apply()
            
            # Add default picture in the community
            source_fn = os.path.join(HERE_COGIP, 'cogip.png')
            r = Resource(
                publisher = service,
                resource_file = DjangoFile(open(source_fn, "rb"), 'cogip.png'),
            )
            r.save()
            service.picture = r
            service.save()
            
            # Create the menu item
            if not MenuItem.objects.filter(slug = "cogip_menu").exists():
                cogip_menu = MenuItem.objects.create(
                    slug = "cogip_menu",
                    order = 5,
                    title = "La COGIP",
                    parent = Menu.objects.get(),
                    link_url = "/",
                )
                cogip_menu.save()
            else:
                cogip_menu = MenuItem.objects.get(slug = "cogip_menu")
            item = MenuItem.objects.create(parent = cogip_menu, target = service)
            item.save()
        else:
            Community.objects.get(slug = service_slug).join(UserAccount.objects.get(slug = username))

        # Create / Replace the profile picture if the image file is available.
        source_fn = os.path.join(HERE_COGIP, useraccount['picture_file'])
        if os.path.isfile(source_fn):
            picture_slug = slugify("pict_%s" % useraccount['picture_file'])
            Resource.objects.filter(slug = picture_slug).delete()
            r = Resource(
                publisher = UserAccount.objects.get(slug = username),
                resource_file = DjangoFile(open(source_fn, "rb"), useraccount['picture_file']),
                slug = picture_slug,
            )
            r.save()
            u = UserAccount.objects.get(slug = username)
            u.picture = Resource.objects.get(slug = picture_slug)
            u.save()
            
        # Add friends in the network (with pending request status)
        if useraccount['network']:
            for friend in [ s.strip() for s in useraccount['network'].split(',') ]:
                log.debug("Put '%s' and '%s' in their network." % (username, friend))
                current_account = UserAccount.objects.get(slug = username)
                __account__ = UserAccount.objects.get(slug = username)
                friend_account = UserAccount.objects.get(slug = friend)
                friend_account.add_to_my_network()
                __account__ = UserAccount.objects.get(slug = friend)
                current_account.add_to_my_network()
                __account__ = SystemAccount.objects.get()

    # Create communities and join ppl from there
    f = open(os.path.join(HERE_COGIP, "communities.csv"), "rU")
    c = csv.DictReader(f, delimiter = ';', fieldnames = ['title', 'description', 'permissions', 'members', ])
    for community in c:
        if not community['members']:
            continue
        member_slugs = [ slug.strip() for slug in community['members'].split(',') ]
        if not member_slugs:
            continue
        service_slug = slugify(community['title'])
        com = Fixture(
            Community,
            slug = service_slug,
            title = community['title'],
            description = community['description'],
            permissions = community['permissions'],
            logged_account = member_slugs[0],
        ).apply()
        
        for member in member_slugs:
            log.debug("Make %s join %s" % (member, com.slug))
            com.join(UserAccount.objects.get(slug = member))

    # Create status updates
    f = open(os.path.join(HERE_COGIP, "status.csv"), "rU")
    contents = csv.DictReader(f, delimiter = ';', fieldnames = ['owner', 'publisher', 'permissions', 'text', ])
    for content in contents:
        __account__ = UserAccount.objects.get(slug = content['owner'])
        status = StatusUpdate(
            publisher = Account.objects.get(slug = content['publisher']),
            permissions = content['permissions'],
            description = content['text'],
        )
        status.save()
        log.debug("Adding status update: %s" % status)
        __account__ = SystemAccount.get()

