Here you'll find various deployment scripts for your favorite HTTP servers.

 * twistranet_project -n fronly mysite
 * cd mysite
 * python manage.py syncdb : no admin
 * python manage.py twistranet_bootstrap
 * python manage.py twistranet_update
 * edit django.fcgi, follow instructions; comment debug setting after testing.
