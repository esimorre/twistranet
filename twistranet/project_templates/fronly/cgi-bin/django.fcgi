#!/usr/bin/python
"""
django.fcgi pour un deploiement chez alwaysdata
 * rendre ce fichier executable (chmod +x django.fcgi)
 * remplacer COUNT et PROJET par le compte alwaysdata et le projet django
 * mettre aussi un fichier .htaccess contenant:
 
AddHandler fcgid-script .fcgi
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ django.fcgi/$1 [QSA,L]

Depuis ~/www
 * ln -s /home/COUNT/modules/PROJET/www/static static
 * ln -s /home/COUNT/modules/PROJET/cgi-bin PROJET
 * cd static: ln -s /usr/local/alwaysdata/python/django/1.4.5/django/contrib/admin/static/admin admin
 * Mettre dans local_settings:
   * BASE_URL = '/PROJET/'
   * ALLOWED_HOSTS = ['monsite.alwaysdata.net', 'localhost', '127.0.0.1']
"""
 
import os, sys
sys.path.insert(0, "/home/COUNT/modules/PROJET")
sys.path.insert(0, "/home/COUNT/modules")
#os.environ['TWISTRANET_DEBUG'] = "DBG"
os.environ['DJANGO_SETTINGS_MODULE'] = "PROJET.settings"
from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="threaded", daemonize="false")
