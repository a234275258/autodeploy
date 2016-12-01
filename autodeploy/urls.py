from django.conf.urls import patterns, include, url

from django.contrib import admin
from user.views import login,checklogin, user_list
from vdeploy.views import index,logout
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'autodeploy.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', login, name="login"),
    url(r'^$', login, name="login"),
    url(r'^index/$', index, name="index"),
    url(r'^checklogin/$', checklogin, name="checklogin"),
    url(r'^logout/$', logout, name="logout"),
    url(r'^user/', include('user.urls')),
)
