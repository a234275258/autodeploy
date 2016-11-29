#coding:utf-8
from django.shortcuts import render
from autodeploy.settings import TITLE
from django.http import HttpResponseRedirect
# Create your views here.

#主页
def index(request):
    cname = TITLE
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if username:
        # return render(request, 'index.html', {'username': usersession})
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
