#!/bin/usr/env python
#coding: utf-8
from django.conf.urls import patterns, include, url
from user.views import *

urlpatterns = patterns('user.views',
                       url(r'^add/$',privilege_add, name="privilege_add"),
                       url(r'^list/$', privilege_list, name="privilege_list"),
                       url(r'^grant/$', privilege_grant, name="privilege_grant"),
                       url(r'^grantlist/$', privilege_grantlist, name="privilege_grantlist"),
                       url(r'^grantdel/$', privilege_grantdel, name="privilege_grantdel"),
                       url(r'^grantedit/$', privilege_grantedit, name="privilege_grantedit"),
                       url(r'^del/$', privilege_del, name='privilege_del'),
                       url(r'^edit/$', privilege_edit, name='privilege_edit'),
                       )
