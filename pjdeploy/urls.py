from django.conf.urls import patterns, include, url
from pjdeploy.views import *
from pjdeploy.kubeviews import *

urlpatterns = patterns('pjdeploy.views',
                       url(r'^add/$', pjdeploy_add, name=' pjdeploy_add'),
                       url(r'^list/$', pjdeploy_list, name='pjdeploy_list'),
                       url(r'^edit/$', pjdeploy_edit, name='pjdeploy_edit'),
                       url(r'^del/$', pjdeploy_del, name='pjdeploy_del'),
                       url(r'^getport/$', getport, name='getport'),
                       url(r'^getsvnfile/$', getsvnfile, name='getsvnfile'),
                       url(r'^getoldfile/$', getoldfile, name='getoldfile'),
                       url(r'^deploylog/$', deploylog, name='deploylog'),
                       url(r'^rollbackadd/$', pjdeploy_rollbackadd, name='pjdeploy_rollbackadd'),
                       url(r'^rollbacklog/$', pjdeploy_rollbacklog, name='pjdeploy_rollbacklog'),
                       url(r'^rollbacklist/$', pjdeploy_rollbacklist, name='pjdeploy_rollbacklist'),
                       url(r'^rollbackedit/$', pjdeploy_rollbackedit, name='pjdeploy_rollbackedit'),
                       url(r'^rollbackdel/$',  pjdeploy_rollbackdel, name='pjdeploy_rollbackdel'),
                       url(r'^imagesadd/$', dimages_add, name=' dimages_add'),
                       url(r'^imageslist/$', dimages_list, name='dimages_list'),
                       url(r'^imagesedit/$', dimages_edit, name='dimages_edit'),
                       url(r'^imagesdel/$', dimages_del, name='dimages_del'),
                       url(r'^kubeadd/$', kube_add, name='kube_add'),
                       url(r'^kubelist/$', kube_list, name='kube_list'),
                       url(r'^kubeedit/$', kube_edit, name='kube_edit'),
                       url(r'^kubedel/$', kube_del, name='kube_del'),

                       )

