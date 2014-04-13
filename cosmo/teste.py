#*-* encoding: utf-8 *-*
from __future__ import unicode_literals
import os, sys

sys.path.append('/multipla/megacosmo/')
sys.path.append('/multipla/megacosmo/cosmo')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cosmo.settings")
# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)

from base.models import Planet
import time

from base.views import master_tick

for cada in Planet.objects.all():
 cada.add_news('announcement', u'Ticks automatizados rodando. Se algo quebrar nao estarei aqui para resolver.')
 
for x in range(10000):
 #try:
  master_tick()
  if x % 70 == 0:
   for cada in Planet.objects.all():
    cada.add_news('info', u'MultiP.LA - Alpha 0.1 - Ticks de 15s<br/>Sugestões ou Críticas no <a href="http://www.ticknet.com.br/forum/viewforum.php?f=4" target="_blank">FÓRUM</a>')
  time.sleep(15)
 #except:
 # pass

