#!/usr/bin/python

"""
django.fcgi pour un deploiement chez alwaysdata
 * rendre ce fichier executable et placer à la racine
 * remplacer COUNT et PROJET par le compte alwaysdata et le projet django
 * mettre aussi un fichier .htaccess suivant:
    AddHandler fcgid-script .fcgi
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^(.*)$ django.fcgi/$1 [QSA,L]
 * mettre un lien PROJET dans /home/COUNT/www vers /home/COUNT/modules/PROJET
"""
 
import os, sys
sys.path.insert(0, "/home/COUNT/modules/PROJET")
sys.path.insert(0, "/home/COUNT/modules")
os.environ['DJANGO_SETTINGS_MODULE'] = "PROJET.settings"
from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="threaded", daemonize="false")
