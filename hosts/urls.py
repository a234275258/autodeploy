from django.conf.urls import patterns, include, url
from hosts.views import *

urlpatterns = patterns('hosts.views',
                       url(r'^list/$', hosts_list, name=' hosts_list'),
                       )
