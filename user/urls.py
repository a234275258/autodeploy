from django.conf.urls import patterns, include, url
from user.views import *

urlpatterns = patterns('user.views',
                       url(r'^add/$', user_add, name='user_add'),
                       url(r'^list/$', user_list, name='user_list'),
                       url(r'^edit/$', user_edit, name='user_edit'),
                       url(r'^del/$', user_del, name='user_del'),
                       url(r'^user_detail/$', user_detail, name='user_detail'),
                       url(r'^user_mail_send/$', user_mail_send, name='user_mail_send'),
                       url(r'^forget/$', forget, name='forget'),
                       url(r'^reset_password/$', reset_password, name='reset_password'),
                       )
