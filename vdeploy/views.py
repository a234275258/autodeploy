#coding:utf-8
from django.shortcuts import render
from autodeploy.settings import TITLE
from django.http import HttpResponseRedirect
from django.contrib.sessions.models import Session
from autodeploy.autodeploy_api import get_alldata
import datetime





#主页
def index(request):
    cname = TITLE
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if username:
        online = Session.objects.filter(expire_date__gte=datetime.datetime.now())  # 获取未过期的sessions
        onlinecount = online.count()
        usercount = get_alldata(False).count()

        return render(request, 'index.html', locals())
    else:
        response = HttpResponseRedirect('/login/')
        return response


def logout(request): # 退出
    try:
        del request.session['username']
        del request.session['isadmin']
    except:
        pass
    response = HttpResponseRedirect('/login/')
    return response
