from django.conf.urls import patterns, include, url
from project.views import *

urlpatterns = patterns('user.views',
                       url(r'^add/$', project_add, name='project_add'),
                       url(r'^list/$', project_list, name='project_list'),
                       url(r'^edit/$', project_edit, name='project_edit'),
                       url(r'^del/$', project_del, name='project_del'),
                       url(r'^buildadd/$', project_buildadd, name='project_buildadd'),
                       url(r'^buildlist/$', project_buildlist, name='project_buildlist'),
                       url(r'^buildedit/$', project_buildedit, name='project_buildedit'),
                       url(r'^builddel/$', project_builddel, name='project_builddel'),
                       url(r'^buildlog/$', project_buildlog, name='project_buildlog'),
                       url(r'^svnadd/$', svnuser_add, name='svnuser_add'),
                       url(r'^svnlist/$', svnuser_list, name='svnuser_list'),
                       url(r'^svnedit/$', svnuser_edit, name='svnuser_edit'),
                       url(r'^svndel/$', svnuser_del, name='svnuser_del'),
                       url(r'^mavenadd/$', mavenpara_add, name='mavenpara_add'),
                       url(r'^mavenlist/$', mavenpara_list, name='mavenpara_list'),
                       url(r'^mavenedit/$', mavenpara_edit, name='mavenpara_edit'),
                       url(r'^mavendel/$', mavenpara_del, name='mavenpara_del'),
                       )
